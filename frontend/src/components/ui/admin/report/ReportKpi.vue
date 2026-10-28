<!--
  ReportKpi.vue — kartu KPI Order Reports: nilai besar, pill perubahan vs periode sebelumnya, dan sparkline.
  `hero` = kartu utama berlatar aksen (dipakai untuk Total Omzet).
  Angka tidak dipotong (tanpa truncate): ukuran huruf mengecil sesuai lebar kartu.
-->
<template>
  <article class="rd-kpi" :class="{ 'rd-kpi--hero': hero }">
    <header class="rd-kpi-top">
      <span class="rd-kpi-icon" aria-hidden="true"><component :is="icon" :size="16" /></span>
      <span v-if="hasDelta" class="rd-delta" :class="`is-${tone}`" :title="deltaTitle">
        <component :is="tone === 'down' ? TrendingDown : tone === 'up' ? TrendingUp : Minus" :size="12" />
        {{ deltaText }}
      </span>
    </header>

    <p class="rd-kpi-label">{{ label }}</p>
    <p class="rd-kpi-value" :title="value">{{ value }}</p>
    <p v-if="sub" class="rd-kpi-sub">{{ sub }}</p>

    <svg v-if="path" class="rd-spark" viewBox="0 0 100 32" preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <linearGradient :id="gid" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="currentColor" stop-opacity="0.35" />
          <stop offset="100%" stop-color="currentColor" stop-opacity="0" />
        </linearGradient>
      </defs>
      <path :d="`${path} L100,32 L0,32 Z`" :fill="`url(#${gid})`" />
      <path :d="path" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"
            stroke-linecap="round" vector-effect="non-scaling-stroke" />
    </svg>
  </article>
</template>

<script setup>
import { computed } from "vue"
import { TrendingUp, TrendingDown, Minus } from "lucide-vue-next"

const gid = `rd-spark-${Math.random().toString(36).slice(2, 9)}`

const props = defineProps({
  label: { type: String, required: true },
  value: { type: String, required: true },
  icon: { type: [Object, Function], required: true },
  delta: { type: Number, default: null },        // persen; null = tidak ada pembanding
  deltaLabel: { type: String, default: "" },     // mis. "minggu sebelumnya"
  spark: { type: Array, default: () => [] },
  sub: { type: String, default: "" },
  hero: { type: Boolean, default: false },
})

const hasDelta = computed(() => props.delta !== null && props.delta !== undefined)
const tone = computed(() => (props.delta > 0.05 ? "up" : props.delta < -0.05 ? "down" : "flat"))
const deltaText = computed(() => {
  const n = Math.abs(props.delta).toLocaleString("id-ID", { maximumFractionDigits: 1 })
  return `${props.delta > 0.05 ? "+" : props.delta < -0.05 ? "−" : ""}${n}%`
})
const deltaTitle = computed(() => (props.deltaLabel ? `Dibanding ${props.deltaLabel}` : ""))

const path = computed(() => {
  const s = props.spark.map((n) => Number(n) || 0)
  if (s.length < 2 || !s.some((n) => n > 0)) return ""
  const max = Math.max(...s), min = Math.min(...s), span = max - min || 1
  return s
    .map((v, i) => `${i ? "L" : "M"}${((i / (s.length - 1)) * 100).toFixed(2)},${(28 - ((v - min) / span) * 24).toFixed(2)}`)
    .join(" ")
})
</script>
