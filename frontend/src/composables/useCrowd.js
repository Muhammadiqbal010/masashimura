/**
 * useCrowd — status keramaian untuk badge pelanggan.
 *
 * Mengambil /orders/crowd/ saat komponen muncul lalu menyegarkan tiap 60 detik,
 * dan berhenti selama tab disembunyikan. Gagal memuat = badge disembunyikan
 * (lebih baik tidak tampil daripada menampilkan angka usang).
 */
import { ref, computed, onMounted, onUnmounted } from "vue"
import { crowdAPI } from "@/api/crowd"

const REFRESH_MS = 60_000

export function useCrowd() {
  const status = ref(null)
  let timer = null

  const load = async () => {
    try {
      const { data } = await crowdAPI.getStatus()
      status.value = data
    } catch {
      status.value = null
    }
  }

  const onVisibility = () => {
    if (document.visibilityState === "visible") load()
  }

  onMounted(() => {
    load()
    timer = setInterval(() => {
      if (document.visibilityState === "visible") load()
    }, REFRESH_MS)
    document.addEventListener("visibilitychange", onVisibility)
  })
  onUnmounted(() => {
    clearInterval(timer)
    document.removeEventListener("visibilitychange", onVisibility)
  })

  const visible = computed(() => !!status.value?.visible && !!status.value?.level)
  const level   = computed(() => status.value?.level || null)
  const label   = computed(() => status.value?.label || "")

  return { status, visible, level, label, reload: load }
}
