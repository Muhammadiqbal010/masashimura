<template>
  <div class="fixed inset-0 z-[60] flex justify-end">

    <!-- Overlay -->
    <div
      class="absolute inset-0 bg-black/70 backdrop-blur-[2px]"
      @click="$emit('close')"
    />

    <!-- Panel -->
    <div class="relative w-full max-w-sm sm:max-w-md bg-[#080808] h-full flex flex-col border-l border-white/[0.06]">

      <!-- HEADER -->
      <div class="flex items-center justify-between px-6 py-5 border-b border-white/[0.06]">
        <div class="flex items-center gap-2.5">
          <span class="w-3 h-px bg-[#DC2626]"></span>
          <span class="font-mono text-[9px] tracking-[0.3em] text-[#DC2626] uppercase">Keranjang</span>
        </div>
        <button
          @click="$emit('close')"
          class="w-8 h-8 flex items-center justify-center rounded-lg text-zinc-600 hover:text-white hover:bg-white/5 transition-all duration-150"
        >
          <X :size="16" />
        </button>
      </div>

      <!-- ITEM COUNT PILL -->
      <div v-if="!cartStore.isEmpty" class="px-6 pt-4">
        <span class="font-mono text-[9px] tracking-[0.2em] text-zinc-700 uppercase">
          {{ Object.values(cartStore.cart).length }} item
        </span>
      </div>

      <!-- LIST ITEMS -->
      <div class="flex-1 overflow-y-auto px-6 py-4 space-y-px">

        <!-- Empty state -->
        <div v-if="cartStore.isEmpty" class="flex flex-col items-center justify-center h-full gap-4 py-24">
          <div class="w-12 h-12 rounded-2xl bg-[#111] border border-white/5 flex items-center justify-center">
            <ShoppingCart :size="20" class="text-zinc-700" />
          </div>
          <div class="text-center space-y-1">
            <p class="font-sora text-[11px] font-bold uppercase tracking-widest text-zinc-600">Keranjang kosong</p>
            <p class="text-[11px] text-zinc-700 font-light">Tambahkan menu dulu yuk.</p>
          </div>
          <router-link
            to="/menu"
            @click="$emit('close')"
            class="mt-2 font-mono text-[10px] tracking-widest text-[#DC2626] uppercase border border-[#DC2626]/30 hover:border-[#DC2626]/60 px-4 py-2 rounded-lg transition-all duration-150"
          >
            Lihat Menu
          </router-link>
        </div>

        <!-- Items -->
        <div
          v-else
          v-for="item in Object.values(cartStore.cart)"
          :key="item.cartKey"
          class="group flex gap-4 py-4 border-b border-white/[0.04] last:border-0"
        >
          <!-- Thumbnail -->
          <div class="w-16 h-16 sm:w-[72px] sm:h-[72px] rounded-xl overflow-hidden bg-[#111] border border-white/[0.06] flex-shrink-0">
            <img
              v-if="item.image_url"
              :src="getMediaUrl(item.image_url)"
              class="w-full h-full object-cover pointer-events-none"
              :alt="item.name"
            />
            <div v-else class="w-full h-full flex items-center justify-center">
              <span class="text-zinc-800 text-lg">🍜</span>
            </div>
          </div>

          <!-- Detail -->
          <div class="flex-1 min-w-0 flex flex-col gap-2">
            <div class="flex items-start justify-between gap-2">
              <h4 class="font-sora text-[12px] font-bold uppercase tracking-wide text-white leading-tight truncate flex-1">
                {{ item.name }}
              </h4>
              <button
                @click="cartStore.removeFromCart(item.cartKey)"
                class="flex-shrink-0 text-zinc-800 hover:text-red-500 transition-colors p-0.5 -mt-0.5"
              >
                <X :size="13" />
              </button>
            </div>

            <!-- Harga per item × qty -->
            <span class="font-mono text-[12px] font-bold text-amber-400 leading-none">
              {{ formatPrice(item.price_web * item.quantity) }}
            </span>

            <!-- Catatan -->
            <input
              v-model="item.notes"
              type="text"
              placeholder="Catatan (contoh: pedas sedang)"
              class="w-full bg-white/[0.03] border border-white/[0.06] hover:border-white/10 focus:border-[#DC2626]/50 rounded-lg py-1.5 px-3 text-[11px] font-mono text-zinc-400 placeholder:text-zinc-700 outline-none transition-colors duration-150"
            />

            <!-- Qty control -->
            <div class="flex items-center gap-2 mt-0.5">
              <button
                @click="cartStore.updateQuantity(item.cartKey, -1)"
                class="w-7 h-7 flex items-center justify-center border border-white/[0.08] rounded-lg text-zinc-500 hover:text-white hover:border-white/20 transition-all duration-150 font-light text-base leading-none"
              >
                −
              </button>
              <span class="font-mono text-[13px] font-bold text-white w-5 text-center">
                {{ item.quantity }}
              </span>
              <button
                @click="cartStore.updateQuantity(item.cartKey, 1)"
                class="w-7 h-7 flex items-center justify-center border border-white/[0.08] rounded-lg text-zinc-500 hover:text-white hover:border-white/20 transition-all duration-150 font-light text-base leading-none"
              >
                +
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- FOOTER TOTAL + CTA -->
      <div v-if="!cartStore.isEmpty" class="px-6 pb-6 pt-4 border-t border-white/[0.06] bg-[#050505]">
        <!-- Total row -->
        <div class="flex items-center justify-between mb-5">
          <div class="space-y-0.5">
            <p class="font-mono text-[9px] tracking-[0.2em] text-zinc-700 uppercase">Total</p>
            <span class="font-mono text-xl font-bold text-amber-400 tracking-tight leading-none">
              {{ formatPrice(cartStore.totalPrice) }}
            </span>
          </div>
          <div class="text-right space-y-0.5">
            <p class="font-mono text-[9px] tracking-[0.2em] text-zinc-700 uppercase">Item</p>
            <span class="font-mono text-[13px] font-bold text-white">
              {{ cartStore.cartItemCount }}x
            </span>
          </div>
        </div>

        <!-- CTA -->
        <router-link
          to="/checkout"
          @click="$emit('close')"
          class="flex items-center justify-center gap-2 w-full bg-[#DC2626] hover:bg-red-700 active:scale-[0.98] text-white font-sora text-[11px] font-bold uppercase tracking-widest py-4 rounded-xl transition-all duration-200"
        >
          <span>Pesan Sekarang</span>
          <ArrowRight :size="14" />
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useCartStore } from "@/stores/cart"
import { getMediaUrl } from "@/api"
import { X, ShoppingCart, ArrowRight } from "lucide-vue-next"

const cartStore = useCartStore()

defineProps({ formatPrice: Function })
defineEmits(["close"])
</script>

<style scoped>
::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.06); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.1); }
</style>