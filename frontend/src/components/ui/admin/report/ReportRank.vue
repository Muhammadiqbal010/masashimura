<!--
  ReportRank.vue — daftar peringkat dengan bar proporsional (gaya "Pages" di referensi).
  items: [{ name, value (angka untuk lebar bar), valueText, meta? }]
-->
<template>
  <ol class="rd-rank">
    <li v-for="(it, i) in items" :key="it.name + i" class="rd-rank-row">
      <span class="rd-rank-no" :class="{ 'is-top': i < 3 }">{{ String(i + 1).padStart(2, "0") }}</span>
      <div class="rd-rank-body">
        <div class="rd-rank-line">
          <span class="rd-rank-name" :title="it.name">{{ it.name }}</span>
          <span class="rd-rank-val">{{ it.valueText }}</span>
        </div>
        <div class="rd-rank-track" aria-hidden="true">
          <span :style="{ width: width(it.value) + '%', background: color }"></span>
        </div>
        <p v-if="it.meta" class="rd-rank-meta">{{ it.meta }}</p>
      </div>
    </li>
  </ol>
</template>

<script setup>
import { computed } from "vue"

const props = defineProps({
  items: { type: Array, required: true },
  color: { type: String, default: "var(--accent)" },
})
const max = computed(() => Math.max(1, ...props.items.map((i) => Number(i.value) || 0)))
const width = (v) => Math.max(2, Math.round(((Number(v) || 0) / max.value) * 100))
</script>
