<template>
  <aside class="sb" :class="{ 'is-open': open }" aria-label="Navigasi admin">
    <!-- ── Brand ─────────────────────────────────────────────────── -->
    <div class="sb-brand">
      <div class="sb-brand-main">
        <!-- Logo dirancang untuk latar gelap, jadi di tema terang ditaruh di "tile" gelap -->
        <div class="sb-logo-tile">
          <img
            src="@/assets/masashimura-logo.png"
            alt="Masashimura"
            class="sb-logo"
            draggable="false"
          />
        </div>
        <p class="sb-eyebrow">Admin System</p>
      </div>

      <!-- Tombol close — mobile only -->
      <button type="button" class="sb-close" aria-label="Tutup navigasi" @click="emit('close')">
        <X :size="16" />
      </button>
    </div>

    <!-- ── Profil mini ───────────────────────────────────────────── -->
    <div class="sb-profile-wrap">
      <div class="sb-profile">
        <div class="sb-avatar" :class="`role-${userRole}`">
          <Crown v-if="userRole === 'owner'" :size="15" />
          <User v-else-if="userRole === 'admin'" :size="15" />
          <BriefcaseBusiness v-else :size="15" />
        </div>
        <div class="sb-profile-text">
          <p class="sb-name">{{ user?.name || 'Guest' }}</p>
          <span class="sb-role" :class="`role-${userRole}`">{{ userRole || 'Kasir' }}</span>
        </div>
      </div>
    </div>

    <!-- ── Navigasi ──────────────────────────────────────────────── -->
    <nav class="sb-nav" aria-label="Menu utama">
      <router-link
        v-if="canSeeDashboard"
        to="/admin/"
        class="sb-link"
        :class="{ 'is-active': isActive('/admin/') }"
        :aria-current="isActive('/admin/') ? 'page' : undefined"
        @click="emit('close')"
      >
        <LayoutDashboard :size="16" class="sb-link-icon" />
        <span class="sb-link-label">Dashboard</span>
      </router-link>

      <p class="sb-section">Navigasi</p>

      <div v-for="group in visibleGroups" :key="group.key" class="sb-group">
        <button
          type="button"
          class="sb-group-btn"
          :aria-expanded="openGroups[group.key] ? 'true' : 'false'"
          :aria-controls="`sb-grp-${group.key}`"
          @click="toggleGroup(group.key)"
        >
          <span class="sb-group-title">
            <component :is="group.icon" :size="15" class="sb-group-icon" :class="`tone-${group.tone}`" />
            <span>{{ group.label }}</span>
          </span>
          <ChevronDown :size="14" class="sb-chevron" :class="{ 'is-open': openGroups[group.key] }" />
        </button>

        <div
          :id="`sb-grp-${group.key}`"
          class="sb-collapse"
          :class="{ 'is-open': openGroups[group.key] }"
        >
          <div class="sb-collapse-inner">
            <router-link
              v-for="link in group.links"
              :key="link.to"
              :to="link.to"
              class="sb-link"
              :class="{ 'is-active': isActive(link.to) }"
              :aria-current="isActive(link.to) ? 'page' : undefined"
              @click="handleNavClick(link.to)"
            >
              <component :is="link.icon" :size="15" class="sb-link-icon" />
              <span class="sb-link-label">{{ link.label }}</span>
              <span
                v-if="link.to === '/admin/orders' && notifStore.unreadCount > 0"
                class="sb-badge"
                :aria-label="`${notifStore.unreadCount} pesanan baru`"
              >
                {{ notifStore.unreadCount > 9 ? '9+' : notifStore.unreadCount }}
              </span>
            </router-link>
          </div>
        </div>
      </div>

      <!-- Profil -->
      <div class="sb-account">
        <router-link
          to="/admin/profile"
          class="sb-link"
          :class="{ 'is-active': isActive('/admin/profile') }"
          :aria-current="isActive('/admin/profile') ? 'page' : undefined"
          @click="emit('close')"
        >
          <UserCheck :size="15" class="sb-link-icon" />
          <span class="sb-link-label">Profil Saya</span>
        </router-link>
      </div>
    </nav>

    <!-- ── Footer: switch tema + logout ──────────────────────────── -->
    <div class="sb-footer">
      <button
        type="button"
        class="sb-theme"
        role="switch"
        aria-label="Mode gelap"
        :aria-checked="isDark ? 'true' : 'false'"
        @click="toggleTheme"
      >
        <span class="sb-theme-text">
          <component :is="isDark ? Moon : Sun" :size="15" class="sb-theme-icon" />
          <span class="sb-theme-copy">
            <span class="sb-theme-title">Tampilan</span>
            <span class="sb-theme-state">{{ isDark ? 'Mode gelap' : 'Mode terang' }}</span>
          </span>
        </span>

        <span class="sb-switch" :class="{ 'is-on': isDark }" aria-hidden="true">
          <span class="sb-switch-thumb">
            <Moon v-if="isDark" :size="12" />
            <Sun v-else :size="12" />
          </span>
        </span>
      </button>

      <button type="button" class="sb-logout" @click="showLogoutModal = true">
        <LogOut :size="15" class="sb-link-icon" />
        <span>Keluar</span>
      </button>
    </div>
  </aside>

  <!-- ── Konfirmasi logout ─────────────────────────────────────── -->
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="showLogoutModal"
        class="sb-modal-overlay"
        @click.self="showLogoutModal = false"
      >
        <div
          class="sb-modal"
          role="alertdialog"
          aria-modal="true"
          aria-labelledby="sb-logout-title"
          aria-describedby="sb-logout-desc"
        >
          <div class="sb-modal-icon"><LogOut :size="18" /></div>
          <h3 id="sb-logout-title" class="sb-modal-title">Keluar Sekarang?</h3>
          <p id="sb-logout-desc" class="sb-modal-text">
            Sesi kamu akan diakhiri. Pastikan semua pekerjaan sudah tersimpan.
          </p>
          <div class="sb-modal-actions">
            <button ref="cancelLogoutBtn" type="button" class="sb-btn sb-btn-ghost" @click="showLogoutModal = false">
              Batal
            </button>
            <button type="button" class="sb-btn sb-btn-primary" @click="confirmLogout">
              Ya, Keluar
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- ── Toast ─────────────────────────────────────────────────── -->
  <Teleport to="body">
    <div class="sb-toasts" aria-live="polite" aria-atomic="false">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="sb-toast"
          :class="`is-${toast.type}`"
          :role="toast.type === 'error' ? 'alert' : 'status'"
        >
          <CheckCircle2 v-if="toast.type === 'success'" :size="15" class="sb-toast-icon" />
          <XCircle v-else-if="toast.type === 'error'" :size="15" class="sb-toast-icon" />
          <AlertTriangle v-else-if="toast.type === 'warning'" :size="15" class="sb-toast-icon" />
          <Info v-else :size="15" class="sb-toast-icon" />
          <p class="sb-toast-text">{{ toast.message }}</p>
          <button type="button" class="sb-toast-close" aria-label="Tutup notifikasi" @click="removeToast(toast.id)">
            <X :size="13" />
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
  Crown, User, BriefcaseBusiness, Gift, KeyRound, Sun, Moon,
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useOrderNotificationsStore } from '@/stores/orderNotifications'
import { useTheme } from '@/composables/useTheme'
import { useRoute } from 'vue-router'
import { computed, reactive, ref, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({ open: Boolean })
const emit  = defineEmits(['close'])

const auth       = useAuthStore()
const notifStore = useOrderNotificationsStore()
const route      = useRoute()
const { isDark, toggleTheme, releaseTheme } = useTheme()

const user     = computed(() => auth.user)
const userRole = computed(() => auth.user?.role?.toLowerCase() || 'kasir')

// ── Penentuan menu aktif ────────────────────────────────────────────
// Rute turunan (mis. /admin/menus/12) tetap menyorot induknya.
const normalize = (p = '') => (p.length > 1 ? p.replace(/\/+$/, '') : p)
const isActive = (path) => {
  const current = normalize(route.path)
  const target  = normalize(path)
  if (target === '/admin') return current === '/admin'
  return current === target || current.startsWith(target + '/')
}

const handleNavClick = (path) => {
  if (path === '/admin/orders') notifStore.clearUnread()
  emit('close')
}

// ── Definisi menu ───────────────────────────────────────────────────
const operationalLinks = [
  { to: '/admin/pos',    icon: ShoppingCart, label: 'New Order (POS)', roles: ['owner', 'admin', 'kasir'] },
  { to: '/admin/orders', icon: Clock,        label: 'Active Orders',   roles: ['owner', 'admin', 'kasir'] },
]
const dataManagementLinks = [
  { to: '/admin/menus',         icon: ChefHat,   label: 'Manage Menus' },
  { to: '/admin/promos',        icon: Tag,       label: 'Kelola Promo' },
  { to: '/admin/point-rewards', icon: Gift,      label: 'Kelola Reward Poin' },
  { to: '/admin/reports',       icon: BarChart3, label: 'Menu Reports' },
  { to: '/admin/edit-homepage', icon: Edit3,     label: 'Edit Homepage' },
  { to: '/admin/customers',     icon: Users,     label: 'Loyal Customers' },
]
const internalLinks = [
  { to: '/admin/finance',          icon: Wallet,   label: 'Buku Kas & Keuangan' },
  { to: '/admin/registerinternal', icon: UserPlus, label: 'Register Staff Baru' },
  { to: '/admin/staff',            icon: KeyRound, label: 'Kelola PIN Staff' },
  { to: '/admin/settings',         icon: Settings, label: 'System Settings' },
]

const groups = [
  { key: 'operational',    label: 'Operasional', icon: Zap,         tone: 'amber', roles: ['owner', 'admin', 'kasir'], links: operationalLinks },
  { key: 'dataManagement', label: 'Data & CMS',  icon: FolderOpen,  tone: 'sky',   roles: ['owner', 'admin'],          links: dataManagementLinks },
  { key: 'internal',       label: 'Internal',    icon: ShieldCheck, tone: 'muted', roles: ['owner'],                   links: internalLinks },
]

const canSeeDashboard = computed(() => ['owner', 'admin'].includes(userRole.value))

const visibleGroups = computed(() =>
  groups
    .filter((g) => g.roles.includes(userRole.value))
    .map((g) => ({ ...g, links: g.links.filter((l) => !l.roles || l.roles.includes(userRole.value)) }))
    .filter((g) => g.links.length)
)

const findActiveGroup = (path) =>
  groups.find((g) => g.links.some((l) => {
    const target = normalize(l.to)
    const current = normalize(path)
    return current === target || current.startsWith(target + '/')
  }))?.key

const openGroups = reactive({
  operational:    true,
  dataManagement: findActiveGroup(route.path) === 'dataManagement',
  internal:       findActiveGroup(route.path) === 'internal',
})
const toggleGroup = (key) => { openGroups[key] = !openGroups[key] }

watch(() => route.path, (newPath) => {
  const key = findActiveGroup(newPath)
  if (key) openGroups[key] = true
})

// ── Toast ───────────────────────────────────────────────────────────
const toasts = ref([])
let toastId = 0

const addToast = (message, type = 'info', duration = 3500) => {
  const id = ++toastId
  toasts.value.push({ id, message, type })
  setTimeout(() => removeToast(id), duration)
}
const removeToast = (id) => {
  const idx = toasts.value.findIndex((t) => t.id === id)
  if (idx !== -1) toasts.value.splice(idx, 1)
}

// ── Logout ──────────────────────────────────────────────────────────
const showLogoutModal  = ref(false)
const cancelLogoutBtn  = ref(null)

watch(showLogoutModal, async (v) => {
  if (v) { await nextTick(); cancelLogoutBtn.value?.focus() }
})

const confirmLogout = async () => {
  showLogoutModal.value = false
  try {
    await auth.logout()
    addToast('Berhasil keluar. Sampai jumpa!', 'success')
  } catch {
    addToast('Gagal logout. Coba lagi.', 'error')
  }
}

// ── Keyboard + kunci scroll saat drawer mobile terbuka ─────────────
const onKeydown = (e) => {
  if (e.key !== 'Escape') return
  if (showLogoutModal.value) { showLogoutModal.value = false; return }
  if (props.open) emit('close')
}

const mobileQuery = typeof window !== 'undefined' ? window.matchMedia('(max-width: 1023.98px)') : null
const syncScrollLock = () => {
  document.body.classList.toggle('adm-no-scroll', !!props.open && !!mobileQuery?.matches)
}
watch(() => props.open, syncScrollLock)

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
  mobileQuery?.addEventListener?.('change', syncScrollLock)
})
onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  mobileQuery?.removeEventListener?.('change', syncScrollLock)
  document.body.classList.remove('adm-no-scroll')
  releaseTheme() // keluar dari area admin → tema admin dilepas
})
</script>

<style scoped>
/* ── Shell ───────────────────────────────────────────────────────── */
.sb {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 40;
  width: min(16rem, 86vw);
  height: 100vh;
  height: 100dvh;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  color: var(--text);
  font-family: 'Inter', sans-serif;
  user-select: none;

  /* mobile: drawer tersembunyi. visibility mencegah fokus keyboard masuk ke menu yang tak terlihat */
  transform: translateX(-100%);
  visibility: hidden;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), visibility 0s linear 0.3s;
}
.sb.is-open {
  transform: none;
  visibility: visible;
  transition-delay: 0s;
  box-shadow: var(--shadow-lg);
}
@media (min-width: 1024px) {
  .sb {
    position: sticky;
    width: 16rem;
    transform: none;
    visibility: visible;
    box-shadow: none;
  }
}

/* ── Brand ───────────────────────────────────────────────────────── */
.sb-brand {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 1.5rem 1.25rem 1.1rem 1.5rem;
  padding-top: calc(1.5rem + env(safe-area-inset-top, 0px));
  border-bottom: 1px solid var(--border);
}
.sb-logo-tile {
  display: inline-flex;
  padding: 0.4rem 0.6rem;
  margin-left: -0.6rem;
  border-radius: 10px;
  background: var(--brand-tile);
}
.sb-logo {
  height: 1.75rem;
  width: auto;
  object-fit: contain;
  opacity: 0.92;
  pointer-events: none;
}
.sb-eyebrow {
  margin: 0.55rem 0 0;
  font-family: var(--font-mono);
  font-size: 0.68rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--text-faint);
}
.sb-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: var(--text-dim);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.sb-close:hover { background: var(--surface-hover); color: var(--text); }
@media (min-width: 1024px) { .sb-close { display: none; } }

/* ── Profil ──────────────────────────────────────────────────────── */
.sb-profile-wrap { padding: 0.9rem 1rem; border-bottom: 1px solid var(--border); }
.sb-profile {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.65rem 0.75rem;
  border-radius: 12px;
  background: rgb(var(--ink) / 0.03);
  border: 1px solid var(--border);
}
.sb-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  border-radius: 50%;
  background: rgb(34 197 94 / 0.12);
  border: 1px solid rgb(34 197 94 / 0.25);
  color: var(--green-soft);
}
.sb-avatar.role-owner { background: rgb(245 158 11 / 0.12); border-color: rgb(245 158 11 / 0.28); color: var(--amber-soft); }
.sb-avatar.role-admin { background: rgb(56 189 248 / 0.12); border-color: rgb(56 189 248 / 0.28); color: var(--blue-soft); }

.sb-profile-text { min-width: 0; flex: 1; }
.sb-name {
  margin: 0 0 0.25rem;
  font-size: 0.8125rem;
  font-weight: 600;
  line-height: 1.1;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sb-role {
  display: inline-block;
  padding: 0.12rem 0.45rem;
  border-radius: 6px;
  font-family: var(--font-mono);
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  background: rgb(34 197 94 / 0.12);
  color: var(--green-soft);
}
.sb-role.role-owner { background: rgb(245 158 11 / 0.12); color: var(--amber-soft); }
.sb-role.role-admin { background: rgb(56 189 248 / 0.12); color: var(--blue-soft); }

/* ── Nav ─────────────────────────────────────────────────────────── */
.sb-nav {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 2px;
  scrollbar-width: none;
}
.sb-nav::-webkit-scrollbar { display: none; }

.sb-section {
  margin: 0.6rem 0 0.2rem;
  padding: 0 0.75rem;
  font-family: var(--font-mono);
  font-size: 0.65rem;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.sb-link {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.7rem;
  min-height: 40px;
  padding: 0.5rem 0.75rem;
  border-radius: 10px;
  color: var(--text-dim);
  font-size: 0.8125rem;
  font-weight: 500;
  text-decoration: none;
  transition: background 0.15s, color 0.15s;
}
.sb-link:hover { background: var(--surface-hover); color: var(--text); }
.sb-link.is-active { background: rgb(var(--ink) / 0.07); color: var(--text); }
.sb-link.is-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 24%;
  bottom: 24%;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--accent);
}
.sb-link-icon { flex-shrink: 0; color: var(--text-faint); transition: color 0.15s; }
.sb-link:hover .sb-link-icon { color: var(--text-dim); }
.sb-link.is-active .sb-link-icon { color: var(--accent-text); }
.sb-link-label { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.sb-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 0.3rem;
  border-radius: 99px;
  background: var(--accent);
  color: var(--on-accent);
  font-family: var(--font-mono);
  font-size: 0.68rem;
  font-weight: 700;
}

/* Grup menu */
.sb-group { display: flex; flex-direction: column; gap: 2px; }
.sb-group-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  min-height: 40px;
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: var(--text-2);
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.sb-group-btn:hover { background: var(--surface-hover); color: var(--text); }
.sb-group-title {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.04em;
}
.sb-group-icon.tone-amber { color: var(--amber-soft); }
.sb-group-icon.tone-sky   { color: var(--blue-soft); }
.sb-group-icon.tone-muted { color: var(--text-faint); }
.sb-chevron { color: var(--text-faint); transition: transform 0.25s; }
.sb-chevron.is-open { transform: rotate(180deg); }

/* Collapse tanpa batas tinggi tetap (grid 0fr → 1fr) */
.sb-collapse {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 0.25s ease;
}
.sb-collapse.is-open { grid-template-rows: 1fr; }
.sb-collapse-inner {
  min-height: 0;
  overflow: hidden;
  padding-left: 0.25rem;
  display: flex;
  flex-direction: column;
  gap: 2px;
  visibility: hidden;
  transition: visibility 0s linear 0.25s;
}
.sb-collapse.is-open .sb-collapse-inner { visibility: visible; transition-delay: 0s; }

.sb-account {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--border);
}

/* ── Footer ──────────────────────────────────────────────────────── */
.sb-footer {
  padding: 0.75rem 1rem;
  padding-bottom: calc(0.75rem + env(safe-area-inset-bottom, 0px));
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

/* Switch tema */
.sb-theme {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  width: 100%;
  min-height: 48px;
  padding: 0.45rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: rgb(var(--ink) / 0.03);
  color: var(--text);
  font-family: inherit;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.sb-theme:hover { background: var(--surface-hover); border-color: var(--border-strong); }
.sb-theme-text { display: flex; align-items: center; gap: 0.65rem; min-width: 0; }
.sb-theme-icon { flex-shrink: 0; color: var(--amber-soft); }
.sb-theme-copy { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.sb-theme-title { font-size: 0.8125rem; font-weight: 600; line-height: 1.2; }
.sb-theme-state { font-size: 0.72rem; color: var(--text-dim); line-height: 1.2; }

.sb-switch {
  position: relative;
  flex-shrink: 0;
  width: 44px;
  height: 24px;
  border-radius: 99px;
  background: #fcd34d;
  border: 1px solid #f59e0b;
  transition: background 0.2s, border-color 0.2s;
}
.sb-switch.is-on { background: #3f3f46; border-color: #52525b; }
.sb-switch-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #ffffff;
  color: #b45309;
  box-shadow: 0 1px 3px rgb(0 0 0 / 0.3);
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), color 0.2s;
}
.sb-switch.is-on .sb-switch-thumb { transform: translateX(20px); color: #3f3f46; }

.sb-logout {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  width: 100%;
  min-height: 40px;
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: var(--text-dim);
  font-family: inherit;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.sb-logout:hover { background: rgb(220 38 38 / 0.1); color: var(--red-soft); }
.sb-logout:hover .sb-link-icon { color: var(--red-soft); }

/* ── Modal logout ────────────────────────────────────────────────── */
.sb-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 9998;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: var(--overlay);
  backdrop-filter: blur(4px);
}
.sb-modal {
  width: 100%;
  max-width: 24rem;
  padding: 1.5rem;
  border: 1px solid var(--border-strong);
  border-radius: 18px;
  background: var(--surface);
  color: var(--text);
  box-shadow: var(--shadow-lg);
  font-family: 'Inter', sans-serif;
}
.sb-modal-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  margin: 0 auto 1.1rem;
  border-radius: 12px;
  background: rgb(var(--ink) / 0.05);
  border: 1px solid var(--border);
  color: var(--text-dim);
}
.sb-modal-title {
  margin: 0 0 0.4rem;
  text-align: center;
  font-family: 'Oswald', sans-serif;
  font-size: 1.05rem;
  font-weight: 500;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.sb-modal-text {
  margin: 0 0 1.4rem;
  text-align: center;
  font-size: 0.8125rem;
  line-height: 1.55;
  color: var(--text-dim);
}
.sb-modal-actions { display: flex; gap: 0.6rem; }
.sb-btn {
  flex: 1;
  min-height: 44px;
  padding: 0.6rem 1rem;
  border-radius: 12px;
  border: 1px solid transparent;
  font-family: inherit;
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.sb-btn-ghost { background: transparent; border-color: var(--border-strong); color: var(--text-2); }
.sb-btn-ghost:hover { background: var(--surface-hover); color: var(--text); }
.sb-btn-primary { background: var(--accent); color: var(--on-accent); }
.sb-btn-primary:hover { background: var(--accent-hover); }

.modal-enter-active, .modal-leave-active { transition: opacity 0.2s ease; }
.modal-enter-active .sb-modal, .modal-leave-active .sb-modal { transition: transform 0.2s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .sb-modal, .modal-leave-to .sb-modal { transform: scale(0.97); }

/* ── Toast ───────────────────────────────────────────────────────── */
.sb-toasts {
  position: fixed;
  top: calc(env(safe-area-inset-top, 0px) + 0.75rem);
  left: 0.75rem;
  right: 0.75rem;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.6rem;
  pointer-events: none;
}
@media (min-width: 640px) {
  .sb-toasts { top: 1.25rem; left: auto; right: 1.25rem; }
}
.sb-toast {
  pointer-events: auto;
  display: flex;
  align-items: flex-start;
  gap: 0.7rem;
  width: min(100%, 22rem);
  padding: 0.75rem 0.9rem;
  border: 1px solid var(--border-strong);
  border-radius: 12px;
  background: var(--surface-2);
  color: var(--text-2);
  box-shadow: var(--shadow-lg);
  font-family: 'Inter', sans-serif;
}
.sb-toast.is-success { border-color: rgb(34 197 94 / 0.4); color: var(--green-soft); }
.sb-toast.is-error   { border-color: rgb(239 68 68 / 0.45); color: var(--red-soft); }
.sb-toast.is-warning { border-color: rgb(245 158 11 / 0.45); color: var(--amber-soft); }
.sb-toast-icon { margin-top: 1px; flex-shrink: 0; }
.sb-toast-text { flex: 1; margin: 0; font-size: 0.8125rem; font-weight: 500; line-height: 1.4; }
.sb-toast-close {
  flex-shrink: 0;
  display: inline-flex;
  padding: 2px;
  border: none;
  background: transparent;
  color: inherit;
  opacity: 0.55;
  cursor: pointer;
  transition: opacity 0.15s;
}
.sb-toast-close:hover { opacity: 1; }

.toast-enter-active { transition: all 0.25s ease; }
.toast-leave-active { transition: all 0.2s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateX(16px); }
</style>