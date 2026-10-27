<template>
  <div class="fixed inset-0 z-[60] flex justify-end" role="dialog" aria-modal="true" aria-label="Keranjang">

    <!-- Overlay -->
    <div
      class="absolute inset-0 bg-black/75 backdrop-blur-md"
      @click="$emit('close')"
    />

    <!-- Panel -->
    <div class="drawer relative flex h-full w-full max-w-md flex-col sm:rounded-l-[2rem]">

      <!-- HEADER -->
      <div class="flex items-center justify-between border-b-2 border-[#111113] bg-white px-6 py-5">
        <div class="flex items-center gap-3">
          <span class="hanko" aria-hidden="true">買</span>
          <h2 class="font-sora text-xl text-[#111113]">Keranjang</h2>
          <span
            v-if="!cartStore.isEmpty"
            class="sticker !rotate-0 !shadow-none tabular-nums"
          >
            {{ Object.values(cartStore.cart).length + cartStore.bundleLines.length }} item
          </span>
        </div>
        <button
          type="button"
          aria-label="Tutup keranjang"
          @click="$emit('close')"
          class="flex h-10 w-10 items-center justify-center rounded-full text-[#55555D] transition-all duration-150 hover:bg-[#111113]/5 hover:text-[#111113]"
        >
          <X :size="18" />
        </button>
      </div>

      <!-- LIST ITEMS -->
      <div class="flex-1 space-y-3 overflow-y-auto px-5 py-5 sm:px-6">

        <!-- Empty state -->
        <div v-if="cartStore.isEmpty" class="flex h-full flex-col items-center justify-center gap-4 py-24">
          <div class="flex h-14 w-14 items-center justify-center rounded-2xl border border-[#111113]/15 bg-white">
            <ShoppingCart :size="22" class="text-[#55555D]" />
          </div>
          <div class="space-y-1 text-center">
            <p class="font-sora text-lg font-semibold text-[#111113]">Keranjang kosong</p>
            <p class="text-sm text-[#55555D]">Tambahkan menu dulu yuk.</p>
          </div>
          <router-link
            to="/menu"
            @click="$emit('close')"
            class="pop-btn mt-2"
          >
            Lihat menu
          </router-link>
        </div>

        <!-- Items -->
        <template v-else>
          <!-- Paket -->
          <div
            v-for="line in cartStore.bundleLines"
            :key="line.cartKey"
            class="item-card group flex flex-col gap-2.5"
          >
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0 flex-1">
                <p class="text-[11px] font-semibold uppercase tracking-wider text-[#B8201A]">Paket</p>
                <h4 class="line-clamp-2 font-sora text-[15px] font-semibold leading-snug text-[#111113]">{{ line.name }}</h4>
              </div>
              <button
                type="button"
                :aria-label="'Hapus ' + line.name + ' dari keranjang'"
                @click="cartStore.removeBundle(line.id)"
                class="-mr-2 -mt-1.5 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full text-[#6B6B73] transition-colors hover:bg-[#D92B22]/10 hover:text-[#B8201A]"
              >
                <X :size="16" />
              </button>
            </div>
            <p class="text-xs text-[#55555D]">{{ line.contents.map((c) => c.quantity + '× ' + c.name).join(' · ') }}</p>
            <p v-if="line.savings > 0" class="text-xs font-semibold text-[#B8201A]">Hemat {{ formatPrice(line.savings * line.quantity) }}</p>
            <div class="flex items-center justify-between gap-3">
              <div class="flex items-center rounded-full border border-[#111113]/15 bg-[#111113]/[0.03] p-1">
                <button type="button" :aria-label="'Kurangi ' + line.name" @click="cartStore.updateBundleQuantity(line.id, -1)"
                  class="flex h-8 w-8 items-center justify-center rounded-full text-[#111113] transition-colors hover:bg-[#111113]/10"><Minus :size="14" /></button>
                <span class="min-w-[1.75rem] text-center text-sm font-semibold tabular-nums text-[#111113]">{{ line.quantity }}</span>
                <button type="button" :aria-label="'Tambah ' + line.name" @click="cartStore.updateBundleQuantity(line.id, 1)"
                  class="flex h-8 w-8 items-center justify-center rounded-full bg-[#D92B22] text-outline text-white transition-colors hover:bg-[#B8201A]"><Plus :size="14" /></button>
              </div>
              <span class="font-sora text-base font-semibold tracking-tight text-[#111113]">{{ formatPrice(line.price * line.quantity) }}</span>
            </div>
          </div>

          <div
            v-for="item in Object.values(cartStore.cart)"
            :key="item.cartKey"
            class="item-card group flex gap-4"
          >
            <!-- Thumbnail -->
            <div class="h-[72px] w-[72px] flex-shrink-0 overflow-hidden rounded-2xl border border-[#111113]/10 bg-[#EFEBE2]">
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
                <h4 class="line-clamp-2 flex-1 font-sora text-[15px] font-semibold leading-snug text-[#111113]">
                  {{ item.name }}
                </h4>
                <button
                  type="button"
                  :aria-label="'Hapus ' + item.name + ' dari keranjang'"
                  @click="cartStore.removeFromCart(item.cartKey)"
                  class="-mr-2 -mt-1.5 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full text-[#6B6B73] transition-colors hover:bg-[#D92B22]/10 hover:text-[#B8201A]"
                >
                  <X :size="16" />
                </button>
              </div>

              <!-- Pilihan opsi (pedas, add-on, dll) -->
              <div v-if="item.optionDetails?.length" class="flex flex-wrap gap-1.5">
                <span
                  v-for="opt in item.optionDetails"
                  :key="opt.group + opt.label"
                  class="rounded-full border border-[#111113]/15 bg-[#111113]/[0.04] px-2.5 py-0.5 text-xs font-medium text-[#3F3F46]"
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
                <div class="flex items-center rounded-full border border-[#111113]/15 bg-[#111113]/[0.03] p-1">
                  <button
                    type="button"
                    :aria-label="'Kurangi ' + item.name"
                    @click="cartStore.updateQuantity(item.cartKey, -1)"
                    class="flex h-8 w-8 items-center justify-center rounded-full text-[#111113] transition-colors hover:bg-[#111113]/10"
                  >
                    <Minus :size="14" />
                  </button>
                  <span class="min-w-[1.75rem] text-center text-sm font-semibold tabular-nums text-[#111113]">
                    {{ item.quantity }}
                  </span>
                  <button
                    type="button"
                    :aria-label="'Tambah ' + item.name"
                    @click="cartStore.updateQuantity(item.cartKey, 1)"
                    :disabled="!cartStore.canAddMore(item.id)"
                    :title="cartStore.canAddMore(item.id) ? '' : 'Batas porsi tercapai. Untuk jumlah besar, hubungi kasir.'"
                    class="flex h-8 w-8 items-center justify-center rounded-full bg-[#D92B22] text-outline text-white transition-colors hover:bg-[#B8201A] disabled:cursor-not-allowed disabled:opacity-35"
                  >
                    <Plus :size="14" />
                  </button>
                </div>

                <span class="font-sora text-base font-semibold tracking-tight text-[#111113]">
                  {{ formatPrice(item.price * item.quantity) }}
                </span>
              </div>
            </div>
          </div>

          <!-- Rekomendasi dari isi keranjang (content-based filtering) -->
          <MenuRecommendations
            :items="recommendations"
            title="Mungkin kamu suka"
            subtitle="Berdasarkan isi keranjang"
            variant="list"
            :format-price="formatPrice"
            :can-add="isStoreOpen"
            class="mt-1"
            @select="$emit('view', $event)"
            @add="$emit('add', $event)"
          />
        </template>
      </div>

      <!-- FOOTER TOTAL + CTA -->
      <div v-if="!cartStore.isEmpty" class="footer-safe border-t-2 border-[#111113] bg-white px-6 pt-5">
        <!-- Total row -->
        <div class="mb-5 flex items-end justify-between gap-4">
          <div class="space-y-1">
            <p class="text-sm text-[#55555D]">Total</p>
            <span class="block font-[family-name:var(--font-display)] text-3xl leading-none text-[#D92B22]">
              {{ formatPrice(cartStore.totalPrice) }}
            </span>
          </div>
          <div class="space-y-1 text-right">
            <p class="text-sm text-[#55555D]">Jumlah</p>
            <span class="block text-base font-semibold tabular-nums text-[#111113]">
              {{ cartStore.cartItemCount }} porsi
            </span>
          </div>
        </div>

        <!-- Toko tutup: beri tahu di sini, jangan sampai customer baru tahu di halaman checkout -->
        <div
          v-if="settingsReady && !isStoreOpen"
          class="mb-4 flex items-start gap-3 rounded-2xl border border-[#D92B22]/25 bg-[#D92B22]/10 px-4 py-3.5"
          role="status"
        >
          <Lock :size="16" class="mt-0.5 flex-shrink-0 text-[#D92B22]" />
          <p class="text-sm leading-relaxed text-[#8F1511]">
            Toko sedang tutup, pesanan belum bisa dibuat.
            <span v-if="nextOpenText" class="mt-0.5 block font-semibold text-[#8F1511]">{{ nextOpenText }}</span>
          </p>
        </div>

        <!-- CTA -->
        <button
          v-if="isStoreOpen"
          type="button"
          :disabled="navigating"
          class="cta-btn pop-btn !min-h-[58px] w-full !text-base disabled:opacity-70"
          @click="goCheckout"
        >
          <span v-if="navigating" class="h-5 w-5 animate-spin rounded-full border-2 border-[#111113]/30 border-t-white" aria-hidden="true"></span>
          <template v-else>
            <span>Pesan sekarang</span>
            <span class="pop-btn-dot" aria-hidden="true"><ArrowRight :size="15" /></span>
          </template>
        </button>
        <button
          v-else
          type="button"
          disabled
          class="flex min-h-[56px] w-full cursor-not-allowed items-center justify-center gap-2 rounded-full border border-[#111113]/10 bg-[#EFEBE2] text-base font-semibold text-[#6B6B73]"
        >
          <span>Toko tutup</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"
import { useCartStore } from "@/stores/cart"
import { getMediaUrl } from "@/api"
import { useStoreSettings } from "@/composables/useStoreSettings"
import { X, ShoppingCart, ArrowRight, Lock, Plus, Minus } from "lucide-vue-next"
import MenuRecommendations from "@/components/ui/MenuRecommendations.vue"

const router = useRouter()
const cartStore = useCartStore()
const { isStoreOpen, settingsReady, nextOpenText, fetchSettings } = useStoreSettings()

onMounted(() => fetchSettings())

defineProps({
  formatPrice: Function,
  // [{ menu, score, reason }] dari useRecommender().cartSuggestions
  recommendations: { type: Array, default: () => [] },
})
const emit = defineEmits(["close", "add", "view"])

// Pindah ke checkout secara programatik (bukan lewat <router-link> + emit close).
// Sebelumnya drawer langsung dibongkar saat diklik, sehingga kalau chunk halaman checkout
// gagal dimuat (mis. setelah deploy baru di Vercel) navigasi macet tanpa pesan apa pun.
const navigating = ref(false)
const goCheckout = async () => {
  if (navigating.value) return
  navigating.value = true
  try {
    await router.push("/checkout")
    emit("close")
  } catch {
    // Fallback keras: muat ulang langsung ke /checkout
    window.location.assign("/checkout")
  } finally {
    navigating.value = false
  }
}
</script>

<style scoped>
/* Palet: Surface #FFFFFF · Washi #111113 · Crimson #D92B22 · Champagne #F4C542 */

.drawer {
  background: #F7F5F0;
  border-left: 3px solid #111113;
  box-shadow: -40px 0 80px -20px rgba(0, 0, 0, 0.45);
}

.item-card {
  border-radius: 1.25rem;
  border: 2px solid #111113;
  box-shadow: 4px 4px 0 #111113;
  background: #FFFFFF;
  padding: 1rem;
}

/* 16px di HP supaya iOS tidak zoom otomatis */
.note-input {
  width: 100%;
  height: 2.5rem;
  border-radius: 0.75rem;
  border: 2px solid rgba(17, 17, 19, 0.25);
  background: #F7F5F0;
  padding: 0 0.875rem;
  font-size: 1rem;
  color: #3F3F46;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
@media (min-width: 640px) {
  .note-input { font-size: 0.8125rem; }
}
.note-input::placeholder { color: #6B6B73; }
.note-input:hover { border-color: rgba(17, 17, 19, 0.5); }
.note-input:focus {
  border-color: #111113;
  box-shadow: 0 0 0 3px rgba(244,197,66, 0.55);
}

/* Footer aman dari home-indicator di HP */
.footer-safe { padding-bottom: calc(1.25rem + env(safe-area-inset-bottom, 0px)); }

a:focus-visible,
button:focus-visible {
  outline: 2px solid #111113;
  outline-offset: 3px;
}

::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(17, 17, 19, 0.08); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: rgba(17, 17, 19, 0.14); }
</style>