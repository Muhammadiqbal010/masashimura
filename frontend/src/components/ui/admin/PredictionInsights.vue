<template>
  <div class="pi-root">
    <!-- RINGKASAN: KEYAKINAN + TREN -->
    <div class="pi-summary">
      <div class="pi-card pi-confidence">
        <div class="pi-card-head">
          <span class="pi-label">Tingkat keyakinan prediksi</span>
          <span class="pi-level">
            <span
              class="pi-bars"
              role="img"
              :aria-label="`Keyakinan ${levelLabel}`"
            >
              <i v-for="n in 3" :key="n" :class="{ on: n <= levelIndex }"></i>
            </span>
            {{ levelLabel }}
          </span>
        </div>
        <p class="pi-text">{{ confidence.message || 'Belum ada keterangan keyakinan dari server.' }}</p>
        <p v-if="confidence.history_days" class="pi-meta">
          Berdasarkan {{ confidence.history_days }} hari data historis
          <template v-if="dataRangeLabel"> · {{ dataRangeLabel }}</template>
        </p>
      </div>

      <div class="pi-card pi-trend">
        <span class="pi-label">Tren vs {{ historyWindowLabel }}</span>
        <div class="pi-trend-value" :class="trendTone">
          <span class="pi-trend-arrow" aria-hidden="true">{{ trendArrow }}</span>
          <span>{{ trendLabel }}</span>
          <span v-if="hasTrendPct" class="pi-trend-pct">{{ trendPctLabel }}</span>
        </div>
        <p v-if="trend.forecast_average_daily" class="pi-meta">
          Rata-rata harian prediksi {{ rupiah(trend.forecast_average_daily) }}
          <template v-if="trend.history_average_daily">
            · historis {{ rupiah(trend.history_average_daily) }}
          </template>
        </p>
        <p class="pi-meta">Dihitung dari hari buka saja.</p>
      </div>
    </div>

    <!-- TABEL RINCIAN HARIAN -->
    <div class="pi-card pi-table-card">
      <h4 class="pi-title">Rincian Prediksi per Hari</h4>
      <div class="pi-table-scroll">
        <table class="pi-table">
          <thead>
            <tr>
              <th>Hari</th>
              <th class="num">Prediksi</th>
              <th class="num">Rentang perkiraan</th>
              <th>Keyakinan</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in rows" :key="row.date" :class="{ closed: row.closed }">
              <td>
                <span class="pi-day">{{ row.dayName }}</span>
                <span class="pi-date">{{ row.dateLabel }}</span>
              </td>
              <template v-if="row.closed">
                <td class="num pi-muted">—</td>
                <td class="num pi-muted">Libur rutin</td>
                <td class="pi-muted">—</td>
              </template>
              <template v-else>
                <td class="num pi-strong">{{ rupiah(row.predicted) }}</td>
                <td class="num pi-range">{{ rupiah(row.lower) }} – {{ rupiah(row.upper) }}</td>
                <td>
                  <span class="pi-chip" :title="row.sampleHint">{{ row.confidenceLabel }}</span>
                </td>
              </template>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="pi-meta pi-caption">
        Rentang adalah perkiraan batas bawah dan atas, bukan jaminan hasil penjualan.
      </p>
    </div>

    <!-- DETAIL METODE & EVALUASI -->
    <details class="pi-card pi-details">
      <summary>Detail metode &amp; evaluasi model</summary>

      <div class="pi-details-body">
        <p class="pi-text">
          Metode yang dipakai saat ini: <strong>{{ methodLabel }}</strong>.
          <template v-if="prediction.selection_reason"> {{ prediction.selection_reason }}</template>
        </p>
        <p v-if="trainedAtLabel" class="pi-meta">Terakhir dilatih dan dievaluasi: {{ trainedAtLabel }}</p>

        <p v-if="metricsMismatch" class="pi-note">
          Angka evaluasi di bawah berasal dari pelatihan sebelumnya dan belum mencerminkan
          metode yang sedang dipakai. Latih ulang model untuk memperbarui.
        </p>

        <div v-if="metricRows.length" class="pi-table-scroll">
          <table class="pi-table">
            <thead>
              <tr>
                <th>Model</th>
                <th class="num">MAE</th>
                <th class="num">RMSE</th>
                <th class="num">MAPE</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in metricRows" :key="m.key">
                <td>
                  {{ m.label }}
                  <span v-if="m.active" class="pi-chip pi-chip-active">dipakai</span>
                </td>
                <td class="num">{{ m.mae }}</td>
                <td class="num">{{ m.rmse }}</td>
                <td class="num">{{ m.mape }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else class="pi-meta">
          Belum ada evaluasi tersimpan. Klik Latih Ulang untuk menjalankannya (butuh minimal 14 hari data).
        </p>

        <p v-if="metricRows.length" class="pi-meta pi-caption">
          <template v-if="testDays">Diuji pada {{ testDays }} hari buka terakhir (backtest walk-forward). </template>
          MAE = rata-rata selisih absolut, RMSE = selisih kuadrat (lebih sensitif ke error besar),
          MAPE = selisih dalam persen. Semakin kecil semakin baik.
        </p>
      </div>
    </details>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { formatRupiah } from '@/utils/price';

const props = defineProps({
  // Respons GET /api/prediction/revenue/
  prediction: { type: Object, required: true },
});

const rupiah = (n) => formatRupiah(Math.round(Number(n) || 0));

const shortDate = (iso) =>
  new Date(`${iso}T00:00:00`).toLocaleDateString('id-ID', { day: '2-digit', month: 'short' });

// ── Keyakinan ─────────────────────────────────────────────────────────────
const LEVELS = { rendah: 1, sedang: 2, tinggi: 3 };
const confidence = computed(() => props.prediction.confidence || {});
const levelIndex = computed(() => LEVELS[confidence.value.level] || 0);
const levelLabel = computed(() => {
  const l = confidence.value.level;
  return l ? l.charAt(0).toUpperCase() + l.slice(1) : 'Tidak diketahui';
});

const dataRangeLabel = computed(() => {
  const r = props.prediction.data_range;
  return r?.start && r?.end ? `${shortDate(r.start)} – ${shortDate(r.end)}` : '';
});

// ── Tren ──────────────────────────────────────────────────────────────────
const trend = computed(() => props.prediction.trend || {});
const TREND_LABELS = { naik: 'Naik', turun: 'Turun', stabil: 'Stabil', tidak_diketahui: 'Belum diketahui' };
const TREND_ARROWS = { naik: '▲', turun: '▼', stabil: '▬', tidak_diketahui: '–' };
const trendLabel = computed(() => TREND_LABELS[trend.value.direction] || 'Belum diketahui');
const trendArrow = computed(() => TREND_ARROWS[trend.value.direction] || '–');
const trendTone = computed(() => `tone-${trend.value.direction || 'tidak_diketahui'}`);
const hasTrendPct = computed(
  () => trend.value.direction && trend.value.direction !== 'tidak_diketahui'
    && typeof trend.value.change_pct === 'number',
);
const trendPctLabel = computed(() => {
  const v = trend.value.change_pct;
  const sign = v > 0 ? '+' : '';
  return `${sign}${v.toLocaleString('id-ID', { maximumFractionDigits: 1 })}%`;
});
const historyWindowLabel = computed(() => {
  const h = (props.prediction.history || []).length;
  return h ? `${h} hari terakhir` : 'riwayat terakhir';
});

// ── Tabel harian ──────────────────────────────────────────────────────────
const rows = computed(() =>
  (props.prediction.forecast || []).map((f) => ({
    date: f.date,
    dayName: f.day_name,
    dateLabel: shortDate(f.date),
    closed: !!f.is_regular_closed_day,
    predicted: f.predicted_revenue,
    lower: f.lower_bound,
    upper: f.upper_bound,
    confidenceLabel: f.confidence ? f.confidence.charAt(0).toUpperCase() + f.confidence.slice(1) : '—',
    sampleHint: f.n_samples ? `Berdasarkan ${f.n_samples} hari ${f.day_name} terakhir` : '',
  })),
);

// ── Metode & evaluasi ─────────────────────────────────────────────────────
const METHOD_LABELS = {
  baseline: 'Baseline (median berbobot per hari dalam seminggu)',
  random_forest: 'Random Forest (fitur kalender)',
  ridge_regression: 'Ridge Regression',
};
const MODEL_SHORT = {
  baseline: 'Baseline',
  random_forest: 'Random Forest',
  ridge_regression: 'Ridge Regression',
};
const methodKey = computed(() => props.prediction.best_model || props.prediction.method);
const methodLabel = computed(() => METHOD_LABELS[methodKey.value] || methodKey.value || '—');

const trainedAtLabel = computed(() => {
  const t = props.prediction.trained_at;
  return t ? new Date(t).toLocaleString('id-ID', { dateStyle: 'medium', timeStyle: 'short' }) : '';
});

const metrics = computed(() => props.prediction.metrics || {});
const metricRows = computed(() =>
  Object.entries(metrics.value).map(([key, m]) => ({
    key,
    label: MODEL_SHORT[key] || key,
    active: key === methodKey.value,
    mae: typeof m.mae === 'number' ? rupiah(m.mae) : '—',
    rmse: typeof m.rmse === 'number' ? rupiah(m.rmse) : '—',
    mape: typeof m.mape === 'number'
      ? `${m.mape.toLocaleString('id-ID', { maximumFractionDigits: 1 })}%`
      : '—',
  })),
);
const testDays = computed(() => {
  const first = Object.values(metrics.value).find((m) => m && m.n_test_days);
  return first ? first.n_test_days : null;
});
// Metrik tersimpan tapi tidak memuat metode yang sedang aktif → kemungkinan
// metadata dari pelatihan lama (mis. Ridge + RF) sementara forecast pakai baseline.
const metricsMismatch = computed(
  () => metricRows.value.length > 0 && !metricRows.value.some((m) => m.active),
);
</script>

<style scoped>
.pi-root {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  margin-top: 1.25rem;
  min-width: 0;
}

.pi-card {
  background: var(--surface-2);
  border: 1px solid rgb(var(--ink) / 0.05);
  border-radius: 12px;
  padding: 1.1rem 1.2rem;
  min-width: 0;
}

.pi-summary {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 1.25rem;
  min-width: 0;
}

.pi-label {
  font-family: 'Manrope', system-ui, sans-serif;
  font-size: 0.75rem;
  letter-spacing: -0.01em;
  color: var(--text-2);
}
.pi-title {
  font-family: 'Manrope', system-ui, sans-serif;
  font-size: 0.75rem;
  letter-spacing: -0.01em;
  color: var(--text-2);
  margin: 0 0 1rem 0;
}

.pi-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 0.65rem;
}

.pi-level {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-family: 'Inter', sans-serif;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text);
}
.pi-bars { display: inline-flex; align-items: flex-end; gap: 3px; }
.pi-bars i {
  display: block;
  width: 5px;
  border-radius: 1px;
  background: rgb(var(--ink) / 0.14);
}
.pi-bars i:nth-child(1) { height: 7px; }
.pi-bars i:nth-child(2) { height: 11px; }
.pi-bars i:nth-child(3) { height: 15px; }
.pi-bars i.on { background: var(--text-2); }

.pi-text {
  font-family: 'Inter', sans-serif;
  font-size: 0.78rem;
  line-height: 1.55;
  color: var(--text-2);
  margin: 0;
}
.pi-meta {
  font-family: 'Inter', sans-serif;
  font-size: 0.7rem;
  color: var(--text-faint);
  margin: 0.5rem 0 0;
}

/* Tren */
.pi-trend-value {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  margin-top: 0.6rem;
  font-family: 'Inter', sans-serif;
  font-size: 1.35rem;
  font-weight: 600;
  color: var(--text);
}
.pi-trend-arrow { font-size: 0.8rem; }
.pi-trend-pct {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-dim);
}
.tone-naik .pi-trend-arrow { color: var(--green-soft); }
.tone-turun .pi-trend-arrow { color: var(--amber-soft); }
.tone-stabil .pi-trend-arrow,
.tone-tidak_diketahui .pi-trend-arrow { color: var(--text-faint); }

/* Tabel */
.pi-table-scroll { overflow-x: auto; max-width: 100%; }
.pi-table {
  width: 100%;
  border-collapse: collapse;
  font-family: 'Inter', sans-serif;
  font-size: 0.78rem;
  font-variant-numeric: tabular-nums;
}
.pi-table th {
  text-align: left;
  font-size: 0.72rem;
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-faint);
  padding: 0 0.75rem 0.55rem;
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}
.pi-table td {
  padding: 0.6rem 0.75rem;
  color: var(--text-2);
  border-bottom: 1px solid rgb(var(--ink) / 0.04);
  white-space: nowrap;
}
.pi-table tbody tr:last-child td { border-bottom: none; }
.pi-table .num { text-align: right; }
.pi-table th.num { text-align: right; }
.pi-table tr.closed td { color: var(--text-faint); }
.pi-day { color: var(--text); margin-right: 0.5rem; }
.pi-date { color: var(--text-faint); font-size: 0.7rem; }
.pi-strong { color: var(--text); font-weight: 600; }
.pi-range, .pi-muted { color: var(--text-dim); }
.pi-caption { margin-top: 0.85rem; }

.pi-chip {
  display: inline-block;
  padding: 0.1rem 0.5rem;
  border: 1px solid var(--border-strong);
  border-radius: 999px;
  font-size: 0.72rem;
  color: var(--text-dim);
}
.pi-chip-active { margin-left: 0.4rem; color: var(--text-2); }

/* Detail */
.pi-details summary {
  cursor: pointer;
  list-style: none;
  font-family: 'Manrope', system-ui, sans-serif;
  font-size: 0.75rem;
  letter-spacing: -0.01em;
  color: var(--text-2);
}
.pi-details summary::-webkit-details-marker { display: none; }
.pi-details summary::before { content: '▸'; display: inline-block; margin-right: 0.5rem; color: var(--text-faint); }
.pi-details[open] summary::before { content: '▾'; }
.pi-details-body { margin-top: 1rem; display: flex; flex-direction: column; gap: 0.85rem; }
.pi-text strong { color: var(--text); font-weight: 600; }
.pi-note {
  font-family: 'Inter', sans-serif;
  font-size: 0.72rem;
  line-height: 1.5;
  color: var(--text-dim);
  margin: 0;
  padding: 0.55rem 0.8rem;
  border: 1px solid var(--border-strong);
  border-radius: 8px;
}

@media (max-width: 768px) {
  .pi-summary { grid-template-columns: 1fr; }
  .pi-card { padding: 1rem; }
}
</style>