<template>
  <div class="home min-h-screen overflow-x-hidden bg-[#111113] text-[#F5F3EF] selection:bg-[#D92B22]/40 selection:text-white">

    <!-- ═══════════════ 1. HERO ═══════════════ -->
    <section class="hero relative overflow-hidden bg-[#111113]">
      <div class="absolute inset-0" aria-hidden="true">
        <div
          class="absolute inset-x-0 -top-[10%] h-[120%] will-change-transform"
          :style="{ transform: `translate3d(0, ${parallaxY}px, 0)` }"
        >
          <img
            v-if="!loading.cms"
            v-blur-img
            :src="cms.hero_bg_image || defaultHeroBg"
            alt=""
            fetchpriority="high"
            decoding="async"
            class="h-full w-full object-cover opacity-[0.28]"
          />
        </div>
        <div class="absolute inset-0 bg-gradient-to-r from-[#111113] via-[#111113]/85 to-[#111113]/40"></div>
        <div class="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-[#111113] to-transparent"></div>
        <!-- Ornamen sapuan kuas: satu merah, satu kuning, hanya di sisi foto -->
        <span class="brush-red hero-brush-red"></span>
        <span class="brush-yellow hero-brush-yellow"></span>
      </div>

      <div class="relative z-10 mx-auto grid w-full max-w-7xl grid-cols-1 items-center gap-10 px-5 pb-16 pt-32 sm:px-8 sm:pb-20 sm:pt-36 lg:grid-cols-12 lg:gap-6 lg:px-10 lg:pb-24">
        <div class="space-y-6 lg:col-span-6">

          <!-- Status + lokasi -->
          <div class="hero-in flex flex-wrap items-center gap-2" style="--d: 0ms">
            <div class="flex w-fit items-center gap-2.5 rounded-full bg-white/[0.08] px-3.5 py-2" role="status">
              <span class="relative flex h-2 w-2 shrink-0">
                <span
                  v-if="openStatus.isOpen"
                  class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60"
                ></span>
                <span
                  class="relative inline-flex h-2 w-2 rounded-full"
                  :class="openStatus.isOpen ? 'bg-emerald-400' : 'bg-[#D92B22]'"
                ></span>
              </span>
              <span class="text-[0.8125rem] font-semibold text-[#F5F3EF]">{{ openStatus.label }}</span>
              <span v-if="openStatus.detail" class="text-[0.8125rem] text-[#B8B8C0]">{{ openStatus.detail }}</span>
            </div>
            <span class="rounded-full bg-[#F4C542]/12 px-3.5 py-2 text-[0.8125rem] font-semibold text-[#F4C542]">
              Bekasi, sejak 2024
            </span>
          </div>

          <!-- Headline -->
          <h1
            v-if="!loading.cms"
            class="hero-title hero-in break-words text-[#F5F3EF]"
            style="--d: 100ms"
          >
            <span v-for="(line, i) in headlineLines" :key="i" class="block">{{ line.text }}</span>
          </h1>
          <div v-else class="space-y-3" aria-hidden="true">
            <div class="skeleton hero-skel w-[85%] rounded-xl"></div>
            <div class="skeleton hero-skel w-[60%] rounded-xl"></div>
          </div>

          <p
            v-if="!loading.cms"
            class="hero-in max-w-md text-base leading-relaxed text-[#C9C9D0] sm:text-lg"
            style="--d: 220ms"
          >
            {{ cms.hero_subheadline }}
          </p>
          <div v-else class="max-w-md space-y-2" aria-hidden="true">
            <div class="skeleton h-4 w-full rounded-full"></div>
            <div class="skeleton h-4 w-2/3 rounded-full"></div>
          </div>

          <div class="hero-in flex flex-col gap-3 pt-2 sm:flex-row" style="--d: 320ms">
            <router-link to="/menu" class="btn-yellow group">
              Lihat menu
              <ArrowRight :size="16" class="transition-transform duration-200 group-hover:translate-x-1" />
            </router-link>
            <router-link to="/contact" class="btn-line">
              Kontak kami
            </router-link>
          </div>
        </div>

        <!-- Foto makanan -->
        <div class="hero-in relative lg:col-span-6" style="--d: 260ms">
          <div class="hero-photo relative mx-auto aspect-[5/4] w-full max-w-[34rem] overflow-hidden rounded-[1.75rem] bg-[#1C1C1F] lg:ml-auto lg:mr-10">
            <img
              v-if="!loading.cms"
              v-blur-img
              :src="cms.hero_food_image || defaultHeroFood"
              alt="Menu andalan Masashimura"
              class="h-full w-full object-cover"
            />
            <div v-else class="skeleton h-full w-full" aria-hidden="true"></div>
          </div>
          <!-- Aksen tepi: teks vertikal Jepang -->
          <p class="jp-vertical absolute right-0 top-1/2 hidden -translate-y-1/2 text-xl text-white/85 xl:block" aria-hidden="true">
            まさしむら
          </p>
        </div>
      </div>
    </section>

    <!-- Marquee: satu baris tenang di bawah hero (teks dari CMS) -->
    <div v-if="cms.marquee_text" class="marquee-wrap overflow-hidden bg-[#111113] pb-6 pt-1" aria-hidden="true">
      <div class="animate-marquee flex">
        <div v-for="g in 2" :key="g" class="flex shrink-0 items-center">
          <template v-for="m in 4" :key="m">
            <span class="mx-8 whitespace-nowrap text-[0.8125rem] font-semibold tracking-[0.14em] text-[#9A9AA3]">
              {{ cms.marquee_text }}
            </span>
            <span class="h-1.5 w-1.5 shrink-0 rounded-full bg-[#F4C542]"></span>
          </template>
        </div>
      </div>
    </div>
    <div v-else class="bg-[#111113] pb-6" aria-hidden="true"></div>

    <!-- ═══════════════ 2. RINGKASAN (krem) ═══════════════ -->
    <section class="on-cream">
      <div ref="metricsRef" class="mx-auto max-w-7xl px-5 pt-10 sm:px-8 lg:px-10">
        <div class="metric-strip grid grid-cols-3 divide-x divide-[#E5E2DC] rounded-2xl bg-white">
          <div class="px-3 py-5 text-center sm:px-8 sm:py-6 sm:text-left">
            <p class="metric-num">{{ metricDisplays.m1 }}</p>
            <p class="metric-label">Berdiri sejak</p>
          </div>
          <div class="px-3 py-5 text-center sm:px-8 sm:py-6 sm:text-left">
            <p class="metric-num">{{ metricDisplays.m2 }}</p>
            <p class="metric-label">Varian menu</p>
          </div>
          <div class="px-3 py-5 text-center sm:px-8 sm:py-6 sm:text-left">
            <p
              class="metric-num whitespace-nowrap"
              :class="metric3IsStars ? '!text-[1rem] !tracking-tighter text-[#C7901A] sm:!text-[1.5rem]' : ''"
            >{{ cms.metric_3 || "–" }}</p>
            <p class="metric-label">Rating pelanggan</p>
          </div>
        </div>
      </div>

      <!-- ═══════════════ 3. MENU TERLARIS ═══════════════ -->
      <div v-reveal class="mx-auto max-w-7xl px-5 py-16 sm:px-8 sm:py-20 lg:px-10 lg:py-24">
        <div class="grid grid-cols-1 gap-10 lg:grid-cols-12 lg:gap-12">
          <div class="space-y-4 lg:col-span-4 lg:pt-4">
            <h2 class="h-section">Menu terlaris</h2>
            <p class="max-w-xs text-base leading-relaxed text-[#66666D]">
              Yang paling sering dipesan pelanggan kami.
            </p>
            <router-link to="/menu" class="link-red group hidden lg:inline-flex">
              Lihat semua menu
              <ArrowRight :size="15" class="transition-transform duration-200 group-hover:translate-x-1" />
            </router-link>
          </div>

          <div class="lg:col-span-8">
            <!-- Skeleton -->
            <div v-if="loading.best" class="grid grid-cols-2 gap-4 sm:grid-cols-3" aria-hidden="true">
              <div v-for="n in 3" :key="n" class="overflow-hidden rounded-2xl bg-white">
                <div class="skeleton-light aspect-[4/3] w-full"></div>
                <div class="space-y-2.5 p-4">
                  <div class="skeleton-light h-4 w-3/4 rounded-full"></div>
                  <div class="skeleton-light h-4 w-1/2 rounded-full"></div>
                </div>
              </div>
            </div>

            <div v-else class="grid grid-cols-2 gap-4 sm:grid-cols-3 sm:gap-5">
              <router-link
                v-for="(item, idx) in topBestSellers"
                :key="idx"
                to="/menu"
                class="menu-card group"
                :aria-label="`${item.name}, ${formatRupiah(item.price)}. Buka halaman menu`"
              >
                <div class="relative aspect-[4/3] w-full overflow-hidden bg-[#E9E5DC]">
                  <img
                    v-blur-img
                    :src="item.image"
                    :alt="item.name"
                    loading="lazy"
                    class="h-full w-full object-cover transition-transform duration-500 ease-out group-hover:scale-[1.04]"
                  />
                  <span v-if="idx === 0" class="menu-tag bg-[#D92B22] text-white">Terlaris</span>
                  <span v-else-if="idx === 1" class="menu-tag bg-[#F4C542] text-[#2A1F00]">Favorit</span>
                </div>
                <div class="flex items-end justify-between gap-2 p-3.5 sm:p-4">
                  <div class="min-w-0">
                    <h3 class="line-clamp-2 text-[0.9375rem] font-bold leading-snug text-[#202024]">{{ item.name }}</h3>
                    <p class="mt-1 text-sm font-semibold tabular-nums text-[#66666D]">{{ formatRupiah(item.price) }}</p>
                  </div>
                  <span class="menu-add" aria-hidden="true"><Plus :size="16" /></span>
                </div>
              </router-link>

              <div
                v-if="bestSellers.length === 0"
                class="col-span-full rounded-2xl bg-white py-16 text-center text-sm text-[#66666D]"
              >
                Menu belum tersedia saat ini.
              </div>
            </div>

            <router-link to="/menu" class="btn-dark mt-8 w-full lg:hidden">
              Lihat semua menu
              <ArrowRight :size="16" />
            </router-link>
          </div>
        </div>
      </div>

      <!-- ═══════════════ 4. PROMO / EVENT ═══════════════ -->
      <PromoSection :promos="promos" />

      <!-- ═══════════════ 5. TENTANG ═══════════════ -->
      <div v-reveal class="mx-auto max-w-7xl px-5 py-16 sm:px-8 sm:py-20 lg:px-10 lg:py-24">
        <div class="grid grid-cols-1 items-center gap-10 lg:grid-cols-12 lg:gap-16">
          <div class="space-y-5 lg:col-span-5">
            <h2 class="h-section">Tentang Masashimura</h2>
            <p v-if="!loading.cms" class="max-w-md text-base leading-[1.85] text-[#4A4A52]">{{ cms.about_text }}</p>
            <div v-else class="max-w-md space-y-2.5" aria-hidden="true">
              <div class="skeleton-light h-4 w-full rounded-full"></div>
              <div class="skeleton-light h-4 w-full rounded-full"></div>
              <div class="skeleton-light h-4 w-4/5 rounded-full"></div>
            </div>
            <router-link to="/contact" class="link-red group inline-flex">
              Lokasi &amp; kontak
              <ArrowRight :size="15" class="transition-transform duration-200 group-hover:translate-x-1" />
            </router-link>
          </div>

          <div class="lg:col-span-7">
            <div class="relative aspect-[16/10] overflow-hidden rounded-[1.5rem] bg-[#E9E5DC]">
              <img
                v-if="!loading.cms"
                v-blur-img
                :src="cms.about_image || defaultAboutImage"
                alt="Suasana Masashimura"
                loading="lazy"
                class="h-full w-full object-cover"
              />
              <div v-else class="skeleton-light h-full w-full" aria-hidden="true"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══════════════ 6. FASILITAS ═══════════════ -->
      <div class="mx-auto max-w-7xl px-5 pb-20 sm:px-8 sm:pb-24 lg:px-10 lg:pb-28">
        <h2 class="h-section mb-8 sm:mb-10">Apa yang lo dapet</h2>

        <div v-if="loading.bento" class="grid grid-cols-1 gap-3 lg:grid-cols-12" aria-hidden="true">
          <div class="skeleton-light min-h-[200px] rounded-2xl lg:col-span-5"></div>
          <div class="grid auto-rows-fr grid-cols-2 gap-3 lg:col-span-7">
            <div v-for="n in 4" :key="n" class="skeleton-light min-h-[110px] rounded-2xl"></div>
          </div>
        </div>

        <div v-else class="grid grid-cols-1 gap-3 sm:gap-4 lg:grid-cols-12">
          <div v-if="bentoLarge.length" class="flex flex-col gap-3 sm:gap-4 lg:col-span-5">
            <div
              v-for="(bento, i) in bentoLarge"
              :key="'l' + i"
              class="bento-feature relative flex min-h-[200px] flex-1 flex-col justify-between overflow-hidden rounded-2xl p-7 sm:min-h-[240px] sm:p-9"
            >
              <span class="brush-red bento-brush" aria-hidden="true"></span>
              <div class="relative flex h-12 w-12 items-center justify-center rounded-xl bg-[#F4C542] text-[#2A1F00]">
                <component :is="getIcon(bento.icon_name)" :size="22" />
              </div>
              <span class="relative text-2xl font-bold leading-tight tracking-tight text-white sm:text-[1.75rem]">
                {{ bento.title }}
              </span>
            </div>
          </div>

          <div
            class="grid auto-rows-fr grid-cols-2 gap-3 sm:gap-4"
            :class="bentoLarge.length ? 'lg:col-span-7' : 'lg:col-span-12 lg:grid-cols-4'"
          >
            <div
              v-for="(bento, i) in bentoSmall"
              :key="'s' + i"
              class="bento-tile flex min-h-[110px] flex-col justify-between gap-5 rounded-2xl bg-white p-5 sm:min-h-[128px] sm:p-6"
              :class="isBentoOrphan(i) ? 'col-span-2' : ''"
            >
              <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[#D92B22]/[0.09] text-[#D92B22]">
                <component :is="getIcon(bento.icon_name)" :size="18" />
              </div>
              <span class="text-[0.9375rem] font-bold leading-snug text-[#202024] sm:text-base">
                {{ bento.title }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════ 7. GALLERY (gelap) ═══════════════ -->
    <section class="bg-[#111113] py-16 sm:py-20 lg:py-24">
      <div class="mx-auto max-w-7xl px-5 sm:px-8 lg:px-10">
        <h2 class="h-section-dark mb-8 sm:mb-10">Gallery</h2>

        <div
          v-if="!loading.gallery && galleryCategories.length > 2"
          class="no-scrollbar -mx-5 mb-8 flex gap-2 overflow-x-auto px-5 pb-1 sm:mx-0 sm:flex-wrap sm:px-0"
        >
          <button
            v-for="cat in galleryCategories"
            :key="cat"
            type="button"
            @click="setCategory(cat)"
            :aria-pressed="activeCategory === cat"
            :class="[
              activeCategory === cat
                ? 'bg-[#D92B22] text-white'
                : 'bg-white/[0.07] text-[#C9C9D0] hover:bg-white/[0.12] hover:text-white',
              'min-h-[44px] shrink-0 cursor-pointer whitespace-nowrap rounded-full px-5 text-sm font-semibold transition-colors'
            ]"
          >
            {{ cat }}
          </button>
        </div>

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
              'group relative cursor-pointer overflow-hidden rounded-2xl border-0 bg-[#1C1C1F] p-0 text-left'
            ]"
          >
            <div class="h-full w-full transition-transform duration-500 ease-out group-hover:scale-[1.04]">
              <img
                v-blur-img
                :src="img.image_url"
                :alt="img.title || 'Dokumentasi Masashimura'"
                loading="lazy"
                class="h-full w-full object-cover"
              />
            </div>
            <div class="absolute inset-0 flex items-end bg-gradient-to-t from-black/75 via-black/0 to-transparent p-3 opacity-0 transition-opacity duration-300 group-hover:opacity-100 group-focus-visible:opacity-100 sm:p-4">
              <div class="min-w-0 space-y-0.5">
                <p class="line-clamp-1 text-sm font-bold text-white">{{ img.title || 'Masashimura' }}</p>
                <p v-if="img.category" class="text-xs font-semibold text-[#F4C542]">{{ img.category }}</p>
              </div>
            </div>
            <div class="absolute right-2.5 top-2.5 flex h-8 w-8 items-center justify-center rounded-full bg-black/55 opacity-0 backdrop-blur-md transition-opacity duration-300 group-hover:opacity-100">
              <Expand :size="14" class="text-white" />
            </div>
          </button>

          <div
            v-if="visibleGallery.length === 0"
            class="col-span-full row-span-2 flex items-center justify-center rounded-2xl bg-white/[0.04] text-center text-sm text-[#9A9AA3]"
          >
            Belum ada foto.
          </div>
        </div>

        <div v-if="!loading.gallery && filteredGallery.length > visibleGallery.length" class="mt-10 flex justify-center">
          <button type="button" @click="galleryLimit += 8" class="btn-line cursor-pointer">
            Muat lebih banyak ({{ filteredGallery.length - visibleGallery.length }})
          </button>
        </div>
      </div>
    </section>

    <!-- LIGHTBOX GALLERY -->
    <transition name="lightbox-fade">
      <div
        v-if="lightboxIndex !== null"
        class="fixed inset-0 z-[60] flex items-center justify-center bg-[#0A0A0B]/95 p-4 backdrop-blur-sm sm:p-10"
        role="dialog" aria-modal="true" aria-label="Galeri foto"
        @click.self="closeLightbox"
        @touchstart.passive="onTouchStart"
        @touchend="handleSwipe($event, nextImage, prevImage)"
      >
        <button
          type="button" @click="closeLightbox" aria-label="Tutup"
          class="absolute right-4 top-4 z-10 flex h-12 w-12 cursor-pointer items-center justify-center rounded-full bg-white/10 text-white transition hover:bg-white/20 sm:right-8 sm:top-8"
        >
          <X :size="18" />
        </button>

        <span class="absolute left-5 top-6 text-sm font-semibold tabular-nums text-[#B8B8C0] sm:left-10 sm:top-10">
          {{ lightboxIndex + 1 }} / {{ visibleGallery.length }}
        </span>

        <button
          v-if="visibleGallery.length > 1" type="button" @click.stop="prevImage" aria-label="Foto sebelumnya"
          class="absolute left-2 top-1/2 z-10 flex h-12 w-12 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full bg-white/10 text-white transition hover:bg-white/20 sm:left-8"
        >
          <ChevronLeft :size="20" />
        </button>
        <button
          v-if="visibleGallery.length > 1" type="button" @click.stop="nextImage" aria-label="Foto berikutnya"
          class="absolute right-2 top-1/2 z-10 flex h-12 w-12 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full bg-white/10 text-white transition hover:bg-white/20 sm:right-8"
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
            <p class="text-base font-bold text-[#F5F3EF]">{{ currentLightboxImage?.title || 'Masashimura' }}</p>
            <p v-if="currentLightboxImage?.category" class="text-sm font-semibold text-[#F4C542]">{{ currentLightboxImage.category }}</p>
          </div>
        </div>
      </div>
    </transition>

    <!-- ═══════════════ 8. REVIEW (krem) ═══════════════ -->
    <section class="on-cream">
      <div class="mx-auto max-w-4xl px-5 py-16 sm:px-8 sm:py-20 lg:px-10 lg:py-24">
        <h2 class="h-section mb-10 sm:mb-12">Kata pelanggan</h2>

        <div v-if="loading.reviews" class="space-y-6" aria-hidden="true">
          <div class="skeleton-light h-8 w-8 rounded-full"></div>
          <div class="max-w-2xl space-y-3">
            <div class="skeleton-light h-5 w-full rounded-full"></div>
            <div class="skeleton-light h-5 w-5/6 rounded-full"></div>
            <div class="skeleton-light h-5 w-2/3 rounded-full"></div>
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
              <Quote :size="32" class="text-[#D92B22]" />
              <blockquote class="max-w-2xl font-[family-name:var(--font-display)] text-xl font-semibold leading-relaxed text-[#202024] sm:text-2xl">
                “{{ review.text }}”
              </blockquote>
              <figcaption class="flex items-center gap-3">
                <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[#111113] text-sm font-bold uppercase text-[#F4C542]">
                  {{ (review.name || '?').trim().charAt(0) }}
                </span>
                <span class="flex min-w-0 flex-col">
                  <span class="truncate text-sm font-bold text-[#202024]">{{ review.name }}</span>
                  <span class="text-sm text-[#66666D]">{{ review.status }}</span>
                </span>
              </figcaption>
            </figure>
          </div>

          <div v-if="reviews.length > 1" class="mt-10 flex items-center gap-2" aria-hidden="true">
            <span
              v-for="(r, i) in reviews"
              :key="i"
              class="block h-1.5 rounded-full transition-all duration-500"
              :class="i === currentReviewIndex ? 'w-8 bg-[#D92B22]' : 'w-1.5 bg-[#202024]/20'"
            ></span>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════ 9. CTA ═══════════════ -->
    <section class="bg-[#111113] px-5 pb-16 pt-4 sm:px-8 sm:pb-20 lg:px-10 lg:pb-24">
      <div class="cta relative mx-auto grid max-w-7xl grid-cols-1 items-center gap-8 overflow-hidden rounded-[1.75rem] p-8 sm:p-12 lg:grid-cols-2 lg:gap-16 lg:p-16">
        <span class="brush-yellow cta-brush" aria-hidden="true"></span>

        <div class="relative space-y-4">
          <h2 class="text-4xl font-black leading-[1.1] text-white sm:text-5xl">
            Udah laper?
          </h2>
          <p class="max-w-xs text-base leading-relaxed text-white/85">
            Pilih menu favorit dan nikmati langsung di kedai atau lewat web ordering.
          </p>
        </div>

        <div class="relative flex flex-col gap-3 sm:flex-row lg:justify-end">
          <router-link to="/menu" class="btn-yellow group">
            Pesan via web
            <ArrowRight :size="16" class="transition-transform duration-200 group-hover:translate-x-1" />
          </router-link>
          <router-link to="/contact" class="btn-line">
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
  Expand, X, ChevronLeft, ChevronRight, ArrowRight, Quote, Plus
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
  return lines.map((text) => ({ text, accent: false }))
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
  Palet Home
  Charcoal #111113 (hero, gallery, CTA) · Krem #F7F5F0 (konten) · Putih #FFFFFF (kartu)
  Merah #D92B22 (aksi utama) · Kuning #F4C542 (penanda & CTA di atas gelap)
*/

a:focus-visible,
button:focus-visible {
  outline: 2px solid #F4C542;
  outline-offset: 3px;
}
.on-cream a:focus-visible,
.on-cream button:focus-visible { outline-color: #202024; }

/* ── Bidang krem ── */
.on-cream { background: #F7F5F0; color: #202024; }

/* ── Judul section (display serif) ── */
.h-section,
.h-section-dark {
  font-family: var(--font-display);
  font-size: clamp(1.75rem, 3.4vw, 2.25rem);
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.015em;
}
.h-section { color: #202024; }
.h-section-dark { color: #F5F3EF; }

.link-red {
  align-items: center;
  gap: 0.5rem;
  min-height: 44px;
  font-size: 0.9375rem;
  font-weight: 700;
  color: #B8201A;
  transition: color 0.2s;
}
.link-red:hover { color: #7A1410; }

/* ── Tombol ── */
.btn-yellow,
.btn-line,
.btn-dark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  min-height: 52px;
  padding: 0 1.9rem;
  border-radius: 12px;
  font-size: 0.9375rem;
  font-weight: 700;
  white-space: nowrap;
  transition: background-color 0.2s, border-color 0.2s, color 0.2s, transform 0.15s;
}
.btn-yellow { background: #F4C542; color: #1F1700; }
.btn-yellow:hover { background: #FFD65C; }
.btn-line { border: 1.5px solid rgb(255 255 255 / 0.28); color: #F5F3EF; }
.btn-line:hover { border-color: rgb(255 255 255 / 0.6); background: rgb(255 255 255 / 0.06); }
.btn-dark { background: #111113; color: #fff; }
.btn-dark:hover { background: #26262B; }
.btn-yellow:active, .btn-line:active, .btn-dark:active { transform: translateY(1px); }

/* ── Hero ── */
.hero { min-height: clamp(34rem, 86svh, 47rem); display: flex; align-items: center; }
.hero > .relative { width: 100%; }
.hero-title {
  font-family: var(--font-display);
  font-weight: 900;
  font-size: clamp(2.5rem, 8.5vw, 3.5rem);
  line-height: 1.12;
  letter-spacing: -0.02em;
}
@media (min-width: 1024px) {
  .hero-title { font-size: clamp(3rem, 4.6vw, 4rem); }
}
.hero-skel { height: clamp(2.1rem, 7vw, 3.6rem); }

.hero-photo { box-shadow: 0 30px 60px -28px rgb(0 0 0 / 0.8); }
.hero-brush-red {
  right: -6%;
  bottom: -8%;
  width: 46%;
  height: 78%;
  opacity: 0.92;
  transform: skewX(-14deg);
}
.hero-brush-yellow {
  right: -3%;
  bottom: 0;
  width: 15%;
  height: 34%;
  transform: skewX(-14deg);
}
@media (max-width: 1023px) {
  .hero-brush-red { right: -20%; bottom: -4%; width: 70%; height: 46%; opacity: 0.7; }
  .hero-brush-yellow { right: -8%; width: 26%; height: 18%; }
}

@keyframes heroIn { to { opacity: 1; transform: none; } }
.hero-in {
  opacity: 0;
  transform: translateY(16px);
  animation: heroIn 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  animation-delay: var(--d, 0ms);
}

/* ── Strip metrik ── */
.metric-strip { box-shadow: 0 1px 2px rgb(32 32 36 / 0.04), 0 14px 34px -22px rgb(32 32 36 / 0.22); }
.metric-num {
  font-family: var(--font-display);
  font-size: clamp(1.25rem, 4.4vw, 1.75rem);
  font-weight: 700;
  line-height: 1.15;
  color: #202024;
  font-variant-numeric: tabular-nums;
}
.metric-label { margin-top: 0.15rem; font-size: 0.8125rem; color: #66666D; }

/* ── Kartu menu ── */
.menu-card {
  display: block;
  overflow: hidden;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 1px 2px rgb(32 32 36 / 0.05), 0 12px 28px -20px rgb(32 32 36 / 0.3);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.menu-card:hover { transform: translateY(-3px); box-shadow: 0 1px 2px rgb(32 32 36 / 0.05), 0 20px 36px -20px rgb(32 32 36 / 0.38); }
.menu-tag {
  position: absolute;
  left: 10px;
  top: 10px;
  padding: 0.25rem 0.65rem;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 800;
}
.menu-add {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: #111113;
  color: #fff;
  transition: background-color 0.2s;
}
.menu-card:hover .menu-add { background: #D92B22; }

/* ── Bento ── */
.bento-feature { background: #111113; }
.bento-brush {
  right: -12%;
  bottom: -18%;
  width: 62%;
  height: 70%;
  opacity: 0.9;
  transform: skewX(-14deg);
}
.bento-tile { box-shadow: 0 1px 2px rgb(32 32 36 / 0.05), 0 12px 28px -22px rgb(32 32 36 / 0.3); }

/* ── Skeleton ── */
.skeleton,
.skeleton-light {
  background-size: 200% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
}
.skeleton {
  background-image: linear-gradient(100deg, rgb(255 255 255 / 0.04) 30%, rgb(255 255 255 / 0.1) 50%, rgb(255 255 255 / 0.04) 70%);
}
.skeleton-light {
  background-image: linear-gradient(100deg, #ECE8DF 30%, #F6F3EC 50%, #ECE8DF 70%);
}
@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── CTA ── */
.cta { background: linear-gradient(135deg, #B8201A 0%, #D92B22 60%, #A31B15 100%); }
.cta-brush {
  right: -4%;
  top: -12%;
  width: 20%;
  height: 130%;
  opacity: 0.9;
  transform: skewX(-14deg);
}
@media (max-width: 1023px) {
  .cta-brush { right: -10%; width: 34%; opacity: 0.6; }
}

/* ── Marquee ── */
@keyframes marquee {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
.animate-marquee { width: max-content; animation: marquee 70s linear infinite; }
.marquee-wrap:hover .animate-marquee { animation-play-state: paused; }
.marquee-wrap { position: relative; }
.marquee-wrap::before,
.marquee-wrap::after {
  content: "";
  position: absolute;
  top: 0;
  bottom: 0;
  width: 12%;
  z-index: 1;
  pointer-events: none;
}
.marquee-wrap::before { left: 0;  background: linear-gradient(90deg,  #111113, transparent); }
.marquee-wrap::after  { right: 0; background: linear-gradient(270deg, #111113, transparent); }

/* ── Lightbox ── */
.lightbox-fade-enter-active,
.lightbox-fade-leave-active { transition: opacity 0.25s ease; }
.lightbox-fade-enter-from,
.lightbox-fade-leave-to { opacity: 0; }
@keyframes lbIn {
  from { opacity: 0; transform: scale(0.98); }
  to   { opacity: 1; transform: scale(1); }
}
.lb-img { animation: lbIn 0.3s ease; }

/* ── Reveal (hanya 2 section, bukan semua) ── */
.reveal {
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.6s cubic-bezier(0.16, 1, 0.3, 1), transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}
.reveal-visible { opacity: 1; transform: none; }

/* ── Gambar: fade saat termuat ── */
.img-blur {
  opacity: 0;
  transition: opacity 0.5s ease;
}
.img-blur.img-loaded { opacity: 1; }
.hero img.img-blur.img-loaded { opacity: 1; }

.no-scrollbar { scrollbar-width: none; }
.no-scrollbar::-webkit-scrollbar { display: none; }

@media (prefers-reduced-motion: reduce) {
  .reveal, .img-blur { transition: none; opacity: 1; transform: none; }
  .hero-in { animation: none; opacity: 1; transform: none; }
  .animate-marquee, .lb-img, .skeleton, .skeleton-light, .animate-ping { animation: none; }
  .menu-card, .menu-card:hover { transition: none; transform: none; }
}
</style>
