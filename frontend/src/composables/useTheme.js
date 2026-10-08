// src/composables/useTheme.js
//
// Tema admin (gelap / terang) — singleton, jadi semua komponen yang memanggil
// useTheme() berbagi state yang sama.
//
// - Disimpan di localStorage, default "gelap" (tampilan lama).
// - Diterapkan lewat atribut <html data-admin-theme="dark|light">. Atribut ini
//   HANYA dipasang selama area admin aktif (lihat releaseTheme di AdminSidebar),
//   jadi halaman customer tidak ikut terpengaruh.
// - Semua warna datang dari CSS variable di assets/admin-theme.css.

import { ref, computed } from 'vue'

const STORAGE_KEY = 'masashimura-admin-theme'
const ATTR = 'data-admin-theme'
const SWITCHING_ATTR = 'data-theme-switching'
const THEMES = ['dark', 'light']
const META_COLOR = { dark: '#08080a', light: '#f4f4f5' }

const readStored = () => {
  try {
    const value = localStorage.getItem(STORAGE_KEY)
    return THEMES.includes(value) ? value : null
  } catch {
    return null // mode private / storage diblokir — tetap jalan tanpa persist
  }
}

const theme = ref(readStored() || 'dark')

// true hanya selama area admin aktif (useTheme() dipanggil) → event storage dari
// tab lain tidak boleh memasang atribut di halaman customer.
let active = false

const setMetaThemeColor = (value) => {
  let meta = document.querySelector('meta[name="theme-color"][data-admin]')
  if (!meta) {
    meta = document.createElement('meta')
    meta.setAttribute('name', 'theme-color')
    meta.setAttribute('data-admin', '')
    document.head.appendChild(meta)
  }
  meta.setAttribute('content', META_COLOR[value])
}

const apply = (value, { animate = false } = {}) => {
  if (typeof document === 'undefined') return
  const root = document.documentElement

  // Matikan transition sesaat saat ganti tema, biar semua elemen berganti
  // warna barengan (tanpa efek "kedip bertahap" tiap komponen).
  if (animate) {
    root.setAttribute(SWITCHING_ATTR, '')
    requestAnimationFrame(() =>
      requestAnimationFrame(() => root.removeAttribute(SWITCHING_ATTR))
    )
  }

  root.setAttribute(ATTR, value)
  setMetaThemeColor(value)
}

// Sinkron antar-tab: ganti tema di satu tab, tab admin lain ikut berubah.
let listening = false
const listenStorage = () => {
  if (listening || typeof window === 'undefined') return
  listening = true
  window.addEventListener('storage', (e) => {
    if (e.key === STORAGE_KEY && THEMES.includes(e.newValue)) {
      theme.value = e.newValue
      if (active) apply(e.newValue, { animate: true })
    }
  })
}

export function useTheme() {
  // Dipanggil di setup() tiap komponen → atribut sudah terpasang sebelum
  // render pertama, jadi tidak ada kedipan warna.
  active = true
  apply(theme.value)
  listenStorage()

  const isDark = computed(() => theme.value === 'dark')

  const setTheme = (value) => {
    if (!THEMES.includes(value)) return
    theme.value = value
    try { localStorage.setItem(STORAGE_KEY, value) } catch { /* abaikan */ }
    apply(value, { animate: true })
  }

  const toggleTheme = () => setTheme(isDark.value ? 'light' : 'dark')

  // Dipanggil saat keluar dari area admin supaya halaman lain tidak
  // kena color-scheme / background tema admin.
  const releaseTheme = () => {
    active = false
    if (typeof document === 'undefined') return
    document.documentElement.removeAttribute(ATTR)
    document.querySelector('meta[name="theme-color"][data-admin]')?.remove()
  }

  return { theme, isDark, setTheme, toggleTheme, releaseTheme }
}