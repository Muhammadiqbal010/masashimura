// src/composables/useRecommender.js
// Pembungkus reaktif untuk utils/recommender.js. Indeks TF-IDF dibangun ulang otomatis
// hanya saat daftar menu berubah (bukan setiap render).
import { computed, unref } from "vue"
import { buildIndex, similarTo, forCart } from "@/utils/recommender"

export function useRecommender(menusRef) {
  const index = computed(() => buildIndex(unref(menusRef) || []))

  return {
    // Menu serupa untuk satu menu (modal detail).
    similarMenus: (menuId, limit = 3) => similarTo(index.value, menuId, { limit }),
    // Rekomendasi dari isi keranjang: 2 mirip + 1 lintas kategori (limit 3).
    cartSuggestions: (menuIds, limit = 3) => forCart(index.value, menuIds, { limit, crossSlots: 1 }),
  }
}
