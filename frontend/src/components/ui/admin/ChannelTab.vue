<!--
  ChannelTab.vue — Channel pesanan (tab di Order Reports): web pelanggan vs POS kasir.
-->
<template>
  <div class="rt">
    <div v-if="loading && !data" class="rt-skel tall" aria-busy="true"></div>

    <div v-else-if="error && !data" class="rt-empty">
      <p class="rt-empty-title">Gagal memuat Channel</p>
      <p class="rt-empty-sub">Periksa koneksi atau coba lagi beberapa saat.</p>
      <button type="button" class="rt-btn" @click="load">Muat ulang</button>
    </div>

    <template v-else-if="data">
      <div v-if="!data.enough_data" class="rt-banner" role="status">
        <strong>Data belum cukup.</strong> Baru {{ data.total_orders }} order lunas di periode ini, perbandingan channel masih kasar.
      </div>

      <div v-if="!data.channels.length" class="rt-card rt-empty">
        <p class="rt-empty-sub">Belum ada order lunas di periode ini.</p>
      </div>

      <template v-else>
        <div class="rt-kpis">
          <div v-for="c in data.channels" :key="c.source" class="rt-card">
            <p class="rt-kpi-label ch-name"><span class="ch-dot" :style="{ background: color(c.source) }" aria-hidden="true"></span>{{ c.label }}</p>
            <p class="rt-kpi-value">{{ rp(c.revenue) }}</p>
            <p class="rt-kpi-sub">{{ c.revenue_share }}% omzet · {{ c.orders.toLocaleString('id-ID') }} order ({{ c.order_share }}%)</p>
            <p class="rt-kpi-sub">Rata-rata order {{ rp(c.avg_order) }} · {{ c.items_per_order }} porsi / order</p>
          </div>
        </div>

        <section class="rt-card">
          <h3 class="rt-title">Omzet per channel · per {{ data.trend.unit === 'month' ? 'bulan' : 'hari' }}</h3>
          <div class="ch-chart"><Bar :data="chartData" :options="chartOpts" /></div>
        </section>

        <section class="rt-card">
          <h3 class="rt-title">Metode pembayaran per channel</h3>
          <div class="ch-pay">
            <div v-for="c in data.channels" :key="c.source">
              <p class="ch-pay-head"><span class="ch-dot" :style="{ background: color(c.source) }" aria-hidden="true"></span>{{ c.label }}</p>
              <ul class="ch-pay-list">
                <li v-for="m in c.payment_methods" :key="m.method">
                  <span class="ch-pay-name">{{ m.label }}</span>
                  <span class="rt-bar" aria-hidden="true"><span :style="{ width: m.share + '%' }"></span></span>
                  <span class="ch-pay-n">{{ m.share }}% · {{ m.count }}</span>
                </li>
              </ul>
            </div>
          </div>
          <p class="rt-lead ch-note">
            Harga di web sudah termasuk tambahan 1% (dibulatkan ke atas kelipatan Rp500), jadi rata-rata order
            web dan POS tidak persis sebanding.
          </p>
        </section>
      </template>
    </template>
  </div>
</template>

<script setup>
import { computed } from "vue"
import { Bar } from "vue-chartjs"
import { Chart as ChartJS, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from "chart.js"
import { analyticsAPI } from "@/api/analytics"
import { useReportLoad } from "@/composables/useReportLoad"
import { useTheme } from "@/composables/useTheme"

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend)

const props = defineProps({ params: { type: Object, required: true } })
const { data, loading, error, load } = useReportLoad(analyticsAPI.getChannels, () => props.params)
defineExpose({ reload: load, loading })

const COLORS = { web: "#3b82f6", pos: "#FFD400" }
const color = (s) => COLORS[s] || "#71717a"
const rp = (v) => "Rp " + Math.round(v || 0).toLocaleString("id-ID")

const LABELS = { web: "Web (pelanggan)", pos: "POS (kasir)" }
const chartData = computed(() => ({
  labels: data.value?.trend.labels || [],
  datasets: Object.entries(data.value?.trend.series || {}).map(([s, values]) => ({
    label: LABELS[s] || s,
    data: values,
    backgroundColor: color(s),
    borderRadius: 4,
    maxBarThickness: 32,
  })),
}))

// Canvas tidak bisa membaca CSS variable, jadi warna mengikuti tema lewat isDark.
const { isDark } = useTheme()
const chartOpts = computed(() => {
  const tick = isDark.value ? "rgba(255,255,255,0.5)" : "#63636b"
  const grid = isDark.value ? "rgba(255,255,255,0.05)" : "rgba(24,24,27,0.07)"
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: "bottom", labels: { color: tick, boxWidth: 12, font: { size: 11 } } },
      tooltip: { callbacks: { label: (c) => `${c.dataset.label}: ${rp(c.parsed.y)}` } },
    },
    scales: {
      x: { stacked: true, grid: { display: false }, ticks: { color: tick, font: { size: 11 }, maxRotation: 0, autoSkip: true } },
      y: { stacked: true, grid: { color: grid }, ticks: { color: tick, font: { size: 11 } }, border: { display: false } },
    },
  }
})
</script>

<style src="@/assets/report-tabs.css"></style>
<style scoped>
.ch-name { display: flex; align-items: center; gap: 0.5rem; margin: 0 0 0.5rem; }
.ch-dot { width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0; display: inline-block; }
.ch-chart { height: 280px; }
.ch-pay { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.5rem; }
.ch-pay-head { display: flex; align-items: center; gap: 0.5rem; margin: 0 0 0.6rem; font-size: 0.8rem; color: var(--text); font-weight: 500; }
.ch-pay-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 0.5rem; }
.ch-pay-list li { display: grid; grid-template-columns: 96px 1fr 76px; align-items: center; gap: 0.6rem; font-size: 0.76rem; }
.ch-pay-name { color: var(--text-dim); }
.ch-pay-n { text-align: right; color: var(--text-faint); font-variant-numeric: tabular-nums; }
.ch-note { margin-top: 1rem; font-size: 0.72rem; }
</style>
