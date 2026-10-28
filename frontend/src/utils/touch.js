// Deteksi perangkat layar sentuh (HP / tablet). Dipakai supaya kolom ketik TIDAK
// di-fokus otomatis di perangkat sentuh — fokus otomatis = keyboard muncul menutupi layar.
export const isTouchDevice = () =>
  typeof window !== 'undefined' &&
  !!(window.matchMedia?.('(pointer: coarse)').matches || window.matchMedia?.('(hover: none)').matches)

// Fokus ke elemen hanya di desktop (mouse/keyboard fisik).
export const focusOnDesktop = (el) => {
  if (!el || isTouchDevice()) return
  el.focus?.({ preventScroll: true })
}

// Elemen yang memunculkan keyboard layar saat difokus.
export const isTextEntry = (el) => {
  if (!el) return false
  if (el.tagName === 'TEXTAREA' || el.tagName === 'SELECT' || el.isContentEditable) return true
  if (el.tagName !== 'INPUT') return false
  return !['checkbox', 'radio', 'button', 'submit', 'range', 'file', 'color', 'reset', 'image'].includes(el.type)
}

// Menjaga CSS var --vvh (tinggi viewport visual) & --vvt di <html>. Di HP, saat keyboard muncul,
// viewport visual mengecil sementara layout viewport tidak; modal pakai var ini supaya tidak
// tertutup keyboard. Panggil sekali di main.js.
export const initViewportVars = () => {
  if (typeof window === 'undefined' || !window.visualViewport || !isTouchDevice()) return
  const root = document.documentElement
  const sync = () => {
    root.style.setProperty('--vvh', `${window.visualViewport.height}px`)
    root.style.setProperty('--vvt', `${window.visualViewport.offsetTop}px`)
  }
  window.visualViewport.addEventListener('resize', sync)
  window.visualViewport.addEventListener('scroll', sync)
  sync()
}
