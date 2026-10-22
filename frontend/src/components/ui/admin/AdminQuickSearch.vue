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
      aria-label="Cari halaman admin"
      @click="openPalette"
    >
      <Search :size="16" aria-hidden="true" />
      <template v-if="variant === 'field'">
        <span class="qs-trigger-text">Cari halaman…</span>
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
            aria-label="Pencarian halaman admin"
            @keydown="onDialogKeydown"
          >
            <div class="qs-input-row">
              <Search :size="18" aria-hidden="true" class="qs-input-icon" />
              <input
                ref="inputRef"
                v-model="query"
                type="text"
                class="qs-input"
                placeholder="Ketik: promo, kas, poin, menu…"
                autocomplete="off"
                spellcheck="false"
                role="combobox"
                aria-expanded="true"
                aria-controls="qs-list"
                :aria-activedescendant="results.length ? `qs-opt-${active}` : undefined"
                aria-label="Cari halaman"
                @keydown.down.prevent="move(1)"
                @keydown.up.prevent="move(-1)"
                @keydown.enter.prevent="go(results[active])"
              />
              <button type="button" class="qs-esc" aria-label="Tutup pencarian" @click="closePalette">Esc</button>
            </div>

            <ul v-if="results.length" id="qs-list" class="qs-list" role="listbox" aria-label="Hasil pencarian">
              <li
                v-for="(r, i) in results"
                :id="`qs-opt-${i}`"
                :key="r.to"
                role="option"
                :aria-selected="i === active"
                class="qs-item"
                :class="{ 'is-active': i === active }"
                @mousemove="active = i"
                @click="go(r)"
              >
                <span class="qs-item-label">{{ r.label }}</span>
                <span class="qs-item-group">{{ r.group }}</span>
              </li>
            </ul>
            <p v-else class="qs-empty" role="status">Tidak ada halaman yang cocok dengan “{{ query }}”.</p>

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
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { searchDestinations } from '@/utils/adminNav'

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
const results = computed(() => searchDestinations(query.value, role.value))

const isMac = typeof navigator !== 'undefined' && /mac|iphone|ipad/i.test(navigator.platform || navigator.userAgent || '')
const shortcutLabel = isMac ? '⌘K' : 'Ctrl K'

watch(query, () => { active.value = 0 })

const openPalette = async () => {
  if (open.value) return
  query.value = ''
  active.value = 0
  open.value = true
  await nextTick()
  inputRef.value?.focus()
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
  router.push(item.to)
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
  font-family: var(--font-mono); font-size: 0.6875rem; line-height: 1.4;
}

.qs-overlay {
  position: fixed; inset: 0; z-index: var(--z-modal);
  display: flex; align-items: flex-start; justify-content: center;
  padding: max(env(safe-area-inset-top, 0px), 1rem) 1rem 1rem;
  padding-top: clamp(1rem, 12vh, 6rem);
  background: var(--overlay); backdrop-filter: blur(2px);
}
.qs-dialog {
  width: 100%; max-width: 34rem; max-height: min(32rem, 80dvh);
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
  font-family: var(--font-mono); font-size: 0.6875rem; cursor: pointer;
}

.qs-list { list-style: none; margin: 0; padding: 0.4rem; overflow-y: auto; }
.qs-item {
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
  min-height: 44px; padding: 0 0.85rem; border-radius: var(--r-md); cursor: pointer;
}
.qs-item.is-active { background: var(--accent); color: var(--on-accent); }
.qs-item-label { font-weight: 600; font-size: 0.9375rem; }
.qs-item-group { font-size: 0.75rem; color: var(--text-dim); white-space: nowrap; }
.qs-item.is-active .qs-item-group { color: color-mix(in srgb, var(--on-accent) 85%, transparent); }

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
