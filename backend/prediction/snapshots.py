"""
Snapshot prediksi omzet dan perbandingannya dengan omzet sebenarnya.

Tidak ada cron di backend serverless, jadi snapshot disimpan setiap kali prediksi
dihitung (dashboard dibuka, briefing harian dimuat). Menyimpan snapshot tidak
boleh pernah mematikan prediksi: semua error database dicatat lalu diabaikan.

Aturan pembanding (Prediksi vs Realisasi):
  Untuk tiap tanggal yang sudah lewat dipakai snapshot TERBARU yang dibuat pada
  atau sebelum tanggal itu. Prediksi untuk hari H yang dihitung pada hari H hanya
  memakai data sampai kemarin (hari berjalan sengaja dibuang dari data, lihat
  data.get_daily_revenue_df), jadi tidak ada kebocoran data dari hari yang diprediksi.
"""
import logging
from datetime import date, datetime, timedelta

from django.db import DatabaseError, transaction
from django.db.models import Min
from django.utils import timezone

from order.models import WIB

from .models import RevenuePredictionSnapshot

logger = logging.getLogger(__name__)

MAX_SNAPSHOT_DAYS = 14        # batas tanggal ke depan yang disimpan per pemanggilan
CHANGE_TOLERANCE = 0.5        # selisih Rp di bawah ini dianggap tidak berubah


def today_wib() -> date:
    return timezone.now().astimezone(WIB).date()


def _as_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def save_forecast(items, method='', made_on=None) -> int:
    """
    Simpan daftar prediksi harian. `items` = list dict dengan kunci date,
    predicted_revenue, lower_bound, upper_bound, confidence, is_regular_closed_day
    (format yang sama dengan hasil forecast()/predict_dates()).

    Hanya hari buka yang disimpan, maksimal MAX_SNAPSHOT_DAYS hari pertama.
    Return jumlah baris yang ditulis (baru atau berubah); 0 bila gagal.
    """
    made_on = made_on or today_wib()
    rows = []
    for it in list(items)[:MAX_SNAPSHOT_DAYS]:
        if it.get('is_regular_closed_day'):
            continue
        try:
            target = _as_date(it['date'])
        except (KeyError, ValueError):
            continue
        if target < made_on:
            continue
        rows.append((target, it))
    if not rows:
        return 0

    try:
        with transaction.atomic():
            existing = {
                r.target_date: r
                for r in RevenuePredictionSnapshot.objects.filter(
                    made_on=made_on, target_date__in=[t for t, _ in rows])
            }
            to_create, to_update = [], []
            now = timezone.now()
            for target, it in rows:
                values = dict(
                    predicted_revenue=round(float(it['predicted_revenue']), 2),
                    lower_bound=round(float(it.get('lower_bound', 0) or 0), 2),
                    upper_bound=round(float(it.get('upper_bound', 0) or 0), 2),
                    method=method or '',
                    confidence=it.get('confidence') or '',
                )
                row = existing.get(target)
                if row is None:
                    to_create.append(RevenuePredictionSnapshot(target_date=target, made_on=made_on, **values))
                    continue
                changed = (
                    abs(row.predicted_revenue - values['predicted_revenue']) > CHANGE_TOLERANCE
                    or abs(row.lower_bound - values['lower_bound']) > CHANGE_TOLERANCE
                    or abs(row.upper_bound - values['upper_bound']) > CHANGE_TOLERANCE
                    or row.method != values['method']
                    or row.confidence != values['confidence']
                )
                if changed:
                    for k, v in values.items():
                        setattr(row, k, v)
                    row.updated_at = now      # bulk_update tidak memicu auto_now
                    to_update.append(row)
            if to_create:
                RevenuePredictionSnapshot.objects.bulk_create(to_create, ignore_conflicts=True)
            if to_update:
                RevenuePredictionSnapshot.objects.bulk_update(
                    to_update,
                    ['predicted_revenue', 'lower_bound', 'upper_bound', 'method', 'confidence', 'updated_at'],
                )
            return len(to_create) + len(to_update)
    except DatabaseError:
        logger.warning('Snapshot prediksi gagal disimpan (tabel belum dimigrasi?).', exc_info=True)
        return 0


def saved_vs_actual(actual_by_date, start, end, today=None):
    """
    Pasangan (prediksi tersimpan, omzet sebenarnya) untuk tanggal start..end yang
    sudah lewat. `actual_by_date` = {'YYYY-MM-DD': omzet}; tanggal yang tidak ada
    di sana dilewati (belum ada data pembanding).
    """
    today = today or today_wib()
    yesterday = today - timedelta(days=1)
    start, end = _as_date(start), min(_as_date(end), yesterday)
    if end < start:
        return []

    try:
        with transaction.atomic():
            snaps = list(
                RevenuePredictionSnapshot.objects
                .filter(target_date__gte=start, target_date__lte=end)
                .order_by('target_date', '-made_on')
            )
    except DatabaseError:
        logger.warning('Snapshot prediksi tidak bisa dibaca.', exc_info=True)
        return []

    chosen = {}
    for s in snaps:
        if s.made_on > s.target_date:        # dibuat setelah harinya: bukan prediksi
            continue
        chosen.setdefault(s.target_date, s)  # terurut made_on terbaru dulu

    out = []
    for target in sorted(chosen):
        key = target.isoformat()
        if key not in actual_by_date:
            continue
        s = chosen[target]
        actual = float(actual_by_date[key])
        out.append({
            'date': key,
            'predicted_revenue': s.predicted_revenue,
            'lower_bound': s.lower_bound,
            'upper_bound': s.upper_bound,
            'actual_revenue': actual,
            'error': round(s.predicted_revenue - actual, 2),
            'made_on': s.made_on.isoformat(),
            'horizon_days': (s.target_date - s.made_on).days,
            'method': s.method,
            'confidence': s.confidence,
        })
    return out


def summarize(pairs):
    """
    Ringkasan akurasi dari hasil saved_vs_actual.
      mae             rata-rata selisih absolut (Rp)
      mape            rata-rata selisih relatif (%), hanya hari dengan omzet > 0
      within_band_pct persentase hari yang omzetnya jatuh di antara batas bawah dan atas
    """
    try:
        with transaction.atomic():
            since = RevenuePredictionSnapshot.objects.aggregate(m=Min('made_on'))['m']
    except DatabaseError:
        since = None

    base = {
        'n_days': len(pairs),
        'mae': None,
        'mape': None,
        'within_band_pct': None,
        'saved_since': since.isoformat() if since else None,
    }
    if not pairs:
        return base

    abs_err = [abs(p['error']) for p in pairs]
    base['mae'] = round(sum(abs_err) / len(abs_err))
    pct = [abs(p['error']) / p['actual_revenue'] * 100 for p in pairs if p['actual_revenue'] > 0]
    base['mape'] = round(sum(pct) / len(pct), 1) if pct else None
    inside = sum(1 for p in pairs if p['lower_bound'] <= p['actual_revenue'] <= p['upper_bound'])
    base['within_band_pct'] = round(inside / len(pairs) * 100)
    return base
