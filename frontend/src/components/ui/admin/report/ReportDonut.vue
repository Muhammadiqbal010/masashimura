<!--
  ReportDonut.vue — donat SVG ringan dengan total di tengah dan legenda bernilai (tanpa Chart.js).
  segments: [{ label, value, color, text? }]  — `text` = nilai yang tampil di legenda (mis. "Rp 1,2 jt · 47%").
-->
<template>
  <div class="rd-donut">
    <div class="rd-donut-ring" role="img" :aria-label="ariaLabel">
      <svg viewBox="0 0 42 42" aria-hidden="true">
        <circle class="rd-donut-track" cx="21" cy="21" r="15.915" fill="none" stroke-width="5.2" />
        <circle v-for="a in arcs" :key="a.label" cx="21" cy="21" r="15.915" fill="none" stroke-width="5.2"
                :stroke="a.color" :stroke-dasharray="`${a.len} ${100 - a.len}`" :stroke-dashoffset="a.offset"
                transform="rotate(-90 21 21)" />
      </svg>
      <div class="rd-donut-center">
        <strong>{{ centerValue }}</strong>
        <span>{{ centerLabel }}</span>
      </div>
    </div>

    <ul class="rd-legend">
      <li v-for="s in segments" :key="s.label">
        <span class="rd-dot" :style="{ background: s.color }"></span>
        <span class="rd-legend-name">{{ s.label }}</span>
        <span class="rd-legend-val">{{ s.text ?? s.value }}</span>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { computed } from "vue"

const props = defineProps({
  segments: { type: Array, required: true },
  centerValue: { type: String, default: "" },
  centerLabel: { type: String, default: "" },
})

const total = computed(() => props.segments.reduce((a, s) => a + (Number(s.value) || 0), 0))
const GAP = 0.8
const arcs = computed(() => {
  let acc = 0
  return props.segments
    .filter((s) => Number(s.value) > 0)
    .map((s) => {
      const pct = (Number(s.value) / total.value) * 100
      const a = { label: s.label, color: s.color, len: Math.max(0, pct - (props.segments.length > 1 ? GAP : 0)), offset: -acc }
      acc += pct
      return a
    })
})
const ariaLabel = computed(() => props.segments.map((s) => `${s.label} ${s.text ?? s.value}`).join(", "))
</script>
