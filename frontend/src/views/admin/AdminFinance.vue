<template>
  <div class="fr-root">

    <!-- ── PAGE HEADER + TOOLBAR ──────────────────────────────────── -->
    <div class="fr-header">
      <div class="fr-heading">
        <p class="fr-eyebrow">Masashimura · Keuangan</p>
        <h1 class="fr-title">Laporan Keuangan</h1>
        <p class="fr-subtitle">{{ viewModeLabel }}</p>
      </div>

      <div class="fr-toolbar">
        <div class="mode-switch">
          <button
            v-for="m in viewModes"
            :key="m.key"
            @click="switchMode(m.key)"
            class="mode-btn"
            :class="{ active: viewMode === m.key }"
          >
            {{ m.label }}
          </button>
        </div>

        <!-- HARIAN -->
        <div v-if="viewMode === 'daily'" class="date-nav">
          <button class="nav-btn" @click="changeDate(-1)" aria-label="Hari sebelumnya">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 18l-6-6 6-6"/></svg>
          </button>
          <span class="nav-current">{{ targetDateString }}</span>
          <button class="nav-btn" @click="changeDate(1)" aria-label="Hari berikutnya">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 18l6-6-6-6"/></svg>
          </button>
        </div>

        <!-- BULANAN -->
        <template v-if="viewMode === 'monthly'">
          <div class="date-nav">
            <button class="nav-btn" @click="changeMonth(-1)" aria-label="Bulan sebelumnya">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 18l-6-6 6-6"/></svg>
            </button>
            <span class="nav-current">{{ monthNames[selectedMonth - 1] }} {{ selectedYear }}</span>
            <button class="nav-btn" @click="changeMonth(1)" aria-label="Bulan berikutnya">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 18l6-6-6-6"/></svg>
            </button>
          </div>
          <select v-model.number="selectedYear" @change="fetchMonthlyData" class="nav-select">
            <option v-for="y in yearsAvailable" :key="y" :value="y">{{ y }}</option>
          </select>
        </template>

        <!-- TAHUNAN -->
        <template v-if="viewMode === 'yearly'">
          <div class="date-nav">
            <button class="nav-btn" @click="changeYear(-1)" aria-label="Tahun sebelumnya">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 18l-6-6 6-6"/></svg>
            </button>
            <span class="nav-current">Tahun {{ selectedYear }}</span>
            <button class="nav-btn" @click="changeYear(1)" aria-label="Tahun berikutnya">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 18l6-6-6-6"/></svg>
            </button>
          </div>
          <select v-model.number="selectedYear" @change="fetchYearlyData" class="nav-select">
            <option v-for="y in yearsAvailable" :key="y" :value="y">{{ y }}</option>
          </select>
        </template>
      </div>
    </div>

    <!-- ── SUMMARY / KPI CARDS ────────────────────────────────────── -->
    <div class="summary-grid">
      <div class="s-card s-green">
        <div class="s-top">
          <span class="s-icon-wrap ic-green">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M23 6l-9.5 9.5-5-5L1 18"/><path d="M17 6h6v6"/></svg>
          </span>
          <span class="s-label">Total Pendapatan</span>
        </div>
        <div class="s-value">Rp {{ formatNumber(summaryCards.revenue) }}</div>
        <div class="s-note">Order lunas terkonfirmasi</div>
      </div>

      <div class="s-card s-amber">
        <div class="s-top">
          <span class="s-icon-wrap ic-amber">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/></svg>
          </span>
          <span class="s-label">Total Pengeluaran</span>
        </div>
        <div class="s-value">Rp {{ formatNumber(summaryCards.expenses) }}</div>
        <div class="s-note">Tunai + QRIS</div>
      </div>

      <div class="s-card s-profit" :class="summaryCards.net_profit >= 0 ? 's-surplus' : 's-defisit'">
        <div class="s-top">
          <span class="s-icon-wrap" :class="summaryCards.net_profit >= 0 ? 'ic-green' : 'ic-red'">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 3v18M5 8l7-5 7 5M5 8v8a2 2 0 002 2h10a2 2 0 002-2V8"/></svg>
          </span>
          <span class="s-label">Laba Bersih</span>
          <span class="s-badge" :class="summaryCards.net_profit >= 0 ? 'badge-up' : 'badge-down'">
            {{ summaryCards.net_profit >= 0 ? '▲ Surplus' : '▼ Defisit' }}
          </span>
        </div>
        <div class="s-value" :class="summaryCards.net_profit >= 0 ? 'val-green' : 'val-red'">
          Rp {{ formatNumber(summaryCards.net_profit) }}
        </div>
        <div class="s-note">Pendapatan dikurangi pengeluaran</div>
      </div>
    </div>

    <!-- ── BODY: MAIN CONTENT + SIDEBAR ───────────────────────────── -->
    <div class="fr-shell">

      <!-- ═══ MAIN COLUMN ═══ -->
      <main class="fr-main">

        <!-- HARIAN: log pengeluaran -->
        <div v-if="viewMode === 'daily'" class="card table-card">
          <div class="card-head border-b">
            <div>
              <p class="card-eyebrow">Rincian Hari Ini</p>
              <h3 class="card-title">Log Pengeluaran — {{ targetDateString }}</h3>
            </div>
            <span class="card-head-meta">{{ dailyExpensesList.length }} entri</span>
          </div>
          <div class="table-scroll">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Keterangan</th>
                  <th>Metode</th>
                  <th class="th-right">Nominal</th>
                  <th class="th-center">Aksi</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="exp in dailyExpensesList" :key="exp.id" class="data-row" :class="{ 'row-editing': editingId === exp.id }">
                  <td class="td-desc">{{ exp.description }}</td>
                  <td class="td-method">
                    <span class="method-badge" :class="exp.payment_method === 'qris' ? 'mb-qris' : 'mb-cash'">{{ methodLabel(exp.payment_method) }}</span>
                  </td>
                  <td class="td-right td-amount">−Rp {{ formatNumber(exp.amount) }}</td>
                  <td class="td-center">
                    <div class="row-actions">
                      <button @click="startEdit(exp)" class="edit-btn">Edit</button>
                      <button @click="askDelete(exp)" class="delete-btn">Hapus</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="!dailyExpensesList.length">
                  <td colspan="4" class="empty-cell">
                    <div class="empty-icon">📋</div>
                    <p>Belum ada pengeluaran hari ini</p>
                  </td>
                </tr>
              </tbody>
              <tfoot v-if="dailyExpensesList.length">
                <tr class="total-row">
                  <td>Total Pengeluaran</td>
                  <td></td>
                  <td class="td-right td-exp">Rp {{ formatNumber(summaryCards.expenses) }}</td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        <!-- BULANAN / TAHUNAN: chart + table -->
        <template v-else>
          <div class="card chart-card">
            <div class="card-head">
              <p class="card-eyebrow">Visualisasi</p>
              <h3 class="card-title">
                {{ viewMode === 'monthly'
                  ? `Pendapatan & Pengeluaran Per Hari — ${monthNames[selectedMonth - 1]} ${selectedYear}`
                  : `Pendapatan & Pengeluaran Per Bulan — Tahun ${selectedYear}` }}
              </h3>
            </div>

            <div v-if="isLoadingChart" class="chart-loading">
              <div class="spinner-sm"></div>
              <span>Memuat grafik...</span>
            </div>

            <div v-else class="chart-area">
              <div class="bar-chart" :class="{ 'bar-chart-yearly': viewMode === 'yearly' }">
                <div
                  v-for="d in (viewMode === 'monthly' ? monthlyData : yearlyData)"
                  :key="viewMode === 'monthly' ? d.date : d.month"
                  class="bar-col"
                  :title="`${viewMode === 'monthly' ? d.date : d.month_name}\nPendapatan: Rp ${formatNumber(d.revenue)}\nPengeluaran: Rp ${formatNumber(d.expenses)}`"
                >
                  <div class="bar-pair">
                    <div class="bar bar-rev" :style="{ height: barHeight(d.revenue, viewMode === 'monthly' ? maxMonthlyRevenue : maxYearlyRevenue) + 'px' }"></div>
                    <div class="bar bar-exp" :style="{ height: barHeight(d.expenses, viewMode === 'monthly' ? maxMonthlyRevenue : maxYearlyRevenue) * 0.6 + 'px' }"></div>
                  </div>
                  <span class="bar-label">{{ viewMode === 'monthly' ? d.day : d.month_name.slice(0, 3) }}</span>
                </div>
              </div>
              <div class="chart-legend">
                <span class="legend-item"><span class="legend-dot ld-green"></span>Pendapatan</span>
                <span class="legend-item"><span class="legend-dot ld-amber"></span>Pengeluaran</span>
              </div>
            </div>
          </div>

          <div class="card table-card">
            <div class="card-head border-b">
              <p class="card-eyebrow">{{ viewMode === 'monthly' ? 'Detail Harian' : 'Rekap Tahunan' }}</p>
              <h3 class="card-title">{{ viewMode === 'monthly' ? `${monthNames[selectedMonth - 1]} ${selectedYear}` : `Tahun ${selectedYear}` }}</h3>
            </div>
            <div class="table-scroll">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>{{ viewMode === 'monthly' ? 'Tanggal' : 'Bulan' }}</th>
                    <th class="th-right">Pendapatan</th>
                    <th class="th-right">Pengeluaran</th>
                    <th class="th-right">Laba Bersih</th>
                  </tr>
                </thead>
                <tbody v-if="viewMode === 'monthly'">
                  <tr v-for="d in monthlyDataFiltered" :key="d.date" class="data-row">
                    <td class="td-mono">{{ d.date }}</td>
                    <td class="td-right td-rev">{{ d.revenue > 0 ? 'Rp ' + formatNumber(d.revenue) : '—' }}</td>
                    <td class="td-right td-exp">{{ d.expenses > 0 ? 'Rp ' + formatNumber(d.expenses) : '—' }}</td>
                    <td class="td-right" :class="d.net_profit >= 0 ? 'td-pos' : 'td-neg'">Rp {{ formatNumber(d.net_profit) }}</td>
                  </tr>
                  <tr v-if="!monthlyDataFiltered.length">
                    <td colspan="4" class="empty-cell"><p>Tidak ada data untuk bulan ini</p></td>
                  </tr>
                  <tr v-if="monthlyDataFiltered.length" class="total-row">
                    <td>Total Bulan</td>
                    <td class="td-right td-rev">Rp {{ formatNumber(summaryCards.revenue) }}</td>
                    <td class="td-right td-exp">Rp {{ formatNumber(summaryCards.expenses) }}</td>
                    <td class="td-right" :class="summaryCards.net_profit >= 0 ? 'td-pos' : 'td-neg'">Rp {{ formatNumber(summaryCards.net_profit) }}</td>
                  </tr>
                </tbody>
                <tbody v-else>
                  <tr
                    v-for="d in yearlyData"
                    :key="d.month"
                    class="data-row"
                    :class="{ 'row-empty': d.revenue === 0 && d.expenses === 0 }"
                  >
                    <td class="td-month">{{ d.month_name }}</td>
                    <td class="td-right td-rev">{{ d.revenue > 0 ? 'Rp ' + formatNumber(d.revenue) : '—' }}</td>
                    <td class="td-right td-exp">{{ d.expenses > 0 ? 'Rp ' + formatNumber(d.expenses) : '—' }}</td>
                    <td class="td-right" :class="d.net_profit >= 0 ? 'td-pos' : 'td-neg'">
                      {{ (d.revenue > 0 || d.expenses > 0) ? 'Rp ' + formatNumber(d.net_profit) : '—' }}
                    </td>
                  </tr>
                  <tr class="total-row">
                    <td>Total {{ selectedYear }}</td>
                    <td class="td-right td-rev">Rp {{ formatNumber(summaryCards.revenue) }}</td>
                    <td class="td-right td-exp">Rp {{ formatNumber(summaryCards.expenses) }}</td>
                    <td class="td-right" :class="summaryCards.net_profit >= 0 ? 'td-pos' : 'td-neg'">Rp {{ formatNumber(summaryCards.net_profit) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>
      </main>

      <!-- ═══ SIDEBAR ═══ -->
      <aside class="fr-aside">

        <!-- Form Input Pengeluaran (hanya mode harian) -->
        <div v-if="viewMode === 'daily'" ref="formCard" class="card">
          <div class="card-head border-b">
            <p class="card-eyebrow">{{ editingId ? 'Ubah Catatan' : 'Catat Biaya' }}</p>
            <h3 class="card-title">{{ editingId ? 'Edit Pengeluaran' : 'Input Pengeluaran' }}</h3>
          </div>
          <form @submit.prevent="submitExpense" class="expense-form">
            <div class="field">
              <label class="field-label">Keterangan</label>
              <input
                v-model="expenseForm.description"
                type="text"
                placeholder="Beli Daging, Gas 3kg, dll."
                required
                class="field-input"
              />
            </div>
            <div class="field">
              <label class="field-label">Nominal (Rp)</label>
              <input
                v-model.number="expenseForm.amount"
                type="number"
                placeholder="150000"
                required
                min="1"
                class="field-input font-mono"
              />
            </div>
            <div class="field">
              <label class="field-label">Dibayar via</label>
              <div class="method-switch" role="group" aria-label="Metode pembayaran">
                <button
                  v-for="m in paymentMethods"
                  :key="m.key"
                  type="button"
                  class="method-btn"
                  :class="{ active: expenseForm.payment_method === m.key }"
                  :aria-pressed="expenseForm.payment_method === m.key"
                  @click="expenseForm.payment_method = m.key"
                >
                  {{ m.label }}
                </button>
              </div>
            </div>
            <button type="submit" :disabled="isSubmittingExpense" class="submit-btn">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12l7 7 7-7"/></svg>
              {{ isSubmittingExpense ? 'Menyimpan...' : (editingId ? 'Simpan Perubahan' : 'Catat Pengeluaran') }}
            </button>
            <button v-if="editingId" type="button" class="cancel-btn" @click="cancelEdit">Batal edit</button>
          </form>
        </div>

        <!-- Rincian pengeluaran per metode (hanya mode harian) -->
        <div v-if="viewMode === 'daily'" class="card insight-card">
          <div class="card-head border-b">
            <p class="card-eyebrow">Rincian</p>
            <h3 class="card-title">Pengeluaran per Metode</h3>
          </div>
          <div class="insight-body">
            <div class="insight-row">
              <span class="insight-label">Tunai</span>
              <span class="insight-value">Rp {{ formatNumber(expenseByMethod.cash) }}</span>
            </div>
            <div class="insight-row">
              <span class="insight-label">QRIS</span>
              <span class="insight-value">Rp {{ formatNumber(expenseByMethod.qris) }}</span>
            </div>
          </div>
        </div>

        <!-- Ringkasan tambahan (bulanan/tahunan) -->
        <div v-if="viewMode === 'monthly' && monthlyStats" class="card insight-card">
          <div class="card-head border-b">
            <p class="card-eyebrow">Ringkasan</p>
            <h3 class="card-title">Insight Bulan Ini</h3>
          </div>
          <div class="insight-body">
            <div class="insight-row">
              <span class="insight-label">Rata-rata Pendapatan / Hari</span>
              <span class="insight-value">Rp {{ formatNumber(monthlyStats.avgRevenue) }}</span>
            </div>
            <div class="insight-row">
              <span class="insight-label">Hari Terbaik</span>
              <span class="insight-value">{{ monthlyStats.best.date }} · Rp {{ formatNumber(monthlyStats.best.revenue) }}</span>
            </div>
          </div>
        </div>

        <div v-if="viewMode === 'yearly' && yearlyStats" class="card insight-card">
          <div class="card-head border-b">
            <p class="card-eyebrow">Ringkasan</p>
            <h3 class="card-title">Insight Tahun Ini</h3>
          </div>
          <div class="insight-body">
            <div class="insight-row">
              <span class="insight-label">Rata-rata Pendapatan / Bulan</span>
              <span class="insight-value">Rp {{ formatNumber(yearlyStats.avgRevenue) }}</span>
            </div>
            <div class="insight-row">
              <span class="insight-label">Bulan Terbaik</span>
              <span class="insight-value">{{ yearlyStats.best.month_name }} · Rp {{ formatNumber(yearlyStats.best.revenue) }}</span>
            </div>
          </div>
        </div>

        <!-- Export Panel (semua mode) -->
        <div class="card export-card">
          <div class="card-head border-b">
            <p class="card-eyebrow">Unduh Laporan</p>
            <h3 class="card-title">Export Dokumen</h3>
          </div>

          <div class="export-body">
            <div class="export-toggle">
              <button @click="exportMode = 'monthly'" class="toggle-btn" :class="{ active: exportMode === 'monthly' }">Bulanan</button>
              <button @click="exportMode = 'yearly'"  class="toggle-btn" :class="{ active: exportMode === 'yearly'  }">Tahunan</button>
            </div>

            <div class="export-controls">
              <select v-if="exportMode === 'monthly'" v-model.number="exportMonth" class="nav-select nav-select-block">
                <option v-for="(name, idx) in monthNames" :key="idx" :value="idx + 1">{{ name }}</option>
              </select>
              <select v-model.number="exportYear" class="nav-select nav-select-block">
                <option v-for="y in yearsAvailable" :key="y" :value="y">{{ y }}</option>
              </select>
            </div>

            <p class="export-period-label">
              Periode: <span class="period-highlight">{{ exportMode === 'monthly' ? `${monthNames[exportMonth - 1]} ${exportYear}` : `Tahun ${exportYear}` }}</span>
            </p>

            <div class="export-btns">
              <button @click="exportDocument('excel')" :disabled="isExporting" class="export-btn btn-excel">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
                {{ isExporting ? 'Mengunduh...' : 'Excel' }}
              </button>
              <button @click="exportDocument('pdf')" :disabled="isExporting" class="export-btn btn-pdf">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
                {{ isExporting ? 'Mengunduh...' : 'PDF' }}
              </button>
            </div>
          </div>
        </div>

      </aside>
    </div>

    <!-- ── KONFIRMASI HAPUS ───────────────────────────────────────── -->
    <div v-if="deleteTarget" class="modal-backdrop" @click.self="closeDelete" @keydown.esc="closeDelete">
      <div class="modal" role="alertdialog" aria-modal="true" aria-labelledby="del-title" aria-describedby="del-desc">
        <div class="modal-icon">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M3 6h18M8 6V4a1 1 0 011-1h6a1 1 0 011 1v2M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6M10 11v6M14 11v6"/></svg>
        </div>
        <h3 id="del-title" class="modal-title">Hapus pengeluaran ini?</h3>
        <p id="del-desc" class="modal-text">
          <strong>{{ deleteTarget.description }}</strong> senilai Rp {{ formatNumber(deleteTarget.amount) }}
          ({{ methodLabel(deleteTarget.payment_method) }}) akan dihapus dari buku kas dan tidak bisa dikembalikan.
        </p>
        <div class="modal-actions">
          <button ref="cancelDeleteBtn" type="button" class="modal-cancel" @click="closeDelete">Batal</button>
          <button type="button" class="modal-confirm" :disabled="isDeleting" @click="confirmDelete">
            {{ isDeleting ? 'Menghapus...' : 'Hapus pengeluaran' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from "vue";
import apiClient from "@/api/client";
import { toast } from "vue-sonner";

const monthNames = ["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"];
const viewModes  = [{ key: "daily", label: "Harian" }, { key: "monthly", label: "Bulanan" }, { key: "yearly", label: "Tahunan" }];

const viewMode       = ref("daily");
const currentDate    = ref(new Date());
const selectedMonth  = ref(new Date().getMonth() + 1);
const selectedYear   = ref(new Date().getFullYear());
const yearsAvailable = ref([new Date().getFullYear()]);

const financialSummary    = ref({ revenue: 0, expenses: 0, net_profit: 0 });
const dailyExpensesList   = ref([]);
const monthlyData         = ref([]);
const yearlyData          = ref([]);
const isLoadingChart      = ref(false);
const isSubmittingExpense = ref(false);
const isExporting         = ref(false);
const expenseForm         = ref({ description: "", amount: null, payment_method: "cash" });
const editingId           = ref(null);
const formCard            = ref(null);

const exportMode  = ref("monthly");
const exportMonth = ref(new Date().getMonth() + 1);
const exportYear  = ref(new Date().getFullYear());

const paymentMethods = [{ key: "cash", label: "Tunai" }, { key: "qris", label: "QRIS" }];
const methodLabel    = (m) => (m === "qris" ? "QRIS" : "Tunai");

// Rincian pengeluaran harian per metode (dihitung dari daftar yang sudah dimuat)
const expenseByMethod = computed(() => {
  const sum = (m) => dailyExpensesList.value
    .filter((e) => (e.payment_method || "cash") === m)
    .reduce((a, e) => a + Number(e.amount || 0), 0);
  return { cash: sum("cash"), qris: sum("qris") };
});

const targetDateString = computed(() => {
  const d = currentDate.value;
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
});
const viewModeLabel = computed(() => {
  if (viewMode.value === "daily")   return `Per Tanggal — ${targetDateString.value}`;
  if (viewMode.value === "monthly") return `Per Hari — ${monthNames[selectedMonth.value - 1]} ${selectedYear.value}`;
  return `Per Bulan — Tahun ${selectedYear.value}`;
});
const summaryCards = computed(() => {
  if (viewMode.value === "daily") return financialSummary.value;
  const src = viewMode.value === "monthly" ? monthlyData.value : yearlyData.value;
  const rev = src.reduce((a, d) => a + (d.revenue  || 0), 0);
  const exp = src.reduce((a, d) => a + (d.expenses || 0), 0);
  return { revenue: rev, expenses: exp, net_profit: rev - exp };
});
const monthlyDataFiltered = computed(() => monthlyData.value.filter(d => d.revenue > 0 || d.expenses > 0));
const maxMonthlyRevenue   = computed(() => Math.max(...monthlyData.value.map(d => Math.max(d.revenue || 0, d.expenses || 0)), 1));
const maxYearlyRevenue    = computed(() => Math.max(...yearlyData.value.map(d => Math.max(d.revenue || 0, d.expenses || 0)), 1));

// Ringkasan tambahan untuk sidebar (derived dari data yang sudah ada, tanpa panggilan API baru)
const monthlyStats = computed(() => {
  const active = monthlyDataFiltered.value;
  if (!active.length) return null;
  const avgRevenue = active.reduce((a, d) => a + d.revenue, 0) / active.length;
  const best = active.reduce((a, d) => (d.revenue > a.revenue ? d : a), active[0]);
  return { avgRevenue, best };
});
const yearlyStats = computed(() => {
  const active = yearlyData.value.filter(d => d.revenue > 0 || d.expenses > 0);
  if (!active.length) return null;
  const avgRevenue = active.reduce((a, d) => a + d.revenue, 0) / active.length;
  const best = active.reduce((a, d) => (d.revenue > a.revenue ? d : a), active[0]);
  return { avgRevenue, best };
});

const formatNumber = (v) => Math.round(v || 0).toLocaleString("id-ID");
const barHeight    = (value, max, maxPx = 140) => max ? Math.max(0, ((value || 0) / max) * maxPx) : 0;

const switchMode = (mode) => {
  viewMode.value = mode;
  cancelEdit();
  if (mode === "monthly") { exportMode.value = "monthly"; exportMonth.value = selectedMonth.value; exportYear.value = selectedYear.value; fetchMonthlyData(); }
  else if (mode === "yearly") { exportMode.value = "yearly"; exportYear.value = selectedYear.value; fetchYearlyData(); }
  else { fetchDailyData(); }
};
const changeDate  = (days) => { cancelEdit(); const d = new Date(currentDate.value); d.setDate(d.getDate() + days); currentDate.value = d; fetchDailyData(); };
const changeMonth = (delta) => { let m = selectedMonth.value + delta, y = selectedYear.value; if (m < 1) { m = 12; y--; } if (m > 12) { m = 1; y++; } selectedMonth.value = m; selectedYear.value = y; exportMonth.value = m; exportYear.value = y; fetchMonthlyData(); };
const changeYear  = (delta) => { selectedYear.value += delta; exportYear.value = selectedYear.value; fetchYearlyData(); };

const fetchDailyData = async () => {
  try {
    const [summaryRes, expenseRes] = await Promise.all([
      apiClient.get("/orders/admin_dashboard_daily_stats/", { params: { target_date: targetDateString.value } }),
      apiClient.get("/expenses/", { params: { date: targetDateString.value } }),
    ]);
    financialSummary.value  = summaryRes.data;
    dailyExpensesList.value = expenseRes.data;
  } catch (err) { console.error(err); toast.error("Gagal memuat data finansial harian."); }
};
const fetchMonthlyData = async () => {
  isLoadingChart.value = true;
  try {
    const { data } = await apiClient.get("/orders/finance/daily/", { params: { year: selectedYear.value, month: selectedMonth.value } });
    monthlyData.value = data.data;
    if (data.years_available) yearsAvailable.value = data.years_available;
  } catch (err) { console.error(err); toast.error("Gagal memuat data bulanan."); }
  finally { isLoadingChart.value = false; }
};
const fetchYearlyData = async () => {
  isLoadingChart.value = true;
  try {
    const { data } = await apiClient.get("/orders/finance/monthly/", { params: { year: selectedYear.value } });
    yearlyData.value = data.data;
    if (data.years_available) yearsAvailable.value = data.years_available;
  } catch (err) { console.error(err); toast.error("Gagal memuat data tahunan."); }
  finally { isLoadingChart.value = false; }
};
const resetExpenseForm = () => { expenseForm.value = { description: "", amount: null, payment_method: "cash" }; };
const cancelEdit = () => { editingId.value = null; resetExpenseForm(); };
const startEdit = (exp) => {
  editingId.value = exp.id;
  expenseForm.value = { description: exp.description, amount: Number(exp.amount), payment_method: exp.payment_method || "cash" };
  formCard.value?.scrollIntoView({ behavior: "smooth", block: "nearest" });
};
const submitExpense = async () => {
  if (!expenseForm.value.description || !expenseForm.value.amount) return;
  isSubmittingExpense.value = true;
  const isEdit  = editingId.value !== null;
  const payload = {
    description: expenseForm.value.description,
    amount: expenseForm.value.amount,
    payment_method: expenseForm.value.payment_method,
  };
  try {
    if (isEdit) await apiClient.patch(`/expenses/${editingId.value}/`, payload);
    else await apiClient.post("/expenses/", { ...payload, date: targetDateString.value });
    cancelEdit();
    await fetchDailyData();
    toast.success(isEdit ? "Pengeluaran diperbarui!" : "Pengeluaran dicatat!");
  } catch { toast.error(isEdit ? "Gagal memperbarui pengeluaran." : "Gagal mencatat pengeluaran."); }
  finally { isSubmittingExpense.value = false; }
};
const deleteTarget    = ref(null);
const isDeleting      = ref(false);
const cancelDeleteBtn = ref(null);
const askDelete = (exp) => { deleteTarget.value = exp; nextTick(() => cancelDeleteBtn.value?.focus()); };
const closeDelete = () => { if (!isDeleting.value) deleteTarget.value = null; };
const confirmDelete = async () => {
  const exp = deleteTarget.value;
  if (!exp) return;
  isDeleting.value = true;
  try {
    await apiClient.delete(`/expenses/${exp.id}/`);
    if (editingId.value === exp.id) cancelEdit();
    toast.success("Pengeluaran dihapus.");
    deleteTarget.value = null;
    fetchDailyData();
  } catch { toast.error("Gagal menghapus pengeluaran."); }
  finally { isDeleting.value = false; }
};
const exportDocument = async (type) => {
  isExporting.value = true;
  const endpoint = type === "excel" ? "/orders/export/finance-excel/" : "/orders/export/finance-pdf/";
  const params   = new URLSearchParams({ mode: exportMode.value, year: exportYear.value });
  if (exportMode.value === "monthly") params.append("month", exportMonth.value);
  const url         = `${apiClient.defaults.baseURL}${endpoint}?${params.toString()}`;
  const periodLabel = exportMode.value === "monthly" ? `${monthNames[exportMonth.value - 1]} ${exportYear.value}` : `Tahun ${exportYear.value}`;
  try { window.open(url, "_blank"); toast.success(`Mengunduh laporan ${type.toUpperCase()} — ${periodLabel}`); }
  catch { toast.error("Gagal membuka link unduhan."); }
  finally { setTimeout(() => { isExporting.value = false; }, 1500); }
};

onMounted(async () => {
  await fetchDailyData();
  try {
    const { data } = await apiClient.get("/orders/finance/monthly/", { params: { year: selectedYear.value } });
    if (data.years_available) yearsAvailable.value = data.years_available;
    yearlyData.value = data.data;
  } catch {}
});
</script>

<style scoped>
/* ── Design tokens ───────────────────────────────────────────────── */
.fr-root {
  --bg: #08080a;
  --surface: #101012;
  --surface-hover: #17171a;
  --border: rgba(255,255,255,0.06);
  --border-strong: rgba(255,255,255,0.12);
  --text: #ffffff;
  --text-dim: rgba(255,255,255,0.42);
  --text-faint: rgba(255,255,255,0.22);
  --accent: #dc2626;
  --green: #22c55e;
  --green-soft: #4ade80;
  --amber: #f59e0b;
  --amber-soft: #fbbf24;
  --red-soft: #f87171;
  --r-sm: 8px;
  --r-md: 12px;
  --r-lg: 16px;

  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
  padding: 2rem 1.75rem 3rem;
  max-width: 1360px;
  margin: 0 auto;
  font-family: 'Inter', sans-serif;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* ── Header + toolbar ────────────────────────────────────────────── */
.fr-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}
.fr-heading { display: flex; flex-direction: column; gap: 0.25rem; }
.fr-eyebrow {
  font-family: 'Oswald', sans-serif;
  font-size: 0.62rem; letter-spacing: 0.22em;
  text-transform: uppercase; color: var(--accent);
  margin: 0;
}
.fr-title {
  font-family: 'Oswald', sans-serif;
  font-size: 1.85rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.03em;
  margin: 0;
  line-height: 1.1;
}
.fr-subtitle { font-size: 0.72rem; color: var(--text-dim); margin: 0; font-family: monospace; }

.fr-toolbar {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.mode-switch {
  display: flex;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 4px;
  gap: 2px;
}
.mode-btn {
  padding: 0.45rem 1.05rem;
  border-radius: 9px; border: none;
  background: transparent;
  color: var(--text-faint);
  font-family: 'Oswald', sans-serif;
  font-size: 0.7rem; letter-spacing: 0.1em;
  text-transform: uppercase; cursor: pointer;
  transition: all 0.15s;
}
.mode-btn:hover { color: rgba(255,255,255,0.7); }
.mode-btn.active { background: var(--accent); color: #fff; }

.date-nav {
  display: flex; align-items: center;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-md); overflow: hidden;
}
.nav-btn {
  display: flex; align-items: center; gap: 0.3rem;
  padding: 0.5rem 0.75rem;
  background: transparent; border: none;
  color: var(--text-dim);
  cursor: pointer;
  transition: all 0.15s;
}
.nav-btn:hover { color: #fff; background: rgba(255,255,255,0.04); }
.nav-current {
  padding: 0.5rem 1rem;
  font-family: monospace; font-size: 0.82rem; color: #fff;
  border-left: 1px solid var(--border);
  border-right: 1px solid var(--border);
  white-space: nowrap;
}
.nav-select {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 0.55rem 0.85rem;
  color: #fff; font-family: monospace; font-size: 0.8rem;
  outline: none; cursor: pointer;
  transition: border-color 0.15s;
}
.nav-select:focus { border-color: rgba(220,38,38,0.5); }
.nav-select-block { width: 100%; }

/* ── Summary / KPI Cards ─────────────────────────────────────────── */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}
@media (max-width: 768px) { .summary-grid { grid-template-columns: 1fr; } }

.s-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 1.4rem 1.5rem;
  position: relative; overflow: hidden;
}
.s-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
}
.s-green::before { background: var(--green); }
.s-amber::before { background: var(--amber); }
.s-surplus::before { background: var(--green); }
.s-defisit::before { background: var(--red-soft); }

.s-top { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.9rem; }
.s-icon-wrap {
  display: flex; align-items: center; justify-content: center;
  width: 28px; height: 28px; border-radius: var(--r-sm);
  flex-shrink: 0;
}
.ic-green { background: rgba(34,197,94,0.1); color: var(--green-soft); }
.ic-amber { background: rgba(245,158,11,0.1); color: var(--amber-soft); }
.ic-red   { background: rgba(239,68,68,0.1); color: var(--red-soft); }
.s-label { font-family: 'Oswald', sans-serif; font-size: 0.62rem; letter-spacing: 0.14em; text-transform: uppercase; color: var(--text-dim); flex: 1; }
.s-badge {
  font-size: 0.55rem; padding: 0.15rem 0.55rem; border-radius: 100px;
  font-family: 'Oswald', sans-serif; letter-spacing: 0.08em; text-transform: uppercase;
  white-space: nowrap;
}
.badge-up   { background: rgba(34,197,94,0.1);  color: var(--green-soft); border: 1px solid rgba(34,197,94,0.2); }
.badge-down { background: rgba(239,68,68,0.1);  color: var(--red-soft); border: 1px solid rgba(239,68,68,0.2); }

.s-value { font-family: monospace; font-size: 1.45rem; font-weight: 700; color: #fff; letter-spacing: -0.02em; margin-bottom: 0.4rem; }
.val-green { color: var(--green-soft); }
.val-red   { color: var(--red-soft); }
.s-note    { font-size: 0.68rem; color: var(--text-faint); }

/* ── Body shell: main + sidebar ──────────────────────────────────── */
.fr-shell {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 1.25rem;
  align-items: start;
}
.fr-main  { display: flex; flex-direction: column; gap: 1rem; min-width: 0; }
.fr-aside { display: flex; flex-direction: column; gap: 1rem; position: sticky; top: 1.5rem; }
@media (max-width: 980px) {
  .fr-shell { grid-template-columns: 1fr; }
  .fr-aside { position: static; }
}

/* ── Card base ───────────────────────────────────────────────────── */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  overflow: hidden;
}
.card-head {
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
  padding: 1.15rem 1.4rem;
}
.card-head.border-b { border-bottom: 1px solid var(--border); }
.card-eyebrow {
  font-family: 'Oswald', sans-serif; font-size: 0.58rem;
  letter-spacing: 0.18em; text-transform: uppercase;
  color: var(--accent); margin: 0 0 0.2rem;
}
.card-title { font-family: 'Oswald', sans-serif; font-size: 0.88rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; margin: 0; color: rgba(255,255,255,0.85); }
.card-head-meta { font-family: monospace; font-size: 0.72rem; color: var(--text-faint); white-space: nowrap; }

/* Expense Form */
.expense-form { padding: 1.25rem 1.4rem; display: flex; flex-direction: column; gap: 1rem; }
.field { display: flex; flex-direction: column; gap: 0.4rem; }
.field-label { font-family: 'Oswald', sans-serif; font-size: 0.58rem; letter-spacing: 0.15em; text-transform: uppercase; color: var(--text-faint); }
.field-input {
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border-strong);
  border-radius: var(--r-sm); padding: 0.7rem 1rem;
  color: #fff; font-size: 0.85rem; font-family: 'Inter', sans-serif;
  outline: none; transition: border-color 0.15s;
}
.field-input::placeholder { color: rgba(255,255,255,0.2); }
.field-input:focus { border-color: rgba(220,38,38,0.45); }
.submit-btn {
  display: flex; align-items: center; justify-content: center; gap: 0.4rem;
  padding: 0.75rem; background: rgba(255,255,255,0.04);
  border: 1px solid var(--border-strong); border-radius: var(--r-sm);
  color: var(--amber-soft); font-family: 'Oswald', sans-serif;
  font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: all 0.15s;
}
.submit-btn:hover:not(:disabled) { background: rgba(251,191,36,0.08); border-color: rgba(251,191,36,0.25); }
.submit-btn:disabled { opacity: 0.35; cursor: not-allowed; }

/* Modal konfirmasi hapus */
.modal-backdrop {
  position: fixed; inset: 0; z-index: 100;
  display: flex; align-items: center; justify-content: center; padding: 1rem;
  background: rgba(0,0,0,0.7); backdrop-filter: blur(4px);
}
.modal {
  width: 100%; max-width: 380px;
  background: var(--surface); border: 1px solid var(--border-strong);
  border-radius: var(--r-lg); padding: 1.5rem;
  box-shadow: 0 24px 60px rgba(0,0,0,0.6);
  animation: modal-in 0.15s ease-out;
}
@keyframes modal-in { from { opacity: 0; transform: translateY(6px) scale(0.98); } to { opacity: 1; transform: none; } }
@media (prefers-reduced-motion: reduce) { .modal { animation: none; } }
.modal-icon {
  display: flex; align-items: center; justify-content: center;
  width: 36px; height: 36px; border-radius: var(--r-sm); margin-bottom: 1rem;
  background: rgba(239,68,68,0.1); color: var(--red-soft);
}
.modal-title {
  font-family: 'Oswald', sans-serif; font-size: 1rem; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.05em; margin: 0 0 0.5rem; color: #fff;
}
.modal-text { font-size: 0.8rem; line-height: 1.55; color: var(--text-dim); margin: 0 0 1.25rem; }
.modal-text strong { color: #fff; font-weight: 600; }
.modal-actions { display: flex; gap: 0.5rem; }
.modal-cancel, .modal-confirm {
  flex: 1; padding: 0.7rem; border-radius: var(--r-sm); border: 1px solid;
  font-family: 'Oswald', sans-serif; font-size: 0.7rem; letter-spacing: 0.1em;
  text-transform: uppercase; cursor: pointer; transition: all 0.15s;
}
.modal-cancel { background: rgba(255,255,255,0.04); border-color: var(--border-strong); color: rgba(255,255,255,0.8); }
.modal-cancel:hover { background: rgba(255,255,255,0.08); }
.modal-confirm { background: var(--accent); border-color: var(--accent); color: #fff; }
.modal-confirm:hover:not(:disabled) { background: #b91c1c; }
.modal-confirm:disabled { opacity: 0.5; cursor: not-allowed; }
.modal-cancel:focus-visible, .modal-confirm:focus-visible { outline: 2px solid var(--amber-soft); outline-offset: 2px; }

/* Metode pembayaran, badge, dan aksi baris */
.method-switch {
  display: flex; background: rgba(255,255,255,0.03);
  border: 1px solid var(--border); border-radius: var(--r-sm); padding: 3px; gap: 2px;
}
.method-btn {
  flex: 1; padding: 0.5rem 0.7rem; border-radius: 6px; border: none; background: transparent;
  color: var(--text-faint); font-family: 'Oswald', sans-serif; font-size: 0.66rem;
  letter-spacing: 0.1em; text-transform: uppercase; cursor: pointer; transition: all 0.15s;
}
.method-btn:hover { color: rgba(255,255,255,0.65); }
.method-btn.active { background: var(--accent); color: #fff; }
.method-btn:focus-visible, .edit-btn:focus-visible, .cancel-btn:focus-visible {
  outline: 2px solid var(--amber-soft); outline-offset: 2px;
}
.cancel-btn {
  padding: 0.65rem; background: transparent; border: 1px solid var(--border);
  border-radius: var(--r-sm); color: var(--text-dim); font-family: 'Oswald', sans-serif;
  font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: all 0.15s;
}
.cancel-btn:hover { color: #fff; border-color: var(--border-strong); }

.method-badge {
  display: inline-block; padding: 0.15rem 0.55rem; border-radius: 100px; border: 1px solid;
  font-family: 'Oswald', sans-serif; font-size: 0.58rem; letter-spacing: 0.1em; text-transform: uppercase;
}
.mb-cash { color: var(--text-dim); background: rgba(255,255,255,0.04); border-color: var(--border-strong); }
.mb-qris { color: #7dd3fc; background: rgba(56,189,248,0.08); border-color: rgba(56,189,248,0.25); }

.row-editing { background: rgba(251,191,36,0.05); }
.row-actions { display: inline-flex; gap: 0.4rem; }
.edit-btn {
  padding: 0.25rem 0.65rem; border-radius: 6px;
  background: rgba(255,255,255,0.04); border: 1px solid var(--border-strong);
  color: var(--text-dim); font-family: 'Oswald', sans-serif;
  font-size: 0.58rem; letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: all 0.15s;
}
.edit-btn:hover { color: #fff; background: rgba(255,255,255,0.08); }

/* Insight card */
.insight-body { padding: 1rem 1.4rem 1.25rem; display: flex; flex-direction: column; gap: 0.85rem; }
.insight-row { display: flex; flex-direction: column; gap: 0.25rem; }
.insight-label { font-size: 0.66rem; letter-spacing: 0.03em; color: var(--text-dim); }
.insight-value { font-family: monospace; font-size: 0.85rem; font-weight: 600; color: #fff; }

/* Export card */
.export-body { padding: 1.1rem 1.4rem 1.4rem; display: flex; flex-direction: column; gap: 0.85rem; }
.export-toggle {
  display: flex; background: rgba(255,255,255,0.03);
  border: 1px solid var(--border); border-radius: var(--r-sm); padding: 3px; gap: 2px;
}
.toggle-btn {
  flex: 1;
  padding: 0.38rem 0.7rem; border-radius: 6px; border: none; background: transparent;
  color: var(--text-faint);
  font-family: 'Oswald', sans-serif; font-size: 0.62rem;
  letter-spacing: 0.1em; text-transform: uppercase; cursor: pointer; transition: all 0.15s;
}
.toggle-btn:hover { color: rgba(255,255,255,0.65); }
.toggle-btn.active { background: var(--accent); color: #fff; }
.export-controls { display: flex; gap: 0.5rem; }
.export-period-label {
  font-family: monospace; font-size: 0.72rem;
  color: var(--text-dim); margin: 0;
  background: rgba(255,255,255,0.03); border: 1px solid var(--border);
  border-radius: var(--r-sm); padding: 0.5rem 0.75rem;
}
.period-highlight { color: var(--accent); }
.export-btns { display: flex; gap: 0.5rem; }
.export-btn {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 0.4rem;
  padding: 0.65rem; border-radius: var(--r-sm); border: 1px solid;
  font-family: 'Oswald', sans-serif; font-size: 0.68rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: all 0.15s;
}
.export-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-excel { background: rgba(34,197,94,0.07); border-color: rgba(34,197,94,0.2); color: var(--green-soft); }
.btn-excel:hover:not(:disabled) { background: rgba(34,197,94,0.14); }
.btn-pdf   { background: rgba(220,38,38,0.07);  border-color: rgba(220,38,38,0.2);  color: var(--red-soft); }
.btn-pdf:hover:not(:disabled)   { background: rgba(220,38,38,0.14); }

/* Table */
.table-scroll { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; min-width: 400px; }
.data-table th {
  padding: 0.65rem 1.4rem;
  font-family: 'Oswald', sans-serif; font-size: 0.58rem; font-weight: 400;
  letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--text-faint); text-align: left;
  background: rgba(255,255,255,0.015);
  border-bottom: 1px solid var(--border);
}
.th-right  { text-align: right; }
.th-center { text-align: center; }

.data-row { border-bottom: 1px solid var(--border); transition: background 0.12s; }
.data-row:hover { background: rgba(255,255,255,0.02); }
.data-row:last-child { border-bottom: none; }
.row-empty { opacity: 0.3; }

.data-table td { padding: 0.8rem 1.4rem; font-size: 0.82rem; vertical-align: middle; }
.td-mono   { font-family: monospace; color: rgba(255,255,255,0.65); }
.td-month  { font-weight: 600; color: rgba(255,255,255,0.8); }
.td-desc   { color: rgba(255,255,255,0.8); }
.td-right  { text-align: right; }
.td-center { text-align: center; }
.td-rev    { font-family: monospace; font-weight: 700; color: var(--green-soft); }
.td-exp    { font-family: monospace; color: var(--amber-soft); }
.td-amount { font-family: monospace; font-weight: 700; color: var(--amber-soft); }
.td-pos    { font-family: monospace; font-weight: 700; color: #fff; }
.td-neg    { font-family: monospace; font-weight: 700; color: var(--red-soft); }

.total-row {
  background: rgba(255,255,255,0.03) !important;
  border-top: 1px solid var(--border-strong) !important;
}
.total-row td { font-family: 'Oswald', sans-serif; font-size: 0.65rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-dim); padding: 0.7rem 1.4rem; }
.total-row .td-rev, .total-row .td-exp, .total-row .td-pos, .total-row .td-neg { font-size: 0.82rem; }

.delete-btn {
  padding: 0.25rem 0.65rem; border-radius: 6px;
  background: rgba(239,68,68,0.07); border: 1px solid rgba(239,68,68,0.15);
  color: var(--red-soft); font-family: 'Oswald', sans-serif;
  font-size: 0.58rem; letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: all 0.15s;
}
.delete-btn:hover { background: rgba(239,68,68,0.15); }

.empty-cell { padding: 2.5rem !important; text-align: center; color: var(--text-faint); }
.empty-icon { font-size: 1.5rem; margin-bottom: 0.5rem; }
.empty-cell p { margin: 0; font-size: 0.78rem; }

/* ── Chart ───────────────────────────────────────────────────────── */
.chart-card .card-head { border-bottom: 1px solid var(--border); }
.chart-loading {
  display: flex; align-items: center; justify-content: center; gap: 0.6rem;
  padding: 3rem; color: var(--text-faint); font-size: 0.75rem;
  font-family: 'Oswald', sans-serif; letter-spacing: 0.1em; text-transform: uppercase;
}
.spinner-sm {
  width: 20px; height: 20px; border: 2px solid rgba(255,255,255,0.07);
  border-top-color: var(--accent); border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.chart-area { padding: 1.25rem 1.4rem 1.1rem; }
.bar-chart {
  display: flex; align-items: flex-end; gap: 3px;
  height: 150px; overflow-x: auto; padding-bottom: 0.5rem;
  background-image: repeating-linear-gradient(to top, transparent 0, transparent calc(25% - 1px), var(--border) calc(25% - 1px), var(--border) 25%);
  background-size: 100% 150px;
  background-position: bottom;
  background-repeat: no-repeat;
}
.bar-chart-yearly { gap: 6px; overflow-x: visible; }
.bar-col { display: flex; flex-direction: column; align-items: center; gap: 0.3rem; flex: 1; min-width: 20px; }
.bar-pair { display: flex; flex-direction: column; justify-content: flex-end; gap: 2px; width: 100%; flex: 1; align-items: center; }
.bar { width: 100%; border-radius: 3px 3px 0 0; transition: height 0.5s ease; min-width: 6px; }
.bar-rev { background: var(--green); }
.bar-exp { background: var(--amber); opacity: 0.75; }
.bar-label { font-size: 0.55rem; font-family: monospace; color: var(--text-faint); white-space: nowrap; }
.chart-legend { display: flex; gap: 1.25rem; margin-top: 0.75rem; }
.legend-item { display: flex; align-items: center; gap: 0.4rem; font-size: 0.7rem; color: var(--text-dim); }
.legend-dot { width: 8px; height: 8px; border-radius: 2px; }
.ld-green { background: var(--green); }
.ld-amber { background: var(--amber); }

/* ── Responsive ─────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .fr-root { padding: 1.25rem 1rem 2rem; }
  .fr-header { flex-direction: column; align-items: flex-start; }
  .fr-title { font-size: 1.4rem; }
  .fr-toolbar { width: 100%; }
  .mode-switch { width: 100%; }
  .mode-btn { flex: 1; }
}

/* Hide spinners */
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
input[type=number] { -moz-appearance: textfield; }
</style>