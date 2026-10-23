<!--
  CrowdBadge.vue — badge keramaian untuk pelanggan (halaman Menu).
  Hanya level (Santai / Sedang / Ramai), tanpa jam atau angka.
  Tampil otomatis hanya bila saklar menyala dan toko buka; kalau tidak, tidak merender apa pun.
-->
<template>
  <span
    v-if="visible"
    class="crowd-badge"
    :class="`is-${level}`"
    role="status"
    :aria-label="`Keramaian saat ini: ${label}`"
  >
    <span class="crowd-dot" aria-hidden="true"></span>
    <span class="crowd-text">Keramaian: <strong>{{ label }}</strong></span>
  </span>
</template>

<script setup>
import { useCrowd } from "@/composables/useCrowd"

const { visible, level, label } = useCrowd()
</script>

<style scoped>
/* Palet Menu: Crimson #D92B22 · Washi #111113 · Champagne #F4C542. Teks selalu ada, warna hanya penegas. */
.crowd-badge {
  --tone: #2FB36D;
  --tone-text: #17703F;
  display: inline-flex; align-items: center; gap: 0.5rem;
  padding: 0.4rem 0.9rem 0.4rem 0.75rem;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--tone) 40%, transparent);
  background: color-mix(in srgb, var(--tone) 10%, transparent);
  color: #111113; font-size: 0.8125rem; line-height: 1.2;
}
.crowd-badge strong { font-weight: 700; color: var(--tone-text); }
.crowd-badge.is-santai { --tone: #2FB36D; --tone-text: #17703F; }
.crowd-badge.is-sedang { --tone: #F4C542; --tone-text: #8A6200; }
.crowd-badge.is-ramai  { --tone: #D92B22; --tone-text: #B8201A; }
.crowd-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--tone); flex-shrink: 0; }
.crowd-badge.is-ramai .crowd-dot { animation: crowd-pulse 1.8s ease-in-out infinite; }
@keyframes crowd-pulse {
  0%, 100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--tone) 55%, transparent); }
  50%      { box-shadow: 0 0 0 5px transparent; }
}
@media (prefers-reduced-motion: reduce) {
  .crowd-badge.is-ramai .crowd-dot { animation: none; }
}
</style>
