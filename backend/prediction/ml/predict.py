"""
Load model revenue yang sudah ditrain, lalu generate forecast N hari ke depan.

CATATAN PENTING soal fitur lag:
Fitur lag_1, lag_7, dan rolling_avg_7 di sini DIBEKUKAN dari histori asli
(nilai pada hari terakhir yang benar-benar ada datanya di database), lalu
dipakai SAMA untuk semua hari forecast -- BUKAN direkursifkan memakai hasil
prediksi hari sebelumnya. Ini pilihan yang lebih simpel & aman (gak numpuk
error dari prediksi ke prediksi), tapi konsekuensinya akurasi forecast
makin menurun kalau n_days-nya panjang, karena efek lag jadi statis dan
gak "mengikuti" tren hari-hari sebelumnya dalam horizon forecast itu sendiri.

Fitur tambahan di versi ini:
- Confidence interval per hari (berbasis RMSE dari evaluasi model saat training)
- Breakdown mingguan (total & rata-rata per minggu forecast)
- Indikator tren: forecast dibanding rata-rata histori (naik/turun/stabil)
- Nama hari & format Rupiah biar langsung enak dipakai di frontend
- Validasi input & logging biar gampang di-debug kalau ada masalah
"""
import json
import logging
from datetime import timedelta
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .data import (
    FEATURE_COLUMNS,
    SCALE_FACTOR,
    add_features,
    get_daily_revenue_df,
    get_regular_closed_weekdays,
)

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).resolve().parent.parent / 'saved_models'
MODEL_PATH = MODEL_DIR / 'revenue_model.joblib'
METADATA_PATH = MODEL_DIR / 'metadata.json'

MIN_N_DAYS = 1
MAX_N_DAYS = 90
MIN_HISTORY_DAYS = 1
MAX_HISTORY_DAYS = 180

# Batas confidence interval gak boleh bikin lower_bound minus (revenue gak mungkin negatif)
CI_FLOOR = 0.0

HARI_INDONESIA = ['Senin', 'Selasa', 'Rabu', 'Kamis', "Jumat", 'Sabtu', 'Minggu']


class ModelNotTrainedError(Exception):
    """Dilempar kalau model belum pernah ditrain (file .joblib/metadata.json belum ada),
    atau kalau data historis yang tersedia gak cukup buat bikin forecast."""
    pass


def _validate_inputs(n_days: int, history_days: int) -> tuple[int, int]:
    if not isinstance(n_days, int) or n_days < MIN_N_DAYS:
        n_days = MIN_N_DAYS
    n_days = min(n_days, MAX_N_DAYS)

    if not isinstance(history_days, int) or history_days < MIN_HISTORY_DAYS:
        history_days = MIN_HISTORY_DAYS
    history_days = min(history_days, MAX_HISTORY_DAYS)

    return n_days, history_days


def _load_model_and_metadata():
    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        logger.warning('Forecast diminta tapi model belum ditrain (%s / %s belum ada).',
                        MODEL_PATH, METADATA_PATH)
        raise ModelNotTrainedError(
            'Model prediksi revenue belum pernah dilatih. Jalankan training '
            'terlebih dahulu (POST /api/prediction/revenue/train/).'
        )

    model = joblib.load(MODEL_PATH)
    with open(METADATA_PATH) as f:
        metadata = json.load(f)

    return model, metadata


def _get_rmse_for_ci(metadata: dict) -> float:
    """
    Ambil RMSE (dalam Rupiah) dari model terbaik yang tersimpan di metadata,
    dipakai sebagai lebar confidence interval. Fallback ke 0 kalau gak ketemu
    (CI jadi sama dengan titik prediksi -- lebih baik daripada error).
    """
    best_model_name = metadata.get('best_model')
    metrics = metadata.get('metrics', {})
    model_metrics = metrics.get(best_model_name, {})
    return float(model_metrics.get('rmse', 0.0))


def _freeze_lag_features(featured: pd.DataFrame) -> dict:
    """
    Bekukan nilai lag_1, lag_7, rolling_avg_7 dari histori asli
    (lihat catatan lengkap di docstring modul ini).
    """
    last_row = featured.iloc[-1]

    lag_1 = float(last_row['revenue_scaled'])
    lag_7 = (
        float(featured['revenue_scaled'].iloc[-7])
        if len(featured) >= 7 else lag_1
    )
    rolling_avg_7 = float(featured['revenue_scaled'].tail(7).mean())

    return {'lag_1': lag_1, 'lag_7': lag_7, 'rolling_avg_7': rolling_avg_7}


def _build_future_rows(future_dates: list, frozen_lags: dict, closed_weekdays: set) -> pd.DataFrame:
    rows = []
    for d in future_dates:
        dow = d.dayofweek
        day_of_month = d.day
        rows.append({
            'day_of_week': dow,
            'is_weekend': 1 if dow >= 5 else 0,
            'day_of_month': day_of_month,
            'is_payday_period': 1 if (day_of_month >= 25 or day_of_month <= 5) else 0,
            'is_regular_closed_day': 1 if dow in closed_weekdays else 0,
            'lag_1': frozen_lags['lag_1'],
            'lag_7': frozen_lags['lag_7'],
            'rolling_avg_7': frozen_lags['rolling_avg_7'],
        })
    return pd.DataFrame(rows)[FEATURE_COLUMNS]


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


def _sane_bounds(featured: pd.DataFrame) -> tuple[float, float]:
    """
    Hitung batas atas/bawah yang MASUK AKAL (dalam Rupiah) berdasarkan
    histori 14 hari terakhir (atau semua histori kalau kurang dari itu).
    Dipakai buat "mengerem" prediksi model — soalnya model regresi
    (terutama yang linear) bisa saja ekstrapolasi jauh dari histori kalau
    data training-nya sedikit/berisik. Rentangnya dibuat longgar (0.2x -
    3x rata-rata) supaya lonjakan/tren wajar tetap kebaca, tapi angka yang
    jelas-jelas tidak realistis (misal 10x lipat histori) tetap dipotong.
    """
    recent = featured['revenue_scaled'].tail(14)
    recent = recent[recent > 0]
    if recent.empty:
        return 0.0, float('inf')

    avg = float(recent.mean()) * SCALE_FACTOR
    return avg * 0.2, avg * 3.0


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
    Forecast revenue harian untuk n_days ke depan, mulai dari sehari
    setelah data historis terakhir.

    Args:
        n_days: jumlah hari ke depan yang mau diforecast (1-90).
        history_days: jumlah hari histori aktual yang mau disertakan
            dalam response, untuk keperluan chart pembanding di dashboard (1-180).

    Returns dict:
        - model_trained, best_model, trained_at, metrics   -> info model
        - generated_at                                     -> kapan forecast ini dibuat
        - data_range                                        -> rentang tanggal data historis yang dipakai
        - forecast          -> list per hari: date, day_name, is_weekend,
                                predicted_revenue, lower_bound, upper_bound
        - weekly_summary    -> breakdown per minggu (total & rata-rata)
        - trend             -> perbandingan rata-rata forecast vs rata-rata histori
        - total_estimated_revenue, average_daily_revenue
        - history           -> list {date, revenue} histori aktual, sepanjang history_days terakhir

    Raises:
        ModelNotTrainedError: kalau model belum ditrain atau data historis kosong.
    """
    n_days, history_days = _validate_inputs(n_days, history_days)

    model, metadata = _load_model_and_metadata()

    daily = get_daily_revenue_df()
    if daily.empty:
        raise ModelNotTrainedError('Belum ada data revenue historis untuk dasar forecast.')

    featured = add_features(daily)
    last_date = daily['date'].max()

    # PENTING: horizon forecast di-anchor ke HARI INI (waktu nyata), bukan
    # ke tanggal terakhir di data historis. Kalau nggak ada order baru
    # beberapa hari, last_date bisa jauh di belakang "hari ini" -- kalau
    # dipakai sebagai basis, forecast-nya nyasar ke tanggal yang udah
    # lewat. Fitur lag/rolling tetap dihitung dari histori (yang berhenti
    # di kemarin), tapi TANGGAL forecast-nya harus selalu mulai besok
    # dari hari ini yang sebenarnya.
    today = pd.Timestamp.now(tz='Asia/Jakarta').tz_localize(None).normalize()
    anchor_date = max(last_date, today)
    future_dates = [anchor_date + timedelta(days=i) for i in range(1, n_days + 1)]

    closed_weekdays = get_regular_closed_weekdays()

    frozen_lags = _freeze_lag_features(featured)
    X_future = _build_future_rows(future_dates, frozen_lags, closed_weekdays)
    preds_scaled = np.clip(model.predict(X_future), a_min=0, a_max=None)
    preds_rupiah = preds_scaled * SCALE_FACTOR

    # PENGAMAN: kalau model (khususnya yang linear) berhasil lolos seleksi
    # tapi ekstrapolasinya kebablasan karena data historis sedikit/berisik,
    # klem hasilnya ke rentang yang masuk akal dibanding histori terkini.
    # Tanpa ini, forecast bisa tampil "ratusan juta" padahal histori
    # aslinya cuma belasan juta per hari.
    lower_sane, upper_sane = _sane_bounds(featured)
    preds_rupiah = np.clip(preds_rupiah, lower_sane, upper_sane)

    # Hari yang JADWALNYA libur rutin (dari StoreSettings.operating_hours)
    # kita udah TAHU pasti tutup -- gak perlu ditebak model sama sekali.
    # Override jadi Rp0 langsung, sekalian lolos dari klem sanity di atas
    # (soalnya Rp0 di hari libur itu benar, bukan anomali yang perlu di-clip).
    for i, d in enumerate(future_dates):
        if d.dayofweek in closed_weekdays:
            preds_rupiah[i] = 0.0

    rmse = _get_rmse_for_ci(metadata)

    forecast_list = []
    for d, pred in zip(future_dates, preds_rupiah):
        pred = float(pred)
        is_closed = d.dayofweek in closed_weekdays
        forecast_list.append({
            'date': d.strftime('%Y-%m-%d'),
            'day_name': HARI_INDONESIA[d.dayofweek],
            'is_weekend': bool(d.dayofweek >= 5),
            'is_regular_closed_day': is_closed,
            'predicted_revenue': pred,
            'lower_bound': 0.0 if is_closed else float(max(CI_FLOOR, pred - rmse)),
            'upper_bound': 0.0 if is_closed else float(pred + rmse),
        })

    logger.info('Forecast berhasil dibuat: %s hari, mulai %s, model=%s',
                n_days, future_dates[0].strftime('%Y-%m-%d'), metadata.get('best_model'))

    # --- Ringkasan mingguan ---
    weekly_summary = _summarize_weekly(forecast_list)

    # --- Tren: rata-rata forecast vs rata-rata histori (pakai history_days terakhir) ---
    # PENTING: rata-rata dihitung dari HARI BUKA saja (buang hari libur
    # rutin). Kalau ikut dihitung, window histori/forecast yang kebetulan
    # punya jumlah hari libur berbeda bisa bikin tren kelihatan "turun"
    # padahal itu cuma efek lebih banyak/sedikit hari tutup, bukan demand
    # yang beneran berubah.
    history_slice = daily.tail(history_days)
    history_open = history_slice[~history_slice['date'].dt.dayofweek.isin(closed_weekdays)]
    history_avg = float(history_open['revenue'].mean()) if not history_open.empty else 0.0

    open_day_preds = [
        p for p, d in zip(preds_rupiah, future_dates) if d.dayofweek not in closed_weekdays
    ]
    forecast_avg = float(np.mean(open_day_preds)) if open_day_preds else 0.0
    trend = _compute_trend(forecast_avg, history_avg)

    history_list = [
        {'date': d.strftime('%Y-%m-%d'), 'revenue': float(r)}
        for d, r in zip(history_slice['date'], history_slice['revenue'])
    ]

    return {
        'model_trained': True,
        'best_model': metadata.get('best_model'),
        'trained_at': metadata.get('trained_at'),
        'metrics': metadata.get('metrics'),
        'generated_at': pd.Timestamp.now().isoformat(),
        'data_range': {
            'start': daily['date'].min().strftime('%Y-%m-%d'),
            'end': daily['date'].max().strftime('%Y-%m-%d'),
            'n_days_used_for_training': metadata.get('n_training_days'),
        },
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