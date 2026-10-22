<template>
  <div class="dashboard-root">
    <!-- HEADER -->
    <div class="dash-header">
      <div>
        <p class="dash-eyebrow">Masashimura</p>
        <h1 class="dash-title">Admin Dashboard</h1>
      </div>
      <div class="dash-meta">
        <span v-if="lastUpdated" class="dash-updated">Diperbarui {{ lastUpdated }}</span>
        <button type="button" class="refresh-btn" :disabled="loading || predictionLoading" @click="refreshAll">
          <svg class="refresh-icon" :class="{ spinning: loading || predictionLoading }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a9 9 0 11-3-6.7L21 8"/><path d="M21 3v5h-5"/></svg>
          <span>Muat ulang</span>
        </button>
      </div>
    </div>

    <!-- BRIEFING HARI INI (independen dari filter tanggal; dimuat sendiri) -->
    <BriefingStrip ref="briefingRef" />

    <!-- PESANAN HARI INI (independen dari filter tanggal; refresh sendiri tiap 30 detik) -->
    <TodayOrdersCard ref="todayOrdersRef" />

    <!-- FILTER BAR -->
    <div class="filter-bar">
      <div class="date-inputs">
        <div class="date-field">
          <label class="date-label" for="dash-from">Dari</label>
          <input id="dash-from" v-model="dateFrom" type="date" class="date-input" :max="dateTo" @change="onDateChange" />
        </div>
        <div class="date-sep">—</div>
        <div class="date-field">
          <label class="date-label" for="dash-to">Sampai</label>
          <input id="dash-to" v-model="dateTo" type="date" class="date-input" :min="dateFrom" @change="onDateChange" />
        </div>
      </div>

      <div class="shortcuts" role="group" aria-label="Rentang cepat">
        <button
          v-for="sc in shortcuts"
          :key="sc.label"
          @click="applyShortcut(sc)"
          class="shortcut-btn"
          :class="{ active: activeShortcut === sc.label }"
          :aria-pressed="activeShortcut === sc.label"
        >
          {{ sc.label }}
        </button>
      </div>
    </div>

    <!-- ERROR -->
    <div v-if="loadError && !loading" class="error-banner" role="alert">
      <div class="error-text">
        <p class="error-title">Statistik gagal dimuat</p>
        <p class="error-msg">{{ loadError }}</p>
      </div>
      <button type="button" class="retry-btn" @click="fetchStats">Coba lagi</button>
    </div>

    <!-- LOADING -->
    <div v-if="loading" class="loading-state" role="status" aria-live="polite">
      <div class="spinner"></div>
      <p>Memuat data...</p>
    </div>

    <template v-else>
      <!-- HERO STAT: Total Revenue -->
      <div v-if="!loadError" class="hero-row">
        <div class="stat-hero">
          <div class="stat-hero-top">
            <span class="stat-hero-label">Total Revenue</span>
            <span class="stat-badge badge-green">Lunas</span>
          </div>
          <div class="stat-hero-value">{{ formatPrice(stats.total_revenue) }}</div>
          <div class="stat-hero-foot">
            <span class="stat-hero-sub">{{ stats.total_orders }} transaksi · {{ activeDateLabel }}</span>
            <span v-if="revenueTrendPct !== null" class="trend-pill" :class="revenueTrendPct >= 0 ? 'trend-up' : 'trend-down'">
              {{ revenueTrendPct >= 0 ? '↑' : '↓' }} {{ Math.abs(revenueTrendPct).toFixed(1) }}%
              <span class="trend-pill-note">vs periode sebelumnya</span>
            </span>
          </div>
        </div>
      </div>

      <!-- SUPPORTING STATS: sama besar, jelas di bawah hero -->
      <div v-if="!loadError" class="support-grid">

        <div class="stat-card">
          <div class="stat-top">
            <span class="stat-label">Total Pesanan</span>
          </div>
          <div class="stat-value">{{ stats.total_orders }}</div>
          <div class="stat-sub">{{ stats.completed_orders }} selesai · {{ activeDateLabel }}</div>
        </div>

        <div class="stat-card">
          <div class="stat-top">
            <span class="stat-label">Menu Terlaris</span>
          </div>
          <div class="stat-value stat-value-text">{{ topMenuName }}</div>
          <div class="stat-sub">
            {{ stats.top_menus.length > 0 ? `${stats.top_menus[0].total_qty} porsi terjual` : 'belum ada data' }}
          </div>
        </div>

        <div class="stat-card" :class="{ 'accent-purple': stats.loyal_users > 0 }">
          <div class="stat-top">
            <span class="stat-label">Loyal Users</span>
          </div>
          <div class="stat-value">{{ stats.loyal_users }}</div>
          <div class="stat-sub">
            {{ stats.loyal_users > 0 ? 'customer dengan poin aktif' : 'belum ada user loyal' }}
          </div>
        </div>

      </div>

      <!-- PREDIKSI PENJUALAN (ML) -->
      <div class="predict-section">
        <div class="predict-header">
          <div class="predict-title-block">
            <h3 class="table-title">Prediksi Penjualan (Machine Learning)</h3>
            <p class="table-sub" v-if="prediction && !predictionError">
              Model: {{ predictionModelLabel }}<template v-if="predictionDataEnd"> · Data s.d. {{ predictionDataEnd }}</template><template v-if="prediction.trained_at"> · Dilatih {{ formatDateTime(prediction.trained_at) }}</template>
            </p>
            <p class="table-sub" v-else>Estimasi penjualan berdasarkan data historis</p>
          </div>

          <div class="predict-inline-stat" v-if="prediction && !predictionError">
            <span class="predict-inline-icon">◆</span>
            <div class="predict-inline-text">
              <span class="predict-inline-label">Estimasi 7 hari ke depan</span>
              <span class="predict-inline-value">{{ formatPrice(prediction.total_estimated_revenue) }}</span>
            </div>
          </div>

          <div class="predict-actions">
            <button class="retrain-btn" @click="retrainModel" :disabled="retraining">
              {{ retraining ? 'Melatih…' : 'Latih Ulang' }}
            </button>
          </div>
        </div>

        <p v-if="retrainNotice" class="predict-notice" role="status">{{ retrainNotice }}</p>

        <!-- Tab kecil: Prediksi | Simulasi (data tab Simulasi baru dimuat saat dibuka) -->
        <div class="predict-tabs" role="tablist" aria-label="Bagian prediksi">
          <button type="button" role="tab" class="predict-tab" :aria-selected="predictTab === 'prediksi'" @click="predictTab = 'prediksi'">Prediksi</button>
          <button type="button" role="tab" class="predict-tab" :aria-selected="predictTab === 'simulasi'" @click="predictTab = 'simulasi'">Simulasi</button>
        </div>

        <SimulationPanel v-if="predictTab === 'simulasi'" />

        <template v-else>
        <div v-if="predictionLoading" class="empty-state">
          <p class="empty-text">Memuat prediksi…</p>
        </div>

        <div v-else-if="predictionError" class="empty-state">
          <div class="empty-icon">🤖</div>
          <p class="empty-text">{{ predictionError }}</p>
          <p v-if="predictionErrorHint" class="empty-hint">{{ predictionErrorHint }}</p>
        </div>

        <template v-else>
        <div class="chart-grid">
          <div class="chart-card">
            <h4 class="chart-title">Tren Penjualan Historis vs Prediksi</h4>
            <p v-if="savedAccuracyText" class="chart-caption">{{ savedAccuracyText }}</p>
            <div class="chart-wrap">
              <Line :data="trendChartData" :options="trendChartOptions" />
            </div>
          </div>
          <div class="chart-card">
            <h4 class="chart-title">Hasil Prediksi 7 Hari ke Depan</h4>
            <div class="chart-wrap">
              <Bar :data="forecastBarData" :options="forecastBarOptions" />
            </div>
          </div>
        </div>
        <PredictionInsights :prediction="prediction" />
        </template>
        </template>
      </div>

      <!-- TOP MENU TABLE -->
      <div v-if="!loadError" class="table-card">
        <div class="table-header">
          <div>
            <h3 class="table-title">{{ menuView === 'tomorrow' ? `Perkiraan Menu Besok${tomorrow ? ' · ' + tomorrow.day_name : ''}` : 'Top 5 Menu Terlaris' }}</h3>
            <p v-if="menuView === 'period'" class="table-sub">Berdasarkan transaksi lunas · {{ activeDateLabel }}</p>
            <p v-else class="table-sub">Pola penjualan hari yang sama pada beberapa minggu terakhir, minggu terbaru berbobot lebih besar</p>
          </div>
          <div class="view-toggle" role="group" aria-label="Pilih tampilan menu">
            <button
              type="button"
              class="view-toggle-btn"
              :class="{ active: menuView === 'period' }"
              :aria-pressed="menuView === 'period'"
              @click="setMenuView('period')"
            >Periode ini</button>
            <button
              type="button"
              class="view-toggle-btn"
              :class="{ active: menuView === 'tomorrow' }"
              :aria-pressed="menuView === 'tomorrow'"
              @click="setMenuView('tomorrow')"
            >Perkiraan besok</button>
          </div>
        </div>

        <!-- PERKIRAAN BESOK -->
        <template v-if="menuView === 'tomorrow'">
          <div v-if="tomorrowLoading && !tomorrow" class="empty-state">
            <p class="empty-text">Memuat perkiraan…</p>
          </div>

          <div v-else-if="tomorrowError && !tomorrow" class="empty-state">
            <p class="empty-text">Perkiraan menu besok gagal dimuat</p>
            <p class="empty-hint">Periksa koneksi lalu coba lagi.</p>
            <button type="button" class="retry-btn" @click="fetchTomorrow">Coba lagi</button>
          </div>

          <div v-else-if="tomorrow && tomorrow.closed" class="empty-state">
            <div class="empty-icon">🌙</div>
            <p class="empty-text">Besok ({{ tomorrow.day_name }}) toko libur</p>
            <p class="empty-hint">Tidak ada perkiraan menu untuk hari libur.</p>
          </div>

          <div v-else-if="tomorrow && tomorrow.menus.length === 0" class="empty-state">
            <div class="empty-icon">🍱</div>
            <p class="empty-text">Belum ada riwayat penjualan hari {{ tomorrow.day_name }}</p>
            <p class="empty-hint">Perkiraan muncul setelah ada penjualan di hari {{ tomorrow.day_name }} sebelumnya.</p>
          </div>

          <template v-else-if="tomorrow">
            <p v-if="!tomorrow.enough_data" class="tomorrow-warn" role="status">
              Baru ada {{ tomorrow.sample_days }} hari {{ tomorrow.day_name }} dengan penjualan (butuh minimal
              {{ tomorrow.min_sample_days }}), jadi urutan ini masih kasar.
            </p>
            <div class="table-wrap">
              <table class="menu-table">
                <thead>
                  <tr>
                    <th class="th-rank">#</th>
                    <th>Nama Menu</th>
                    <th class="th-center">Perkiraan permintaan</th>
                    <th class="th-right">Konsistensi</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="menu in tomorrow.menus" :key="menu.id" class="menu-row">
                    <td class="td-rank">
                      <span :class="['rank-badge', menu.rank === 1 ? 'rank-gold' : menu.rank === 2 ? 'rank-silver' : menu.rank === 3 ? 'rank-bronze' : 'rank-default']">
                        {{ menu.rank }}
                      </span>
                    </td>
                    <td class="td-name">{{ menu.name }}</td>
                    <td class="td-center">
                      <span class="level-chip" :class="`is-${menu.level}`">{{ menu.level_label }}</span>
                    </td>
                    <td class="td-right td-muted">Terjual di {{ menu.sold_days }} dari {{ tomorrow.sample_days }} hari</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p class="tomorrow-note">
              Ini pola penjualan historis, bukan keluaran model prediksi omzet. Pesanan yang belum lunas ikut dihitung
              karena dapur tetap menyiapkannya.
            </p>
          </template>
        </template>

        <div v-else-if="stats.top_menus.length === 0" class="empty-state">
          <div class="empty-icon">🍱</div>
          <p class="empty-text">Belum ada data penjualan di periode ini</p>
          <p class="empty-hint">Coba ubah rentang tanggal di atas</p>
        </div>

        <div v-else class="table-wrap">
          <table class="menu-table">
            <thead>
              <tr>
                <th class="th-rank">#</th>
                <th>Nama Menu</th>
                <th class="th-center">Porsi Terjual</th>
                <th class="th-right">Omzet</th>
                <th class="th-bar">Proporsi vs #1</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(menu, index) in stats.top_menus" :key="menu.name" class="menu-row">
                <td class="td-rank">
                  <span :class="['rank-badge', index === 0 ? 'rank-gold' : index === 1 ? 'rank-silver' : index === 2 ? 'rank-bronze' : 'rank-default']">
                    {{ index + 1 }}
                  </span>
                </td>
                <td class="td-name">{{ menu.name }}</td>
                <td class="td-center">
                  <span class="qty-val">{{ menu.total_qty }}</span>
                  <span class="qty-unit">porsi</span>
                </td>
                <td class="td-right td-revenue">{{ formatPrice(menu.total_revenue) }}</td>
                <td class="td-bar">
                  <div class="bar-cell">
                    <div class="bar-track">
                      <div class="bar-fill" :style="{ width: barWidth(menu.total_qty) + '%' }"></div>
                    </div>
                    <span class="bar-pct">{{ barWidth(menu.total_qty) }}%</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { Line, Bar } from 'vue-chartjs';
import {
  Chart as ChartJS, LineElement, PointElement, BarElement,
  CategoryScale, LinearScale, Filler, Tooltip, Legend,
} from 'chart.js';
import apiClient from '@/api/client';
import { useTheme } from '@/composables/useTheme';
import PredictionInsights from '@/components/ui/admin/PredictionInsights.vue';
import BriefingStrip from '@/components/ui/admin/BriefingStrip.vue';
import TodayOrdersCard from '@/components/ui/admin/TodayOrdersCard.vue';
import SimulationPanel from '@/components/ui/admin/SimulationPanel.vue';
import { analyticsAPI } from '@/api/analytics';

ChartJS.register(LineElement, PointElement, BarElement, CategoryScale, LinearScale, Filler, Tooltip, Legend);

const { isDark } = useTheme();

const loading        = ref(true);
const loadError      = ref('');
const lastUpdated    = ref('');
const dateFrom       = ref(today());
const dateTo         = ref(today());
const activeShortcut = ref('Hari Ini');

const stats = ref({
  total_revenue:    0,
  total_orders:     0,
  pending_orders:   0,
  completed_orders: 0,
  loyal_users:      0,
  top_menus:        [],
  // Opsional dari backend: revenue_trend_pct (persen perubahan vs periode
  // sebelumnya, sudah dihitung di server). Kalau field ini belum ada,
  // pill tren di hero card otomatis disembunyikan (lihat revenueTrendPct).
  revenue_trend_pct: null,
});

const topMenuName = computed(() => stats.value.top_menus[0]?.name || '—');

// Hanya render pill tren kalau backend benar-benar mengirim angkanya —
// lebih baik gak nampilin apa-apa daripada nampilin angka palsu.
const revenueTrendPct = computed(() => {
  const v = stats.value.revenue_trend_pct;
  return typeof v === 'number' ? v : null;
});

const shortcuts = [
  { label: 'Hari Ini',  from: () => today(),       to: () => today() },
  { label: 'Kemarin',   from: () => daysAgo(1),     to: () => daysAgo(1) },
  { label: '7 Hari',    from: () => daysAgo(6),     to: () => today() },
  { label: 'Bulan Ini', from: () => startOfMonth(), to: () => today() },
];

function applyShortcut(sc) {
  activeShortcut.value = sc.label;
  dateFrom.value = sc.from();
  dateTo.value   = sc.to();
  fetchStats();
}

function onDateChange() {
  activeShortcut.value = '';
  fetchStats();
}

const activeDateLabel = computed(() => {
  if (dateFrom.value === dateTo.value) return formatDate(dateFrom.value);
  return `${formatDate(dateFrom.value)} – ${formatDate(dateTo.value)}`;
});

const fetchStats = async () => {
  loading.value = true;
  loadError.value = '';
  try {
    const { data } = await apiClient.get('/orders/stats/', {
      params: { date_from: dateFrom.value, date_to: dateTo.value },
    });
    stats.value = data;
    lastUpdated.value = new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', hour12: false });
  } catch (err) {
    console.error('Gagal load dashboard stats:', err);
    const status = err?.response?.status;
    loadError.value = !status
      ? 'Tidak bisa terhubung ke server. Cek koneksi internet atau status backend.'
      : status === 401 || status === 403
        ? 'Sesi login habis atau akun tidak punya akses. Coba login ulang.'
        : `Server mengembalikan error (${status}). Data kamu tidak hilang — coba lagi sebentar.`;
  } finally {
    loading.value = false;
  }
};

onMounted(fetchStats);

// ── Prediksi Penjualan (ML) ───────────────────────────────────────────────
const prediction          = ref(null);
const predictTab          = ref('prediksi');   // 'prediksi' | 'simulasi'
const predictionLoading   = ref(true);
const predictionError     = ref('');
const predictionErrorHint = ref('');
const retraining          = ref(false);
const retrainNotice       = ref('');

// best_model dari API: 'baseline' atau 'random_forest'
const MODEL_LABELS = {
  random_forest: 'Random Forest',
  baseline: 'Baseline (median per hari)',
};
const predictionModelLabel = computed(() => {
  if (!prediction.value) return '';
  const key = prediction.value.best_model;
  return MODEL_LABELS[key] || key || '';
});

// Tanggal data terakhir yang dipakai untuk membuat prediksi (bukan tanggal training).
const predictionDataEnd = computed(() => {
  const end = prediction.value?.data_range?.end;
  return end ? formatDate(end) : '';
});

// Pesan error dibedakan menurut status HTTP supaya tidak menyesatkan
// (data kurang vs server bermasalah vs tidak ada koneksi).
const describeError = (err, dataFallback) => {
  if (!err.response) {
    return { text: 'Tidak dapat terhubung ke server. Periksa koneksi lalu coba lagi.', hint: '' };
  }
  const status = err.response.status;
  const apiMsg = typeof err.response.data?.error === 'string' ? err.response.data.error : '';
  if (status === 403) {
    return { text: 'Hanya admin yang dapat mengakses prediksi penjualan.', hint: '' };
  }
  if (status === 409 || status === 422) {
    return {
      text: apiMsg || dataFallback,
      hint: 'Butuh lebih banyak data transaksi lunas dulu sebelum prediksi tersedia.',
    };
  }
  return {
    text: `Server sedang bermasalah (kode ${status}).`,
    hint: 'Data transaksi kamu tidak hilang. Coba lagi sebentar.',
  };
};

const fetchPrediction = async () => {
  predictionLoading.value = true;
  predictionError.value = '';
  predictionErrorHint.value = '';
  try {
    const { data } = await apiClient.get('/prediction/revenue/', {
      params: { days: 7, history_days: 30 },
    });
    prediction.value = data;
  } catch (err) {
    prediction.value = null;
    const { text, hint } = describeError(err, 'Belum ada data untuk dibuat prediksinya.');
    predictionError.value = text;
    predictionErrorHint.value = hint;
  } finally {
    predictionLoading.value = false;
  }
};

const retrainModel = async () => {
  retraining.value = true;
  retrainNotice.value = '';
  try {
    const { data } = await apiClient.post('/prediction/revenue/train/');
    // persisted === false: evaluasi berhasil dihitung tapi gagal disimpan ke database.
    retrainNotice.value = data?.persisted === false
      ? (data.persist_error || 'Evaluasi selesai, tetapi hasilnya gagal disimpan. Prediksi tetap memakai model yang sudah ada.')
      : 'Model berhasil dilatih ulang dan tersimpan.';
    await fetchPrediction();
  } catch (err) {
    // Gagal latih ulang TIDAK boleh menghapus grafik prediksi yang sudah tampil.
    const { text } = describeError(err, 'Data belum cukup untuk melatih ulang model.');
    retrainNotice.value = `Gagal melatih ulang model. ${text}`;
  } finally {
    retraining.value = false;
  }
};

onMounted(fetchPrediction);

// ── Strip Briefing (dimuat sendiri; di sini hanya ikut "Muat ulang") ──────
const briefingRef = ref(null);
const todayOrdersRef = ref(null);

// ── Menu: periode ini / perkiraan besok ───────────────────────────────────
// Data besok dimuat saat toggle pertama kali dibuka, bukan di awal, supaya dashboard tetap ringan.
const menuView        = ref('period');
const tomorrow        = ref(null);
const tomorrowLoading = ref(false);
const tomorrowError   = ref(false);

const fetchTomorrow = async () => {
  tomorrowLoading.value = true;
  tomorrowError.value = false;
  try {
    const { data } = await analyticsAPI.getMenuTomorrow();
    tomorrow.value = data;
  } catch (err) {
    console.error('Gagal load perkiraan menu besok:', err);
    tomorrowError.value = true;
  } finally {
    tomorrowLoading.value = false;
  }
};

const setMenuView = (view) => {
  menuView.value = view;
  if (view === 'tomorrow' && !tomorrow.value && !tomorrowLoading.value) fetchTomorrow();
};

const refreshAll = () => Promise.all([
  fetchStats(),
  fetchPrediction(),
  briefingRef.value?.reload?.(),
  todayOrdersRef.value?.reload?.(),
  menuView.value === 'tomorrow' ? fetchTomorrow() : null,
]);

function formatDateTime(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}
function shortDateLabel(iso) {
  return new Date(iso + 'T00:00:00').toLocaleDateString('id-ID', { day: '2-digit', month: 'short' });
}

// ── Prediksi tersimpan vs aktual ──────────────────────────────────────────
// Prediksi yang dulu pernah ditampilkan (snapshot) untuk tanggal yang sudah lewat,
// digaris di atas data historis supaya kelihatan seberapa meleset.
const savedByDate = computed(() => {
  const map = {};
  for (const r of prediction.value?.saved_history || []) map[r.date] = r.predicted_revenue;
  return map;
});
const hasSavedPoints = computed(() => Object.keys(savedByDate.value).length > 0);

const savedAccuracyText = computed(() => {
  const acc = prediction.value?.saved_accuracy;
  if (!acc) return '';
  if (acc.n_days > 0) {
    const parts = [`Prediksi tersimpan vs aktual (${acc.n_days} hari): selisih rata-rata ${formatPrice(acc.mae)}`];
    if (acc.mape !== null) parts[0] += ` (${acc.mape}%)`;
    if (acc.within_band_pct !== null) parts.push(`${acc.within_band_pct}% hari masuk rentang prediksi`);
    return parts.join(' · ');
  }
  if (acc.saved_since) {
    return `Prediksi mulai disimpan sejak ${formatDate(acc.saved_since)}. Perbandingan dengan omzet sebenarnya muncul setelah ada hari yang sudah lewat.`;
  }
  return '';
});

// Chart "Tren Historis vs Prediksi" — garis historis (solid) nyambung ke
// garis prediksi (putus-putus) di titik terakhir data aktual, plus band
// confidence interval (batas atas/bawah) di rentang prediksi.
const trendChartData = computed(() => {
  if (!prediction.value) return { labels: [], datasets: [] };

  const history = prediction.value.history || [];
  const preds   = prediction.value.forecast || [];
  const labels  = [...history.map(h => shortDateLabel(h.date)), ...preds.map(p => shortDateLabel(p.date))];

  const historyData = [...history.map(h => h.revenue), ...preds.map(() => null)];

  // Titik jembatan: nilai aktual terakhir dipakai juga sebagai titik awal
  // garis prediksi, biar dua garis itu nyambung visual di chart.
  const bridgeValue = history.length ? history[history.length - 1].revenue : null;
  const predData = [
    ...history.map(() => null).slice(0, -1),
    bridgeValue,
    ...preds.map(p => p.predicted_revenue),
  ];
  const savedData = [...history.map(h => savedByDate.value[h.date] ?? null), ...preds.map(() => null)];
  const upperData = [...history.map(() => null).slice(0, -1), bridgeValue, ...preds.map(p => p.upper_bound)];
  const lowerData = [...history.map(() => null).slice(0, -1), bridgeValue, ...preds.map(p => p.lower_bound)];

  return {
    labels,
    datasets: [
      {
        label: 'Batas Atas',
        data: upperData,
        borderColor: 'transparent',
        backgroundColor: 'rgba(217,43,34,0.12)',
        pointRadius: 0,
        fill: '+1',
        tension: 0.3,
      },
      {
        label: 'Batas Bawah',
        data: lowerData,
        borderColor: 'transparent',
        backgroundColor: 'rgba(217,43,34,0.12)',
        pointRadius: 0,
        fill: false,
        tension: 0.3,
      },
      {
        label: 'Prediksi',
        data: predData,
        borderColor: '#d92b22',
        backgroundColor: '#d92b22',
        borderDash: [6, 4],
        pointRadius: 2,
        tension: 0.3,
        fill: false,
      },
      {
        label: 'Prediksi Tersimpan',
        data: savedData,
        borderColor: '#f4c542',
        backgroundColor: '#f4c542',
        borderDash: [2, 3],
        borderWidth: 1.5,
        pointRadius: 3,
        pointStyle: 'rectRot',
        tension: 0,
        spanGaps: false,
        fill: false,
      },
      {
        label: 'Data Historis',
        data: historyData,
        borderColor: isDark.value ? '#60a5fa' : '#2563eb',
        backgroundColor: isDark.value ? '#60a5fa' : '#2563eb',
        pointRadius: 2,
        tension: 0.3,
        fill: false,
      },
    ],
  };
});

// Warna chart (canvas tidak bisa baca CSS variable) → ikut tema aktif.
const chartTheme = computed(() => isDark.value
  ? { tick: 'rgba(255,255,255,0.55)', grid: 'rgba(255,255,255,0.07)', legend: 'rgba(255,255,255,0.7)', tipBg: '#18181b', tipText: '#fafafa', tipBorder: 'rgba(255,255,255,0.14)' }
  : { tick: 'rgba(24,24,27,0.62)',    grid: 'rgba(24,24,27,0.08)',    legend: 'rgba(24,24,27,0.75)',    tipBg: '#ffffff', tipText: '#18181b', tipBorder: 'rgba(24,24,27,0.18)' });

const tooltipBase = (t) => ({
  backgroundColor: t.tipBg, titleColor: t.tipText, bodyColor: t.tipText,
  borderColor: t.tipBorder, borderWidth: 1, padding: 10, cornerRadius: 8,
});

const trendChartOptions = computed(() => {
  const t = chartTheme.value;
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: {
        labels: {
          color: t.legend,
          font: { family: 'Inter', size: 11 },
          boxWidth: 12,
          filter: (item) => item.text === 'Data Historis' || item.text === 'Prediksi'
            || (item.text === 'Prediksi Tersimpan' && hasSavedPoints.value),
        },
      },
      tooltip: {
        ...tooltipBase(t),
        filter: (item) => item.dataset.label === 'Data Historis' || item.dataset.label === 'Prediksi'
          || (item.dataset.label === 'Prediksi Tersimpan' && item.parsed.y !== null),
        callbacks: {
          label: (ctx) => `${ctx.dataset.label}: ${formatPrice(ctx.parsed.y)}`,
        },
      },
    },
    scales: {
      x: { ticks: { color: t.tick, font: { size: 10 }, maxRotation: 0, autoSkip: true, maxTicksLimit: 8 }, grid: { color: t.grid } },
      y: { ticks: { color: t.tick, font: { size: 10 }, callback: (v) => formatPriceShort(v) }, grid: { color: t.grid } },
    },
  };
});

const forecastBarData = computed(() => {
  if (!prediction.value) return { labels: [], datasets: [] };
  const preds = prediction.value.forecast || [];
  return {
    labels: preds.map(p => shortDateLabel(p.date)),
    datasets: [{
      label: 'Prediksi Revenue',
      data: preds.map(p => p.predicted_revenue),
      backgroundColor: '#d92b22',
      borderRadius: 4,
      maxBarThickness: 36,
    }],
  };
});

const forecastBarOptions = computed(() => {
  const t = chartTheme.value;
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: { ...tooltipBase(t), callbacks: { label: (ctx) => formatPrice(ctx.parsed.y) } },
    },
    scales: {
      x: { ticks: { color: t.tick, font: { size: 10 } }, grid: { display: false } },
      y: { ticks: { color: t.tick, font: { size: 10 }, callback: (v) => formatPriceShort(v) }, grid: { color: t.grid } },
    },
  };
});

function formatPriceShort(value) {
  if (value >= 1_000_000_000) return `Rp ${(value / 1_000_000_000).toFixed(1)}M`;
  if (value >= 1_000_000) return `Rp ${Math.round(value / 1_000_000)}jt`;
  if (value >= 1_000) return `Rp ${Math.round(value / 1_000)}rb`;
  return `Rp ${value}`;
}

function today() { return new Date().toISOString().slice(0, 10); }
function daysAgo(n) { const d = new Date(); d.setDate(d.getDate() - n); return d.toISOString().slice(0, 10); }
function startOfMonth() { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`; }
function formatDate(iso) {
  if (!iso) return '';
  return new Date(iso + 'T00:00:00').toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' });
}
const barWidth = (qty) => {
  const max = Math.max(...stats.value.top_menus.map(m => m.total_qty), 1);
  return Math.round((qty / max) * 100);
};
const formatPrice = (value) =>
  new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(value || 0);
</script>

<style scoped>
/* ── Root ─────────────────────────────────────────────────────────── */
.dashboard-root {
  --page-max: 1280px;
  min-height: 100%;
  background: var(--bg);
  color: var(--text);
  /* konten dibatasi --page-max, tapi latar tetap full-width */
  padding: clamp(1.1rem, 3vw, 2.5rem) max(clamp(1rem, 3vw, 1.5rem), calc((100% - var(--page-max)) / 2));
  font-family: var(--font-body);
  -webkit-font-smoothing: antialiased;
  padding-top: 0.5rem;
}

/* ── Header ──────────────────────────────────────────────────────── */
.dash-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 1.75rem;
}
.dash-eyebrow {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--accent-text);
  margin: 0 0 0.25rem;
}
.dash-title {
  font-family: var(--font-display);
  font-size: clamp(1.75rem, 1.4rem + 1vw, 2.25rem);
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -0.015em;
  color: var(--text);
  margin: 0;
}

/* ── Filter Bar ───────────────────────────────────────────────────── */
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.75rem;
  padding: 0.85rem 1.25rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: var(--shadow-card);
}
.date-inputs {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.date-field {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}
.date-label {
  font-size: 0.8125rem;
  font-family: var(--font-body);
  letter-spacing: -0.01em;
  color: var(--text-faint);
}
.date-input {
  background: transparent;
  border: none;
  outline: none;
  color: var(--text);
  font-size: 0.85rem;
  font-family: var(--font-body);
  cursor: pointer;
  min-width: 130px;

}
.date-input::-webkit-calendar-picker-indicator { filter: invert(0.4); cursor: pointer; }
.date-sep { color: var(--text-faint); font-size: 0.9rem; }

.shortcuts {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-left: auto;
}
.shortcut-btn {
  min-height: 36px;
  padding: 0.35rem 1rem;
  border-radius: 10px;
  border: 1px solid rgb(var(--ink) / 0.1);
  background: transparent;
  color: var(--text-dim);
  font-family: var(--font-body);
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
}
.shortcut-btn:hover {
  border-color: rgb(var(--ink) / 0.25);
  color: var(--text-2);
}
.shortcut-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--on-accent);
}

/* ── Loading ─────────────────────────────────────────────────────── */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 6rem 2rem;
  color: var(--text-faint);
  font-size: 0.75rem;
  font-family: var(--font-body);
  letter-spacing: -0.01em;
}
.spinner {
  width: 32px; height: 32px;
  border: 2px solid rgb(var(--ink) / 0.1);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Hero Stat (Total Revenue) ──────────────────────────────────────
   Satu-satunya tempat aksen merah brand dipakai penuh — semua card lain
   netral, biar hero ini jelas jadi metrik #1 yang dilihat duluan. */
.hero-row {
  margin-bottom: 1.25rem;
}
.stat-hero {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: clamp(1.25rem, 3vw, 1.75rem) clamp(1.25rem, 3vw, 2rem);
  position: relative;
  overflow: hidden;
  box-shadow: var(--shadow-card);
}
.stat-hero::before {
  content: '';
  position: absolute;
  top: 0; bottom: 0; left: 0;
  width: 4px;
  background: var(--accent);
}
.stat-hero-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}
.stat-hero-label {
  font-family: var(--font-body);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-dim);
}
.stat-hero-value {
  font-family: var(--font-body);
  font-family: var(--font-display);
  font-size: clamp(2rem, 5.5vw, 2.75rem);
  font-weight: 700;
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
  color: var(--text);
  line-height: 1.05;
  margin-bottom: 0.85rem;
}
.stat-hero-foot {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.9rem;
}
.stat-hero-sub {
  font-size: 0.8rem;
  color: var(--text-dim);
}
.trend-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.25rem 0.7rem;
  border-radius: 100px;
  font-family: var(--font-body);
  font-size: 0.78rem;
  font-weight: 700;
}
.trend-up   { background: rgba(34,197,94,0.1);  color: var(--green-soft); border: 1px solid rgba(34,197,94,0.25); }
.trend-down { background: rgba(248,113,113,0.1); color: var(--red-soft); border: 1px solid rgba(248,113,113,0.25); }
.trend-pill-note {
  font-family: var(--font-body);
  font-weight: 400;
  font-size: 0.8125rem;
  opacity: 0.7;
}

.stat-badge {
  font-size: 0.8125rem;
  font-family: var(--font-body);
  letter-spacing: -0.01em;
  padding: 0.15rem 0.5rem;
  border-radius: 100px;
  border: 1px solid rgb(var(--ink) / 0.1);
  color: var(--text-faint);
  white-space: nowrap;
  flex-shrink: 0;
}
.badge-green { border-color: rgba(34,197,94,0.3); color: var(--green-soft); background: rgba(34,197,94,0.08); }

/* ── Supporting Stats ────────────────────────────────────────────── */
.support-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 2.5rem;
}
@media (max-width: 900px) { .support-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 560px) { .support-grid { grid-template-columns: 1fr; } }

.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1.15rem 1.3rem;
  box-shadow: var(--shadow-card);
  position: relative;
  overflow: hidden;
  min-width: 0;
  transition: border-color 0.2s;
}
/* Warna cuma dipakai kalau ada makna status (di sini: ada loyal user aktif) */
.stat-card.accent-purple::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: var(--purple-soft);
}

.stat-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.6rem;
}
.stat-label {
  font-family: var(--font-body);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-dim);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}
.stat-value {
  font-family: var(--font-body);
  font-family: var(--font-display);
  font-variant-numeric: tabular-nums;
  font-size: 1.625rem;
  font-weight: 700;
  color: var(--text);
  line-height: 1.15;
  margin-bottom: 0.4rem;
  letter-spacing: -0.02em;
}
.accent-purple .stat-value { color: var(--purple-soft); }

.stat-value-text {
  font-family: var(--font-body);
  font-size: 1.0625rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stat-sub {
  font-size: 0.78rem;
  color: var(--text-faint);
  font-family: var(--font-body);
}

/* ── Table Card ──────────────────────────────────────────────────── */
.table-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: var(--shadow-card);
  overflow: hidden;
  margin-bottom: 1.5rem;
}
.table-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding: 1.5rem 1.75rem;
  border-bottom: 1px solid var(--border);
}
.table-title {
  font-family: var(--font-body);
  font-size: 1.0625rem;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 0.25rem;
}
.table-sub {
  font-size: 0.78rem;
  color: var(--text-faint);
  font-family: var(--font-body);
  margin: 0;
}

/* Empty state */
.empty-state {
  padding: 4rem 2rem;
  text-align: center;
}
.empty-icon { font-size: 2rem; margin-bottom: 0.75rem; }
.empty-text {
  color: var(--text-faint);
  font-size: 0.85rem;
  margin: 0 0 0.3rem;
}
.empty-hint {
  color: var(--text-faint);
  font-size: 0.8125rem;
  margin: 0;
}

/* Table */
.table-wrap { overflow-x: auto; }
.menu-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 600px;
}
.menu-table thead tr {
  background: var(--surface-2);
}
.menu-table th {
  padding: 0.75rem 1.5rem;
  font-family: var(--font-body);
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--text-dim);
  text-align: left;
  white-space: nowrap;
}
.th-center { text-align: center; }
.th-right  { text-align: right; }
.th-bar    { min-width: 160px; white-space: nowrap; }

.menu-row {
  border-top: 1px solid rgb(var(--ink) / 0.04);
  transition: background 0.15s;
}
.menu-row:hover { background: rgb(var(--ink) / 0.02); }

.menu-table td {
  padding: 1rem 1.5rem;
  font-size: 0.875rem;
  vertical-align: middle;
}
.td-rank { width: 56px; }
.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px; height: 28px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 700;
  font-family: var(--font-body);
}
.rank-gold   { background: rgba(244,197,66,0.15); color: var(--amber-soft); }
.rank-silver { background: rgba(156,163,175,0.12); color: var(--text-dim); }
.rank-bronze { background: rgba(180,83,9,0.15);  color: var(--amber-soft); }
.rank-default{ background: rgb(var(--ink) / 0.04); color: var(--text-faint); }

.td-name { font-weight: 500; color: var(--text); }

.td-center { text-align: center; }
.qty-val { font-weight: 700; font-family: monospace; font-size: 1rem; }
.qty-unit { font-size: 0.78rem; color: var(--text-faint); margin-left: 0.25rem; }

.td-right { text-align: right; }
.td-revenue { font-family: monospace; font-weight: 700; color: var(--amber-soft); }

.td-bar { min-width: 160px; }
.bar-cell { display: flex; align-items: center; gap: 0.6rem; }
.bar-track {
  flex: 1;
  background: var(--border);
  height: 4px;
  border-radius: 99px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #d92b22, #f0524a);
  border-radius: 99px;
  transition: width 0.7s ease;
}
.bar-pct {
  font-size: 0.8125rem;
  font-family: monospace;
  color: var(--text-faint);
  min-width: 2.5rem;
  text-align: right;
}

/* ── Predict Section ─────────────────────────────────────────────── */
.predict-tabs { display: inline-flex; gap: 4px; padding: 3px; margin-bottom: 1.1rem; border-radius: 10px; background: var(--border); }
.predict-tab { min-height: 36px; padding: 0 1rem; border: 0; border-radius: 8px; background: transparent; color: var(--text-dim); font-size: .75rem; cursor: pointer; }
.predict-tab[aria-selected="true"] { background: var(--surface); color: var(--text); font-weight: 600; }
.predict-tab:focus-visible { outline: 2px solid var(--red-soft); outline-offset: 2px; }
.predict-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1.5rem 1.75rem;
  margin-bottom: 2.5rem;
}
.predict-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}
.predict-title-block { flex: 1; min-width: 220px; }

/* Baris ringkas: ikon + label + angka sejajar — bukan card kotak lagi,
   biar prediksi kebaca sebagai bagian dari section chart, bukan
   angka lepas yang bersaing sama stat card lain. */
.predict-inline-stat {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.5rem 1rem;
  border-left: 2px solid rgba(168,85,247,0.4);
}
.predict-inline-icon {
  color: var(--purple-soft);
  font-size: 0.9rem;
}
.predict-inline-text {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}
.predict-inline-label {
  font-family: var(--font-body);
  font-size: 0.8125rem;
  letter-spacing: -0.01em;
  color: var(--text-faint);
}
.predict-inline-value {
  font-family: var(--font-body);
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--purple-soft);
}

.predict-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.retrain-btn {
  padding: 0.45rem 1rem;
  border-radius: 8px;
  border: 1px solid rgba(217,43,34,0.3);
  background: rgba(217,43,34,0.08);
  color: var(--red-soft);
  font-family: var(--font-body);
  font-size: 0.8125rem;
  letter-spacing: -0.01em;
  cursor: pointer;
  transition: all 0.18s ease;
  white-space: nowrap;
}
.retrain-btn:hover:not(:disabled) { background: rgba(217,43,34,0.18); }
.retrain-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.predict-notice {
  margin: -0.75rem 0 1.25rem;
  padding: 0.55rem 0.8rem;
  font-size: 0.8125rem;
  font-family: var(--font-body);
  color: var(--text-faint);
  border: 1px solid rgba(128, 128, 128, 0.3);
  border-radius: 8px;
}

.chart-grid {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 1.25rem;
  min-width: 0;
}
@media (max-width: 900px) { .chart-grid { grid-template-columns: 1fr; } }

.chart-card {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.1rem 1.2rem;
  min-width: 0;
  overflow: hidden;
}
.chart-title {
  font-family: var(--font-body);
  font-size: 0.75rem;
  letter-spacing: -0.01em;
  color: var(--text-2);
  margin: 0 0 1rem 0;
}
.chart-wrap {
  height: 260px;
  width: 100%;
  position: relative;
  overflow: hidden;
}

/* ── Responsive tweaks ───────────────────────────────────────────── */
@media (max-width: 768px) {
  .dashboard-root { padding: 1.5rem 1rem; }
  .dash-title { font-size: 1.4rem; }
  .filter-bar { flex-direction: column; align-items: flex-start; }
  .shortcuts { margin-left: 0; }
  .table-header { flex-direction: column; gap: 0.25rem; }
  .stat-hero-value { font-size: 2.2rem; }
  .predict-header { flex-direction: column; align-items: flex-start; }
  .predict-inline-stat { border-left: none; padding-left: 0; }
}


/* ══ Tambahan: tema, UX, responsif ═════════════════════════════════ */
.stat-card, .stat-hero, .table-card, .predict-section, .filter-bar { box-shadow: var(--shadow-sm); }
.stat-hero { border-color: rgb(220 38 38 / 0.3); }
.stat-hero-value, .stat-value, .qty-val, .td-revenue, .bar-pct { font-variant-numeric: tabular-nums; }

/* meta header: info update + tombol muat ulang */
.dash-meta { display: flex; align-items: center; gap: 0.75rem; }
.dash-updated { font-size: 0.8125rem; color: var(--text-dim); white-space: nowrap; }
.refresh-btn {
  display: inline-flex; align-items: center; gap: 0.45rem;
  min-height: 36px; padding: 0.4rem 0.85rem;
  border-radius: 10px; border: 1px solid var(--border-strong);
  background: transparent; color: var(--text-2);
  font-family: var(--font-body); font-size: 0.78rem;
  letter-spacing: -0.01em;
  cursor: pointer; transition: all 0.15s;
}
.refresh-btn:hover:not(:disabled) { background: var(--surface-hover); color: var(--text); }
.refresh-btn:disabled { opacity: 0.55; cursor: progress; }
.refresh-icon.spinning { animation: spin 0.9s linear infinite; }

/* error banner */
.error-banner {
  display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap;
  margin-bottom: 1.5rem; padding: 0.9rem 1.1rem; border-radius: 12px;
  background: rgb(239 68 68 / 0.08); border: 1px solid rgb(239 68 68 / 0.35);
}
.error-text { flex: 1 1 260px; min-width: 0; }
.error-title { margin: 0 0 0.2rem; font-size: 0.85rem; font-weight: 600; color: var(--red-soft); }
.error-msg { margin: 0; font-size: 0.75rem; line-height: 1.5; color: var(--text-2); }
.retry-btn {
  min-height: 36px; padding: 0.45rem 1rem; border-radius: 8px; flex-shrink: 0;
  background: transparent; border: 1px solid rgb(239 68 68 / 0.5); color: var(--red-soft);
  font-family: var(--font-body); font-size: 0.78rem; letter-spacing: -0.01em;
  cursor: pointer; transition: background 0.15s;
}
.retry-btn:hover { background: rgb(239 68 68 / 0.12); }

/* filter bar */
.date-input { color-scheme: inherit; }
.date-input:focus-visible { outline: 2px solid var(--ring); outline-offset: 2px; border-radius: 4px; }
.date-sep { color: var(--text-faint); }
.shortcut-btn { min-height: 36px; }
.shortcut-btn.active { color: var(--on-accent); }

/* stat */
.stat-card:hover { border-color: var(--border-strong); }
.stat-label { white-space: normal; }

/* tabel */
.menu-table th { padding-block: 0.85rem; }
.th-rank { width: 56px; }
.menu-row:hover { background: var(--surface-hover); }
.bar-track { min-width: 60px; }

/* sedikit lebih tinggi di desktop lebar */
@media (min-width: 1100px) { .chart-wrap { height: 300px; } }

@media (max-width: 768px) {
  .dash-header { align-items: flex-start; gap: 0.75rem; margin-bottom: 1.5rem; padding-bottom: 1.1rem; }
  .filter-bar { align-items: stretch; margin-bottom: 1.5rem; padding: 0.9rem; }
  .date-inputs { width: 100%; }
  .date-field { flex: 1; min-width: 0; }
  .date-input { width: 100%; min-width: 0; min-height: 36px; }
  .shortcuts { width: 100%; display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.4rem; }
  .shortcut-btn { padding-inline: 0.3rem; text-align: center; }
  .support-grid { margin-bottom: 1.5rem; }
  .stat-hero-foot { flex-direction: column; align-items: flex-start; gap: 0.5rem; }
  .table-header { padding: 1.1rem 1.1rem; }
  .predict-section { padding: 1.1rem; margin-bottom: 1.5rem; }
  .predict-actions { width: 100%; }
  .retrain-btn { width: 100%; min-height: 40px; }
  .chart-card { padding: 0.9rem; }
  .chart-wrap { height: 220px; }
}

@media (max-width: 640px) {
  .dash-updated { display: none; }
  .refresh-btn span { display: none; }
  .refresh-btn { padding: 0.4rem 0.6rem; }

  /* tabel top menu: sembunyikan kolom proporsi, rapatkan padding */
  .menu-table { min-width: 0; }
  .menu-table th, .menu-table td { padding: 0.75rem 0.7rem; }
  .th-bar, .td-bar { display: none; }
  .th-rank, .td-rank { width: 40px; padding-right: 0; }
  .td-name { word-break: break-word; }
}

@media (max-width: 480px) {
  .shortcuts { grid-template-columns: repeat(2, 1fr); }
  .stat-hero { border-radius: 14px; }
  .qty-unit { display: none; }
}

@media (pointer: coarse) {
  .shortcut-btn, .refresh-btn, .retrain-btn { min-height: 44px; }
}


/* ── Prediksi tersimpan: keterangan akurasi di bawah judul grafik ───── */
.chart-caption {
  margin: -0.2rem 0 0.7rem;
  font-size: 0.8125rem;
  line-height: 1.4;
  color: var(--text-dim);
}

/* ── Toggle Top 5: Periode ini / Perkiraan besok ───────────────────── */
.view-toggle {
  display: inline-flex;
  padding: 3px;
  gap: 2px;
  border: 1px solid rgb(var(--ink) / 0.1);
  border-radius: 10px;
  background: rgb(var(--ink) / 0.03);
}
.view-toggle-btn {
  padding: 0.3rem 0.8rem;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: var(--text-dim);
  font-family: var(--font-body);
  font-size: 0.8125rem;
  letter-spacing: -0.01em;
  cursor: pointer;
  transition: background 0.18s ease, color 0.18s ease;
}
.view-toggle-btn:hover { color: var(--text-2); }
.view-toggle-btn.active { background: #d92b22; color: var(--on-accent); }

.level-chip {
  display: inline-block;
  padding: 0.12rem 0.65rem;
  border-radius: 999px;
  border: 1px solid rgb(var(--ink) / 0.14);
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-2);
}
.level-chip.is-tinggi {
  color: var(--green-soft);
  border-color: color-mix(in srgb, var(--green-soft) 45%, transparent);
}
.td-muted { font-size: 0.75rem; color: var(--text-dim); }
.tomorrow-warn {
  margin: 0 0 0.9rem;
  padding: 0.55rem 0.8rem;
  font-size: 0.76rem;
  color: var(--amber-soft);
  background: color-mix(in srgb, var(--amber-soft) 9%, transparent);
  border: 1px solid color-mix(in srgb, var(--amber-soft) 28%, transparent);
  border-radius: 10px;
}
.tomorrow-note {
  margin: 0.9rem 0 0;
  font-size: 0.8125rem;
  line-height: 1.45;
  color: var(--text-faint);
}
</style>