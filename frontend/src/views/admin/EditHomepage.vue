<template>
  <div class="adm-page adm-page--form">

    <!-- ── Header ─────────────────────────────────────────────────── -->
    <header class="adm-header">
      <div>
        <p class="adm-eyebrow">Masashimura · Admin</p>
        <h1 class="adm-title">Edit Homepage</h1>
        <p class="adm-sub">Kendalikan konten, gambar, teks berjalan, promo, dan statistik halaman depan Masashimura.</p>
      </div>
    </header>

    <!-- ── 01. Hero ───────────────────────────────────────────────── -->
    <section class="adm-card">
      <div class="adm-card-head">
        <span class="eh-num">01</span>
        <div class="adm-card-head-main">
          <h2 class="adm-card-title">Hero Section</h2>
          <p class="adm-card-desc">Bagian paling atas halaman, tampil selebar layar.</p>
        </div>
      </div>
      <div class="adm-card-body">
        <div class="adm-grid-2">
          <div class="adm-field">
            <label class="adm-label" for="hero-headline">Headline utama</label>
            <input id="hero-headline" v-model="form.hero_headline" type="text" class="adm-input eh-strong" />
          </div>
          <div class="adm-field">
            <label class="adm-label" for="hero-sub">Sub-headline singkat</label>
            <input id="hero-sub" v-model="form.hero_subheadline" type="text" class="adm-input" />
          </div>
        </div>

        <div class="adm-field">
          <span class="adm-label">Foto background parallax <span class="adm-opt">(16:9)</span></span>
          <AdminImageField
            v-model="form.hero_bg_image" label="background hero" ratio="16 / 9" thumb-width="10rem" removable
            hint="Dipotong otomatis ke rasio 16:9 sebelum diupload."
            @pick="(f) => startCrop(f, 'hero_bg')" @clear="form.hero_bg_image = null"
          />
        </div>

        <div class="adm-field">
          <span class="adm-label">Foto makanan kotak kanan hero <span class="adm-opt">(1:1)</span></span>
          <AdminImageField
            v-model="form.hero_food_image" label="makanan hero" removable
            hint="Dipotong otomatis ke rasio 1:1 sebelum diupload."
            @pick="(f) => startCrop(f, 'hero_food')" @clear="form.hero_food_image = null"
          />
        </div>
      </div>
    </section>

    <!-- ── 02. Marquee ────────────────────────────────────────────── -->
    <section class="adm-card">
      <div class="adm-card-head">
        <span class="eh-num">02</span>
        <div class="adm-card-head-main">
          <h2 class="adm-card-title">Aksen Teks Berjalan</h2>
          <p class="adm-card-desc">Teks marquee di bawah hero. Kecepatan dan warna diatur otomatis.</p>
        </div>
      </div>
      <div class="adm-card-body">
        <div class="adm-field">
          <label class="adm-label" for="marquee">Konten teks berjalan</label>
          <input id="marquee" v-model="form.marquee_text" type="text" class="adm-input adm-input--mono" />
          <p class="adm-hint">Pisahkan tiap frasa dengan tanda <code class="eh-code">•</code></p>
        </div>
      </div>
    </section>

    <!-- ── 03. Tentang & statistik ────────────────────────────────── -->
    <section class="adm-card">
      <div class="adm-card-head">
        <span class="eh-num">03</span>
        <div class="adm-card-head-main">
          <h2 class="adm-card-title">Tentang Masashimura & Statistik</h2>
          <p class="adm-card-desc">Deskripsi kedai, foto suasana, dan tiga angka ringkasan.</p>
        </div>
      </div>
      <div class="adm-card-body">
        <div class="adm-field">
          <label class="adm-label" for="about-text">Deskripsi panjang <span class="adm-opt">(kolom teks kanan)</span></label>
          <textarea id="about-text" v-model="form.about_text" rows="4" class="adm-input"></textarea>
        </div>

        <div class="adm-field">
          <span class="adm-label">Foto outlet suasana kedai <span class="adm-opt">(kolom kiri, 1:1)</span></span>
          <AdminImageField
            v-model="form.about_image" label="suasana kedai" thumb-width="6rem" removable
            hint="Dipotong otomatis ke rasio 1:1 sebelum diupload."
            @pick="(f) => startCrop(f, 'about')" @clear="form.about_image = null"
          />
        </div>

        <div class="adm-grid-3">
          <div class="adm-field">
            <label class="adm-label" for="metric-1">Angka 1 <span class="adm-opt">(tahun berdiri)</span></label>
            <input id="metric-1" v-model="form.metric_1" type="text" class="adm-input eh-metric" />
          </div>
          <div class="adm-field">
            <label class="adm-label" for="metric-2">Angka 2 <span class="adm-opt">(jumlah menu)</span></label>
            <input id="metric-2" v-model="form.metric_2" type="text" class="adm-input eh-metric" />
            <p class="adm-hint">Di homepage otomatis memakai jumlah menu asli; isian ini cadangan.</p>
          </div>
          <div class="adm-field">
            <label class="adm-label" for="metric-3">Angka 3 <span class="adm-opt">(rating)</span></label>
            <input id="metric-3" v-model="form.metric_3" type="text" class="adm-input eh-metric eh-metric--star" />
          </div>
        </div>
      </div>
    </section>

    <!-- ── 04. Promo & Event ──────────────────────────────────────── -->
    <section class="adm-card">
      <div class="adm-card-head">
        <span class="eh-num">04</span>
        <div class="adm-card-head-main">
          <h2 class="adm-card-title">Promo & Event</h2>
          <p class="adm-card-desc">
            Banner di bawah teks berjalan. <strong>Kosongkan judul, keterangan, dan gambar</strong> kalau tidak ada promo, section otomatis hilang.
          </p>
        </div>
        <div v-if="hasPromo" class="adm-card-head-actions">
          <button type="button" class="adm-btn adm-btn--ghost adm-btn--sm" @click="clearPromo">
            <Trash2 :size="14" /> Kosongkan
          </button>
        </div>
      </div>

      <div class="adm-card-body">

        <!-- Gambar -->
        <div class="adm-field">
          <span class="adm-label">Gambar promo <span class="adm-opt">(opsional · bebas rasio)</span></span>
          <AdminImageField
            v-model="form.promo_image" label="gambar promo" :ratio="promoRatioCss" thumb-width="9rem" removable
            hint="Gambar diperkecil otomatis (maks 1800px) sebelum diupload. Rasio tampilan diatur lewat opsi di bawah."
            @pick="uploadPromoImage" @clear="form.promo_image = null"
          />
        </div>

        <!-- Opsi gambar: muncul setelah ada gambar -->
        <template v-if="form.promo_image">

          <div class="adm-field">
            <span id="pr-ratio" class="adm-label">Rasio tampilan gambar</span>
            <div class="eh-opts" role="radiogroup" aria-labelledby="pr-ratio">
              <button
                v-for="r in RATIO_OPTIONS" :key="r.value" type="button" role="radio"
                class="eh-opt" :class="{ 'is-selected': form.promo_image_ratio === r.value }"
                :aria-checked="form.promo_image_ratio === r.value"
                @click="form.promo_image_ratio = r.value"
              >
                <span class="eh-ratio-box" :style="ratioBox(r.num)"></span>
                <span class="eh-opt-main">{{ r.value }}</span>
                <span class="eh-opt-sub">{{ r.hint }}</span>
              </button>
            </div>
          </div>

          <div class="adm-field">
            <span id="pr-layout" class="adm-label">Tata letak</span>
            <div class="eh-opts eh-opts--wide" role="radiogroup" aria-labelledby="pr-layout">
              <button
                v-for="l in LAYOUT_OPTIONS" :key="l.value" type="button" role="radio"
                class="eh-opt eh-opt--text" :class="{ 'is-selected': form.promo_layout === l.value }"
                :aria-checked="form.promo_layout === l.value"
                @click="form.promo_layout = l.value"
              >
                <span class="eh-opt-main">{{ l.label }}</span>
                <span class="eh-opt-sub">{{ l.hint }}</span>
              </button>
            </div>
          </div>

          <div class="adm-grid-2">
            <div v-if="form.promo_layout === 'split'" class="adm-field">
              <span id="pr-side" class="adm-label">Posisi gambar</span>
              <div class="adm-seg adm-seg--fill" role="radiogroup" aria-labelledby="pr-side">
                <button type="button" role="radio" class="adm-seg-btn" :aria-checked="form.promo_image_side === 'left'" @click="form.promo_image_side = 'left'">Kiri</button>
                <button type="button" role="radio" class="adm-seg-btn" :aria-checked="form.promo_image_side === 'right'" @click="form.promo_image_side = 'right'">Kanan</button>
              </div>
            </div>

            <div v-if="form.promo_layout !== 'split'" class="adm-field">
              <span id="pr-align" class="adm-label">Rata teks</span>
              <div class="adm-seg adm-seg--fill" role="radiogroup" aria-labelledby="pr-align">
                <button type="button" role="radio" class="adm-seg-btn" :aria-checked="form.promo_align === 'left'" @click="form.promo_align = 'left'">Kiri</button>
                <button type="button" role="radio" class="adm-seg-btn" :aria-checked="form.promo_align === 'center'" @click="form.promo_align = 'center'">Tengah</button>
              </div>
            </div>

            <div v-if="form.promo_layout === 'overlay'" class="adm-field">
              <label class="adm-label" for="pr-overlay">Gelap overlay <span class="adm-opt">({{ form.promo_overlay }}%)</span></label>
              <input id="pr-overlay" v-model.number="form.promo_overlay" type="range" min="0" max="90" step="5" class="eh-range" />
              <p class="adm-hint">Makin tinggi, teks makin mudah dibaca di atas foto yang terang.</p>
            </div>
          </div>

          <div class="adm-field">
            <span id="pr-focus" class="adm-label">Titik fokus gambar <span class="adm-opt">(bagian yang dipertahankan saat dipotong)</span></span>
            <div class="eh-focus-wrap">
              <div class="eh-focus" role="radiogroup" aria-labelledby="pr-focus">
                <button
                  v-for="f in FOCUS_OPTIONS" :key="f.value" type="button" role="radio"
                  class="eh-focus-dot" :class="{ 'is-selected': form.promo_focus === f.value }"
                  :aria-checked="form.promo_focus === f.value" :aria-label="f.label" :title="f.label"
                  @click="form.promo_focus = f.value"
                ><span></span></button>
              </div>
              <p class="adm-hint">Terpilih: <strong>{{ focusLabel }}</strong>. Berguna kalau wajah/makanan utama ada di pinggir foto.</p>
            </div>
          </div>

          <div class="adm-field">
            <label class="adm-label" for="pr-alt">Deskripsi gambar <span class="adm-opt">(untuk pembaca layar, opsional)</span></label>
            <input id="pr-alt" v-model="form.promo_image_alt" type="text" maxlength="150" class="adm-input" placeholder="Contoh: Poster live music Sabtu malam" />
          </div>
        </template>

        <!-- Teks -->
        <div class="adm-field">
          <label class="adm-label" for="pr-badge">Label kecil <span class="adm-opt">(opsional, default “Promo &amp; Event”)</span></label>
          <input id="pr-badge" v-model="form.promo_badge" type="text" maxlength="30" class="adm-input" placeholder="Contoh: Live Music" />
          <div class="eh-presets">
            <button v-for="p in BADGE_PRESETS" :key="p" type="button" class="eh-preset" @click="form.promo_badge = p">{{ p }}</button>
          </div>
        </div>

        <div class="adm-field">
          <label class="adm-label" for="promo-title">Judul promo / event</label>
          <input id="promo-title" v-model="form.promo_title" type="text" maxlength="120"
            class="adm-input eh-strong" placeholder="Contoh: Diskon 20% khusus mahasiswa" />
        </div>

        <div class="adm-field">
          <label class="adm-label" for="promo-text">Keterangan <span class="adm-opt">(opsional)</span></label>
          <input id="promo-text" v-model="form.promo_text" type="text" maxlength="255"
            class="adm-input" placeholder="Contoh: Tunjukkan KTM, berlaku Senin–Jumat" />
        </div>

        <!-- Tombol -->
        <div class="adm-grid-2">
          <div class="adm-field">
            <label class="adm-label" for="promo-label">Teks tombol <span class="adm-opt">(opsional)</span></label>
            <input id="promo-label" v-model="form.promo_link_label" type="text" maxlength="40"
              class="adm-input" placeholder="Lihat Detail" />
          </div>
          <div class="adm-field">
            <label class="adm-label" for="promo-link">Link tombol <span class="adm-opt">(opsional)</span></label>
            <input id="promo-link" v-model="form.promo_link" type="text"
              class="adm-input adm-input--mono" placeholder="/menu atau https://wa.me/62..." />
            <p class="adm-hint">Pakai <code class="eh-code">/menu</code> untuk halaman sendiri, atau <code class="eh-code">https://…</code> untuk link luar. Kosong = tanpa tombol.</p>
          </div>
        </div>

        <!-- Warna -->
        <div class="adm-field">
          <span id="pr-theme" class="adm-label">Warna aksen</span>
          <div class="eh-swatches" role="radiogroup" aria-labelledby="pr-theme">
            <button
              v-for="t in THEME_OPTIONS" :key="t.value" type="button" role="radio"
              class="eh-swatch" :class="{ 'is-selected': form.promo_theme === t.value }"
              :aria-checked="form.promo_theme === t.value" :aria-label="t.label" :title="t.label"
              :style="{ '--sw': t.accent }"
              @click="form.promo_theme = t.value"
            ></button>
          </div>
        </div>

        <!-- Jadwal -->
        <div class="adm-grid-2">
          <div class="adm-field">
            <label class="adm-label" for="promo-from">Mulai tayang <span class="adm-opt">(opsional)</span></label>
            <input id="promo-from" v-model="form.promo_from" type="date" class="adm-input" />
            <p class="adm-hint">Kosong = langsung tayang setelah disimpan.</p>
          </div>
          <div class="adm-field">
            <label class="adm-label" for="promo-until">Tayang sampai <span class="adm-opt">(opsional)</span></label>
            <input id="promo-until" v-model="form.promo_until" type="date" class="adm-input" />
            <p class="adm-hint">Hilang otomatis setelah tanggal ini (akhir hari WIB). Kosong = tayang terus.</p>
          </div>
        </div>

        <div class="eh-checks">
          <label class="eh-check">
            <input v-model="form.promo_countdown" type="checkbox" :disabled="!form.promo_until" />
            <span>
              Tampilkan hitung mundur
              <small>Contoh: “Sisa 2 hari”. Perlu tanggal “Tayang sampai”.</small>
            </span>
          </label>
          <label class="eh-check">
            <input v-model="form.promo_dismissible" type="checkbox" />
            <span>
              Pengunjung boleh menutup banner
              <small>Tombol ✕ muncul; banner muncul lagi kalau isi promo diganti.</small>
            </span>
          </label>
        </div>

        <!-- Pratinjau langsung -->
        <div class="pv" :style="pvVars">
          <p class="pv-cap">Pratinjau tampilan desktop (disederhanakan)</p>

          <div v-if="!hasPromo" class="pv-empty">Isi judul, keterangan, atau gambar untuk melihat pratinjau.</div>

          <div v-else class="pv-stage">
            <div class="pv-wrap" :class="pvWrapClass" :style="pvWrapStyle">

              <span v-if="pvLayout === 'text'" class="pv-icon"><Tag :size="16" /></span>

              <div v-if="form.promo_image && pvLayout !== 'text'" class="pv-media" :style="pvMediaStyle">
                <img :src="form.promo_image" alt="" :style="{ objectPosition: focusCss }" />
                <div v-if="pvLayout === 'overlay'" class="pv-shade" :style="{ background: pvShade }"></div>
              </div>

              <div class="pv-copy" :class="{ 'is-center': pvCenter }">
                <p class="pv-eyebrow"><i></i>{{ form.promo_badge || 'Promo & Event' }}</p>
                <p class="pv-title" :class="'pv-title--' + pvLayout">{{ form.promo_title || 'Judul promo' }}</p>
                <p v-if="form.promo_text" class="pv-text">{{ form.promo_text }}</p>
                <p v-if="form.promo_until" class="pv-meta">
                  Sampai {{ untilLabel }}<template v-if="form.promo_countdown"> · hitung mundur aktif</template>
                </p>
                <span v-if="form.promo_link" class="pv-btn">{{ form.promo_link_label || 'Lihat Detail' }} →</span>
              </div>
            </div>
          </div>
        </div>

      </div>
    </section>

    <!-- ── Pratinjau cepat ────────────────────────────────────────── -->
    <section class="adm-card">
      <div class="adm-card-head">
        <div class="adm-card-icon tone-blue"><Eye :size="18" /></div>
        <div class="adm-card-head-main">
          <h2 class="adm-card-title">Pratinjau Cepat</h2>
          <p class="adm-card-desc">Cuplikan teks utama sesuai isian di atas (belum termasuk gambar).</p>
        </div>
      </div>
      <div class="adm-card-body">
        <div class="eh-preview-hero">
          <p class="eh-preview-title">{{ form.hero_headline || 'Headline kosong' }}</p>
          <p v-if="form.hero_subheadline" class="eh-preview-sub">{{ form.hero_subheadline }}</p>
        </div>
        <div class="eh-preview-marquee adm-mono">
          <span>Marquee</span>{{ form.marquee_text || '—' }}
        </div>
        <div v-if="hasPromo" class="eh-preview-marquee adm-mono">
          <span>Promo</span>{{ form.promo_title || form.promo_text || 'Hanya gambar' }}
        </div>
      </div>
    </section>

    <!-- ── Bar simpan (teks utama 01–04) ──────────────────────────── -->
    <div class="adm-savebar" :class="{ 'is-clean': !hasChanges }">
      <p class="adm-savebar-text" aria-live="polite">
        <span class="adm-dot"></span>
        {{ hasChanges ? 'Ada perubahan teks/foto utama yang belum dipublikasikan' : 'Konten utama sudah tersimpan' }}
      </p>
      <div class="adm-savebar-actions">
        <button v-if="hasChanges && !isSaving" type="button" class="adm-btn adm-btn--ghost" @click="resetMain">Batalkan</button>
        <button type="button" class="adm-btn adm-btn--primary" :disabled="isSaving || !hasChanges" @click="saveHomepageData">
          <span v-if="isSaving" class="adm-spinner"></span>
          <Save v-else :size="15" />
          {{ isSaving ? 'Menyimpan…' : 'Simpan Konten Utama' }}
        </button>
      </div>
    </div>

    <!-- ── 05. Bento ──────────────────────────────────────────────── -->
    <section class="adm-card adm-card--flush">
      <div class="adm-card-head">
        <span class="eh-num">05</span>
        <div class="adm-card-head-main">
          <h2 class="adm-card-title">Bento Grid Fasilitas</h2>
          <p class="adm-card-desc">Kartu fasilitas di homepage. Perubahan di bagian ini <strong>langsung tersimpan</strong>.</p>
        </div>
        <div class="adm-card-head-actions">
          <button type="button" class="adm-btn adm-btn--soft adm-btn--sm" @click="openBentoModal(null)">
            <Plus :size="14" /> Tambah
          </button>
        </div>
      </div>

      <ul v-if="bentoFacilities.length" class="eh-bento-list">
        <li v-for="bento in bentoFacilities" :key="bento.id" class="eh-bento-row">
          <span class="eh-bento-icon"><component :is="iconMap[bento.icon_name] || Coffee" :size="18" /></span>
          <div class="eh-bento-info">
            <p class="eh-bento-title adm-truncate">{{ bento.title }}</p>
            <p class="eh-bento-meta adm-mono">{{ bento.icon_name }}</p>
          </div>
          <span class="adm-badge" :class="bento.size === 'large' ? 'adm-badge--red' : ''">
            {{ bento.size === 'large' ? 'Large 2×2' : 'Normal 1×1' }}
          </span>
          <div class="eh-row-actions">
            <button type="button" class="adm-icon-btn" :aria-label="`Edit ${bento.title}`" @click="openBentoModal(bento)"><Pencil :size="15" /></button>
            <button type="button" class="adm-icon-btn adm-icon-btn--danger" :aria-label="`Hapus ${bento.title}`" @click="deleteBento(bento)"><Trash2 :size="15" /></button>
          </div>
        </li>
      </ul>
      <div v-else class="adm-empty">
        <div class="adm-empty-icon"><LayoutGrid :size="22" /></div>
        <p class="adm-empty-title">Belum ada fasilitas bento</p>
        <p class="adm-empty-text">Tambahkan fasilitas pertama untuk ditampilkan di homepage.</p>
      </div>
    </section>

    <!-- ── 06. Galeri ─────────────────────────────────────────────── -->
    <section class="adm-card">
      <div class="adm-card-head">
        <span class="eh-num">06</span>
        <div class="adm-card-head-main">
          <h2 class="adm-card-title">Galeri & Dokumentasi Event</h2>
          <p class="adm-card-desc">Foto suasana dan event. Perubahan di bagian ini <strong>langsung tersimpan</strong>.</p>
        </div>
        <div class="adm-card-head-actions">
          <button type="button" class="adm-btn adm-btn--soft adm-btn--sm" @click="openGalleryModal()">
            <Plus :size="14" /> Upload
          </button>
        </div>
      </div>

      <div class="adm-card-body">
        <ul v-if="galleryData.length" class="eh-gallery">
          <li v-for="img in galleryData" :key="img.id" class="eh-tile">
            <img :src="img.image_url" :alt="img.title || 'Foto galeri'" loading="lazy" />
            <div class="eh-tile-actions">
              <button type="button" class="eh-tile-btn" :aria-label="`Edit ${img.title || 'foto'}`" @click="openGalleryModal(img)"><Pencil :size="13" /></button>
              <button type="button" class="eh-tile-btn eh-tile-btn--danger" :aria-label="`Hapus ${img.title || 'foto'}`" @click="deleteGalleryItem(img)"><Trash2 :size="13" /></button>
            </div>
            <div class="eh-tile-caption">
              <p class="adm-truncate">{{ img.title || 'Tanpa judul' }}</p>
              <span v-if="img.category">{{ img.category }}</span>
            </div>
          </li>
        </ul>
        <div v-else class="adm-empty">
          <div class="adm-empty-icon"><ImageIcon :size="22" /></div>
          <p class="adm-empty-title">Belum ada dokumentasi foto</p>
          <p class="adm-empty-text">Upload foto event pertama untuk mengisi galeri.</p>
        </div>
      </div>
    </section>

    <!-- ══ Modal Bento ══════════════════════════════════════════════ -->
    <AdminModal
      v-model="bentoOpen"
      :title="editingBentoId ? 'Edit Fasilitas Bento' : 'Tambah Fasilitas Bento'"
      :persistent="isSavingSub"
    >
      <form id="bento-form" class="eh-form" @submit.prevent="saveBento">
        <div class="adm-field">
          <label class="adm-label" for="bento-title">Nama fasilitas <span class="adm-req">*</span></label>
          <input id="bento-title" v-model="bentoForm.title" data-autofocus type="text" class="adm-input" placeholder="Contoh: WiFi 150Mbps" />
        </div>

        <div class="adm-field">
          <span id="bento-icon-label" class="adm-label">Icon</span>
          <div class="eh-icons" role="radiogroup" aria-labelledby="bento-icon-label">
            <button
              v-for="(comp, name) in iconMap" :key="name"
              type="button" role="radio" class="eh-icon-btn"
              :class="{ 'is-selected': bentoForm.icon_name === name }"
              :aria-checked="bentoForm.icon_name === name" :aria-label="name" :title="name"
              @click="bentoForm.icon_name = name"
            >
              <component :is="comp" :size="18" />
            </button>
          </div>
          <p class="adm-hint">Terpilih: <strong class="adm-mono">{{ bentoForm.icon_name }}</strong></p>
        </div>

        <div class="adm-field">
          <span id="bento-size-label" class="adm-label">Ukuran kartu</span>
          <div class="adm-seg adm-seg--fill" role="radiogroup" aria-labelledby="bento-size-label">
            <button type="button" role="radio" class="adm-seg-btn" :aria-checked="bentoForm.size === 'normal'" @click="bentoForm.size = 'normal'">Standard 1×1</button>
            <button type="button" role="radio" class="adm-seg-btn" :aria-checked="bentoForm.size === 'large'" @click="bentoForm.size = 'large'">Large 2×2</button>
          </div>
        </div>
      </form>
      <template #footer>
        <button type="button" class="adm-btn adm-btn--ghost" :disabled="isSavingSub" @click="bentoOpen = false">Batal</button>
        <button type="submit" form="bento-form" class="adm-btn adm-btn--primary" :disabled="isSavingSub">
          <span v-if="isSavingSub" class="adm-spinner"></span>{{ isSavingSub ? 'Menyimpan…' : 'Simpan' }}
        </button>
      </template>
    </AdminModal>

    <!-- ══ Modal Galeri ═════════════════════════════════════════════
         Disembunyikan sementara saat cropper terbuka agar tidak saling tumpuk;
         isi form tetap aman karena state-nya ada di halaman ini. -->
    <AdminModal
      :model-value="galleryOpen && !isCropping"
      :title="editingGalleryId ? 'Edit Dokumentasi Foto' : 'Upload Foto Event'"
      :persistent="isSavingSub"
      @update:model-value="(v) => !v && (galleryOpen = false)"
    >
      <form id="gallery-form" class="eh-form" @submit.prevent="saveGalleryItem">
        <div class="adm-field">
          <label class="adm-label" for="gal-title">Judul event / dokumentasi <span class="adm-req">*</span></label>
          <input id="gal-title" v-model="galleryForm.title" data-autofocus type="text" class="adm-input" placeholder="Contoh: Nobar Akbar Semifinal" />
        </div>
        <div class="adm-field">
          <label class="adm-label" for="gal-cat">Kategori</label>
          <input id="gal-cat" v-model="galleryForm.category" type="text" class="adm-input" placeholder="Suasana Kedai, Event, Best Seller…" />
        </div>
        <div class="adm-field">
          <span class="adm-label">Foto <span class="adm-req">*</span> <span class="adm-opt">(1:1)</span></span>
          <AdminImageField
            v-model="galleryForm.image_url" label="dokumentasi" stack thumb-width="8rem"
            hint="Dipotong otomatis ke rasio 1:1 sebelum diupload."
            @pick="(f) => startCrop(f, 'gallery')"
          />
        </div>
      </form>
      <template #footer>
        <button type="button" class="adm-btn adm-btn--ghost" :disabled="isSavingSub" @click="galleryOpen = false">Batal</button>
        <button type="submit" form="gallery-form" class="adm-btn adm-btn--primary" :disabled="isSavingSub">
          <span v-if="isSavingSub" class="adm-spinner"></span>{{ isSavingSub ? 'Menyimpan…' : 'Simpan' }}
        </button>
      </template>
    </AdminModal>

    <AdminConfirm :state="confirmState" @confirm="acceptConfirm" @cancel="cancelConfirm" />

    <!-- Cropper (hero, about, galeri) -->
    <ImageCropper
      v-if="isCropping"
      :image="imageSrc"
      :type="cropType"
      @crop-complete="handleUploadToCloudinary"
      @cancel="closeCropper"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { toast } from 'vue-sonner'
import axios from 'axios'
import apiClient from '@/api/client'
import ImageCropper from '@/components/ui/ImageCropper.vue'
import AdminModal from '@/components/ui/admin/Adminmodal.vue'
import AdminConfirm from '@/components/ui/admin/Adminconfirm.vue'
import AdminImageField from '@/components/ui/admin/Adminimagefield.vue'
import { useAdminConfirm } from '@/composables/useAdminConfirm'
import {
  Coffee, Wifi, Zap, Utensils, DollarSign, Moon, Shield, Tv,
  Music, Gamepad2, Beer, BatteryCharging, Heart, Award, Smartphone,
  Plus, Pencil, Trash2, Save, Eye, LayoutGrid, Image as ImageIcon, Tag,
} from 'lucide-vue-next'

// Objek mapping icon agar bisa di-looping di template
const iconMap = {
  Coffee, Wifi, Zap, Utensils, DollarSign, Moon, Shield, Tv,
  Music, Gamepad2, Beer, BatteryCharging, Heart, Award, Smartphone,
}

const { state: confirmState, ask, accept: acceptConfirm, cancel: cancelConfirm } = useAdminConfirm()

// Cloudinary pakai axios biasa karena base URL-nya beda (bukan backend sendiri)
const CLOUDINARY_CLOUD_NAME = import.meta.env.VITE_CLOUDINARY_CLOUD_NAME
const CLOUDINARY_UPLOAD_PRESET = import.meta.env.VITE_CLOUDINARY_UPLOAD_PRESET
const CLOUDINARY_UPLOAD_URL = `https://api.cloudinary.com/v1_1/${CLOUDINARY_CLOUD_NAME}/image/upload`

const isSaving = ref(false)
const isSavingSub = ref(false)
const isCropping = ref(false)
const bentoOpen = ref(false)
const galleryOpen = ref(false)

const imageSrc = ref('')
const cropType = ref('hero')

// ── Opsi promo ──────────────────────────────────────────────────────
const RATIO_OPTIONS = [
  { value: '16:9', css: '16 / 9', num: 16 / 9, hint: 'Landscape' },
  { value: '21:9', css: '21 / 9', num: 21 / 9, hint: 'Ultrawide' },
  { value: '4:3',  css: '4 / 3',  num: 4 / 3,  hint: 'Klasik' },
  { value: '1:1',  css: '1 / 1',  num: 1,      hint: 'Kotak' },
  { value: '4:5',  css: '4 / 5',  num: 4 / 5,  hint: 'Portrait' },
  { value: '3:4',  css: '3 / 4',  num: 3 / 4,  hint: 'Portrait' },
  { value: '9:16', css: '9 / 16', num: 9 / 16, hint: 'Story' },
]
const LAYOUT_OPTIONS = [
  { value: 'split',   label: 'Gambar + Teks',      hint: 'Gambar di samping teks. Cocok untuk promo menu.' },
  { value: 'overlay', label: 'Teks di atas Gambar', hint: 'Gambar jadi latar kartu lebar. Cocok untuk foto suasana.' },
  { value: 'poster',  label: 'Poster',              hint: 'Gambar tampil utuh, teks di bawah. Cocok untuk flyer 4:5 / 9:16.' },
]
const FOCUS_OPTIONS = [
  { value: 'top-left', label: 'Kiri atas', css: '0% 0%' },
  { value: 'top', label: 'Atas', css: '50% 0%' },
  { value: 'top-right', label: 'Kanan atas', css: '100% 0%' },
  { value: 'left', label: 'Kiri', css: '0% 50%' },
  { value: 'center', label: 'Tengah', css: '50% 50%' },
  { value: 'right', label: 'Kanan', css: '100% 50%' },
  { value: 'bottom-left', label: 'Kiri bawah', css: '0% 100%' },
  { value: 'bottom', label: 'Bawah', css: '50% 100%' },
  { value: 'bottom-right', label: 'Kanan bawah', css: '100% 100%' },
]
const THEME_OPTIONS = [
  { value: 'red',     label: 'Merah',  accent: '#DC2626', ink: '#ffffff' },
  { value: 'amber',   label: 'Kuning', accent: '#F59E0B', ink: '#1c1300' },
  { value: 'emerald', label: 'Hijau',  accent: '#10B981', ink: '#03150d' },
  { value: 'sky',     label: 'Biru',   accent: '#0EA5E9', ink: '#02131c' },
  { value: 'violet',  label: 'Ungu',   accent: '#8B5CF6', ink: '#ffffff' },
  { value: 'pink',    label: 'Pink',   accent: '#EC4899', ink: '#ffffff' },
]
const BADGE_PRESETS = ['Promo', 'Event', 'Baru', 'Terbatas', 'Live Music', 'Nobar', 'Diskon']

// Form teks utama (01–04)
const defaultMain = () => ({
  hero_headline: 'Warkop Level Up Masashimura',
  hero_subheadline: 'Tempat nongkrong kasual modern di Bekasi.',
  hero_bg_image: null,
  hero_food_image: null,
  marquee_text: 'MASA SIH MURAH? • WARKOP EVOLUTION • GOOD FOOD • GOOD VIBES',
  about_text: '',
  about_image: null,
  metric_1: '2024',
  metric_2: '50+',
  metric_3: '★★★★★',
  // Promo & Event
  promo_badge: '',
  promo_title: '',
  promo_text: '',
  promo_link: '',
  promo_link_label: '',
  promo_image: null,
  promo_image_alt: '',
  promo_image_ratio: '16:9',
  promo_layout: 'split',
  promo_image_side: 'left',
  promo_focus: 'center',
  promo_theme: 'red',
  promo_align: 'left',
  promo_overlay: 55,
  promo_from: null,
  promo_until: null,
  promo_countdown: false,
  promo_dismissible: false,
})
const form = ref(defaultMain())
const savedMain = ref(JSON.stringify(defaultMain()))
const hasChanges = computed(() => JSON.stringify(form.value) !== savedMain.value)

// ── Promo: computed ─────────────────────────────────────────────────
const hasPromo = computed(() => !!(form.value.promo_title || form.value.promo_text || form.value.promo_image))

const ratioOpt = computed(() => RATIO_OPTIONS.find((r) => r.value === form.value.promo_image_ratio) || RATIO_OPTIONS[0])
const promoRatioCss = computed(() => ratioOpt.value.css)
const focusOpt = computed(() => FOCUS_OPTIONS.find((f) => f.value === form.value.promo_focus) || FOCUS_OPTIONS[4])
const focusCss = computed(() => focusOpt.value.css)
const focusLabel = computed(() => focusOpt.value.label)
const themeOpt = computed(() => THEME_OPTIONS.find((t) => t.value === form.value.promo_theme) || THEME_OPTIONS[0])

// Kotak kecil penanda rasio di tombol pilihan
const ratioBox = (num) => {
  const base = 28
  return num >= 1
    ? { width: `${base}px`, height: `${Math.round(base / num)}px` }
    : { width: `${Math.round(base * num)}px`, height: `${base}px` }
}

const untilLabel = computed(() => {
  if (!form.value.promo_until) return ''
  const d = new Date(`${form.value.promo_until}T12:00:00+07:00`)
  return isNaN(d) ? form.value.promo_until : d.toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })
})

// ── Pratinjau promo ─────────────────────────────────────────────────
const pvLayout = computed(() => (form.value.promo_image ? form.value.promo_layout : 'text'))
const pvCenter = computed(() => pvLayout.value !== 'split' && pvLayout.value !== 'text' && form.value.promo_align === 'center')
const pvVars = computed(() => ({
  '--pa': themeOpt.value.accent,
  '--pa-ink': themeOpt.value.ink,
  '--pa-soft': `${themeOpt.value.accent}22`,
  '--pa-line': `${themeOpt.value.accent}66`,
}))
const pvWrapClass = computed(() => [
  `pv-wrap--${pvLayout.value}`,
  pvLayout.value === 'split' && form.value.promo_image_side === 'right' ? 'is-right' : '',
])
const pvWrapStyle = computed(() => {
  if (pvLayout.value !== 'overlay') return {}
  const n = ratioOpt.value.num
  return { aspectRatio: ratioOpt.value.css, minHeight: '9rem', maxWidth: n < 1 ? '14rem' : '100%', marginInline: n < 1 ? 'auto' : '0' }
})
const pvMediaStyle = computed(() => {
  const n = ratioOpt.value.num
  if (pvLayout.value === 'overlay') return {}
  let width
  if (pvLayout.value === 'split') width = n >= 1.5 ? '46%' : n >= 1.2 ? '40%' : n >= 0.95 ? '32%' : '24%'
  else width = n >= 1.5 ? '70%' : n >= 1.2 ? '58%' : n >= 0.95 ? '44%' : n >= 0.7 ? '36%' : '26%'
  return { width, aspectRatio: ratioOpt.value.css }
})
const pvShade = computed(() => {
  const s = Math.min(Math.max(Number(form.value.promo_overlay) || 0, 0), 90) / 100
  return `linear-gradient(to top, rgba(8,8,8,${Math.min(1, s + 0.35)}), rgba(8,8,8,${(s * 0.55).toFixed(2)}) 60%, rgba(8,8,8,${(s * 0.2).toFixed(2)}))`
})

const clearPromo = () => {
  const d = defaultMain()
  Object.keys(d).filter((k) => k.startsWith('promo_')).forEach((k) => { form.value[k] = d[k] })
}

// Sub-modul dinamis
const bentoFacilities = ref([])
const galleryData = ref([])

const editingBentoId = ref(null)
const bentoForm = ref({ title: '', icon_name: 'Coffee', size: 'normal', order: 0 })

const editingGalleryId = ref(null)
const galleryForm = ref({ title: '', image_url: '', category: 'Event' })

// Ambil pesan error pertama dari backend (DRF) kalau ada
const apiErrorText = (err, fallback) => {
  const d = err?.response?.data
  if (d && typeof d === 'object') {
    const first = Object.values(d)[0]
    const msg = Array.isArray(first) ? first[0] : first
    if (typeof msg === 'string') return msg
  }
  return fallback
}

// ── Fetch ───────────────────────────────────────────────────────────
const fetchHomepageData = async () => {
  try {
    const [coreRes, bentoRes, galleryRes] = await Promise.all([
      apiClient.get('/homepage/config/current/'),
      apiClient.get('/homepage/bento/'),
      apiClient.get('/homepage/gallery/'),
    ])
    if (coreRes.data) form.value = { ...form.value, ...coreRes.data }
    if (bentoRes.data) bentoFacilities.value = bentoRes.data
    if (galleryRes.data) galleryData.value = galleryRes.data
    savedMain.value = JSON.stringify(form.value)
  } catch (err) {
    console.error('Gagal sinkronisasi data CMS homepage:', err)
    toast.error('Gagal memuat konfigurasi homepage dari server.')
  }
}

// ── Simpan teks utama ───────────────────────────────────────────────
const saveHomepageData = async () => {
  const token = localStorage.getItem('token')
  if (!token) return toast.error('Sesi login tidak ditemukan. Silakan login ulang.')
  isSaving.value = true

  const payload = { ...form.value }
  for (const k of ['hero_food_image', 'hero_bg_image', 'about_image', 'promo_image', 'promo_from', 'promo_until']) {
    if (payload[k] === '') payload[k] = null
  }
  // Hitung mundur hanya masuk akal kalau ada tanggal selesai
  if (!payload.promo_until) payload.promo_countdown = false

  try {
    await apiClient.post('/homepage/config/update/', payload)
    savedMain.value = JSON.stringify(form.value)
    toast.success('Konten utama homepage berhasil dipublikasikan!')
  } catch (err) {
    console.error('Gagal menyimpan konfigurasi homepage:', err)
    toast.error(apiErrorText(err, 'Gagal menyimpan konten ke server.'))
  } finally {
    isSaving.value = false
  }
}

const resetMain = () => { form.value = JSON.parse(savedMain.value) }

const onBeforeUnload = (e) => {
  if (!hasChanges.value) return
  e.preventDefault()
  e.returnValue = ''
}
window.addEventListener('beforeunload', onBeforeUnload)

// ── Cropper + upload Cloudinary (hero/about/gallery) ────────────────
const closeCropper = () => {
  isCropping.value = false
  if (imageSrc.value) URL.revokeObjectURL(imageSrc.value)
  imageSrc.value = ''
}

const startCrop = (file, type) => {
  if (imageSrc.value) URL.revokeObjectURL(imageSrc.value)
  cropType.value = type
  imageSrc.value = URL.createObjectURL(file)
  isCropping.value = true
}

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', onBeforeUnload)
  if (imageSrc.value) URL.revokeObjectURL(imageSrc.value)
})

const handleUploadToCloudinary = async (blobData) => {
  closeCropper()
  const toastId = toast.loading('Mengupload foto…')
  const formData = new FormData()
  formData.append('file', blobData)
  formData.append('upload_preset', CLOUDINARY_UPLOAD_PRESET)

  try {
    const { data } = await axios.post(CLOUDINARY_UPLOAD_URL, formData)
    if (!data?.secure_url) throw new Error('no url')
    const url = data.secure_url
    if (cropType.value === 'hero_bg')   form.value.hero_bg_image   = url
    if (cropType.value === 'hero_food') form.value.hero_food_image = url
    if (cropType.value === 'hero')      form.value.hero_food_image = url // legacy
    if (cropType.value === 'about')     form.value.about_image     = url
    if (cropType.value === 'gallery')   galleryForm.value.image_url = url
    toast.success('Foto berhasil diupload!', { id: toastId })
  } catch {
    toast.error('Gagal upload gambar.', { id: toastId })
  }
}

// ── Upload gambar promo: tanpa cropper, bebas rasio ─────────────────
// Dipotong saat tampil di homepage (CSS) sesuai rasio & titik fokus yang dipilih.
// Di sini hanya diperkecil agar upload cepat & halaman ringan.
const MAX_PROMO_EDGE = 1800
const MAX_PROMO_FILE = 15 * 1024 * 1024

const shrinkImage = (file) => new Promise((resolve, reject) => {
  // GIF dibiarkan apa adanya supaya animasinya tidak hilang
  if (file.type === 'image/gif') return resolve(file)
  const url = URL.createObjectURL(file)
  const img = new Image()
  img.onload = () => {
    URL.revokeObjectURL(url)
    const scale = Math.min(1, MAX_PROMO_EDGE / Math.max(img.naturalWidth, img.naturalHeight))
    if (scale === 1 && file.size <= 1.5 * 1024 * 1024) return resolve(file)
    const canvas = document.createElement('canvas')
    canvas.width = Math.round(img.naturalWidth * scale)
    canvas.height = Math.round(img.naturalHeight * scale)
    canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height)
    // PNG tetap PNG (menjaga transparansi), selain itu JPEG
    const type = file.type === 'image/png' ? 'image/png' : 'image/jpeg'
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('resize'))), type, 0.88)
  }
  img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('load')) }
  img.src = url
})

const uploadPromoImage = async (file) => {
  if (!file?.type?.startsWith('image/')) return toast.warning('File harus berupa gambar.')
  if (file.size > MAX_PROMO_FILE) return toast.warning('Ukuran gambar maksimal 15 MB.')

  const toastId = toast.loading('Mengupload gambar promo…')
  try {
    const blob = await shrinkImage(file)
    const fd = new FormData()
    fd.append('file', blob, file.name || 'promo')
    fd.append('upload_preset', CLOUDINARY_UPLOAD_PRESET)
    const { data } = await axios.post(CLOUDINARY_UPLOAD_URL, fd)
    if (!data?.secure_url) throw new Error('no url')
    form.value.promo_image = data.secure_url
    toast.success('Gambar promo berhasil diupload!', { id: toastId })
  } catch {
    toast.error('Gagal upload gambar promo.', { id: toastId })
  }
}

// ── CRUD Bento ──────────────────────────────────────────────────────
const openBentoModal = (bento = null) => {
  if (bento) {
    editingBentoId.value = bento.id
    bentoForm.value = { title: bento.title, icon_name: bento.icon_name, size: bento.size, order: bento.order }
  } else {
    editingBentoId.value = null
    bentoForm.value = { title: '', icon_name: 'Coffee', size: 'normal', order: bentoFacilities.value.length }
  }
  bentoOpen.value = true
}

const saveBento = async () => {
  if (!bentoForm.value.title.trim()) return toast.warning('Nama fasilitas tidak boleh kosong!')
  isSavingSub.value = true
  try {
    if (editingBentoId.value) {
      await apiClient.put(`/homepage/bento/${editingBentoId.value}/`, bentoForm.value)
      toast.success('Fasilitas diperbarui!')
    } else {
      await apiClient.post('/homepage/bento/create/', bentoForm.value)
      toast.success('Fasilitas baru ditambahkan!')
    }
    bentoOpen.value = false
    const res = await apiClient.get('/homepage/bento/')
    bentoFacilities.value = res.data
  } catch {
    toast.error('Gagal menyimpan data bento.')
  } finally {
    isSavingSub.value = false
  }
}

const deleteBento = async (bento) => {
  const ok = await ask({
    title: 'Hapus fasilitas?',
    message: `"${bento.title}" akan dihapus dari bento grid homepage.`,
    confirmText: 'Ya, hapus',
    danger: true,
  })
  if (!ok) return
  try {
    await apiClient.delete(`/homepage/bento/${bento.id}/`)
    bentoFacilities.value = bentoFacilities.value.filter((b) => b.id !== bento.id)
    toast.success('Fasilitas dihapus.')
  } catch {
    toast.error('Gagal menghapus fasilitas.')
  }
}

// ── CRUD Galeri ─────────────────────────────────────────────────────
const openGalleryModal = (item = null) => {
  if (item) {
    editingGalleryId.value = item.id
    galleryForm.value = { title: item.title || '', image_url: item.image_url, category: item.category || 'Event' }
  } else {
    editingGalleryId.value = null
    galleryForm.value = { title: '', image_url: '', category: 'Event' }
  }
  galleryOpen.value = true
}

const saveGalleryItem = async () => {
  if (!galleryForm.value.image_url) return toast.warning('Upload foto terlebih dahulu!')
  if (!galleryForm.value.title.trim()) return toast.warning('Judul event wajib diisi!')
  isSavingSub.value = true
  try {
    if (editingGalleryId.value) {
      await apiClient.put(`/homepage/gallery/${editingGalleryId.value}/`, galleryForm.value)
      toast.success('Dokumentasi diperbarui!')
    } else {
      await apiClient.post('/homepage/gallery/create/', galleryForm.value)
      toast.success('Dokumentasi dipublikasikan!')
    }
    galleryOpen.value = false
    const res = await apiClient.get('/homepage/gallery/')
    galleryData.value = res.data
  } catch {
    toast.error('Gagal menyimpan dokumentasi foto.')
  } finally {
    isSavingSub.value = false
  }
}

const deleteGalleryItem = async (img) => {
  const ok = await ask({
    title: 'Hapus foto?',
    message: `"${img.title || 'Foto ini'}" akan dihapus dari galeri. Tindakan ini tidak bisa dibatalkan.`,
    confirmText: 'Ya, hapus',
    danger: true,
  })
  if (!ok) return
  try {
    await apiClient.delete(`/homepage/gallery/${img.id}/`)
    galleryData.value = galleryData.value.filter((g) => g.id !== img.id)
    toast.success('Foto dihapus.')
  } catch {
    toast.error('Gagal menghapus foto.')
  }
}

onMounted(fetchHomepageData)
</script>

<style scoped>
/* Nomor section di header card */
.eh-num {
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  width: 38px; height: 38px; border-radius: var(--r-sm);
  background: var(--tint-accent); border: 1px solid var(--line-accent);
  color: var(--accent-text); font-family: var(--font-mono); font-size: 0.78rem; font-weight: 700;
}
.eh-strong { font-weight: 700; }
.eh-code { padding: 1px 6px; border-radius: 4px; background: rgb(var(--ink) / 0.07); font-family: var(--font-mono); color: var(--text-2); }
.eh-metric { text-align: center; font-family: var(--font-display); font-size: 1.1rem; font-weight: 600; }
.eh-metric--star { color: var(--amber-soft); }
.eh-form { display: flex; flex-direction: column; gap: 1rem; }

/* Pratinjau cepat */
.eh-preview-hero { padding: 0.25rem 0 0.25rem 1rem; border-left: 3px solid var(--accent); }
.eh-preview-title { margin: 0; font-family: var(--font-display); font-size: clamp(1.05rem, 0.9rem + 1vw, 1.4rem); font-weight: 600; text-transform: uppercase; color: var(--text); overflow-wrap: anywhere; }
.eh-preview-sub { margin: 0.3rem 0 0; font-size: 0.8125rem; color: var(--text-dim); }
.eh-preview-marquee {
  display: flex; align-items: center; gap: 0.75rem; min-width: 0;
  padding: 0.65rem 0.85rem; border-radius: var(--r-md);
  background: var(--surface-2); border: 1px solid var(--border);
  font-size: 0.75rem; color: var(--text-dim); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.eh-preview-marquee + .eh-preview-marquee { margin-top: 0.5rem; }
.eh-preview-marquee span { flex-shrink: 0; font-weight: 700; color: var(--accent-text); }

/* ── Pilihan promo: kartu opsi ── */
.eh-opts { display: grid; grid-template-columns: repeat(auto-fill, minmax(5.5rem, 1fr)); gap: 0.5rem; }
.eh-opts--wide { grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr)); }
.eh-opt {
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.3rem;
  min-height: 4.6rem; padding: 0.6rem 0.5rem; text-align: center;
  border: 1px solid var(--border); border-radius: var(--r-md);
  background: var(--surface-2); color: var(--text-dim); cursor: pointer;
  transition: border-color 0.15s, background 0.15s, color 0.15s;
}
.eh-opt:hover { border-color: var(--line-accent); color: var(--text); }
.eh-opt.is-selected { border-color: var(--accent); background: var(--tint-accent); color: var(--text); }
.eh-opt--text { align-items: flex-start; text-align: left; padding: 0.75rem 0.85rem; gap: 0.2rem; }
.eh-opt-main { font-size: 0.8125rem; font-weight: 700; }
.eh-opt-sub { font-size: 0.68rem; line-height: 1.35; opacity: 0.75; }
.eh-ratio-box { display: block; border: 2px solid currentColor; border-radius: 3px; opacity: 0.7; }
.eh-opt.is-selected .eh-ratio-box { opacity: 1; border-color: var(--accent); }

/* Titik fokus 3x3 */
.eh-focus-wrap { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }
.eh-focus { display: grid; grid-template-columns: repeat(3, 2.2rem); gap: 0.3rem; padding: 0.4rem; border: 1px solid var(--border); border-radius: var(--r-md); background: var(--surface-2); }
.eh-focus-dot { display: flex; align-items: center; justify-content: center; width: 2.2rem; height: 2.2rem; border: none; border-radius: var(--r-sm); background: transparent; cursor: pointer; }
.eh-focus-dot span { width: 0.55rem; height: 0.55rem; border-radius: 50%; background: var(--text-faint); transition: transform 0.15s, background 0.15s; }
.eh-focus-dot:hover span { background: var(--text-2); }
.eh-focus-dot.is-selected { background: var(--tint-accent); }
.eh-focus-dot.is-selected span { background: var(--accent); transform: scale(1.5); }

/* Preset label */
.eh-presets { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.5rem; }
.eh-preset { padding: 0.3rem 0.65rem; border: 1px solid var(--border); border-radius: 999px; background: transparent; color: var(--text-dim); font-size: 0.72rem; cursor: pointer; transition: all 0.15s; }
.eh-preset:hover { border-color: var(--accent); color: var(--text); }

/* Warna aksen */
.eh-swatches { display: flex; flex-wrap: wrap; gap: 0.6rem; }
.eh-swatch { width: 2.2rem; height: 2.2rem; border-radius: 50%; border: 2px solid transparent; background: var(--sw); cursor: pointer; outline: 2px solid transparent; outline-offset: 2px; transition: transform 0.15s; }
.eh-swatch:hover { transform: scale(1.08); }
.eh-swatch.is-selected { outline-color: var(--sw); border-color: var(--surface); }

.eh-range { width: 100%; accent-color: var(--accent); }

/* Checkbox */
.eh-checks { display: flex; flex-direction: column; gap: 0.75rem; }
.eh-check { display: flex; align-items: flex-start; gap: 0.65rem; cursor: pointer; font-size: 0.8125rem; color: var(--text-2); }
.eh-check input { margin-top: 0.2rem; width: 1rem; height: 1rem; accent-color: var(--accent); flex-shrink: 0; }
.eh-check input:disabled + span { opacity: 0.5; }
.eh-check small { display: block; margin-top: 0.1rem; font-size: 0.7rem; color: var(--text-faint); }

/* ── Pratinjau promo (selalu gelap, meniru homepage) ── */
.pv { border: 1px solid var(--border); border-radius: var(--r-md); background: var(--surface-2); padding: 0.85rem; }
.pv-cap { margin: 0 0 0.6rem; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-faint); }
.pv-empty { padding: 1.2rem; text-align: center; font-size: 0.78rem; color: var(--text-faint); border: 1px dashed var(--border); border-radius: var(--r-sm); }
.pv-stage { padding: 1rem; border-radius: var(--r-sm); background: #0a0a0a; color: #fff; overflow: hidden; }
.pv-wrap { display: flex; gap: 1rem; align-items: center; }
.pv-wrap--split.is-right { flex-direction: row-reverse; }
.pv-wrap--overlay { position: relative; overflow: hidden; border: 1px solid rgb(255 255 255 / 0.1); background: #18181b; align-items: stretch; }
.pv-wrap--poster { flex-direction: column; }
.pv-icon { display: flex; align-items: center; justify-content: center; flex-shrink: 0; width: 2.2rem; height: 2.2rem; border: 1px solid var(--pa-line); background: var(--pa-soft); color: var(--pa); }
.pv-media { position: relative; flex-shrink: 0; overflow: hidden; border: 1px solid rgb(255 255 255 / 0.1); background: #18181b; }
.pv-media img { display: block; width: 100%; height: 100%; object-fit: cover; }
.pv-wrap--overlay .pv-media { position: absolute; inset: 0; width: auto; border: none; }
.pv-shade { position: absolute; inset: 0; }
.pv-copy { position: relative; z-index: 1; min-width: 0; flex: 1; display: flex; flex-direction: column; gap: 0.3rem; }
.pv-wrap--overlay .pv-copy { justify-content: flex-end; padding: 0.9rem; }
.pv-wrap--poster .pv-copy { flex: none; width: 100%; max-width: 22rem; }
.pv-copy.is-center { align-items: center; text-align: center; }
.pv-eyebrow { display: flex; align-items: center; gap: 0.5rem; margin: 0; font-family: var(--font-mono); font-size: 0.6rem; letter-spacing: 0.25em; text-transform: uppercase; color: var(--pa); }
.pv-eyebrow i { display: block; width: 1.2rem; height: 1px; background: var(--pa); }
.pv-title { margin: 0; font-weight: 800; text-transform: uppercase; line-height: 1.15; font-size: 0.95rem; overflow-wrap: anywhere; }
.pv-title--split, .pv-title--overlay { font-size: 1.15rem; }
.pv-text { margin: 0; font-size: 0.74rem; color: #a1a1aa; line-height: 1.5; }
.pv-meta { margin: 0; font-family: var(--font-mono); font-size: 0.62rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--pa); }
.pv-btn { align-self: flex-start; margin-top: 0.4rem; padding: 0.45rem 0.85rem; background: var(--pa); color: var(--pa-ink); font-size: 0.62rem; font-weight: 800; letter-spacing: 0.15em; text-transform: uppercase; }
.pv-copy.is-center .pv-btn { align-self: center; }
.pv-wrap--text { justify-content: space-between; }

/* Bento */
.eh-bento-list { margin: 0; padding: 0; list-style: none; }
.eh-bento-row {
  display: grid; grid-template-columns: auto minmax(0, 1fr) auto auto; align-items: center; gap: 0.85rem;
  padding: 0.8rem 1.25rem; border-bottom: 1px solid var(--border);
}
.eh-bento-row:last-child { border-bottom: none; }
.eh-bento-icon {
  display: flex; align-items: center; justify-content: center;
  width: 40px; height: 40px; border-radius: var(--r-sm);
  background: rgb(var(--ink) / 0.06); color: var(--text-2);
}
.eh-bento-title { margin: 0; font-size: 0.875rem; font-weight: 600; color: var(--text); }
.eh-bento-meta { margin: 0.1rem 0 0; font-size: 0.7rem; color: var(--text-faint); }
.eh-row-actions { display: flex; gap: 0.15rem; }

/* Pemilih icon */
.eh-icons { display: grid; grid-template-columns: repeat(auto-fill, minmax(2.75rem, 1fr)); gap: 0.4rem; padding: 0.5rem; border: 1px solid var(--border); border-radius: var(--r-md); background: var(--surface-2); }
.eh-icon-btn {
  display: flex; align-items: center; justify-content: center;
  aspect-ratio: 1; min-height: 40px; border: 1px solid transparent; border-radius: var(--r-sm);
  background: transparent; color: var(--text-dim); cursor: pointer; transition: background 0.15s, color 0.15s;
}
.eh-icon-btn:hover { background: var(--surface-hover); color: var(--text); }
.eh-icon-btn.is-selected { background: var(--accent); color: var(--on-accent); }

/* Galeri */
.eh-gallery { margin: 0; padding: 0; list-style: none; display: grid; grid-template-columns: repeat(auto-fill, minmax(10rem, 1fr)); gap: 0.85rem; }
.eh-tile { position: relative; aspect-ratio: 1; overflow: hidden; border: 1px solid var(--border); border-radius: var(--r-md); background: var(--surface-2); }
.eh-tile img { display: block; width: 100%; height: 100%; object-fit: cover; }
.eh-tile-caption {
  position: absolute; left: 0; right: 0; bottom: 0; padding: 1.5rem 0.65rem 0.55rem;
  background: linear-gradient(to top, rgb(0 0 0 / 0.78), transparent); color: #fff;
}
.eh-tile-caption p { margin: 0; font-size: 0.75rem; font-weight: 600; }
.eh-tile-caption span { font-size: 0.65rem; opacity: 0.75; }
.eh-tile-actions { position: absolute; top: 0.4rem; right: 0.4rem; display: flex; gap: 0.3rem; transition: opacity 0.15s; }
.eh-tile-btn {
  display: flex; align-items: center; justify-content: center; width: 32px; height: 32px;
  border: 1px solid rgb(255 255 255 / 0.25); border-radius: var(--r-sm);
  background: rgb(0 0 0 / 0.6); color: #fff; cursor: pointer; backdrop-filter: blur(4px);
}
.eh-tile-btn:hover { background: rgb(0 0 0 / 0.85); }
.eh-tile-btn--danger:hover { background: var(--accent); border-color: var(--accent); }
@media (hover: hover) {
  .eh-tile-actions { opacity: 0; }
  .eh-tile:hover .eh-tile-actions, .eh-tile:focus-within .eh-tile-actions { opacity: 1; }
}

@media (max-width: 560px) {
  .eh-bento-row { grid-template-columns: auto minmax(0, 1fr) auto; padding: 0.8rem 1rem; }
  .eh-bento-row .adm-badge { grid-column: 2; grid-row: 2; justify-self: start; }
  .eh-bento-row .eh-row-actions { grid-column: 3; grid-row: 1 / span 2; }
  .adm-card-head { flex-wrap: wrap; }
  .adm-card-head-actions { margin-left: 3.2rem; }
  .eh-gallery { grid-template-columns: repeat(2, 1fr); gap: 0.6rem; }
  .pv-wrap--split, .pv-wrap--split.is-right, .pv-wrap--text { flex-direction: column; align-items: stretch; }
  .pv-media { width: 100% !important; }
}
</style>