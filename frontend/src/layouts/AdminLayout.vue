<template>
  <div class="min-h-screen bg-[#050505] text-white font-inter antialiased flex">

    <!-- Overlay mobile -->
    <Transition name="fade">
      <div
        v-if="sidebarOpen"
        class="fixed inset-0 z-30 bg-black/50 backdrop-blur-[2px] lg:hidden"
        @click="sidebarOpen = false"
      />
    </Transition>

    <!-- Sidebar -->
    <AdminSidebar
      :open="sidebarOpen"
      @close="sidebarOpen = false"
    />

    <!-- Area konten -->
    <div class="flex-1 min-h-screen flex flex-col min-w-0">

      <!-- Topbar — mobile only -->
      <header class="lg:hidden sticky top-0 z-20 flex items-center gap-3 px-4 py-3.5 bg-[#0a0a0a]/95 backdrop-blur-xl border-b border-white/[0.05]">
        <button
          @click="sidebarOpen = true"
          class="w-8 h-8 flex flex-col items-center justify-center gap-[4px] rounded-lg hover:bg-white/[0.06] transition-colors shrink-0"
          aria-label="Buka navigasi"
        >
          <span class="block w-[18px] h-px bg-white/50 rounded-full" />
          <span class="block w-[13px] h-px bg-white/30 rounded-full self-start ml-[2px]" />
          <span class="block w-[18px] h-px bg-white/50 rounded-full" />
        </button>
        <div class="flex items-center gap-2">
          <img
            src="@/assets/masashimura-logo.png"
            alt="Masashimura"
            class="h-7 w-auto object-contain select-none pointer-events-none opacity-90"
          />
          <span class="font-mono text-[8px] uppercase tracking-[0.2em] text-white/20">Admin</span>
        </div>
      </header>

      <!-- Konten halaman -->
      <main class="flex-grow px-4 sm:px-6 lg:px-8 py-6 lg:py-10 w-full max-w-screen-2xl">
        <router-view />
      </main>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import AdminSidebar from '@/components/ui/layouts/AdminSidebar.vue'
import { useOrderNotificationsStore } from '@/stores/orderNotifications'
import { unlockNotificationAudio } from '@/utils/notificationSound'

const sidebarOpen = ref(false)

// ── Notifikasi order baru: polling + suara ────────────────────────────────
// Sebelumnya store & util ini ada tapi ngga pernah dipanggil di manapun,
// jadi polling ngga pernah jalan dan audio context ngga pernah ke-unlock.
// Dipasang di sini (root layout admin) biar aktif begitu admin login,
// di halaman manapun dia berada.
const orderNotifications = useOrderNotificationsStore()

onMounted(() => {
  orderNotifications.startPolling()
  // Browser nge-block AudioContext sebelum ada interaksi user pertama kali
  // (klik/tap) di halaman — jadi listener ini cuma buat "buka kunci" audio,
  // sekali kepakai langsung ke-remove sendiri.
  window.addEventListener('click', unlockNotificationAudio, { once: true })
})

onUnmounted(() => {
  orderNotifications.stopPolling()
})
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from,   .fade-leave-to     { opacity: 0; }
</style>