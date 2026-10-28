<template>
  <div class="home min-h-screen overflow-x-hidden bg-[#111113] text-[#F5F3EF] selection:bg-[#D92B22]/40 selection:text-white">

    <!-- ═══════════════ 1. HERO ═══════════════ -->
    <section class="hero relative overflow-hidden bg-[#111113]">
      <div class="pattern-seigaiha absolute inset-0" aria-hidden="true"></div>
      <div class="absolute inset-0" aria-hidden="true">
        <div class="absolute inset-x-0 -top-[10%] h-[120%] will-change-transform" :style="{ transform: `translate3d(0, ${parallaxY}px, 0)` }">
          <img
            v-if="!loading.cms"
            v-blur-img
            :src="cms.hero_bg_image || defaultHeroBg"
            alt=""
            fetchpriority="high"
            decoding="async"
            class="h-full w-full object-cover opacity-[0.16]"
          />
        </div>
        <div class="absolute inset-0 bg-gradient-to-r from-[#111113] via-[#111113]/85 to-[#111113]/30"></div>
        <!-- Bentuk geometri: lingkaran merah + balok kuning miring -->
        <span class="hero-sun"></span>
        <span class="hero-slab-red"></span>
        <span class="hero-slab-yellow"></span>
      </div>

      <div class="relative z-10 mx-auto grid w-full max-w-7xl grid-cols-1 items-center gap-12 px-5 pb-28 pt-36 sm:px-8 sm:pt-40 lg:grid-cols-12 lg:gap-6 lg:px-10 lg:pb-32">
        <div class="space-y-6 lg:col-span-6">

          <div class="hero-in flex flex-wrap items-center gap-3" style="--d: 0ms">
            <div v-if="openStatus.ready" class="flex w-fit items-center gap-2.5 rounded-full border-2 border-white/15 bg-white/[0.05] px-3.5 py-2" role="status">
              <span class="relative flex h-2 w-2 shrink-0">
                <span v-if="openStatus.isOpen" class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60"></span>
                <span class="relative inline-flex h-2 w-2 rounded-full" :class="openStatus.isOpen ? 'bg-emerald-400' : 'bg-[#D92B22]'"></span>
              </span>
              <span class="text-[0.8125rem] font-bold text-[#F5F3EF]">{{ openStatus.label }}</span>
              <span v-if="openStatus.detail" class="text-[0.8125rem] text-[#B8B8C0]">{{ openStatus.detail }}</span>
            </div>
            <span class="sticker">Bekasi, sejak 2024</span>
          </div>

          <h1 v-if="!loading.cms" class="hero-title hero-in break-words" style="--d: 100ms">
            <span v-for="(line, i) in headlineLines" :key="i" class="block" :class="line.accent ? 'hero-accent' : 'text-[#F5F3EF]'">{{ line.text }}</span>
          </h1>
          <div v-else class="space-y-3" aria-hidden="true">
            <div class="skeleton hero-skel w-[85%] rounded-xl"></div>
            <div class="skeleton hero-skel w-[60%] rounded-xl"></div>
          </div>

          <p v-if="!loading.cms" class="hero-in max-w-md text-base leading-relaxed text-[#D2D2D8] sm:text-lg" style="--d: 220ms">
            {{ cms.hero_subheadline }}
          </p>
          <div v-else class="max-w-md space-y-2" aria-hidden="true">
            <div class="skeleton h-4 w-full rounded-full"></div>
            <div class="skeleton h-4 w-2/3 rounded-full"></div>
          </div>

          <div class="hero-in flex flex-col gap-4 pt-3 sm:flex-row sm:items-center" style="--d: 320ms">
            <router-link to="/menu" class="pop-btn pop-btn--on-dark">
              Lihat menu
              <span class="pop-btn-dot" aria-hidden="true"><ArrowUpRight :size="15" /></span>
            </router-link>
            <router-link to="/contact" class="pop-btn pop-btn--ghost">Kontak kami</router-link>
          </div>
        </div>

        <!-- Foto makanan: kartu miring + stiker + segel -->
        <div class="hero-in relative lg:col-span-6" style="--d: 260ms">
          <div class="hero-card-back" aria-hidden="true"></div>
          <div class="hero-frame relative mx-auto aspect-[5/4] w-full max-w-[34rem] overflow-hidden bg-[#1C1C1F] lg:ml-auto lg:mr-12">
            <img v-if="!loading.cms" v-blur-img :src="cms.hero_food_image || defaultHeroFood" alt="Menu andalan Masashimura" class="h-full w-full object-cover" />
            <div v-else class="skeleton h-full w-full" aria-hidden="true"></div>
          </div>
          <span class="sticker sticker--red absolute left-1 top-3 z-10 text-[0.9375rem] sm:left-4" aria-hidden="true">おいしい！</span>
          <span class="hanko absolute -bottom-3 right-2 z-10 !h-12 !w-12 !rounded-xl !text-xl sm:right-8" aria-hidden="true">ま</span>

          <!-- Lencana berputar -->
          <svg class="hero-badge absolute -bottom-6 left-0 z-10 h-28 w-28 sm:left-4" viewBox="0 0 120 120" aria-hidden="true">
            <circle cx="60" cy="60" r="57" fill="#F4C542" stroke="#111113" stroke-width="3" />
            <defs><path id="badge-circle" d="M60,60 m-42,0 a42,42 0 1,1 84,0 a42,42 0 1,1 -84,0" /></defs>
            <g class="hero-badge-ring">
              <text font-size="8.6" font-weight="800" letter-spacing="1.5" fill="#111113" font-family="var(--font-ui)">
                <textPath href="#badge-circle">GOOD FOOD • GOOD VIBES • BEKASI •</textPath>
              </text>
            </g>
            <text x="60" y="73" text-anchor="middle" font-size="34" fill="#D92B22" font-family="var(--font-display)">味</text>
          </svg>

          <p class="jp-vertical absolute -right-1 top-1/4 hidden text-lg text-[#F4C542] xl:block" aria-hidden="true">まさしむら</p>
        </div>
      </div>
    </section>

    <!-- Pita ticker miring -->
    <div class="relative z-20 -mt-14 mb-0 overflow-hidden pb-10 pt-6" aria-hidden="true">
      <div class="tape marquee-wrap overflow-hidden py-3">
        <div class="animate-marquee flex">
          <div v-for="g in 2" :key="g" class="flex shrink-0 items-center">
            <template v-for="m in 3" :key="m">
              <template v-if="cms.marquee_text">
                <span class="mx-6 whitespace-nowrap text-sm font-extrabold tracking-wide sm:text-base">{{ cms.marquee_text }}</span>
                <span class="h-2.5 w-2.5 shrink-0 rotate-45 bg-[#D92B22]"></span>
              </template>
              <template v-for="w in tickerJp" :key="w">
                <span class="mx-6 whitespace-nowrap font-[family-name:var(--font-display)] text-sm sm:text-base">{{ w }}</span>
                <span class="h-2.5 w-2.5 shrink-0 rotate-45 bg-[#D92B22]"></span>
              </template>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════ 2. KRUNCI (krem berpola titik) ═══════════════ -->
    <section class="dot-grid on-cream">
      <div ref="metricsRef" class="mx-auto max-w-7xl px-5 pt-14 sm:px-8 lg:px-10">
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-3 sm:gap-6">
          <div class="pop-card px-6 py-5">
            <p class="metric-num">{{ metricDisplays.m1 }}</p>
            <p class="metric-label">Berdiri sejak</p>
          </div>
          <div class="pop-card pop-card--yellow px-6 py-5">
            <p class="metric-num">{{ metricDisplays.m2 }}</p>
            <p class="metric-label">Varian menu</p>
          </div>
          <div class="pop-card pop-card--red px-6 py-5">
            <p class="metric-num whitespace-nowrap" :class="metric3IsStars ? '!text-[1.5rem] !tracking-tight' : ''">{{ cms.metric_3 || "–" }}</p>
            <p class="metric-label text-outline !text-white">Rating pelanggan</p>
          </div>
        </div>
      </div>

      <!-- ═══════════════ 3. MENU TERLARIS ═══════════════ -->
      <div v-reveal class="mx-auto max-w-7xl px-5 py-20 sm:px-8 sm:py-24 lg:px-10">
        <div class="grid grid-cols-1 gap-10 lg:grid-cols-12 lg:gap-12">
          <div class="space-y-4 lg:col-span-4 lg:pt-3">
            <p class="eyebrow-jp"><span class="hanko" aria-hidden="true">人気</span>Favorit</p>
            <h2 class="h-section">{{ bestCopy.title }}</h2>
            <p class="max-w-xs text-base leading-relaxed text-[#5A5A62]">{{ bestCopy.sub }}</p>
            <router-link to="/menu" class="link-pop hidden lg:inline-flex">
              Lihat semua menu
              <ArrowUpRight :size="16" aria-hidden="true" />
            </router-link>
          </div>

          <div class="lg:col-span-8">
            <div v-if="loading.best" class="grid grid-cols-2 gap-5 sm:grid-cols-3" aria-hidden="true">
              <div v-for="n in 3" :key="n" class="pop-card overflow-hidden">
                <div class="skeleton-light aspect-[4/3] w-full"></div>
                <div class="space-y-2.5 p-4">
                  <div class="skeleton-light h-4 w-3/4 rounded-full"></div>
                  <div class="skeleton-light h-4 w-1/2 rounded-full"></div>
                </div>
              </div>
            </div>

            <div v-else class="grid grid-cols-2 gap-5 sm:grid-cols-3 sm:gap-6">
              <router-link
                v-for="(item, idx) in topBestSellers"
                :key="idx"
                to="/menu"
                class="menu-card pop-card group"
                :aria-label="`${item.name}, ${formatRupiah(item.price)}. Buka halaman menu`"
              >
                <div class="relative aspect-[4/3] w-full overflow-hidden rounded-t-[18px] bg-[#E9E5DC]">
                  <img v-blur-img :src="item.image" :alt="item.name" loading="lazy" class="h-full w-full object-cover transition-transform duration-500 ease-out group-hover:scale-[1.05]" />
                  <span
                    v-if="item.badge"
                    class="sticker absolute left-2.5 top-2.5"
                    :class="idx === 0 || item.badge === 'Rekomendasi' ? 'sticker--red' : item.badge === 'Baru' ? 'sticker--pink' : ''"
                  >{{ item.badge }}</span>
                </div>
                <div class="flex items-end justify-between gap-2 border-t-2 border-[#111113] p-3.5 sm:p-4">
                  <div class="min-w-0">
                    <h3 class="line-clamp-2 text-[0.9375rem] font-extrabold leading-snug text-[#111113]">{{ item.name }}</h3>
                    <p class="mt-1 text-sm font-extrabold tabular-nums text-[#D92B22]">{{ formatRupiah(item.price) }}</p>
                  </div>
                  <span class="menu-add" aria-hidden="true"><Plus :size="18" :stroke-width="3" /></span>
                </div>
              </router-link>

              <div v-if="bestSellers.length === 0" class="pop-card col-span-full py-16 text-center text-sm text-[#5A5A62]">Menu belum tersedia saat ini.</div>
            </div>

            <router-link to="/menu" class="pop-btn mt-8 w-full lg:hidden">
              Lihat semua menu
              <span class="pop-btn-dot" aria-hidden="true"><ArrowUpRight :size="15" /></span>
            </router-link>
          </div>
        </div>
      </div>

      <!-- ═══════════════ 4. PROMO / EVENT ═══════════════ -->
      <PromoSection :promos="promos" />

      <!-- ═══════════════ 5. TENTANG ═══════════════ -->
      <div v-reveal class="mx-auto max-w-7xl px-5 py-16 sm:px-8 sm:py-20 lg:px-10 lg:py-24">
        <div class="grid grid-cols-1 items-center gap-12 lg:grid-cols-12 lg:gap-16">
          <div class="space-y-5 lg:col-span-5">
            <p class="eyebrow-jp"><span class="hanko" aria-hidden="true">物語</span>Cerita kami</p>
            <h2 class="h-section">Tentang Masashimura</h2>
            <p v-if="!loading.cms" class="max-w-md text-base leading-[1.85] text-[#3F3F46]">{{ cms.about_text }}</p>
            <div v-else class="max-w-md space-y-2.5" aria-hidden="true">
              <div class="skeleton-light h-4 w-full rounded-full"></div>
              <div class="skeleton-light h-4 w-full rounded-full"></div>
              <div class="skeleton-light h-4 w-4/5 rounded-full"></div>
            </div>
            <router-link to="/contact" class="link-pop inline-flex">
              Lokasi &amp; kontak
              <ArrowUpRight :size="16" aria-hidden="true" />
            </router-link>
          </div>

          <div class="relative lg:col-span-7">
            <div class="about-photo relative aspect-[16/10] overflow-hidden bg-[#E9E5DC]">
              <img v-if="!loading.cms" v-blur-img :src="cms.about_image || defaultAboutImage" alt="Suasana Masashimura" loading="lazy" class="h-full w-full object-cover" />
              <div v-else class="skeleton-light h-full w-full" aria-hidden="true"></div>
            </div>
            <span class="sticker sticker--pink absolute -top-4 right-4 z-10 rotate-[4deg] text-[0.875rem]" aria-hidden="true">nongkrong yuk!</span>
          </div>
        </div>
      </div>

      <!-- ═══════════════ 6. FASILITAS ═══════════════ -->
      <div class="mx-auto max-w-7xl px-5 pb-24 sm:px-8 sm:pb-28 lg:px-10">
        <p class="eyebrow-jp mb-4"><span class="hanko" aria-hidden="true">設備</span>Fasilitas</p>
        <h2 class="h-section mb-10">Apa yang lo dapet</h2>

        <div v-if="loading.bento" class="grid grid-cols-1 gap-4 lg:grid-cols-12" aria-hidden="true">
          <div class="skeleton-light min-h-[220px] rounded-3xl lg:col-span-5"></div>
          <div class="grid auto-rows-fr grid-cols-2 gap-4 lg:col-span-7">
            <div v-for="n in 4" :key="n" class="skeleton-light min-h-[110px] rounded-3xl"></div>
          </div>
        </div>

        <div v-else class="grid grid-cols-1 gap-5 sm:gap-6 lg:grid-cols-12">
          <div v-if="bentoLarge.length" class="flex flex-col gap-5 lg:col-span-5">
            <div
              v-for="(bento, i) in bentoLarge"
              :key="'l' + i"
              class="bento-feature pattern-seigaiha relative flex min-h-[220px] flex-1 flex-col justify-between overflow-hidden p-7 sm:min-h-[260px] sm:p-9"
            >
              <span class="bento-slab" aria-hidden="true"></span>
              <div class="icon-tile-yellow relative"><component :is="getIcon(bento.icon_name)" :size="22" /></div>
              <span class="text-outline relative font-[family-name:var(--font-display)] text-2xl leading-tight text-white sm:text-[1.75rem]">{{ bento.title }}</span>
            </div>
          </div>

          <div class="grid auto-rows-fr grid-cols-2 gap-5 sm:gap-6" :class="bentoLarge.length ? 'lg:col-span-7' : 'lg:col-span-12 lg:grid-cols-4'">
            <div
              v-for="(bento, i) in bentoSmall"
              :key="'s' + i"
              class="bento-feature bento-feature--sm pattern-seigaiha relative flex min-h-[132px] flex-col justify-between gap-5 overflow-hidden p-5 sm:min-h-[150px] sm:p-6"
              :class="isBentoOrphan(i) ? 'col-span-2' : ''"
            >
              <span class="bento-slab" aria-hidden="true"></span>
              <div class="icon-tile-yellow icon-tile-yellow--sm relative"><component :is="getIcon(bento.icon_name)" :size="20" /></div>
              <span class="text-outline relative font-[family-name:var(--font-display)] text-lg leading-tight text-white sm:text-xl">{{ bento.title }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════ 7. GALLERY (gelap) ═══════════════ -->
    <section class="pattern-seigaiha relative bg-[#111113] py-20 sm:py-24">
      <div class="mx-auto max-w-7xl px-5 sm:px-8 lg:px-10">
        <p class="eyebrow-jp eyebrow-jp--yellow mb-4"><span class="hanko" aria-hidden="true">写真</span>Dokumentasi</p>
        <h2 class="h-section-dark mb-8">Gallery</h2>

        <div v-if="!loading.gallery && galleryCategories.length > 2" class="no-scrollbar -mx-5 mb-8 flex gap-2.5 overflow-x-auto px-5 pb-1 sm:mx-0 sm:flex-wrap sm:px-0">
          <button
            v-for="cat in galleryCategories"
            :key="cat"
            type="button"
            @click="setCategory(cat)"
            :aria-pressed="activeCategory === cat"
            :class="[
              activeCategory === cat ? 'border-[#F4C542] bg-[#F4C542] text-[#111113]' : 'border-white/25 bg-transparent text-white hover:border-white/60',
              'min-h-[46px] shrink-0 cursor-pointer whitespace-nowrap rounded-full border-2 px-5 text-sm font-extrabold transition-colors'
            ]"
          >{{ cat }}</button>
        </div>

        <div v-if="loading.gallery" class="grid auto-rows-[150px] grid-cols-2 gap-3 sm:auto-rows-[180px] sm:grid-cols-3 md:grid-cols-4" aria-hidden="true">
          <div v-for="n in 8" :key="n" class="skeleton rounded-2xl" :class="n === 1 ? 'col-span-2 row-span-2' : ''"></div>
        </div>

        <div v-else class="grid auto-rows-[150px] grid-flow-row-dense grid-cols-2 gap-3 sm:auto-rows-[180px] sm:grid-cols-3 md:grid-cols-4">
          <button
            v-for="(img, i) in visibleGallery"
            :key="img.id ?? img.image_url"
            type="button"
            :aria-label="'Buka foto: ' + (img.title || 'Masashimura')"
            @click="openLightbox(i)"
            :class="[isFeatured(i) ? 'col-span-2 row-span-2' : '', 'gallery-tile group relative cursor-pointer overflow-hidden bg-[#1C1C1F] p-0 text-left']"
          >
            <div class="h-full w-full transition-transform duration-500 ease-out group-hover:scale-[1.05]">
              <img v-blur-img :src="img.image_url" :alt="img.title || 'Dokumentasi Masashimura'" loading="lazy" class="h-full w-full object-cover" />
            </div>
            <div class="absolute inset-0 flex items-end bg-gradient-to-t from-black/80 via-black/0 to-transparent p-3 opacity-0 transition-opacity duration-300 group-hover:opacity-100 group-focus-visible:opacity-100 sm:p-4">
              <div class="min-w-0 space-y-0.5">
                <p class="line-clamp-1 text-sm font-extrabold text-white">{{ img.title || 'Masashimura' }}</p>
                <p v-if="img.category" class="text-xs font-bold text-[#F4C542]">{{ img.category }}</p>
              </div>
            </div>
            <div class="absolute right-2.5 top-2.5 flex h-8 w-8 items-center justify-center rounded-full bg-[#F4C542] text-[#111113] opacity-0 transition-opacity duration-300 group-hover:opacity-100">
              <Expand :size="14" />
            </div>
          </button>

          <div v-if="visibleGallery.length === 0" class="col-span-full row-span-2 flex items-center justify-center rounded-2xl border-2 border-dashed border-white/20 text-center text-sm text-[#B8B8C0]">Belum ada foto.</div>
        </div>

        <div v-if="!loading.gallery && filteredGallery.length > visibleGallery.length" class="mt-10 flex justify-center">
          <button type="button" @click="galleryLimit += 8" class="pop-btn pop-btn--ghost cursor-pointer">
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
        <button type="button" @click="closeLightbox" aria-label="Tutup" class="absolute right-4 top-4 z-10 flex h-12 w-12 cursor-pointer items-center justify-center rounded-full bg-[#F4C542] text-[#111113] transition hover:bg-[#FFD65C] sm:right-8 sm:top-8">
          <X :size="18" />
        </button>
        <span class="absolute left-5 top-6 text-sm font-bold tabular-nums text-[#B8B8C0] sm:left-10 sm:top-10">{{ lightboxIndex + 1 }} / {{ visibleGallery.length }}</span>
        <button v-if="visibleGallery.length > 1" type="button" @click.stop="prevImage" aria-label="Foto sebelumnya" class="absolute left-2 top-1/2 z-10 flex h-12 w-12 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full bg-white/10 text-white transition hover:bg-white/20 sm:left-8"><ChevronLeft :size="20" /></button>
        <button v-if="visibleGallery.length > 1" type="button" @click.stop="nextImage" aria-label="Foto berikutnya" class="absolute right-2 top-1/2 z-10 flex h-12 w-12 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full bg-white/10 text-white transition hover:bg-white/20 sm:right-8"><ChevronRight :size="20" /></button>
        <div class="w-full max-w-4xl space-y-4" @click.stop>
          <div class="flex max-h-[75vh] items-center justify-center overflow-hidden">
            <img :key="lightboxIndex" :src="currentLightboxImage?.image_url" :alt="currentLightboxImage?.title || 'Masashimura'" class="lb-img max-h-[75vh] max-w-full rounded-2xl border-2 border-white/20 object-contain" />
          </div>
          <div class="space-y-1 text-center">
            <p class="text-base font-extrabold text-[#F5F3EF]">{{ currentLightboxImage?.title || 'Masashimura' }}</p>
            <p v-if="currentLightboxImage?.category" class="text-sm font-bold text-[#F4C542]">{{ currentLightboxImage.category }}</p>
          </div>
        </div>
      </div>
    </transition>

    <!-- ═══════════════ 8. REVIEW (krem) ═══════════════ -->
    <section class="dot-grid on-cream">
      <div class="mx-auto max-w-4xl px-5 py-20 sm:px-8 sm:py-24 lg:px-10">
        <p class="eyebrow-jp mb-4"><span class="hanko" aria-hidden="true">声</span>Testimoni</p>
        <h2 class="h-section mb-10">Kata pelanggan</h2>

        <div v-if="loading.reviews" class="pop-card p-8" aria-hidden="true">
          <div class="max-w-2xl space-y-3">
            <div class="skeleton-light h-5 w-full rounded-full"></div>
            <div class="skeleton-light h-5 w-5/6 rounded-full"></div>
            <div class="skeleton-light h-5 w-2/3 rounded-full"></div>
          </div>
        </div>

        <div v-else-if="reviews.length" class="pop-card touch-pan-y select-none p-7 sm:p-10" @touchstart.passive="onTouchStart" @touchend="onReviewSwipe">
          <div class="grid">
            <figure
              v-for="(review, i) in reviews"
              :key="i"
              :aria-hidden="i !== currentReviewIndex"
              class="col-start-1 row-start-1 space-y-6 transition-all duration-500 ease-out"
              :class="i === currentReviewIndex ? 'translate-y-0 opacity-100' : 'pointer-events-none translate-y-3 opacity-0'"
            >
              <Quote :size="30" class="text-[#D92B22]" />
              <blockquote class="max-w-2xl text-xl font-extrabold leading-relaxed text-[#111113] sm:text-2xl">“{{ review.text }}”</blockquote>
              <figcaption class="flex items-center gap-3">
                <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border-2 border-[#111113] bg-[#F4C542] text-sm font-extrabold uppercase text-[#111113]">{{ (review.name || '?').trim().charAt(0) }}</span>
                <span class="flex min-w-0 flex-col">
                  <span class="truncate text-sm font-extrabold text-[#111113]">{{ review.name }}</span>
                  <span class="text-sm text-[#5A5A62]">{{ review.status }}</span>
                </span>
              </figcaption>
            </figure>
          </div>
          <div v-if="reviews.length > 1" class="mt-8 flex items-center gap-2" aria-hidden="true">
            <span v-for="(r, i) in reviews" :key="i" class="block h-2 rounded-full transition-all duration-500" :class="i === currentReviewIndex ? 'w-8 bg-[#D92B22]' : 'w-2 bg-[#111113]/20'"></span>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════ 9. CTA ═══════════════ -->
    <section class="bg-[#111113] px-5 pb-20 pt-16 sm:px-8 sm:pb-24 lg:px-10">
      <div class="cta pattern-seigaiha relative mx-auto grid max-w-7xl grid-cols-1 items-center gap-8 overflow-hidden p-8 sm:p-12 lg:grid-cols-2 lg:gap-16 lg:p-14">
        <span class="cta-sun" aria-hidden="true"></span>
        <p class="jp-outline pointer-events-none absolute -bottom-4 left-4 whitespace-nowrap text-[5.5rem] leading-none sm:text-[8rem]" aria-hidden="true">腹減った</p>

        <div class="relative space-y-4">
          <h2 class="text-outline font-[family-name:var(--font-display)] text-4xl leading-[1.1] text-white sm:text-5xl">Udah laper?</h2>
          <p class="text-outline max-w-xs text-base font-semibold leading-relaxed text-white">Pilih menu favorit dan nikmati langsung di kedai atau lewat web ordering.</p>
        </div>

        <div class="relative flex flex-col gap-4 sm:flex-row lg:justify-end">
          <router-link to="/menu" class="pop-btn pop-btn--on-dark">
            Pesan via web
            <span class="pop-btn-dot" aria-hidden="true"><ArrowUpRight :size="15" /></span>
          </router-link>
          <router-link to="/contact" class="pop-btn pop-btn--ghost">Hubungi kami</router-link>
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
  Expand, X, ChevronLeft, ChevronRight, ArrowRight, ArrowUpRight, Quote, Plus
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

const tickerJp = ["美味しい", "最高", "乾杯", "夜ふかし", "青春"]

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

// Kartu menu di homepage. badge: "Terlaris" | "Rekomendasi" | "Baru"
const toCard = (item, badge) => ({
  name:  item.name,
  desc:  item.description || "Menu favorit pilihan squad Masashimura.",
  price: getWebPrice(item),   // sama persis dengan halaman Menu
  image: item.image_url || defaultHeroFood,
  badge,
})

// "best" = terlaris dari data order | "recommended" = ditandai rekomendasi di Kelola Menu | "new" = menu terbaru
const bestSource = ref("best")
const bestCopy = computed(() => ({
  best:        { title: "Menu terlaris",   sub: "Yang paling sering dipesan pelanggan kami." },
  recommended: { title: "Menu rekomendasi", sub: "Pilihan tim Masashimura yang wajib kamu coba." },
  new:         { title: "Menu pilihan",     sub: "Menu-menu andalan yang bisa kamu pesan sekarang." },
}[bestSource.value]))

const fetchBestSellers = async () => {
  try {
    // 1) Terlaris dari data penjualan
    try {
      const { data } = await apiClient.get("/menus/bestsellers/")
      if (Array.isArray(data) && data.length > 0) {
        bestSellers.value = data.map(item => toCard(item, "Terlaris"))
        bestSource.value = "best"
        return
      }
    } catch (err) {
      console.error("Best sellers:", err)
    }

    // 2) Belum ada data penjualan → rekomendasi, lalu menu terbaru. Section jangan sampai kosong.
    const { data } = await apiClient.get("/menus/")
    const list = (Array.isArray(data) ? data : data?.results || [])
      .filter(m => m.is_active !== false && m.is_available !== false && m.image_url)
    const rec = list.filter(m => m.is_recommended)
    if (rec.length) {
      bestSellers.value = rec.slice(0, 6).map(m => toCard(m, "Rekomendasi"))
      bestSource.value = "recommended"
    } else {
      const newest = [...list].sort((a, b) => {
        const ta = a.created_at ? new Date(a.created_at).getTime() : 0
        const tb = b.created_at ? new Date(b.created_at).getTime() : 0
        return tb - ta || b.id - a.id
      })
      bestSellers.value = newest.slice(0, 6).map(m => toCard(m, null))
      bestSource.value = "new"
    }
  } catch (err) {
    console.error("Menu homepage:", err)
  } finally {
    loading.best = false
  }
}

// Cadangan kalau API testimoni gagal (mis. server baru bangun). Isinya sama dengan backend.
const fallbackReviews = [
  { name: "Deny Yusuf Akbar",   status: "Local Guide", text: "Cozy place, like Izakaya in Japan. Cheap food, very delicious especially Mie Jebew with Chili oil." },
  { name: "rifky aziz",         status: "Local Guide", text: "Makanannya murah murah, rasanya mantul, pelayanan cepat, ada wifinya, cocok buat nobar." },
  { name: "Issa Xander",        status: "Local Guide", text: "Tempat Nya asik full musik juga. Ayam goreng sama Milkshake nya mantap." },
  { name: "nabil khalid",       status: "Customer",    text: "Tempaaat rekomendassiii bangettt daah, gabakall nyesel, mao ajak pacar, rekanan jugaaa bisaa bangetttt!" },
  { name: "ayimuhammad taupik", status: "Customer",    text: "Harga merakyat, makanannya enak, ada wifinya lagi. Recomended buat tempat nongkrong." },
  { name: "Fajri Azhari",       status: "Customer",    text: "Tempat nongkrong rekomendasi, harga terjangkau, makanan nya juga enak, tempat nya bersih, pelayan nya oke, gass keun kesini." },
  { name: "Muhamad Riandy",     status: "Customer",    text: "Solusi nongkrong hemat budget, harga kaki lima rasa bintang 5." },
  { name: "Ceplik -_-",         status: "Customer",    text: "Tempatnya asik, bersih, nyaman. Serta harga murah juga euy." },
  { name: "Zyss",               status: "Customer",    text: "Mantap, paling cocok buat nongkrong." },
  { name: "joss tv",            status: "Customer",    text: "Tempat nya orang santuy." },
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
a:focus-visible,
button:focus-visible { outline: 3px solid #F4C542; outline-offset: 3px; }
.on-cream a:focus-visible,
.on-cream button:focus-visible { outline-color: #111113; }

.on-cream { color: #202024; }

/* ── Judul section: Dela Gothic One (satu bobot) ── */
.h-section,
.h-section-dark {
  font-family: var(--font-display);
  font-weight: 400;
  font-size: clamp(1.9rem, 4vw, 2.6rem);
  line-height: 1.15;
  letter-spacing: 0;
}
.h-section { color: #111113; }
.h-section-dark { color: #F5F3EF; }

.link-pop {
  align-items: center;
  gap: 0.4rem;
  min-height: 44px;
  font-size: 0.9375rem;
  font-weight: 800;
  color: #B8201A;
  border-bottom: 3px solid #D92B22;
  align-self: flex-start;
  transition: color 0.2s, border-color 0.2s;
}
.link-pop:hover { color: #111113; border-color: #111113; }

/* ── Hero ── */
.hero { min-height: clamp(36rem, 92svh, 50rem); display: flex; align-items: center; }
.hero > .relative { width: 100%; }
.hero-title {
  font-family: var(--font-display);
  font-weight: 400;
  font-size: clamp(2.4rem, 8vw, 3.4rem);
  line-height: 1.12;
  letter-spacing: 0;
}
@media (min-width: 1024px) { .hero-title { font-size: clamp(3rem, 4.4vw, 4rem); } }
.hero-accent { color: #F4C542; text-shadow: 3px 3px 0 #D92B22; }
.hero-skel { height: clamp(2.1rem, 7vw, 3.6rem); }

.hero-sun {
  position: absolute;
  right: -8%;
  top: 12%;
  width: 46vw;
  max-width: 40rem;
  aspect-ratio: 1;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, #E8473F, #D92B22 55%, #A31B15);
}
.hero-slab-red {
  position: absolute;
  right: -4%;
  bottom: 0;
  width: 30%;
  height: 34%;
  background: #D92B22;
  clip-path: polygon(18% 0, 100% 0, 100% 100%, 0 100%);
  opacity: 0.9;
}
.hero-slab-yellow {
  position: absolute;
  right: -2%;
  bottom: 0;
  width: 18%;
  height: 26%;
  background: #F4C542;
  clip-path: polygon(30% 0, 100% 0, 100% 100%, 0 100%);
}
@media (max-width: 1023px) {
  .hero-sun { right: -30%; top: 38%; width: 90vw; opacity: 0.85; }
  .hero-slab-red, .hero-slab-yellow { display: none; }
}

.hero-card-back {
  position: absolute;
  inset: 0;
  margin: 0 auto;
  max-width: 34rem;
  border: 3px solid #111113;
  border-radius: 28px;
  background: #F4C542;
  transform: translate(14px, 12px) rotate(2deg);
}
@media (min-width: 1024px) { .hero-card-back { margin-right: 3rem; margin-left: auto; } }
.hero-frame {
  border: 4px solid #fff;
  border-radius: 28px;
  transform: rotate(2deg);
  box-shadow: 0 0 0 3px #111113;
}
.hero-badge { filter: drop-shadow(3px 3px 0 #111113); }
.hero-badge-ring { transform-origin: 60px 60px; animation: spin-slow 22s linear infinite; }
@keyframes spin-slow { to { transform: rotate(360deg); } }

@keyframes heroIn { to { opacity: 1; transform: none; } }
.hero-in {
  opacity: 0;
  transform: translateY(16px);
  animation: heroIn 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  animation-delay: var(--d, 0ms);
}

/* ── Metrik ── */
.metric-num { font-family: var(--font-display); font-size: clamp(1.6rem, 4vw, 2rem); line-height: 1.15; color: inherit; }
.metric-label { margin-top: 0.2rem; font-size: 0.875rem; font-weight: 800; color: #111113; }

/* ── Kartu menu ── */
.menu-card { display: block; overflow: hidden; transition: transform 0.18s ease, box-shadow 0.18s ease; }
.menu-card:hover { transform: translate(-2px, -2px); box-shadow: 9px 9px 0 #111113; }
.menu-add {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  border: 2px solid #111113;
  border-radius: 50%;
  background: #F4C542;
  color: #111113;
  transition: background-color 0.2s;
}
.menu-card:hover .menu-add { background: #D92B22; color: #fff; }

/* ── Tentang ── */
.about-photo {
  border: 3px solid #111113;
  border-radius: 28px;
  box-shadow: 12px 12px 0 #D92B22, 12px 12px 0 3px #111113;
}

/* ── Bento ── */
.bento-feature {
  border: 2px solid #111113;
  border-radius: 28px;
  background-color: #111113;
  box-shadow: 8px 8px 0 #F4C542, 8px 8px 0 2px #111113;
}
/* 2x1: desain sama persis dengan 2x2, hanya skalanya diperkecil */
.bento-feature--sm {
  border-radius: 24px;
  box-shadow: 6px 6px 0 #F4C542, 6px 6px 0 2px #111113;
}
.bento-feature--sm .bento-slab { width: 50%; height: 50%; border-bottom-right-radius: 22px; }
.bento-slab {
  position: absolute;
  right: -2px;
  bottom: -2px;
  width: 58%;
  height: 52%;
  background: #D92B22;
  clip-path: polygon(22% 0, 100% 0, 100% 100%, 0 100%);
  border-bottom-right-radius: 26px;
}
.icon-tile-yellow,
.icon-tile-red {
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #111113;
  border-radius: 14px;
  box-shadow: 2px 2px 0 #fff;
}
.icon-tile-yellow { width: 52px; height: 52px; background: #F4C542; color: #111113; }
.icon-tile-yellow--sm { width: 46px; height: 46px; border-radius: 13px; }
.icon-tile-red { width: 42px; height: 42px; background: #D92B22; color: #fff; box-shadow: 2px 2px 0 #111113; }

/* ── Gallery ── */
.gallery-tile { border: 2px solid rgb(255 255 255 / 0.18); border-radius: 20px; transition: border-color 0.2s, transform 0.18s; }
.gallery-tile:hover { border-color: #F4C542; }

/* ── CTA ── */
.cta {
  border: 3px solid #fff;
  border-radius: 28px;
  background-color: #D92B22;
  background-image: linear-gradient(120deg, #B8201A, #D92B22 60%);
  box-shadow: 9px 9px 0 #F4C542, 9px 9px 0 3px #111113;
}
.cta-sun {
  position: absolute;
  right: -5rem;
  top: -5rem;
  width: 17rem;
  height: 17rem;
  border-radius: 50%;
  background: #F4C542;
  border: 3px solid #111113;
}

/* ── Skeleton ── */
.skeleton, .skeleton-light { background-size: 200% 100%; animation: shimmer 1.4s ease-in-out infinite; }
.skeleton { background-image: linear-gradient(100deg, rgb(255 255 255 / 0.04) 30%, rgb(255 255 255 / 0.1) 50%, rgb(255 255 255 / 0.04) 70%); }
.skeleton-light { background-image: linear-gradient(100deg, #ECE8DF 30%, #F6F3EC 50%, #ECE8DF 70%); }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

/* ── Ticker ── */
@keyframes marquee { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
.animate-marquee { width: max-content; animation: marquee 60s linear infinite; }
.marquee-wrap:hover .animate-marquee { animation-play-state: paused; }

/* ── Lightbox ── */
.lightbox-fade-enter-active, .lightbox-fade-leave-active { transition: opacity 0.25s ease; }
.lightbox-fade-enter-from, .lightbox-fade-leave-to { opacity: 0; }
@keyframes lbIn { from { opacity: 0; transform: scale(0.98); } to { opacity: 1; transform: scale(1); } }
.lb-img { animation: lbIn 0.3s ease; }

/* ── Reveal ── */
.reveal { opacity: 0; transform: translateY(20px); transition: opacity 0.6s cubic-bezier(0.16, 1, 0.3, 1), transform 0.6s cubic-bezier(0.16, 1, 0.3, 1); }
.reveal-visible { opacity: 1; transform: none; }

.img-blur { opacity: 0; transition: opacity 0.5s ease; }
.img-blur.img-loaded { opacity: 1; }

.no-scrollbar { scrollbar-width: none; }
.no-scrollbar::-webkit-scrollbar { display: none; }

@media (prefers-reduced-motion: reduce) {
  .reveal, .img-blur { transition: none; opacity: 1; transform: none; }
  .hero-in { animation: none; opacity: 1; transform: none; }
  .animate-marquee, .hero-badge-ring, .lb-img, .skeleton, .skeleton-light, .animate-ping { animation: none; }
  .menu-card, .menu-card:hover { transition: none; transform: none; }
}
</style>
