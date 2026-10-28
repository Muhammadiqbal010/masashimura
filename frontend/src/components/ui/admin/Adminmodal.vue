<template>
  <Teleport to="body">
    <Transition name="adm-modal">
      <div v-if="modelValue" ref="overlayEl" class="adm-overlay" @mousedown.self="onBackdrop">
        <div
          ref="dialogEl"
          class="adm-modal"
          :class="`adm-modal--${size}`"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="titleId"
          tabindex="-1"
          @keydown.tab="trapTab"
        >
          <header class="adm-modal-head">
            <h2 :id="titleId" class="adm-modal-title">{{ title }}</h2>
            <button type="button" class="adm-icon-btn" aria-label="Tutup" @click="close">
              <X :size="16" />
            </button>
          </header>

          <div ref="bodyEl" class="adm-modal-body">
            <slot />
          </div>

          <footer v-if="$slots.footer" class="adm-modal-foot">
            <slot name="footer" />
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
// State bersama SEMUA instance modal. Harus di <script> biasa: top-level <script setup> itu
// dibuat ulang per instance, sehingga stack modal & penghitung kunci scroll tidak akan terbagi.
let uid = 0
const stack = []
let lockCount = 0
let rewinding = false   // true selama history.back() buatan modal sendiri; modal lain mengabaikannya
</script>

<script setup>
// Modal admin: Escape menutup, fokus dikunci di dalam dialog, fokus kembali ke
// tombol pemicu saat ditutup, scroll body dikunci, dan modal bertumpuk (mis.
// "Tambah Kategori" di atas "Edit Menu") hanya menutup yang paling atas.
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { X } from 'lucide-vue-next'
import { isTouchDevice, isTextEntry } from '@/utils/touch'

const props = defineProps({
  modelValue: Boolean,
  title: { type: String, required: true },
  size: { type: String, default: 'md' }, // sm | md | lg
  persistent: Boolean,                   // true → tidak bisa ditutup (mis. saat menyimpan)
  backClose: Boolean,                    // true → tombol Back (browser / HP) menutup modal, bukan pindah halaman
})
const emit = defineEmits(['update:modelValue', 'close'])

const titleId = `adm-modal-title-${++uid}`
const overlayEl = ref(null)
const dialogEl = ref(null)
const bodyEl = ref(null)
const token = {}
let opener = null
let active = false

const FOCUSABLE =
  'a[href],button:not([disabled]),input:not([disabled]):not([type=hidden]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])'

// ── Keyboard layar (HP) ─────────────────────────────────────────────
// Saat keyboard muncul, viewport visual mengecil tapi layout viewport tidak, sehingga
// bottom-sheet tertutup keyboard. Kita samakan tinggi overlay dengan viewport visual
// (lewat CSS var) dan gulirkan kolom yang sedang diketik ke tengah layar.
const syncViewport = () => {
  const vv = window.visualViewport
  const el = overlayEl.value
  if (!vv || !el) return
  el.style.setProperty('--adm-vvh', `${vv.height}px`)
  el.style.setProperty('--adm-vvt', `${vv.offsetTop}px`)
}
const onFocusIn = (e) => {
  if (!isTouchDevice() || !isTextEntry(e.target)) return
  // Tunggu keyboard selesai naik, baru gulirkan.
  setTimeout(() => e.target?.scrollIntoView?.({ block: 'center', behavior: 'smooth' }), 300)
}
const bindViewport = () => {
  if (!isTouchDevice() || !window.visualViewport) return
  window.visualViewport.addEventListener('resize', syncViewport)
  window.visualViewport.addEventListener('scroll', syncViewport)
  syncViewport()
}
const unbindViewport = () => {
  window.visualViewport?.removeEventListener('resize', syncViewport)
  window.visualViewport?.removeEventListener('scroll', syncViewport)
}

const close = () => {
  if (props.persistent) return
  emit('update:modelValue', false)
  emit('close')
}
const onBackdrop = () => close()

const onKey = (e) => {
  if (e.key === 'Escape' && stack[stack.length - 1] === token) {
    e.stopPropagation()
    close()
  }
}

const trapTab = (e) => {
  const items = [...dialogEl.value.querySelectorAll(FOCUSABLE)].filter((el) => el.offsetParent !== null)
  if (!items.length) { e.preventDefault(); return }
  const first = items[0]
  const last = items[items.length - 1]
  if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus() }
  else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus() }
}

// ── Tombol Back menutup modal ───────────────────────────────────────
// Saat modal (backClose) dibuka kita selipkan 1 entri riwayat. Back = entri itu dibuang
// → modal tertutup, halaman TETAP di tempat. Kalau modal ditutup lewat X / Esc / klik luar,
// entri selipan dibuang lewat history.back() supaya Back berikutnya tidak "kosong".
let pushed = false

const onPop = () => {
  if (!pushed || rewinding) return
  // Modal bertumpuk: satu kali Back hanya menutup modal paling atas.
  if (stack[stack.length - 1] !== token) return
  if (props.persistent) {
    // Lagi menyimpan: Back tidak boleh menutup modal. Pasang lagi entri yang baru terbuang.
    history.pushState({ ...(history.state || {}), __admModal: true }, '')
    return
  }
  pushed = false
  window.removeEventListener('popstate', onPop)
  emit('update:modelValue', false)
  emit('close')
}

const pushBackEntry = () => {
  if (!props.backClose || pushed) return
  // Spread state lama supaya data milik vue-router (position, dll) tidak hilang.
  history.pushState({ ...(history.state || {}), __admModal: true }, '')
  pushed = true
  window.addEventListener('popstate', onPop)
}

const dropBackEntry = ({ rewind }) => {
  if (!pushed) return
  pushed = false
  window.removeEventListener('popstate', onPop)
  if (rewind && history.state && history.state.__admModal) {
    rewinding = true
    // Didaftarkan SETELAH listener modal lain, jadi dijalankan paling akhir di popstate yang sama.
    window.addEventListener('popstate', () => { rewinding = false }, { once: true })
    history.back()
  }
}

const activate = async () => {
  if (active) return
  active = true
  pushBackEntry()
  opener = document.activeElement
  stack.push(token)
  if (lockCount++ === 0) document.body.classList.add('adm-no-scroll')
  document.addEventListener('keydown', onKey)
  await nextTick()
  bindViewport()
  dialogEl.value?.addEventListener('focusin', onFocusIn)
  let target =
    bodyEl.value?.querySelector('[data-autofocus]') ||
    bodyEl.value?.querySelector(FOCUSABLE) ||
    dialogEl.value
  // HP/tablet: jangan fokus otomatis ke kolom ketik — itu langsung memunculkan keyboard
  // yang menutupi separuh modal. Fokus ke dialog saja; keyboard baru muncul saat kolom diketuk.
  if (isTouchDevice() && isTextEntry(target)) target = dialogEl.value
  target?.focus({ preventScroll: true })
}

const deactivate = ({ rewind = true } = {}) => {
  if (!active) return
  active = false
  dropBackEntry({ rewind })
  const i = stack.indexOf(token)
  if (i !== -1) stack.splice(i, 1)
  if (--lockCount <= 0) { lockCount = 0; document.body.classList.remove('adm-no-scroll') }
  document.removeEventListener('keydown', onKey)
  unbindViewport()
  dialogEl.value?.removeEventListener('focusin', onFocusIn)
  // Di HP jangan kembalikan fokus ke kolom ketik (keyboard akan muncul lagi tanpa diminta).
  if (opener && document.contains(opener) && !(isTouchDevice() && isTextEntry(opener))) opener.focus?.({ preventScroll: true })
  opener = null
}

watch(() => props.modelValue, (v) => (v ? activate() : deactivate()), { immediate: true })
// Komponen dilepas (mis. pindah halaman): jangan panggil history.back() lagi, cukup bersihkan.
onBeforeUnmount(() => deactivate({ rewind: false }))
</script>