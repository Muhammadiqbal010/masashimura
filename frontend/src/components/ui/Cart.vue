<template>
  <div class="fixed inset-0 z-[60] flex justify-end" role="dialog" aria-modal="true" aria-label="Keranjang">

    <!-- Overlay -->
    <div
      class="absolute inset-0 bg-black/75 backdrop-blur-md"
      @click="$emit('close')"
    />

    <!-- Panel -->
    <div class="drawer relative flex h-full w-full max-w-md flex-col border-l border-white/[0.08] sm:rounded-l-[2rem]">

      <!-- HEADER -->
      <div class="flex items-center justify-between border-b border-white/[0.07] px-6 py-5">
        <div class="flex items-center gap-3">
          <h2 class="font-sora text-xl font-semibold tracking-tight text-[#F5F0EA]">Keranjang</h2>
          <span
            v-if="!cartStore.isEmpty"
            class="rounded-full border border-[#D4B483]/25 bg-[#D4B483]/10 px-2.5 py-0.5 text-xs font-semibold tabular-nums text-[#D4B483]"
          >
            {{ Object.values(cartStore.cart).length }} item
          </span>
        </div>
        <button
          type="button"
          aria-label="Tutup keranjang"
          @click="$emit('close')"
          class="flex h-10 w-10 items-center justify-center rounded-full text-[#A39A93] transition-all duration-150 hover:bg-white/5 hover:text-[#F5F0EA]"
        >
          <X :size="18" />
        </button>
      </div>

      <!-- LIST ITEMS -->
      <div class="flex-1 space-y-3 overflow-y-auto px-5 py-5 sm:px-6">

        <!-- Empty state -->
        <div v-if="cartStore.isEmpty" class="flex h-full flex-col items-center justify-center gap-4 py-24">
          <div class="flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-[#141211]">
            <ShoppingCart :size="22" class="text-[#A39A93]" />
          </div>
          <div class="space-y-1 text-center">
            <p class="font-sora text-lg font-semibold text-[#F5F0EA]">Keranjang kosong</p>
            <p class="text-sm text-[#A39A93]">Tambahkan menu dulu yuk.</p>
          </div>
          <router-link
            to="/menu"
            @click="$emit('close')"
            class="mt-2 inline-flex items-center justify-center rounded-full bg-[#D7263D] px-7 py-3 text-sm font-semibold text-white transition-all duration-150 hover:bg-[#B91C32]"
          >
            Lihat menu
          </router-link>
        </div>

        <!-- Items -->
        <template v-else>
          <div
            v-for="item in Object.values(cartStore.cart)"
            :key="item.cartKey"
            class="item-card group flex gap-4"
          >
            <!-- Thumbnail -->
            <div class="h-[72px] w-[72px] flex-shrink-0 overflow-hidden rounded-2xl border border-white/[0.07] bg-[#1A1716]">
              <img
                v-if="item.image_url"
                :src="getMediaUrl(item.image_url, 160)"
                class="pointer-events-none h-full w-full object-cover"
                :alt="item.name"
                loading="lazy"
              />
              <div v-else class="flex h-full w-full items-center justify-center">
                <span class="text-lg opacity-30">🍜</span>
              </div>
            </div>

            <!-- Detail -->
            <div class="flex min-w-0 flex-1 flex-col gap-2.5">
              <div class="flex items-start justify-between gap-2">
                <h4 class="line-clamp-2 flex-1 font-sora text-[15px] font-semibold leading-snug text-[#F5F0EA]">
                  {{ item.name }}
                </h4>
                <button
                  type="button"
                  :aria-label="'Hapus ' + item.name + ' dari keranjang'"
                  @click="cartStore.removeFromCart(item.cartKey)"
                  class="-mr-2 -mt-1.5 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full text-[#6F6761] transition-colors hover:bg-[#D7263D]/10 hover:text-[#F2707A]"
                >
                  <X :size="16" />
                </button>
              </div>

              <!-- Pilihan opsi (pedas, add-on, dll) -->
              <div v-if="item.optionDetails?.length" class="flex flex-wrap gap-1.5">
                <span
                  v-for="opt in item.optionDetails"
                  :key="opt.group + opt.label"
                  class="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-0.5 text-xs font-medium text-[#C9C1B9]"
                >
                  {{ opt.label }}<template v-if="opt.price"> +{{ formatPrice(opt.price) }}</template>
                </span>
              </div>

              <!-- Catatan -->
              <input
                v-model="item.notes"
                type="text"
                :aria-label="'Catatan untuk ' + item.name"
                placeholder="Catatan (contoh: tanpa sayur)"
                class="note-input"
              />

              <!-- Qty + subtotal -->
              <div class="flex items-center justify-between gap-3">
                <div class="flex items-center rounded-full border border-white/10 bg-white/[0.03] p-1">
                  <button
                    type="button"
                    :aria-label="'Kurangi ' + item.name"
                    @click="cartStore.updateQuantity(item.cartKey, -1)"
                    class="flex h-8 w-8 items-center justify-center rounded-full text-[#F5F0EA] transition-colors hover:bg-white/10"
                  >
                    <Minus :size="14" />
                  </button>
                  <span class="min-w-[1.75rem] text-center text-sm font-semibold tabular-nums text-[#F5F0EA]">
                    {{ item.quantity }}
                  </span>
                  <button
                    type="button"
                    :aria-label="'Tambah ' + item.name"
                    @click="cartStore.updateQuantity(item.cartKey, 1)"
                    class="flex h-8 w-8 items-center justify-center rounded-full bg-[#D7263D] text-white transition-colors hover:bg-[#B91C32]"
                  >
                    <Plus :size="14" />
                  </button>
                </div>

                <span class="font-sora text-base font-semibold tracking-tight text-[#F5F0EA]">
                  {{ formatPrice(item.price * item.quantity) }}
                </span>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- FOOTER TOTAL + CTA -->
      <div v-if="!cartStore.isEmpty" class="footer-safe border-t border-white/[0.07] bg-black/25 px-6 pt-5">
        <!-- Total row -->
        <div class="mb-5 flex items-end justify-between gap-4">
          <div class="space-y-1">
            <p class="text-sm text-[#A39A93]">Total</p>
            <span class="block font-sora text-3xl font-semibold leading-none tracking-tight text-[#F5F0EA]">
              {{ formatPrice(cartStore.totalPrice) }}
            </span>
          </div>
          <div class="space-y-1 text-right">
            <p class="text-sm text-[#A39A93]">Jumlah</p>
            <span class="block text-base font-semibold tabular-nums text-[#F5F0EA]">
              {{ cartStore.cartItemCount }} porsi
            </span>
          </div>
        </div>

        <!-- Toko tutup: beri tahu di sini, jangan sampai customer baru tahu di halaman checkout -->
        <div
          v-if="settingsReady && !isStoreOpen"
          class="mb-4 flex items-start gap-3 rounded-2xl border border-[#D7263D]/25 bg-[#D7263D]/10 px-4 py-3.5"
          role="status"
        >
          <Lock :size="16" class="mt-0.5 flex-shrink-0 text-[#F2707A]" />
          <p class="text-sm leading-relaxed text-[#F6B4BA]">
            Toko sedang tutup, pesanan belum bisa dibuat.
            <span v-if="nextOpenText" class="mt-0.5 block font-semibold text-[#FBD5D8]">{{ nextOpenText }}</span>
          </p>
        </div>

        <!-- CTA -->
        <router-link
          v-if="isStoreOpen"
          to="/checkout"
          @click="$emit('close')"
          class="flex min-h-[56px] w-full items-center justify-center gap-2 rounded-full bg-[#D7263D] text-base font-semibold text-white transition-all duration-200 hover:bg-[#B91C32] hover:shadow-[0_8px_24px_-8px_rgba(215,38,61,0.6)] active:scale-[0.98]"
        >
          <span>Pesan sekarang</span>
          <ArrowRight :size="18" />
        </router-link>
        <button
          v-else
          type="button"
          disabled
          class="flex min-h-[56px] w-full cursor-not-allowed items-center justify-center gap-2 rounded-full border border-white/5 bg-[#1A1716] text-base font-semibold text-[#6F6761]"
        >
          <span>Toko tutup</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from "vue"
import { useCartStore } from "@/stores/cart"
import { getMediaUrl } from "@/api"
import { useStoreSettings } from "@/composables/useStoreSettings"
import { X, ShoppingCart, ArrowRight, Lock, Plus, Minus } from "lucide-vue-next"

const cartStore = useCartStore()
const { isStoreOpen, settingsReady, nextOpenText, fetchSettings } = useStoreSettings()

onMounted(() => fetchSettings())

defineProps({ formatPrice: Function })
defineEmits(["close"])
</script>

<style scoped>
/* Palet: Surface #141211 · Washi #F5F0EA · Crimson #D7263D · Champagne #D4B483 */

.drawer {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.035), rgba(255, 255, 255, 0.008)), #0F0D0C;
  box-shadow: -40px 0 80px -20px rgba(0, 0, 0, 0.6);
}

.item-card {
  border-radius: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.07);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.01)), #141211;
  padding: 1rem;
}

/* 16px di HP supaya iOS tidak zoom otomatis */
.note-input {
  width: 100%;
  height: 2.5rem;
  border-radius: 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: #0F0D0C;
  padding: 0 0.875rem;
  font-size: 1rem;
  color: #C9C1B9;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
@media (min-width: 640px) {
  .note-input { font-size: 0.8125rem; }
}
.note-input::placeholder { color: #6F6761; }
.note-input:hover { border-color: rgba(255, 255, 255, 0.18); }
.note-input:focus {
  border-color: rgba(212, 180, 131, 0.6);
  box-shadow: 0 0 0 3px rgba(212, 180, 131, 0.12);
}

/* Footer aman dari home-indicator di HP */
.footer-safe { padding-bottom: calc(1.25rem + env(safe-area-inset-bottom, 0px)); }

a:focus-visible,
button:focus-visible {
  outline: 2px solid #D4B483;
  outline-offset: 3px;
}

::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.14); }
</style>