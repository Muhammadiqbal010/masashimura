<template>
  <div class="qs">
    <!-- Pemicu: kolom pencarian di desktop, tombol ikon di HP -->
    <button
      ref="triggerRef"
      type="button"
      class="qs-trigger"
      :class="`qs-trigger--${variant}`"
      aria-haspopup="dialog"
      :aria-expanded="open"
      aria-label="Cari di admin"
      @click="openPalette"
    >
      <Search :size="16" aria-hidden="true" />
      <template v-if="variant === 'field'">
        <span class="qs-trigger-text">Cari apa saja…</span>
        <kbd class="qs-kbd" aria-hidden="true">{{ shortcutLabel }}</kbd>
      </template>
    </button>

    <Teleport to="body">
      <Transition name="qs-fade">
        <div v-if="open" class="qs-overlay" @mousedown.self="closePalette">
          <div
            class="qs-dialog"
            role="dialog"
            aria-modal="true"
            aria-label="Pencarian admin"
            @keydown="onDialogKeydown"
          >
            <div class="qs-input-row">
              <Search :size="18" aria-hidden="true" class="qs-input-icon" />
              <input
                ref="inputRef"
                v-model="query"
                type="text"
                class="qs-input"
                placeholder="Cari halaman, pesanan, menu, pelanggan, promo…"
                autocomplete="off"
                spellcheck="false"
                role="combobox"
                aria-expanded="true"
                aria-controls="qs-list"
                :aria-activedescendant="results.length ? `qs-opt-${active}` : undefined"
                aria-label="Cari di admin"
                @keydown.down.prevent="move(1)"
                @keydown.up.prevent="move(-1)"
                @keydown.enter.prevent="go(results[active])"
              />
              <button type="button" class="qs-esc" aria-label="Tutup pencarian" @click="closePalette">Esc</button>
            </div>

            <ul v-if="results.length" id="qs-list" class="qs-list" role="listbox" aria-label="Hasil pencarian">
              <template v-for="sec in sections" :key="sec.title">
                <li class="qs-sec" role="presentation">{{ sec.title }}</li>
                <li
                  v-for="r in sec.items"
                  :id="`qs-opt-${r.idx}`"
                  :key="r.key"
                  role="option"
                  :aria-selected="r.idx === active"
                  class="qs-item"
                  :class="{ 'is-active': r.idx === active }"
                  @mousemove="active = r.idx"
                  @click="go(r)"
                >
                  <span class="qs-item-label">{{ r.label }}</span>
                  <span class="qs-item-group">{{ r.hint }}</span>
                </li>
              </template>
            </ul>
            <p v-else-if="!loadingData" class="qs-empty" role="status">Tidak ada hasil untuk “{{ query }}”.</p>
            <p v-if="loadingData && query.trim().length >= 2" class="qs-loading" role="status">Memuat pesanan, menu, dan data lain…</p>

            <footer class="qs-foot" aria-hidden="true">
              <span><kbd class="qs-kbd">↑</kbd> <kbd class="qs-kbd">↓</kbd> pilih</span>
              <span><kbd class="qs-kbd">Enter</kbd> buka</span>
              <span><kbd class="qs-kbd">Esc</kbd> tutup</span>
            </footer>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { searchDestinations } from '@/utils/adminNav'
import { searchEntities, matchScore, norm } from '@/utils/adminSearch'
import { useTheme } from '@/composables/useTheme'
import { menuAPI } from '@/api/menu'
import { orderAPI, pointRewardAPI } from '@/api/order'
import { statsAPI } from '@/api/stats'
import apiClient from '@/api/client'

defineProps({
  // 'field' = kolom lebar (desktop), 'icon' = tombol ikon (HP)
  variant: { type: String, default: 'field' },
})

const router = useRouter()
const auth = useAuthStore()

const open = ref(false)
const query = ref('')
const active = ref(0)
const inputRef = ref(null)
const triggerRef = ref(null)

const role = computed(() => auth.user?.role?.toLowerCase() || 'kasir')
const { toggleTheme } = useTheme()

// ── Data yang dicari (dimuat sekali saat palet dibuka, disegarkan bila sudah > 1 menit) ──
const data = reactive({ orders: [], menus: [], customers: [], promos: [], rewards: [] })
const loadingData = ref(false)
let loadedAt = 0
const asList = (d) => (Array.isArray(d) ? d : (d?.results || d?.customers || []))
const todayWib = () => new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Jakarta' })

const loadData = async () => {
  if (Date.now() - loadedAt < 60_000) return
  loadingData.value = true
  const staff = role.value === 'owner' || role.value === 'admin'
  const jobs = staff
    ? [
        ['orders', orderAPI.getAll()],
        ['menus', menuAPI.getAll()],
        ['customers', statsAPI.getLoyalCustomers()],
        ['promos', apiClient.get('/promotions/')],
        ['rewards', pointRewardAPI.getAll()],
      ]
    // Kasir tidak punya akses daftar lengkap: cukup order hari ini (sama seperti halaman Pesanan).
    : [['orders', orderAPI.getActiveOrders(todayWib())]]
  const settled = await Promise.allSettled(jobs.map(([, p]) => p))
  settled.forEach((r, i) => { if (r.status === 'fulfilled') data[jobs[i][0]] = asList(r.value.data) })
  loadedAt = Date.now()
  loadingData.value = false
}

// Aksi cepat (bukan halaman): dijalankan langsung.
const ACTIONS = [
  { key: 'act-theme', label: 'Ganti tema gelap / terang', hint: 'Tampilan', keywords: 'tema mode gelap terang dark light tampilan', run: () => toggleTheme() },
]

// Susunan hasil: Halaman → Aksi → data. Tiap item diberi idx berurutan untuk navigasi keyboard.
const sections = computed(() => {
  const words = norm(query.value).split(/\s+/).filter(Boolean)
  const secs = []
  const pages = searchDestinations(query.value, role.value).map((d) => ({ key: d.to, label: d.label, hint: d.group, to: d.to }))
  if (pages.length) secs.push({ title: 'Halaman', items: pages })
  const acts = ACTIONS.filter((a) => !words.length || matchScore(words, [a.label, a.keywords]) > 0)
  if (acts.length && words.length) secs.push({ title: 'Aksi', items: acts })
  secs.push(...searchEntities(query.value, data))
  let n = 0
  return secs.map((sec) => ({ ...sec, items: sec.items.map((it) => ({ ...it, idx: n++ })) }))
})
const results = computed(() => sections.value.flatMap((s) => s.items))

const isMac = typeof navigator !== 'undefined' && /mac|iphone|ipad/i.test(navigator.platform || navigator.userAgent || '')
const shortcutLabel = isMac ? '⌘K' : 'Ctrl K'

watch(query, () => { active.value = 0 })
watch(query, (v) => { if (v.trim().length >= 2) loadData() })

const openPalette = async () => {
  if (open.value) return
  query.value = ''
  active.value = 0
  open.value = true
  await nextTick()
  inputRef.value?.focus()
  loadData()
}

const closePalette = () => {
  open.value = false
  // Kembalikan fokus ke pemicu supaya navigasi keyboard tidak "hilang".
  nextTick(() => triggerRef.value?.focus())
}

const move = (step) => {
  const n = results.value.length
  if (!n) return
  active.value = (active.value + step + n) % n
  nextTick(() => document.getElementById(`qs-opt-${active.value}`)?.scrollIntoView({ block: 'nearest' }))
}

const go = (item) => {
  if (!item) return
  open.value = false
  if (item.run) item.run()
  else router.push(item.to)
}

// Esc menutup; Tab dijaga di dalam dialog (hanya ada input dan tombol Esc).
const onDialogKeydown = (e) => {
  if (e.key === 'Escape') {
    e.preventDefault()
    closePalette()
  } else if (e.key === 'Tab') {
    const focusables = e.currentTarget.querySelectorAll('input, button')
    if (!focusables.length) return
    const first = focusables[0]
    const last = focusables[focusables.length - 1]
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus() }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus() }
  }
}

const onGlobalKeydown = (e) => {
  // Ada dua instance (desktop + HP); hanya yang pemicunya tampil yang menanggapi pintasan.
  if (!triggerRef.value || triggerRef.value.offsetParent === null) return
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    open.value ? closePalette() : openPalette()
  }
}

onMounted(() => window.addEventListener('keydown', onGlobalKeydown))
onUnmounted(() => window.removeEventListener('keydown', onGlobalKeydown))
</script>

<style scoped>
.qs-trigger {
  display: inline-flex; align-items: center; gap: 0.6rem;
  min-height: 40px; border-radius: var(--r-md);
  border: 1px solid var(--border); background: var(--surface); color: var(--text-dim);
  font: inherit; font-size: 0.875rem; cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.qs-trigger:hover { background: var(--surface-hover); color: var(--text); border-color: var(--border-strong); }
.qs-trigger--field { width: 100%; max-width: 22rem; padding: 0 0.6rem 0 0.85rem; }
.qs-trigger--icon { width: 44px; height: 44px; min-height: 44px; justify-content: center; padding: 0; }
.qs-trigger-text { flex: 1; text-align: left; }

.qs-kbd {
  display: inline-block; padding: 0.1rem 0.4rem; border-radius: var(--r-xs);
  border: 1px solid var(--border-strong); background: var(--surface-2); color: var(--text-dim);
  font-family: var(--font-mono); font-size: 0.75rem; line-height: 1.4;
}

.qs-overlay {
  position: fixed; inset: 0; z-index: var(--z-modal);
  display: flex; align-items: flex-start; justify-content: center;
  padding: max(env(safe-area-inset-top, 0px), 1rem) 1rem 1rem;
  padding-top: clamp(1rem, 12vh, 6rem);
  background: var(--overlay); backdrop-filter: blur(2px);
}
.qs-dialog {
  width: 100%; max-width: 38rem; max-height: min(34rem, 80dvh);
  display: flex; flex-direction: column; overflow: hidden;
  background: var(--surface); color: var(--text);
  border: 1px solid var(--border-strong); border-radius: var(--r-lg); box-shadow: var(--shadow-lg);
}
.qs-input-row { display: flex; align-items: center; gap: 0.6rem; padding: 0 0.75rem 0 1rem; border-bottom: 1px solid var(--border); }
.qs-input-icon { color: var(--text-faint); flex-shrink: 0; }
.qs-input {
  flex: 1; min-width: 0; height: 52px; background: transparent; border: 0; outline: none;
  color: var(--text); font: inherit; font-size: 1rem;
}
.qs-input::placeholder { color: var(--text-faint); }
.qs-esc {
  min-height: 32px; padding: 0 0.6rem; border-radius: var(--r-sm);
  border: 1px solid var(--border-strong); background: var(--surface-2); color: var(--text-dim);
  font-family: var(--font-mono); font-size: 0.75rem; cursor: pointer;
}

.qs-list { list-style: none; margin: 0; padding: 0.4rem; overflow-y: auto; }
.qs-item {
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
  min-height: 44px; padding: 0 0.85rem; border-radius: var(--r-md); cursor: pointer;
}
.qs-item.is-active { background: var(--accent); color: var(--on-accent); }
.qs-sec { padding: 0.55rem 0.85rem 0.25rem; font-size: 0.6875rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: var(--text-faint); }
.qs-item-label { font-weight: 600; font-size: 0.9375rem; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.qs-item-group { font-size: 0.75rem; color: var(--text-dim); white-space: nowrap; flex-shrink: 0; max-width: 55%; overflow: hidden; text-overflow: ellipsis; }
.qs-item.is-active .qs-item-group { color: color-mix(in srgb, var(--on-accent) 85%, transparent); }

.qs-loading { margin: 0; padding: 0.6rem 1rem; text-align: center; font-size: 0.8125rem; color: var(--text-faint); }
.qs-empty { margin: 0; padding: 1.75rem 1rem; text-align: center; font-size: 0.875rem; color: var(--text-dim); }
.qs-foot {
  display: flex; gap: 1rem; padding: 0.6rem 1rem; border-top: 1px solid var(--border);
  font-size: 0.75rem; color: var(--text-faint);
}

.qs-fade-enter-active, .qs-fade-leave-active { transition: opacity 0.15s ease; }
.qs-fade-enter-from, .qs-fade-leave-to { opacity: 0; }
@media (prefers-reduced-motion: reduce) {
  .qs-fade-enter-active, .qs-fade-leave-active { transition: none; }
}
@media (max-width: 639px) { .qs-foot { display: none; } }
</style>
