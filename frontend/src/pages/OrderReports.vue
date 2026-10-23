<template>
  <div class="adm-page">

    <!-- ═══ HEADER ════════════════════════════════════════════════════
         Sengaja TIDAK sticky: judul + tab + filter + badge periode tingginya ±330px,
         jadi kalau menempel di atas ia menutup grafik dan tabel saat halaman di-scroll. -->
    <header class="adm-header">
      <div>
        <p class="adm-eyebrow">Masashimura · Admin</p>
        <h1 class="adm-title">Order Reports</h1>
        <p class="adm-sub">{{ activeTabSubtitle }}</p>
      </div>

      <div class="adm-header-actions">
        <!-- Refresh -->
        <button
          type="button"
          @click="refresh"
          :disabled="loading || tabRef?.loading"
          aria-label="Muat ulang data"
          class="adm-icon-btn adm-icon-btn--bordered"
        >
          <RefreshCw :size="14" :class="{ 'animate-spin': loading || tabRef?.loading }" />
        </button>

        <!-- Export dropdown -->
        <div class="relative" ref="exportMenuRef">
          <button
            v-if="activeTab === 'ringkasan' && canExport"
            type="button"
            @click="exportOpen = !exportOpen"
            aria-haspopup="menu"
            :aria-expanded="exportOpen"
            :disabled="loading"
            class="adm-btn adm-btn--ghost"
          >
            <Download :size="13" class="text-[color:var(--accent-text)]" />
            <span class="hidden sm:inline">Export</span>
            <ChevronDown :size="12" class="text-[color:var(--text-faint)]" />
          </button>

          <Transition
            enter-active-class="transition duration-150 ease-out"
            enter-from-class="opacity-0 -translate-y-1"
            enter-to-class="opacity-100 translate-y-0"
            leave-active-class="transition duration-100 ease-in"
            leave-from-class="opacity-100"
            leave-to-class="opacity-0"
          >
            <div v-if="exportOpen" class="rep-menu" role="menu">
              <button type="button" role="menuitem" @click="exportDocument('pdf')" class="rep-menu-item">
                <FileText :size="13" class="text-[color:var(--accent-text)]" /> Export PDF
              </button>
              <button type="button" role="menuitem" @click="exportDocument('excel')" class="rep-menu-item">
                <Sheet :size="13" class="text-[color:var(--green-soft)]" /> Export Excel
              </button>
            </div>
          </Transition>
        </div>
      </div>
    </header>

    <!-- ═══ TAB HALAMAN ═════════════════════════════════════════════ -->
    <div class="adm-seg" role="tablist" aria-label="Bagian laporan">
      <button
        v-for="t in pageTabs"
        :key="t.value"
        type="button"
        role="tab"
        class="adm-seg-btn"
        :aria-selected="activeTab === t.value"
        :aria-pressed="activeTab === t.value"
        @click="activeTab = t.value"
      >{{ t.label }}</button>
    </div>

    <template v-if="activeTab !== 'jam'">
      <!-- ═══ FILTER BAR ══════════════════════════════════════════════ -->
      <div class="adm-toolbar">
        <div class="adm-seg" role="group" aria-label="Rentang periode">
          <button
            v-for="g in groups"
            :key="g.value"
            type="button"
            class="adm-seg-btn"
            :aria-pressed="activeGroup === g.value"
            @click="selectGroup(g.value)"
          >
            <component :is="g.icon" :size="12" />
            {{ g.label }}
          </button>
        </div>

        <!-- Sub-filter: Mingguan -->
        <div v-if="activeGroup === 'weekly'" class="adm-seg" role="group" aria-label="Minggu">
          <button
            v-for="w in weekOptions"
            :key="w.value"
            type="button"
            class="adm-seg-btn"
            :aria-pressed="activeWeek === w.value"
            @click="activeWeek = w.value; fetchReport()"
          >{{ w.label }}</button>
        </div>

        <!-- Sub-filter: Bulanan -->
        <template v-if="activeGroup === 'monthly'">
          <select v-model.number="activeMonth" @change="fetchReport()" class="adm-input rep-select" aria-label="Pilih bulan">
            <option v-for="m in 12" :key="m" :value="m">{{ monthName(m) }}</option>
          </select>
          <select v-model.number="activeYear" @change="fetchReport()" class="adm-input rep-select" aria-label="Pilih tahun">
            <option v-for="y in yearOptions" :key="y" :value="y">{{ y }}</option>
          </select>
        </template>

        <!-- Sub-filter: Tahunan -->
        <div v-if="activeGroup === 'yearly'" class="adm-seg" role="group" aria-label="Tahun">
          <button
            v-for="y in yearOptions"
            :key="y"
            type="button"
            class="adm-seg-btn"
            :aria-pressed="activeYear === y"
            @click="activeYear = y; fetchReport()"
          >{{ y }}</button>
        </div>

        <!-- Sub-filter: Lifetime — just a label -->
        <span v-if="activeGroup === 'lifetime'" class="adm-badge">Semua waktu</span>
      </div>

      <!-- ═══ PERIOD BADGE ════════════════════════════════════════════ -->
      <p class="adm-hint rep-period">{{ periodLabel }}</p>
    </template>

    <div class="rep-body">

        <!-- ═══ TAB LAIN (dimuat saat dibuka; mengikuti filter periode di atas) ═══ -->
        <template v-if="activeTab !== 'ringkasan'">
          <BusyHoursTab v-if="activeTab === 'jam'" ref="tabRef" />
          <MenuPerformanceTab v-else-if="activeTab === 'performa'" ref="tabRef" :params="periodParams" />
          <MenuPairsTab v-else-if="activeTab === 'pasangan'" ref="tabRef" :params="periodParams" />
          <ChannelTab v-else-if="activeTab === 'channel'" ref="tabRef" :params="periodParams" />
        </template>

        <!-- ═══ LOADING SKELETON ═══════════════════════════════════════ -->
        <div v-else-if="loading" class="space-y-5 animate-pulse">
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            <div v-for="i in 4" :key="i" class="adm-card p-5 h-[112px]">
              <div class="w-10 h-10 rounded-[var(--r-sm)] bg-[color:rgb(var(--ink)/0.06)] mb-4"></div>
              <div class="w-16 h-4 bg-[color:rgb(var(--ink)/0.06)] rounded mb-2"></div>
              <div class="w-20 h-2.5 bg-[color:rgb(var(--ink)/0.06)] rounded"></div>
            </div>
          </div>
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <div class="adm-card p-6 h-64"></div>
            <div class="adm-card p-6 h-64"></div>
          </div>
          <p class="text-center text-[color:var(--text-faint)] text-[11px] font-semibold pt-2">
            Memuat data laporan...
          </p>
        </div>

        <!-- ═══ CONTENT ═════════════════════════════════════════════════ -->
        <template v-else-if="report">

          <!-- 1. KPI STATS -->
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-5 sm:mb-6">
            <StatCard icon="DollarSign" color="red"     label="Total Omzet"         :value="formatRp(report.stats.total_omzet)" :sub="vsLabel" />
            <StatCard icon="ShoppingBag" color="amber"  label="Total Transaksi"     :value="report.stats.total_transaksi.toLocaleString('id-ID')" />
            <StatCard icon="TrendingUp"  color="emerald" label="Rata-rata Transaksi" :value="formatRp(report.stats.rata_rata_transaksi)" />
            <StatCard icon="Utensils"    color="sky"    label="Menu Aktif"           :value="report.stats.menu_aktif" />
          </div>

          <!-- 2. TREND CHARTS -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-5 mb-4 sm:mb-5">
            <RCard title="Omzet" :subtitle="trendSubtitle" icon="TrendingUp" accent="red">
              <div class="h-56 sm:h-64">
                <Bar :data="omzetData" :options="barOpts" />
              </div>
            </RCard>
            <RCard title="Transaksi" :subtitle="trendSubtitle" icon="ShoppingBag" accent="amber">
              <div class="h-56 sm:h-64">
                <Bar :data="transaksiData" :options="barOpts" />
              </div>
            </RCard>
          </div>

          <!-- 3. TOP MENU + PALING MENGHASILKAN -->
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-5 mb-4 sm:mb-5">
            <RCard title="Top 10 Menu Terlaris" icon="Award" accent="amber" class="lg:col-span-2">
              <!-- Desktop table -->
              <table class="adm-table hidden sm:table">
                <thead>
                  <tr>
                    <th class="w-8">#</th>
                    <th >Menu</th>
                    <th class="adm-th-r">Qty</th>
                    <th class="adm-th-r">Omzet</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(m, i) in report.top_menu" :key="i">
                    <td class="text-[color:var(--text-faint)] font-bold">{{ String(i+1).padStart(2,'0') }}</td>
                    <td class="text-[color:var(--text)] font-semibold">{{ m.name }}</td>
                    <td class="adm-td-r">
                      <span class="adm-badge adm-badge--amber">{{ m.qty }}</span>
                    </td>
                    <td class="adm-td-r adm-mono">{{ formatRp(m.omzet) }}</td>
                  </tr>
                </tbody>
              </table>

              <!-- Mobile stacked cards -->
              <div class="flex flex-col gap-2 sm:hidden">
                <div
                  v-for="(m, i) in report.top_menu"
                  :key="i"
                  class="flex items-center justify-between bg-[color:var(--surface-2)] border border-[color:var(--border)] rounded-[var(--r-md)] px-3.5 py-3"
                >
                  <div class="flex items-center gap-3 min-w-0">
                    <span class="text-[color:var(--text-faint)] text-[11px] font-semibold shrink-0">{{ String(i+1).padStart(2,'0') }}</span>
                    <div class="min-w-0">
                      <p class="text-[color:var(--text)] font-semibold text-xs truncate">{{ m.name }}</p>
                      <p class="text-[color:var(--text-faint)] text-[11px] font-mono mt-0.5">{{ formatRp(m.omzet) }}</p>
                    </div>
                  </div>
                  <span class="adm-badge adm-badge--amber shrink-0 ml-2">{{ m.qty }}</span>
                </div>
              </div>

              <EmptyState v-if="!report.top_menu.length" text="Belum ada data penjualan" />
            </RCard>

            <RCard title="Paling Menghasilkan" icon="Gem" accent="emerald">
              <div class="space-y-5">
                <div v-for="(m, i) in report.menu_paling_menghasilkan" :key="i">
                  <div class="flex justify-between text-xs mb-2 gap-2">
                    <span class="text-[color:var(--text)] font-semibold truncate">{{ m.name }}</span>
                    <span class="text-[color:var(--green-soft)] font-bold tabular-nums shrink-0">{{ formatRp(m.omzet) }}</span>
                  </div>
                  <div class="w-full bg-[color:rgb(var(--ink)/0.06)] h-1.5 rounded-full overflow-hidden">
                    <div
                      class="h-full rounded-full transition-all duration-700"
                      :style="{ width: pct(m.omzet, maxMenghasilkan) + '%', background: 'linear-gradient(90deg, var(--green), var(--green-soft))' }"
                    ></div>
                  </div>
                </div>
                <EmptyState v-if="!report.menu_paling_menghasilkan.length" text="Belum ada data" compact />
              </div>
            </RCard>
          </div>

          <!-- 4. BOTTOM ROW -->
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-5 mb-4 sm:mb-5">

            <!-- Menu Tidak Laku -->
            <RCard title="Menu Tidak Laku" icon="AlertTriangle" accent="red">
              <div class="space-y-2 max-h-64 overflow-y-auto pr-1 custom-scroll">
                <div
                  v-for="(m, i) in report.menu_tidak_laku"
                  :key="i"
                  class="flex justify-between items-center bg-[color:var(--tint-accent)] border border-[color:var(--line-accent)] rounded-[var(--r-md)] px-4 py-3"
                >
                  <span class="text-[color:var(--text)] text-xs font-semibold truncate mr-2">{{ m.name }}</span>
                  <span class="text-[color:var(--red-soft)] text-[11px] font-bold uppercase tracking-wider shrink-0">
                    {{ m.transaksi }}×
                  </span>
                </div>
                <EmptyState v-if="!report.menu_tidak_laku.length" text="Semua menu terjual" emoji="🎉" />
              </div>
            </RCard>

            <!-- Metode Pembayaran -->
            <RCard title="Metode Pembayaran" icon="CreditCard" accent="sky">
              <div class="flex flex-col items-center">
                <div class="w-36 h-36 sm:w-40 sm:h-40 mb-5">
                  <Pie :data="paymentData" :options="pieOpts" />
                </div>
                <div class="w-full space-y-2.5">
                  <div
                    v-for="(p, i) in report.metode_pembayaran"
                    :key="i"
                    class="flex items-center justify-between"
                  >
                    <div class="flex items-center gap-2 min-w-0">
                      <div class="w-2 h-2 rounded-full shrink-0" :style="{ background: payColors[p.method] || '#9a9aa3' }"></div>
                      <span class="text-[color:var(--text-dim)] text-xs truncate">{{ p.label }}</span>
                    </div>
                    <span class="text-[color:var(--text)] text-xs font-bold tabular-nums shrink-0">{{ p.percent }}%</span>
                  </div>
                  <EmptyState v-if="!report.metode_pembayaran.length" text="Belum ada transaksi" compact />
                </div>
              </div>
            </RCard>

            <!-- Jam Teramai -->
            <RCard title="Jam Teramai" icon="Clock" accent="violet">
              <div class="h-52 sm:h-56">
                <Bar :data="jamData" :options="barOptsY" />
              </div>
            </RCard>
          </div>

          <!-- 5. PELANGGAN -->
          <RCard title="Pelanggan" icon="Users" accent="pink">
            <div class="grid grid-cols-3 gap-3 sm:gap-6 text-center">
              <div class="py-3 sm:py-4">
                <p class="font-display text-2xl sm:text-4xl text-[color:var(--text)] mb-1">{{ report.pelanggan.baru }}</p>
                <p class="text-xs text-[color:var(--text-faint)] uppercase tracking-[0.15em] sm:tracking-[0.2em]">Pelanggan Baru</p>
              </div>
              <div class="py-3 sm:py-4 border-x border-[color:rgb(var(--ink)/0.05)]">
                <p class="font-display text-2xl sm:text-4xl text-[color:var(--text)] mb-1">{{ report.pelanggan.lama }}</p>
                <p class="text-xs text-[color:var(--text-faint)] uppercase tracking-[0.15em] sm:tracking-[0.2em]">Pelanggan Lama</p>
              </div>
              <div class="py-3 sm:py-4">
                <p class="font-display text-2xl sm:text-4xl text-[color:var(--amber-soft)] mb-1">{{ report.pelanggan.loyal_member }}</p>
                <p class="text-xs text-[color:var(--text-faint)] uppercase tracking-[0.15em] sm:tracking-[0.2em]">Member Loyal</p>
              </div>
            </div>
          </RCard>
        </template>

        <!-- ═══ ERROR / EMPTY ═════════════════════════════════════════════ -->
        <div v-else class="flex flex-col items-center justify-center py-24 sm:py-32 text-center">
          <div class="w-12 h-12 rounded-[var(--r-md)] bg-[color:var(--tint-accent)] flex items-center justify-center mb-4">
            <AlertTriangle :size="20" class="text-[color:var(--accent-text)]" />
          </div>
          <p class="text-[color:var(--text)] text-sm font-semibold mb-1">Gagal memuat data</p>
          <p class="text-[color:var(--text-faint)] text-xs mb-5">Periksa koneksi atau coba lagi beberapa saat.</p>
          <button type="button" @click="fetchReport()" class="adm-btn adm-btn--primary">
            <RefreshCw :size="13" /> Muat ulang
          </button>
        </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, h } from "vue";
import { Bar, Pie } from "vue-chartjs";
import {
  Chart as ChartJS, BarElement, CategoryScale, LinearScale,
  ArcElement, Tooltip, Legend,
} from "chart.js";
import {
  TrendingUp, Award, Download, ShoppingBag, DollarSign, Utensils,
  AlertTriangle, CreditCard, Clock, Users, Gem, Calendar,
  CalendarDays, CalendarRange, Infinity as InfinityIcon, RefreshCw, ChevronDown,
  FileText, Sheet,
} from "lucide-vue-next";
import apiClient from "@/api/client";
import BusyHoursTab from "@/components/ui/admin/BusyHoursTab.vue";
import MenuPerformanceTab from "@/components/ui/admin/MenuPerformanceTab.vue";
import MenuPairsTab from "@/components/ui/admin/MenuPairsTab.vue";
import ChannelTab from "@/components/ui/admin/ChannelTab.vue";
import { useTheme } from "@/composables/useTheme";

ChartJS.register(BarElement, CategoryScale, LinearScale, ArcElement, Tooltip, Legend);

// ── Filter state ──────────────────────────────────────────────────────────
const now        = new Date();
const loading    = ref(true);
const report     = ref(null);
const exportOpen = ref(false);
const exportMenuRef = ref(null);

// Tab halaman: Ringkasan (laporan yang sudah ada) | Jam Sibuk (dimuat saat dibuka)
const activeTab = ref("ringkasan");
const tabRef    = ref(null);
const pageTabs  = [
  { label: "Ringkasan",    value: "ringkasan", sub: "Analisis omzet, performa menu, dan pelanggan" },
  { label: "Performa Menu", value: "performa",  sub: "Volume, kontribusi omzet, dan kelompok tiap menu" },
  { label: "Pasangan Menu", value: "pasangan",  sub: "Menu yang sering dipesan bersamaan, dasar ide paket" },
  { label: "Channel",       value: "channel",   sub: "Perbandingan pesanan web pelanggan dan POS kasir" },
  { label: "Jam Sibuk",     value: "jam",       sub: "Pola jam dan hari tersibuk dari data pesanan" },
];
const activeTabSubtitle = computed(() => pageTabs.find((t) => t.value === activeTab.value)?.sub || "");
const refresh = () => (activeTab.value === "ringkasan" ? fetchReport() : tabRef.value?.reload());

const activeGroup = ref("lifetime");   // lifetime | weekly | monthly | yearly
const activeWeek  = ref("this");       // this | last
const activeMonth = ref(now.getMonth() + 1);
const activeYear  = ref(now.getFullYear());

const groups = [
  { label: "Lifetime",  value: "lifetime", icon: InfinityIcon },
  { label: "Mingguan",  value: "weekly",   icon: CalendarDays },
  { label: "Bulanan",   value: "monthly",  icon: Calendar },
  { label: "Tahunan",   value: "yearly",   icon: CalendarRange },
];

const weekOptions = [
  { label: "Minggu ini",  value: "this" },
  { label: "Minggu lalu", value: "last" },
  { label: "2 minggu",    value: "2w" },
  { label: "4 minggu",    value: "4w" },
];

const yearOptions = Array.from({ length: 5 }, (_, i) => now.getFullYear() - i);

const BULAN = ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"];
const monthName = (m) => BULAN[m - 1];

// ── Close export menu on outside click ───────────────────────────────────
const handleClickOutside = (e) => {
  if (exportMenuRef.value && !exportMenuRef.value.contains(e.target)) {
    exportOpen.value = false;
  }
};
const handleEsc = (e) => { if (e.key === "Escape") exportOpen.value = false; };
onMounted(() => { document.addEventListener("click", handleClickOutside); document.addEventListener("keydown", handleEsc); });
onBeforeUnmount(() => { document.removeEventListener("click", handleClickOutside); document.removeEventListener("keydown", handleEsc); });

// ── Derived labels ────────────────────────────────────────────────────────
const periodLabel = computed(() => {
  if (activeGroup.value === "lifetime") return "Semua data tersimpan";
  if (activeGroup.value === "weekly") {
    const w = weekOptions.find(w => w.value === activeWeek.value);
    return w?.label || "Mingguan";
  }
  if (activeGroup.value === "monthly") return `${monthName(activeMonth.value)} ${activeYear.value}`;
  return `Tahun ${activeYear.value}`;
});

const trendSubtitle = computed(() => periodLabel.value);
const vsLabel       = computed(() => "vs. periode sebelumnya");

// ── API params ────────────────────────────────────────────────────────────
const buildParams = () => {
  const g = activeGroup.value;
  if (g === "lifetime") return { period: "lifetime" };
  if (g === "weekly") {
    const daysMap = { this: 7, last: 7, "2w": 14, "4w": 28 };
    const offset  = { this: 0, last: 7, "2w": 0, "4w": 0 };
    return { period: "week", days: daysMap[activeWeek.value], offset: offset[activeWeek.value] };
  }
  if (g === "monthly") return { period: "month", month: activeMonth.value, year: activeYear.value };
  return { period: "year", year: activeYear.value };
};

// ── Fetch ─────────────────────────────────────────────────────────────────
// Klik filter berturut-turut menjalankan beberapa request sekaligus. Hanya request TERAKHIR yang
// boleh mengisi layar, supaya jawaban lambat dari filter lama tidak menimpa filter yang aktif.
let reportRequestId = 0;
const fetchReport = async () => {
  // Tab lain memuat datanya sendiri dan memantau periodParams. Ringkasan dimuat ulang saat tab dibuka lagi.
  if (activeTab.value !== "ringkasan") return;
  const requestId = ++reportRequestId;
  loading.value = true;
  try {
    const { data } = await apiClient.get("/orders/reports/full/", { params: buildParams() });
    if (requestId !== reportRequestId) return;
    report.value = data;
  } catch (e) {
    if (requestId !== reportRequestId) return;
    console.error("Gagal load report:", e);
    report.value = null;
  } finally {
    if (requestId === reportRequestId) loading.value = false;
  }
};

const periodParams = computed(() => buildParams());
watch(activeTab, (t) => { if (t === "ringkasan") fetchReport(); });

const selectGroup = (g) => {
  activeGroup.value = g;
  fetchReport();
};

// ── Chart data ────────────────────────────────────────────────────────────
const omzetData = computed(() => ({
  labels: report.value?.trend.labels || [],
  datasets: [{
    label: "Omzet",
    data: report.value?.trend.omzet || [],
    backgroundColor: "#d92b22",
    borderRadius: 6,
    borderSkipped: false,
    maxBarThickness: 36,
  }],
}));

const transaksiData = computed(() => ({
  labels: report.value?.trend.labels || [],
  datasets: [{
    label: "Transaksi",
    data: report.value?.trend.transaksi || [],
    backgroundColor: "#f4c542",
    borderRadius: 6,
    borderSkipped: false,
    maxBarThickness: 36,
  }],
}));

const jamData = computed(() => ({
  labels: report.value?.jam_teramai.map(j => j.label) || [],
  datasets: [{
    label: "Transaksi",
    data: report.value?.jam_teramai.map(j => j.count) || [],
    backgroundColor: "#c79bf7",
    borderRadius: 6,
    borderSkipped: false,
  }],
}));

const payColors = { cash: "#2fb36d", qris: "#7cc4f5", qris_manual: "#f4c542", gateway: "#c79bf7" };
const paymentData = computed(() => ({
  labels: report.value?.metode_pembayaran.map(p => p.label) || [],
  datasets: [{
    data: report.value?.metode_pembayaran.map(p => p.total) || [],
    backgroundColor: report.value?.metode_pembayaran.map(p => payColors[p.method] || "#9a9aa3") || [],
    borderWidth: 0,
    hoverOffset: 6,
  }],
}));

const maxMenghasilkan = computed(() =>
  Math.max(1, ...(report.value?.menu_paling_menghasilkan.map(m => m.omzet) || [1]))
);
const pct = (v, max) => Math.round((v / max) * 100);

// ── Chart options (ikut tema: canvas tidak bisa baca CSS variable) ───────
const { isDark } = useTheme();
const chartTheme = computed(() => isDark.value
  ? { grid: "rgba(255,255,255,0.05)", tick: "rgba(255,255,255,0.5)", tipBg: "#151518", tipBorder: "rgba(255,255,255,0.12)", tipTitle: "#fafafa", tipBody: "rgba(255,255,255,0.7)" }
  : { grid: "rgba(24,24,27,0.07)",   tick: "rgba(24,24,27,0.62)",    tipBg: "#ffffff", tipBorder: "rgba(24,24,27,0.15)",    tipTitle: "#18181b", tipBody: "#3f3f46" });

const barOpts = computed(() => {
  const c = chartTheme.value;
  const tick = { color: c.tick, font: { size: 11, family: "Plus Jakarta Sans" } };
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: c.tipBg, borderColor: c.tipBorder, borderWidth: 1,
        titleColor: c.tipTitle, titleFont: { family: "Plus Jakarta Sans" },
        bodyColor: c.tipBody, padding: 10, cornerRadius: 8,
      },
    },
    scales: {
      x: { grid: { display: false }, ticks: tick, border: { display: false } },
      y: { grid: { color: c.grid }, ticks: tick, border: { display: false } },
    },
  };
});

const barOptsY = computed(() => ({ ...barOpts.value, indexAxis: "y" }));

const pieOpts = computed(() => {
  const c = chartTheme.value;
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: { backgroundColor: c.tipBg, borderColor: c.tipBorder, borderWidth: 1, titleColor: c.tipTitle, bodyColor: c.tipBody, padding: 10, cornerRadius: 8 },
    },
    cutout: "62%",
  };
});

// ── Format ────────────────────────────────────────────────────────────────
const formatRp = (v) => "Rp " + Math.round(v || 0).toLocaleString("id-ID");

// ── Export ────────────────────────────────────────────────────────────────
// Endpoint export hanya mengenal laporan bulanan dan tahunan. Mingguan/lifetime tidak diekspor:
// dulu keduanya diam-diam mengunduh laporan BULAN INI, tidak sesuai dengan angka di layar.
const canExport = computed(() => activeGroup.value === "monthly" || activeGroup.value === "yearly");

const exportDocument = (type) => {
  exportOpen.value = false;
  if (!canExport.value) return;
  const params = activeGroup.value === "yearly"
    ? `mode=yearly&year=${activeYear.value}`
    : `mode=monthly&month=${activeMonth.value}&year=${activeYear.value}`;
  window.open(`${apiClient.defaults.baseURL}/orders/export/finance-${type === "pdf" ? "pdf" : "excel"}/?${params}`, "_blank");
};

// ── Komponen lokal ────────────────────────────────────────────────────────
const iconMap = { TrendingUp, Award, ShoppingBag, DollarSign, Utensils, AlertTriangle, CreditCard, Clock, Users, Gem };

const accentText = {
  red: "text-[color:var(--red-soft)]", amber: "text-[color:var(--amber-soft)]", emerald: "text-[color:var(--green-soft)]",
  sky: "text-[color:var(--blue-soft)]", violet: "text-[color:var(--purple-soft)]", pink: "text-[color:var(--purple-soft)]",
};

const RCard = (props, { slots }) =>
  h("div", { class: "adm-card p-4 sm:p-6" }, [
    h("div", { class: "flex items-center gap-2 mb-4 sm:mb-5" }, [
      props.icon && iconMap[props.icon]
        ? h(iconMap[props.icon], { size: 13, class: accentText[props.accent] || "text-[color:var(--red-soft)]" })
        : null,
      h("h3", { class: "text-[color:var(--text-dim)] text-sm font-bold" }, props.title),
      props.subtitle
        ? h("span", { class: "text-[color:var(--text-faint)] text-xs ml-1" }, `· ${props.subtitle}`)
        : null,
    ]),
    slots.default ? slots.default() : null,
  ]);

const StatCard = (props) => {
  const bgMap  = { red: "tone-accent", amber: "tone-amber", emerald: "tone-green", sky: "tone-blue" };
  const txtMap = { red: "text-[color:var(--red-soft)]", amber: "text-[color:var(--amber-soft)]", emerald: "text-[color:var(--green-soft)]", sky: "text-[color:var(--blue-soft)]" };
  return h("div", { class: "adm-stat !block" }, [
    h("div", { class: `w-9 h-9 sm:w-10 sm:h-10 rounded-[var(--r-sm)] ${bgMap[props.color]} flex items-center justify-center mb-3 sm:mb-4` }, [
      iconMap[props.icon] ? h(iconMap[props.icon], { size: 17, class: txtMap[props.color] }) : null,
    ]),
    h("p", { class: "adm-stat-value truncate" }, String(props.value)),
    h("p", { class: "text-xs text-[color:var(--text-faint)] uppercase tracking-[0.15em] sm:tracking-[0.18em] mt-1" }, props.label),
    props.sub
      ? h("p", { class: "text-[11px] text-[color:var(--text-faint)] mt-1.5" }, props.sub)
      : null,
  ]);
};

const EmptyState = (props) =>
  h("div", { class: `text-center text-[color:var(--text-faint)] text-xs ${props.compact ? "py-4" : "py-8 sm:py-10"}` }, [
    props.emoji ? h("p", { class: "mb-1 text-base" }, props.emoji) : null,
    h("p", null, props.text),
  ]);

onMounted(fetchReport);
</script>

<style scoped>
.rep-select { width: auto; min-height: 40px; padding-block: 0.4rem; font-weight: 600; }
.rep-period { margin: 0; }
.rep-menu {
  position: absolute; right: 0; z-index: 40; width: 11rem; margin-top: 0.5rem; overflow: hidden;
  background: var(--surface); border: 1px solid var(--border-strong); border-radius: var(--r-md); box-shadow: var(--shadow-lg);
}
.rep-menu-item {
  display: flex; align-items: center; gap: 0.6rem; width: 100%; padding: 0.7rem 1rem;
  border: 0; background: transparent; color: var(--text-2); cursor: pointer;
  font-family: var(--font-body); font-size: 0.8125rem; font-weight: 600; text-align: left;
}
.rep-menu-item:hover { background: var(--surface-hover); color: var(--text); }
.custom-scroll::-webkit-scrollbar { width: 3px; }
.custom-scroll::-webkit-scrollbar-track { background: transparent; }
.custom-scroll::-webkit-scrollbar-thumb { background: rgb(var(--ink) / 0.1); border-radius: 99px; }

</style>