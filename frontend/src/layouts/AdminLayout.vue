<template>
  <div class="min-h-screen min-h-[100dvh] bg-[color:var(--bg)] text-[color:var(--text)] font-inter antialiased flex">

    <!-- Overlay mobile -->
    <Transition name="fade">
      <div
        v-if="sidebarOpen"
        class="fixed inset-0 z-30 bg-[color:var(--overlay)] backdrop-blur-[2px] lg:hidden"
        @click="sidebarOpen = false"
      />
    </Transition>

    <!-- Sidebar -->
    <AdminSidebar
      :open="sidebarOpen"
      @close="sidebarOpen = false"
    />

    <!-- Area konten -->
    <div class="flex-1 min-h-screen min-h-[100dvh] flex flex-col min-w-0">

      <!-- Topbar — mobile only -->
      <header
        class="lg:hidden sticky top-0 z-20 flex items-center gap-3 px-4 pb-3 pt-[calc(0.75rem+env(safe-area-inset-top,0px))] bg-[color:color-mix(in_srgb,var(--bg-sidebar)_95%,transparent)] backdrop-blur-xl border-b border-[color:var(--border)]"
      >
        <button
          type="button"
          @click="sidebarOpen = true"
          class="w-10 h-10 flex flex-col items-center justify-center gap-[4px] rounded-lg hover:bg-[color:var(--surface-hover)] transition-colors shrink-0"
          aria-label="Buka navigasi"
          :aria-expanded="sidebarOpen"
        >
          <span class="block w-[18px] h-px bg-[color:var(--text-dim)] rounded-full" />
          <span class="block w-[13px] h-px bg-[color:var(--text-faint)] rounded-full self-start ml-[11px]" />
          <span class="block w-[18px] h-px bg-[color:var(--text-dim)] rounded-full" />
        </button>

        <div class="flex items-center gap-2 min-w-0">
          <!-- Logo dirancang untuk latar gelap → di tema terang ditaruh di tile gelap -->
          <span class="inline-flex rounded-lg px-2 py-1 bg-[color:var(--brand-tile)]">
            <img
              src="@/assets/masashimura-logo.png"
              alt="Masashimura"
              class="h-6 w-auto object-contain select-none pointer-events-none opacity-90"
            />
          </span>
          <span class="font-mono text-[10px] uppercase tracking-[0.2em] text-[color:var(--text-faint)]">Admin</span>
        </div>

        <!-- Switch tema cepat di HP (opsional, switch utama tetap di sidebar) -->
        <ThemeToggle variant="icon" class="ml-auto" />
      </header>

      <!-- Konten halaman -->
      <main class="flex-grow px-4 sm:px-6 lg:px-8 py-6 lg:py-10 w-full max-w-screen-2xl mx-auto">
        <router-view />
      </main>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import AdminSidebar from '@/components/ui/layouts/AdminSidebar.vue'
import ThemeToggle from '@/components/ui/admin/ThemeToggle.vue'
import { useOrderNotificationsStore } from '@/stores/orderNotifications'
import { unlockNotificationAudio } from '@/utils/notificationSound'
import { useTheme } from '@/composables/useTheme'

const sidebarOpen = ref(false)

// Pasang atribut tema di level layout, jadi sudah aktif sebelum render pertama
// (releaseTheme tetap dipanggil AdminSidebar saat keluar dari area admin).
useTheme()

// ── Notifikasi order baru: polling + suara ────────────────────────────────
// Dipasang di root layout admin supaya aktif begitu admin login,
// di halaman manapun dia berada.
const orderNotifications = useOrderNotificationsStore()

onMounted(() => {
  orderNotifications.startPolling()
  // Browser nge-block AudioContext sebelum ada interaksi user pertama kali,
  // jadi listener ini cuma buat "buka kunci" audio, lalu ke-remove sendiri.
  window.addEventListener('click', unlockNotificationAudio, { once: true })
})

onUnmounted(() => {
  orderNotifications.stopPolling()
  window.removeEventListener('click', unlockNotificationAudio)
})
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from,   .fade-leave-to     { opacity: 0; }
</style>