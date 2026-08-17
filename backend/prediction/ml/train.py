"""
Latih dan bandingkan 2 model buat prediksi revenue harian:
- Linear Regression  → baseline sederhana
- Random Forest      → nangkep pola non-linear (efek weekend, gajian, dll)

Karena data historis masih pendek (hitungan minggu), evaluasi TIDAK pakai
random train-test split — itu bakal bocor informasi masa depan ke masa
lalu. Yang benar buat time series: split berurutan (train = hari-hari
awal, test = hari-hari terakhir).
"""
import json
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
from django.conf import settings
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error

from .data import FEATURE_COLUMNS, MIN_DAYS_REQUIRED, SCALE_FACTOR, get_training_data

MODEL_DIR = Path(__file__).resolve().parent.parent / 'saved_models'
MODEL_DIR.mkdir(exist_ok=True)

MODEL_PATH = MODEL_DIR / 'revenue_model.joblib'
METADATA_PATH = MODEL_DIR / 'metadata.json'

TEST_SIZE_DAYS = 7  # sisihkan 7 hari terakhir buat evaluasi out-of-sample


def _evaluate(y_true, y_pred):
    """
    y_true & y_pred di sini masih dalam satuan revenue_scaled (jutaan Rupiah,
    lihat SCALE_FACTOR di data.py) -- karena get_training_data() mengembalikan
    target yang sudah di-scale biar regresi lebih stabil secara numerik.
    MAE & RMSE WAJIB dikaliin balik SCALE_FACTOR di sini supaya metrik yang
    disimpan ke metadata.json & ditampilkan ke user dalam satuan Rupiah asli
    -- kalau lupa, hasilnya bakal keliatan absurd kecil (mis. "MAE=Rp1"
    padahal aslinya sekitar Rp1.000.000).
    """
    mae = mean_absolute_error(y_true, y_pred) * SCALE_FACTOR
    rmse = np.sqrt(mean_squared_error(y_true, y_pred)) * SCALE_FACTOR

    return {
        'mae': float(mae),
        'rmse': float(rmse),
        # MAPE dihitung manual dengan pengaman div-by-zero (hari revenue=0 bikin
        # mean_absolute_percentage_error bawaan sklearn meledak ke inf).
        # MAPE itu rasio (%), jadi skalanya gak kepengaruh SCALE_FACTOR -- aman dihitung
        # langsung dari y_true/y_pred yang masih di-scale.
        'mape': float(
            np.mean([
                abs(t - p) / t if t != 0 else 0.0
                for t, p in zip(y_true, y_pred)
            ]) * 100
        ),
    }


def train_and_select_best():
    """
    Latih kedua model, evaluasi di 7 hari terakhir, pilih yang MAE-nya
    lebih kecil, lalu retrain model terpilih pakai SEMUA data (biar model
    final yang disimpan memanfaatkan histori penuh, bukan cuma data train).

    Return dict berisi status & metrik — dilempar apa adanya ke caller
    (management command / view) buat ditampilkan.
    """
    X, y, _ = get_training_data()

    if X is None or len(X) < MIN_DAYS_REQUIRED:
        return {
            'success': False,
            'reason': f'Data historis kurang dari {MIN_DAYS_REQUIRED} hari '
                      f'(ada {0 if X is None else len(X)} hari). Butuh lebih banyak transaksi completed.',
        }

    if len(X) <= TEST_SIZE_DAYS + 5:
        # Data terlalu pendek buat disisihkan 7 hari penuh sbg test set.
        # PENTING: jangan sampai test set-nya cuma 1-3 hari — dengan sampel
        # segitu sedikit, "MAE lebih kecil" nyaris random dan gampang bikin
        # kita salah pilih model (lihat catatan di bawah soal Ridge vs LR).
        # Sisihkan proporsi tetap (~25%) dari data yang ada, minimal 3 hari,
        # dan selalu sisakan minimal 5 hari buat training.
        test_size = max(3, len(X) // 4)
        split_idx = max(1, len(X) - test_size)
    else:
        split_idx = len(X) - TEST_SIZE_DAYS

    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    candidates = {
        # Dulu pakai LinearRegression() polos. Masalahnya: dengan 7 fitur
        # dan histori yang kadang cuma belasan hari, matriks fiturnya
        # hampir singular -> koefisien bisa "meledak" jadi nilai ekstrem,
        # dan kalau kebetulan menang di test split yang kecil, forecast-nya
        # bisa jauh melampaui histori (ratusan juta padahal histori cuma
        # belasan juta/hari). Ridge menambah regularisasi L2 supaya
        # koefisien tetap terkendali walau data sedikit/berisik, tanpa
        # menghilangkan kemampuan menangkap tren linear.
        'ridge_regression': Ridge(alpha=1.0),
        'random_forest': RandomForestRegressor(
            n_estimators=200,
            max_depth=5,          # dibatasi — data dikit, gampang overfit kalau dalem
            min_samples_leaf=2,
            random_state=42,
        ),
    }

    results = {}
    for name, model in candidates.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        preds = np.clip(preds, a_min=0, a_max=None)  # revenue gak mungkin negatif
        results[name] = _evaluate(y_test.values, preds)

    best_name = min(results, key=lambda k: results[k]['mae'])
    best_model = candidates[best_name]

    # Retrain model terpilih pakai seluruh data (train+test) buat produksi
    best_model.fit(X, y)

    joblib.dump(best_model, MODEL_PATH)

    metadata = {
        'trained_at': datetime.now().isoformat(),
        'best_model': best_name,
        'n_training_days': int(len(X)),
        'feature_columns': FEATURE_COLUMNS,
        'metrics': results,
    }
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=2)

    return {'success': True, **metadata}