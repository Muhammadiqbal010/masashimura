"""
Evaluasi & pemilihan metode forecast revenue harian.

Dua kandidat:
- baseline : median berbobot per hari-dalam-seminggu (lihat baseline.py)
- random_forest : ML dengan fitur kalender saja (tanpa lag)

Aturan pemilihan (sengaja konservatif):
1. Data < MIN_DAYS_FOR_BACKTEST hari -> baseline, belum bisa dievaluasi.
2. Data < MIN_DAYS_FOR_ML hari -> baseline, ML belum dicoba (menghafal doang).
3. Selain itu keduanya di-backtest pada hari-hari terakhir, dan ML HANYA
   dipakai kalau MAE-nya minimal 10% lebih kecil dari baseline.

Backtest-nya walk-forward tanpa kebocoran data: baseline di-fit ulang untuk
tiap hari uji memakai histori SEBELUM hari itu saja, ML dilatih hanya dari
data sebelum split. Evaluasi hanya di HARI BUKA (hari libur rutin pasti Rp0,
kalau ikut dihitung malah bikin metrik kelihatan bagus palsu).
"""
import json
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor

from .baseline import (
    CALENDAR_FEATURES,
    build_calendar_features,
    fit_baseline,
    ml_upper_bound,
    predict_baseline,
)
from .data import SCALE_FACTOR, get_daily_revenue_df, get_regular_closed_weekdays

MODEL_DIR = Path(__file__).resolve().parent.parent / 'saved_models'
MODEL_DIR.mkdir(exist_ok=True)

MODEL_PATH = MODEL_DIR / 'revenue_model.joblib'
METADATA_PATH = MODEL_DIR / 'metadata.json'

TEST_SIZE_DAYS = 14        # jumlah hari terakhir untuk backtest (dikecilkan otomatis kalau data pendek)
MIN_DAYS_FOR_BACKTEST = 14
MIN_DAYS_FOR_ML = 56       # 8 minggu
ML_WIN_MARGIN = 0.9        # ML harus MAE <= 90% MAE baseline


def _metrics(y_true, y_pred) -> dict:
    """Semua dalam Rupiah asli. MAPE hanya dihitung di hari dengan omzet > 0."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    nonzero = y_true > 0
    mape = (
        float(np.mean(np.abs(y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero]) * 100)
        if nonzero.any() else None
    )
    return {
        'mae': float(np.mean(np.abs(y_true - y_pred))),
        'rmse': float(np.sqrt(np.mean((y_true - y_pred) ** 2))),
        'mape': mape,
        'n_test_days': int(len(y_true)),
    }


def _new_rf() -> RandomForestRegressor:
    return RandomForestRegressor(
        n_estimators=200,
        max_depth=4,
        min_samples_leaf=3,
        random_state=42,
    )


def _fit_rf(daily, closed, end_idx: int) -> RandomForestRegressor:
    """Latih RF dari baris [0, end_idx) -- hanya hari buka."""
    head = daily.iloc[:end_idx]
    open_mask = ~head['date'].dt.dayofweek.isin(closed).to_numpy()
    X = build_calendar_features(head['date'], closed)[open_mask]
    y = (head['revenue'] / SCALE_FACTOR).to_numpy()[open_mask]
    model = _new_rf()
    model.fit(X, y)
    return model


def _backtest_baseline(daily, closed, split_idx: int):
    actual, preds = [], []
    for i in range(split_idx, len(daily)):
        date = daily['date'].iloc[i]
        if date.dayofweek in closed:
            continue
        baseline = fit_baseline(daily.iloc[:i], closed)
        preds.append(predict_baseline(baseline, date)[0])
        actual.append(float(daily['revenue'].iloc[i]))
    return actual, preds


def _backtest_ml(daily, closed, split_idx: int):
    model = _fit_rf(daily, closed, split_idx)
    test = daily.iloc[split_idx:]
    open_mask = ~test['date'].dt.dayofweek.isin(closed).to_numpy()
    if not open_mask.any():
        return [], []
    X_test = build_calendar_features(test['date'], closed)[open_mask]
    preds = np.clip(model.predict(X_test), a_min=0, a_max=None) * SCALE_FACTOR
    preds = np.clip(preds, 0, ml_upper_bound(daily.iloc[:split_idx]))
    actual = test['revenue'].to_numpy(dtype=float)[open_mask]
    return list(actual), list(preds)


def train_and_select_best():
    """
    Backtest baseline vs ML, pilih metode, simpan metadata (dan model ML
    kalau ML yang menang). Return dict yang dilempar apa adanya ke view.
    """
    daily = get_daily_revenue_df()
    if daily.empty:
        return {
            'success': False,
            'reason': 'Belum ada transaksi completed sama sekali, belum ada yang bisa dipakai untuk forecast.',
        }

    closed = get_regular_closed_weekdays()
    n_days = int(len(daily))
    metrics = {}
    best_name = 'baseline'

    if n_days < MIN_DAYS_FOR_BACKTEST:
        reason = (
            f'Data baru {n_days} hari (minimal {MIN_DAYS_FOR_BACKTEST} hari untuk evaluasi). '
            'Memakai baseline median per hari-dalam-seminggu, belum bisa diuji akurasinya.'
        )
    else:
        test_size = min(TEST_SIZE_DAYS, n_days // 4)
        split_idx = n_days - test_size

        actual, preds = _backtest_baseline(daily, closed, split_idx)
        if actual:
            metrics['baseline'] = _metrics(actual, preds)

        if n_days < MIN_DAYS_FOR_ML:
            reason = (
                f'Data baru {n_days} hari (ML baru dicoba mulai {MIN_DAYS_FOR_ML} hari, '
                'di bawah itu ML cuma menghafal). Memakai baseline.'
            )
        else:
            ml_actual, ml_preds = _backtest_ml(daily, closed, split_idx)
            if ml_actual:
                metrics['random_forest'] = _metrics(ml_actual, ml_preds)

            base, ml = metrics.get('baseline'), metrics.get('random_forest')
            if base and ml and ml['mae'] <= base['mae'] * ML_WIN_MARGIN:
                best_name = 'random_forest'
                reason = (
                    f"Random Forest lebih akurat di backtest (MAE Rp{ml['mae']:,.0f} "
                    f"vs baseline Rp{base['mae']:,.0f})."
                )
            else:
                reason = (
                    'Random Forest tidak cukup lebih akurat dari baseline di backtest '
                    f'(butuh MAE minimal {round((1 - ML_WIN_MARGIN) * 100)}% lebih kecil). Memakai baseline.'
                )

    if best_name == 'random_forest':
        final_model = _fit_rf(daily, closed, n_days)  # retrain pakai SEMUA data
        joblib.dump(final_model, MODEL_PATH)
    else:
        MODEL_PATH.unlink(missing_ok=True)  # buang model lama biar tidak basi

    metadata = {
        'trained_at': datetime.now().isoformat(),
        'best_model': best_name,
        'selection_reason': reason,
        'n_training_days': n_days,
        'feature_columns': CALENDAR_FEATURES if best_name == 'random_forest' else [],
        'metrics': metrics,
    }
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=2)

    return {'success': True, **metadata}