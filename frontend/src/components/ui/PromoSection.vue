<!--
  PromoSection.vue  →  src/components/ui/PromoSection.vue   (menggantikan PromoBanner.vue)

  Dipakai di Home.vue:
    import PromoSection from "@/components/ui/PromoSection.vue"
    <PromoSection :promos="promos" />

  Props `promos` = array dari /homepage/promos/ (maks 5).
  Susunan otomatis mengikuti rasio gambar yang dipilih di admin:
    • gambar lebar (16:9, 21:9, 4:3) / tanpa gambar  -> 1 baris penuh, memanjang
    • gambar kotak / portrait (1:1, 4:5, 3:4, 9:16) berurutan -> berjajar 2-3 per baris
  Jadwal, hitung mundur, dan tombol tutup berjalan per promo.
-->
<template>
  <section
    v-if="rows.length"
    class="promo-section relative border-b border-white/[0.06]"
    aria-label="Promo dan event"
  >
    <div class="mx-auto max-w-7xl px-5 py-10 sm:px-8 sm:py-14 lg:px-10">
      <TransitionGroup name="promo" tag="div" appear class="promo-rows">
        <div
          v-for="row in rows"
          :key="row.key"
          class="promo-row"
          :style="{ '--cols': row.cols }"
        >
          <PromoCard
            v-for="item in row.items"
            :key="item.id"
            :promo="item"
            :now="now"
            :compact="row.cols > 1"
            @dismiss="dismiss"
          />
        </div>
      </TransitionGroup>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue"
import PromoCard from "@/components/ui/PromoCard.vue"
import { PROMO_MAX, hasContent, inSchedule, signature, buildRows } from "@/utils/promo"

const props = defineProps({
  promos: { type: Array, default: () => [] },
})

// Waktu diperbarui tiap 30 detik: jadwal tayang & hitung mundur otomatis
const now = ref(Date.now())
let timer = null
onMounted(() => { timer = setInterval(() => { now.value = Date.now() }, 30000) })
onUnmounted(() => { if (timer) clearInterval(timer) })

// Tombol tutup: diingat per isi promo (muncul lagi kalau isinya diganti)
const STORAGE_KEY = "masashimura:promos-dismissed"
const dismissed = ref([])
try {
  const raw = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]")
  if (Array.isArray(raw)) dismissed.value = raw
} catch { /* storage diblokir / isinya rusak: abaikan */ }

const dismiss = (promo) => {
  const sig = signature(promo)
  if (!dismissed.value.includes(sig)) dismissed.value = [...dismissed.value, sig]
  try {
    // Simpan hanya tanda tangan promo yang masih ada, supaya tidak menumpuk
    const alive = new Set((props.promos || []).map(signature))
    const keep = dismissed.value.filter((s) => alive.has(s))
    localStorage.setItem(STORAGE_KEY, JSON.stringify(keep))
  } catch { /* abaikan */ }
}

const visible = computed(() =>
  (props.promos || [])
    .filter((p) => hasContent(p) && inSchedule(p, now.value))
    .filter((p) => !(p.dismissible && dismissed.value.includes(signature(p))))
    .slice(0, PROMO_MAX),
)
const rows = computed(() => buildRows(visible.value))
</script>

<style scoped>
/* Latar sama dengan halaman (#111111), ditambah sorot halus supaya promo terasa menonjol */
.promo-section {
  background:
    radial-gradient(50% 80% at 50% 0%, rgba(215,25,32, 0.07), transparent 70%),
    #111111;
}

.promo-rows { display: flex; flex-direction: column; gap: 1.25rem; }
@media (min-width: 640px) {
  .promo-rows { gap: 1.5rem; }
}

.promo-row {
  display: grid;
  grid-template-columns: repeat(var(--cols, 1), minmax(0, 1fr));
  gap: 1.25rem;
  align-items: start;
}
@media (min-width: 640px) {
  .promo-row { gap: 1.5rem; }
}
@media (max-width: 767px) {
  .promo-row { grid-template-columns: minmax(0, 1fr); }
}

.promo-enter-active,
.promo-leave-active { transition: opacity 0.5s ease, transform 0.5s cubic-bezier(0.16, 1, 0.3, 1); }
.promo-enter-from,
.promo-leave-to { opacity: 0; transform: translateY(14px); }

@media (prefers-reduced-motion: reduce) {
  .promo-enter-active, .promo-leave-active { transition: none; }
}
</style>