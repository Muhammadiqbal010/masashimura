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
              Model: {{ predictionModelLabel }} · Update terakhir {{ formatDateTime(prediction.trained_at) }}
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

        <div v-if="predictionLoading" class="empty-state">
          <p class="empty-text">Memuat prediksi…</p>
        </div>

        <div v-else-if="predictionError" class="empty-state">
          <div class="empty-icon">🤖</div>
          <p class="empty-text">{{ predictionError }}</p>
          <p class="empty-hint">Butuh lebih banyak data transaksi lunas dulu sebelum model bisa dilatih</p>
        </div>

        <div v-else class="chart-grid">
          <div class="chart-card">
            <h4 class="chart-title">Tren Penjualan Historis vs Prediksi</h4>
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
      </div>

      <!-- TOP MENU TABLE -->
      <div v-if="!loadError" class="table-card">
        <div class="table-header">
          <div>
            <h3 class="table-title">Top 5 Menu Terlaris</h3>
            <p class="table-sub">Berdasarkan transaksi lunas · {{ activeDateLabel }}</p>
          </div>
        </div>

        <div v-if="stats.top_menus.length === 0" class="empty-state">
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
const prediction        = ref(null);
const predictionLoading = ref(true);
const predictionError   = ref('');
const retraining        = ref(false);

const predictionModelLabel = computed(() => {
  if (!prediction.value) return '';
  return prediction.value.best_model === 'random_forest' ? 'Random Forest' : 'Ridge Regression';
});

const fetchPrediction = async () => {
  predictionLoading.value = true;
  predictionError.value = '';
  try {
    const { data } = await apiClient.get('/prediction/revenue/', {
      params: { days: 7, history_days: 30 },
    });
    prediction.value = data;
  } catch (err) {
    prediction.value = null;
    predictionError.value =
      err.response?.data?.error || 'Belum ada model prediksi yang terlatih.';
  } finally {
    predictionLoading.value = false;
  }
};

const retrainModel = async () => {
  retraining.value = true;
  try {
    await apiClient.post('/prediction/revenue/train/');
    await fetchPrediction();
  } catch (err) {
    predictionError.value = err.response?.data?.error || 'Gagal melatih ulang model.';
  } finally {
    retraining.value = false;
  }
};

onMounted(fetchPrediction);

const refreshAll = () => Promise.all([fetchStats(), fetchPrediction()]);

function formatDateTime(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}
function shortDateLabel(iso) {
  return new Date(iso + 'T00:00:00').toLocaleDateString('id-ID', { day: '2-digit', month: 'short' });
}

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
  const upperData = [...history.map(() => null).slice(0, -1), bridgeValue, ...preds.map(p => p.upper_bound)];
  const lowerData = [...history.map(() => null).slice(0, -1), bridgeValue, ...preds.map(p => p.lower_bound)];

  return {
    labels,
    datasets: [
      {
        label: 'Batas Atas',
        data: upperData,
        borderColor: 'transparent',
        backgroundColor: 'rgba(220,38,38,0.12)',
        pointRadius: 0,
        fill: '+1',
        tension: 0.3,
      },
      {
        label: 'Batas Bawah',
        data: lowerData,
        borderColor: 'transparent',
        backgroundColor: 'rgba(220,38,38,0.12)',
        pointRadius: 0,
        fill: false,
        tension: 0.3,
      },
      {
        label: 'Prediksi',
        data: predData,
        borderColor: '#dc2626',
        backgroundColor: '#dc2626',
        borderDash: [6, 4],
        pointRadius: 2,
        tension: 0.3,
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
          filter: (item) => item.text === 'Data Historis' || item.text === 'Prediksi',
        },
      },
      tooltip: {
        ...tooltipBase(t),
        filter: (item) => item.dataset.label === 'Data Historis' || item.dataset.label === 'Prediksi',
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
      backgroundColor: '#dc2626',
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
  font-family: 'Inter', sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* ── Header ──────────────────────────────────────────────────────── */
.dash-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 2.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgb(var(--ink) / 0.06);
}
.dash-eyebrow {
  font-family: 'Oswald', sans-serif;
  font-size: 0.68rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--accent-text);
  margin-bottom: 0.3rem;
}
.dash-title {
  font-family: 'Oswald', sans-serif;
  font-size: 1.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text);
  margin: 0;
}

/* ── Filter Bar ───────────────────────────────────────────────────── */
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2.5rem;
  padding: 1rem 1.25rem;
  background: var(--surface);
  border: 1px solid rgb(var(--ink) / 0.06);
  border-radius: 14px;
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
  font-size: 0.68rem;
  font-family: 'Oswald', sans-serif;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--text-faint);
}
.date-input {
  background: transparent;
  border: none;
  outline: none;
  color: var(--text);
  font-size: 0.85rem;
  font-family: 'Inter', monospace;
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
  padding: 0.35rem 0.9rem;
  border-radius: 8px;
  border: 1px solid rgb(var(--ink) / 0.1);
  background: transparent;
  color: var(--text-dim);
  font-family: 'Oswald', sans-serif;
  font-size: 0.7rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.18s ease;
}
.shortcut-btn:hover {
  border-color: rgb(var(--ink) / 0.25);
  color: var(--text-2);
}
.shortcut-btn.active {
  background: #dc2626;
  border-color: #dc2626;
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
  font-family: 'Oswald', sans-serif;
  letter-spacing: 0.15em;
  text-transform: uppercase;
}
.spinner {
  width: 32px; height: 32px;
  border: 2px solid rgb(var(--ink) / 0.08);
  border-top-color: #dc2626;
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
  background: linear-gradient(135deg, var(--hero-from) 0%, var(--surface) 65%);
  border: 1px solid rgba(220,38,38,0.25);
  border-radius: 18px;
  padding: clamp(1.25rem, 3vw, 2rem) clamp(1.25rem, 3vw, 2.25rem);
  position: relative;
  overflow: hidden;
}
.stat-hero::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: #dc2626;
}
.stat-hero-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}
.stat-hero-label {
  font-family: 'Oswald', sans-serif;
  font-size: 0.75rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--text-dim);
}
.stat-hero-value {
  font-family: 'Inter', monospace;
  font-size: clamp(2rem, 6vw, 3rem);
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--red-soft);
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
  font-family: 'Inter', monospace;
  font-size: 0.78rem;
  font-weight: 700;
}
.trend-up   { background: rgba(34,197,94,0.1);  color: var(--green-soft); border: 1px solid rgba(34,197,94,0.25); }
.trend-down { background: rgba(248,113,113,0.1); color: var(--red-soft); border: 1px solid rgba(248,113,113,0.25); }
.trend-pill-note {
  font-family: 'Inter', sans-serif;
  font-weight: 400;
  font-size: 0.68rem;
  opacity: 0.7;
}

.stat-badge {
  font-size: 0.68rem;
  font-family: 'Oswald', sans-serif;
  letter-spacing: 0.1em;
  text-transform: uppercase;
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
  border: 1px solid rgb(var(--ink) / 0.05);
  border-radius: 14px;
  padding: 1.15rem 1.3rem;
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
  background: #a855f7;
}

.stat-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.6rem;
}
.stat-label {
  font-family: 'Oswald', sans-serif;
  font-size: 0.68rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-dim);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}
.stat-value {
  font-family: 'Inter', monospace;
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--text);
  line-height: 1.1;
  margin-bottom: 0.4rem;
  letter-spacing: -0.02em;
}
.accent-purple .stat-value { color: var(--purple-soft); }

.stat-value-text {
  font-family: 'Inter', sans-serif;
  font-size: 1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stat-sub {
  font-size: 0.7rem;
  color: var(--text-faint);
  font-family: 'Inter', sans-serif;
}

/* ── Table Card ──────────────────────────────────────────────────── */
.table-card {
  background: var(--surface);
  border: 1px solid rgb(var(--ink) / 0.05);
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 1.5rem;
}
.table-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 1.5rem 1.75rem;
  border-bottom: 1px solid rgb(var(--ink) / 0.05);
}
.table-title {
  font-family: 'Oswald', sans-serif;
  font-size: 1rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text);
  margin: 0 0 0.25rem;
}
.table-sub {
  font-size: 0.7rem;
  color: var(--text-faint);
  font-family: 'Inter', sans-serif;
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
  font-size: 0.72rem;
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
  background: rgb(var(--ink) / 0.02);
}
.menu-table th {
  padding: 0.75rem 1.5rem;
  font-family: 'Oswald', sans-serif;
  font-size: 0.68rem;
  font-weight: 400;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--text-faint);
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
  font-family: 'Inter', monospace;
}
.rank-gold   { background: rgba(251,191,36,0.15); color: var(--amber-soft); }
.rank-silver { background: rgba(156,163,175,0.12); color: var(--text-dim); }
.rank-bronze { background: rgba(180,83,9,0.15);  color: var(--amber-soft); }
.rank-default{ background: rgb(var(--ink) / 0.04); color: var(--text-faint); }

.td-name { font-weight: 500; color: var(--text); }

.td-center { text-align: center; }
.qty-val { font-weight: 700; font-family: monospace; font-size: 1rem; }
.qty-unit { font-size: 0.7rem; color: var(--text-faint); margin-left: 0.25rem; }

.td-right { text-align: right; }
.td-revenue { font-family: monospace; font-weight: 700; color: var(--amber-soft); }

.td-bar { min-width: 160px; }
.bar-cell { display: flex; align-items: center; gap: 0.6rem; }
.bar-track {
  flex: 1;
  background: rgb(var(--ink) / 0.06);
  height: 4px;
  border-radius: 99px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #dc2626, #ef4444);
  border-radius: 99px;
  transition: width 0.7s ease;
}
.bar-pct {
  font-size: 0.68rem;
  font-family: monospace;
  color: var(--text-faint);
  min-width: 2.5rem;
  text-align: right;
}

/* ── Predict Section ─────────────────────────────────────────────── */
.predict-section {
  background: var(--surface);
  border: 1px solid rgb(var(--ink) / 0.05);
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
  font-family: 'Oswald', sans-serif;
  font-size: 0.68rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-faint);
}
.predict-inline-value {
  font-family: 'Inter', monospace;
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
  border: 1px solid rgba(220,38,38,0.3);
  background: rgba(220,38,38,0.08);
  color: var(--red-soft);
  font-family: 'Oswald', sans-serif;
  font-size: 0.68rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.18s ease;
  white-space: nowrap;
}
.retrain-btn:hover:not(:disabled) { background: rgba(220,38,38,0.18); }
.retrain-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.chart-grid {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 1.25rem;
  min-width: 0;
}
@media (max-width: 900px) { .chart-grid { grid-template-columns: 1fr; } }

.chart-card {
  background: var(--surface-2);
  border: 1px solid rgb(var(--ink) / 0.05);
  border-radius: 12px;
  padding: 1.1rem 1.2rem;
  min-width: 0;
  overflow: hidden;
}
.chart-title {
  font-family: 'Oswald', sans-serif;
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
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
.dash-updated { font-size: 0.72rem; color: var(--text-dim); white-space: nowrap; }
.refresh-btn {
  display: inline-flex; align-items: center; gap: 0.45rem;
  min-height: 36px; padding: 0.4rem 0.85rem;
  border-radius: 10px; border: 1px solid var(--border-strong);
  background: transparent; color: var(--text-2);
  font-family: 'Oswald', sans-serif; font-size: 0.7rem;
  letter-spacing: 0.1em; text-transform: uppercase;
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
  font-family: 'Oswald', sans-serif; font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase;
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

</style>