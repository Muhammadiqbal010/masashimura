<template>
  <div class="page relative min-h-screen bg-[#111113] font-inter text-[#FAFAFA]">
    <!-- Atmosfer latar -->
    <div class="page-glow pointer-events-none absolute inset-x-0 top-0 h-[480px]" aria-hidden="true"></div>

    <!-- ── HEADER ──────────────────────────────────────────────────────────── -->
    <header class="relative mx-auto max-w-7xl px-5 pb-8 pt-28 sm:px-8 sm:pb-10 sm:pt-32 lg:px-10">
      <h1 class="font-sora text-4xl font-semibold leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl">
        Pilih menu
      </h1>
      <p class="mt-4 max-w-md text-base leading-relaxed text-[#B8B8C0] sm:text-lg">
        Rasa dijamin enak, harga ramah di kantong. Fresh tiap hari.
      </p>
      <CrowdBadge class="mt-5" />
    </header>

    <!-- ── STICKY SEARCH + FILTER BAR ─────────────────────────────────────────── -->
    <div class="sticky top-[60px] z-30 bg-[#111113]/80 backdrop-blur-xl sm:top-[68px]">
      <div class="mx-auto max-w-7xl space-y-3 px-5 py-3 sm:px-8 sm:py-4 lg:px-10">

        <!-- Search + Sort -->
        <div class="flex gap-2.5">
          <div class="relative min-w-0 flex-1">
            <Search :size="16" class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[#9A9AA3]" />
            <input
              v-model="searchQuery"
              type="text"
              inputmode="search"
              enterkeyhint="search"
              autocomplete="off"
              placeholder="Cari menu favoritmu"
              aria-label="Cari menu"
              class="h-12 w-full rounded-xl border border-white/10 bg-[#1C1C1F] pl-11 pr-11 text-base text-[#FAFAFA] transition-colors placeholder:text-[#9A9AA3] focus:border-[#F4C542]/60 focus:outline-none sm:text-sm"
            />
            <button
              v-if="searchQuery"
              type="button"
              @click="searchQuery = ''"
              aria-label="Hapus pencarian"
              class="absolute right-1.5 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full text-[#9A9AA3] transition-colors hover:text-[#FAFAFA]"
            >
              <X :size="16" />
            </button>
          </div>

          <div class="relative flex-shrink-0">
            <select
              v-model="sortBy"
              aria-label="Urutkan menu"
              class="h-12 cursor-pointer appearance-none rounded-xl border border-white/10 bg-[#1C1C1F] pl-4 pr-10 text-base font-medium text-[#FAFAFA] transition-colors focus:border-[#F4C542]/60 focus:outline-none sm:text-sm"
            >
              <option value="default">Urutkan</option>
              <option value="price_asc">Termurah</option>
              <option value="price_desc">Termahal</option>
            </select>
            <ChevronDown :size="15" class="pointer-events-none absolute right-3.5 top-1/2 -translate-y-1/2 text-[#9A9AA3]" />
          </div>
        </div>

        <!-- Filter chip (fade di kanan sebagai petunjuk bisa digeser) -->
        <div class="relative">
          <div
            ref="tabsRef"
            class="scrollbar-none flex gap-2 overflow-x-auto pr-10 sm:pr-0"
            style="-webkit-overflow-scrolling: touch;"
          >
            <template v-if="showChipSkeleton">
              <div
                v-for="n in 4"
                :key="'chip-skel-' + n"
                class="h-10 w-24 flex-shrink-0 animate-pulse rounded-full border border-white/10 bg-white/[0.04]"
                aria-hidden="true"
              ></div>
            </template>

            <template v-else>
              <button
                v-for="cat in categories"
                :key="cat.value"
                type="button"
                :ref="el => setTabRef(el, cat.value)"
                :aria-pressed="selectedCategory === cat.value"
                :title="cat.value === FILTER_FAVORITE ? 'Favorit tersimpan di HP ini' : undefined"
                @click="selectCategoryWithScroll(cat.value)"
                :class="[
                  'inline-flex min-h-[40px] flex-shrink-0 items-center gap-1.5 rounded-full border px-4 py-2 text-sm font-medium transition-all duration-200',
                  selectedCategory === cat.value
                    ? 'border-[#D92B22] bg-[#D92B22] text-white'
                    : 'border-white/10 bg-[#1C1C1F] text-[#B8B8C0] hover:border-white/25 hover:text-[#FAFAFA]'
                ]"
              >
                <ThumbsUp v-if="cat.value === FILTER_RECOMMENDED" :size="13" />
                <Heart v-else-if="cat.value === FILTER_FAVORITE" :size="13" />
                {{ cat.label }}
                <span
                  class="rounded-full px-1.5 text-xs tabular-nums"
                  :class="selectedCategory === cat.value ? 'bg-white/20 text-white' : 'bg-white/[0.06] text-[#9A9AA3]'"
                >{{ getCategoryCount(cat.value) }}</span>
              </button>
            </template>
          </div>
          <div class="pointer-events-none absolute bottom-0 right-0 top-0 w-10 bg-gradient-to-l from-[#111113] to-transparent sm:hidden"></div>
        </div>
      </div>
    </div>

    <!-- ── GRID MENU ────────────────────────────────────────────────────────── -->
    <div class="relative mx-auto max-w-7xl px-5 pb-32 pt-6 sm:px-8 sm:pt-8 lg:px-10">

      <!-- Store closed banner -->
      <div
        v-if="settingsReady && !isStoreOpen"
        class="mb-6 flex items-start gap-3 rounded-2xl border border-[#D92B22]/25 bg-[#D92B22]/10 px-5 py-4"
        role="status"
      >
        <Lock :size="17" class="mt-0.5 flex-shrink-0 text-[#F0605A]" />
        <p class="text-sm leading-relaxed text-[#FFB0B0]">
          {{ closedMessage }}
          <span v-if="nextOpenText" class="mt-1 block font-semibold text-[#FFD0D0]">{{ nextOpenText }}</span>
        </p>
      </div>

      <!-- Paket (hanya di tampilan semua menu tanpa pencarian) -->
      <BundleSection v-if="selectedCategory === 'all' && !searchQuery.trim()" />

      <!-- Info hasil + toggle habis + reset filter -->
      <div v-if="!loading && menus.length > 0" class="mb-5 flex flex-wrap items-center justify-between gap-x-4 gap-y-3">
        <span aria-live="polite" class="text-sm text-[#B8B8C0]">
          <span class="font-semibold text-[#FAFAFA]">{{ filteredMenus.length }}</span> menu<template v-if="selectedCategory !== 'all'"> di {{ activeFilterLabel }}</template>
        </span>

        <div class="flex items-center gap-5">
          <button
            v-if="soldOutCount > 0"
            type="button"
            role="switch"
            :aria-checked="hideSoldOut"
            @click="hideSoldOut = !hideSoldOut"
            class="inline-flex items-center gap-2.5 text-sm text-[#B8B8C0] transition-colors hover:text-[#FAFAFA]"
          >
            <span
              class="relative h-5 w-9 flex-shrink-0 rounded-full border transition-colors"
              :class="hideSoldOut ? 'border-[#D92B22] bg-[#D92B22]' : 'border-white/20 bg-white/[0.04]'"
              aria-hidden="true"
            >
              <span
                class="absolute left-0.5 top-0.5 h-3.5 w-3.5 rounded-full bg-white transition-transform duration-150"
                :class="hideSoldOut ? 'translate-x-4' : ''"
              ></span>
            </span>
            Sembunyikan yang habis
          </button>

          <button
            v-if="hasActiveFilters"
            type="button"
            @click="resetFilters"
            class="border-b border-[#F4C542]/60 pb-0.5 text-sm font-medium text-[#F4C542] transition-colors hover:text-[#FAFAFA]"
          >
            Reset filter
          </button>
        </div>
      </div>

      <!-- Loading skeleton -->
      <div v-if="loading" class="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-5 lg:grid-cols-3">
        <div
          v-for="n in 6"
          :key="n"
          class="flex animate-pulse flex-col overflow-hidden rounded-3xl border border-white/[0.06] bg-[#1C1C1F]"
        >
          <div class="aspect-video w-full bg-white/[0.04]"></div>
          <div class="space-y-3 p-5">
            <div class="h-4 w-2/3 rounded-full bg-white/[0.06]"></div>
            <div class="h-3 w-1/2 rounded-full bg-white/[0.04]"></div>
            <div class="flex items-center justify-between pt-4">
              <div class="h-5 w-1/3 rounded-full bg-white/[0.06]"></div>
              <div class="h-11 w-1/4 rounded-full bg-white/[0.06]"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Error state -->
      <div
        v-else-if="loadError && menus.length === 0"
        class="space-y-4 rounded-3xl border border-dashed border-white/10 py-24 text-center sm:py-28"
        role="alert"
      >
        <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-[#1C1C1F]">
          <WifiOff :size="22" class="text-[#B8B8C0]" />
        </div>
        <p class="px-4 font-sora text-lg font-semibold text-[#FAFAFA]">Gagal memuat menu</p>
        <p class="px-4 text-sm text-[#B8B8C0]">Cek koneksi internet kamu, lalu coba lagi.</p>
        <button
          type="button"
          @click="fetchMenus"
          class="mt-2 inline-flex items-center justify-center gap-2 rounded-full bg-[#D92B22] px-6 py-3 text-sm font-semibold text-white transition hover:bg-[#B8201A] active:scale-95"
        >
          <RefreshCw :size="15" />
          Coba lagi
        </button>
      </div>

      <!-- Empty state -->
      <div
        v-else-if="filteredMenus.length === 0"
        class="space-y-4 rounded-3xl border border-dashed border-white/10 py-24 text-center sm:py-28"
      >
        <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-[#1C1C1F]">
          <span class="text-2xl">🍽️</span>
        </div>
        <p class="px-4 font-sora text-lg font-semibold text-[#FAFAFA]">
          {{ searchQuery ? `Tidak ada hasil untuk "${searchQuery}"` : "Menu tidak tersedia" }}
        </p>
        <p class="text-sm text-[#B8B8C0]">Coba kategori lain atau cek lagi nanti.</p>
        <button
          v-if="hasActiveFilters"
          type="button"
          @click="resetFilters"
          class="mt-2 inline-flex items-center justify-center rounded-full border border-white/20 px-6 py-3 text-sm font-semibold text-[#FAFAFA] transition hover:border-white/50 hover:bg-white/5"
        >
          Reset filter
        </button>
      </div>

      <!-- Grid -->
      <TransitionGroup
        v-else
        tag="div"
        class="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-5 lg:grid-cols-3"
        enter-active-class="transition duration-300 ease-out"
        enter-from-class="opacity-0 translate-y-2"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
        move-class="transition-transform duration-300 ease-out"
      >
        <div
          v-for="menu in filteredMenus"
          :key="menu.id"
          class="menu-card group relative flex flex-col overflow-hidden rounded-3xl border border-white/[0.07] transition-all duration-300 hover:border-[#F4C542]/35 sm:hover:-translate-y-1 sm:hover:shadow-[0_28px_48px_-30px_rgba(217,43,34,0.5)]"
        >
          <!-- Foto 16:9 (klik → detail) -->
          <button
            type="button"
            :aria-label="'Lihat detail ' + menu.name"
            class="relative aspect-video w-full shrink-0 overflow-hidden bg-[#232327] text-left"
            @click="openDetail(menu)"
          >
            <img
              v-if="menu.image_url"
              :src="getMediaUrl(menu.image_url, 640)"
              :alt="menu.name"
              :class="{ 'grayscale opacity-60': !menu.is_available }"
              class="pointer-events-none absolute inset-0 h-full w-full object-cover transition-transform duration-700 group-hover:scale-[1.05]"
              loading="lazy"
              decoding="async"
            />
            <div v-else class="absolute inset-0 flex flex-col items-center justify-center gap-2">
              <span class="text-3xl opacity-25">🍜</span>
              <span class="text-xs text-[#9A9AA3]">Belum ada foto</span>
            </div>

            <div class="pointer-events-none absolute inset-0 bg-gradient-to-t from-[#1C1C1F] via-transparent to-transparent opacity-70"></div>

            <!-- Badge -->
            <div class="absolute left-3 top-3 z-10 flex flex-col items-start gap-1.5">
              <div
                v-if="!menu.is_available"
                class="rounded-full border border-white/10 bg-black/70 px-2.5 py-1 backdrop-blur-md"
              >
                <span class="text-[11px] font-semibold text-[#FAFAFA]">Habis</span>
              </div>
              <div
                v-if="menu.is_recommended"
                class="flex items-center gap-1 rounded-full bg-[#D92B22] px-2.5 py-1 text-white"
                title="Rekomendasi"
              >
                <ThumbsUp :size="11" />
                <span class="text-[11px] font-semibold">Rekomendasi</span>
              </div>
              <div
                v-if="bestSellerIds.has(menu.id)"
                class="flex items-center gap-1 rounded-full bg-[#F4C542] px-2.5 py-1 text-[#2A1F00]"
                title="Terlaris"
              >
                <Flame :size="11" />
                <span class="text-[11px] font-semibold">Terlaris</span>
              </div>
            </div>
          </button>

          <!-- Favorit -->
          <button
            type="button"
            :aria-pressed="isFavorite(menu.id)"
            :aria-label="(isFavorite(menu.id) ? 'Hapus dari favorit: ' : 'Simpan ke favorit: ') + menu.name"
            class="absolute right-3 top-3 z-20 flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-black/55 backdrop-blur-md transition-colors hover:bg-black/80"
            @click.stop="toggleFavorite(menu.id)"
          >
            <Heart :size="16" :class="isFavorite(menu.id) ? 'fill-[#D92B22] text-[#D92B22]' : 'text-white/85'" />
          </button>

          <!-- Info -->
          <div
            class="flex min-w-0 flex-1 flex-col gap-4 p-5"
            :class="{ 'opacity-60': !menu.is_available }"
          >
            <div class="flex items-start gap-2">
              <button
                type="button"
                class="min-w-0 flex-1 space-y-1.5 text-left"
                @click="openDetail(menu)"
              >
                <span class="block text-xs font-medium text-[#F4C542]">
                  {{ menu.category_name }}
                </span>
                <h3 class="line-clamp-2 font-sora text-lg font-semibold leading-snug text-[#FAFAFA] transition-colors group-hover:text-white">
                  {{ menu.name }}
                </h3>
                <p class="line-clamp-2 text-sm leading-relaxed text-[#B8B8C0]">
                  {{ menu.description || "Menu andalan spesial Masashimura." }}
                </p>
              </button>
              <button
                type="button"
                :aria-label="'Bagikan ' + menu.name + ' lewat WhatsApp'"
                class="-mr-1.5 -mt-1.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-[#9A9AA3] transition-colors hover:bg-white/5 hover:text-[#FAFAFA]"
                @click="shareMenu(menu)"
              >
                <Share2 :size="16" />
              </button>
            </div>

            <!-- Harga + tombol -->
            <div class="mt-auto flex items-center justify-between gap-3 border-t border-white/[0.07] pt-4">
              <span class="font-sora text-lg font-semibold leading-none tracking-tight text-[#FAFAFA]">
                {{ formatPrice(menu.price_web) }}
              </span>

              <!-- Stepper -->
              <div
                v-if="cartStore.quantityOfMenu(menu.id) > 0"
                class="flex items-center rounded-full border border-white/10 bg-white/[0.03] p-1"
              >
                <button
                  type="button"
                  :aria-label="'Kurangi ' + menu.name"
                  class="flex h-9 w-9 items-center justify-center rounded-full text-[#FAFAFA] transition-colors hover:bg-white/10"
                  @click="cartStore.decrementMenu(menu.id)"
                >
                  <Minus :size="15" />
                </button>
                <span class="min-w-[2rem] text-center text-sm font-semibold tabular-nums text-[#FAFAFA]">
                  {{ cartStore.quantityOfMenu(menu.id) }}
                </span>
                <button
                  type="button"
                  :aria-label="'Tambah ' + menu.name"
                  :disabled="!menu.is_available || !isStoreOpen"
                  class="flex h-9 w-9 items-center justify-center rounded-full bg-[#D92B22] text-white transition-colors hover:bg-[#B8201A] disabled:opacity-40"
                  @click="requestAdd(menu)"
                >
                  <Plus :size="15" />
                </button>
              </div>

              <button
                v-else
                type="button"
                @click="requestAdd(menu)"
                :disabled="!menu.is_available || !isStoreOpen"
                :aria-label="'Tambah ' + menu.name + ' ke keranjang'"
                :class="[
                  'flex min-h-[44px] items-center justify-center gap-1.5 rounded-full px-5 text-sm font-semibold transition-all duration-200',
                  menu.is_available && isStoreOpen
                    ? 'bg-[#D92B22] text-white hover:bg-[#B8201A] hover:shadow-[0_8px_24px_-8px_rgba(217,43,34,0.6)] active:scale-95'
                    : 'cursor-not-allowed border border-white/5 bg-[#232327] text-[#9A9AA3]'
                ]"
              >
                <Plus :size="15" />
                <span>{{ menu.is_available ? "Tambah" : "Habis" }}</span>
              </button>
            </div>
          </div>
        </div>
      </TransitionGroup>
    </div>

    <!-- ── BAR KERANJANG ──────────────────────────────────────────────────────── -->
    <transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="opacity-0 translate-y-3"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-3"
    >
      <div
        v-if="cartStore.cartItemCount > 0 && !isCartOpen"
        class="bar-safe fixed inset-x-4 z-50 sm:inset-x-0 sm:mx-auto sm:max-w-xl"
      >
        <button
          type="button"
          @click="isCartOpen = true"
          :aria-label="`Buka keranjang: ${cartStore.cartItemCount} item, total ${formatPrice(cartStore.totalPrice)}`"
          class="cart-bar flex w-full items-center justify-between gap-4 rounded-2xl border border-white/10 py-3.5 pl-4 pr-5 text-white shadow-[0_16px_44px_rgba(217,43,34,0.4)] transition-all duration-200 active:scale-[0.99]"
          :class="{ 'fab-bump': cartBump }"
        >
          <div class="flex min-w-0 items-center gap-3">
            <div class="relative flex-shrink-0">
              <ShoppingCart :size="20" />
              <span class="absolute -right-2 -top-2 flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-[#FAFAFA] px-1 text-[11px] font-bold leading-none text-[#8F0000]">
                {{ cartStore.cartItemCount }}
              </span>
            </div>
            <span class="truncate font-sora text-sm font-semibold">Lihat keranjang</span>
          </div>
          <span class="flex-shrink-0 font-sora text-base font-semibold tracking-tight">
            {{ formatPrice(cartStore.totalPrice) }}
          </span>
        </button>
      </div>
    </transition>

    <!-- ── CART DRAWER ────────────────────────────────────────────────────────── -->
    <Cart
      v-if="isCartOpen"
      :format-price="formatPrice"
      :recommendations="cartRecommendations"
      @close="isCartOpen = false"
      @add="requestAdd"
      @view="viewFromCart"
    />

    <!-- ── DETAIL MODAL ───────────────────────────────────────────────────────── -->
    <MenuDetailModal
      v-if="selectedMenu"
      :menu="selectedMenu"
      :format-price="formatPrice"
      :is-store-open="isStoreOpen"
      :is-best-seller="bestSellerIds.has(selectedMenu.id)"
      :is-favorite="isFavorite(selectedMenu.id)"
      :recommendations="detailRecommendations"
      @close="closeDetail"
      @open-menu="openDetail"
      @add-to-cart="requestAdd"
      @share="shareMenu"
      @toggle-favorite="toggleFavorite"
    />

    <!-- ── PICKER OPSI (pedas, add-on, dll) ───────────────────────────────────── -->
    <MenuOptionPicker
      v-if="pickerMenu"
      :menu="pickerMenu"
      :format-price="formatPrice"
      @close="pickerMenu = null"
      @confirm="confirmPicker"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useCartStore } from "@/stores/cart"
import { useAuthStore } from "@/stores/auth"
import { menuAPI, getMediaUrl } from "@/api"
import { toast } from "vue-sonner"
import {
  ShoppingCart, Plus, Minus, Search, X, ChevronDown, Lock,
  ThumbsUp, Flame, Heart, Share2, RefreshCw, WifiOff,
} from "lucide-vue-next"
import Cart from "@/components/ui/Cart.vue"
import MenuDetailModal from "@/components/ui/MenuDetailModal.vue"
import MenuOptionPicker from "@/components/ui/MenuOptionPicker.vue"
import CrowdBadge from "@/components/ui/CrowdBadge.vue"
import { useRecommender } from "@/composables/useRecommender"
import BundleSection from "@/components/ui/BundleSection.vue"
import { useStoreSettings } from "@/composables/useStoreSettings"
import { shareMenuToWhatsApp } from "@/composables/useShareMenu"

const route  = useRoute()
const router = useRouter()

const cartStore = useCartStore()
const authStore = useAuthStore()
const menus      = ref([])
const loading    = ref(true)
const loadError  = ref(false)
const isCartOpen = ref(false)

// Filter spesial di deretan chip kategori
const FILTER_RECOMMENDED = "__recommended"
const FILTER_FAVORITE    = "__favorite"

const selectedCategory = ref("all")
const searchQuery      = ref("")
const sortBy           = ref("default") // 'default' | 'price_asc' | 'price_desc'
const hideSoldOut      = ref(false)
const selectedMenu     = ref(null)       // menu yang lagi dibuka di detail modal
const pickerMenu       = ref(null)       // menu beropsi yang lagi dipilih opsinya

// ── Favorit (disimpan di perangkat ini, hilang kalau ganti HP / hapus data) ──
const FAV_KEY = "masashimura:favoriteMenus"
const loadFavorites = () => {
  try {
    const parsed = JSON.parse(localStorage.getItem(FAV_KEY) || "[]")
    return Array.isArray(parsed) ? parsed.filter(Number.isInteger) : []
  } catch {
    return []
  }
}
const favoriteIds = ref(loadFavorites())
watch(favoriteIds, (value) => {
  try { localStorage.setItem(FAV_KEY, JSON.stringify(value)) } catch { /* storage penuh / mode private */ }
}, { deep: true })

const isFavorite = (id) => favoriteIds.value.includes(id)
const toggleFavorite = (id) => {
  if (isFavorite(id)) {
    favoriteIds.value = favoriteIds.value.filter((x) => x !== id)
  } else {
    favoriteIds.value = [...favoriteIds.value, id]
    toast.success("Disimpan ke favorit di HP ini ❤️")
  }
}

// ── Terlaris (otomatis dari endpoint best seller) ───────────────────────────
const bestSellerIds = ref(new Set())
const fetchBestSellers = async () => {
  try {
    const { data } = await menuAPI.getBestSellers()
    bestSellerIds.value = new Set((data || []).map((m) => m.id))
  } catch {
    /* badge Terlaris hanya pemanis: kalau gagal, halaman tetap jalan tanpa badge */
  }
}

const activeMenus = computed(() => menus.value.filter((m) => m.category_name))

// ── Rekomendasi (content-based: TF-IDF + cosine similarity) ─────────────────
// Indeks dibangun dari menu yang tampil di halaman ini (tanpa menu secret/nonaktif).
const { similarMenus, cartSuggestions } = useRecommender(activeMenus)
const detailRecommendations = computed(() =>
  selectedMenu.value ? similarMenus(selectedMenu.value.id, 3) : []
)
const cartRecommendations = computed(() =>
  cartSuggestions(cartStore.cartItems.map((item) => item.id), 3)
)

const soldOutCount = computed(() => activeMenus.value.filter((m) => !m.is_available).length)

// Chip kategori belum ada datanya selama pemuatan pertama
const showChipSkeleton = computed(() => loading.value && menus.value.length === 0)

const categories = computed(() => {
  const uniqueCats = [...new Set(activeMenus.value.map((m) => m.category_name))]
  const list = [{ label: "Semua", value: "all" }]
  if (activeMenus.value.some((m) => m.is_recommended)) {
    list.push({ label: "Rekomendasi", value: FILTER_RECOMMENDED })
  }
  if (activeMenus.value.some((m) => isFavorite(m.id))) {
    list.push({ label: "Favorit", value: FILTER_FAVORITE })
  }
  return [...list, ...uniqueCats.map((name) => ({ label: name, value: name }))]
})

const activeFilterLabel = computed(
  () => categories.value.find((c) => c.value === selectedCategory.value)?.label ?? selectedCategory.value
)

// Chip yang lagi aktif bisa hilang (mis. favorit terakhir dihapus) → balik ke "Semua"
watch(categories, (list) => {
  if (!list.some((c) => c.value === selectedCategory.value)) selectedCategory.value = "all"
})

const { isStoreOpen, closedMessage, nextOpenText, settingsReady, fetchSettings } = useStoreSettings()
onMounted(() => {
  fetchMenus()
  fetchBestSellers()
  fetchSettings()
})

const selectCategory = (val) => { selectedCategory.value = val }

const getCategoryCount = (val) => {
  if (val === "all") return activeMenus.value.length
  if (val === FILTER_RECOMMENDED) return activeMenus.value.filter((m) => m.is_recommended).length
  if (val === FILTER_FAVORITE) return activeMenus.value.filter((m) => isFavorite(m.id)).length
  return activeMenus.value.filter((m) => m.category_name === val).length
}

// Samakan keranjang (tersimpan di HP) dengan daftar menu terbaru, lalu kabari customer
// kalau ada yang berubah. Dengan begini masalahnya ketahuan di sini, bukan baru saat bayar.
const reconcileCart = () => {
  if (cartStore.isEmpty || menus.value.length === 0) return
  const r = cartStore.reconcileWithMenus(menus.value)

  const notes = []
  if (r.removed.length)        notes.push(`${r.removed.join(", ")} sudah tidak tersedia`)
  if (r.soldOut.length)        notes.push(`${r.soldOut.join(", ")} habis`)
  if (r.optionsChanged.length) notes.push(`opsi ${r.optionsChanged.join(", ")} berubah, silakan pilih ulang`)
  if (r.repriced.length)       notes.push(`harga ${r.repriced.join(", ")} diperbarui`)

  if (notes.length) {
    toast.info(`Keranjang diperbarui: ${notes.join("; ")}.`, { duration: 7000 })
  }
}

const fetchMenus = async () => {
  try {
    loading.value = true
    loadError.value = false
    const { data } = await menuAPI.getAll()
    // Server sudah menyaring untuk customer. Filter ini untuk staff yang login: mereka
    // menerima semua menu, tapi halaman customer tidak boleh menampilkan secret/nonaktif.
    menus.value = (data || []).filter((m) => m.is_active !== false && !m.is_secret)
    reconcileCart()
  } catch {
    loadError.value = true
    // Kalau sudah ada daftar menu sebelumnya, cukup toast. Kalau belum, panel error yang tampil.
    if (menus.value.length > 0) toast.error("Gagal memperbarui daftar menu.")
  } finally {
    loading.value = false
    syncDetailFromRoute()
  }
}

const filteredMenus = computed(() => {
  // Menu tanpa kategori (category_name null) selalu disembunyikan dari customer
  let list = activeMenus.value

  if (selectedCategory.value === FILTER_RECOMMENDED) {
    list = list.filter((m) => m.is_recommended)
  } else if (selectedCategory.value === FILTER_FAVORITE) {
    list = list.filter((m) => isFavorite(m.id))
  } else if (selectedCategory.value !== "all") {
    list = list.filter((m) => m.category_name === selectedCategory.value)
  }

  if (hideSoldOut.value) {
    list = list.filter((m) => m.is_available)
  }

  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    list = list.filter((m) =>
      m.name?.toLowerCase().includes(q) ||
      m.description?.toLowerCase().includes(q)
    )
  }

  list = [...list].sort((a, b) => {
    // Habis selalu di bawah, ga peduli sort apa
    if (a.is_available !== b.is_available) return b.is_available - a.is_available
    if (sortBy.value === "price_asc")  return a.price_web - b.price_web
    if (sortBy.value === "price_desc") return b.price_web - a.price_web
    return 0
  })

  return list
})

// Ada filter/sort/pencarian yang aktif? (buat nampilin tombol "Reset filter")
const hasActiveFilters = computed(() =>
  selectedCategory.value !== "all" ||
  searchQuery.value.trim() !== "" ||
  sortBy.value !== "default" ||
  hideSoldOut.value
)

// ── Tambah ke keranjang ─────────────────────────────────────────────────────
// Pintu masuk dari kartu & detail modal: menu beropsi dibuka picker dulu.
const requestAdd = (menu) => {
  if (!isStoreOpen.value) return toast.error(closedMessage.value)
  if (!menu.is_available) return toast.error("Menu ini sedang habis!")
  if (menu.options?.length) {
    pickerMenu.value = menu
    return
  }
  addToCart(menu)
}

const addToCart = (menu, selection = {}, quantity = 1) => {
  const result = cartStore.addToCart(menu, selection, quantity)
  if (!result.ok) {
    toast.error(result.error)
    return false
  }
  toast.success(`${menu.name} ditambahkan! 🛒`)
  return true
}

const confirmPicker = ({ selection, quantity }) => {
  const menu = pickerMenu.value
  if (!menu) return
  if (addToCart(menu, selection, quantity)) {
    pickerMenu.value = null
    if (selectedMenu.value) closeDetail()
  }
}

// ── Detail modal + deep link (/menu?item=ID) ────────────────────────────────
const setItemQuery = (id) => {
  const query = { ...route.query }
  if (id == null) delete query.item
  else query.item = String(id)
  router.replace({ query }).catch(() => {})
}

// Samakan modal dengan URL: link yang dibagikan ke WhatsApp langsung membuka detail menu.
const syncDetailFromRoute = () => {
  // Tunggu daftar menu selesai dimuat. Kalau gagal dimuat, jangan salah mengira
  // menunya sudah tidak ada: biarkan ?item= di URL sampai customer menekan "Coba lagi".
  if (loading.value || loadError.value) return
  const raw = route.query.item
  if (raw == null || raw === "") {
    selectedMenu.value = null
    return
  }
  const found = menus.value.find((m) => String(m.id) === String(raw))
  if (found) {
    selectedMenu.value = found
  } else {
    selectedMenu.value = null
    toast.info("Menu itu sudah tidak tersedia.")
    setItemQuery(null)
  }
}
watch(() => route.query.item, syncDetailFromRoute)

// Dari rekomendasi di keranjang: tutup drawer dulu, baru buka detail menunya.
const viewFromCart = (menu) => {
  isCartOpen.value = false
  openDetail(menu)
}

const openDetail = (menu) => {
  selectedMenu.value = menu
  setItemQuery(menu.id)
}
const closeDetail = () => {
  selectedMenu.value = null
  setItemQuery(null)
}

// ── Share ke WhatsApp ───────────────────────────────────────────────────────
// getMediaUrl dikirim tanpa lebar, jadi foto yang dibagikan tetap file aslinya.
const shareMenu = async (menu) => {
  try {
    const mode = await shareMenuToWhatsApp(menu, { formatPrice, getMediaUrl })
    if (mode === "link") toast.info("Membuka WhatsApp…")
  } catch {
    toast.error("Gagal membagikan menu")
  }
}

const formatPrice = (p) =>
  new Intl.NumberFormat("id-ID", {
    style: "currency", currency: "IDR", minimumFractionDigits: 0,
  }).format(p || 0)

const tabsRef = ref(null)
const tabRefs = {}

const setTabRef = (el, val) => { if (el) tabRefs[val] = el }

const scrollTabIntoView = (val) => {
  const tab = tabRefs[val]
  const container = tabsRef.value
  if (!tab || !container) return
  container.scrollTo({
    left: tab.offsetLeft - container.offsetWidth / 2 + tab.offsetWidth / 2,
    behavior: "smooth",
  })
}

const selectCategoryWithScroll = (val) => {
  selectCategory(val)
  scrollTabIntoView(val)
}

const resetFilters = () => {
  searchQuery.value = ""
  sortBy.value = "default"
  hideSoldOut.value = false
  selectCategoryWithScroll("all")
}

// Animasi kecil di bar keranjang tiap ada item yang ditambah
const cartBump = ref(false)
let bumpTimer = null
watch(() => cartStore.cartItemCount, (now, before) => {
  if (now > (before || 0)) {
    cartBump.value = true
    clearTimeout(bumpTimer)
    bumpTimer = setTimeout(() => { cartBump.value = false }, 350)
  }
})
onUnmounted(() => clearTimeout(bumpTimer))
</script>

<style scoped>
/*
  Palet (sama dengan halaman Lokasi & Kontak)
  Warm black #111113 · Surface #1C1C1F · Washi #FAFAFA
  Crimson #D92B22 (aksi) · Champagne #F4C542 (detail premium)
*/

.page-glow {
  background:
    radial-gradient(60% 70% at 15% 0%, rgba(217,43,34, 0.09), transparent 70%),
    radial-gradient(40% 50% at 90% 10%, rgba(244,197,66, 0.03), transparent 70%);
}

.menu-card {
  background: #1C1C1F;
}

.cart-bar {
  background: #D92B22;
}
.cart-bar:hover {
  filter: brightness(1.08);
}

.scrollbar-none::-webkit-scrollbar { display: none; }
.scrollbar-none { -ms-overflow-style: none; scrollbar-width: none; }

/* Fokus keyboard yang jelas */
a:focus-visible,
button:focus-visible,
select:focus-visible {
  outline: 2px solid #F4C542;
  outline-offset: 3px;
}

/* Bar keranjang aman dari home-indicator / notch di HP */
.bar-safe { bottom: calc(1rem + env(safe-area-inset-bottom, 0px)); }
@media (min-width: 640px) {
  .bar-safe { bottom: 1.5rem; }
}

@keyframes fabBump {
  0%   { transform: scale(1); }
  40%  { transform: scale(1.03); }
  100% { transform: scale(1); }
}
.fab-bump { animation: fabBump 0.35s ease; }

@media (prefers-reduced-motion: reduce) {
  .fab-bump { animation: none; }
}
</style>