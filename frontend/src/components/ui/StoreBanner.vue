<!--
  StoreBanner.vue
  Taruh di src/components/ui/StoreBanner.vue

  Pakai di MenuView.vue dan CheckoutView.vue:
    import StoreBanner from "@/components/ui/StoreBanner.vue"
    <StoreBanner />
-->
<template>
  <transition
    enter-active-class="transition-all duration-300 ease-out"
    enter-from-class="opacity-0 -translate-y-2"
    enter-to-class="opacity-100 translate-y-0"
  >
    <div v-if="!isStoreOpen" class="store-banner">
      <div class="banner-icon">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="11" width="18" height="11" rx="2"/>
          <path d="M7 11V7a5 5 0 0110 0v4"/>
        </svg>
      </div>
      <div class="banner-content">
        <p class="banner-title">Toko Sedang Tutup</p>
        <p class="banner-msg">{{ closedMessage }}</p>
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

const { isStoreOpen, closedMessage, settings, fetchSettings } = useStoreSettings()

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
.store-banner {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  background: rgba(239, 68, 68, 0.06);
  border: 1px solid rgba(239, 68, 68, 0.18);
  border-radius: 14px;
  padding: 16px 18px;
  margin-bottom: 20px;
}

.banner-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #f87171;
  flex-shrink: 0;
}

.banner-content { flex: 1; }

.banner-title {
  font-size: 13px;
  font-weight: 700;
  color: #f87171;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  line-height: 1.2;
}

.banner-msg {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
  margin-top: 4px;
  line-height: 1.5;
}

.banner-hours {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  flex-shrink: 0;
}

.hours-label {
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: rgba(255, 255, 255, 0.2);
}

.hours-value {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 12.5px;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 600;
}

@media (max-width: 480px) {
  .store-banner { flex-wrap: wrap; }
  .banner-hours { align-items: flex-start; flex-direction: row; gap: 6px; align-items: center; }
}
</style>