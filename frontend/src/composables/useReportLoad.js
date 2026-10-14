/**
 * useReportLoad — pola muat data untuk tab laporan.
 * Memuat saat dipasang dan tiap kali `params` berubah. Jawaban lama yang datang
 * terlambat diabaikan, supaya ganti periode cepat-cepat tidak menampilkan data basi.
 */
import { ref, watch, onMounted } from "vue"

export function useReportLoad(fetcher, getParams) {
  const data = ref(null)
  const loading = ref(false)
  const error = ref(false)
  let latest = 0

  const load = async () => {
    const mine = ++latest
    loading.value = true
    error.value = false
    try {
      const res = await fetcher(getParams())
      if (mine !== latest) return
      data.value = res.data
    } catch {
      if (mine !== latest) return
      error.value = true
    } finally {
      if (mine === latest) loading.value = false
    }
  }

  onMounted(load)
  watch(getParams, load, { deep: true })

  return { data, loading, error, load }
}
