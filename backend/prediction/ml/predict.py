"""
Generate forecast revenue harian N hari ke depan.

Metode default: BASELINE (median berbobot per hari-dalam-seminggu, lihat
baseline.py). Model Random Forest hanya dipakai kalau train.py sudah
membuktikan lewat backtest bahwa dia lebih akurat (best_model di
metadata.json == 'random_forest') dan file modelnya berhasil di-load.
Selain itu otomatis jatuh ke baseline, jadi endpoint ini TIDAK lagi error
409 cuma karena model belum pernah dilatih.

Setiap hari forecast punya status keyakinan (rendah/sedang/tinggi), dan
response punya satu status keyakinan keseluruhan + pesan peringatan buat
ditampilkan di dashboard. Keyakinan 'rendah' = datanya belum cukup, jangan
dipakai buat keputusan besar.

Tidak ada fitur lag di sini, jadi tidak ada lagi masalah "lag dibekukan"
atau error yang menumpuk antar hari forecast.
"""
import json
import logging
from datetime import timedelta
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .baseline import (
    build_calendar_features,
    confidence_for_samples,
    fit_baseline,
    lowest_confidence,
    ml_upper_bound,
    predict_baseline,
)
from .data import SCALE_FACTOR, get_daily_revenue_df, get_regular_closed_weekdays

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).resolve().parent.parent / 'saved_models'
MODEL_PATH = MODEL_DIR / 'revenue_model.joblib'
METADATA_PATH = MODEL_DIR / 'metadata.json'

MIN_N_DAYS = 1
MAX_N_DAYS = 90
MIN_HISTORY_DAYS = 1
MAX_HISTORY_DAYS = 180

CI_FLOOR = 0.0
UNCERTAIN_BAND_RATIO = 0.5   # lebar interval = 50% prediksi kalau sampelnya < 3
ML_HIGH_CONFIDENCE_DAYS = 180

HARI_INDONESIA = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

CONFIDENCE_MESSAGES = {
    'rendah': (
        'Data historis masih sedikit, jadi angka ini cuma gambaran kasar. '
        'Jangan dijadikan dasar keputusan besar (stok bahan, jadwal karyawan) dulu.'
    ),
    'sedang': (
        'Data historis mulai cukup tapi masih terbatas. '
        'Pakai sebagai acuan dan tetap cek kondisi lapangan.'
    ),
    'tinggi': 'Data historis sudah cukup untuk pola mingguan yang stabil.',
}


class ModelNotTrainedError(Exception):
    """Dilempar kalau belum ada data revenue historis sama sekali untuk dasar forecast."""
    pass


def _validate_inputs(n_days: int, history_days: int) -> tuple[int, int]:
    if not isinstance(n_days, int) or n_days < MIN_N_DAYS:
        n_days = MIN_N_DAYS
    n_days = min(n_days, MAX_N_DAYS)

    if not isinstance(history_days, int) or history_days < MIN_HISTORY_DAYS:
        history_days = MIN_HISTORY_DAYS
    history_days = min(history_days, MAX_HISTORY_DAYS)

    return n_days, history_days


def _load_metadata() -> dict:
    if not METADATA_PATH.exists():
        return {}
    try:
        with open(METADATA_PATH) as f:
            return json.load(f)
    except (OSError, ValueError):
        logger.warning('metadata.json gagal dibaca, forecast pakai baseline.', exc_info=True)
        return {}


def _load_ml_model(metadata: dict):
    """Return model ML kalau memang terpilih & bisa di-load, selain itu None (-> baseline)."""
    if metadata.get('best_model') != 'random_forest' or not MODEL_PATH.exists():
        return None
    try:
        return joblib.load(MODEL_PATH)
    except Exception:
        logger.exception('Model ML gagal di-load, forecast pakai baseline.')
        return None


def _summarize_weekly(forecast_list: list) -> list:
    """Kelompokkan hasil forecast harian jadi ringkasan per minggu (Minggu 1, Minggu 2, dst)."""
    weekly = []
    for start in range(0, len(forecast_list), 7):
        chunk = forecast_list[start:start + 7]
        total = sum(item['predicted_revenue'] for item in chunk)
        weekly.append({
            'week_number': (start // 7) + 1,
            'date_start': chunk[0]['date'],
            'date_end': chunk[-1]['date'],
            'total_revenue': float(total),
            'average_daily_revenue': float(total / len(chunk)),
            'n_days': len(chunk),
        })
    return weekly


def _compute_trend(forecast_avg: float, history_avg: float) -> dict:
    if history_avg <= 0:
        return {'direction': 'tidak_diketahui', 'change_pct': 0.0}

    change_pct = ((forecast_avg - history_avg) / history_avg) * 100
    if change_pct > 3:
        direction = 'naik'
    elif change_pct < -3:
        direction = 'turun'
    else:
        direction = 'stabil'

    return {'direction': direction, 'change_pct': round(float(change_pct), 2)}


def forecast(n_days: int = 30, history_days: int = 30) -> dict:
    """
    Forecast revenue harian untuk n_days ke depan, mulai besok (hari ini
    yang sebenarnya, bukan tanggal order terakhir).

    Returns dict (key lama tetap ada, supaya frontend tidak patah):
        - model_trained (selalu True), best_model ('baseline' / 'random_forest'),
          method, selection_reason, trained_at, metrics
        - confidence   -> {level, message, history_days}   (BARU)
        - forecast     -> per hari: date, day_name, is_weekend, is_regular_closed_day,
                          predicted_revenue, lower_bound, upper_bound,
                          confidence, n_samples                (confidence & n_samples BARU)
        - weekly_summary, trend, total_estimated_revenue, average_daily_revenue, history

    Raises:
        ModelNotTrainedError: kalau belum ada data revenue historis sama sekali.
    """
    n_days, history_days = _validate_inputs(n_days, history_days)

    daily = get_daily_revenue_df()
    if daily.empty:
        raise ModelNotTrainedError('Belum ada data revenue historis untuk dasar forecast.')

    closed = get_regular_closed_weekdays()
    metadata = _load_metadata()
    ml_model = _load_ml_model(metadata)
    method = 'random_forest' if ml_model is not None else 'baseline'

    # Horizon di-anchor ke HARI INI (waktu nyata), bukan ke tanggal terakhir
    # di data. daily sudah dipotong sampai kemarin, jadi forecast mulai besok.
    last_date = daily['date'].max()
    today = pd.Timestamp.now(tz='Asia/Jakarta').tz_localize(None).normalize()
    anchor_date = max(last_date, today)
    future_dates = [anchor_date + timedelta(days=i) for i in range(1, n_days + 1)]

    baseline = fit_baseline(daily, closed)

    ml_preds = None
    ml_rmse = None
    if ml_model is not None:
        X_future = build_calendar_features(future_dates, closed)
        ml_preds = np.clip(ml_model.predict(X_future), a_min=0, a_max=None) * SCALE_FACTOR
        ml_preds = np.clip(ml_preds, 0, ml_upper_bound(daily))
        ml_rmse = (metadata.get('metrics') or {}).get('random_forest', {}).get('rmse')
        ml_confidence = 'tinggi' if len(daily) >= ML_HIGH_CONFIDENCE_DAYS else 'sedang'

    forecast_list = []
    preds_rupiah = []
    open_day_confidences = []

    for i, d in enumerate(future_dates):
        is_closed = d.dayofweek in closed

        if is_closed:
            # Jadwal libur rutin sudah PASTI, tidak perlu ditebak.
            pred, lower, upper = 0.0, 0.0, 0.0
            confidence, n_samples = 'tinggi', None
        elif method == 'baseline':
            pred, n_samples, spread = predict_baseline(baseline, d)
            half_width = spread if spread is not None else pred * UNCERTAIN_BAND_RATIO
            lower = max(CI_FLOOR, pred - half_width)
            upper = pred + half_width
            confidence = confidence_for_samples(n_samples)
            open_day_confidences.append(confidence)
        else:
            pred = float(ml_preds[i])
            n_samples = None
            half_width = float(ml_rmse) if ml_rmse else pred * UNCERTAIN_BAND_RATIO
            lower = max(CI_FLOOR, pred - half_width)
            upper = pred + half_width
            confidence = ml_confidence
            open_day_confidences.append(confidence)

        pred = float(pred)
        preds_rupiah.append(pred)
        forecast_list.append({
            'date': d.strftime('%Y-%m-%d'),
            'day_name': HARI_INDONESIA[d.dayofweek],
            'is_weekend': bool(d.dayofweek >= 5),
            'is_regular_closed_day': is_closed,
            'predicted_revenue': pred,
            'lower_bound': float(lower),
            'upper_bound': float(upper),
            'confidence': confidence,
            'n_samples': n_samples,
        })

    logger.info('Forecast dibuat: %s hari, mulai %s, metode=%s',
                n_days, future_dates[0].strftime('%Y-%m-%d'), method)

    overall_level = lowest_confidence(open_day_confidences)
    confidence_info = {
        'level': overall_level,
        'message': CONFIDENCE_MESSAGES[overall_level],
        'history_days': int(len(daily)),
    }

    weekly_summary = _summarize_weekly(forecast_list)

    # Tren dihitung dari HARI BUKA saja, supaya jumlah hari libur yang beda
    # antar window tidak bikin tren kelihatan naik/turun palsu.
    history_slice = daily.tail(history_days)
    history_open = history_slice[~history_slice['date'].dt.dayofweek.isin(closed)]
    history_avg = float(history_open['revenue'].mean()) if not history_open.empty else 0.0

    open_day_preds = [
        p for p, d in zip(preds_rupiah, future_dates) if d.dayofweek not in closed
    ]
    forecast_avg = float(np.mean(open_day_preds)) if open_day_preds else 0.0
    trend = _compute_trend(forecast_avg, history_avg)

    history_list = [
        {'date': d.strftime('%Y-%m-%d'), 'revenue': float(r)}
        for d, r in zip(history_slice['date'], history_slice['revenue'])
    ]

    return {
        'model_trained': True,
        'best_model': method,
        'method': method,
        'selection_reason': metadata.get('selection_reason'),
        'trained_at': metadata.get('trained_at'),
        'metrics': metadata.get('metrics') or {},
        'generated_at': pd.Timestamp.now().isoformat(),
        'data_range': {
            'start': daily['date'].min().strftime('%Y-%m-%d'),
            'end': daily['date'].max().strftime('%Y-%m-%d'),
            'n_days_used_for_training': metadata.get('n_training_days'),
        },
        'confidence': confidence_info,
        'n_days': n_days,
        'forecast': forecast_list,
        'weekly_summary': weekly_summary,
        'trend': {
            **trend,
            'forecast_average_daily': round(forecast_avg, 2),
            'history_average_daily': round(history_avg, 2),
        },
        'total_estimated_revenue': float(np.sum(preds_rupiah)),
        'average_daily_revenue': round(forecast_avg, 2),
        'history': history_list,
    }