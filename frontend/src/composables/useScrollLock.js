import { onUnmounted } from "vue"

// Daftar pengunci aktif. Scroll baru dibuka lagi kalau SEMUA pengunci sudah lepas,
// jadi navbar & lightbox tidak saling membuka kunci satu sama lain.
const locks = new Set()

const apply = () => {
  document.body.style.overflow = locks.size > 0 ? "hidden" : ""
}

export function useScrollLock() {
  const id = Symbol("scroll-lock")

  const lock = () => {
    locks.add(id)
    apply()
  }
  const unlock = () => {
    locks.delete(id)
    apply()
  }

  // Pastikan kunci lepas kalau komponen dibongkar
  onUnmounted(unlock)

  return { lock, unlock }
}