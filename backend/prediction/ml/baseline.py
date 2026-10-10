"""
Baseline forecast + fitur kalender, dipakai bareng oleh train.py dan predict.py.

Ide utamanya: forecast "default" adalah MEDIAN BERBOBOT dari omzet hari-hari
yang sama dalam seminggu (misal semua Sabtu terakhir), bobot lebih besar ke
minggu terbaru. Metode ini:
- tidak bisa meledak (hasilnya selalu di rentang yang pernah terjadi),
- bisa dijelaskan ke owner ("rata-rata Sabtu-Sabtu terakhir"),
- tidak menumpuk error seperti forecast rekursif.

Model ML (kalender saja, tanpa lag) hanya jadi challenger: baru dipakai kalau
di backtest terbukti lebih akurat dari baseline ini (lihat train.py).
"""
import numpy as np
import pandas as pd

# Fitur kalender saja -- sengaja TANPA lag_1/lag_7/rolling_avg_7, karena fitur
# lag harus dibekukan atau direkursifkan saat forecast dan itu sumber masalah.
CALENDAR_FEATURES = [
    'day_of_week', 'is_weekend', 'is_payday_period', 'is_regular_closed_day',
]

BASELINE_MAX_SAMPLES = 8        # pakai maksimal 8 sampel terakhir per hari-dalam-seminggu
RECENCY_DECAY = 0.8             # bobot sampel ke-k terbaru = 0.8 ** k
FALLBACK_RECENT_OPEN_DAYS = 28  # fallback kalau suatu hari-dalam-seminggu belum punya sampel

CONFIDENCE_MEDIUM_MIN_SAMPLES = 3
CONFIDENCE_HIGH_MIN_SAMPLES = 6

ML_UPPER_BOUND_MULTIPLIER = 1.5   # prediksi ML dipotong maksimal 1.5x omzet tertinggi terkini
ML_UPPER_BOUND_WINDOW_DAYS = 56

CONFIDENCE_ORDER = ['rendah', 'sedang', 'tinggi']


def build_calendar_features(dates, closed_weekdays) -> pd.DataFrame:
    """DataFrame fitur kalender (kolom sesuai CALENDAR_FEATURES) untuk daftar tanggal."""
    idx = pd.DatetimeIndex(dates)
    dow = np.asarray(idx.dayofweek)
    dom = np.asarray(idx.day)
    return pd.DataFrame({
        'day_of_week': dow,
        'is_weekend': (dow >= 5).astype(int),
        'is_payday_period': ((dom >= 25) | (dom <= 5)).astype(int),
        'is_regular_closed_day': np.isin(dow, list(closed_weekdays)).astype(int),
    })[CALENDAR_FEATURES]


def weighted_median(values, weights) -> float:
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    order = np.argsort(values)
    v = values[order]
    cum = np.cumsum(weights[order])
    return float(v[np.searchsorted(cum, cum[-1] / 2.0)])


def fit_baseline(daily: pd.DataFrame, closed_weekdays) -> dict:
    """
    Hitung median berbobot per hari-dalam-seminggu dari histori `daily`
    (kolom date, revenue dalam Rupiah). Hari libur rutin TIDAK dihitung.
    """
    df = daily[['date', 'revenue']].copy()
    df['dow'] = df['date'].dt.dayofweek
    df = df[~df['dow'].isin(closed_weekdays)].sort_values('date')

    by_dow = {}
    for dow, grp in df.groupby('dow'):
        values = grp['revenue'].tail(BASELINE_MAX_SAMPLES).to_numpy(dtype=float)[::-1]  # terbaru dulu
        weights = RECENCY_DECAY ** np.arange(len(values))
        by_dow[int(dow)] = {
            'value': weighted_median(values, weights),
            'n_samples': int(len(values)),
            'spread': float(np.std(values)) if len(values) >= CONFIDENCE_MEDIUM_MIN_SAMPLES else None,
        }

    recent_open = df['revenue'].tail(FALLBACK_RECENT_OPEN_DAYS)
    fallback = float(recent_open.median()) if not recent_open.empty else 0.0

    return {'by_dow': by_dow, 'fallback': fallback, 'n_open_days': int(len(df))}


def predict_baseline(baseline: dict, date) -> tuple:
    """Return (nilai_rupiah, n_samples, spread). spread None kalau sampel < 3."""
    entry = baseline['by_dow'].get(int(date.dayofweek))
    if entry is None:
        return baseline['fallback'], 0, None
    return entry['value'], entry['n_samples'], entry['spread']


def confidence_for_samples(n_samples: int) -> str:
    if n_samples >= CONFIDENCE_HIGH_MIN_SAMPLES:
        return 'tinggi'
    if n_samples >= CONFIDENCE_MEDIUM_MIN_SAMPLES:
        return 'sedang'
    return 'rendah'


def lowest_confidence(levels) -> str:
    levels = list(levels)
    if not levels:
        return 'rendah'
    return min(levels, key=CONFIDENCE_ORDER.index)


def ml_upper_bound(daily: pd.DataFrame) -> float:
    """Batas atas pengaman untuk prediksi ML (Rupiah)."""
    recent = daily['revenue'].tail(ML_UPPER_BOUND_WINDOW_DAYS)
    return float(recent.max()) * ML_UPPER_BOUND_MULTIPLIER if not recent.empty else 0.0