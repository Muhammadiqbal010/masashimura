"""
Agregasi data Order (status=completed) jadi time series revenue harian.
"""
from datetime import timedelta
import pandas as pd
from order.models import Order, StoreSettings

MIN_DAYS_REQUIRED = 14

# Ganti konstanta skala biar model lebih stabil secara numerik
SCALE_FACTOR = 1_000_000.0  # Konversi ke Juta Rupiah (misal: Rp 713.000.000 -> 713.0)


def get_regular_closed_weekdays() -> set:
    """
    Ambil hari-hari (0=Senin ... 6=Minggu, sama dengan pandas .dt.dayofweek)
    yang JADWALNYA libur rutin, dari StoreSettings.operating_hours.
    Kalau operating_hours belum diisi/kosong, anggap toko buka tiap hari
    (jangan asumsikan ada hari libur yang sebenarnya nggak diatur admin).
    """
    try:
        settings_obj = StoreSettings.get()
    except Exception:
        return set()

    hours = settings_obj.operating_hours or {}
    closed = set()
    for dow in range(7):
        entry = hours.get(str(dow))
        if not entry:  # null, atau key nggak ada sama sekali = libur
            closed.add(dow)
    return closed

def get_daily_revenue_df() -> pd.DataFrame:
    """
    Return DataFrame dengan kolom: date, revenue (dalam Rupiah asli).
    """
    rows = Order.objects.filter(status='completed').values_list('created_at', 'total_price')

    if not rows:
        return pd.DataFrame(columns=['date', 'revenue'])

    df = pd.DataFrame(list(rows), columns=['created_at', 'total_price'])
    df['created_at'] = pd.to_datetime(df['created_at'])
    
    if df['created_at'].dt.tz is not None:
        df['created_at'] = df['created_at'].dt.tz_convert('Asia/Jakarta')
        
    # Pastikan format tanggal string YYYY-MM-DD untuk menghindari bug timezone reindex
    df['date'] = df['created_at'].dt.strftime('%Y-%m-%d')
    df['total_price'] = df['total_price'].astype(float)

    # PENTING: buang HARI INI dari agregasi. Selama toko masih buka, hari
    # ini belum "tuntas" -- total revenue-nya pasti kelihatan rendah cuma
    # karena belum semua transaksi hari ini masuk, bukan karena omset
    # beneran turun. Kalau ini ikut dihitung sebagai hari penuh, garis
    # histori jadi "jatuh" tajam di titik terakhir (padahal cuma belum
    # selesai), dan fitur lag_1/rolling_avg_7 buat forecast ikut ke-freeze
    # dari angka yang belum lengkap itu. Lebih aman berhenti bersih di
    # data kemarin yang sudah pasti final.
    today_str = pd.Timestamp.now(tz='Asia/Jakarta').strftime('%Y-%m-%d')
    df = df[df['date'] < today_str]

    if df.empty:
        return pd.DataFrame(columns=['date', 'revenue'])

    daily = df.groupby('date', as_index=False)['total_price'].sum()
    daily.columns = ['date', 'revenue']
    daily['date'] = pd.to_datetime(daily['date'])

    # Reindex kontinu — PENTING: batas akhirnya bukan cuma tanggal order
    # terakhir (daily['date'].max()), tapi selalu diperpanjang sampai
    # KEMARIN (hari ini - 1). Kalau nggak, dan ternyata udah beberapa hari
    # nggak ada order baru, forecast bakal ngitung "besok" dari tanggal
    # order terakhir itu -- bukan dari hari ini yang sebenarnya. Akibatnya
    # forecast-nya nyasar ke tanggal yang udah lewat, bukan ke depan.
    # Hari-hari yang kosong (nggak ada order sama sekali) diisi Rp0 --
    # itu representasi yang benar kalau beneran nggak ada transaksi,
    # bukan bug.
    if not daily.empty:
        yesterday_str = (pd.Timestamp.now(tz='Asia/Jakarta') - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
        range_end = max(daily['date'].max(), pd.Timestamp(yesterday_str))
        full_range = pd.date_range(daily['date'].min(), range_end, freq='D')
        daily = daily.set_index('date').reindex(full_range, fill_value=0.0).reset_index()
        daily.columns = ['date', 'revenue']

    return daily


def add_features(daily: pd.DataFrame) -> pd.DataFrame:
    """
    Tambah kolom fitur. Menggunakan revenue_scaled (dalam juta) untuk komputasi lag & rolling.
    """
    df = daily.copy()
    # PENTING: Lakukan scaling nilai omset ke jutaan rupiah
    df['revenue_scaled'] = df['revenue'] / SCALE_FACTOR

    df['day_of_week'] = df['date'].dt.dayofweek
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    df['day_of_month'] = df['date'].dt.day
    df['is_payday_period'] = df['day_of_month'].apply(
        lambda d: 1 if (d >= 25 or d <= 5) else 0
    )

    # Hari libur RUTIN (misal toko selalu tutup tiap Senin) itu beda
    # secara struktural dari "hari buka tapi sepi" -- kalau nggak dibedain,
    # model bakal nganggep Rp0 di hari libur sebagai penurunan demand yang
    # perlu "dijelaskan" lewat lag/rolling, padahal itu cuma karena
    # tokonya emang tutup. Kasih fitur eksplisit biar model belajar pola
    # ini dengan benar, bukan nebak-nebak dari noise.
    closed_weekdays = get_regular_closed_weekdays()
    df['is_regular_closed_day'] = df['day_of_week'].isin(closed_weekdays).astype(int)

    # Fitur lag berbasis data yang sudah di-scale
    df['lag_1'] = df['revenue_scaled'].shift(1)
    df['lag_7'] = df['revenue_scaled'].shift(7)
    df['rolling_avg_7'] = df['revenue_scaled'].shift(1).rolling(window=7, min_periods=1).mean()

    return df


FEATURE_COLUMNS = [
    'day_of_week', 'is_weekend', 'day_of_month', 'is_payday_period',
    'is_regular_closed_day', 'lag_1', 'lag_7', 'rolling_avg_7',
]


def get_training_data():
    """
    Return (X, y_scaled, daily_df_with_features)
    Target y menggunakan nilai jutaan rupiah agar regresi linear teratur.
    """
    daily = get_daily_revenue_df()
    if daily.empty:
        return None, None, daily

    featured = add_features(daily)
    featured_clean = featured.dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)

    X = featured_clean[FEATURE_COLUMNS]
    y = featured_clean['revenue_scaled']  # Target di-scale ke Juta Rupiah
    return X, y, featured