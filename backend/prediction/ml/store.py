"""
Penyimpanan state model prediksi di DATABASE (bukan file).

Filesystem serverless (Vercel) read-only, jadi training tidak bisa menulis
metadata.json / revenue_model.joblib di sana. Semua dibaca/ditulis lewat
PredictionModelState supaya tersimpan permanen dan sama untuk semua instance.

Semua pembacaan dibungkus savepoint (transaction.atomic) dan tidak pernah
melempar error: kalau tabel belum dimigrasi atau DB bermasalah, hasilnya
"belum ada state" dan forecast otomatis memakai baseline.
"""
import io
import logging

import joblib
from django.db import DatabaseError, transaction

from ..models import PredictionModelState

logger = logging.getLogger(__name__)

STATE_NAME = 'revenue'

# Cache model di memori proses, dikunci oleh updated_at supaya tidak
# di-unpickle ulang di setiap request.
_cache = {'stamp': None, 'model': None}


def load_metadata() -> dict:
    """Metadata tersimpan, atau {} kalau belum pernah dilatih / DB tidak bisa dibaca."""
    try:
        with transaction.atomic():
            row = (PredictionModelState.objects
                   .defer('model_blob').filter(name=STATE_NAME).first())
    except DatabaseError:
        logger.warning('State model prediksi tidak bisa dibaca (tabel belum dimigrasi?). '
                       'Forecast pakai baseline.', exc_info=True)
        return {}
    return dict(row.metadata or {}) if row else {}


def load_model():
    """Model ML tersimpan, atau None (-> baseline)."""
    try:
        with transaction.atomic():
            stamp = (PredictionModelState.objects.filter(name=STATE_NAME)
                     .values_list('updated_at', flat=True).first())
            if stamp is None:
                return None
            if _cache['stamp'] == stamp and _cache['model'] is not None:
                return _cache['model']
            blob = (PredictionModelState.objects.filter(name=STATE_NAME)
                    .values_list('model_blob', flat=True).first())
    except DatabaseError:
        logger.warning('Model prediksi tidak bisa dibaca dari DB, pakai baseline.', exc_info=True)
        return None

    if not blob:
        return None
    try:
        # joblib = pickle. Aman di sini karena blob hanya ditulis oleh kode training
        # server ini sendiri (save_state), bukan input pengguna.
        model = joblib.load(io.BytesIO(bytes(blob)))
    except Exception:
        logger.exception('Model prediksi gagal di-load, pakai baseline.')
        return None
    _cache.update(stamp=stamp, model=model)
    return model


def save_state(metadata: dict, model=None) -> None:
    """
    Simpan metadata (+ model kalau ada) ke DB, atomik. `model=None` berarti baseline
    yang menang, jadi model lama dihapus supaya tidak basi. Melempar exception kalau
    gagal, dan pemanggil yang menanganinya.
    """
    blob = None
    if model is not None:
        buf = io.BytesIO()
        joblib.dump(model, buf)
        blob = buf.getvalue()

    with transaction.atomic():
        PredictionModelState.objects.update_or_create(
            name=STATE_NAME,
            defaults={
                'metadata': metadata,
                'model_blob': blob,
                'trained_at': _parse_dt(metadata.get('trained_at')),
            },
        )
    _cache.update(stamp=None, model=None)


def _parse_dt(value):
    from django.utils.dateparse import parse_datetime
    return parse_datetime(value) if isinstance(value, str) else None