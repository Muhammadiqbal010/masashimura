<template>
  <div class="min-h-screen bg-[#060606] text-white font-inter">

    <!-- ── HEADER ──────────────────────────────────────────────────────────── -->
    <div class="pt-24 sm:pt-28 pb-6 sm:pb-8 px-6 sm:px-10 max-w-7xl mx-auto">
      <div class="space-y-3">
        <div class="flex items-center gap-3">
          <span class="w-6 h-px bg-[#DC2626]"></span>
          <span class="font-mono text-[10px] tracking-[0.3em] text-[#DC2626] uppercase">Menu Kuliner</span>
        </div>
        <h1 class="font-sora text-4xl sm:text-5xl font-extrabold uppercase tracking-tight text-white leading-[0.95]">
          Pilih <span class="text-[#DC2626]">Menu</span>
        </h1>
        <p class="text-zinc-400 text-sm font-light max-w-sm leading-relaxed">
          Rasa dijamin enak yang ramah di kantong. Fresh tiap hari.
        </p>
      </div>
    </div>

    <!-- ── STICKY SEARCH + FILTER BAR ─────────────────────────────────────────── -->
    <div class="sticky top-0 z-30 bg-[#060606]/90 backdrop-blur-md border-y border-white/[0.06]">
      <div class="px-6 sm:px-10 max-w-7xl mx-auto py-3 sm:py-4 space-y-3">

        <!-- Search + Sort row -->
        <div class="flex gap-2">
          <div class="relative flex-1 min-w-0">
            <Search :size="15" class="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none" />
            <input
              v-model="searchQuery"
              type="text"
              inputmode="search"
              enterkeyhint="search"
              autocomplete="off"
              placeholder="Cari menu..."
              aria-label="Cari menu"
              class="w-full bg-[#0d0d0d] border border-white/10 pl-10 pr-10 py-3 text-base sm:text-sm font-light text-white placeholder:text-zinc-500 focus:outline-none focus:border-[#DC2626]/60 transition-colors"
            />
            <button
              v-if="searchQuery"
              type="button"
              @click="searchQuery = ''"
              aria-label="Hapus pencarian"
              class="absolute right-1.5 top-1/2 -translate-y-1/2 w-9 h-9 flex items-center justify-center text-zinc-500 hover:text-white transition-colors"
            >
              <X :size="15" />
            </button>
          </div>

          <div class="relative flex-shrink-0">
            <select
              v-model="sortBy"
              aria-label="Urutkan menu"
              class="h-full bg-[#0d0d0d] border border-white/10 pl-3.5 pr-9 text-base font-medium normal-case text-zinc-300 sm:text-xs sm:font-sora sm:font-bold sm:uppercase sm:tracking-widest sm:text-zinc-400 focus:outline-none focus:border-[#DC2626]/60 transition-colors appearance-none cursor-pointer"
            >
              <option value="default">Urutkan</option>
              <option value="price_asc">Termurah</option>
              <option value="price_desc">Termahal</option>
            </select>
            <ChevronDown :size="14" class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none" />
          </div>
        </div>

        <!-- Filter tabs (fade di kanan sebagai petunjuk bisa digeser) -->
        <div class="relative">
          <div
            ref="tabsRef"
            class="flex gap-2 overflow-x-auto scrollbar-none pr-10 sm:pr-0"
            style="-webkit-overflow-scrolling: touch;"
          >
            <!-- Skeleton chip saat pertama dimuat, supaya layout tidak loncat -->
            <template v-if="showChipSkeleton">
              <div
                v-for="n in 4"
                :key="'chip-skel-' + n"
                class="flex-shrink-0 h-10 w-24 border border-white/10 bg-white/[0.04] animate-pulse"
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
                  'flex-shrink-0 min-h-[40px] px-4 py-2 border text-[10px] font-sora font-bold uppercase tracking-widest transition-all duration-200',
                  selectedCategory === cat.value
                    ? 'text-white bg-[#DC2626] border-[#DC2626]'
                    : 'text-zinc-400 bg-[#0d0d0d] border-white/10 hover:text-white hover:border-white/30'
                ]"
              >
                <ThumbsUp v-if="cat.value === FILTER_RECOMMENDED" :size="11" class="inline -mt-0.5 mr-1" />
                <Heart v-else-if="cat.value === FILTER_FAVORITE" :size="11" class="inline -mt-0.5 mr-1" />
                {{ cat.label }}
                <span class="ml-1.5 font-mono text-[9px] opacity-60">{{ getCategoryCount(cat.value) }}</span>
              </button>
            </template>
          </div>
          <div class="pointer-events-none absolute right-0 top-0 bottom-0 w-10 bg-gradient-to-l from-[#060606] to-transparent sm:hidden"></div>
        </div>
      </div>
    </div>

    <!-- ── GRID MENU ────────────────────────────────────────────────────────── -->
    <div class="px-6 sm:px-10 max-w-7xl mx-auto pt-6 sm:pt-8 pb-32">

      <!-- Store closed banner -->
      <div
        v-if="settingsReady && !isStoreOpen"
        class="flex items-center gap-3 bg-red-500/10 border border-red-500/20 px-5 py-4 mb-6"
        role="status"
      >
        <Lock :size="16" class="text-red-400 flex-shrink-0" />
        <p class="font-mono text-[11px] text-red-300 leading-relaxed">
          {{ closedMessage }}
          <span v-if="nextOpenText" class="block mt-1 font-bold text-red-200">{{ nextOpenText }}</span>
        </p>
      </div>

      <!-- Info hasil + toggle habis + reset filter -->
      <div v-if="!loading && menus.length > 0" class="flex flex-wrap items-center justify-between gap-x-4 gap-y-3 mb-5">
        <span aria-live="polite" class="font-mono text-[10px] text-zinc-500 tracking-[0.25em] uppercase">
          {{ filteredMenus.length }} menu<template v-if="selectedCategory !== 'all'"> · {{ activeFilterLabel }}</template>
        </span>

        <div class="flex items-center gap-5">
          <button
            v-if="soldOutCount > 0"
            type="button"
            role="switch"
            :aria-checked="hideSoldOut"
            @click="hideSoldOut = !hideSoldOut"
            class="inline-flex items-center gap-2 font-mono text-[10px] tracking-[0.2em] uppercase text-zinc-400 hover:text-white transition-colors"
          >
            <span
              class="relative w-7 h-4 border transition-colors flex-shrink-0"
              :class="hideSoldOut ? 'bg-[#DC2626] border-[#DC2626]' : 'bg-transparent border-white/25'"
              aria-hidden="true"
            >
              <span
                class="absolute top-0.5 left-0.5 w-2.5 h-2.5 bg-white transition-transform duration-150"
                :class="hideSoldOut ? 'translate-x-3' : ''"
              ></span>
            </span>
            Sembunyikan habis
          </button>

          <button
            v-if="hasActiveFilters"
            type="button"
            @click="resetFilters"
            class="font-mono text-[10px] tracking-[0.2em] uppercase text-zinc-400 hover:text-white border-b border-[#DC2626] pb-0.5 transition-colors"
          >
            Reset filter
          </button>
        </div>
      </div>

      <!-- Loading skeleton -->
      <div v-if="loading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
        <div
          v-for="n in 6"
          :key="n"
          class="bg-[#0d0d0d] border border-white/[0.06] overflow-hidden animate-pulse flex flex-col"
        >
          <div class="w-full aspect-video bg-white/[0.04]"></div>
          <div class="p-4 sm:p-5 space-y-3">
            <div class="h-3 bg-white/[0.05] w-2/3"></div>
            <div class="h-2 bg-white/[0.03] w-1/2"></div>
            <div class="flex justify-between items-center pt-4">
              <div class="h-5 bg-white/[0.05] w-1/3"></div>
              <div class="h-10 bg-white/[0.05] w-1/4"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Error state: gagal memuat dan belum ada data sama sekali -->
      <div
        v-else-if="loadError && menus.length === 0"
        class="py-24 sm:py-28 text-center space-y-4 border border-dashed border-white/10"
        role="alert"
      >
        <div class="w-14 h-14 bg-[#0d0d0d] border border-white/10 flex items-center justify-center mx-auto">
          <WifiOff :size="22" class="text-zinc-500" />
        </div>
        <p class="font-sora text-xs font-bold uppercase tracking-widest text-zinc-300 px-4">
          Gagal memuat menu
        </p>
        <p class="text-xs text-zinc-500 font-light px-4">Cek koneksi internet kamu, lalu coba lagi.</p>
        <button
          type="button"
          @click="fetchMenus"
          class="mt-2 inline-flex items-center justify-center gap-2 bg-[#DC2626] hover:bg-red-700 text-white font-sora text-[10px] uppercase tracking-[0.2em] px-6 py-3 font-bold transition active:scale-95"
        >
          <RefreshCw :size="13" />
          Coba lagi
        </button>
      </div>

      <!-- Empty state -->
      <div
        v-else-if="filteredMenus.length === 0"
        class="py-24 sm:py-28 text-center space-y-4 border border-dashed border-white/10"
      >
        <div class="w-14 h-14 bg-[#0d0d0d] border border-white/10 flex items-center justify-center mx-auto">
          <span class="text-2xl">🍽️</span>
        </div>
        <p class="font-sora text-xs font-bold uppercase tracking-widest text-zinc-300 px-4">
          {{ searchQuery ? `Tidak ada hasil untuk "${searchQuery}"` : "Menu tidak tersedia" }}
        </p>
        <p class="text-xs text-zinc-500 font-light">Coba kategori lain atau cek lagi nanti.</p>
        <button
          v-if="hasActiveFilters"
          type="button"
          @click="resetFilters"
          class="mt-2 inline-flex items-center justify-center border border-white/20 hover:border-white/50 hover:bg-white/5 text-white font-sora text-[10px] uppercase tracking-[0.2em] px-6 py-3 font-bold transition"
        >
          Reset filter
        </button>
      </div>

      <!-- Grid -->
      <TransitionGroup
        v-else
        tag="div"
        class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5"
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
          class="group relative bg-[#0d0d0d] border border-white/[0.07] overflow-hidden flex flex-col transition-all duration-300 hover:border-[#DC2626]/40 sm:hover:-translate-y-1 sm:hover:shadow-[0_24px_40px_-28px_rgba(220,38,38,0.45)]"
        >
          <!-- Foto 16:9 (klik → detail). Rasio sama dengan hasil crop di admin, jadi tidak ada yang terpotong. -->
          <button
            type="button"
            :aria-label="'Lihat detail ' + menu.name"
            class="relative shrink-0 w-full aspect-video bg-[#111] overflow-hidden text-left"
            @click="openDetail(menu)"
          >
            <img
              v-if="menu.image_url"
              :src="getMediaUrl(menu.image_url, 640)"
              :alt="menu.name"
              :class="{ 'grayscale opacity-60': !menu.is_available }"
              class="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-[1.06] pointer-events-none"
              loading="lazy"
              decoding="async"
            />
            <div
              v-else
              class="absolute inset-0 flex flex-col items-center justify-center gap-2"
            >
              <span class="text-3xl opacity-20">🍜</span>
              <span class="font-mono text-[9px] uppercase tracking-widest text-zinc-600">No Image</span>
            </div>

            <!-- Overlay gradient bawah foto -->
            <div class="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent pointer-events-none"></div>

            <!-- Badge: Habis, Rekomendasi (jempol, diatur owner), Terlaris (otomatis) -->
            <div class="absolute top-3 left-3 z-10 flex flex-col items-start gap-1">
              <div
                v-if="!menu.is_available"
                class="bg-black/75 backdrop-blur-md border border-white/10 px-2 py-1"
              >
                <span class="font-mono text-[9px] font-bold tracking-[0.2em] text-zinc-300 uppercase">Habis</span>
              </div>
              <div
                v-if="menu.is_recommended"
                class="flex items-center gap-1 bg-[#DC2626] text-white px-1.5 py-1"
                title="Rekomendasi"
              >
                <ThumbsUp :size="11" />
                <span class="font-mono text-[9px] font-bold tracking-[0.15em] uppercase">Rekomendasi</span>
              </div>
              <div
                v-if="bestSellerIds.has(menu.id)"
                class="flex items-center gap-1 bg-amber-400 text-black px-1.5 py-1"
                title="Terlaris"
              >
                <Flame :size="11" />
                <span class="font-mono text-[9px] font-bold tracking-[0.15em] uppercase">Terlaris</span>
              </div>
            </div>
          </button>

          <!-- Favorit (disimpan di perangkat ini). Posisi tetap di pojok kanan atas foto. -->
          <button
            type="button"
            :aria-pressed="isFavorite(menu.id)"
            :aria-label="(isFavorite(menu.id) ? 'Hapus dari favorit: ' : 'Simpan ke favorit: ') + menu.name"
            class="absolute z-20 top-3 right-3 w-9 h-9 flex items-center justify-center rounded-full bg-black/60 backdrop-blur-md border border-white/10 hover:bg-black/80 transition-colors"
            @click.stop="toggleFavorite(menu.id)"
          >
            <Heart :size="15" :class="isFavorite(menu.id) ? 'fill-[#DC2626] text-[#DC2626]' : 'text-white/80'" />
          </button>

          <!-- Info -->
          <div
            class="flex-1 min-w-0 p-4 sm:p-5 flex flex-col gap-3 sm:gap-4"
            :class="{ 'opacity-60': !menu.is_available }"
          >
            <!-- Kategori + nama + deskripsi (klik → detail) -->
            <div class="flex items-start gap-2">
              <button
                type="button"
                class="flex-1 min-w-0 space-y-1.5 text-left"
                @click="openDetail(menu)"
              >
                <span class="block font-mono text-[9px] tracking-[0.2em] uppercase text-zinc-500">
                  {{ menu.category_name }}
                </span>
                <h3 class="font-sora text-sm font-bold uppercase tracking-wide text-white leading-tight line-clamp-2 group-hover:text-[#DC2626] transition-colors">
                  {{ menu.name }}
                </h3>
                <p class="text-zinc-400 text-xs font-light leading-relaxed line-clamp-2">
                  {{ menu.description || "Menu andalan spesial Masashimura." }}
                </p>
              </button>
              <button
                type="button"
                :aria-label="'Bagikan ' + menu.name + ' lewat WhatsApp'"
                class="shrink-0 -mt-1 -mr-1 w-9 h-9 flex items-center justify-center text-zinc-500 hover:text-white transition-colors"
                @click="shareMenu(menu)"
              >
                <Share2 :size="15" />
              </button>
            </div>

            <!-- Harga + tombol -->
            <div class="mt-auto flex items-center justify-between gap-3 pt-3 sm:pt-4 border-t border-white/[0.07]">
              <span class="font-mono text-[15px] font-bold text-amber-400 tracking-tight leading-none">
                {{ formatPrice(menu.price_web) }}
              </span>

              <!-- Stepper: muncul kalau menu sudah ada di keranjang -->
              <div
                v-if="cartStore.quantityOfMenu(menu.id) > 0"
                class="flex items-center border border-white/10"
              >
                <button
                  type="button"
                  :aria-label="'Kurangi ' + menu.name"
                  class="w-10 h-11 flex items-center justify-center text-zinc-300 hover:text-white hover:bg-white/5 transition-colors"
                  @click="cartStore.decrementMenu(menu.id)"
                >
                  <Minus :size="14" />
                </button>
                <span class="min-w-[1.75rem] text-center font-mono text-[13px] font-bold text-white">
                  {{ cartStore.quantityOfMenu(menu.id) }}
                </span>
                <button
                  type="button"
                  :aria-label="'Tambah ' + menu.name"
                  :disabled="!menu.is_available || !isStoreOpen"
                  class="w-10 h-11 flex items-center justify-center bg-[#DC2626] hover:bg-red-700 text-white disabled:opacity-40 transition-colors"
                  @click="requestAdd(menu)"
                >
                  <Plus :size="14" />
                </button>
              </div>

              <button
                v-else
                type="button"
                @click="requestAdd(menu)"
                :disabled="!menu.is_available || !isStoreOpen"
                :aria-label="'Tambah ' + menu.name + ' ke keranjang'"
                :class="[
                  'flex items-center justify-center gap-1.5 min-h-[44px] px-4 text-[10px] font-sora font-bold uppercase tracking-widest transition-all duration-200',
                  menu.is_available && isStoreOpen
                    ? 'bg-[#DC2626] hover:bg-red-700 text-white active:scale-95'
                    : 'bg-[#161616] text-zinc-600 cursor-not-allowed border border-white/5'
                ]"
              >
                <Plus :size="14" />
                <span>{{ menu.is_available ? "Tambah" : "Habis" }}</span>
              </button>
            </div>
          </div>
        </div>
      </TransitionGroup>
    </div>

    <!-- ── BAR KERANJANG (jumlah + total, tap untuk buka) ───────────────────── -->
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
        class="bar-safe fixed inset-x-4 sm:inset-x-0 sm:max-w-xl sm:mx-auto z-50"
      >
        <button
          type="button"
          @click="isCartOpen = true"
          :aria-label="`Buka keranjang: ${cartStore.cartItemCount} item, total ${formatPrice(cartStore.totalPrice)}`"
          class="w-full flex items-center justify-between gap-4 bg-[#DC2626] text-white pl-4 pr-5 py-3.5 shadow-[0_12px_40px_rgba(220,38,38,0.35)] hover:bg-red-700 active:scale-[0.99] transition-colors duration-200"
          :class="{ 'fab-bump': cartBump }"
        >
          <div class="flex items-center gap-3 min-w-0">
            <div class="relative flex-shrink-0">
              <ShoppingCart :size="18" />
              <span class="absolute -top-2 -right-2 bg-white text-[#DC2626] text-[9px] font-black min-w-[16px] h-4 px-1 rounded-full flex items-center justify-center leading-none">
                {{ cartStore.cartItemCount }}
              </span>
            </div>
            <span class="font-sora text-[10px] font-bold uppercase tracking-widest truncate">Lihat Keranjang</span>
          </div>
          <span class="font-mono text-[14px] font-bold tracking-tight flex-shrink-0">
            {{ formatPrice(cartStore.totalPrice) }}
          </span>
        </button>
      </div>
    </transition>

    <!-- ── CART DRAWER ────────────────────────────────────────────────────────── -->
    <Cart v-if="isCartOpen" @close="isCartOpen = false" :format-price="formatPrice" />

    <!-- ── DETAIL MODAL ───────────────────────────────────────────────────────── -->
    <MenuDetailModal
      v-if="selectedMenu"
      :menu="selectedMenu"
      :format-price="formatPrice"
      :is-store-open="isStoreOpen"
      :is-best-seller="bestSellerIds.has(selectedMenu.id)"
      :is-favorite="isFavorite(selectedMenu.id)"
      @close="closeDetail"
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
.scrollbar-none::-webkit-scrollbar { display: none; }
.scrollbar-none { -ms-overflow-style: none; scrollbar-width: none; }

/* Fokus keyboard yang jelas */
a:focus-visible,
button:focus-visible,
select:focus-visible {
  outline: 2px solid #DC2626;
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