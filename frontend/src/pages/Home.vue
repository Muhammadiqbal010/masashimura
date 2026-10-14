<template>
  <div class="min-h-screen overflow-x-hidden bg-[#111111] font-inter text-[#FAFAFA] selection:bg-[#D71920]/40 selection:text-white">

    <!-- ═══════════════════════════════════════════
         1. HERO (tampil langsung, bagian CMS pakai skeleton)
    ═══════════════════════════════════════════ -->
    <section class="hero relative flex items-end overflow-hidden">

      <div class="absolute inset-0">
        <div
          class="absolute inset-x-0 -top-[12%] h-[124%] will-change-transform"
          :style="{ transform: `translate3d(0, ${parallaxY}px, 0)` }"
        >
          <img
            v-if="!loading.cms"
            v-blur-img
            :src="cms.hero_bg_image || defaultHeroBg"
            alt=""
            fetchpriority="high"
            decoding="async"
            class="h-full w-full object-cover"
          />
        </div>
        <div class="absolute inset-0 bg-gradient-to-t from-[#111111] via-[#111111]/60 to-[#111111]/55"></div>
        <div class="absolute inset-0 hidden bg-gradient-to-r from-[#111111] via-[#111111]/70 to-transparent lg:block"></div>
        <div class="hero-glow pointer-events-none absolute inset-0"></div>
      </div>

      <div class="relative z-10 mx-auto grid w-full max-w-7xl grid-cols-1 items-end gap-10 px-5 pb-16 pt-32 sm:px-8 sm:pb-20 lg:grid-cols-12 lg:px-10 lg:pb-24">
        <div class="space-y-6 sm:space-y-7 lg:col-span-7">

          <!-- Status + lokasi -->
          <div class="hero-in flex flex-wrap items-center gap-2" style="--d: 0ms">
            <div
              class="flex w-fit items-center gap-2.5 rounded-full border border-white/10 bg-black/40 px-3.5 py-1.5 backdrop-blur-md"
              role="status"
            >
              <span class="relative flex h-2 w-2 shrink-0">
                <span
                  class="relative inline-flex h-2 w-2 rounded-full"
                  :class="openStatus.isOpen ? 'bg-emerald-400' : 'bg-[#D71920]'"
                ></span>
              </span>
              <span class="text-xs font-medium text-[#FAFAFA]">{{ openStatus.label }}</span>
              <span v-if="openStatus.detail" class="text-xs text-[#A3A3A3]">{{ openStatus.detail }}</span>
            </div>
            <span class="rounded-full border border-[#FFD400]/25 bg-[#FFD400]/10 px-3.5 py-1.5 text-xs font-medium text-[#FFD400]">
              Bekasi, sejak 2024
            </span>
          </div>

          <!-- Headline -->
          <h1
            v-if="!loading.cms"
            class="hero-title hero-in break-words font-sora font-semibold leading-[1.02] tracking-tight text-[#FAFAFA]"
            style="--d: 100ms"
          >
            <span
              v-for="(line, i) in headlineLines"
              :key="i"
              class="block"
              :class="line.accent ? 'text-[#FFD400]' : ''"
            >{{ line.text }}</span>
          </h1>
          <div v-else class="space-y-3" aria-hidden="true">
            <div class="skeleton hero-skel w-[85%] rounded-xl"></div>
            <div class="skeleton hero-skel w-[60%] rounded-xl"></div>
          </div>

          <!-- Subheadline -->
          <p
            v-if="!loading.cms"
            class="hero-in max-w-md text-base leading-relaxed text-[#C8C8C8] sm:text-lg"
            style="--d: 220ms"
          >
            {{ cms.hero_subheadline }}
          </p>
          <div v-else class="max-w-md space-y-2" aria-hidden="true">
            <div class="skeleton h-4 w-full rounded-full"></div>
            <div class="skeleton h-4 w-2/3 rounded-full"></div>
          </div>

          <div class="hero-in flex flex-col gap-3 pt-2 sm:flex-row sm:gap-4" style="--d: 320ms">
            <router-link to="/menu" class="btn-primary group px-8 py-4">
              Pesan sekarang
              <ArrowRight :size="16" class="transition-transform duration-200 group-hover:translate-x-1" />
            </router-link>
            <router-link to="/contact" class="btn-ghost px-8 py-4">
              Kontak kami
            </router-link>
          </div>
        </div>

        <!-- Foto makanan (desktop) -->
        <div class="hero-in hidden items-end justify-end lg:col-span-5 lg:flex" style="--d: 300ms">
          <div class="relative w-80">
            <div class="absolute -right-3 -top-3 h-full w-full rounded-[2rem] border border-[#FFD400]/30"></div>
            <div class="relative aspect-square overflow-hidden rounded-[2rem] border border-white/10 bg-[#1B1B1B]">
              <img
                v-if="!loading.cms"
                v-blur-img
                :src="cms.hero_food_image || defaultHeroFood"
                alt="Masashimura Signature Dish"
                class="h-full w-full object-cover"
              />
              <div v-else class="skeleton h-full w-full" aria-hidden="true"></div>
              <div class="absolute inset-x-3 bottom-3 flex items-center justify-between rounded-2xl border border-white/10 bg-black/55 px-4 py-3 backdrop-blur-md">
                <span class="text-sm font-medium text-[#FAFAFA]">Signature dish</span>
                <span class="h-2 w-2 rounded-full bg-[#D71920]"></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="pointer-events-none absolute bottom-6 left-1/2 hidden -translate-x-1/2 flex-col items-center gap-1.5 opacity-40 sm:flex">
        <span class="text-xs text-[#A3A3A3]">Scroll</span>
        <div class="h-8 w-px bg-gradient-to-b from-[#A3A3A3] to-transparent"></div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════
         2. MARQUEE
    ═══════════════════════════════════════════ -->
    <div v-if="cms.marquee_text" class="marquee-wrap overflow-hidden border-y border-white/[0.06] bg-[#111111] py-5" aria-hidden="true">
      <div class="animate-marquee flex">
        <div v-for="g in 2" :key="g" class="flex shrink-0 items-center">
          <template v-for="m in 4" :key="m">
            <span class="mx-8 whitespace-nowrap font-sora text-sm font-medium tracking-[0.2em] text-[#737373]">
              {{ cms.marquee_text }}
            </span>
            <span class="h-1.5 w-1.5 shrink-0 rounded-full bg-[#FFD400]"></span>
          </template>
        </div>
      </div>
    </div>
    <div v-else class="border-y border-white/[0.06] bg-[#111111] py-5" aria-hidden="true">
      <div class="skeleton mx-auto h-3 w-1/2 rounded-full"></div>
    </div>

    <!-- ═══════════════════════════════════════════
         3. PROMO / EVENT
    ═══════════════════════════════════════════ -->
    <PromoSection :promos="promos" />

    <!-- ═══════════════════════════════════════════
         4. BEST SELLER
    ═══════════════════════════════════════════ -->
    <section v-reveal class="mx-auto max-w-7xl px-5 py-20 sm:px-8 sm:py-28 lg:px-10 lg:py-32">

      <div class="mb-10 flex items-end justify-between gap-6 sm:mb-14">
        <div class="space-y-3">
          <h2 class="section-title">Menu terlaris</h2>
          <p class="max-w-md text-base text-[#A3A3A3]">Yang paling sering dipesan pelanggan kami.</p>
        </div>
        <router-link to="/menu" class="group hidden items-center gap-2 text-sm font-medium text-[#FFD400] transition-colors hover:text-[#FAFAFA] sm:inline-flex">
          Lihat semua
          <ArrowRight :size="15" class="transition-transform duration-200 group-hover:translate-x-1" />
        </router-link>
      </div>

      <!-- Skeleton -->
      <div v-if="loading.best" class="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-5 lg:grid-cols-3" aria-hidden="true">
        <div v-for="n in 3" :key="n" class="overflow-hidden rounded-3xl border border-white/[0.07] bg-[#1B1B1B]">
          <div class="skeleton aspect-[4/3] w-full"></div>
          <div class="space-y-3 p-6">
            <div class="skeleton h-5 w-3/4 rounded-full"></div>
            <div class="skeleton h-3 w-full rounded-full"></div>
            <div class="skeleton h-3 w-2/3 rounded-full"></div>
            <div class="mt-1 flex items-center justify-between border-t border-white/10 pt-4">
              <div class="skeleton h-5 w-24 rounded-full"></div>
              <div class="skeleton h-10 w-24 rounded-full"></div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-5 lg:grid-cols-3">
        <router-link
          v-for="(item, idx) in topBestSellers"
          :key="idx"
          to="/menu"
          class="card-surface group flex flex-col overflow-hidden !p-0 transition-all duration-300 hover:-translate-y-1 hover:border-[#FFD400]/35 hover:shadow-lg shadow-black/20"
        >
          <div class="relative aspect-[4/3] w-full shrink-0 overflow-hidden bg-[#1B1B1B]">
            <div class="h-full w-full transition-transform duration-700 ease-out group-hover:scale-105">
              <img
                v-blur-img
                :src="item.image"
                :alt="item.name"
                loading="lazy"
                class="h-full w-full object-cover"
              />
            </div>
            <div class="pointer-events-none absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-[#1B1B1B] to-transparent opacity-80"></div>
            <span class="absolute left-3 top-3 flex h-8 min-w-8 items-center justify-center rounded-full border border-white/10 bg-black/55 px-2 text-xs font-semibold tabular-nums text-[#FAFAFA] backdrop-blur-md">
              {{ idx + 1 }}
            </span>
            <span
              v-if="idx === 0"
              class="absolute right-3 top-3 rounded-full bg-[#FFD400] px-3 py-1 text-xs font-semibold text-[#1A1700]"
            >
              Terlaris
            </span>
          </div>

          <div class="flex flex-1 flex-col gap-3 p-6">
            <h3 class="line-clamp-2 font-sora text-lg font-semibold leading-snug text-[#FAFAFA]">
              {{ item.name }}
            </h3>
            <p class="line-clamp-2 flex-1 text-sm leading-relaxed text-[#A3A3A3]">{{ item.desc }}</p>
            <div class="mt-1 flex items-center justify-between border-t border-white/[0.07] pt-4">
              <span class="font-sora text-lg font-semibold tracking-tight text-[#FAFAFA]">
                {{ formatRupiah(item.price) }}
              </span>
              <span class="inline-flex items-center gap-2 rounded-full bg-[#D71920] px-5 py-2.5 text-sm font-semibold text-white transition-colors group-hover:bg-[#B5121B]">
                Pesan
                <ArrowRight :size="14" class="transition-transform duration-200 group-hover:translate-x-0.5" />
              </span>
            </div>
          </div>
        </router-link>

        <div
          v-if="bestSellers.length === 0"
          class="col-span-full rounded-3xl border border-dashed border-white/10 py-20 text-center text-sm text-[#737373]"
        >
          Menu belum tersedia saat ini.
        </div>
      </div>

      <div class="mt-8 sm:hidden">
        <router-link to="/menu" class="btn-ghost w-full px-6 py-4">
          Lihat semua menu
          <ArrowRight :size="16" />
        </router-link>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════
         5. TENTANG MASASHIMURA
    ═══════════════════════════════════════════ -->
    <section v-reveal class="border-y border-white/[0.06] bg-[#111111] py-20 sm:py-28 lg:py-32">
      <div class="mx-auto grid max-w-7xl grid-cols-1 items-center gap-14 px-5 sm:px-8 lg:grid-cols-2 lg:gap-20 lg:px-10">

        <div class="relative">
          <div class="absolute -bottom-3 -left-3 h-full w-full rounded-[2rem] border border-[#FFD400]/25 sm:-bottom-4 sm:-left-4"></div>
          <div class="relative aspect-square overflow-hidden rounded-[2rem] bg-[#1B1B1B]">
            <img
              v-if="!loading.cms"
              v-blur-img
              :src="cms.about_image || defaultAboutImage"
              alt="Suasana Masashimura"
              loading="lazy"
              class="h-full w-full object-cover"
            />
            <div v-else class="skeleton h-full w-full" aria-hidden="true"></div>
          </div>
        </div>

        <div class="space-y-8 sm:space-y-10">
          <div class="space-y-4">
            <h2 class="section-title">Tentang Masashimura</h2>
            <p v-if="!loading.cms" class="max-w-md text-base leading-[1.85] text-[#A3A3A3]">{{ cms.about_text }}</p>
            <div v-else class="max-w-md space-y-2.5" aria-hidden="true">
              <div class="skeleton h-4 w-full rounded-full"></div>
              <div class="skeleton h-4 w-full rounded-full"></div>
              <div class="skeleton h-4 w-4/5 rounded-full"></div>
            </div>
          </div>

          <!-- Metrics -->
          <div ref="metricsRef" class="grid grid-cols-3 divide-x divide-white/[0.07] overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.02]">
            <div class="space-y-1 px-3 py-5 sm:px-6">
              <p class="font-sora text-2xl font-semibold leading-tight text-[#FAFAFA] sm:text-3xl">{{ metricDisplays.m1 }}</p>
              <p class="text-xs text-[#A3A3A3] sm:text-sm">Berdiri</p>
            </div>
            <div class="space-y-1 px-3 py-5 sm:px-6">
              <p class="font-sora text-2xl font-semibold leading-tight text-[#FAFAFA] sm:text-3xl">{{ metricDisplays.m2 }}</p>
              <p class="text-xs text-[#A3A3A3] sm:text-sm">Varian menu</p>
            </div>
            <div class="space-y-1 px-3 py-5 sm:px-6">
              <p
                class="whitespace-nowrap font-sora font-semibold leading-tight text-[#FFD400]"
                :class="metric3IsStars ? 'pt-1 text-[0.9rem] tracking-tighter sm:pt-0 sm:text-2xl' : 'text-2xl sm:text-3xl'"
              >
                {{ cms.metric_3 || "–" }}
              </p>
              <p class="text-xs text-[#A3A3A3] sm:text-sm">Rating</p>
            </div>
          </div>

          <router-link to="/menu" class="group inline-flex items-center gap-2 text-sm font-semibold text-[#FFD400] transition-colors hover:text-[#FAFAFA]">
            Lihat semua menu
            <ArrowRight :size="15" class="transition-transform duration-200 group-hover:translate-x-1" />
          </router-link>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════
         6. BENTO FASILITAS
    ═══════════════════════════════════════════ -->
    <section v-reveal class="mx-auto max-w-7xl px-5 py-20 sm:px-8 sm:py-28 lg:px-10 lg:py-32">
      <div class="mb-10 sm:mb-14">
        <h2 class="section-title">Apa yang lo dapet</h2>
      </div>

      <!-- Skeleton -->
      <div v-if="loading.bento" class="grid grid-cols-1 gap-3 lg:grid-cols-12" aria-hidden="true">
        <div class="skeleton min-h-[220px] rounded-3xl sm:min-h-[260px] lg:col-span-5"></div>
        <div class="grid auto-rows-fr grid-cols-2 gap-3 lg:col-span-7">
          <div v-for="n in 4" :key="n" class="skeleton min-h-[112px] rounded-2xl sm:min-h-[130px]"></div>
        </div>
      </div>

      <div v-else class="grid grid-cols-1 gap-3 lg:grid-cols-12">
        <div v-if="bentoLarge.length" class="flex flex-col gap-3 lg:col-span-5">
          <div
            v-for="(bento, i) in bentoLarge"
            :key="'l' + i"
            class="bento-large group relative flex min-h-[220px] flex-1 flex-col justify-between overflow-hidden rounded-3xl border border-white/[0.07] p-8 transition-colors duration-300 hover:border-[#FFD400]/35 sm:min-h-[260px] sm:p-10"
          >
            <div class="pointer-events-none absolute -bottom-10 -right-10 text-[#FFD400] opacity-[0.07] transition-opacity duration-500 group-hover:opacity-[0.14]">
              <component :is="getIcon(bento.icon_name)" :size="220" :stroke-width="1" />
            </div>
            <div class="icon-tile relative !h-12 !w-12">
              <component :is="getIcon(bento.icon_name)" :size="22" />
            </div>
            <span class="relative font-sora text-2xl font-semibold leading-tight tracking-tight text-[#FAFAFA] sm:text-3xl">
              {{ bento.title }}
            </span>
          </div>
        </div>

        <div
          class="grid auto-rows-fr grid-cols-2 gap-3"
          :class="bentoLarge.length ? 'lg:col-span-7' : 'lg:col-span-12'"
        >
          <div
            v-for="(bento, i) in bentoSmall"
            :key="'s' + i"
            class="card-surface group flex min-h-[112px] flex-col justify-between gap-6 !p-5 transition-colors duration-300 hover:border-[#FFD400]/35 sm:min-h-[130px] sm:!p-6"
            :class="isBentoOrphan(i) ? 'col-span-2' : ''"
          >
            <div class="icon-tile">
              <component :is="getIcon(bento.icon_name)" :size="18" />
            </div>
            <span class="font-sora text-sm font-semibold text-[#FAFAFA] sm:text-base">
              {{ bento.title }}
            </span>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════
         7. GALLERY
    ═══════════════════════════════════════════ -->
    <section v-reveal class="border-y border-white/[0.06] bg-[#111111] py-20 sm:py-28 lg:py-32">
      <div class="mx-auto max-w-7xl px-5 sm:px-8 lg:px-10">
        <div class="mb-8 sm:mb-10">
          <h2 class="section-title">Gallery</h2>
        </div>

        <div
          v-if="!loading.gallery && galleryCategories.length > 2"
          class="no-scrollbar -mx-5 mb-8 flex gap-2 overflow-x-auto px-5 pb-1 sm:mx-0 sm:flex-wrap sm:px-0 md:mb-10"
        >
          <button
            v-for="cat in galleryCategories"
            :key="cat"
            type="button"
            @click="setCategory(cat)"
            :class="[
              activeCategory === cat
                ? 'border-[#D71920] bg-[#D71920] text-white'
                : 'border-white/10 bg-[#1B1B1B] text-[#A3A3A3] hover:border-white/25 hover:text-[#FAFAFA]',
              'shrink-0 cursor-pointer whitespace-nowrap rounded-full border px-4 py-2.5 text-sm font-medium transition-all'
            ]"
          >
            {{ cat }}
          </button>
        </div>

        <!-- Skeleton -->
        <div
          v-if="loading.gallery"
          class="grid auto-rows-[150px] grid-cols-2 gap-2 sm:auto-rows-[180px] sm:grid-cols-3 sm:gap-3 md:grid-cols-4"
          aria-hidden="true"
        >
          <div v-for="n in 8" :key="n" class="skeleton rounded-2xl" :class="n === 1 ? 'col-span-2 row-span-2' : ''"></div>
        </div>

        <div v-else class="grid auto-rows-[150px] grid-flow-row-dense grid-cols-2 gap-2 sm:auto-rows-[180px] sm:grid-cols-3 sm:gap-3 md:grid-cols-4">
          <button
            v-for="(img, i) in visibleGallery"
            :key="img.id ?? img.image_url"
            type="button"
            :aria-label="'Buka foto: ' + (img.title || 'Masashimura')"
            @click="openLightbox(i)"
            :class="[
              isFeatured(i) ? 'col-span-2 row-span-2' : '',
              'group relative cursor-pointer overflow-hidden rounded-2xl border-0 bg-[#1B1B1B] p-0 text-left'
            ]"
          >
            <div class="h-full w-full transition-transform duration-700 ease-out group-hover:scale-105">
              <img
                v-blur-img
                :src="img.image_url"
                :alt="img.title || 'Dokumentasi Masashimura'"
                loading="lazy"
                class="h-full w-full object-cover"
              />
            </div>
            <div class="absolute inset-0 flex items-end bg-gradient-to-t from-black/80 via-black/0 to-transparent p-3 opacity-0 transition-opacity duration-300 group-hover:opacity-100 sm:p-4">
              <div class="min-w-0 space-y-0.5">
                <p class="line-clamp-1 font-sora text-sm font-semibold text-white">{{ img.title || 'Masashimura' }}</p>
                <p v-if="img.category" class="text-xs text-[#FFD400]">{{ img.category }}</p>
              </div>
            </div>
            <div class="absolute right-2.5 top-2.5 flex h-8 w-8 items-center justify-center rounded-full border border-white/10 bg-black/55 opacity-0 backdrop-blur-md transition-opacity duration-300 group-hover:opacity-100 sm:right-3 sm:top-3">
              <Expand :size="14" class="text-white" />
            </div>
          </button>

          <div
            v-if="visibleGallery.length === 0"
            class="col-span-full row-span-2 flex items-center justify-center rounded-2xl border border-dashed border-white/10 text-center text-sm text-[#737373]"
          >
            Belum ada foto.
          </div>
        </div>

        <div v-if="!loading.gallery && filteredGallery.length > visibleGallery.length" class="mt-10 flex justify-center">
          <button type="button" @click="galleryLimit += 8" class="btn-ghost cursor-pointer px-6 py-3.5">
            Muat lebih banyak ({{ filteredGallery.length - visibleGallery.length }})
          </button>
        </div>
      </div>
    </section>

    <!-- LIGHTBOX GALLERY -->
    <transition name="lightbox-fade">
      <div
        v-if="lightboxIndex !== null"
        class="fixed inset-0 z-[60] flex items-center justify-center bg-black/95 p-4 backdrop-blur-sm sm:p-10"
        role="dialog" aria-modal="true" aria-label="Galeri foto"
        @click.self="closeLightbox"
        @touchstart.passive="onTouchStart"
        @touchend="handleSwipe($event, nextImage, prevImage)"
      >
        <button
          type="button" @click="closeLightbox" aria-label="Tutup"
          class="absolute right-4 top-4 z-10 flex h-11 w-11 cursor-pointer items-center justify-center rounded-full border border-white/10 bg-white/5 text-white transition hover:bg-white/10 sm:right-8 sm:top-8"
        >
          <X :size="18" />
        </button>

        <span class="absolute left-5 top-6 text-sm font-medium tabular-nums text-[#A3A3A3] sm:left-10 sm:top-10">
          {{ lightboxIndex + 1 }} / {{ visibleGallery.length }}
        </span>

        <button
          v-if="visibleGallery.length > 1" type="button" @click.stop="prevImage" aria-label="Foto sebelumnya"
          class="absolute left-2 top-1/2 z-10 flex h-11 w-11 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full border border-white/10 bg-white/5 text-white transition hover:bg-white/10 sm:left-8"
        >
          <ChevronLeft :size="20" />
        </button>
        <button
          v-if="visibleGallery.length > 1" type="button" @click.stop="nextImage" aria-label="Foto berikutnya"
          class="absolute right-2 top-1/2 z-10 flex h-11 w-11 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full border border-white/10 bg-white/5 text-white transition hover:bg-white/10 sm:right-8"
        >
          <ChevronRight :size="20" />
        </button>

        <div class="w-full max-w-4xl space-y-4" @click.stop>
          <div class="flex max-h-[75vh] items-center justify-center overflow-hidden">
            <img
              :key="lightboxIndex"
              :src="currentLightboxImage?.image_url"
              :alt="currentLightboxImage?.title || 'Masashimura'"
              class="lb-img max-h-[75vh] max-w-full rounded-2xl object-contain"
            />
          </div>
          <div class="space-y-1 text-center">
            <p class="font-sora text-base font-semibold text-[#FAFAFA]">{{ currentLightboxImage?.title || 'Masashimura' }}</p>
            <p v-if="currentLightboxImage?.category" class="text-sm text-[#FFD400]">{{ currentLightboxImage.category }}</p>
          </div>
        </div>
      </div>
    </transition>

    <!-- ═══════════════════════════════════════════
         8. REVIEW (bisa swipe di mobile)
    ═══════════════════════════════════════════ -->
    <section v-reveal class="mx-auto max-w-4xl px-5 py-20 sm:px-8 sm:py-28 lg:px-10 lg:py-32">
      <div class="mb-10 sm:mb-14">
        <h2 class="section-title">Kata pelanggan</h2>
      </div>

      <!-- Skeleton -->
      <div v-if="loading.reviews" class="space-y-6" aria-hidden="true">
        <div class="skeleton h-8 w-8 rounded-full"></div>
        <div class="max-w-2xl space-y-3">
          <div class="skeleton h-5 w-full rounded-full"></div>
          <div class="skeleton h-5 w-5/6 rounded-full"></div>
          <div class="skeleton h-5 w-2/3 rounded-full"></div>
        </div>
        <div class="flex items-center gap-3">
          <div class="skeleton h-10 w-10 rounded-full"></div>
          <div class="space-y-2">
            <div class="skeleton h-3 w-28 rounded-full"></div>
            <div class="skeleton h-3 w-20 rounded-full"></div>
          </div>
        </div>
      </div>

      <div
        v-else-if="reviews.length"
        class="touch-pan-y select-none"
        @touchstart.passive="onTouchStart"
        @touchend="onReviewSwipe"
      >
        <div class="grid">
          <figure
            v-for="(review, i) in reviews"
            :key="i"
            :aria-hidden="i !== currentReviewIndex"
            class="col-start-1 row-start-1 space-y-7 transition-all duration-500 ease-out"
            :class="i === currentReviewIndex ? 'translate-y-0 opacity-100' : 'pointer-events-none translate-y-3 opacity-0'"
          >
            <Quote :size="32" class="text-[#FFD400]/70" />
            <blockquote class="max-w-2xl font-sora text-xl font-normal leading-relaxed text-[#FAFAFA] sm:text-2xl">
              “{{ review.text }}”
            </blockquote>
            <figcaption class="flex items-center gap-3">
              <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-[#FFD400]/30 bg-[#FFD400]/10 font-sora text-sm font-semibold uppercase text-[#FFD400]">
                {{ (review.name || '?').trim().charAt(0) }}
              </span>
              <span class="flex min-w-0 flex-col">
                <span class="truncate text-sm font-semibold text-[#FAFAFA]">{{ review.name }}</span>
                <span class="text-sm text-[#737373]">{{ review.status }}</span>
              </span>
            </figcaption>
          </figure>
        </div>

        <div v-if="reviews.length > 1" class="mt-10 flex items-center gap-2 sm:mt-12" aria-hidden="true">
          <span
            v-for="(r, i) in reviews"
            :key="i"
            class="block h-1.5 rounded-full transition-all duration-500"
            :class="i === currentReviewIndex ? 'w-8 bg-[#D71920]' : 'w-1.5 bg-white/20'"
          ></span>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════
         9. CTA
    ═══════════════════════════════════════════ -->
    <section v-reveal class="mx-auto max-w-7xl px-5 pb-20 sm:px-8 sm:pb-28 lg:px-10 lg:pb-32">
      <div class="cta relative grid grid-cols-1 items-center gap-10 overflow-hidden rounded-[2rem] p-8 sm:p-12 lg:grid-cols-2 lg:gap-16 lg:p-16">
        <div class="cta-sheen pointer-events-none absolute inset-0" aria-hidden="true"></div>

        <div class="relative space-y-5">
          <h2 class="font-sora text-4xl font-semibold leading-[1.05] tracking-tight text-white sm:text-5xl lg:text-6xl">
            Udah laper?
          </h2>
          <p class="max-w-xs text-base leading-relaxed text-white/75">
            Pilih menu favorit dan nikmati langsung di kedai atau lewat web ordering.
          </p>
        </div>

        <div class="relative flex flex-col gap-3 sm:flex-row sm:gap-4 lg:justify-end">
          <router-link
            to="/menu"
            class="group inline-flex items-center justify-center gap-2.5 whitespace-nowrap rounded-full bg-[#FAFAFA] px-9 py-4 font-sora text-sm font-semibold text-[#2A0A0F] transition-all duration-200 hover:bg-white active:scale-[0.98]"
          >
            Pesan via web
            <ArrowRight :size="16" class="transition-transform duration-200 group-hover:translate-x-1" />
          </router-link>
          <router-link
            to="/contact"
            class="inline-flex items-center justify-center whitespace-nowrap rounded-full border border-white/30 px-9 py-4 font-sora text-sm font-semibold text-white transition-all duration-200 hover:border-white/70 hover:bg-white/10 active:scale-[0.98]"
          >
            Hubungi kami
          </router-link>
        </div>
      </div>
    </section>

  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted } from "vue"
import {
  Coffee, Wifi, Zap, Utensils, DollarSign, Moon, Shield, Tv,
  Music, Gamepad2, Beer, BatteryCharging, Heart, Award, Smartphone,
  Expand, X, ChevronLeft, ChevronRight, ArrowRight, Quote
} from "lucide-vue-next"
import apiClient from "@/api/client"
import PromoSection from "@/components/ui/PromoSection.vue"
import { useOpenStatus } from "@/composables/useOpenStatus"
import { useScrollLock } from "@/composables/useScrollLock"
import { getWebPrice, formatRupiah } from "@/utils/price"

// ── Status per bagian: skeleton tampil sampai datanya datang ─────────────
const loading = reactive({
  cms: true,
  best: true,
  bento: true,
  gallery: true,
  reviews: true,
})

const scrollY            = ref(0)
const currentReviewIndex = ref(0)
let   reviewInterval     = null

const { status: openStatus } = useOpenStatus()
const { lock: lockScroll, unlock: unlockScroll } = useScrollLock()

const defaultHeroBg     = "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?q=80&w=1920"
const defaultHeroFood   = "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?q=80&w=800"
const defaultAboutImage = "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?q=80&w=1000"

const cms = ref({
  hero_headline:    "",
  hero_subheadline: "",
  hero_bg_image:    null,
  hero_food_image:  null,
  marquee_text:     "",
  about_text:       "",
  about_image:      null,
  metric_1: "", metric_2: "", metric_3: "",
})

// Promo & Event: array dari /homepage/promos/ (kosong = section tidak tampil)
const promos = ref([])

const bestSellers     = ref([])
const bentoFacilities = ref([])
const galleryData     = ref([])
const reviews         = ref([])

const iconMap = {
  Coffee, Wifi, Zap, Utensils, DollarSign, Moon, Shield, Tv,
  Music, Gamepad2, Beer, BatteryCharging, Heart, Award, Smartphone
}
const getIcon = (name) => iconMap[name] || iconMap["Coffee"]

// ── Scroll reveal directive ──────────────────────────────────────────────
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

// ── Image fade-up directive ──────────────────────────────────────────────
const vBlurImg = {
  mounted(el) {
    el.classList.add("img-blur")
    const markLoaded = () => el.classList.add("img-loaded")
    if (el.complete && el.naturalWidth > 0) {
      markLoaded()
    } else {
      el.addEventListener("load", markLoaded, { once: true })
      el.addEventListener("error", markLoaded, { once: true })
    }
  }
}

// ── Hero ─────────────────────────────────────────────────────────────────
const headlineLines = computed(() => {
  const lines = String(cms.value.hero_headline || "")
    .split("\n")
    .map(l => l.trim())
    .filter(Boolean)
  return lines.map((text, i) => ({ text, accent: lines.length > 1 && i === lines.length - 1 }))
})

const parallaxY = computed(() => Math.min(scrollY.value, 700) * 0.1)

// ── Metric count-up (jalan setelah terlihat DAN data CMS + jumlah menu siap) ──
const metricsRef      = ref(null)
const metricDisplays  = ref({ m1: "–", m2: "–" })
const metricsVisible  = ref(false)
let   metricsAnimated = false
let   metricsObserver = null

const metric3IsStars = computed(() => /★/.test(String(cms.value.metric_3 || "")))
const metricsReady   = computed(() => !loading.cms)

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
    metricDisplays.value[key] = raw || "–"
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

watch([metricsVisible, metricsReady], ([visible, ready]) => {
  if (!visible || !ready || metricsAnimated) return
  metricsAnimated = true
  animateMetric(cms.value.metric_1, "m1")
  // Varian menu: pakai jumlah asli dari API, fallback ke isi CMS
  animateMetric(cms.value.metric_2, "m2")
})

const setupMetricsObserver = () => {
  if (!metricsRef.value) return
  metricsObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        metricsVisible.value = true
        metricsObserver.unobserve(entry.target)
      }
    })
  }, { threshold: 0.3 })
  metricsObserver.observe(metricsRef.value)
}

// ── Best seller: maksimal 6 ──────────────────────────────────────────────
const topBestSellers = computed(() => bestSellers.value.slice(0, 6))

// ── Bento ────────────────────────────────────────────────────────────────
const bentoLarge = computed(() => bentoFacilities.value.filter(b => b.size === "large"))
const bentoSmall = computed(() => bentoFacilities.value.filter(b => b.size !== "large"))
const isBentoOrphan = (i) => bentoSmall.value.length % 2 === 1 && i === bentoSmall.value.length - 1

// ── Gallery ──────────────────────────────────────────────────────────────
const activeCategory = ref("Semua")
const galleryLimit   = ref(8)
const lightboxIndex  = ref(null)

const galleryCategories = computed(() => {
  const cats = new Set(galleryData.value.map(g => g.category).filter(Boolean))
  return ["Semua", ...cats]
})

const filteredGallery = computed(() => {
  if (activeCategory.value === "Semua") return galleryData.value
  return galleryData.value.filter(g => g.category === activeCategory.value)
})

const visibleGallery = computed(() => filteredGallery.value.slice(0, galleryLimit.value))

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

// Kunci scroll lewat composable terpusat (tidak bentrok dengan navbar)
watch(lightboxIndex, (v) => (v !== null ? lockScroll() : unlockScroll()))

// ── Swipe (lightbox & review) ────────────────────────────────────────────
let touchX = 0
let touchY = 0
const onTouchStart = (e) => {
  const t = e.changedTouches[0]
  touchX = t.clientX
  touchY = t.clientY
}
// Return true kalau memang terdeteksi sebagai swipe horizontal
const handleSwipe = (e, onLeft, onRight) => {
  const t = e.changedTouches[0]
  const dx = t.clientX - touchX
  const dy = t.clientY - touchY
  if (Math.abs(dx) < 50 || Math.abs(dx) < Math.abs(dy) * 1.5) return false
  if (dx < 0) onLeft()
  else onRight()
  return true
}

// ── Review slider ────────────────────────────────────────────────────────
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
const prevReview = () => {
  const n = reviews.value.length
  if (n === 0) return
  currentReviewIndex.value = (currentReviewIndex.value - 1 + n) % n
}

const startAutoplay = () => {
  stopAutoplay()
  if (reviews.value.length < 2) return
  reviewInterval = setInterval(nextReview, 6000)
}

// Setelah swipe, reset timer supaya review tidak langsung loncat sendiri
const onReviewSwipe = (e) => {
  if (handleSwipe(e, nextReview, prevReview)) startAutoplay()
}

// ── Data fetchers ────────────────────────────────────────────────────────
const fetchCMSData = async () => {
  let d = {}
  try {
    const res = await apiClient.get("/homepage/config/current/")
    d = res.data || {}
  } catch (err) {
    console.error("CMS fallback:", err)
  }
  const t = (v) => (typeof v === "string" ? v.trim() : v)

  cms.value = {
    // Positioning seragam: "Warkop Level Up" (sama dengan footer)
    hero_headline:    t(d.hero_headline)    || "Warkop Level Up\nMasashimura",
    hero_subheadline: t(d.hero_subheadline) || "Tempat nongkrong kasual modern di Bekasi dengan cita rasa nikmat.",
    hero_bg_image:    d.hero_bg_image   || null,
    hero_food_image:  d.hero_food_image || null,
    marquee_text:     t(d.marquee_text) || "MASA SIH MURAH? • WARKOP EVOLUTION • GOOD FOOD • GOOD VIBES • SINCE 2024",
    about_text:       t(d.about_text)   || "Masashimura adalah usaha kuliner asal Bekasi yang berdiri sejak 2024. Mengusung konsep tempat makan kasual yang nyaman, kami hadir buat lo yang mau nongkrong sambil menikmati makanan dengan harga bersahabat.",
    about_image:      d.about_image || null,
    metric_1: t(d.metric_1) || "2024",
    metric_2: t(d.metric_2) || "50+",
    metric_3: t(d.metric_3) || "★★★★★",
  }
  loading.cms = false
}

const fetchPromos = async () => {
  try {
    const { data } = await apiClient.get("/homepage/promos/")
    promos.value = Array.isArray(data) ? data.slice(0, 5) : []
  } catch (err) {
    console.error("Promos:", err)
    promos.value = []
  }
}

const fetchBestSellers = async () => {
  try {
    const { data } = await apiClient.get("/menus/bestsellers/")
    if (Array.isArray(data) && data.length > 0) {
      bestSellers.value = data.map(item => ({
        name:  item.name,
        desc:  item.description || "Menu favorit pilihan squad Masashimura.",
        price: getWebPrice(item),   // sama persis dengan halaman Menu
        image: item.image_url || defaultHeroFood,
      }))
    }
  } catch (err) {
    console.error("Best sellers:", err)
  } finally {
    loading.best = false
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
  } finally {
    loading.reviews = false
    startAutoplay()
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
  { title: "Menu Andalan",  image_url: defaultHeroFood, category: "Best Seller" },
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
  } finally {
    loading.bento = false
    loading.gallery = false
  }
}

// ── Scroll parallax (throttle rAF) ───────────────────────────────────────
let scrollTicking = false
const handleScroll = () => {
  if (scrollTicking) return
  scrollTicking = true
  requestAnimationFrame(() => {
    scrollY.value = window.scrollY
    scrollTicking = false
  })
}

// ── Lifecycle: halaman tampil duluan, semua fetch jalan paralel ──────────
onMounted(() => {
  window.addEventListener("scroll", handleScroll, { passive: true })
  window.addEventListener("keydown", handleLightboxKeydown)
  setupMetricsObserver()

  fetchCMSData()
  fetchPromos()
  fetchBestSellers()
  fetchGoogleReviews()
  fetchBentoAndGallery()
})

onUnmounted(() => {
  window.removeEventListener("scroll", handleScroll)
  window.removeEventListener("keydown", handleLightboxKeydown)
  stopAutoplay()
  if (metricsObserver) metricsObserver.disconnect()
})
</script>

<style scoped>
/*
  Palet (sama dengan halaman Menu dan Lokasi & Kontak)
  Warm black #111111 · Band #111111 · Surface #1B1B1B · Washi #FAFAFA
  Crimson #D71920 (aksi) · Champagne #FFD400 (detail premium)
*/

a:focus-visible,
button:focus-visible {
  outline: 2px solid #FFD400;
  outline-offset: 3px;
}

/* ── Judul section ── */
.section-title {
  font-family: "Sora", ui-sans-serif, system-ui, sans-serif;
  font-size: clamp(1.875rem, 4vw, 2.75rem);
  font-weight: 600;
  line-height: 1.1;
  letter-spacing: -0.02em;
  color: #FAFAFA;
}

/* ── Kartu & tombol ── */
.card-surface {
  border-radius: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.07);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.045), rgba(255, 255, 255, 0.012)), #1B1B1B;
  padding: 1.5rem;
}

.bento-large {
  background:
    radial-gradient(70% 70% at 100% 100%, rgba(215,25,32, 0.14), transparent 70%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.045), rgba(255, 255, 255, 0.012)),
    #1B1B1B;
}

.icon-tile {
  display: flex;
  height: 2.5rem;
  width: 2.5rem;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 0.75rem;
  border: 1px solid rgba(255,212,0, 0.22);
  background: rgba(255,212,0, 0.1);
  color: #FFD400;
}

.btn-primary,
.btn-ghost {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 600;
  transition: all 0.2s ease;
}
.btn-primary {
  background: #D71920;
  color: #fff;
}
.btn-primary:hover {
  background: #B5121B;
  box-shadow: 0 8px 24px -8px rgba(215,25,32, 0.6);
  transform: translateY(-2px);
}
.btn-ghost {
  border: 1px solid rgba(255, 255, 255, 0.18);
  color: #FAFAFA;
}
.btn-ghost:hover {
  border-color: rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.06);
}
.btn-primary:active,
.btn-ghost:active {
  transform: scale(0.98);
}

/* ── Skeleton ── */
.skeleton {
  background: linear-gradient(
    100deg,
    rgba(255, 255, 255, 0.04) 30%,
    rgba(255, 255, 255, 0.09) 50%,
    rgba(255, 255, 255, 0.04) 70%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
}
@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
/* tinggi baris headline skeleton menyamai ukuran font hero */
.hero-skel { height: clamp(2.1rem, 8vw, 4.4rem); }

/* ── Hero ── */
.hero {
  min-height: 100vh;
  min-height: 100svh;
}
.hero-title {
  font-size: clamp(2.5rem, 9vw, 5rem);
}
@media (min-width: 1024px) {
  .hero-title { font-size: clamp(3.25rem, 6vw, 5rem); }
}
.hero-glow {
  background:
    radial-gradient(60% 50% at 0% 100%, rgba(215,25,32, 0.2), transparent 70%),
    radial-gradient(40% 40% at 100% 0%, rgba(255,212,0, 0.08), transparent 70%);
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

/* ── CTA ── */
.cta {
  background: linear-gradient(135deg, #8E1016 0%, #B5121B 45%, #5A0D1A 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.cta-sheen {
  background:
    radial-gradient(60% 90% at 100% 0%, rgba(255, 214, 170, 0.22), transparent 65%),
    radial-gradient(50% 70% at 0% 100%, rgba(0, 0, 0, 0.35), transparent 70%);
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
.marquee-wrap::before { left: 0;  background: linear-gradient(90deg,  #111111, transparent); }
.marquee-wrap::after  { right: 0; background: linear-gradient(270deg, #111111, transparent); }

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
  .lb-img,
  .skeleton,
  .animate-ping {
    animation: none;
  }
}
</style>