<template>
  <aside
    :class="[
      'fixed lg:sticky top-0 h-screen w-64 bg-[#0a0a0a] border-r border-white/[0.06] flex flex-col shrink-0 text-white select-none font-inter z-40',
      'transition-transform duration-300 ease-in-out lg:translate-x-0',
      open ? 'translate-x-0 shadow-2xl' : '-translate-x-full',
    ]"
  >
    <!-- Header Brand -->
    <div class="relative flex items-start justify-between px-7 pt-7 pb-5 border-b border-white/[0.04]">
      <div>
        <img
          src="@/assets/masashimura-logo.png"
          alt="Masashimura"
          class="h-8 w-auto object-contain select-none pointer-events-none opacity-90"
        />
        <p class="text-[9px] text-white/25 tracking-[0.25em] uppercase mt-2 font-mono">
          Admin System
        </p>
      </div>
      <!-- Tombol close — mobile only -->
      <button
        @click="emit('close')"
        class="lg:hidden w-7 h-7 rounded-lg flex items-center justify-center text-white/20 hover:text-white/60 hover:bg-white/5 transition-all mt-0.5"
        aria-label="Tutup navigasi"
      >
        <X size="14" />
      </button>
    </div>

    <!-- Profil Mini Pengguna -->
    <div class="px-5 py-4 border-b border-white/[0.04]">
      <div class="flex items-center gap-3 px-3 py-3 rounded-xl bg-white/[0.03] border border-white/[0.05]">
        <div class="w-8 h-8 rounded-full bg-white/[0.06] border border-white/10 flex items-center justify-center shrink-0">
          <Crown v-if="userRole === 'owner'" size="14" class="text-amber-400/80" />
          <User  v-else-if="userRole === 'admin'" size="14" class="text-blue-400/80" />
          <BriefcaseBusiness v-else size="14" class="text-emerald-400/80" />
        </div>
        <div class="min-w-0 flex-1">
          <p class="text-[12px] font-semibold text-white/80 truncate leading-none mb-1">
            {{ user?.name || "Guest" }}
          </p>
          <span
            class="inline-block text-[8px] uppercase font-bold tracking-[0.15em] font-mono px-1.5 py-0.5 rounded-md"
            :class="
              userRole === 'owner' ? 'bg-amber-500/10 text-amber-500/80' :
              userRole === 'admin' ? 'bg-blue-500/10 text-blue-400/80' :
                                    'bg-emerald-500/10 text-emerald-400/80'
            "
          >
            {{ userRole || "Kasir" }}
          </span>
        </div>
      </div>
    </div>

    <!-- Navigasi -->
    <nav class="flex-1 px-3 py-3 space-y-0.5 overflow-y-auto scrollbar-none">

      <!-- DASHBOARD -->
      <div v-if="['owner', 'admin'].includes(userRole)" class="mb-1">
        <router-link
          to="/admin/"
          @click="emit('close')"
          class="group flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200"
          :class="isActive('/admin/') ? 'bg-white/[0.07] text-white' : 'text-white/35 hover:text-white/80 hover:bg-white/[0.04]'"
        >
          <LayoutDashboard size="15" :class="isActive('/admin/') ? 'text-white/70' : 'text-white/25 group-hover:text-white/50'" />
          <span class="text-[13px] font-medium font-inter tracking-normal">Dashboard</span>
        </router-link>
      </div>

      <!-- Divider label -->
      <div class="pt-2 pb-1 px-3">
        <span class="font-mono text-[8px] tracking-[0.25em] uppercase text-white/15">Navigasi</span>
      </div>

      <!-- KELOMPOK 1: OPERASIONAL TOKO -->
      <div class="space-y-0.5">
        <button
          type="button"
          @click="toggleGroup('operational')"
          class="group w-full flex items-center justify-between px-3 py-2.5 rounded-xl hover:bg-white/[0.03] transition-colors"
        >
          <span class="flex items-center gap-2.5">
            <Zap size="14" class="text-amber-500/50" />
            <span class="text-[12px] font-semibold text-white/50 group-hover:text-white/70 tracking-wide font-inter transition-colors">Operasional</span>
          </span>
          <ChevronDown
            size="13"
            class="text-white/20 transition-transform duration-300 group-hover:text-white/40"
            :class="openGroups.operational ? 'rotate-180' : ''"
          />
        </button>
        <div
          class="overflow-hidden transition-all duration-300 ease-in-out pl-1"
          :class="openGroups.operational ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'"
        >
          <template v-for="link in operationalLinks" :key="link.to">
            <router-link
              v-if="link.roles.includes(userRole)"
              :to="link.to"
              @click="handleNavClick(link.to)"
              class="group flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200"
              :class="isActive(link.to) ? 'bg-white/[0.07] text-white' : 'text-white/35 hover:text-white/80 hover:bg-white/[0.04]'"
            >
              <component :is="link.icon" size="14" :class="isActive(link.to) ? 'text-white/70' : 'text-white/20 group-hover:text-white/50'" />
              <span class="text-[13px] font-medium font-inter tracking-normal flex-1">{{ link.label }}</span>
              <span
                v-if="link.to === '/admin/orders' && notifStore.unreadCount > 0"
                class="min-w-[18px] h-[18px] px-1 flex items-center justify-center rounded-full bg-red-600 text-white text-[10px] font-bold font-mono"
              >
                {{ notifStore.unreadCount > 9 ? '9+' : notifStore.unreadCount }}
              </span>
            </router-link>
          </template>
        </div>
      </div>

      <!-- KELOMPOK 2: DATA & CMS -->
      <div v-if="['owner', 'admin'].includes(userRole)" class="space-y-0.5">
        <button
          type="button"
          @click="toggleGroup('dataManagement')"
          class="group w-full flex items-center justify-between px-3 py-2.5 rounded-xl hover:bg-white/[0.03] transition-colors"
        >
          <span class="flex items-center gap-2.5">
            <FolderOpen size="14" class="text-sky-500/50" />
            <span class="text-[12px] font-semibold text-white/50 group-hover:text-white/70 tracking-wide font-inter transition-colors">Data &amp; CMS</span>
          </span>
          <ChevronDown
            size="13"
            class="text-white/20 transition-transform duration-300 group-hover:text-white/40"
            :class="openGroups.dataManagement ? 'rotate-180' : ''"
          />
        </button>
        <div
          class="overflow-hidden transition-all duration-300 ease-in-out pl-1"
          :class="openGroups.dataManagement ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'"
        >
          <template v-for="link in dataManagementLinks" :key="link.to">
            <router-link
              :to="link.to"
              @click="emit('close')"
              class="group flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200"
              :class="isActive(link.to) ? 'bg-white/[0.07] text-white' : 'text-white/35 hover:text-white/80 hover:bg-white/[0.04]'"
            >
              <component :is="link.icon" size="14" :class="isActive(link.to) ? 'text-white/70' : 'text-white/20 group-hover:text-white/50'" />
              <span class="text-[13px] font-medium font-inter tracking-normal">{{ link.label }}</span>
            </router-link>
          </template>
        </div>
      </div>

      <!-- KELOMPOK 3: OTORITAS INTERNAL -->
      <div v-if="userRole === 'owner'" class="space-y-0.5">
        <button
          type="button"
          @click="toggleGroup('internal')"
          class="group w-full flex items-center justify-between px-3 py-2.5 rounded-xl hover:bg-white/[0.03] transition-colors"
        >
          <span class="flex items-center gap-2.5">
            <ShieldCheck size="14" class="text-white/20" />
            <span class="text-[12px] font-semibold text-white/50 group-hover:text-white/70 tracking-wide font-inter transition-colors">Internal</span>
          </span>
          <ChevronDown
            size="13"
            class="text-white/20 transition-transform duration-300 group-hover:text-white/40"
            :class="openGroups.internal ? 'rotate-180' : ''"
          />
        </button>
        <div
          class="overflow-hidden transition-all duration-300 ease-in-out pl-1"
          :class="openGroups.internal ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'"
        >
          <template v-for="link in internalLinks" :key="link.to">
            <router-link
              :to="link.to"
              @click="emit('close')"
              class="group flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200"
              :class="isActive(link.to) ? 'bg-white/[0.07] text-white' : 'text-white/35 hover:text-white/80 hover:bg-white/[0.04]'"
            >
              <component :is="link.icon" size="14" :class="isActive(link.to) ? 'text-white/70' : 'text-white/20 group-hover:text-white/50'" />
              <span class="text-[13px] font-medium font-inter tracking-normal">{{ link.label }}</span>
            </router-link>
          </template>
        </div>
      </div>

      <!-- PROFIL -->
      <div class="pt-2 border-t border-white/[0.04] mt-2 space-y-0.5">
        <router-link
          to="/admin/profile"
          @click="emit('close')"
          class="group flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200"
          :class="isActive('/admin/profile') ? 'bg-white/[0.07] text-white' : 'text-white/35 hover:text-white/80 hover:bg-white/[0.04]'"
        >
          <UserCheck size="14" :class="isActive('/admin/profile') ? 'text-white/70' : 'text-white/20 group-hover:text-white/50'" />
          <span class="text-[13px] font-medium font-inter tracking-normal">Profil Saya</span>
        </router-link>
      </div>

    </nav>

    <!-- Footer Logout -->
    <div class="px-5 py-4 border-t border-white/[0.04]">
      <button
        @click="showLogoutModal = true"
        class="group flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-white/25 hover:text-white/60 hover:bg-white/[0.04] transition-all text-[13px] font-medium font-inter cursor-pointer"
      >
        <LogOut size="14" class="group-hover:text-white/50 transition-colors" />
        Keluar
      </button>
    </div>
  </aside>

  <!-- ── CONFIRM MODAL LOGOUT ── -->
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="showLogoutModal"
        class="fixed inset-0 z-[9998] flex items-center justify-center p-4"
        @click.self="showLogoutModal = false"
      >
        <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" />
        <div class="relative bg-[#0f0f0f] border border-white/[0.08] rounded-2xl p-6 w-full max-w-sm shadow-2xl">
          <div class="flex justify-center mb-5">
            <div class="w-11 h-11 rounded-xl bg-white/[0.04] border border-white/[0.06] flex items-center justify-center">
              <LogOut size="18" class="text-white/40" />
            </div>
          </div>
          <h3 class="text-white font-oswald text-base uppercase text-center mb-1.5 tracking-wide">Keluar Sekarang?</h3>
          <p class="text-white/30 text-[12px] text-center leading-relaxed mb-6 font-inter">
            Sesi kamu akan diakhiri. Pastikan semua pekerjaan sudah tersimpan.
          </p>
          <div class="flex gap-2.5">
            <button
              @click="showLogoutModal = false"
              class="flex-1 px-4 py-2.5 rounded-xl border border-white/[0.08] text-white/30 text-[13px] font-medium hover:text-white/60 hover:border-white/[0.15] transition-all font-inter"
            >
              Batal
            </button>
            <button
              @click="confirmLogout"
              class="flex-1 px-4 py-2.5 rounded-xl bg-white/[0.08] hover:bg-white/[0.13] border border-white/[0.08] text-white/80 text-[13px] font-semibold transition-all font-inter"
            >
              Ya, Keluar
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- ── TOAST NOTIFICATIONS ── -->
  <Teleport to="body">
    <div class="fixed top-5 right-5 z-[9999] flex flex-col gap-2.5 pointer-events-none">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="pointer-events-auto flex items-start gap-3 px-4 py-3 rounded-xl border shadow-2xl min-w-[260px] max-w-[340px] bg-[#111] backdrop-blur-xl"
          :class="{
            'border-emerald-500/20 text-emerald-400': toast.type === 'success',
            'border-red-500/20 text-red-400':         toast.type === 'error',
            'border-amber-500/20 text-amber-400':     toast.type === 'warning',
            'border-white/[0.08] text-white/60':      toast.type === 'info',
          }"
        >
          <CheckCircle2  v-if="toast.type === 'success'" size="14" class="mt-0.5 shrink-0" />
          <XCircle       v-else-if="toast.type === 'error'"   size="14" class="mt-0.5 shrink-0" />
          <AlertTriangle v-else-if="toast.type === 'warning'" size="14" class="mt-0.5 shrink-0" />
          <Info          v-else                               size="14" class="mt-0.5 shrink-0" />
          <p class="text-[12px] font-medium leading-snug font-inter flex-1">{{ toast.message }}</p>
          <button
            @click="removeToast(toast.id)"
            class="shrink-0 opacity-30 hover:opacity-70 transition-opacity"
          >
            <X size="13" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import {
  LayoutDashboard, Users, Clock, Settings, LogOut,
  ShoppingCart, ChefHat, BarChart3, Wallet, UserPlus,
  UserCheck, Edit3, ChevronDown, Zap, FolderOpen, ShieldCheck,
  CheckCircle2, XCircle, AlertTriangle, Info, X, Tag,
  Crown, User, BriefcaseBusiness, Gift,
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useOrderNotificationsStore } from '@/stores/orderNotifications'
import { useRoute } from 'vue-router'
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({ open: Boolean })
const emit  = defineEmits(['close'])

const auth      = useAuthStore()
const notifStore = useOrderNotificationsStore()
const route     = useRoute()
const user      = computed(() => auth.user)
const userRole  = computed(() => auth.user?.role?.toLowerCase() || 'kasir')
const isActive  = (path) => route.path === path

const handleNavClick = (path) => {
  if (path === '/admin/orders') notifStore.clearUnread()
  emit('close')
}

const operationalLinks = [
  { to: '/admin/pos',    icon: ShoppingCart, label: 'New Order (POS)', roles: ['owner', 'admin', 'kasir'] },
  { to: '/admin/orders', icon: Clock,        label: 'Active Orders',   roles: ['owner', 'admin', 'kasir'] },
]
const dataManagementLinks = [
  { to: '/admin/menus',         icon: ChefHat,   label: 'Manage Menus' },
  { to: '/admin/promos',        icon: Tag,        label: 'Kelola Promo' },
  { to: '/admin/point-rewards', icon: Gift,       label: 'Kelola Reward Poin' },
  { to: '/admin/reports',       icon: BarChart3,  label: 'Menu Reports' },
  { to: '/admin/edit-homepage', icon: Edit3,      label: 'Edit Homepage' },
  { to: '/admin/customers',     icon: Users,      label: 'Loyal Customers' },
]
const internalLinks = [
  { to: '/admin/finance',          icon: Wallet,   label: 'Buku Kas & Keuangan' },
  { to: '/admin/registerinternal', icon: UserPlus, label: 'Register Staff Baru' },
  { to: '/admin/settings',         icon: Settings, label: 'System Settings' },
]

const allLinks = [
  ...operationalLinks.map(l    => ({ ...l, group: 'operational' })),
  ...dataManagementLinks.map(l => ({ ...l, group: 'dataManagement' })),
  ...internalLinks.map(l       => ({ ...l, group: 'internal' })),
]
const findActiveGroup = (path) => allLinks.find(l => l.to === path)?.group

const openGroups = reactive({
  operational:    true,
  dataManagement: findActiveGroup(route.path) === 'dataManagement',
  internal:       findActiveGroup(route.path) === 'internal',
})
const toggleGroup = (key) => { openGroups[key] = !openGroups[key] }

watch(() => route.path, (newPath) => {
  const group = findActiveGroup(newPath)
  if (group) openGroups[group] = true
})

// Toast
const toasts = ref([])
let toastId  = 0

const addToast = (message, type = 'info', duration = 3500) => {
  const id = ++toastId
  toasts.value.push({ id, message, type })
  setTimeout(() => removeToast(id), duration)
}
const removeToast = (id) => {
  const idx = toasts.value.findIndex(t => t.id === id)
  if (idx !== -1) toasts.value.splice(idx, 1)
}

// Logout
const showLogoutModal = ref(false)

const confirmLogout = async () => {
  showLogoutModal.value = false
  try {
    await auth.logout()
    addToast('Berhasil keluar. Sampai jumpa!', 'success')
  } catch {
    addToast('Gagal logout. Coba lagi.', 'error')
  }
}
</script>

<style scoped>
.scrollbar-none::-webkit-scrollbar { display: none; }
.scrollbar-none { -ms-overflow-style: none; scrollbar-width: none; }

.modal-enter-active, .modal-leave-active { transition: all 0.2s ease; }
.modal-enter-from,   .modal-leave-to     { opacity: 0; transform: scale(0.97); }

.toast-enter-active { transition: all 0.25s ease; }
.toast-leave-active { transition: all 0.2s ease; }
.toast-enter-from   { opacity: 0; transform: translateX(16px); }
.toast-leave-to     { opacity: 0; transform: translateX(16px); }
</style>