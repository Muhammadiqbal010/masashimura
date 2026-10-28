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
            v-if="activeTab === 'ringkasan'"
            type="button"
            @click="exportOpen = !exportOpen"
            aria-haspopup="menu"
            :aria-expanded="exportOpen"
            :disabled="loading || !report"
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
              <button type="button" role="menuitem" @click="exportCsv" class="rep-menu-item">
                <Table2 :size="13" class="text-[color:var(--blue-soft)]" /> Unduh CSV (tampilan ini)
              </button>
              <button type="button" role="menuitem" :disabled="!canExport" @click="exportDocument('pdf')" class="rep-menu-item">
                <FileText :size="13" class="text-[color:var(--accent-text)]" /> Export PDF
              </button>
              <button type="button" role="menuitem" :disabled="!canExport" @click="exportDocument('excel')" class="rep-menu-item">
                <Sheet :size="13" class="text-[color:var(--green-soft)]" /> Export Excel
              </button>
              <p v-if="!canExport" class="rd-menu-hint">PDF &amp; Excel keuangan hanya tersedia untuk periode Bulanan atau Tahunan.</p>
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
      <p class="rd-period-line rep-period">
        <strong>{{ periodLabel }}</strong>
        <span v-if="rangeText">{{ rangeText }}</span>
        <span v-if="report?.previous">Pembanding: {{ report.previous.label }}</span>
      </p>
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
        <div v-else-if="loading && !report" class="rd animate-pulse" aria-busy="true">
          <div class="rd-kpis">
            <div v-for="i in 4" :key="i" class="rd-kpi" style="min-height: 10.5rem"></div>
          </div>
          <div class="rd-grid">
            <div class="rd-card rd-col-8" style="height: 20rem"></div>
            <div class="rd-card rd-col-4" style="height: 20rem"></div>
          </div>
          <p class="text-center text-[color:var(--text-faint)] text-[11px] font-semibold pt-2">Memuat data laporan...</p>
        </div>

        <!-- ═══ CONTENT ═════════════════════════════════════════════════ -->
        <div v-else-if="report" class="rd" :class="{ 'opacity-60 pointer-events-none transition-opacity': loading }">

          <!-- 1. KPI -->
          <section class="rd-kpis" aria-label="Ringkasan angka utama">
            <ReportKpi hero :icon="DollarSign" label="Total Omzet" :value="formatRp(report.stats.total_omzet)"
              :delta="report.delta?.omzet ?? null" :delta-label="report.previous?.label" :spark="report.trend.omzet"
              :sub="omzetSub" />
            <ReportKpi :icon="ShoppingBag" label="Total Transaksi" :value="num(report.stats.total_transaksi)"
              :delta="report.delta?.transaksi ?? null" :delta-label="report.previous?.label" :spark="report.trend.transaksi"
              :sub="trxSub" />
            <ReportKpi :icon="TrendingUp" label="Rata-rata Transaksi" :value="formatRp(report.stats.rata_rata_transaksi)"
              :delta="report.delta?.rata_rata ?? null" :delta-label="report.previous?.label" :spark="avgSpark"
              sub="Omzet dibagi jumlah transaksi" />
            <ReportKpi :icon="Utensils" label="Porsi Terjual" :value="num(report.stats.porsi_terjual)"
              :delta="report.delta?.porsi ?? null" :delta-label="report.previous?.label"
              :sub="`${report.stats.menu_aktif} menu aktif · ${report.menu_tidak_terjual} belum terjual`" />
          </section>

          <!-- 2. INSIGHT OTOMATIS -->
          <section v-if="insights.length" class="rd-insights" aria-label="Sorotan otomatis">
            <div v-for="(it, i) in insights" :key="i" class="rd-insight" :class="`is-${it.tone}`">
              <span class="rd-insight-ico" aria-hidden="true"><component :is="it.icon" :size="14" /></span>
              <span v-html="it.html"></span>
            </div>
          </section>

          <!-- 3. TREN + PEMBAYARAN -->
          <div class="rd-grid">
            <section class="rd-card rd-col-8">
              <div class="rd-card-head">
                <div>
                  <h3 class="rd-card-title">Tren {{ metric === 'omzet' ? 'Omzet' : 'Transaksi' }}</h3>
                  <p class="rd-card-sub">{{ trendSub }}</p>
                </div>
                <div class="rd-toggle" role="group" aria-label="Metrik tren">
                  <button type="button" :aria-pressed="metric === 'omzet'" @click="metric = 'omzet'">Omzet</button>
                  <button type="button" :aria-pressed="metric === 'transaksi'" @click="metric = 'transaksi'">Transaksi</button>
                </div>
              </div>
              <div v-if="hasTrend" class="rd-chart"><Bar :data="trendData" :options="trendOpts" /></div>
              <p v-else class="rd-empty">Belum ada transaksi di periode ini.</p>
            </section>

            <section class="rd-card rd-col-4">
              <div class="rd-card-head">
                <div>
                  <h3 class="rd-card-title">Metode Pembayaran</h3>
                  <p class="rd-card-sub">Porsi dari total omzet</p>
                </div>
              </div>
              <ReportDonut v-if="report.metode_pembayaran.length" :segments="paySegments"
                :center-value="rpShort(report.stats.total_omzet)" center-label="total omzet" />
              <p v-else class="rd-empty">Belum ada transaksi.</p>
            </section>
          </div>

          <!-- 4. MENU -->
          <div class="rd-grid">
            <section class="rd-card rd-col-8">
              <div class="rd-card-head">
                <div>
                  <h3 class="rd-card-title">Menu Terbaik</h3>
                  <p class="rd-card-sub">10 teratas menurut {{ rankBy === 'qty' ? 'jumlah porsi' : 'omzet' }}</p>
                </div>
                <div class="rd-toggle" role="group" aria-label="Urutkan menu">
                  <button type="button" :aria-pressed="rankBy === 'qty'" @click="rankBy = 'qty'">Terlaris</button>
                  <button type="button" :aria-pressed="rankBy === 'omzet'" @click="rankBy = 'omzet'">Paling menghasilkan</button>
                </div>
              </div>
              <ReportRank v-if="rankItems.length" :items="rankItems"
                :color="rankBy === 'qty' ? 'var(--amber-soft)' : 'var(--green)'" />
              <p v-else class="rd-empty">Belum ada data penjualan.</p>
            </section>

            <section class="rd-card rd-col-4">
              <div class="rd-card-head">
                <div>
                  <h3 class="rd-card-title">Omzet per Kategori</h3>
                  <p class="rd-card-sub">Dari penjualan menu</p>
                </div>
              </div>
              <ReportDonut v-if="report.kategori.length" :segments="kategoriSegments"
                :center-value="String(report.kategori.length)" center-label="kategori" />
              <p v-else class="rd-empty">Belum ada data.</p>
            </section>
          </div>

          <!-- 5. WAKTU -->
          <div class="rd-grid">
            <section class="rd-card rd-col-8">
              <div class="rd-card-head">
                <div>
                  <h3 class="rd-card-title">Jam Ramai</h3>
                  <p class="rd-card-sub">Jumlah transaksi menurut jam (WIB){{ peakHour ? ` · puncak ${peakHour.range}` : '' }}</p>
                </div>
              </div>
              <div v-if="report.jam_distribusi.length" class="rd-chart rd-chart--sm"><Bar :data="jamData" :options="jamOpts" /></div>
              <p v-else class="rd-empty">Belum ada transaksi.</p>
            </section>

            <section class="rd-card rd-col-4">
              <div class="rd-card-head">
                <div>
                  <h3 class="rd-card-title">Hari dalam Seminggu</h3>
                  <p class="rd-card-sub">Rata-rata omzet per hari aktif</p>
                </div>
              </div>
              <ul class="rd-days">
                <li v-for="d in report.per_hari" :key="d.day" :class="{ 'is-best': d.day === bestWeekday }">
                  <span class="rd-days-name">{{ d.short }}</span>
                  <span class="rd-days-track" aria-hidden="true"><span :style="{ width: weekdayPct(d) + '%' }"></span></span>
                  <span class="rd-days-val" :class="{ 'is-none': !d.active_days }">{{ d.active_days ? rpShort(d.avg_omzet) : 'Tidak ada' }}</span>
                </li>
              </ul>
              <p class="rd-note">Hari tanpa transaksi tidak ikut dirata-rata.</p>
            </section>
          </div>

          <!-- 6. PELANGGAN + MENU KURANG LAKU -->
          <div class="rd-grid">
            <section class="rd-card rd-col-8">
              <div class="rd-card-head">
                <div>
                  <h3 class="rd-card-title">Pelanggan &amp; Layanan</h3>
                  <p class="rd-card-sub">Pelanggan dikenali dari nomor telepon pesanan</p>
                </div>
              </div>
              <div class="rd-mini">
                <div class="rd-mini-item"><strong>{{ num(report.pelanggan.baru) }}</strong><span>Pelanggan baru</span></div>
                <div class="rd-mini-item"><strong>{{ num(report.pelanggan.lama) }}</strong><span>Pelanggan lama</span></div>
                <div class="rd-mini-item is-amber"><strong>{{ num(report.pelanggan.loyal_member) }}</strong><span>Member loyal</span></div>
                <div class="rd-mini-item"><strong>{{ pct(report.pelanggan.repeat_rate) }}</strong><span>Kembali berbelanja</span></div>
              </div>
              <p v-if="report.pelanggan.tanpa_nomor" class="rd-note">
                {{ num(report.pelanggan.tanpa_nomor) }} transaksi tanpa nomor telepon tidak masuk hitungan pelanggan.
              </p>

              <h4 class="rd-subhead">Jenis layanan</h4>
              <ReportRank v-if="report.layanan.length" :items="layananItems" color="var(--blue-soft)" />
              <p v-else class="rd-empty">Belum ada transaksi.</p>
            </section>

            <section class="rd-card rd-col-4">
              <div class="rd-card-head">
                <div>
                  <h3 class="rd-card-title">Menu Kurang Laku</h3>
                  <p class="rd-card-sub">{{ report.menu_tidak_terjual }} dari {{ report.stats.menu_aktif }} menu aktif belum terjual</p>
                </div>
              </div>
              <div v-if="report.menu_tidak_laku.length" class="rd-unsold custom-scroll">
                <div v-for="(m, i) in report.menu_tidak_laku" :key="i" class="rd-unsold-row">
                  <span>{{ m.name }}</span><span>{{ m.transaksi }}×</span>
                </div>
              </div>
              <p v-else class="rd-empty">Semua menu terjual 🎉</p>
              <p class="rd-note">Detail kelompok tiap menu ada di tab Performa Menu.</p>
            </section>
          </div>
        </div>

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
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue";
import { useRoute } from "vue-router";
import { Bar } from "vue-chartjs";
import {
  Chart as ChartJS, BarElement, LineElement, PointElement, CategoryScale, LinearScale, Tooltip, Legend, Filler,
} from "chart.js";
import {
  TrendingUp, Download, ShoppingBag, DollarSign, Utensils, AlertTriangle, Calendar,
  CalendarDays, CalendarRange, Infinity as InfinityIcon, RefreshCw, ChevronDown,
  FileText, Sheet, Table2, Trophy, Clock, Tag, Users, TrendingDown,
} from "lucide-vue-next";
import apiClient from "@/api/client";
import BusyHoursTab from "@/components/ui/admin/BusyHoursTab.vue";
import MenuPerformanceTab from "@/components/ui/admin/MenuPerformanceTab.vue";
import MenuPairsTab from "@/components/ui/admin/MenuPairsTab.vue";
import ChannelTab from "@/components/ui/admin/ChannelTab.vue";
import ReportKpi from "@/components/ui/admin/report/ReportKpi.vue";
import ReportDonut from "@/components/ui/admin/report/ReportDonut.vue";
import ReportRank from "@/components/ui/admin/report/ReportRank.vue";
import { useTheme } from "@/composables/useTheme";

ChartJS.register(BarElement, LineElement, PointElement, CategoryScale, LinearScale, Tooltip, Legend, Filler);

// ── Filter state ──────────────────────────────────────────────────────────
const now        = new Date();
const loading    = ref(true);
const report     = ref(null);
const exportOpen = ref(false);
const exportMenuRef = ref(null);

// Tab halaman: Ringkasan | Performa Menu | Pasangan Menu | Channel | Jam Sibuk
const activeTab = ref("ringkasan");
const tabRef    = ref(null);
const pageTabs  = [
  { label: "Ringkasan",    value: "ringkasan", sub: "Analisis omzet, performa menu, dan pelanggan" },
  { label: "Performa Menu", value: "performa",  sub: "Volume, kontribusi omzet, dan kelompok tiap menu" },
  { label: "Pasangan Menu", value: "pasangan",  sub: "Menu yang sering dipesan bersamaan, dasar ide paket" },
  { label: "Channel",       value: "channel",   sub: "Perbandingan pesanan web pelanggan dan POS kasir" },
  { label: "Jam Sibuk",     value: "jam",       sub: "Pola jam dan hari tersibuk dari data pesanan" },
];
// ?tab= dari pencarian global (mis. /admin/reports?tab=jam)
const route = useRoute();
watch(
  () => route.query.tab,
  (t) => { if (pageTabs.some((x) => x.value === t)) activeTab.value = t; },
  { immediate: true },
);
const activeTabSubtitle = computed(() => pageTabs.find((t) => t.value === activeTab.value)?.sub || "");
const refresh = () => (activeTab.value === "ringkasan" ? fetchReport() : tabRef.value?.reload());

const activeGroup = ref("lifetime");   // lifetime | weekly | monthly | yearly
const activeWeek  = ref("this");       // this | last | 2w | 4w
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
  if (exportMenuRef.value && !exportMenuRef.value.contains(e.target)) exportOpen.value = false;
};
const handleEsc = (e) => { if (e.key === "Escape") exportOpen.value = false; };
onMounted(() => { document.addEventListener("click", handleClickOutside); document.addEventListener("keydown", handleEsc); });
onBeforeUnmount(() => { document.removeEventListener("click", handleClickOutside); document.removeEventListener("keydown", handleEsc); });

// ── Derived labels ────────────────────────────────────────────────────────
const periodLabel = computed(() => {
  if (activeGroup.value === "lifetime") return "Semua data tersimpan";
  if (activeGroup.value === "weekly") return weekOptions.find((w) => w.value === activeWeek.value)?.label || "Mingguan";
  if (activeGroup.value === "monthly") return `${monthName(activeMonth.value)} ${activeYear.value}`;
  return `Tahun ${activeYear.value}`;
});

const fmtDate = (iso) => {
  const [y, m, d] = iso.split("-").map(Number);
  return `${d} ${BULAN[m - 1]} ${y}`;
};
// Rentang tanggal nyata dari server, supaya "Minggu ini" / "4 minggu" tidak ambigu.
const rangeText = computed(() => {
  const p = report.value?.period;
  if (!p?.start || !p?.end || activeGroup.value === "monthly" || activeGroup.value === "yearly") return "";
  return `${fmtDate(p.start)} – ${fmtDate(p.end)}`;
});

const trendSub = computed(() => {
  const t = report.value?.trend;
  const unit = t?.unit === "month" ? "per bulan" : "per hari";
  return `${periodLabel.value} · ${unit}`;
});

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
// Hanya request TERAKHIR yang boleh mengisi layar, supaya jawaban lambat dari filter lama tidak menimpa filter aktif.
let reportRequestId = 0;
const fetchReport = async () => {
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

// ── Format ────────────────────────────────────────────────────────────────
const formatRp = (v) => "Rp " + Math.round(v || 0).toLocaleString("id-ID");
const num = (v) => Number(v || 0).toLocaleString("id-ID");
const pct = (v) => `${Number(v || 0).toLocaleString("id-ID", { maximumFractionDigits: 1 })}%`;
const dec1 = (v, max = 1) => Number(v || 0).toLocaleString("id-ID", { maximumFractionDigits: max });
// Rupiah ringkas untuk sumbu grafik, pusat donat, dan daftar sempit.
const rpShort = (v) => {
  const n = Math.round(v || 0), a = Math.abs(n);
  if (a >= 1e9) return `Rp ${dec1(n / 1e9, 2)} M`;
  if (a >= 1e6) return `Rp ${dec1(n / 1e6, 2)} jt`;
  if (a >= 1e3) return `Rp ${dec1(n / 1e3, 1)} rb`;
  return `Rp ${n}`;
};

// ── KPI ───────────────────────────────────────────────────────────────────
const omzetSub = computed(() => {
  const h = report.value?.highlights;
  if (!h?.active_days) return "";
  return `≈ ${rpShort(h.avg_omzet_per_active_day)} per hari aktif`;
});
const trxSub = computed(() => {
  const h = report.value?.highlights;
  if (!h?.active_days) return "";
  return `≈ ${dec1(h.avg_trx_per_active_day)} transaksi per hari aktif`;
});
// Rata-rata per titik tren; titik tanpa transaksi mewarisi nilai sebelumnya supaya garis tidak jatuh ke 0.
const avgSpark = computed(() => {
  const t = report.value?.trend;
  if (!t) return [];
  let last = 0;
  return t.omzet.map((o, i) => (t.transaksi[i] ? (last = o / t.transaksi[i]) : last));
});

// ── Insight otomatis ──────────────────────────────────────────────────────
const peakHour = computed(() => {
  const j = report.value?.jam_distribusi || [];
  const best = j.reduce((a, b) => (b.count > (a?.count ?? 0) ? b : a), null);
  return best && best.count > 0 ? best : null;
});
const bestWeekday = computed(() => {
  const d = report.value?.per_hari || [];
  const best = d.reduce((a, b) => (b.avg_omzet > (a?.avg_omzet ?? 0) ? b : a), null);
  return best && best.avg_omzet > 0 ? best.day : null;
});

const insights = computed(() => {
  const r = report.value;
  if (!r || !r.stats.total_transaksi) return [];
  const out = [];
  const b = (s) => `<strong>${s}</strong>`;
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  if (r.delta?.omzet != null && Math.abs(r.delta.omzet) >= 0.1) {
    const up = r.delta.omzet > 0;
    out.push({
      tone: up ? "good" : "bad", icon: up ? TrendingUp : TrendingDown,
      html: `Omzet ${up ? "naik" : "turun"} ${b(pct(Math.abs(r.delta.omzet)))} dibanding ${esc(r.previous.label)}.`,
    });
  }
  const best = r.highlights.best_day;
  if (best) out.push({ tone: "good", icon: Trophy, html: `Hari terbaik: ${b(esc(best.label))} dengan omzet ${b(rpShort(best.omzet))} dari ${best.transaksi} transaksi.` });
  if (peakHour.value) out.push({ tone: "warn", icon: Clock, html: `Paling ramai pukul ${b(peakHour.value.range)} (${peakHour.value.count} transaksi).` });
  const top = r.top_menu[0];
  if (top) out.push({ tone: "warn", icon: Utensils, html: `${b(esc(top.name))} paling laris: ${num(top.qty)} porsi.` });
  const cat = r.kategori[0];
  if (cat && r.kategori.length > 1) out.push({ tone: "warn", icon: Tag, html: `Kategori ${b(esc(cat.name))} menyumbang ${b(pct(cat.share))} omzet menu.` });
  if (r.pelanggan.unik >= 5) out.push({ tone: "warn", icon: Users, html: `${b(pct(r.pelanggan.repeat_rate))} pelanggan adalah pelanggan lama yang kembali.` });
  return out.slice(0, 4);
});

// ── Chart theme (canvas tidak bisa baca CSS variable) ─────────────────────
const { isDark } = useTheme();
const chartTheme = computed(() => isDark.value
  ? { grid: "rgba(255,255,255,0.05)", tick: "rgba(255,255,255,0.55)", tipBg: "#151518", tipBorder: "rgba(255,255,255,0.12)", tipTitle: "#fafafa", tipBody: "rgba(255,255,255,0.75)", line: "#f5f3ef", muted: "rgba(199,155,247,0.35)" }
  : { grid: "rgba(24,24,27,0.07)",   tick: "rgba(24,24,27,0.65)",    tipBg: "#ffffff", tipBorder: "rgba(24,24,27,0.15)",    tipTitle: "#18181b", tipBody: "#3f3f46", line: "#18181b", muted: "rgba(122,46,194,0.28)" });

const baseOpts = (c, { yFormat } = {}) => {
  const tick = { color: c.tick, font: { size: 11, family: "Plus Jakarta Sans" } };
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: c.tipBg, borderColor: c.tipBorder, borderWidth: 1,
        titleColor: c.tipTitle, titleFont: { family: "Plus Jakarta Sans" },
        bodyColor: c.tipBody, padding: 10, cornerRadius: 8,
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: {
          ...tick,
          maxRotation: 0,
          autoSkip: true,
          autoSkipPadding: 24,
          maxTicksLimit: 12,
          // Cuma angka tanggal; nama bulan hanya di label pertama & saat bulan berganti.
          callback(value) {
            const cur = String(this.getLabelForValue(value) || "");
            const [day, mon] = cur.split(" ");
            if (!mon) return cur;
            const prev = value > 0 ? String(this.getLabelForValue(value - 1) || "").split(" ")[1] : null;
            return prev === mon ? day : cur;
          },
        },
        border: { display: false },
      },
      y: { beginAtZero: true, grid: { color: c.grid }, ticks: { ...tick, ...(yFormat ? { callback: yFormat } : {}) }, border: { display: false } },
    },
  };
};

// ── Tren ──────────────────────────────────────────────────────────────────
const metric = ref("omzet");
const hasTrend = computed(() => (report.value?.trend.transaksi || []).some((n) => n > 0));

const trendData = computed(() => {
  const t = report.value?.trend;
  if (!t) return { labels: [], datasets: [] };
  const isOmzet = metric.value === "omzet";
  const datasets = [{
    type: "bar",
    label: isOmzet ? "Omzet" : "Transaksi",
    data: isOmzet ? t.omzet : t.transaksi,
    backgroundColor: isOmzet ? "#d92b22" : "#f4c542",
    borderRadius: 6, borderSkipped: false, maxBarThickness: 34, order: 2,
  }];
  if (isOmzet && t.moving_avg?.length) {
    datasets.push({
      type: "line", label: "Rata-rata 7 hari", data: t.moving_avg, order: 1,
      borderColor: chartTheme.value.line, borderWidth: 2, pointRadius: 0, pointHoverRadius: 4, tension: 0.35,
    });
  }
  return { labels: t.labels, datasets };
});

const trendOpts = computed(() => {
  const c = chartTheme.value;
  const isOmzet = metric.value === "omzet";
  const o = baseOpts(c, { yFormat: isOmzet ? (v) => rpShort(v) : (v) => (Number.isInteger(v) ? v : "") });
  o.plugins.legend = { display: isOmzet && !!report.value?.trend.moving_avg?.length, labels: { color: c.tick, boxWidth: 10, boxHeight: 2, font: { size: 11 } } };
  o.plugins.tooltip.callbacks = {
    label: (ctx) => ` ${ctx.dataset.label}: ${isOmzet ? formatRp(ctx.parsed.y) : num(ctx.parsed.y) + " transaksi"}`,
  };
  return o;
});

// ── Pembayaran / kategori / layanan ───────────────────────────────────────
const payColors = { cash: "#2fb36d", qris: "#7cc4f5", qris_manual: "#f4c542", gateway: "#c79bf7" };
const fallbackColors = ["#d92b22", "#f4c542", "#2fb36d", "#7cc4f5", "#c79bf7", "#ff9f5a", "#9a9aa3"];

const paySegments = computed(() => (report.value?.metode_pembayaran || []).map((p, i) => ({
  label: p.label, value: p.total, color: payColors[p.method] || fallbackColors[i % fallbackColors.length],
  text: `${rpShort(p.total)} · ${pct(p.percent)}`,
})));

const kategoriSegments = computed(() => {
  const k = report.value?.kategori || [];
  const MAX = 5;
  const head = k.slice(0, MAX);
  const rest = k.slice(MAX);
  const segs = head.map((c, i) => ({ label: c.name, value: c.omzet, color: fallbackColors[i], text: `${rpShort(c.omzet)} · ${pct(c.share)}` }));
  if (rest.length) {
    const omzet = rest.reduce((a, c) => a + c.omzet, 0);
    segs.push({ label: `Lainnya (${rest.length})`, value: omzet, color: "#9a9aa3", text: `${rpShort(omzet)} · ${pct(rest.reduce((a, c) => a + c.share, 0))}` });
  }
  return segs;
});

const layananItems = computed(() => (report.value?.layanan || []).map((l) => ({
  name: l.label, value: l.count, valueText: `${num(l.count)} transaksi · ${pct(l.percent)}`,
  meta: `Omzet ${formatRp(l.total)}`,
})));

// ── Menu ──────────────────────────────────────────────────────────────────
const rankBy = ref("qty");
const rankItems = computed(() => {
  const r = report.value;
  if (!r) return [];
  const list = rankBy.value === "qty" ? r.top_menu : r.menu_paling_menghasilkan;
  return list.map((m) => ({
    name: m.name,
    value: rankBy.value === "qty" ? m.qty : m.omzet,
    valueText: rankBy.value === "qty" ? `${num(m.qty)} porsi` : formatRp(m.omzet),
    meta: rankBy.value === "qty" ? `${formatRp(m.omzet)} · ${pct(m.share)} omzet menu` : `${num(m.qty)} porsi · ${pct(m.share)} omzet menu`,
  }));
});

// ── Jam & hari ────────────────────────────────────────────────────────────
const jamData = computed(() => {
  const j = report.value?.jam_distribusi || [];
  const peak = peakHour.value?.hour;
  const c = chartTheme.value;
  return {
    labels: j.map((x) => x.label),
    datasets: [{
      label: "Transaksi", data: j.map((x) => x.count),
      backgroundColor: j.map((x) => (x.hour === peak ? "#d92b22" : c.muted)),
      borderRadius: 6, borderSkipped: false, maxBarThickness: 30,
    }],
  };
});
const jamOpts = computed(() => {
  const o = baseOpts(chartTheme.value, { yFormat: (v) => (Number.isInteger(v) ? v : "") });
  o.plugins.tooltip.callbacks = {
    title: (items) => report.value?.jam_distribusi[items[0].dataIndex]?.range || "",
    label: (ctx) => ` ${num(ctx.parsed.y)} transaksi`,
  };
  return o;
});

const weekdayMax = computed(() => Math.max(1, ...(report.value?.per_hari || []).map((d) => d.avg_omzet)));
const weekdayPct = (d) => (d.active_days ? Math.max(3, Math.round((d.avg_omzet / weekdayMax.value) * 100)) : 0);

// ── Export ────────────────────────────────────────────────────────────────
// PDF/Excel keuangan hanya mengenal laporan bulanan dan tahunan.
const canExport = computed(() => activeGroup.value === "monthly" || activeGroup.value === "yearly");

const exportDocument = (type) => {
  exportOpen.value = false;
  if (!canExport.value) return;
  const params = activeGroup.value === "yearly"
    ? `mode=yearly&year=${activeYear.value}`
    : `mode=monthly&month=${activeMonth.value}&year=${activeYear.value}`;
  window.open(`${apiClient.defaults.baseURL}/orders/export/finance-${type === "pdf" ? "pdf" : "excel"}/?${params}`, "_blank");
};

// CSV dari data yang sedang tampil: berlaku untuk semua periode (Lifetime & Mingguan juga).
const csvCell = (v) => {
  let s = String(v ?? "");
  if (/^[=+\-@\t\r]/.test(s)) s = "'" + s;           // cegah formula injection saat dibuka di Excel
  return /[",;\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
};
const exportCsv = () => {
  exportOpen.value = false;
  const r = report.value;
  if (!r) return;
  const rows = [
    ["Order Reports Masashimura", periodLabel.value, r.period.start || "", r.period.end || ""],
    [],
    ["RINGKASAN"],
    ["Total omzet", Math.round(r.stats.total_omzet)],
    ["Total transaksi", r.stats.total_transaksi],
    ["Rata-rata transaksi", Math.round(r.stats.rata_rata_transaksi)],
    ["Porsi terjual", r.stats.porsi_terjual],
    [],
    ["TREN", "Omzet", "Transaksi"],
    ...r.trend.labels.map((l, i) => [l, Math.round(r.trend.omzet[i]), r.trend.transaksi[i]]),
    [],
    ["MENU TERLARIS", "Porsi", "Omzet"],
    ...r.top_menu.map((m) => [m.name, m.qty, Math.round(m.omzet)]),
    [],
    ["KATEGORI", "Porsi", "Omzet", "Persen"],
    ...r.kategori.map((k) => [k.name, k.qty, Math.round(k.omzet), k.share]),
    [],
    ["METODE PEMBAYARAN", "Transaksi", "Omzet", "Persen"],
    ...r.metode_pembayaran.map((p) => [p.label, p.count, Math.round(p.total), p.percent]),
    [],
    ["JAM", "Transaksi"],
    ...r.jam_distribusi.map((j) => [j.range, j.count]),
  ];
  const csv = "\ufeff" + rows.map((row) => row.map(csvCell).join(",")).join("\r\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = `order-report-${r.period.start || "lifetime"}${r.period.end ? "_" + r.period.end : ""}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
};

onMounted(fetchReport);
</script>

<style src="@/assets/report-dashboard.css"></style>
<style scoped>
.rep-select { width: auto; min-height: 40px; padding-block: 0.4rem; font-weight: 600; }
.rep-period { margin: 0; }
.rep-menu {
  position: absolute; right: 0; z-index: 40; width: 15rem; margin-top: 0.5rem; overflow: hidden;
  background: var(--surface); border: 1px solid var(--border-strong); border-radius: var(--r-md); box-shadow: var(--shadow-lg);
}
.rep-menu-item {
  display: flex; align-items: center; gap: 0.6rem; width: 100%; padding: 0.7rem 1rem;
  border: 0; background: transparent; color: var(--text-2); cursor: pointer;
  font-family: var(--font-body); font-size: 0.8125rem; font-weight: 600; text-align: left;
}
.rep-menu-item:hover:not(:disabled) { background: var(--surface-hover); color: var(--text); }
.rep-menu-item:disabled { opacity: 0.45; cursor: not-allowed; }
.custom-scroll::-webkit-scrollbar { width: 3px; }
.custom-scroll::-webkit-scrollbar-track { background: transparent; }
.custom-scroll::-webkit-scrollbar-thumb { background: rgb(var(--ink) / 0.1); border-radius: 99px; }
</style>
