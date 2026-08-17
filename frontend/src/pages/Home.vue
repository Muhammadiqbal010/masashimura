<template>
  <div class="min-h-screen bg-[#080808] text-white font-inter overflow-x-hidden selection:bg-red-600/30 selection:text-white">

    <!-- LOADING -->
    <div v-if="isLoading" class="h-screen w-screen flex flex-col justify-center items-center bg-[#080808] text-zinc-600 font-mono text-[10px] tracking-[0.4em] uppercase">
      <div class="w-4 h-4 border border-[#DC2626] border-t-transparent rounded-full animate-spin mb-4"></div>
      Loading
    </div>

    <template v-else>

      <!-- ═══════════════════════════════════════════
           1. HERO
      ═══════════════════════════════════════════ -->
      <section class="relative h-screen flex items-end overflow-hidden">

        <!-- Background full bleed -->
        <div class="absolute inset-0">
          <img
            :src="cms.hero_bg_image || defaultHeroBg"
            alt=""
            class="w-full h-full object-cover"
            :style="{ transform: `translateY(${scrollY * 0.12}px)` }"
          />
          <!-- Lapisan gelap kiri & bawah -->
          <div class="absolute inset-0 bg-gradient-to-r from-[#080808] via-[#080808]/70 to-transparent" />
          <div class="absolute inset-0 bg-gradient-to-t from-[#080808] via-transparent to-[#080808]/30" />
        </div>

        <!-- Teks hero — bottom-left anchored -->
        <div class="relative z-10 max-w-7xl w-full mx-auto px-6 sm:px-10 pb-20 grid grid-cols-1 lg:grid-cols-12 gap-8 items-end">
          <div class="lg:col-span-7 space-y-6">

            <!-- Eyebrow -->
            <div class="flex items-center gap-3">
              <span class="w-8 h-px bg-[#DC2626]"></span>
              <span class="font-mono text-[10px] tracking-[0.3em] text-[#DC2626] uppercase">Bekasi · Since 2024</span>
            </div>

            <!-- Headline -->
            <h1 class="font-sora text-5xl sm:text-7xl font-extrabold tracking-tight uppercase leading-[0.92] text-white whitespace-pre-line">
              {{ cms.hero_headline }}
            </h1>

            <p class="text-zinc-400 text-sm max-w-md font-light leading-relaxed">
              {{ cms.hero_subheadline }}
            </p>

            <div class="flex gap-4 pt-2">
              <router-link to="/menu"
                class="bg-[#DC2626] hover:bg-red-700 text-white font-sora text-[11px] uppercase tracking-[0.2em] px-8 py-4 font-bold transition-all duration-200 hover:-translate-y-0.5">
                Pesan Sekarang
              </router-link>
              <router-link to="/contact"
                class="border border-white/20 hover:border-white/50 text-white font-sora text-[11px] uppercase tracking-[0.2em] px-8 py-4 font-bold transition-all duration-200">
                Kontak Kami
              </router-link>
            </div>
          </div>

          <!-- Foto makanan — kotak kanan -->
          <div class="hidden lg:flex lg:col-span-5 justify-end items-end">
            <div class="relative w-72 aspect-square overflow-hidden border border-white/10">
              <img
                :src="cms.hero_food_image || defaultHeroFood"
                alt="Masashimura Signature Dish"
                class="w-full h-full object-cover"
              />
              <!-- Label pojok -->
              <div class="absolute bottom-0 left-0 right-0 bg-[#080808]/80 backdrop-blur-sm px-4 py-2.5 flex justify-between items-center border-t border-white/10">
                <span class="font-mono text-[9px] tracking-[0.25em] text-zinc-400 uppercase">Signature Dish</span>
                <span class="w-1.5 h-1.5 rounded-full bg-[#DC2626]"></span>
              </div>
            </div>
          </div>
        </div>

        <!-- Scroll indicator -->
        <div class="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1.5 opacity-30">
          <span class="font-mono text-[9px] tracking-[0.3em] uppercase text-zinc-500">Scroll</span>
          <div class="w-px h-10 bg-gradient-to-b from-zinc-500 to-transparent"></div>
        </div>
      </section>

      <!-- ═══════════════════════════════════════════
           2. MARQUEE
      ═══════════════════════════════════════════ -->
      <div class="border-y border-white/[0.06] bg-[#0a0a0a] overflow-hidden py-4 pointer-events-none">
        <div class="whitespace-nowrap flex animate-marquee">
          <span v-for="n in 6" :key="n"
            class="inline-block font-sora text-[11px] font-bold tracking-[0.35em] uppercase text-zinc-700 mx-10">
            {{ cms.marquee_text }}
          </span>
        </div>
      </div>

      <!-- ═══════════════════════════════════════════
           3. BEST SELLER
      ═══════════════════════════════════════════ -->
      <section class="py-32 px-6 sm:px-10 max-w-7xl mx-auto">

        <div class="flex items-end justify-between mb-16">
          <div class="space-y-3">
            <div class="flex items-center gap-3">
              <span class="w-6 h-px bg-[#DC2626]"></span>
              <span class="font-mono text-[10px] tracking-[0.3em] text-[#DC2626] uppercase">Most Ordered</span>
            </div>
            <h2 class="font-sora text-3xl sm:text-4xl font-extrabold uppercase tracking-tight">Menu Terlaris</h2>
          </div>
          <router-link to="/menu"
            class="hidden sm:flex items-center gap-2 font-mono text-[10px] tracking-[0.2em] uppercase text-zinc-500 hover:text-white transition group">
            Lihat Semua
            <span class="w-6 h-px bg-zinc-500 group-hover:w-10 group-hover:bg-white transition-all duration-300"></span>
          </router-link>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          <div
            v-for="(item, idx) in bestSellers"
            :key="idx"
            class="bg-[#080808] rounded-2xl overflow-hidden border border-white/5 group flex flex-col hover:-translate-y-1 hover:border-[#DC2626]/40 transition-all duration-300"
          >
            <!-- Foto -->
            <div class="relative w-full aspect-[4/3] shrink-0 overflow-hidden bg-zinc-900">
              <img
                :src="item.image"
                :alt="item.name"
                loading="lazy"
                class="w-full h-full object-cover"
              />
              <div class="absolute top-3 left-3 font-mono text-[10px] text-white/50 bg-black/40 px-1.5 py-0.5 rounded">
                {{ String(idx + 1).padStart(2,'0') }}
              </div>
            </div>

            <!-- Info -->
            <div class="p-5 flex flex-col gap-3 flex-1">
              <h3
                class="font-sora text-base font-bold uppercase tracking-wide text-white group-hover:text-[#DC2626] transition-colors">
                {{ item.name }}
              </h3>
              <p class="text-zinc-400 text-sm leading-relaxed flex-1 line-clamp-2">{{ item.desc }}</p>
              <div class="flex items-center justify-between pt-4 mt-2 border-t border-white/10">
                <span class="font-mono text-lg font-bold text-[#DC2626]">
                  Rp {{ item.price.toLocaleString('id-ID') }}
                </span>
                <router-link
                  to="/menu"
                  class="px-4 py-2 rounded-full bg-[#DC2626] text-white text-[10px] uppercase tracking-wider hover:bg-red-700 transition"
                >
                  Order
                </router-link>
              </div>
            </div>
          </div>

          <!-- Empty state -->
          <div v-if="bestSellers.length === 0"
            class="col-span-full py-20 text-center text-zinc-700 font-mono text-xs tracking-widest uppercase">
            Memuat menu...
          </div>
        </div>
      </section>

      <!-- ═══════════════════════════════════════════
           4. TENTANG MASASHIMURA
      ═══════════════════════════════════════════ -->
      <section class="py-32 border-t border-white/[0.06] bg-[#0a0a0a]">
        <div class="max-w-7xl mx-auto px-6 sm:px-10 grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">

          <!-- Foto outlet -->
          <div class="relative">
            <div class="aspect-square overflow-hidden">
              <img :src="cms.about_image || defaultAboutImage" alt="Suasana Masashimura" loading="lazy"
                class="w-full h-full object-cover grayscale-[15%] hover:grayscale-0 transition duration-700" />
            </div>
            <!-- Aksen garis merah pojok -->
            <div class="absolute -bottom-4 -right-4 w-20 h-20 border-b-2 border-r-2 border-[#DC2626]"></div>
            <div class="absolute -top-4 -left-4 w-20 h-20 border-t-2 border-l-2 border-[#DC2626]"></div>
          </div>

          <!-- Teks -->
          <div class="space-y-10">
            <div class="space-y-4">
              <div class="flex items-center gap-3">
                <span class="w-6 h-px bg-[#DC2626]"></span>
                <span class="font-mono text-[10px] tracking-[0.3em] text-[#DC2626] uppercase">Tentang Kami</span>
              </div>
              <h2 class="font-sora text-3xl sm:text-4xl font-extrabold uppercase tracking-tight leading-tight">
                Masashimura
              </h2>
              <p class="text-zinc-400 text-sm font-light leading-[1.9] max-w-md">{{ cms.about_text }}</p>
            </div>

            <!-- Metrics — horizontal rule style -->
            <div class="grid grid-cols-3 border border-white/[0.07] divide-x divide-white/[0.07]">
              <div class="px-6 py-5 space-y-1">
                <p class="font-sora text-2xl font-extrabold text-[#DC2626]">{{ cms.metric_1 }}</p>
                <p class="font-mono text-[9px] tracking-[0.25em] text-zinc-600 uppercase">Berdiri</p>
              </div>
              <div class="px-6 py-5 space-y-1">
                <p class="font-sora text-2xl font-extrabold text-white">{{ cms.metric_2 }}</p>
                <p class="font-mono text-[9px] tracking-[0.25em] text-zinc-600 uppercase">Varian Menu</p>
              </div>
              <div class="px-6 py-5 space-y-1">
                <p class="font-sora text-2xl font-extrabold text-amber-500">{{ cms.metric_3 }}</p>
                <p class="font-mono text-[9px] tracking-[0.25em] text-zinc-600 uppercase">Rating</p>
              </div>
            </div>

            <router-link to="/menu"
              class="inline-flex items-center gap-3 font-sora text-[11px] uppercase tracking-[0.2em] font-bold border-b border-[#DC2626] pb-1 text-white hover:text-[#DC2626] transition group">
              Lihat Semua Menu
              <span class="w-5 h-px bg-[#DC2626] group-hover:w-8 transition-all duration-300"></span>
            </router-link>
          </div>
        </div>
      </section>

      <!-- ═══════════════════════════════════════════
           5. BENTO GRID FASILITAS
      ═══════════════════════════════════════════ -->
      <section class="py-32 px-6 sm:px-10 max-w-7xl mx-auto">
        <div class="flex items-end justify-between mb-16">
          <div class="space-y-3">
            <div class="flex items-center gap-3">
              <span class="w-6 h-px bg-[#DC2626]"></span>
              <span class="font-mono text-[10px] tracking-[0.3em] text-[#DC2626] uppercase">Fasilitas</span>
            </div>
            <h2 class="font-sora text-3xl sm:text-4xl font-extrabold uppercase tracking-tight">Apa yang Lo Dapet</h2>
          </div>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-3 grid-flow-row-dense gap-3 max-w-4xl">
          <div v-for="(bento, i) in bentoFacilities" :key="i"
            :class="[
              bento.size === 'large'
                ? 'col-span-2 row-span-2 md:col-span-2 p-10 min-h-[260px]'
                : 'p-6 min-h-[120px]',
              'border border-white/[0.07] bg-[#0d0d0d] flex flex-col justify-between group hover:border-[#DC2626]/40 transition-all duration-300'
            ]"
          >
            <component
              :is="iconMap[bento.icon_name] || iconMap['Coffee']"
              :size="bento.size === 'large' ? 20 : 16"
              class="text-[#DC2626] opacity-70 group-hover:opacity-100 transition"
            />
            <span :class="[
              bento.size === 'large' ? 'text-xl' : 'text-xs',
              'font-sora font-bold uppercase tracking-wide text-zinc-300 group-hover:text-white transition-colors'
            ]">
              {{ bento.title }}
            </span>
          </div>
        </div>
      </section>

      <!-- ═══════════════════════════════════════════
           6. GALLERY (Diperbaiki — dense grid dinamis, filter kategori, lightbox)
      ═══════════════════════════════════════════ -->
      <section class="py-32 border-t border-white/[0.06] bg-[#0a0a0a]">
        <div class="max-w-7xl mx-auto px-6 sm:px-10">
          <div class="mb-10 space-y-3">
            <div class="flex items-center gap-3">
              <span class="w-6 h-px bg-[#DC2626]"></span>
              <span class="font-mono text-[10px] tracking-[0.3em] text-[#DC2626] uppercase">Dokumentasi</span>
            </div>
            <h2 class="font-sora text-3xl sm:text-4xl font-extrabold uppercase tracking-tight">Gallery</h2>
          </div>

          <!-- Filter kategori — cuma muncul kalau memang ada lebih dari 1 kategori nyata -->
          <div v-if="galleryCategories.length > 2" class="flex flex-wrap gap-2 mb-10">
            <button
              v-for="cat in galleryCategories"
              :key="cat"
              type="button"
              @click="setCategory(cat)"
              :class="[
                activeCategory === cat
                  ? 'bg-[#DC2626] border-[#DC2626] text-white'
                  : 'bg-transparent border-white/10 text-zinc-400 hover:border-white/30 hover:text-white',
                'px-4 py-2 rounded-full border font-mono text-[10px] tracking-[0.15em] uppercase transition-all cursor-pointer'
              ]"
            >
              {{ cat }}
            </button>
          </div>

          <!-- Dense grid: item pertama besar, sisanya kotak seragam — otomatis rapi berapa pun jumlah fotonya -->
          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 grid-flow-row-dense auto-rows-[140px] sm:auto-rows-[170px] gap-3">
            <button
              v-for="(img, i) in visibleGallery"
              :key="img.id ?? img.image_url"
              type="button"
              @click="openLightbox(i)"
              :class="[
                i === 0 ? 'col-span-2 row-span-2' : '',
                'relative overflow-hidden group text-left bg-zinc-900 border-0 p-0 cursor-pointer'
              ]"
            >
              <img :src="img.image_url" :alt="img.title || 'Dokumentasi Masashimura'" loading="lazy"
                class="w-full h-full object-cover grayscale-[15%] group-hover:grayscale-0 group-hover:scale-105 transition-all duration-700" />
              <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-black/0 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-4">
                <div class="space-y-0.5">
                  <p class="font-sora text-[10px] sm:text-xs font-bold uppercase tracking-wider text-white line-clamp-1">{{ img.title || 'Masashimura' }}</p>
                  <p v-if="img.category" class="font-mono text-[9px] tracking-[0.2em] text-zinc-400 uppercase">{{ img.category }}</p>
                </div>
              </div>
              <div class="absolute top-3 right-3 w-7 h-7 rounded-full bg-black/50 border border-white/10 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <Expand :size="13" class="text-white" />
              </div>
            </button>

            <div v-if="visibleGallery.length === 0"
              class="col-span-full py-20 text-center text-zinc-700 font-mono text-xs tracking-widest uppercase border border-dashed border-white/10">
              Belum ada foto.
            </div>
          </div>

          <!-- Muat lebih banyak -->
          <div v-if="filteredGallery.length > visibleGallery.length" class="flex justify-center mt-10">
            <button type="button" @click="galleryLimit += 8"
              class="font-mono text-[10px] tracking-[0.25em] uppercase text-zinc-500 hover:text-white border border-white/10 hover:border-white/30 px-6 py-3 transition-all cursor-pointer">
              Muat Lebih Banyak
            </button>
          </div>
        </div>
      </section>

      <!-- LIGHTBOX GALLERY -->
      <transition name="lightbox-fade">
        <div v-if="lightboxIndex !== null"
          class="fixed inset-0 z-[60] bg-black/95 backdrop-blur-sm flex items-center justify-center p-4 sm:p-10"
          @click.self="closeLightbox"
        >
          <button type="button" @click="closeLightbox"
            class="absolute top-5 right-5 sm:top-8 sm:right-8 w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 flex items-center justify-center text-white transition cursor-pointer">
            <X :size="18" />
          </button>

          <button v-if="visibleGallery.length > 1" type="button" @click.stop="prevImage"
            class="absolute left-3 sm:left-8 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 flex items-center justify-center text-white transition cursor-pointer">
            <ChevronLeft :size="20" />
          </button>
          <button v-if="visibleGallery.length > 1" type="button" @click.stop="nextImage"
            class="absolute right-3 sm:right-8 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 flex items-center justify-center text-white transition cursor-pointer">
            <ChevronRight :size="20" />
          </button>

          <div class="max-w-4xl w-full space-y-4" @click.stop>
            <div class="max-h-[75vh] flex items-center justify-center overflow-hidden">
              <img :src="currentLightboxImage?.image_url" :alt="currentLightboxImage?.title || 'Masashimura'"
                class="max-h-[75vh] max-w-full object-contain" />
            </div>
            <div class="text-center space-y-1">
              <p class="font-sora text-sm font-bold uppercase tracking-wider text-white">{{ currentLightboxImage?.title || 'Masashimura' }}</p>
              <p v-if="currentLightboxImage?.category" class="font-mono text-[9px] tracking-[0.25em] text-zinc-500 uppercase">{{ currentLightboxImage.category }}</p>
            </div>
          </div>
        </div>
      </transition>

      <!-- ═══════════════════════════════════════════
           7. REVIEW
      ═══════════════════════════════════════════ -->
      <section class="py-32 px-6 sm:px-10 max-w-4xl mx-auto">
        <div class="mb-16 space-y-3">
          <div class="flex items-center gap-3">
            <span class="w-6 h-px bg-[#DC2626]"></span>
            <span class="font-mono text-[10px] tracking-[0.3em] text-[#DC2626] uppercase">Kata Mereka</span>
          </div>
          <h2 class="font-sora text-3xl sm:text-4xl font-extrabold uppercase tracking-tight">Review Pelanggan</h2>
        </div>

        <div class="relative min-h-[180px]">
          <transition-group name="review-fade" tag="div" class="w-full">
            <div v-for="(review, i) in reviews" v-show="i === currentReviewIndex" :key="i"
              class="absolute inset-0 border-l-2 border-[#DC2626] pl-8 space-y-4">
              <p class="text-zinc-300 text-base sm:text-lg font-sora font-light italic leading-relaxed max-w-2xl">
                "{{ review.text }}"
              </p>
              <div class="flex items-center gap-3">
                <span class="w-4 h-px bg-zinc-600"></span>
                <span class="font-mono text-[10px] tracking-[0.2em] text-zinc-400 uppercase">{{ review.name }}</span>
                <span class="font-mono text-[10px] text-zinc-700">· {{ review.status }}</span>
              </div>
            </div>
          </transition-group>
        </div>

        <!-- Dot indicator -->
        <div class="flex gap-2 mt-12">
          <button v-for="(r, i) in reviews" :key="i" @click="currentReviewIndex = i"
            :class="[
              'h-px transition-all duration-300',
              i === currentReviewIndex ? 'w-8 bg-[#DC2626]' : 'w-4 bg-zinc-700 hover:bg-zinc-500'
            ]"
          />
        </div>
      </section>

      <!-- ═══════════════════════════════════════════
           8. CTA
      ═══════════════════════════════════════════ -->
      <section class="border-t border-white/[0.06] bg-[#0a0a0a]">
        <div class="max-w-7xl mx-auto px-6 sm:px-10 py-32 grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div class="space-y-6">
            <div class="flex items-center gap-3">
              <span class="w-6 h-px bg-[#DC2626]"></span>
              <span class="font-mono text-[10px] tracking-[0.3em] text-[#DC2626] uppercase">Yuk Order</span>
            </div>
            <h2 class="font-sora text-4xl sm:text-6xl font-extrabold uppercase tracking-tight leading-[0.9]">
              Udah<br/>Laper?
            </h2>
            <p class="text-zinc-500 text-sm font-light max-w-xs leading-relaxed">
              Pilih menu favorit dan nikmati langsung di kedai atau melalui web ordering.
            </p>
          </div>
          <div class="flex flex-col sm:flex-row gap-4">
            <router-link to="/menu"
              class="bg-[#DC2626] hover:bg-red-700 text-white font-sora text-[11px] uppercase tracking-[0.2em] px-10 py-5 font-bold transition-all duration-200 hover:-translate-y-0.5 text-center">
              Pesan via Web
            </router-link>
            <router-link to="/contact"
              class="border border-white/20 hover:border-white/50 text-white font-sora text-[11px] uppercase tracking-[0.2em] px-10 py-5 font-bold transition-all duration-200 text-center">
              Hubungi Kami
            </router-link>
          </div>
        </div>
      </section>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue"
import {
  Coffee, Wifi, Zap, Utensils, DollarSign, Moon, Shield, Tv,
  Music, Gamepad2, Beer, BatteryCharging, Heart, Award, Smartphone,
  Expand, X, ChevronLeft, ChevronRight
} from "lucide-vue-next"
import apiClient from "@/api/client"

const isLoading          = ref(true)
const scrollY            = ref(0)
const currentReviewIndex = ref(0)
let   reviewInterval     = null

const cms = ref({
  hero_headline:    "",
  hero_subheadline: "",
  hero_bg_image:    null,
  hero_food_image:  null,
  marquee_text:     "",
  about_text:       "",
  about_image:      null,
  metric_1: "", metric_2: "", metric_3: ""
})

const defaultHeroBg    = "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?q=80&w=1920"
const defaultHeroFood  = "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?q=80&w=800"
const defaultAboutImage = "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?q=80&w=1000"

const bestSellers    = ref([])
const bentoFacilities = ref([])
const galleryData    = ref([])
const reviews        = ref([])

const iconMap = {
  Coffee, Wifi, Zap, Utensils, DollarSign, Moon, Shield, Tv,
  Music, Gamepad2, Beer, BatteryCharging, Heart, Award, Smartphone
}

// ── Gallery: filter kategori + pagination + lightbox ──────────────────────
const activeCategory = ref("Semua")
const galleryLimit    = ref(8)
const lightboxIndex   = ref(null)

// Ambil daftar kategori unik dari data galeri (hasilnya konsisten walau data berubah)
const galleryCategories = computed(() => {
  const cats = new Set(galleryData.value.map(g => g.category).filter(Boolean))
  return ["Semua", ...cats]
})

const filteredGallery = computed(() => {
  if (activeCategory.value === "Semua") return galleryData.value
  return galleryData.value.filter(g => g.category === activeCategory.value)
})

// Grid dense butuh array terpotong biar tombol "Muat Lebih Banyak" konsisten
const visibleGallery = computed(() => filteredGallery.value.slice(0, galleryLimit.value))

const currentLightboxImage = computed(() =>
  lightboxIndex.value !== null ? visibleGallery.value[lightboxIndex.value] : null
)

const setCategory = (cat) => {
  activeCategory.value = cat
  galleryLimit.value = 8
}

const openLightbox  = (i) => { lightboxIndex.value = i }
const closeLightbox = () => { lightboxIndex.value = null }

const nextImage = () => {
  if (lightboxIndex.value === null || visibleGallery.value.length === 0) return
  lightboxIndex.value = (lightboxIndex.value + 1) % visibleGallery.value.length
}
const prevImage = () => {
  if (lightboxIndex.value === null || visibleGallery.value.length === 0) return
  lightboxIndex.value = (lightboxIndex.value - 1 + visibleGallery.value.length) % visibleGallery.value.length
}

const handleLightboxKeydown = (e) => {
  if (lightboxIndex.value === null) return
  if (e.key === "Escape")     closeLightbox()
  if (e.key === "ArrowRight") nextImage()
  if (e.key === "ArrowLeft")  prevImage()
}

// ── Data fetchers ─────────────────────────────────────────────────────────
const fetchCMSData = async () => {
  try {
    const { data: d } = await apiClient.get("/homepage/config/current/")
    cms.value = {
      hero_headline:    d.hero_headline?.trim()    || "Warkop Level Up\nMasashimura",
      hero_subheadline: d.hero_subheadline?.trim() || "Tempat nongkrong kasual modern di Bekasi dengan cita rasa nikmat.",
      hero_bg_image:    d.hero_bg_image    || null,
      hero_food_image:  d.hero_food_image  || null,
      marquee_text:     d.marquee_text?.trim()     || "MASA SIH MURAH? • WARKOP EVOLUTION • GOOD FOOD • GOOD VIBES • SINCE 2024",
      about_text:       d.about_text?.trim()       || "Masashimura adalah usaha kuliner asal Bekasi yang berdiri sejak 2024. Mengusung konsep tempat makan kasual yang nyaman, kami hadir buat lo yang mau nongkrong sambil menikmati makanan dengan harga bersahabat.",
      about_image:      d.about_image || null,
      metric_1: d.metric_1?.trim() || "2024",
      metric_2: d.metric_2?.trim() || "50+",
      metric_3: d.metric_3?.trim() || "★★★★★",
    }
  } catch (err) {
    console.error("CMS fallback:", err)
  }
}

const fetchBestSellers = async () => {
  try {
    const { data } = await apiClient.get("/menus/bestsellers/")
    if (Array.isArray(data) && data.length > 0) {
      bestSellers.value = data.map(item => ({
        name:  item.name,
        desc:  item.description || "Menu favorit pilihan squad Masashimura.",
        price: Number(item.price),
        image: item.image_url || defaultHeroFood,
      }))
    }
  } catch (err) {
    console.error("Best sellers:", err)
  }
}

const fallbackReviews = [
  { name: "Irfan Setya",  status: "Maps Local Guide", text: "WiFi kenceng, makanannya enak, harga mahasiswa — Masashimura jawara nongkrong di Bekasi!" },
  { name: "Helen S",      status: "Maps Reviewer",    text: "Tiap kali nyari tempat yang gak bising tapi estetik minimalis, selalu balik ke Masashimura." },
  { name: "Dimas R",      status: "Regular Customer", text: "Beef yakiniku-nya gak ada lawannya di harga segitu. Seriously underrated." },
]

const fetchGoogleReviews = async () => {
  try {
    const { data } = await apiClient.get("/homepage/reviews/maps/")
    reviews.value = data?.length > 0 ? data : fallbackReviews
  } catch {
    reviews.value = fallbackReviews
  }
}

const fallbackBento = [
  { title: "Nyaman Sepanjang Hari", icon_name: "Coffee", size: "large" },
  { title: "Free WiFi",             icon_name: "Wifi",   size: "normal" },
  { title: "Banyak Colokan",        icon_name: "Zap",    size: "normal" },
  { title: "Buka Sampai Malam",     icon_name: "Moon",   size: "normal" },
]

const fallbackGallery = [
  { title: "Suasana Kedai", image_url: defaultHeroBg,   category: "Suasana Kedai" },
  { title: "Menu Andalan",  image_url: defaultHeroFood,  category: "Best Seller" },
]

const fetchBentoAndGallery = async () => {
  try {
    const [b, g] = await Promise.all([
      apiClient.get("/homepage/bento/"),
      apiClient.get("/homepage/gallery/"),
    ])
    bentoFacilities.value = b.data?.length > 0 ? b.data : fallbackBento
    galleryData.value     = g.data?.length > 0 ? g.data : fallbackGallery
  } catch {
    bentoFacilities.value = fallbackBento
    galleryData.value     = fallbackGallery
  }
}

// ── Scroll parallax ──────────────────────────────────────────────────────
const handleScroll = () => { scrollY.value = window.scrollY }

// ── Lifecycle ────────────────────────────────────────────────────────────
onMounted(async () => {
  window.addEventListener("scroll", handleScroll, { passive: true })
  window.addEventListener("keydown", handleLightboxKeydown)
  await Promise.all([fetchCMSData(), fetchBestSellers(), fetchGoogleReviews(), fetchBentoAndGallery()])
  isLoading.value = false
  reviewInterval = setInterval(() => {
    if (reviews.value.length > 0)
      currentReviewIndex.value = (currentReviewIndex.value + 1) % reviews.value.length
  }, 5000)
})

onUnmounted(() => {
  window.removeEventListener("scroll", handleScroll)
  window.removeEventListener("keydown", handleLightboxKeydown)
  if (reviewInterval) clearInterval(reviewInterval)
})
</script>

<style scoped>
@keyframes marquee {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
.animate-marquee {
  width: max-content;
  animation: marquee 40s linear infinite;
}

.review-fade-enter-active,
.review-fade-leave-active {
  transition: opacity 0.5s ease, transform 0.5s ease;
}
.review-fade-enter-from { opacity: 0; transform: translateY(8px); }
.review-fade-leave-to   { opacity: 0; transform: translateY(-8px); }
.review-fade-leave-active { position: absolute; width: 100%; }

.lightbox-fade-enter-active,
.lightbox-fade-leave-active {
  transition: opacity 0.25s ease;
}
.lightbox-fade-enter-from,
.lightbox-fade-leave-to {
  opacity: 0;
}
</style>