<template>
  <Teleport to="body">
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        class="fixed inset-0 z-[60] flex items-end justify-center bg-black/75 backdrop-blur-md sm:items-center sm:p-6"
        role="dialog"
        aria-modal="true"
        :aria-label="'Detail ' + menu.name"
        @click.self="$emit('close')"
      >
        <transition
          appear
          enter-active-class="transition duration-300 ease-out"
          enter-from-class="opacity-0 translate-y-6 sm:scale-95"
          enter-to-class="opacity-100 translate-y-0 sm:scale-100"
        >
          <div class="modal-sheet flex max-h-[92vh] w-full flex-col overflow-hidden rounded-t-[2rem] border border-white/[0.08] sm:max-w-lg sm:rounded-[2rem]">

            <!-- Foto (16:9, sama dengan hasil crop di admin) -->
            <div class="relative aspect-video w-full flex-shrink-0 bg-[#232327]">
              <img
                v-if="menu.image_url"
                :src="getMediaUrl(menu.image_url, 900)"
                :alt="menu.name"
                class="h-full w-full object-cover"
              />
              <div v-else class="flex h-full w-full flex-col items-center justify-center gap-2">
                <span class="text-4xl opacity-25">🍜</span>
                <span class="text-xs text-[#9A9AA3]">Belum ada foto</span>
              </div>

              <div class="pointer-events-none absolute inset-0 bg-gradient-to-t from-[#1C1C1F] via-transparent to-black/30"></div>

              <!-- Aksi kanan atas: favorit, bagikan, tutup -->
              <div class="absolute right-3 top-3 z-10 flex items-center gap-2">
                <button
                  type="button"
                  :aria-pressed="isFavorite"
                  :aria-label="isFavorite ? 'Hapus dari favorit' : 'Simpan ke favorit'"
                  class="icon-btn"
                  @click="$emit('toggle-favorite', menu.id)"
                >
                  <Heart :size="16" :class="isFavorite ? 'fill-[#D92B22] text-[#D92B22]' : 'text-white'" />
                </button>
                <button
                  type="button"
                  aria-label="Bagikan lewat WhatsApp"
                  class="icon-btn text-white"
                  @click="$emit('share', menu)"
                >
                  <Share2 :size="16" />
                </button>
                <button
                  type="button"
                  aria-label="Tutup"
                  class="icon-btn text-white"
                  @click="$emit('close')"
                >
                  <X :size="16" />
                </button>
              </div>

              <!-- Badge kiri atas -->
              <div class="absolute left-3 top-3 z-10 flex flex-col items-start gap-1.5">
                <div
                  v-if="!menu.is_available"
                  class="rounded-full border border-white/10 bg-black/70 px-2.5 py-1 backdrop-blur-md"
                >
                  <span class="text-[11px] font-semibold text-[#FAFAFA]">Habis</span>
                </div>
                <div v-if="menu.is_recommended" class="flex items-center gap-1.5 rounded-full bg-[#D92B22] px-2.5 py-1 text-white">
                  <ThumbsUp :size="11" />
                  <span class="text-[11px] font-semibold">Rekomendasi</span>
                </div>
                <div v-if="isBestSeller" class="flex items-center gap-1.5 rounded-full bg-[#F4C542] px-2.5 py-1 text-[#2A1F00]">
                  <Flame :size="11" />
                  <span class="text-[11px] font-semibold">Terlaris</span>
                </div>
              </div>
            </div>

            <!-- Info -->
            <div ref="scrollEl" class="modal-body flex min-h-0 flex-1 flex-col gap-5 overflow-y-auto px-6 pb-2 pt-4 sm:px-7">
              <div class="space-y-2.5">
                <span class="block text-xs font-medium text-[#F4C542]">
                  {{ menu.category_name }}
                </span>
                <h2 class="font-sora text-2xl font-semibold leading-tight tracking-tight text-[#FAFAFA]">
                  {{ menu.name }}
                </h2>
                <p class="text-sm leading-relaxed text-[#B8B8C0]">
                  {{ menu.description || "Menu andalan spesial Masashimura." }}
                </p>
              </div>

              <!-- Ringkasan opsi yang bisa dipilih -->
              <div v-if="menu.options?.length" class="space-y-2">
                <span class="block text-xs font-medium text-[#9A9AA3]">Pilihan yang tersedia</span>
                <div class="flex flex-wrap items-center gap-2">
                  <span
                    v-for="group in menu.options"
                    :key="group.name"
                    class="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs font-medium text-[#C8C8C8]"
                  >
                    {{ group.name }}<span v-if="group.required" class="text-[#F0605A]" title="Wajib dipilih"> *</span>
                  </span>
                </div>
              </div>

              <!-- Rekomendasi: menu serupa (content-based filtering) -->
              <MenuRecommendations
                :items="recommendations"
                title="Menu serupa"
                subtitle="Dari nama, kategori, dan deskripsi menu"
                variant="cards"
                :format-price="formatPrice"
                :can-add="isStoreOpen"
                show-reason
                @select="$emit('open-menu', $event)"
                @add="$emit('add-to-cart', $event)"
              />
            </div>

            <!-- Footer: harga + aksi -->
            <div class="footer-safe flex flex-shrink-0 items-center justify-between gap-4 border-t border-white/[0.07] bg-black/20 px-6 pt-4 sm:px-7">
              <div class="min-w-0">
                <span class="block text-xs text-[#9A9AA3]">Harga</span>
                <span class="block font-sora text-2xl font-semibold leading-none tracking-tight text-[#FAFAFA]">
                  {{ formatPrice(menu.price_web) }}
                </span>
              </div>

              <button
                type="button"
                @click="handleAdd"
                :disabled="!menu.is_available || !isStoreOpen"
                :class="[
                  'flex min-h-[48px] flex-shrink-0 items-center gap-2 rounded-full px-6 text-sm font-semibold transition-all duration-200',
                  menu.is_available && isStoreOpen
                    ? 'bg-[#D92B22] text-white hover:bg-[#B8201A] hover:shadow-[0_8px_24px_-8px_rgba(217,43,34,0.6)] active:scale-95'
                    : 'cursor-not-allowed border border-white/5 bg-[#232327] text-[#9A9AA3]'
                ]"
              >
                <Plus :size="16" />
                {{ menu.options?.length ? "Pilih & tambah" : "Tambah" }}
              </button>
            </div>
          </div>
        </transition>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, watch } from "vue"
import { Plus, X, ThumbsUp, Flame, Heart, Share2 } from "lucide-vue-next"
import { getMediaUrl } from "@/api"
import MenuRecommendations from "@/components/ui/MenuRecommendations.vue"

const props = defineProps({
  menu: { type: Object, required: true },
  formatPrice: { type: Function, required: true },
  isStoreOpen: { type: Boolean, default: true },
  isBestSeller: { type: Boolean, default: false },
  isFavorite: { type: Boolean, default: false },
  // [{ menu, score, reason }] dari useRecommender().similarMenus
  recommendations: { type: Array, default: () => [] },
})

const emit = defineEmits(["close", "add-to-cart", "share", "toggle-favorite", "open-menu"])

// Saat pindah ke menu serupa, konten modal yang sama dipakai ulang: kembalikan scroll ke atas.
const scrollEl = ref(null)
watch(
  () => props.menu.id,
  () => scrollEl.value?.scrollTo({ top: 0 })
)

// Menu beropsi: Menu.vue yang membuka picker; di sini cukup meneruskan menunya.
const handleAdd = () => {
  emit("add-to-cart", props.menu)
}
</script>

<style scoped>
/* Lebar bleed = padding kiri/kanan area scroll, supaya kartu rekomendasi geser sampai tepi sheet di HP */
.modal-body { --rec-bleed: 1.5rem; }
@media (min-width: 640px) { .modal-body { --rec-bleed: 1.75rem; } }

/* Palet: Surface #1C1C1F · Washi #FAFAFA · Crimson #D92B22 · Champagne #F4C542 */

.modal-sheet {
  background: #1C1C1F;
  box-shadow: 0 40px 80px -20px rgba(0, 0, 0, 0.7);
}

.icon-btn {
  display: flex;
  height: 2.5rem;
  width: 2.5rem;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(12px);
  transition: background-color 0.2s ease;
}
.icon-btn:hover {
  background: rgba(0, 0, 0, 0.8);
}

/* Footer aman dari home-indicator di HP */
.footer-safe {
  padding-bottom: calc(1rem + env(safe-area-inset-bottom, 0px));
}

button:focus-visible {
  outline: 2px solid #F4C542;
  outline-offset: 3px;
}
</style>