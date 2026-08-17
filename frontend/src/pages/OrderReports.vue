<template>
  <div class="w-full min-h-screen bg-[#070707]">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 pb-24">

      <!-- ═══ STICKY HEADER ═════════════════════════════════════════════ -->
      <div class="sticky top-0 z-30 -mx-4 sm:-mx-6 px-4 sm:px-6 pt-6 pb-4 bg-[#070707]/85 backdrop-blur-xl border-b border-white/[0.06]">
        <div class="flex flex-col sm:flex-row sm:justify-between sm:items-end gap-4">
          <div>
            <div class="flex items-center gap-2 mb-2">
              <span class="w-1 h-1 rounded-full bg-red-600"></span>
              <p class="text-white/30 text-[10px] font-oswald uppercase tracking-[0.25em]">Masashimura · Admin</p>
            </div>
            <h1 class="font-oswald text-3xl sm:text-4xl lg:text-5xl uppercase italic tracking-tighter text-red-600 leading-none">
              Order Reports
            </h1>
            <p class="text-white/35 text-xs sm:text-sm font-light mt-2">
              Analisis omzet, performa menu, dan pelanggan
            </p>
          </div>

          <div class="flex items-center gap-2 shrink-0">
            <!-- Refresh -->
            <button
              @click="fetch()"
              :disabled="loading"
              aria-label="Muat ulang data"
              class="flex items-center justify-center w-11 h-11 bg-white/[0.04] border border-white/10 rounded-xl text-white/50 hover:text-white hover:bg-white/[0.08] transition-all disabled:opacity-30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-600/60"
            >
              <RefreshCw :size="14" :class="{ 'animate-spin': loading }" />
            </button>

            <!-- Export dropdown -->
            <div class="relative" ref="exportMenuRef">
              <button
                v-if="activeGroup !== 'lifetime'"
                @click="exportOpen = !exportOpen"
                :disabled="loading"
                class="flex items-center gap-2 bg-white/[0.04] border border-white/10 px-4 sm:px-5 h-11 rounded-xl text-[10px] font-oswald uppercase tracking-widest hover:bg-white/[0.08] transition-all text-white disabled:opacity-30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-600/60"
              >
                <Download :size="13" class="text-red-500" />
                <span class="hidden sm:inline">Export</span>
                <ChevronDown :size="12" class="text-white/40" />
              </button>

              <Transition
                enter-active-class="transition duration-150 ease-out"
                enter-from-class="opacity-0 -translate-y-1"
                enter-to-class="opacity-100 translate-y-0"
                leave-active-class="transition duration-100 ease-in"
                leave-from-class="opacity-100"
                leave-to-class="opacity-0"
              >
                <div
                  v-if="exportOpen"
                  class="absolute right-0 mt-2 w-44 bg-[#0d0d0d] border border-white/10 rounded-xl shadow-2xl shadow-black/50 overflow-hidden z-40"
                >
                  <button
                    @click="exportDocument('pdf')"
                    class="w-full flex items-center gap-2.5 px-4 py-3 text-[11px] font-oswald uppercase tracking-widest text-white/70 hover:bg-white/5 hover:text-white transition-colors"
                  >
                    <FileText :size="13" class="text-red-500" /> Export PDF
                  </button>
                  <button
                    @click="exportDocument('excel')"
                    class="w-full flex items-center gap-2.5 px-4 py-3 text-[11px] font-oswald uppercase tracking-widest text-white/70 hover:bg-white/5 hover:text-white transition-colors border-t border-white/5"
                  >
                    <Sheet :size="13" class="text-emerald-500" /> Export Excel
                  </button>
                </div>
              </Transition>
            </div>
          </div>
        </div>

        <!-- ═══ FILTER BAR ══════════════════════════════════════════════ -->
        <div class="bg-[#0d0d0d] border border-white/8 rounded-2xl p-1.5 mt-5 flex flex-col sm:flex-row gap-1.5 sm:gap-1">

          <!-- Group tabs — horizontal scroll on mobile instead of wrapping -->
          <div class="flex gap-1 overflow-x-auto no-scrollbar sm:flex-1 sm:min-w-[260px]">
            <button
              v-for="g in groups"
              :key="g.value"
              @click="selectGroup(g.value)"
              :class="[
                'flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-[11px] font-oswald uppercase tracking-widest transition-all duration-200 whitespace-nowrap shrink-0 sm:flex-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-600/60',
                activeGroup === g.value
                  ? 'bg-red-600 text-white shadow-lg shadow-red-900/30'
                  : 'text-white/30 hover:text-white/60 hover:bg-white/5'
              ]"
            >
              <component :is="g.icon" :size="12" />
              {{ g.label }}
            </button>
          </div>

          <!-- Divider -->
          <div class="w-px bg-white/8 my-1 hidden sm:block"></div>
          <div class="h-px bg-white/8 mx-1 sm:hidden" v-if="activeGroup !== 'lifetime'"></div>

          <!-- Sub-filter: Mingguan -->
          <template v-if="activeGroup === 'weekly'">
            <div class="flex items-center gap-1 px-1 overflow-x-auto no-scrollbar">
              <button
                v-for="w in weekOptions"
                :key="w.value"
                @click="activeWeek = w.value; fetch()"
                :class="[
                  'px-4 py-3 rounded-xl text-[10px] font-oswald uppercase tracking-widest transition-all whitespace-nowrap shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-600/60',
                  activeWeek === w.value ? 'bg-white/10 text-white' : 'text-white/30 hover:text-white/50'
                ]"
              >
                {{ w.label }}
              </button>
            </div>
          </template>

          <!-- Sub-filter: Bulanan -->
          <template v-if="activeGroup === 'monthly'">
            <div class="flex items-center gap-2 px-1 sm:px-2">
              <select
                v-model.number="activeMonth"
                @change="fetch()"
                class="flex-1 sm:flex-none bg-transparent border border-white/10 rounded-lg px-3 py-2.5 text-[11px] font-oswald uppercase tracking-widest outline-none focus:border-red-600 text-white cursor-pointer"
              >
                <option v-for="m in 12" :key="m" :value="m" class="bg-[#111]">{{ monthName(m) }}</option>
              </select>
              <select
                v-model.number="activeYear"
                @change="fetch()"
                class="flex-1 sm:flex-none bg-transparent border border-white/10 rounded-lg px-3 py-2.5 text-[11px] font-oswald uppercase tracking-widest outline-none focus:border-red-600 text-white cursor-pointer"
              >
                <option v-for="y in yearOptions" :key="y" :value="y" class="bg-[#111]">{{ y }}</option>
              </select>
            </div>
          </template>

          <!-- Sub-filter: Tahunan -->
          <template v-if="activeGroup === 'yearly'">
            <div class="flex items-center gap-1 px-1 overflow-x-auto no-scrollbar">
              <button
                v-for="y in yearOptions"
                :key="y"
                @click="activeYear = y; fetch()"
                :class="[
                  'px-4 py-3 rounded-xl text-[11px] font-oswald uppercase tracking-widest transition-all whitespace-nowrap shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-600/60',
                  activeYear === y ? 'bg-white/10 text-white' : 'text-white/30 hover:text-white/50'
                ]"
              >
                {{ y }}
              </button>
            </div>
          </template>

          <!-- Sub-filter: Lifetime — just a label -->
          <template v-if="activeGroup === 'lifetime'">
            <div class="flex items-center px-4 py-2 sm:py-0">
              <span class="text-white/20 text-[10px] font-oswald uppercase tracking-widest">Semua waktu</span>
            </div>
          </template>
        </div>

        <!-- ═══ PERIOD BADGE ════════════════════════════════════════════ -->
        <div class="flex items-center gap-3 mt-5">
          <div class="h-px flex-1 bg-white/5"></div>
          <span class="text-white/25 text-[10px] font-oswald uppercase tracking-[0.25em] whitespace-nowrap">
            {{ periodLabel }}
          </span>
          <div class="h-px flex-1 bg-white/5"></div>
        </div>
      </div>

      <div class="pt-6">

        <!-- ═══ LOADING SKELETON ═══════════════════════════════════════ -->
        <div v-if="loading" class="space-y-5 animate-pulse">
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            <div v-for="i in 4" :key="i" class="bg-[#0a0a0a] border border-white/5 rounded-2xl p-5 h-[112px]">
              <div class="w-10 h-10 rounded-xl bg-white/5 mb-4"></div>
              <div class="w-16 h-4 bg-white/5 rounded mb-2"></div>
              <div class="w-20 h-2.5 bg-white/5 rounded"></div>
            </div>
          </div>
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <div class="bg-[#0a0a0a] border border-white/5 rounded-2xl p-6 h-64"></div>
            <div class="bg-[#0a0a0a] border border-white/5 rounded-2xl p-6 h-64"></div>
          </div>
          <p class="text-center text-white/20 text-[10px] font-oswald uppercase tracking-widest pt-2">
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
              <table class="w-full text-sm hidden sm:table">
                <thead>
                  <tr class="text-white/25 text-[9px] uppercase tracking-[0.15em]">
                    <th class="pb-4 text-left font-normal w-8">#</th>
                    <th class="pb-4 text-left font-normal">Menu</th>
                    <th class="pb-4 text-right font-normal">Qty</th>
                    <th class="pb-4 text-right font-normal">Omzet</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(m, i) in report.top_menu"
                    :key="i"
                    class="border-t border-white/4 group hover:bg-white/[0.03] transition-colors"
                  >
                    <td class="py-3 pr-3 text-white/20 text-xs font-oswald">{{ String(i+1).padStart(2,'0') }}</td>
                    <td class="py-3 text-white font-oswald uppercase tracking-tight text-sm">{{ m.name }}</td>
                    <td class="py-3 text-right">
                      <span class="bg-amber-500/10 text-amber-400 font-bold text-xs px-2.5 py-1 rounded-lg">{{ m.qty }}</span>
                    </td>
                    <td class="py-3 text-right text-white/50 font-mono text-xs">{{ formatRp(m.omzet) }}</td>
                  </tr>
                </tbody>
              </table>

              <!-- Mobile stacked cards -->
              <div class="flex flex-col gap-2 sm:hidden">
                <div
                  v-for="(m, i) in report.top_menu"
                  :key="i"
                  class="flex items-center justify-between bg-white/[0.02] border border-white/5 rounded-xl px-3.5 py-3"
                >
                  <div class="flex items-center gap-3 min-w-0">
                    <span class="text-white/20 text-[11px] font-oswald shrink-0">{{ String(i+1).padStart(2,'0') }}</span>
                    <div class="min-w-0">
                      <p class="text-white font-oswald uppercase tracking-tight text-xs truncate">{{ m.name }}</p>
                      <p class="text-white/40 text-[10px] font-mono mt-0.5">{{ formatRp(m.omzet) }}</p>
                    </div>
                  </div>
                  <span class="bg-amber-500/10 text-amber-400 font-bold text-[11px] px-2 py-1 rounded-lg shrink-0 ml-2">{{ m.qty }}</span>
                </div>
              </div>

              <EmptyState v-if="!report.top_menu.length" text="Belum ada data penjualan" />
            </RCard>

            <RCard title="Paling Menghasilkan" icon="Gem" accent="emerald">
              <div class="space-y-5">
                <div v-for="(m, i) in report.menu_paling_menghasilkan" :key="i">
                  <div class="flex justify-between text-xs mb-2 gap-2">
                    <span class="text-white font-oswald uppercase tracking-tight truncate">{{ m.name }}</span>
                    <span class="text-emerald-400 font-bold tabular-nums shrink-0">{{ formatRp(m.omzet) }}</span>
                  </div>
                  <div class="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
                    <div
                      class="h-full rounded-full transition-all duration-700"
                      :style="{ width: pct(m.omzet, maxMenghasilkan) + '%', background: 'linear-gradient(90deg, #10b981, #34d399)' }"
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
                  class="flex justify-between items-center bg-red-950/20 border border-red-500/8 rounded-xl px-4 py-3"
                >
                  <span class="text-white text-xs font-oswald uppercase tracking-tight truncate mr-2">{{ m.name }}</span>
                  <span class="text-red-400/70 text-[9px] font-bold uppercase tracking-wider shrink-0">
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
                      <div class="w-2 h-2 rounded-full shrink-0" :style="{ background: payColors[p.method] || '#6b7280' }"></div>
                      <span class="text-white/50 text-xs truncate">{{ p.label }}</span>
                    </div>
                    <span class="text-white text-xs font-bold tabular-nums shrink-0">{{ p.percent }}%</span>
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
                <p class="font-oswald text-2xl sm:text-4xl font-bold text-white mb-1">{{ report.pelanggan.baru }}</p>
                <p class="text-[8px] sm:text-[9px] text-white/30 uppercase tracking-[0.15em] sm:tracking-[0.2em]">Pelanggan Baru</p>
              </div>
              <div class="py-3 sm:py-4 border-x border-white/5">
                <p class="font-oswald text-2xl sm:text-4xl font-bold text-white mb-1">{{ report.pelanggan.lama }}</p>
                <p class="text-[8px] sm:text-[9px] text-white/30 uppercase tracking-[0.15em] sm:tracking-[0.2em]">Pelanggan Lama</p>
              </div>
              <div class="py-3 sm:py-4">
                <p class="font-oswald text-2xl sm:text-4xl font-bold text-amber-400 mb-1">{{ report.pelanggan.loyal_member }}</p>
                <p class="text-[8px] sm:text-[9px] text-white/30 uppercase tracking-[0.15em] sm:tracking-[0.2em]">Member Loyal</p>
              </div>
            </div>
          </RCard>
        </template>

        <!-- ═══ ERROR / EMPTY ═════════════════════════════════════════════ -->
        <div v-else class="flex flex-col items-center justify-center py-24 sm:py-32 text-center">
          <div class="w-12 h-12 rounded-2xl bg-red-500/10 flex items-center justify-center mb-4">
            <AlertTriangle :size="20" class="text-red-500" />
          </div>
          <p class="text-white text-sm font-oswald uppercase tracking-wide mb-1">Gagal memuat data</p>
          <p class="text-white/30 text-xs mb-5">Periksa koneksi atau coba lagi beberapa saat.</p>
          <button
            @click="fetch()"
            class="flex items-center gap-2 bg-red-600 hover:bg-red-500 text-white text-[11px] font-oswald uppercase tracking-widest px-5 py-3 rounded-xl transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400"
          >
            <RefreshCw :size="13" /> Muat ulang
          </button>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, h } from "vue";
import { Bar, Pie } from "vue-chartjs";
import {
  Chart as ChartJS, BarElement, CategoryScale, LinearScale,
  ArcElement, Tooltip, Legend,
} from "chart.js";
import {
  TrendingUp, Award, Download, ShoppingBag, DollarSign, Utensils,
  AlertTriangle, CreditCard, Clock, Users, Gem, Calendar,
  CalendarDays, CalendarRange, Infinity, RefreshCw, ChevronDown,
  FileText, Sheet,
} from "lucide-vue-next";
import apiClient from "@/api/client";

ChartJS.register(BarElement, CategoryScale, LinearScale, ArcElement, Tooltip, Legend);

// ── Filter state ──────────────────────────────────────────────────────────
const now        = new Date();
const loading    = ref(true);
const report     = ref(null);
const exportOpen = ref(false);
const exportMenuRef = ref(null);

const activeGroup = ref("lifetime");   // lifetime | weekly | monthly | yearly
const activeWeek  = ref("this");       // this | last
const activeMonth = ref(now.getMonth() + 1);
const activeYear  = ref(now.getFullYear());

const groups = [
  { label: "Lifetime",  value: "lifetime", icon: Infinity },
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
onMounted(() => document.addEventListener("click", handleClickOutside));
onBeforeUnmount(() => document.removeEventListener("click", handleClickOutside));

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
    const daysMap = { this: 7, last: 14, "2w": 14, "4w": 28 };
    const offset  = { this: 0, last: 7, "2w": 0, "4w": 0 };
    return { period: "week", days: daysMap[activeWeek.value], offset: offset[activeWeek.value] };
  }
  if (g === "monthly") return { period: "month", month: activeMonth.value, year: activeYear.value };
  return { period: "year", year: activeYear.value };
};

// ── Fetch ─────────────────────────────────────────────────────────────────
const fetch = async () => {
  loading.value = true;
  try {
    const { data } = await apiClient.get("/orders/reports/full/", { params: buildParams() });
    report.value = data;
  } catch (e) {
    console.error("Gagal load report:", e);
    report.value = null;
  } finally {
    loading.value = false;
  }
};

const selectGroup = (g) => {
  activeGroup.value = g;
  fetch();
};

// ── Chart data ────────────────────────────────────────────────────────────
const omzetData = computed(() => ({
  labels: report.value?.trend.labels || [],
  datasets: [{
    label: "Omzet",
    data: report.value?.trend.omzet || [],
    backgroundColor: "#dc2626",
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
    backgroundColor: "#f59e0b",
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
    backgroundColor: "#8b5cf6",
    borderRadius: 6,
    borderSkipped: false,
  }],
}));

const payColors = { cash: "#22c55e", qris: "#3b82f6", qris_manual: "#06b6d4", gateway: "#a855f7" };
const paymentData = computed(() => ({
  labels: report.value?.metode_pembayaran.map(p => p.label) || [],
  datasets: [{
    data: report.value?.metode_pembayaran.map(p => p.total) || [],
    backgroundColor: report.value?.metode_pembayaran.map(p => payColors[p.method] || "#374151") || [],
    borderWidth: 0,
    hoverOffset: 6,
  }],
}));

const maxMenghasilkan = computed(() =>
  Math.max(1, ...(report.value?.menu_paling_menghasilkan.map(m => m.omzet) || [1]))
);
const pct = (v, max) => Math.round((v / max) * 100);

// ── Chart options ─────────────────────────────────────────────────────────
const gridColor = "rgba(255,255,255,0.04)";
const tickStyle = { color: "rgba(255,255,255,0.35)", font: { size: 10, family: "Oswald" } };

const barOpts = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: "#111",
      borderColor: "rgba(255,255,255,0.08)",
      borderWidth: 1,
      titleColor: "#fff",
      titleFont: { family: "Oswald" },
      bodyColor: "rgba(255,255,255,0.6)",
      padding: 10,
      cornerRadius: 8,
    },
  },
  scales: {
    x: { grid: { display: false }, ticks: tickStyle, border: { display: false } },
    y: { grid: { color: gridColor }, ticks: tickStyle, border: { display: false } },
  },
};

const barOptsY = {
  ...barOpts,
  indexAxis: "y",
};

const pieOpts = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: "#111",
      borderColor: "rgba(255,255,255,0.08)",
      borderWidth: 1,
      padding: 10,
      cornerRadius: 8,
    },
  },
  cutout: "62%",
};

// ── Format ────────────────────────────────────────────────────────────────
const formatRp = (v) => "Rp " + Math.round(v || 0).toLocaleString("id-ID");

// ── Export ────────────────────────────────────────────────────────────────
const exportDocument = (type) => {
  exportOpen.value = false;
  const g = activeGroup.value;
  let params = "";
  if (g === "monthly") params = `mode=monthly&month=${activeMonth.value}&year=${activeYear.value}`;
  else if (g === "yearly") params = `mode=yearly&year=${activeYear.value}`;
  else params = `mode=monthly&month=${activeMonth.value}&year=${activeYear.value}`;
  window.open(`${apiClient.defaults.baseURL}/orders/export/finance-${type === "pdf" ? "pdf" : "excel"}/?${params}`, "_blank");
};

// ── Komponen lokal ────────────────────────────────────────────────────────
const iconMap = { TrendingUp, Award, ShoppingBag, DollarSign, Utensils, AlertTriangle, CreditCard, Clock, Users, Gem };

const accentText = {
  red: "text-red-400", amber: "text-amber-400", emerald: "text-emerald-400",
  sky: "text-sky-400", violet: "text-violet-400", pink: "text-pink-400",
};

const RCard = (props, { slots }) =>
  h("div", { class: "bg-[#0a0a0a] border border-white/5 rounded-2xl p-4 sm:p-6 hover:border-white/10 transition-all duration-500" }, [
    h("div", { class: "flex items-center gap-2 mb-4 sm:mb-5" }, [
      props.icon && iconMap[props.icon]
        ? h(iconMap[props.icon], { size: 13, class: accentText[props.accent] || "text-red-400" })
        : null,
      h("h3", { class: "font-oswald uppercase text-white/30 text-[10px] tracking-[0.18em]" }, props.title),
      props.subtitle
        ? h("span", { class: "text-white/15 text-[10px] font-light ml-1" }, `· ${props.subtitle}`)
        : null,
    ]),
    slots.default ? slots.default() : null,
  ]);

const StatCard = (props) => {
  const bgMap  = { red: "bg-red-500/8", amber: "bg-amber-500/8", emerald: "bg-emerald-500/8", sky: "bg-sky-500/8" };
  const txtMap = { red: "text-red-400", amber: "text-amber-400", emerald: "text-emerald-400", sky: "text-sky-400" };
  return h("div", { class: "bg-[#0a0a0a] border border-white/5 p-4 sm:p-5 rounded-2xl hover:border-white/10 transition-all duration-300" }, [
    h("div", { class: `w-9 h-9 sm:w-10 sm:h-10 rounded-xl ${bgMap[props.color]} flex items-center justify-center mb-3 sm:mb-4` }, [
      iconMap[props.icon] ? h(iconMap[props.icon], { size: 17, class: txtMap[props.color] }) : null,
    ]),
    h("p", { class: "font-oswald text-lg sm:text-xl font-bold text-white leading-tight truncate" }, String(props.value)),
    h("p", { class: "text-[8.5px] sm:text-[9px] text-white/30 uppercase tracking-[0.15em] sm:tracking-[0.18em] mt-1" }, props.label),
    props.sub
      ? h("p", { class: "text-[9px] text-white/15 mt-1.5" }, props.sub)
      : null,
  ]);
};

const EmptyState = (props) =>
  h("div", { class: `text-center text-white/20 text-xs ${props.compact ? "py-4" : "py-8 sm:py-10"}` }, [
    props.emoji ? h("p", { class: "mb-1 text-base" }, props.emoji) : null,
    h("p", null, props.text),
  ]);

onMounted(fetch);
</script>

<style scoped>
.custom-scroll::-webkit-scrollbar { width: 3px; }
.custom-scroll::-webkit-scrollbar-track { background: transparent; }
.custom-scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 99px; }

.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>