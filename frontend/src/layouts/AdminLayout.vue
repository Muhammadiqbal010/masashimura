<template>
  <div class="min-h-screen min-h-[100dvh] bg-[color:var(--bg)] text-[color:var(--text)] font-manrope antialiased flex">

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
        class="lg:hidden sticky top-0 z-20 flex items-center gap-3 px-4 pb-3 pt-[calc(0.75rem+env(safe-area-inset-top,0px))] bg-[color:color-mix(in_srgb,var(--bg-sidebar)_95%,transparent)] backdrop-blur-xl"
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
          <span class="text-[10px] font-bold uppercase tracking-[0.18em] text-[color:var(--text-faint)]">Admin</span>
        </div>

        <!-- Switch tema cepat di HP (opsional, switch utama tetap di sidebar) -->
        <div class="ml-auto flex items-center gap-1">
          <AdminQuickSearch variant="icon" />
          <ThemeToggle variant="icon" />
        </div>
      </header>

      <!-- Topbar — desktop: tanggal, notifikasi pesanan, tema, profil -->
      <header class="admin-topbar hidden lg:flex" aria-label="Kontrol global">
        <p class="admin-topbar-date">{{ todayLabel }}</p>
        <div class="admin-topbar-search"><AdminQuickSearch variant="field" /></div>
        <div class="admin-topbar-actions">
          <router-link
            to="/admin/orders"
            class="admin-topbar-btn"
            :aria-label="orderNotifications.unreadCount > 0 ? `${orderNotifications.unreadCount} pesanan baru` : 'Riwayat pesanan'"
            @click="orderNotifications.clearUnread()"
          >
            <Bell :size="18" aria-hidden="true" />
            <span v-if="orderNotifications.unreadCount > 0" class="admin-topbar-badge">
              {{ orderNotifications.unreadCount > 9 ? '9+' : orderNotifications.unreadCount }}
            </span>
          </router-link>
          <ThemeToggle variant="icon" />
          <router-link to="/admin/profile" class="admin-topbar-user">
            <span class="admin-topbar-avatar" aria-hidden="true">{{ initial }}</span>
            <span class="admin-topbar-name">{{ auth.user?.name || 'Admin' }}</span>
          </router-link>
        </div>
      </header>

      <!-- Konten halaman -->
      <main class="flex-grow px-4 sm:px-6 lg:px-8 pb-6 pt-6 lg:pt-2 lg:pb-10 w-full max-w-screen-2xl mx-auto">
        <router-view />
      </main>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Bell } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import AdminSidebar from '@/components/ui/layouts/AdminSidebar.vue'
import ThemeToggle from '@/components/ui/admin/ThemeToggle.vue'
import AdminQuickSearch from '@/components/ui/admin/AdminQuickSearch.vue'
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
const auth = useAuthStore()

const todayLabel = new Intl.DateTimeFormat('id-ID', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }).format(new Date())
const initial = computed(() => (auth.user?.name || 'A').trim().charAt(0).toUpperCase())

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
.admin-topbar {
  position: sticky; top: 0; z-index: 20;
  align-items: center; justify-content: space-between; gap: 1rem;
  padding: 0.85rem 2rem;
  background: color-mix(in srgb, var(--bg) 88%, transparent);
  backdrop-filter: blur(12px);
}
.admin-topbar-date { margin: 0; padding: 0.45rem 0.9rem; white-space: nowrap; border: 1.5px solid var(--border-strong); border-radius: 999px; background: var(--surface); font-size: 0.8125rem; font-weight: 700; color: var(--text-2); }
.admin-topbar-date::before { content: ''; display: inline-block; width: 7px; height: 7px; margin-right: 0.55rem; background: var(--accent); transform: rotate(45deg); }
.admin-topbar-search { flex: 1; min-width: 0; display: flex; justify-content: center; }
.admin-topbar-actions { display: flex; align-items: center; gap: 0.5rem; }
.admin-topbar-btn {
  position: relative; display: inline-flex; align-items: center; justify-content: center;
  width: 40px; height: 40px; border-radius: 12px;
  border: 1px solid var(--border); background: var(--surface); color: var(--text-2);
  transition: background 0.15s, color 0.15s;
}
.admin-topbar-btn:hover { background: var(--surface-hover); color: var(--text); }
.admin-topbar-badge {
  position: absolute; top: -5px; right: -5px; min-width: 18px; height: 18px; padding: 0 4px;
  display: inline-flex; align-items: center; justify-content: center;
  border-radius: 99px; background: var(--accent); color: var(--on-accent);
  font-size: 0.75rem; font-weight: 700; line-height: 1;
}
.admin-topbar-user {
  display: inline-flex; align-items: center; gap: 0.6rem; height: 40px; padding: 0 0.85rem 0 0.35rem;
  border-radius: 99px; border: 1px solid var(--border); background: var(--surface);
  color: var(--text); font-size: 0.875rem; font-weight: 600; text-decoration: none;
  transition: background 0.15s;
}
.admin-topbar-user:hover { background: var(--surface-hover); }
.admin-topbar-avatar {
  display: inline-flex; align-items: center; justify-content: center;
  width: 30px; height: 30px; border-radius: 50%;
  background: var(--accent); color: var(--on-accent); font-size: 0.8125rem; font-weight: 700;
}
.admin-topbar-name { max-width: 9rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from,   .fade-leave-to     { opacity: 0; }
</style>