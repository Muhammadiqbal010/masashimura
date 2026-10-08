<template>
  <div class="adm-page adm-page--form">

    <!-- ── Header ─────────────────────────────────────────────────── -->
    <header class="adm-header">
      <div>
        <p class="adm-eyebrow">Masashimura · Admin</p>
        <h1 class="adm-title">Edit Homepage</h1>
        <p class="adm-sub">Kendalikan konten, gambar, teks berjalan, dan statistik halaman depan Masashimura.</p>
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
          </div>
          <div class="adm-field">
            <label class="adm-label" for="metric-3">Angka 3 <span class="adm-opt">(rating)</span></label>
            <input id="metric-3" v-model="form.metric_3" type="text" class="adm-input eh-metric eh-metric--star" />
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
      </div>
    </section>

    <!-- ── Bar simpan (teks utama 01–03) ──────────────────────────── -->
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

    <!-- ── 04. Bento ──────────────────────────────────────────────── -->
    <section class="adm-card adm-card--flush">
      <div class="adm-card-head">
        <span class="eh-num">04</span>
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

    <!-- ── 05. Galeri ─────────────────────────────────────────────── -->
    <section class="adm-card">
      <div class="adm-card-head">
        <span class="eh-num">05</span>
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

    <!-- Cropper -->
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
  Plus, Pencil, Trash2, Save, Eye, LayoutGrid, Image as ImageIcon,
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

// Form teks utama (01–03)
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
})
const form = ref(defaultMain())
const savedMain = ref(JSON.stringify(defaultMain()))
const hasChanges = computed(() => JSON.stringify(form.value) !== savedMain.value)

// Sub-modul dinamis
const bentoFacilities = ref([])
const galleryData = ref([])

const editingBentoId = ref(null)
const bentoForm = ref({ title: '', icon_name: 'Coffee', size: 'normal', order: 0 })

const editingGalleryId = ref(null)
const galleryForm = ref({ title: '', image_url: '', category: 'Event' })

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
  for (const k of ['hero_food_image', 'hero_bg_image', 'about_image']) {
    if (payload[k] === '') payload[k] = null
  }

  try {
    await apiClient.post('/homepage/config/update/', payload)
    savedMain.value = JSON.stringify(form.value)
    toast.success('Konten utama homepage berhasil dipublikasikan!')
  } catch (err) {
    console.error('Gagal menyimpan konfigurasi homepage:', err)
    toast.error('Gagal menyimpan konten ke server.')
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

// ── Cropper + upload Cloudinary (satu jalur untuk hero/about/gallery) ──
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

/* Pratinjau */
.eh-preview-hero { padding: 0.25rem 0 0.25rem 1rem; border-left: 3px solid var(--accent); }
.eh-preview-title { margin: 0; font-family: var(--font-display); font-size: clamp(1.05rem, 0.9rem + 1vw, 1.4rem); font-weight: 600; text-transform: uppercase; color: var(--text); overflow-wrap: anywhere; }
.eh-preview-sub { margin: 0.3rem 0 0; font-size: 0.8125rem; color: var(--text-dim); }
.eh-preview-marquee {
  display: flex; align-items: center; gap: 0.75rem; min-width: 0;
  padding: 0.65rem 0.85rem; border-radius: var(--r-md);
  background: var(--surface-2); border: 1px solid var(--border);
  font-size: 0.75rem; color: var(--text-dim); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.eh-preview-marquee span { flex-shrink: 0; font-weight: 700; color: var(--accent-text); }

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
/* Perangkat dengan mouse: aksi muncul saat hover/fokus. Layar sentuh: selalu tampil. */
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
}
</style>