// Mengisi kolom pencarian sebuah halaman dari ?q= di URL (dipakai pencarian global Ctrl/Cmd+K).
// Ikut berubah kalau URL berganti saat halaman yang sama sedang terbuka.
import { watch } from 'vue'
import { useRoute } from 'vue-router'

export function useRouteSearch(searchRef) {
  const route = useRoute()
  watch(
    () => route.query.q,
    (v) => { if (typeof v === 'string') searchRef.value = v },
    { immediate: true },
  )
}
