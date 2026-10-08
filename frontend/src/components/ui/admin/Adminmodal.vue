<template>
  <Teleport to="body">
    <Transition name="adm-modal">
      <div v-if="modelValue" class="adm-overlay" @mousedown.self="onBackdrop">
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

<script setup>
// Modal admin: Escape menutup, fokus dikunci di dalam dialog, fokus kembali ke
// tombol pemicu saat ditutup, scroll body dikunci, dan modal bertumpuk (mis.
// "Tambah Kategori" di atas "Edit Menu") hanya menutup yang paling atas.
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { X } from 'lucide-vue-next'

let uid = 0
const stack = []
let lockCount = 0

const props = defineProps({
  modelValue: Boolean,
  title: { type: String, required: true },
  size: { type: String, default: 'md' }, // sm | md | lg
  persistent: Boolean,                   // true → tidak bisa ditutup (mis. saat menyimpan)
})
const emit = defineEmits(['update:modelValue', 'close'])

const titleId = `adm-modal-title-${++uid}`
const dialogEl = ref(null)
const bodyEl = ref(null)
const token = {}
let opener = null
let active = false

const FOCUSABLE =
  'a[href],button:not([disabled]),input:not([disabled]):not([type=hidden]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])'

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

const activate = async () => {
  if (active) return
  active = true
  opener = document.activeElement
  stack.push(token)
  if (lockCount++ === 0) document.body.classList.add('adm-no-scroll')
  document.addEventListener('keydown', onKey)
  await nextTick()
  const target =
    bodyEl.value?.querySelector('[data-autofocus]') ||
    bodyEl.value?.querySelector(FOCUSABLE) ||
    dialogEl.value
  target?.focus({ preventScroll: true })
}

const deactivate = () => {
  if (!active) return
  active = false
  const i = stack.indexOf(token)
  if (i !== -1) stack.splice(i, 1)
  if (--lockCount <= 0) { lockCount = 0; document.body.classList.remove('adm-no-scroll') }
  document.removeEventListener('keydown', onKey)
  if (opener && document.contains(opener)) opener.focus?.({ preventScroll: true })
  opener = null
}

watch(() => props.modelValue, (v) => (v ? activate() : deactivate()), { immediate: true })
onBeforeUnmount(deactivate)
</script>