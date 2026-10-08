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
        class="fixed inset-0 z-[60] bg-black/70 backdrop-blur-sm flex items-end sm:items-center justify-center"
        @click.self="$emit('close')"
      >
        <transition
          appear
          enter-active-class="transition duration-250 ease-out"
          enter-from-class="opacity-0 translate-y-6 sm:scale-95"
          enter-to-class="opacity-100 translate-y-0 sm:scale-100"
        >
          <div class="w-full sm:max-w-md bg-[#0d0d0d] border border-white/[0.08] rounded-t-3xl sm:rounded-2xl overflow-hidden max-h-[90vh] flex flex-col">

            <!-- Foto -->
            <div class="w-full aspect-[4/3] bg-[#111] relative flex-shrink-0">
              <img
                v-if="menu.image_url"
                :src="getMediaUrl(menu.image_url)"
                :alt="menu.name"
                class="w-full h-full object-cover"
              />
              <div v-else class="w-full h-full flex flex-col items-center justify-center gap-2">
                <span class="text-4xl opacity-20">🍜</span>
                <span class="font-mono text-[9px] uppercase tracking-widest text-zinc-700">No Image</span>
              </div>

              <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent pointer-events-none"></div>

              <!-- Aksi kanan atas: favorit, bagikan, tutup -->
              <div class="absolute top-3 right-3 z-10 flex items-center gap-2">
                <button
                  type="button"
                  :aria-pressed="isFavorite"
                  :aria-label="isFavorite ? 'Hapus dari favorit' : 'Simpan ke favorit'"
                  class="bg-black/60 backdrop-blur-md border border-white/10 rounded-full w-8 h-8 flex items-center justify-center hover:bg-black/80 transition-colors"
                  @click="$emit('toggle-favorite', menu.id)"
                >
                  <Heart :size="15" :class="isFavorite ? 'fill-[#DC2626] text-[#DC2626]' : 'text-white'" />
                </button>
                <button
                  type="button"
                  aria-label="Bagikan lewat WhatsApp"
                  class="bg-black/60 backdrop-blur-md border border-white/10 rounded-full w-8 h-8 flex items-center justify-center text-white hover:bg-black/80 transition-colors"
                  @click="$emit('share', menu)"
                >
                  <Share2 :size="15" />
                </button>
                <button
                  type="button"
                  aria-label="Tutup"
                  class="bg-black/60 backdrop-blur-md border border-white/10 rounded-full w-8 h-8 flex items-center justify-center text-white hover:bg-black/80 transition-colors"
                  @click="$emit('close')"
                >
                  <X :size="15" />
                </button>
              </div>

              <!-- Badge kiri atas -->
              <div class="absolute top-3 left-3 z-10 flex flex-col items-start gap-1.5">
                <div
                  v-if="!menu.is_available"
                  class="bg-black/70 backdrop-blur-md border border-white/10 px-2.5 py-1 rounded-lg"
                >
                  <span class="font-mono text-[9px] font-bold tracking-[0.2em] text-zinc-400 uppercase">Habis</span>
                </div>
                <div v-if="menu.is_recommended" class="flex items-center gap-1.5 bg-[#DC2626] text-white px-2.5 py-1 rounded-lg">
                  <ThumbsUp :size="11" />
                  <span class="font-mono text-[9px] font-bold tracking-[0.15em] uppercase">Rekomendasi</span>
                </div>
                <div v-if="isBestSeller" class="flex items-center gap-1.5 bg-amber-400 text-black px-2.5 py-1 rounded-lg">
                  <Flame :size="11" />
                  <span class="font-mono text-[9px] font-bold tracking-[0.15em] uppercase">Terlaris</span>
                </div>
              </div>

              <div class="absolute bottom-3 left-4">
                <span class="font-mono text-[9px] tracking-[0.15em] uppercase text-white/50">
                  {{ menu.category_name }}
                </span>
              </div>
            </div>

            <!-- Info -->
            <div class="p-6 flex flex-col gap-4 overflow-y-auto">
              <div class="space-y-2">
                <h2 class="font-sora text-lg font-extrabold uppercase tracking-wide text-white leading-tight">
                  {{ menu.name }}
                </h2>
                <p class="text-zinc-500 text-[12px] font-light leading-relaxed">
                  {{ menu.description || "Menu andalan spesial Masashimura." }}
                </p>
              </div>

              <!-- Ringkasan opsi yang bisa dipilih -->
              <div v-if="menu.options?.length" class="flex flex-wrap items-center gap-1.5">
                <span class="font-mono text-[9px] tracking-[0.2em] uppercase text-zinc-600">Pilihan</span>
                <span
                  v-for="group in menu.options"
                  :key="group.name"
                  class="font-mono text-[10px] text-zinc-400 bg-white/[0.04] border border-white/[0.06] rounded-md px-2 py-0.5"
                >
                  {{ group.name }}<span v-if="group.required" class="text-[#DC2626]"> *</span>
                </span>
              </div>

              <div class="flex items-center justify-between gap-3 pt-4 border-t border-white/[0.05]">
                <span class="font-mono text-xl font-bold text-amber-400 tracking-tight leading-none">
                  {{ formatPrice(menu.price_web) }}
                </span>

                <button
                  type="button"
                  @click="handleAdd"
                  :disabled="!menu.is_available || !isStoreOpen"
                  :class="[
                    'flex items-center gap-2 px-5 py-3 rounded-xl text-[11px] font-sora font-bold uppercase tracking-widest transition-all duration-200',
                    menu.is_available && isStoreOpen
                      ? 'bg-[#DC2626] hover:bg-red-700 text-white active:scale-95'
                      : 'bg-[#1a1a1a] text-zinc-700 cursor-not-allowed border border-white/5'
                  ]"
                >
                  <Plus :size="13" />
                  {{ menu.options?.length ? "Pilih & Tambah" : "Tambah" }}
                </button>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { Plus, X, ThumbsUp, Flame, Heart, Share2 } from "lucide-vue-next"
import { getMediaUrl } from "@/api"

const props = defineProps({
  menu: { type: Object, required: true },
  formatPrice: { type: Function, required: true },
  isStoreOpen: { type: Boolean, default: true },
  isBestSeller: { type: Boolean, default: false },
  isFavorite: { type: Boolean, default: false },
})

const emit = defineEmits(["close", "add-to-cart", "share", "toggle-favorite"])

// Menu beropsi: Menu.vue yang membuka picker; di sini cukup meneruskan menunya.
const handleAdd = () => {
  emit("add-to-cart", props.menu)
}
</script>