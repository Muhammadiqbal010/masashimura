<!--
  StoreBanner.vue
  Taruh di src/components/ui/StoreBanner.vue

  Dipakai di Checkout.vue:
    import StoreBanner from "@/components/ui/StoreBanner.vue"
    <StoreBanner />
-->
<template>
  <transition
    enter-active-class="transition-all duration-300 ease-out"
    enter-from-class="opacity-0 -translate-y-2"
    enter-to-class="opacity-100 translate-y-0"
  >
    <div v-if="settingsReady && !isStoreOpen" class="store-banner" role="status">
      <div class="banner-icon">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <rect x="3" y="11" width="18" height="11" rx="2"/>
          <path d="M7 11V7a5 5 0 0110 0v4"/>
        </svg>
      </div>
      <div class="banner-content">
        <p class="banner-title">Toko sedang tutup</p>
        <p class="banner-msg">{{ closedMessage }}</p>
        <p v-if="nextOpenText" class="banner-next">{{ nextOpenText }}</p>
      </div>
      <div v-if="todaySchedule" class="banner-hours">
        <span class="hours-label">Jam buka hari ini</span>
        <span class="hours-value">{{ todaySchedule.open }} – {{ todaySchedule.close }}</span>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { computed, onMounted } from "vue"
import { useStoreSettings } from "@/composables/useStoreSettings"

const { isStoreOpen, closedMessage, nextOpenText, settingsReady, settings, fetchSettings } = useStoreSettings()

onMounted(() => fetchSettings())

// Hari ini (WIB) — 0=Senin ... 6=Minggu
const todayKey = computed(() => {
  const d = new Date()
  const wib = new Date(d.getTime() + 7 * 60 * 60 * 1000)
  const day = wib.getUTCDay()   // 0=Minggu ... 6=Sabtu
  return String(day === 0 ? 6 : day - 1)
})

const todaySchedule = computed(() => {
  const s = settings.value.operating_hours?.[todayKey.value]
  return s?.open && s?.close ? s : null
})
</script>

<style scoped>
/* Palet: Crimson #D92B22 · Washi #FAFAFA · Champagne #F4C542 */
.store-banner {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  background:
    radial-gradient(80% 120% at 0% 0%, rgba(217,43,34, 0.14), transparent 70%),
    rgba(217,43,34, 0.05);
  border: 1px solid rgba(217,43,34, 0.25);
  border-radius: 20px;
  padding: 18px 20px;
  margin-bottom: 24px;
}

.banner-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: rgba(217,43,34, 0.14);
  border: 1px solid rgba(217,43,34, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #F0605A;
  flex-shrink: 0;
}

.banner-content { flex: 1; min-width: 0; }

.banner-title {
  font-family: "Manrope", ui-sans-serif, system-ui, sans-serif;
  font-size: 16px;
  font-weight: 600;
  color: #FAFAFA;
  line-height: 1.3;
}

.banner-msg {
  font-size: 14px;
  color: #B8B8C0;
  margin-top: 4px;
  line-height: 1.55;
}

.banner-next {
  font-size: 14px;
  font-weight: 600;
  color: #F4C542;
  margin-top: 6px;
  line-height: 1.4;
}

.banner-hours {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  flex-shrink: 0;
  padding-left: 16px;
  border-left: 1px solid rgba(255, 255, 255, 0.08);
}

.hours-label {
  font-size: 12px;
  color: #9A9AA3;
}

.hours-value {
  font-size: 14px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: #FAFAFA;
}

@media (max-width: 520px) {
  .store-banner { flex-wrap: wrap; padding: 16px; }
  .banner-hours {
    width: 100%;
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    padding: 12px 0 0;
    border-left: none;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
  }
}
</style>