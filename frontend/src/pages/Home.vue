<template>
  <div class="min-h-screen bg-[#080808] text-white font-inter overflow-x-hidden selection:bg-red-600/30 selection:text-white">

    <!-- LOADING -->
    <div v-if="isLoading" class="h-screen w-screen flex flex-col justify-center items-center gap-5 bg-[#080808]">
      <span class="font-sora text-xl font-extrabold uppercase tracking-[0.3em] text-white/80 animate-pulse">Masashimura</span>
      <div class="w-24 h-px bg-white/10 overflow-hidden">
        <div class="load-bar h-full w-1/2 bg-[#DC2626]"></div>
      </div>
    </div>

    <template v-else>

      <!-- ═══════════════════════════════════════════
           1. HERO
      ═══════════════════════════════════════════ -->
      <section class="hero relative flex items-end overflow-hidden">

        <!-- Background full bleed (di-oversize supaya parallax nggak bikin celah) -->
        <div class="absolute inset-0">
          <div
            class="absolute inset-x-0 -top-[12%] h-[124%] will-change-transform"
            :style="{ transform: `translate3d(0, ${parallaxY}px, 0)` }"
          >
            <img
              :src="cms.hero_bg_image || defaultHeroBg"
              alt=""
              fetchpriority="high"
              decoding="async"
              class="w-full h-full object-cover"
            />
          </div>
          <!-- Overlay: gelap merata + gelap sisi kiri di desktop -->
          <div class="absolute inset-0 bg-gradient-to-t from-[#080808] via-[#080808]/55 to-[#080808]/50"></div>
          <div class="absolute inset-0 hidden lg:block bg-gradient-to-r from-[#080808] via-[#080808]/65 to-transparent"></div>
          <div class="hero-glow absolute inset-0 pointer-events-none"></div>
        </div>

        <!-- Konten hero — anchored bawah -->
        <div class="relative z-10 w-full max-w-7xl mx-auto px-6 sm:px-10 pt-32 pb-16 sm:pb-20 lg:pb-24 grid grid-cols-1 lg:grid-cols-12 gap-10 items-end">
          <div class="lg:col-span-7 space-y-6 sm:space-y-7">

            <!-- Eyebrow -->
            <div class="hero-in flex items-center gap-3" style="--d: 0ms">
              <span class="w-8 h-px bg-[#DC2626]"></span>
              <span class="font-mono text-[10px] tracking-[0.3em] text-[#DC2626] uppercase">Bekasi · Since 2024</span>
            </div>

            <!-- Headline: baris terakhir diberi aksen merah -->
            <h1 class="hero-title hero-in font-sora font-extrabold tracking-tight uppercase leading-[0.95] text-white break-words" style="--d: 120ms">
              <span
                v-for="(line, i) in headlineLines"
                :key="i"
                class="block"
                :class="line.accent ? 'text-[#DC2626]' : ''"
              >{{ line.text }}</span>
            </h1>

            <p class="hero-in text-zinc-300 text-sm sm:text-base max-w-md font-light leading-relaxed" style="--d: 240ms">
              {{ cms.hero_subheadline }}
            </p>

            <div class="hero-in flex flex-col sm:flex-row gap-3 sm:gap-4 pt-2" style="--d: 360ms">
              <router-link to="/menu"
                class="group inline-flex items-center justify-center gap-3 bg-[#DC2626] hover:bg-red-700 text-white font-sora text-[11px] uppercase tracking-[0.2em] px-8 py-4 font-bold transition-all duration-200 hover:-translate-y-0.5">
                Pesan Sekarang
                <ArrowRight :size="14" class="transition-transform duration-200 group-hover:translate-x-1" />
              </router-link>
              <router-link to="/contact"
                class="inline-flex items-center justify-center border border-white/25 hover:border-white/60 hover:bg-white/5 text-white font-sora text-[11px] uppercase tracking-[0.2em] px-8 py-4 font-bold transition-all duration-200">
                Kontak Kami
              </router-link>
            </div>
          </div>

          <!-- Foto makanan — kartu kanan (desktop) -->
          <div class="hero-in hidden lg:flex lg:col-span-5 justify-end items-end" style="--d: 300ms">
            <div class="relative w-72">
              <div class="absolute -top-3 -right-3 w-full h-full border border-[#DC2626]/40"></div>
              <div class="relative aspect-square overflow-hidden border border-white/10 bg-zinc-900">
                <img
                  :src="cms.hero_food_image || defaultHeroFood"
                  alt="Masashimura Signature Dish"
                  class="w-full h-full object-cover"
                />
                <div class="absolute bottom-0 left-0 right-0 bg-[#080808]/80 backdrop-blur-sm px-4 py-2.5 flex justify-between items-center border-t border-white/10">
                  <span class="font-mono text-[9px] tracking-[0.25em] text-zinc-400 uppercase">Signature Dish</span>
                  <span class="w-1.5 h-1.5 rounded-full bg-[#DC2626] animate-pulse"></span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Scroll indicator (disembunyikan di mobile supaya nggak nabrak tombol) -->
        <div class="hidden sm:flex absolute bottom-6 left-1/2 -translate-x-1/2 flex-col items-center gap-1.5 opacity-40 pointer-events-none">
          <span class="font-mono text-[9px] tracking-[0.3em] uppercase text-zinc-400">Scroll</span>
          <div class="w-px h-8 bg-gradient-to-b from-zinc-400 to-transparent"></div>
        </div>
      </section>

      <!-- ═══════════════════════════════════════════
           2. MARQUEE
      ═══════════════════════════════════════════ -->
      <div class="marquee-wrap border-y border-white/[0.06] bg-[#0a0a0a] overflow-hidden py-4" aria-hidden="true">
        <div class="animate-marquee flex">
          <div v-for="g in 2" :key="g" class="flex shrink-0 items-center">
            <template v-for="m in 4" :key="m">
              <span class="font-sora text-[11px] font-bold tracking-[0.35em] uppercase text-zinc-600 mx-8 whitespace-nowrap">
                {{ cms.marquee_text }}
              </span>
              <span class="w-1.5 h-1.5 rotate-45 bg-[#DC2626] shrink-0"></span>
            </template>
          </div>
        </div>
      </div>

      <!-- ═══════════════════════════════════════════
           3. BEST SELLER
      ═══════════════════════════════════════════ -->
      <section v-reveal class="py-20 sm:py-28 lg:py-32 px-6 sm:px-10 max-w-7xl mx-auto">

        <div class="flex items-end justify-between mb-10 sm:mb-14">
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

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
          <router-link
            v-for="(item, idx) in topBestSellers"
            :key="idx"
            to="/menu"
            class="group flex flex-col bg-[#0d0d0d] border border-white/[0.07] overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:border-[#DC2626]/50 hover:shadow-[0_24px_40px_-24px_rgba(220,38,38,0.4)]"
          >
            <!-- Foto -->
            <div class="relative w-full aspect-[4/3] shrink-0 overflow-hidden bg-zinc-900">
              <div class="w-full h-full transition-transform duration-700 ease-out group-hover:scale-105">
                <img
                  v-blur-img
                  :src="item.image"
                  :alt="item.name"
                  loading="lazy"
                  class="w-full h-full object-cover"
                />
              </div>
              <div class="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-black/60 to-transparent pointer-events-none"></div>
              <span class="absolute top-3 left-3 font-mono text-[10px] tracking-widest text-white/80 bg-black/50 backdrop-blur-sm px-2 py-1">
                {{ String(idx + 1).padStart(2, '0') }}
              </span>
              <span v-if="idx === 0"
                class="absolute top-3 right-3 font-mono text-[9px] tracking-[0.2em] uppercase bg-[#DC2626] text-white px-2 py-1">
                Best Seller
              </span>
            </div>

            <!-- Info -->
            <div class="p-5 sm:p-6 flex flex-col gap-3 flex-1">
              <h3 class="font-sora text-base font-bold uppercase tracking-wide text-white group-hover:text-[#DC2626] transition-colors line-clamp-2">
                {{ item.name }}
              </h3>
              <p class="text-zinc-400 text-sm leading-relaxed flex-1 line-clamp-2">{{ item.desc }}</p>
              <div class="flex items-center justify-between pt-4 mt-1 border-t border-white/10">
                <span class="font-mono text-lg font-bold text-[#DC2626]">
                  Rp {{ item.price.toLocaleString('id-ID') }}
                </span>
                <span class="inline-flex items-center gap-2 bg-[#DC2626] group-hover:bg-red-700 text-white font-sora text-[10px] uppercase tracking-[0.18em] font-bold px-4 py-2.5 transition-colors">
                  Order
                  <ArrowRight :size="12" class="transition-transform duration-200 group-hover:translate-x-0.5" />
                </span>
              </div>
            </div>
          </router-link>

          <!-- Empty state -->
          <div v-if="bestSellers.length === 0"
            class="col-span-full py-20 text-center text-zinc-600 font-mono text-xs tracking-widest uppercase border border-dashed border-white/10">
            Menu belum tersedia saat ini.
          </div>
        </div>

        <!-- Link "lihat semua" untuk mobile -->
        <div class="sm:hidden mt-8">
          <router-link to="/menu"
            class="flex items-center justify-center gap-3 w-full border border-white/20 hover:border-white/50 text-white font-sora text-[11px] uppercase tracking-[0.2em] px-6 py-4 font-bold transition">
            Lihat Semua Menu
            <ArrowRight :size="14" />
          </router-link>
        </div>
      </section>

      <!-- ═══════════════════════════════════════════
           4. TENTANG MASASHIMURA
      ═══════════════════════════════════════════ -->
      <section v-reveal class="py-20 sm:py-28 lg:py-32 border-t border-white/[0.06] bg-[#0a0a0a]">
        <div class="max-w-7xl mx-auto px-6 sm:px-10 grid grid-cols-1 lg:grid-cols-2 gap-14 lg:gap-20 items-center">

          <!-- Foto outlet -->
          <div class="relative">
            <div class="aspect-square overflow-hidden bg-zinc-900">
              <img v-blur-img :src="cms.about_image || defaultAboutImage" alt="Suasana Masashimura" loading="lazy"
                class="w-full h-full object-cover grayscale-[15%] hover:grayscale-0" />
            </div>
            <!-- Aksen garis merah pojok -->
            <div class="absolute -bottom-3 -right-3 sm:-bottom-4 sm:-right-4 w-16 h-16 sm:w-20 sm:h-20 border-b-2 border-r-2 border-[#DC2626] pointer-events-none"></div>
            <div class="absolute -top-3 -left-3 sm:-top-4 sm:-left-4 w-16 h-16 sm:w-20 sm:h-20 border-t-2 border-l-2 border-[#DC2626] pointer-events-none"></div>
          </div>

          <!-- Teks -->
          <div class="space-y-8 sm:space-y-10">
            <div class="space-y-4">
              <div class="flex items-center gap-3">
                <span class="w-6 h-px bg-[#DC2626]"></span>
                <span class="font-mono text-[10px] tracking-[0.3em] text-[#DC2626] uppercase">Tentang Kami</span>
              </div>
              <h2 class="font-sora text-3xl sm:text-4xl font-extrabold uppercase tracking-tight leading-tight">
                Masashimura
              </h2>
              <p class="text-zinc-400 text-sm sm:text-[15px] font-light leading-[1.9] max-w-md">{{ cms.about_text }}</p>
            </div>

            <!-- Metrics -->
            <div ref="metricsRef" class="grid grid-cols-3 border border-white/[0.07] divide-x divide-white/[0.07] bg-[#080808]/40">
              <div class="px-3 sm:px-6 py-5 space-y-1">
                <p class="font-sora text-xl sm:text-2xl font-extrabold text-[#DC2626] leading-tight">{{ metricDisplays.m1 }}</p>
                <p class="font-mono text-[9px] tracking-[0.2em] sm:tracking-[0.25em] text-zinc-500 uppercase">Berdiri</p>
              </div>
              <div class="px-3 sm:px-6 py-5 space-y-1">
                <p class="font-sora text-xl sm:text-2xl font-extrabold text-white leading-tight">{{ metricDisplays.m2 }}</p>
                <p class="font-mono text-[9px] tracking-[0.2em] sm:tracking-[0.25em] text-zinc-500 uppercase">Varian Menu</p>
              </div>
              <div class="px-3 sm:px-6 py-5 space-y-1">
                <p class="font-sora font-extrabold text-amber-500 leading-tight whitespace-nowrap"
                  :class="metric3IsStars ? 'text-[0.9rem] sm:text-2xl tracking-tighter pt-1 sm:pt-0' : 'text-xl sm:text-2xl'">
                  {{ cms.metric_3 }}
                </p>
                <p class="font-mono text-[9px] tracking-[0.2em] sm:tracking-[0.25em] text-zinc-500 uppercase">Rating</p>
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
           5. BENTO FASILITAS (tanpa sel kosong, selaras dgn lebar section lain)
      ═══════════════════════════════════════════ -->
      <section v-reveal class="py-20 sm:py-28 lg:py-32 px-6 sm:px-10 max-w-7xl mx-auto">
        <div class="mb-10 sm:mb-14 space-y-3">
          <div class="flex items-center gap-3">
            <span class="w-6 h-px bg-[#DC2626]"></span>
            <span class="font-mono text-[10px] tracking-[0.3em] text-[#DC2626] uppercase">Fasilitas</span>
          </div>
          <h2 class="font-sora text-3xl sm:text-4xl font-extrabold uppercase tracking-tight">Apa yang Lo Dapet</h2>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-3">

          <!-- Kartu besar (featured) -->
          <div v-if="bentoLarge.length" class="lg:col-span-5 flex flex-col gap-3">
            <div
              v-for="(bento, i) in bentoLarge"
              :key="'l' + i"
              class="group relative flex-1 min-h-[220px] sm:min-h-[260px] overflow-hidden border border-white/[0.07] bg-[#0d0d0d] p-8 sm:p-10 flex flex-col justify-between hover:border-[#DC2626]/40 transition-colors duration-300"
            >
              <div class="pointer-events-none absolute -right-10 -bottom-10 text-[#DC2626] opacity-[0.06] group-hover:opacity-[0.12] transition-opacity duration-500">
                <component :is="getIcon(bento.icon_name)" :size="220" :stroke-width="1" />
              </div>
              <div class="relative w-12 h-12 flex items-center justify-center border border-[#DC2626]/40 bg-[#DC2626]/10 text-[#DC2626]">
                <component :is="getIcon(bento.icon_name)" :size="22" />
              </div>
              <span class="relative font-sora text-2xl sm:text-3xl font-extrabold uppercase tracking-tight leading-tight text-white">
                {{ bento.title }}
              </span>
            </div>
          </div>

          <!-- Kartu kecil -->
          <div
            class="grid grid-cols-2 gap-3 auto-rows-fr"
            :class="bentoLarge.length ? 'lg:col-span-7' : 'lg:col-span-12'"
          >
            <div
              v-for="(bento, i) in bentoSmall"
              :key="'s' + i"
              class="group p-5 sm:p-6 min-h-[112px] sm:min-h-[130px] border border-white/[0.07] bg-[#0d0d0d] flex flex-col justify-between gap-6 hover:border-[#DC2626]/40 hover:bg-[#101010] transition-all duration-300"
              :class="isBentoOrphan(i) ? 'col-span-2' : ''"
            >
              <component
                :is="getIcon(bento.icon_name)"
                :size="18"
                class="text-[#DC2626] opacity-70 group-hover:opacity-100 transition"
              />
              <span class="font-sora text-xs sm:text-sm font-bold uppercase tracking-wide text-zinc-300 group-hover:text-white transition-colors">
                {{ bento.title }}
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- ═══════════════════════════════════════════
           6. GALLERY
      ═══════════════════════════════════════════ -->
      <section v-reveal class="py-20 sm:py-28 lg:py-32 border-t border-white/[0.06] bg-[#0a0a0a]">
        <div class="max-w-7xl mx-auto px-6 sm:px-10">
          <div class="mb-8 sm:mb-10 space-y-3">
            <div class="flex items-center gap-3">
              <span class="w-6 h-px bg-[#DC2626]"></span>
              <span class="font-mono text-[10px] tracking-[0.3em] text-[#DC2626] uppercase">Dokumentasi</span>
            </div>
            <h2 class="font-sora text-3xl sm:text-4xl font-extrabold uppercase tracking-tight">Gallery</h2>
          </div>

          <!-- Filter kategori — scroll horizontal di mobile, muncul cuma kalau ada >1 kategori nyata -->
          <div v-if="galleryCategories.length > 2"
            class="no-scrollbar flex gap-2 mb-8 sm:mb-10 overflow-x-auto sm:flex-wrap -mx-6 px-6 sm:mx-0 sm:px-0 pb-1">
            <button
              v-for="cat in galleryCategories"
              :key="cat"
              type="button"
              @click="setCategory(cat)"
              :class="[
                activeCategory === cat
                  ? 'bg-[#DC2626] border-[#DC2626] text-white'
                  : 'bg-transparent border-white/10 text-zinc-400 hover:border-white/30 hover:text-white',
                'shrink-0 whitespace-nowrap px-4 py-2.5 border font-mono text-[10px] tracking-[0.15em] uppercase transition-all cursor-pointer'
              ]"
            >
              {{ cat }}
            </button>
          </div>

          <!-- Grid dense: item pertama jadi featured hanya kalau fotonya cukup banyak -->
          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 grid-flow-row-dense auto-rows-[150px] sm:auto-rows-[180px] gap-2 sm:gap-3">
            <button
              v-for="(img, i) in visibleGallery"
              :key="img.id ?? img.image_url"
              type="button"
              :aria-label="'Buka foto: ' + (img.title || 'Masashimura')"
              @click="openLightbox(i)"
              :class="[
                isFeatured(i) ? 'col-span-2 row-span-2' : '',
                'relative overflow-hidden group text-left bg-zinc-900 border-0 p-0 cursor-pointer'
              ]"
            >
              <div class="w-full h-full transition-transform duration-700 ease-out group-hover:scale-105">
                <img v-blur-img :src="img.image_url" :alt="img.title || 'Dokumentasi Masashimura'" loading="lazy"
                  class="w-full h-full object-cover grayscale-[15%] group-hover:grayscale-0" />
              </div>
              <div class="absolute inset-0 bg-gradient-to-t from-black/75 via-black/0 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-3 sm:p-4">
                <div class="space-y-0.5 min-w-0">
                  <p class="font-sora text-[10px] sm:text-xs font-bold uppercase tracking-wider text-white line-clamp-1">{{ img.title || 'Masashimura' }}</p>
                  <p v-if="img.category" class="font-mono text-[9px] tracking-[0.2em] text-zinc-300 uppercase">{{ img.category }}</p>
                </div>
              </div>
              <div class="absolute top-2.5 right-2.5 sm:top-3 sm:right-3 w-7 h-7 rounded-full bg-black/50 border border-white/10 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <Expand :size="13" class="text-white" />
              </div>
            </button>

            <div v-if="visibleGallery.length === 0"
              class="col-span-full row-span-2 flex items-center justify-center text-center text-zinc-600 font-mono text-xs tracking-widest uppercase border border-dashed border-white/10">
              Belum ada foto.
            </div>
          </div>

          <!-- Muat lebih banyak -->
          <div v-if="filteredGallery.length > visibleGallery.length" class="flex justify-center mt-10">
            <button type="button" @click="galleryLimit += 8"
              class="font-mono text-[10px] tracking-[0.25em] uppercase text-zinc-400 hover:text-white border border-white/10 hover:border-white/30 px-6 py-3.5 transition-all cursor-pointer">
              Muat Lebih Banyak ({{ filteredGallery.length - visibleGallery.length }})
            </button>
          </div>
        </div>
      </section>

      <!-- LIGHTBOX GALLERY -->
      <transition name="lightbox-fade">
        <div v-if="lightboxIndex !== null"
          class="fixed inset-0 z-[60] bg-black/95 backdrop-blur-sm flex items-center justify-center p-4 sm:p-10"
          role="dialog" aria-modal="true" aria-label="Galeri foto"
          @click.self="closeLightbox"
          @touchstart.passive="onTouchStart"
          @touchend="handleSwipe($event, nextImage, prevImage)"
        >
          <button type="button" @click="closeLightbox" aria-label="Tutup"
            class="absolute top-4 right-4 sm:top-8 sm:right-8 w-11 h-11 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 flex items-center justify-center text-white transition cursor-pointer z-10">
            <X :size="18" />
          </button>

          <span class="absolute top-6 left-5 sm:top-10 sm:left-10 font-mono text-[10px] tracking-[0.25em] text-zinc-500 uppercase">
            {{ String(lightboxIndex + 1).padStart(2, '0') }} / {{ String(visibleGallery.length).padStart(2, '0') }}
          </span>

          <button v-if="visibleGallery.length > 1" type="button" @click.stop="prevImage" aria-label="Foto sebelumnya"
            class="absolute left-2 sm:left-8 top-1/2 -translate-y-1/2 w-11 h-11 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 flex items-center justify-center text-white transition cursor-pointer z-10">
            <ChevronLeft :size="20" />
          </button>
          <button v-if="visibleGallery.length > 1" type="button" @click.stop="nextImage" aria-label="Foto berikutnya"
            class="absolute right-2 sm:right-8 top-1/2 -translate-y-1/2 w-11 h-11 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 flex items-center justify-center text-white transition cursor-pointer z-10">
            <ChevronRight :size="20" />
          </button>

          <div class="max-w-4xl w-full space-y-4" @click.stop>
            <div class="max-h-[75vh] flex items-center justify-center overflow-hidden">
              <img :key="lightboxIndex" :src="currentLightboxImage?.image_url" :alt="currentLightboxImage?.title || 'Masashimura'"
                class="lb-img max-h-[75vh] max-w-full object-contain" />
            </div>
            <div class="text-center space-y-1">
              <p class="font-sora text-sm font-bold uppercase tracking-wider text-white">{{ currentLightboxImage?.title || 'Masashimura' }}</p>
              <p v-if="currentLightboxImage?.category" class="font-mono text-[9px] tracking-[0.25em] text-zinc-500 uppercase">{{ currentLightboxImage.category }}</p>
            </div>
          </div>
        </div>
      </transition>

      <!-- ═══════════════════════════════════════════
           7. REVIEW (tinggi otomatis, bisa swipe, ada kontrol)
      ═══════════════════════════════════════════ -->
      <section v-reveal class="py-20 sm:py-28 lg:py-32 px-6 sm:px-10 max-w-4xl mx-auto">
        <div class="mb-10 sm:mb-14 space-y-3">
          <div class="flex items-center gap-3">
            <span class="w-6 h-px bg-[#DC2626]"></span>
            <span class="font-mono text-[10px] tracking-[0.3em] text-[#DC2626] uppercase">Kata Mereka</span>
          </div>
          <h2 class="font-sora text-3xl sm:text-4xl font-extrabold uppercase tracking-tight">Review Pelanggan</h2>
        </div>

        <div v-if="reviews.length" class="select-none">
          <!-- Semua review ditumpuk di 1 sel grid → tinggi = review terpanjang, nggak ada yang kepotong -->
          <div class="grid">
            <figure
              v-for="(review, i) in reviews"
              :key="i"
              :aria-hidden="i !== currentReviewIndex"
              class="col-start-1 row-start-1 border-l-2 border-[#DC2626] pl-6 sm:pl-10 space-y-6 transition-all duration-500 ease-out"
              :class="i === currentReviewIndex ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-3 pointer-events-none'"
            >
              <Quote :size="28" class="text-[#DC2626]/60" />
              <blockquote class="text-zinc-200 text-lg sm:text-2xl font-sora font-light italic leading-relaxed max-w-2xl">
                “{{ review.text }}”
              </blockquote>
              <figcaption class="flex items-center gap-3">
                <span class="w-9 h-9 shrink-0 rounded-full bg-[#DC2626]/15 border border-[#DC2626]/30 flex items-center justify-center font-sora text-xs font-bold text-[#DC2626] uppercase">
                  {{ (review.name || '?').trim().charAt(0) }}
                </span>
                <span class="flex flex-col min-w-0">
                  <span class="font-mono text-[10px] tracking-[0.2em] text-zinc-300 uppercase truncate">{{ review.name }}</span>
                  <span class="font-mono text-[10px] text-zinc-600">{{ review.status }}</span>
                </span>
              </figcaption>
            </figure>
          </div>

          <!-- Indikator saja (otomatis jalan, tanpa tombol) -->
          <div v-if="reviews.length > 1" class="mt-10 sm:mt-12 flex items-center gap-2" aria-hidden="true">
            <span v-for="(r, i) in reviews" :key="i"
              class="block h-0.5 transition-all duration-500"
              :class="i === currentReviewIndex ? 'w-8 bg-[#DC2626]' : 'w-4 bg-zinc-700'"></span>
          </div>
        </div>
      </section>

      <!-- ═══════════════════════════════════════════
           8. CTA
      ═══════════════════════════════════════════ -->
      <section v-reveal class="relative overflow-hidden border-t border-white/[0.06] bg-[#0a0a0a]">
        <div class="cta-glow absolute inset-0 pointer-events-none"></div>
        <div class="relative max-w-7xl mx-auto px-6 sm:px-10 py-20 sm:py-28 lg:py-32 grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-16 items-center">
          <div class="space-y-6">
            <div class="flex items-center gap-3">
              <span class="w-6 h-px bg-[#DC2626]"></span>
              <span class="font-mono text-[10px] tracking-[0.3em] text-[#DC2626] uppercase">Yuk Order</span>
            </div>
            <h2 class="font-sora text-5xl sm:text-6xl lg:text-7xl font-extrabold uppercase tracking-tight leading-[0.9]">
              Udah<br/><span class="text-[#DC2626]">Laper?</span>
            </h2>
            <p class="text-zinc-400 text-sm font-light max-w-xs leading-relaxed">
              Pilih menu favorit dan nikmati langsung di kedai atau melalui web ordering.
            </p>
          </div>
          <div class="flex flex-col sm:flex-row lg:justify-end gap-3 sm:gap-4">
            <router-link to="/menu"
              class="group inline-flex items-center justify-center gap-3 bg-[#DC2626] hover:bg-red-700 text-white font-sora text-[11px] uppercase tracking-[0.2em] px-10 py-5 font-bold transition-all duration-200 hover:-translate-y-0.5">
              Pesan via Web
              <ArrowRight :size="14" class="transition-transform duration-200 group-hover:translate-x-1" />
            </router-link>
            <router-link to="/contact"
              class="inline-flex items-center justify-center border border-white/25 hover:border-white/60 hover:bg-white/5 text-white font-sora text-[11px] uppercase tracking-[0.2em] px-10 py-5 font-bold transition-all duration-200">
              Hubungi Kami
            </router-link>
          </div>
        </div>
      </section>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from "vue"
import {
  Coffee, Wifi, Zap, Utensils, DollarSign, Moon, Shield, Tv,
  Music, Gamepad2, Beer, BatteryCharging, Heart, Award, Smartphone,
  Expand, X, ChevronLeft, ChevronRight, ArrowRight, Quote
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
const getIcon = (name) => iconMap[name] || iconMap["Coffee"]

// ── Scroll reveal directive: fade + slide up sekali pas section masuk viewport ──
const vReveal = {
  mounted(el) {
    el.classList.add("reveal")
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          el.classList.add("reveal-visible")
          observer.unobserve(el)
        }
      })
    }, { threshold: 0.12 })
    observer.observe(el)
  }
}

// ── Image fade-up directive: img mulai transparan+scale, muncul pas selesai load ──
const vBlurImg = {
  mounted(el) {
    el.classList.add("img-blur")
    const markLoaded = () => el.classList.add("img-loaded")
    if (el.complete && el.naturalWidth > 0) {
      markLoaded()
    } else {
      el.addEventListener("load", markLoaded, { once: true })
    }
  }
}

// ── Hero: headline (baris terakhir beraksen merah) + parallax ─────────────
const headlineLines = computed(() => {
  const lines = String(cms.value.hero_headline || "")
    .split("\n")
    .map(l => l.trim())
    .filter(Boolean)
  return lines.map((text, i) => ({ text, accent: lines.length > 1 && i === lines.length - 1 }))
})

const parallaxY = computed(() => Math.min(scrollY.value, 700) * 0.1)

// ── Metric count-up (section Tentang) ────────────────────────────────────
const metricsRef     = ref(null)
const metricDisplays = ref({ m1: "0", m2: "0" })
let   metricsAnimated = false
let   metricsObserver = null

const metric3IsStars = computed(() => /★/.test(String(cms.value.metric_3 || "")))

const parseMetricParts = (raw) => {
  const str = String(raw ?? "")
  const match = str.match(/^([\d.,]+)(.*)$/)
  if (!match) return null
  const numStr = match[1].replace(/,/g, "")
  const target = parseFloat(numStr)
  if (isNaN(target)) return null
  const decimals = (numStr.split(".")[1] || "").length
  const suffix = match[2] || ""
  return { target, decimals, suffix }
}

const animateMetric = (raw, key) => {
  const parts = parseMetricParts(raw)
  if (!parts) {
    metricDisplays.value[key] = raw
    return
  }
  const { target, decimals, suffix } = parts
  const duration = 1400
  const startTime = performance.now()
  const step = (now) => {
    const progress = Math.min((now - startTime) / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    const current = (target * eased).toFixed(decimals)
    metricDisplays.value[key] = `${current}${suffix}`
    if (progress < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

const setupMetricsObserver = () => {
  if (!metricsRef.value) return
  metricsObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting && !metricsAnimated) {
        metricsAnimated = true
        animateMetric(cms.value.metric_1, "m1")
        animateMetric(cms.value.metric_2, "m2")
        metricsObserver.unobserve(entry.target)
      }
    })
  }, { threshold: 0.3 })
  metricsObserver.observe(metricsRef.value)
}

// ── Best seller: maksimal 6 biar grid 3 kolom selalu rapi ────────────────
const topBestSellers = computed(() => bestSellers.value.slice(0, 6))

// ── Bento: pisah kartu besar & kecil, kartu kecil ganjil terakhir dilebarkan ──
const bentoLarge = computed(() => bentoFacilities.value.filter(b => b.size === "large"))
const bentoSmall = computed(() => bentoFacilities.value.filter(b => b.size !== "large"))
const isBentoOrphan = (i) => bentoSmall.value.length % 2 === 1 && i === bentoSmall.value.length - 1

// ── Gallery: filter kategori + pagination + lightbox ──────────────────────
const activeCategory = ref("Semua")
const galleryLimit    = ref(8)
const lightboxIndex   = ref(null)

const galleryCategories = computed(() => {
  const cats = new Set(galleryData.value.map(g => g.category).filter(Boolean))
  return ["Semua", ...cats]
})

const filteredGallery = computed(() => {
  if (activeCategory.value === "Semua") return galleryData.value
  return galleryData.value.filter(g => g.category === activeCategory.value)
})

const visibleGallery = computed(() => filteredGallery.value.slice(0, galleryLimit.value))

// Item pertama baru dibesarkan kalau fotonya >= 5, supaya grid nggak bolong
const isFeatured = (i) => i === 0 && visibleGallery.value.length >= 5

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

// Kunci scroll halaman saat lightbox terbuka
watch(lightboxIndex, (v) => {
  document.body.style.overflow = v !== null ? "hidden" : ""
})

// ── Swipe (dipakai lightbox & review) ─────────────────────────────────────
let touchX = 0
let touchY = 0
const onTouchStart = (e) => {
  const t = e.changedTouches[0]
  touchX = t.clientX
  touchY = t.clientY
}
const handleSwipe = (e, onLeft, onRight) => {
  const t = e.changedTouches[0]
  const dx = t.clientX - touchX
  const dy = t.clientY - touchY
  if (Math.abs(dx) < 50 || Math.abs(dx) < Math.abs(dy) * 1.5) return
  if (dx < 0) onLeft()
  else onRight()
}

// ── Review slider ─────────────────────────────────────────────────────────
const stopAutoplay = () => {
  if (reviewInterval) {
    clearInterval(reviewInterval)
    reviewInterval = null
  }
}

const nextReview = () => {
  const n = reviews.value.length
  if (n === 0) return
  currentReviewIndex.value = (currentReviewIndex.value + 1) % n
}

const startAutoplay = () => {
  stopAutoplay()
  if (reviews.value.length < 2) return
  reviewInterval = setInterval(nextReview, 6000)
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
        price: Number(item.price_web),
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

// ── Scroll parallax (di-throttle pakai rAF) ──────────────────────────────
let scrollTicking = false
const handleScroll = () => {
  if (scrollTicking) return
  scrollTicking = true
  requestAnimationFrame(() => {
    scrollY.value = window.scrollY
    scrollTicking = false
  })
}

// ── Lifecycle ────────────────────────────────────────────────────────────
onMounted(async () => {
  window.addEventListener("scroll", handleScroll, { passive: true })
  window.addEventListener("keydown", handleLightboxKeydown)
  await Promise.all([fetchCMSData(), fetchBestSellers(), fetchGoogleReviews(), fetchBentoAndGallery()])
  isLoading.value = false
  await nextTick()
  setupMetricsObserver()
  startAutoplay()
})

onUnmounted(() => {
  window.removeEventListener("scroll", handleScroll)
  window.removeEventListener("keydown", handleLightboxKeydown)
  document.body.style.overflow = ""
  stopAutoplay()
  if (metricsObserver) metricsObserver.disconnect()
})
</script>

<style scoped>
/* Fokus keyboard yang jelas & konsisten */
a:focus-visible,
button:focus-visible {
  outline: 2px solid #DC2626;
  outline-offset: 3px;
}

/* ── Loading bar ── */
@keyframes loadBar {
  0%   { transform: translateX(-100%); }
  100% { transform: translateX(200%); }
}
.load-bar { animation: loadBar 1.2s ease-in-out infinite; }

/* ── Hero ── */
.hero {
  min-height: 100vh;
  min-height: 100svh; /* aman dari address bar browser mobile */
}
.hero-title {
  font-size: clamp(2.25rem, 8.5vw, 4.75rem);
}
@media (min-width: 1024px) {
  .hero-title { font-size: clamp(3rem, 6vw, 4.75rem); }
}
.hero-glow {
  background: radial-gradient(60% 50% at 0% 100%, rgba(220, 38, 38, 0.18), transparent 70%);
}
.cta-glow {
  background: radial-gradient(50% 70% at 100% 100%, rgba(220, 38, 38, 0.14), transparent 70%);
}

@keyframes heroIn {
  to { opacity: 1; transform: none; }
}
.hero-in {
  opacity: 0;
  transform: translateY(18px);
  animation: heroIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  animation-delay: var(--d, 0ms);
}

/* ── Marquee ── */
@keyframes marquee {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
.animate-marquee {
  width: max-content;
  animation: marquee 60s linear infinite;
}
.marquee-wrap:hover .animate-marquee {
  animation-play-state: paused;
}
/* Fade di sisi kiri & kanan: teks masuk/keluar pelan-pelan, garis border tetap solid */
.marquee-wrap { position: relative; }
.marquee-wrap::before,
.marquee-wrap::after {
  content: "";
  position: absolute;
  top: 0;
  bottom: 0;
  width: 14%;
  z-index: 1;
  pointer-events: none;
}
.marquee-wrap::before { left: 0;  background: linear-gradient(90deg,  #0a0a0a, transparent); }
.marquee-wrap::after  { right: 0; background: linear-gradient(270deg, #0a0a0a, transparent); }

/* ── Lightbox ── */
.lightbox-fade-enter-active,
.lightbox-fade-leave-active {
  transition: opacity 0.25s ease;
}
.lightbox-fade-enter-from,
.lightbox-fade-leave-to {
  opacity: 0;
}
@keyframes lbIn {
  from { opacity: 0; transform: scale(0.98); }
  to   { opacity: 1; transform: scale(1); }
}
.lb-img { animation: lbIn 0.3s ease; }

/* ── Scroll reveal per section ── */
.reveal {
  opacity: 0;
  transform: translateY(28px);
  transition: opacity 0.7s cubic-bezier(0.16, 1, 0.3, 1), transform 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}
.reveal-visible {
  opacity: 1;
  transform: none;
}

/* ── Image fade-up on load ── */
.img-blur {
  opacity: 0;
  transform: scale(1.04);
  transition: opacity 0.6s ease, transform 0.6s ease, filter 0.7s ease;
}
.img-blur.img-loaded {
  opacity: 1;
  transform: scale(1);
}

/* ── Util ── */
.no-scrollbar { scrollbar-width: none; }
.no-scrollbar::-webkit-scrollbar { display: none; }

@media (prefers-reduced-motion: reduce) {
  .reveal, .img-blur {
    transition: none;
    opacity: 1;
    transform: none;
  }
  .hero-in {
    animation: none;
    opacity: 1;
    transform: none;
  }
  .animate-marquee,
  .load-bar,
  .lb-img {
    animation: none;
  }
}
</style>