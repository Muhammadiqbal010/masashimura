<template>
  <div class="min-h-screen bg-[#060606] text-white font-inter">

    <!-- ── HEADER ──────────────────────────────────────────────────────────── -->
    <div class="pt-24 pb-8 px-4 sm:px-8 max-w-7xl mx-auto">
      <div class="space-y-1 mb-8">
        <div class="flex items-center gap-2">
          <span class="w-4 h-px bg-[#DC2626]"></span>
          <span class="font-mono text-[9px] tracking-[0.35em] text-[#DC2626] uppercase">Menu Kuliner</span>
        </div>
        <h1 class="font-sora text-3xl sm:text-4xl font-extrabold uppercase tracking-tight text-white">
          Pilih Menu 
        </h1>
        <p class="text-zinc-600 text-[11px] font-light max-w-xs leading-relaxed mt-1">
          Rasa dijamin enak yang ramah di kantong. Fresh tiap hari.
        </p>
      </div>

      <!-- Filter tabs -->
      <div
        ref="tabsRef"
        class="flex gap-1.5 overflow-x-auto scrollbar-none"
        style="-webkit-overflow-scrolling: touch;"
      >
        <button
          v-for="cat in categories"
          :key="cat.value"
          :ref="el => setTabRef(el, cat.value)"
          @click="selectCategoryWithScroll(cat.value)"
          :class="[
            'flex-shrink-0 px-4 py-2 text-[10px] font-sora font-bold uppercase tracking-widest transition-all duration-200 rounded-lg',
            selectedCategory === cat.value
              ? 'text-white bg-[#DC2626]'
              : 'text-zinc-600 bg-[#111111] hover:text-zinc-300 border border-white/[0.06] hover:border-white/10'
          ]"
        >
          {{ cat.label }}
          <span
            v-if="cat.value !== 'all'"
            class="ml-1.5 font-mono text-[9px] opacity-50"
          >{{ getCategoryCount(cat.value) }}</span>
        </button>
      </div>

      <!-- Store closed banner -->
      <div
        v-if="!isStoreOpen"
        class="flex items-center gap-3 bg-red-500/10 border border-red-500/20 rounded-2xl px-5 py-4 mb-6"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-red-400 flex-shrink-0">
          <rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/>
        </svg>
        <p class="font-mono text-[11px] text-red-400 leading-relaxed">{{ closedMessage }}</p>
      </div>
    </div>

    <!-- ── GRID MENU ────────────────────────────────────────────────────────── -->
    <div class="px-4 sm:px-8 max-w-7xl mx-auto pb-32">

      <!-- Loading skeleton -->
      <div v-if="loading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="n in 6"
          :key="n"
          class="bg-[#0d0d0d] border border-white/[0.05] rounded-2xl overflow-hidden animate-pulse"
        >
          <div class="aspect-[4/3] bg-white/[0.04]"></div>
          <div class="p-5 space-y-3">
            <div class="h-3 bg-white/[0.05] rounded w-2/3"></div>
            <div class="h-2 bg-white/[0.03] rounded w-1/2"></div>
            <div class="flex justify-between items-center mt-5">
              <div class="h-5 bg-white/[0.05] rounded w-1/3"></div>
              <div class="h-8 bg-white/[0.05] rounded-xl w-1/4"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div
        v-else-if="filteredMenus.length === 0"
        class="py-28 text-center space-y-3"
      >
        <div class="w-14 h-14 rounded-2xl bg-[#111] border border-white/5 flex items-center justify-center mx-auto mb-4">
          <span class="text-2xl">🍽️</span>
        </div>
        <p class="font-sora text-xs font-bold uppercase tracking-widest text-zinc-600">Menu tidak tersedia</p>
        <p class="text-[11px] text-zinc-700 font-light">Coba kategori lain atau cek lagi nanti.</p>
      </div>

      <!-- Grid -->
      <div
        v-else
        class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5"
      >
        <div
          v-for="menu in filteredMenus"
          :key="menu.id"
          class="group relative bg-[#0d0d0d] border border-white/[0.06] rounded-2xl overflow-hidden flex flex-col transition-all duration-300 hover:border-white/[0.12]"
          :class="{ 'opacity-50': !menu.is_available }"
        >
          <!-- Foto -->
          <div class="w-full aspect-[4/3] bg-[#111] overflow-hidden relative">
            <img
              v-if="menu.image_url"
              :src="getMediaUrl(menu.image_url)"
              :alt="menu.name"
              class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-[1.06] pointer-events-none"
              loading="lazy"
            />
            <div
              v-else
              class="w-full h-full flex flex-col items-center justify-center gap-2"
            >
              <span class="text-3xl opacity-20">🍜</span>
              <span class="font-mono text-[9px] uppercase tracking-widest text-zinc-700">No Image</span>
            </div>

            <!-- Overlay gradient bawah foto -->
            <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent pointer-events-none"></div>

            <!-- Badge HABIS -->
            <div
              v-if="!menu.is_available"
              class="absolute top-3 left-3 z-10 bg-black/70 backdrop-blur-md border border-white/10 px-2.5 py-1 rounded-lg"
            >
              <span class="font-mono text-[9px] font-bold tracking-[0.2em] text-zinc-400 uppercase">Habis</span>
            </div>

            <!-- Kategori label -->
            <div class="absolute bottom-3 left-4">
              <span class="font-mono text-[9px] tracking-[0.15em] uppercase text-white/50">
                {{ menu.category_name }}
              </span>
            </div>
          </div>

          <!-- Info -->
          <div class="p-5 flex flex-col gap-4 flex-1">
            <!-- Nama + deskripsi -->
            <div class="flex-1 space-y-1.5">
              <h3 class="font-sora text-[13px] font-bold uppercase tracking-wide text-white leading-tight">
                {{ menu.name }}
              </h3>
              <p class="text-zinc-600 text-[11px] font-light leading-relaxed line-clamp-2">
                {{ menu.description || "Menu andalan spesial Masashimura." }}
              </p>
            </div>

            <!-- Harga + tombol -->
            <div class="flex items-center justify-between gap-3 pt-4 border-t border-white/[0.05]">
              <span class="font-mono text-[15px] font-bold text-amber-400 tracking-tight leading-none">
                {{ formatPrice(menu.price_web) }}
              </span>

              <button
                @click="addToCart(menu)"
                :disabled="!menu.is_available || !isStoreOpen"
                :class="[
                  'flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-[10px] font-sora font-bold uppercase tracking-widest transition-all duration-200',
                  menu.is_available
                    ? 'bg-[#DC2626] hover:bg-red-700 text-white active:scale-95'
                    : 'bg-[#1a1a1a] text-zinc-700 cursor-not-allowed border border-white/5'
                ]"
              >
                <Plus :size="11" />
                Tambah
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Info jumlah item -->
      <div v-if="!loading && filteredMenus.length > 0" class="mt-10 text-center">
        <span class="font-mono text-[9px] text-zinc-800 tracking-[0.3em] uppercase">
          {{ filteredMenus.length }} menu
        </span>
      </div>
    </div>

    <!-- ── FAB KERANJANG ─────────────────────────────────────────────────────── -->
    <transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="opacity-0 translate-y-3 scale-95"
      enter-to-class="opacity-100 translate-y-0 scale-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100 translate-y-0 scale-100"
      leave-to-class="opacity-0 translate-y-3 scale-95"
    >
      <button
        v-if="cartStore.cartItemCount > 0"
        @click="isCartOpen = true"
        class="fixed bottom-6 right-4 sm:bottom-8 sm:right-8 z-50 flex items-center gap-3 bg-[#DC2626] text-white pl-4 pr-5 py-3.5 rounded-2xl shadow-[0_12px_40px_rgba(220,38,38,0.35)] hover:bg-red-700 active:scale-95 transition-all duration-200"
      >
        <div class="relative">
          <ShoppingCart :size="16" />
          <span class="absolute -top-2 -right-2 bg-white text-[#DC2626] text-[8px] font-black w-4 h-4 rounded-full flex items-center justify-center leading-none">
            {{ cartStore.cartItemCount }}
          </span>
        </div>
        <span class="font-sora text-[10px] font-bold uppercase tracking-widest">Keranjang</span>
      </button>
    </transition>

    <!-- ── CART DRAWER ────────────────────────────────────────────────────────── -->
    <Cart v-if="isCartOpen" @close="isCartOpen = false" :format-price="formatPrice" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useCartStore } from "@/stores/cart"
import { useAuthStore } from "@/stores/auth"
import { menuAPI, getMediaUrl } from "@/api"
import { toast } from "vue-sonner"
import { ShoppingCart, Plus } from "lucide-vue-next"
import Cart from "@/components/ui/Cart.vue"
import { useStoreSettings } from "@/composables/useStoreSettings"

const cartStore = useCartStore()
const authStore = useAuthStore()
const menus      = ref([])
const loading    = ref(true)
const isCartOpen = ref(false)

const selectedCategory = ref("all")

const categories = computed(() => {
  const uniqueCats = [...new Set(menus.value.map(m => m.category_name).filter(Boolean))];
  return [
    { label: "Semua", value: "all" },
    ...uniqueCats.map(name => ({ label: name, value: name })),
  ];
});

const { isStoreOpen, closedMessage, fetchSettings } = useStoreSettings()
onMounted(() => {
  fetchMenus()
  fetchSettings()   // ← tambah ini
})

const selectCategory = (val) => { selectedCategory.value = val }

const getCategoryCount = (val) =>
  menus.value.filter(m => m.category_name === val).length

const fetchMenus = async () => {
  try {
    loading.value = true
    const { data } = await menuAPI.getAll()
    menus.value = data || []
  } catch {
    toast.error("Gagal memuat daftar menu.")
  } finally {
    loading.value = false
  }
}

const filteredMenus = computed(() => {
  // Menu tanpa kategori (category_name null) selalu disembunyikan dari customer
  const validMenus = menus.value.filter(m => m.category_name)

  const list = selectedCategory.value === "all"
    ? validMenus
    : validMenus.filter(m => m.category_name === selectedCategory.value)

  return [...list].sort((a, b) => b.is_available - a.is_available)
})

const addToCart = (menu) => {
  if (!isStoreOpen.value) return toast.error(closedMessage.value)  // ← tambah ini
  if (!menu.is_available) return toast.error("Menu ini sedang habis!")
  cartStore.addToCart(menu)
  toast.success(`${menu.name} ditambahkan! 🛒`)
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
</script>

<style scoped>
.scrollbar-none::-webkit-scrollbar { display: none; }
.scrollbar-none { -ms-overflow-style: none; scrollbar-width: none; }
</style>