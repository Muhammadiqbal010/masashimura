// src/composables/useAdminConfirm.js
//
// Pengganti window.confirm() yang ikut tema & bisa di-await:
//
//   const { state, ask, accept, cancel } = useAdminConfirm()
//   if (!(await ask({ title: 'Hapus?', message: '…', danger: true }))) return
//
//   <AdminConfirm :state="state" @confirm="accept" @cancel="cancel" />

import { reactive } from 'vue'

const defaults = () => ({
  title: '',
  message: '',
  confirmText: 'Ya, lanjutkan',
  cancelText: 'Batal',
  danger: false,
})

export function useAdminConfirm() {
  const state = reactive({ open: false, ...defaults() })
  let resolver = null

  const settle = (value) => {
    state.open = false
    resolver?.(value)
    resolver = null
  }

  const ask = (options = {}) =>
    new Promise((resolve) => {
      resolver?.(false)
      Object.assign(state, defaults(), options, { open: true })
      resolver = resolve
    })

  return { state, ask, accept: () => settle(true), cancel: () => settle(false) }
}