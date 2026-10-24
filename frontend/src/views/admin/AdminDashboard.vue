<template>
  <div class="adm-page dashboard-root">
    <!-- HEADER -->
    <header class="adm-header">
      <div>
        <p class="adm-eyebrow">Masashimura · Admin</p>
        <h1 class="adm-title">Admin Dashboard</h1>
      </div>
      <div class="adm-header-actions">
        <button type="button" class="adm-btn adm-btn--ghost adm-btn--sm" :disabled="loading || predictionLoading" @click="refreshAll">
          <svg class="refresh-icon" :class="{ spinning: loading || predictionLoading }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a9 9 0 11-3-6.7L21 8"/><path d="M21 3v5h-5"/></svg>
          <span>Muat ulang</span>
        </button>
      </div>
    </header>

    <!-- HARI INI: briefing + pesanan (tidak ikut filter tanggal; dimuat dan disegarkan sendiri) -->
    <BriefingStrip ref="briefingRef" />
    <TodayOrdersCard ref="todayOrdersRef" />

    <!-- RINGKASAN PERIODE: semua yang ikut filter tanggal ada di satu bagian ini -->
    <section class="period" aria-labelledby="period-title">
      <div class="period-head">
        <div class="period-title-block">
          <h2 id="period-title" class="period-title">Ringkasan periode</h2>
          <p class="period-sub">
            {{ activeDateLabel }}<template v-if="lastUpdated"> · diperbarui {{ lastUpdated }}</template>
          </p>
        </div>

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
        <!-- KPI: empat kartu sama besar, satu gaya -->
        <div v-if="!loadError" class="kpi-grid">
          <div class="stat-card stat-card--primary">
            <div class="stat-top">
              <span class="stat-label">Total Revenue</span>
              <span class="stat-badge badge-green">Lunas</span>
            </div>
            <div class="stat-value">{{ formatPrice(stats.total_revenue) }}</div>
            <div class="stat-sub">
              {{ stats.total_orders }} transaksi
              <span v-if="revenueTrendPct !== null" class="trend-pill" :class="revenueTrendPct >= 0 ? 'trend-up' : 'trend-down'">
                {{ revenueTrendPct >= 0 ? '↑' : '↓' }} {{ Math.abs(revenueTrendPct).toFixed(1) }}%
              </span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-top"><span class="stat-label">Total Pesanan</span></div>
            <div class="stat-value">{{ stats.total_orders }}</div>
            <div class="stat-sub">{{ stats.completed_orders }} selesai</div>
          </div>

          <div class="stat-card">
            <div class="stat-top"><span class="stat-label">Menu Terlaris</span></div>
            <div class="stat-value stat-value-text">{{ topMenuName }}</div>
            <div class="stat-sub">
              {{ stats.top_menus.length > 0 ? `${stats.top_menus[0].total_qty} porsi terjual` : 'belum ada data' }}
            </div>
          </div>

          <div class="stat-card" :class="{ 'accent-purple': stats.loyal_users > 0 }">
            <div class="stat-top"><span class="stat-label">Loyal Users</span></div>
            <div class="stat-value">{{ stats.loyal_users }}</div>
            <div class="stat-sub">
              {{ stats.loyal_users > 0 ? 'customer dengan poin aktif' : 'belum ada user loyal' }}
            </div>
          </div>
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
    </section>

    <!-- PREDIKSI & SIMULASI (dimuat terpisah; tidak ikut filter tanggal) -->
    <section class="predict-section" aria-labelledby="predict-title">
      <div class="predict-header">
        <div class="predict-title-block">
          <h2 id="predict-title" class="period-title">Prediksi Penjualan</h2>
          <p class="period-sub" v-if="prediction && !predictionError">
            Metode: {{ predictionModelLabel }}<template v-if="predictionDataEnd"> · data s.d. {{ predictionDataEnd }}</template><template v-if="prediction.trained_at"> · dilatih {{ formatDateTime(prediction.trained_at) }}</template>
          </p>
          <p class="period-sub" v-else>Estimasi penjualan berdasarkan data historis</p>
        </div>

        <div class="predict-summary" v-if="prediction && !predictionError">
          <div class="predict-inline-text">
            <span class="predict-inline-label">Estimasi 7 hari ke depan</span>
            <span class="predict-inline-value">{{ formatPrice(prediction.total_estimated_revenue) }}</span>
          </div>
          <span v-if="predictionLevel" class="predict-conf" :class="`is-${predictionLevel}`">Keyakinan {{ predictionLevel }}</span>
        </div>

        <button class="retrain-btn" @click="retrainModel" :disabled="retraining">
          {{ retraining ? 'Melatih…' : 'Latih Ulang' }}
        </button>
      </div>

      <p v-if="retrainNotice" class="predict-notice" role="status">{{ retrainNotice }}</p>

      <div class="predict-tabs" role="tablist" aria-label="Bagian prediksi">
        <button type="button" role="tab" class="predict-tab" :aria-selected="predictTab === 'grafik'" @click="predictTab = 'grafik'">Grafik</button>
        <button type="button" role="tab" class="predict-tab" :aria-selected="predictTab === 'hari'" @click="predictTab = 'hari'">Per Hari</button>
        <button type="button" role="tab" class="predict-tab" :aria-selected="predictTab === 'simulasi'" @click="predictTab = 'simulasi'">Simulasi</button>
      </div>

      <SimulationPanel v-if="predictTab === 'simulasi'" />

      <template v-else>
        <div v-if="predictionLoading && !prediction" class="empty-state">
          <p class="empty-text">Memuat prediksi…</p>
        </div>

        <div v-else-if="predictionError" class="empty-state">
          <div class="empty-icon">🤖</div>
          <p class="empty-text">{{ predictionError }}</p>
          <p v-if="predictionErrorHint" class="empty-hint">{{ predictionErrorHint }}</p>
        </div>

        <template v-else-if="prediction">
          <!-- GRAFIK: satu grafik, prediksi lama bisa dinyalakan sendiri -->
          <div v-if="predictTab === 'grafik'" class="predict-panel">
            <div class="chart-card">
              <div class="chart-toolbar">
                <h3 class="chart-title">Omzet harian: asli dan prediksi</h3>
                <button
                  v-if="hasSavedPoints"
                  type="button"
                  class="saved-toggle"
                  :aria-pressed="showSaved"
                  @click="showSaved = !showSaved"
                >
                  <span class="saved-toggle-dot" aria-hidden="true"></span>
                  Bandingkan dengan prediksi lama
                </button>
              </div>

              <ul class="chart-legend" aria-label="Keterangan grafik">
                <li><span class="lg lg-real" aria-hidden="true"></span>Omzet asli</li>
                <li><span class="lg lg-pred" aria-hidden="true"></span>Prediksi ke depan</li>
                <li><span class="lg lg-band" aria-hidden="true"></span>Rentang perkiraan</li>
                <li v-if="showSaved && hasSavedPoints"><span class="lg lg-saved" aria-hidden="true"></span>Prediksi lama</li>
              </ul>

              <div class="chart-wrap">
                <Line :data="trendChartData" :options="trendChartOptions" />
              </div>

              <p v-if="savedAccuracyText && (showSaved || !hasSavedPoints)" class="chart-caption">{{ savedAccuracyText }}</p>
              <p v-if="showSaved && hasSavedPoints" class="chart-caption chart-caption--hint">
                Prediksi lama adalah tebakan yang dibuat sebelum harinya tiba, jadi bisa dinilai dengan omzet asli.
              </p>
            </div>
            <PredictionInsights :prediction="prediction" :sections="['strip']" />
          </div>

          <!-- PER HARI: tabel rincian + detail metode -->
          <div v-else class="predict-panel">
            <PredictionInsights :prediction="prediction" :sections="['table', 'details']" />
          </div>
        </template>
      </template>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { Line } from 'vue-chartjs';
import {
  Chart as ChartJS, LineElement, PointElement,
  CategoryScale, LinearScale, Filler, Tooltip, Legend,
} from 'chart.js';
import apiClient from '@/api/client';
import { useTheme } from '@/composables/useTheme';
import PredictionInsights from '@/components/ui/admin/PredictionInsights.vue';
import BriefingStrip from '@/components/ui/admin/BriefingStrip.vue';
import TodayOrdersCard from '@/components/ui/admin/TodayOrdersCard.vue';
import SimulationPanel from '@/components/ui/admin/SimulationPanel.vue';
import { analyticsAPI } from '@/api/analytics';

ChartJS.register(LineElement, PointElement, CategoryScale, LinearScale, Filler, Tooltip, Legend);

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
const predictTab          = ref('grafik');     // 'grafik' | 'hari' | 'simulasi'
const showSaved           = ref(false);        // tampilkan garis prediksi lama (sengaja mati dulu supaya grafik tidak ramai)
const predictionLoading   = ref(true);
const predictionError     = ref('');
const predictionErrorHint = ref('');
const retraining          = ref(false);
const retrainNotice       = ref('');

// best_model dari API: 'baseline' atau 'random_forest'
const MODEL_LABELS = {
  random_forest: 'Random Forest',
  baseline: 'Baseline (median per hari)',
  ridge_regression: 'Ridge Regression',
};
const predictionModelLabel = computed(() => {
  if (!prediction.value) return '';
  const key = prediction.value.best_model;
  return MODEL_LABELS[key] || key || '';
});

// 'rendah' | 'sedang' | 'tinggi' dari server (dipakai untuk chip di header prediksi).
const predictionLevel = computed(() => prediction.value?.confidence?.level || '');

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
    const parts = [`Prediksi lama vs omzet asli (${acc.n_days} hari): meleset rata-rata ${formatPrice(acc.mae)}`];
    if (acc.mape !== null) parts[0] += ` (${acc.mape}%)`;
    if (acc.within_band_pct !== null) parts.push(`${acc.within_band_pct}% hari omzetnya masuk rentang prediksi`);
    return parts.join(' · ');
  }
  if (acc.saved_since) {
    return `Prediksi mulai disimpan sejak ${formatDate(acc.saved_since)}. Perbandingan dengan omzet sebenarnya muncul setelah ada hari yang sudah lewat.`;
  }
  return '';
});

// Chart omzet harian: garis asli (solid, biru) nyambung ke garis prediksi (putus-putus, merah)
// di titik terakhir data aktual, plus rentang perkiraan (area merah muda) di sisi prediksi.
// "Prediksi lama" (kuning) hanya tampil kalau dinyalakan lewat tombol di atas grafik.
// Legenda digambar sendiri di template (lebih jelas dan bisa diberi nama yang mudah dipahami).
const trendChartData = computed(() => {
  if (!prediction.value) return { labels: [], datasets: [] };

  const history = prediction.value.history || [];
  const preds   = prediction.value.forecast || [];
  const labels  = [...history.map(h => shortDateLabel(h.date)), ...preds.map(p => shortDateLabel(p.date))];

  const historyData = [...history.map(h => h.revenue), ...preds.map(() => null)];

  const bridgeValue = history.length ? history[history.length - 1].revenue : null;
  const blanks = history.map(() => null).slice(0, -1);
  const predData  = [...blanks, bridgeValue, ...preds.map(p => p.predicted_revenue)];
  const upperData = [...blanks, bridgeValue, ...preds.map(p => p.upper_bound)];
  const lowerData = [...blanks, bridgeValue, ...preds.map(p => p.lower_bound)];
  const savedData = [...history.map(h => savedByDate.value[h.date] ?? null), ...preds.map(() => null)];

  const real = isDark.value ? '#60a5fa' : '#2563eb';
  const realFill = isDark.value ? 'rgba(96,165,250,0.14)' : 'rgba(37,99,235,0.09)';
  // 'monotone' menjaga garis tidak melengkung melewati nilai data (mis. dipantulkan di bawah Rp0 saat hari libur).
  const smooth = { cubicInterpolationMode: 'monotone', tension: 0 };

  return {
    labels,
    datasets: [
      { label: 'Batas Atas', data: upperData, borderColor: 'transparent', backgroundColor: 'rgba(217,43,34,0.12)', pointRadius: 0, fill: '+1', ...smooth },
      { label: 'Batas Bawah', data: lowerData, borderColor: 'transparent', backgroundColor: 'rgba(217,43,34,0.12)', pointRadius: 0, fill: false, ...smooth },
      { label: 'Prediksi ke depan', data: predData, borderColor: '#d92b22', backgroundColor: '#d92b22', borderDash: [6, 4], borderWidth: 2, pointRadius: 2.5, fill: false, ...smooth },
      {
        label: 'Prediksi lama', data: savedData, hidden: !showSaved.value,
        borderColor: '#e0a800', backgroundColor: '#e0a800', borderDash: [2, 3], borderWidth: 1.5,
        pointRadius: 3.5, pointStyle: 'rectRot', spanGaps: false, fill: false, tension: 0,
      },
      { label: 'Omzet asli', data: historyData, borderColor: real, backgroundColor: realFill, pointBackgroundColor: real, pointBorderColor: real, borderWidth: 2.25, pointRadius: 2.5, fill: 'origin', ...smooth },
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
  const shown = ['Omzet asli', 'Prediksi ke depan', 'Prediksi lama'];
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        ...tooltipBase(t),
        filter: (item) => shown.includes(item.dataset.label) && item.parsed.y !== null,
        callbacks: {
          label: (ctx) => `${ctx.dataset.label}: ${formatPrice(ctx.parsed.y)}`,
        },
      },
    },
    scales: {
      x: { ticks: { color: t.tick, font: { size: 10 }, maxRotation: 0, autoSkip: true, maxTicksLimit: 8 }, grid: { color: t.grid } },
      y: { beginAtZero: true, grace: '8%', ticks: { color: t.tick, font: { size: 10 }, callback: (v) => formatPriceShort(v) }, grid: { color: t.grid } },
    },
  };
});

function formatPriceShort(value) {
  if (value >= 1_000_000_000) return `Rp ${(value / 1_000_000_000).toFixed(1)}M`;
  if (value >= 1_000_000) return `Rp ${Math.round(value / 1_000_000)}jt`;
  if (value >= 1_000) return `Rp ${Math.round(value / 1_000)}rb`;
  return `Rp ${value}`;
}

// Tanggal LOKAL (bukan toISOString yang UTC): antara 00.00 dan 07.00 WIB, versi UTC masih "kemarin".
function ymd(d) { return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; }
function today() { return ymd(new Date()); }
function daysAgo(n) { const d = new Date(); d.setDate(d.getDate() - n); return ymd(d); }
function startOfMonth() { const d = new Date(); d.setDate(1); return ymd(d); }
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
/* ── Ringkasan periode (judul + filter tanggal) ─────────────────── */
.period { display: flex; flex-direction: column; gap: 1.1rem; min-width: 0; }
.period-head {
  display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between; gap: 0.9rem 1.5rem;
}
.period-title {
  margin: 0 0 0.2rem; font-family: var(--font-display); font-size: 1.15rem; font-weight: 400;
  letter-spacing: 0; color: var(--text);
}
.period-sub { margin: 0; font-size: 0.8rem; color: var(--text-faint); font-family: var(--font-body); }

.filter-bar { display: flex; flex-wrap: wrap; align-items: center; gap: 0.75rem 1rem; }
.date-inputs {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.4rem 0.85rem; background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
}
.date-field { display: flex; flex-direction: column; gap: 0.1rem; }
.date-label { font-size: 0.75rem; font-family: var(--font-body); color: var(--text-faint); }
.date-input {
  background: transparent; border: none; outline: none; color: var(--text);
  font-size: 0.85rem; font-family: var(--font-body); cursor: pointer; min-width: 125px;
}
.date-input::-webkit-calendar-picker-indicator { filter: invert(0.4); cursor: pointer; }
.date-sep { color: var(--text-faint); font-size: 0.9rem; }

.shortcuts { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.shortcut-btn {
  min-height: 36px; padding: 0.35rem 1rem; border-radius: 10px;
  border: 1px solid rgb(var(--ink) / 0.1); background: var(--surface); color: var(--text-dim);
  font-family: var(--font-body); font-size: 0.8125rem; font-weight: 600; cursor: pointer; transition: all 0.18s ease;
}
.shortcut-btn:hover { border-color: rgb(var(--ink) / 0.25); color: var(--text-2); }
.shortcut-btn.active { background: var(--accent); border-color: var(--accent); color: var(--on-accent); }

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

/* ── KPI: empat kartu sama besar, satu gaya ──────────────────────────
   Aksen merah brand hanya di kartu Revenue (metrik #1); sisanya netral. */
.kpi-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0.9rem; }
@media (max-width: 1000px) { .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 520px) { .kpi-grid { grid-template-columns: 1fr; } }

.stat-card {
  position: relative; overflow: hidden; min-width: 0;
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--r-lg);
  padding: 1.1rem 1.25rem; box-shadow: var(--shadow-card);
  transition: border-color 0.2s;
}
.stat-card:hover { border-color: var(--border-strong); }
.stat-card--primary::before {
  content: ''; position: absolute; top: 0; bottom: 0; left: 0; width: 4px; background: var(--accent);
}
.stat-card.accent-purple::after {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: var(--purple-soft);
}
.stat-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 0.5rem; margin-bottom: 0.55rem; }
.stat-label { font-family: var(--font-body); font-size: 0.85rem; font-weight: 600; color: var(--text-dim); min-width: 0; }
.stat-value {
  font-family: var(--font-display); font-variant-numeric: tabular-nums;
  font-size: 1.6rem; font-weight: 700; color: var(--text); line-height: 1.15; margin-bottom: 0.4rem; letter-spacing: -0.02em;
  overflow-wrap: anywhere;
}
.accent-purple .stat-value { color: var(--purple-soft); }
.stat-value-text { font-family: var(--font-body); font-size: 1.05rem; line-height: 1.35; }
.stat-sub { display: flex; flex-wrap: wrap; align-items: center; gap: 0.4rem 0.6rem; font-size: 0.78rem; color: var(--text-faint); font-family: var(--font-body); }

.trend-pill {
  display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.1rem 0.5rem; border-radius: 100px;
  font-family: var(--font-body); font-size: 0.75rem; font-weight: 700;
}
.trend-up   { background: rgba(34,197,94,0.1);  color: var(--green-soft); border: 1px solid rgba(34,197,94,0.25); }
.trend-down { background: rgba(248,113,113,0.1); color: var(--red-soft); border: 1px solid rgba(248,113,113,0.25); }

.stat-badge {
  font-size: 0.78rem; font-family: var(--font-body); padding: 0.1rem 0.5rem; border-radius: 100px;
  border: 1px solid rgb(var(--ink) / 0.1); color: var(--text-faint); white-space: nowrap; flex-shrink: 0;
}
.badge-green { border-color: rgba(34,197,94,0.3); color: var(--green-soft); background: rgba(34,197,94,0.08); }

/* ── Table Card ──────────────────────────────────────────────────── */
.table-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  margin-bottom: 0;
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
  padding: 2rem 1.5rem;
  text-align: center;
}
.empty-icon { font-size: 1.6rem; margin-bottom: 0.5rem; }
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
  background: linear-gradient(90deg, var(--accent), var(--red-soft));
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
.predict-section {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--r-lg);
  box-shadow: var(--shadow-card); padding: 1.4rem 1.6rem; min-width: 0;
}
.predict-header {
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem 1.5rem; margin-bottom: 1.1rem;
}
.predict-title-block { flex: 1; min-width: 220px; }

/* Angka besar di kiri atas panel: inti prediksi terbaca tanpa mencari */
.predict-summary { display: flex; align-items: center; gap: 0.9rem; padding-left: 1.1rem; border-left: 2px solid var(--line-accent); }
.predict-inline-text { display: flex; flex-direction: column; gap: 0.1rem; }
.predict-inline-label { font-family: var(--font-body); font-size: 0.78rem; color: var(--text-faint); }
.predict-inline-value { font-family: var(--font-display); font-size: 1.35rem; font-weight: 400; color: var(--text); font-variant-numeric: tabular-nums; }
.predict-conf {
  padding: 0.15rem 0.65rem; border-radius: 999px; font-size: 0.75rem; font-weight: 700; white-space: nowrap;
  border: 1px solid rgb(var(--ink) / 0.14); color: var(--text-dim);
}
.predict-conf.is-rendah { color: var(--amber-soft); border-color: color-mix(in srgb, var(--amber-soft) 45%, transparent); background: color-mix(in srgb, var(--amber-soft) 8%, transparent); }
.predict-conf.is-sedang { color: var(--text-2); }
.predict-conf.is-tinggi { color: var(--green-soft); border-color: color-mix(in srgb, var(--green-soft) 45%, transparent); background: color-mix(in srgb, var(--green-soft) 8%, transparent); }

.retrain-btn {
  padding: 0.45rem 1rem; border-radius: 8px; border: 1px solid var(--line-accent); background: var(--tint-accent);
  color: var(--red-soft); font-family: var(--font-body); font-size: 0.8125rem; cursor: pointer; white-space: nowrap; transition: all 0.18s ease;
}
.retrain-btn:hover:not(:disabled) { background: color-mix(in srgb, var(--accent) 20%, transparent); }
.retrain-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.predict-notice {
  margin: -0.4rem 0 1rem; padding: 0.55rem 0.8rem; font-size: 0.8125rem; font-family: var(--font-body);
  color: var(--text-dim); border: 1px solid var(--border-strong); border-radius: 8px;
}

.predict-tabs { display: inline-flex; gap: 4px; padding: 3px; margin-bottom: 1rem; border-radius: 10px; background: var(--border); }
.predict-tab { min-height: 36px; padding: 0 1.1rem; border: 0; border-radius: 8px; background: transparent; color: var(--text-dim); font-size: 0.8125rem; cursor: pointer; }
.predict-tab[aria-selected="true"] { background: var(--surface); color: var(--text); font-weight: 600; box-shadow: 0 1px 2px rgb(0 0 0 / 0.08); }
.predict-tab:focus-visible { outline: 2px solid var(--red-soft); outline-offset: 2px; }

.predict-panel { display: flex; flex-direction: column; gap: 1rem; min-width: 0; }

.chart-card { background: var(--surface-2); border: 1px solid var(--border); border-radius: 12px; padding: 1.1rem 1.2rem; min-width: 0; overflow: hidden; }
.chart-toolbar { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.6rem; margin-bottom: 0.7rem; }
.chart-title { font-family: var(--font-body); font-size: 0.85rem; font-weight: 600; color: var(--text); margin: 0; }
.saved-toggle {
  display: inline-flex; align-items: center; gap: 0.45rem; min-height: 32px; padding: 0.25rem 0.8rem; border-radius: 999px;
  border: 1px solid var(--border-strong); background: transparent; color: var(--text-dim);
  font-family: var(--font-body); font-size: 0.78rem; cursor: pointer; transition: all 0.15s ease;
}
.saved-toggle:hover { color: var(--text); border-color: rgb(var(--ink) / 0.3); }
.saved-toggle[aria-pressed="true"] { color: var(--text); background: color-mix(in srgb, #e0a800 14%, transparent); border-color: color-mix(in srgb, #e0a800 55%, transparent); }
.saved-toggle-dot { width: 8px; height: 8px; background: #e0a800; transform: rotate(45deg); }

.chart-legend { display: flex; flex-wrap: wrap; gap: 0.35rem 1.1rem; list-style: none; margin: 0 0 0.75rem; padding: 0; font-size: 0.78rem; color: var(--text-dim); }
.chart-legend li { display: inline-flex; align-items: center; gap: 0.45rem; }
.lg { display: inline-block; flex-shrink: 0; }
.lg-real  { width: 16px; height: 3px; border-radius: 2px; background: #2563eb; }
.lg-pred  { width: 16px; height: 0; border-top: 2.5px dashed #d92b22; }
.lg-band  { width: 14px; height: 10px; border-radius: 3px; background: rgba(217,43,34,0.18); }
.lg-saved { width: 8px; height: 8px; background: #e0a800; transform: rotate(45deg); }
html[data-admin-theme='dark'] .lg-real { background: #60a5fa; }

.chart-wrap { height: 300px; width: 100%; position: relative; overflow: hidden; }
@media (min-width: 1100px) { .chart-wrap { height: 340px; } }
.chart-caption--hint { margin-top: 0.2rem; color: var(--text-faint); }

/* ── Error banner & retry ───────────────────────────────────────── */
.error-banner {
  display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap;
  padding: 0.9rem 1.1rem; border-radius: var(--r-md); background: var(--tint-accent); border: 1px solid var(--line-accent);
}
.error-text { flex: 1 1 260px; min-width: 0; }
.error-title { margin: 0 0 0.2rem; font-size: 0.85rem; font-weight: 600; color: var(--red-soft); }
.error-msg { margin: 0; font-size: 0.78rem; line-height: 1.5; color: var(--text-2); }
.retry-btn {
  min-height: 36px; padding: 0.45rem 1rem; border-radius: 8px; flex-shrink: 0; background: transparent;
  border: 1px solid var(--line-accent); color: var(--red-soft); font-family: var(--font-body); font-size: 0.78rem; cursor: pointer; transition: background 0.15s;
}
.retry-btn:hover { background: var(--tint-accent); }

/* ── Tabel & detail kecil ───────────────────────────────────────── */
.date-input { color-scheme: inherit; }
.date-input:focus-visible { outline: 2px solid var(--ring); outline-offset: 2px; border-radius: 4px; }
.refresh-icon.spinning { animation: spin 0.9s linear infinite; }
.qty-val, .td-revenue, .bar-pct { font-variant-numeric: tabular-nums; }
.menu-table th { padding-block: 0.85rem; }
.th-rank { width: 56px; }
.menu-row:hover { background: var(--surface-hover); }
.bar-track { min-width: 60px; }

/* ── Responsif ──────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .period-head { align-items: stretch; }
  .filter-bar { width: 100%; flex-direction: column; align-items: stretch; }
  .date-inputs { width: 100%; }
  .date-field { flex: 1; min-width: 0; }
  .date-input { width: 100%; min-width: 0; min-height: 36px; }
  .shortcuts { width: 100%; display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.4rem; }
  .shortcut-btn { padding-inline: 0.3rem; text-align: center; }
  .table-header { padding: 1.1rem; flex-direction: column; gap: 0.25rem; }
  .predict-section { padding: 1.1rem; }
  .predict-header { flex-direction: column; align-items: stretch; }
  .predict-summary { border-left: none; padding-left: 0; }
  .retrain-btn { width: 100%; min-height: 40px; }
  .predict-tabs { display: flex; }
  .predict-tab { flex: 1; padding: 0; }
  .chart-card { padding: 0.9rem; }
  .chart-wrap { height: 240px; }
}
@media (max-width: 640px) {
  .menu-table { min-width: 0; }
  .menu-table th, .menu-table td { padding: 0.75rem 0.7rem; }
  .th-bar, .td-bar { display: none; }
  .th-rank, .td-rank { width: 40px; padding-right: 0; }
  .td-name { word-break: break-word; }
}
@media (max-width: 480px) {
  .shortcuts { grid-template-columns: repeat(2, 1fr); }
  .qty-unit { display: none; }
}
@media (pointer: coarse) {
  .shortcut-btn, .retrain-btn, .saved-toggle { min-height: 44px; }
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
.view-toggle-btn.active { background: var(--accent); color: var(--on-accent); }

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

/* Ritme vertikal dipegang oleh .adm-page (gap), bukan margin tiap blok */
.adm-page.dashboard-root > * { margin-bottom: 0; }
</style>
