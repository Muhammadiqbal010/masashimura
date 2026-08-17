<template>
  <div class="max-w-5xl mx-auto p-4 sm:p-6 text-white box-border space-y-8 font-inter">

    <!-- HEADER CMS -->
    <div class="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="font-sora text-3xl font-extrabold uppercase tracking-tight text-white">
          Edit Homepage
        </h1>
        <p class="text-white/40 text-xs font-light mt-1">
          Kendalikan semua konten, gambar, teks berjalan, dan statistik halaman depan Masashimura
        </p>
      </div>
      <div class="flex gap-3">
        <button
          @click="saveHomepageData"
          :disabled="isSaving"
          class="bg-[#DC2626] hover:bg-red-700 text-white font-sora text-xs uppercase tracking-widest px-6 py-3.5 rounded-xl font-bold transition disabled:opacity-50 cursor-pointer w-full sm:w-auto shadow-lg"
        >
          {{ isSaving ? "Menyimpan..." : "Simpan Perubahan Teks Utama" }}
        </button>
      </div>
    </div>

    <div class="space-y-6">

      <!-- 01. HERO SECTION -->
      <div class="bg-[#0F0F0F] border border-white/5 rounded-xl p-6 space-y-4">
        <h2 class="font-sora text-sm font-bold uppercase tracking-wider text-[#DC2626] flex items-center gap-2">
          <span>01.</span> Hero Section (100vh)
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div class="space-y-1.5">
            <label class="text-white/40 uppercase font-bold tracking-wider">Headline Utama</label>
            <input v-model="form.hero_headline" type="text"
              class="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-sm focus:border-red-600 outline-none text-white font-sora font-bold" />
          </div>
          <div class="space-y-1.5">
            <label class="text-white/40 uppercase font-bold tracking-wider">Sub-Headline Singkat</label>
            <input v-model="form.hero_subheadline" type="text"
              class="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-sm focus:border-red-600 outline-none text-white" />
          </div>

          <!-- FOTO BACKGROUND PARALLAX (16:9) -->
          <div class="space-y-1.5 md:col-span-2">
            <label class="text-white/40 uppercase font-bold tracking-wider">
              Foto Background Parallax Hero (16:9)
            </label>
            <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center bg-white/[0.02] border border-white/5 p-4 rounded-xl">
              <div
                @click="triggerImageCrop(null, 'hero_bg')"
                class="w-32 aspect-video bg-zinc-900 rounded-lg overflow-hidden border border-white/10 flex-shrink-0 cursor-pointer group relative"
                title="Klik untuk ganti foto"
              >
                <img v-if="form.hero_bg_image" :src="form.hero_bg_image"
                  class="w-full h-full object-cover group-hover:opacity-60 transition" />
                <div v-else class="w-full h-full flex items-center justify-center text-[10px] text-white/20">No Image</div>
                <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
                  <span class="text-[10px] text-white font-bold bg-black/60 px-2 py-1 rounded">✏️ Ganti</span>
                </div>
              </div>
              <div class="space-y-2 w-full">
                <input type="text" :value="form.hero_bg_image" readonly
                  class="w-full bg-black/40 border border-white/5 rounded-lg p-2.5 text-xs font-mono text-zinc-400 outline-none cursor-not-allowed"
                  placeholder="URL Cloudinary terisi otomatis..." />
                <label class="inline-block bg-white/5 border border-white/10 hover:bg-white/10 text-white font-sora text-[10px] uppercase tracking-widest px-4 py-2.5 rounded-md font-bold transition cursor-pointer">
                  Pilih & Potong Foto Background (16:9)
                  <input type="file" accept="image/*" class="hidden" @change="triggerImageCrop($event, 'hero_bg')" />
                </label>
              </div>
            </div>
          </div>

          <!-- FOTO MAKANAN KOTAK KANAN (1:1) -->
          <div class="space-y-1.5 md:col-span-2">
            <label class="text-white/40 uppercase font-bold tracking-wider">
              Foto Makanan Kotak Kanan Hero (1:1)
            </label>
            <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center bg-white/[0.02] border border-white/5 p-4 rounded-xl">
              <div
                @click="triggerImageCrop(null, 'hero_food')"
                class="w-32 aspect-square bg-zinc-900 rounded-lg overflow-hidden border border-white/10 flex-shrink-0 cursor-pointer group relative"
                title="Klik untuk ganti foto"
              >
                <img v-if="form.hero_food_image" :src="form.hero_food_image"
                  class="w-full h-full object-cover group-hover:opacity-60 transition" />
                <div v-else class="w-full h-full flex items-center justify-center text-[10px] text-white/20">No Image</div>
                <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
                  <span class="text-[10px] text-white font-bold bg-black/60 px-2 py-1 rounded">✏️ Ganti</span>
                </div>
              </div>
              <div class="space-y-2 w-full">
                <input type="text" :value="form.hero_food_image" readonly
                  class="w-full bg-black/40 border border-white/5 rounded-lg p-2.5 text-xs font-mono text-zinc-400 outline-none cursor-not-allowed"
                  placeholder="URL Cloudinary terisi otomatis..." />
                <label class="inline-block bg-white/5 border border-white/10 hover:bg-white/10 text-white font-sora text-[10px] uppercase tracking-widest px-4 py-2.5 rounded-md font-bold transition cursor-pointer">
                  Pilih & Potong Foto Makanan (1:1)
                  <input type="file" accept="image/*" class="hidden" @change="triggerImageCrop($event, 'hero_food')" />
                </label>
              </div>
            </div>
          </div>

          <!--
            NB: Form foto "Outlet Suasana Kedai (1:1)" yang tadinya ada di sini
            SUDAH DIHAPUS karena duplikat 100% dengan form foto about di Section 03
            (sama-sama bind ke form.about_image). Cukup satu saja di Section 03.
          -->
        </div>
      </div>

      <!-- 02. AKSEN TEKS BERJALAN -->
      <div class="bg-[#0F0F0F] border border-white/5 rounded-xl p-6 space-y-4">
        <h2 class="font-sora text-sm font-bold uppercase tracking-wider text-[#DC2626] flex items-center gap-2">
          <span>02.</span> Aksen Teks Berjalan (Marquee)
        </h2>
        <div class="text-xs space-y-1.5">
          <label class="text-white/40 uppercase font-bold tracking-wider">Konten Teks Berjalan (Gunakan • Sebagai Pemisah)</label>
          <input v-model="form.marquee_text" type="text" class="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-sm focus:border-red-600 outline-none text-white font-mono tracking-wide" />
          <p class="text-[10px] text-zinc-600 italic">*Teks berjalan diatur lambat dengan warna abu transparan otomatis.</p>
        </div>
      </div>

      <!-- 03. TENTANG MASASHIMURA & STATISTIK -->
      <div class="bg-[#0F0F0F] border border-white/5 rounded-xl p-6 space-y-4">
        <h2 class="font-sora text-sm font-bold uppercase tracking-wider text-[#DC2626] flex items-center gap-2">
          <span>03.</span> Tentang Masashimura & Statistik
        </h2>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div class="sm:col-span-3 space-y-1.5">
            <label class="text-white/40 uppercase font-bold tracking-wider">Deskripsi Panjang (Teks 50%)</label>
            <textarea v-model="form.about_text" rows="3" class="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-sm focus:border-red-600 outline-none text-white resize-none"></textarea>
          </div>

          <!-- SATU-SATUNYA FORM FOTO ABOUT (dulu duplikat, sekarang cuma di sini) -->
          <div class="sm:col-span-3 space-y-1.5">
            <label class="text-white/40 uppercase font-bold tracking-wider">Foto Outlet Suasana Kedai (Kiri 50%)</label>
            <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center bg-white/[0.02] border border-white/5 p-4 rounded-xl">
              <div
                @click="triggerImageCrop(null, 'about')"
                class="w-24 aspect-square bg-zinc-900 rounded-lg overflow-hidden border border-white/10 flex-shrink-0 cursor-pointer group relative"
                title="Klik untuk ganti foto"
              >
                <img v-if="form.about_image" :src="form.about_image" class="w-full h-full object-cover group-hover:opacity-60 transition" alt="Preview About" />
                <div v-else class="w-full h-full flex items-center justify-center text-[10px] text-white/20">No Image</div>
                <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
                  <span class="text-[10px] text-white font-bold bg-black/60 px-2 py-1 rounded">✏️ Ganti</span>
                </div>
              </div>
              <div class="space-y-2 w-full">
                <input type="text" :value="form.about_image" readonly class="w-full bg-black/40 border border-white/5 rounded-lg p-2.5 text-xs font-mono text-zinc-400 outline-none cursor-not-allowed" placeholder="URL Cloudinary terisi otomatis..." />
                <label class="inline-block bg-white/5 border border-white/10 hover:bg-white/10 text-white font-sora text-[10px] uppercase tracking-widest px-4 py-2.5 rounded-md font-bold transition cursor-pointer">
                  Pilih & Potong Foto (1:1)
                  <input type="file" accept="image/*" class="hidden" @change="triggerImageCrop($event, 'about')" />
                </label>
              </div>
            </div>
          </div>

          <div class="space-y-1.5">
            <label class="text-white/40 uppercase font-bold tracking-wider">Data Angka 1 (Tahun Berdiri)</label>
            <input v-model="form.metric_1" type="text" class="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-sm focus:border-red-600 outline-none text-white font-sora font-bold text-center" />
          </div>
          <div class="space-y-1.5">
            <label class="text-white/40 uppercase font-bold tracking-wider">Data Angka 2 (Jumlah Menu)</label>
            <input v-model="form.metric_2" type="text" class="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-sm focus:border-red-600 outline-none text-white font-sora font-bold text-center" />
          </div>
          <div class="space-y-1.5">
            <label class="text-white/40 uppercase font-bold tracking-wider">Data Angka 3 (Rating Simbol)</label>
            <input v-model="form.metric_3" type="text" class="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-sm focus:border-red-600 outline-none text-amber-500 font-bold text-center" />
          </div>
        </div>
      </div>

      <!-- 04. CORE BENTO GRID LAMA (TETAP DIAMANKAN UNTUK COMPATIBILITY) -->
      <div class="hidden bg-[#0F0F0F] border border-white/5 rounded-xl p-6 space-y-4">
        <h2 class="font-sora text-sm font-bold uppercase tracking-wider text-[#DC2626] flex items-center gap-2">
          <span>04.</span> Core Bento Grid Teks & Status (Legacy Columns)
        </h2>
      </div>

      <!-- 🔥 05. NEW BENTO GRID MANAGEMENT MODULAR (Dinamis CRUD) -->
      <div class="bg-[#0F0F0F] border border-white/5 rounded-xl p-6 space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="font-sora text-sm font-bold uppercase tracking-wider text-[#DC2626] flex items-center gap-2">
            <span>05.</span> Sistem Arsitektur Bento Grid (Dinamis)
          </h2>
          <button @click="openBentoModal(null)" class="bg-[#DC2626]/10 border border-[#DC2626]/20 text-[#DC2626] hover:bg-[#DC2626]/20 text-[10px] font-sora font-bold uppercase tracking-widest px-4 py-2 rounded-lg transition-all flex items-center gap-1 cursor-pointer">
            + Tambah Fasilitas
          </button>
        </div>

        <div class="overflow-x-auto rounded-xl border border-white/5 text-xs">
          <table class="w-full text-left font-sora">
            <thead class="bg-white/[0.02] text-zinc-400 uppercase font-bold tracking-wider border-b border-white/5">
              <tr>
                <th class="p-4">Fasilitas</th>
                <th class="p-4">Icon Name</th>
                <th class="p-4">Card Size</th>
                <th class="p-4 text-center">Aksi</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/5">
              <tr v-for="bento in bentoFacilities" :key="bento.id" class="hover:bg-white/[0.01] transition-colors">
                <td class="p-4 font-bold text-white tracking-wide">{{ bento.title }}</td>
                <td class="p-4 font-mono text-zinc-400">{{ bento.icon_name }}</td>
                <td class="p-4">
                  <span :class="bento.size === 'large' ? 'bg-red-600/10 text-red-500 border border-red-500/20' : 'bg-zinc-800 text-zinc-400'" class="px-2 py-0.5 rounded text-[9px] font-bold uppercase">
                    {{ bento.size === 'large' ? 'Large (2x2)' : 'Normal (1x1)' }}
                  </span>
                </td>
                <td class="p-4 flex justify-center gap-3">
                  <button @click="openBentoModal(bento)" class="text-zinc-400 hover:text-white transition-colors cursor-pointer">Edit</button>
                  <button @click="deleteBento(bento.id)" class="text-zinc-500 hover:text-red-500 transition-colors cursor-pointer">Hapus</button>
                </td>
              </tr>
              <tr v-if="bentoFacilities.length === 0">
                <td colspan="4" class="p-6 text-center text-zinc-600 italic">Belum ada fasilitas bento di database.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 🔥 06. NEW GALLERY & EVENT MANAGEMENT MODULAR (Dinamis CRUD, kini bisa full-edit) -->
      <div class="bg-[#0F0F0F] border border-white/5 rounded-xl p-6 space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="font-sora text-sm font-bold uppercase tracking-wider text-[#DC2626] flex items-center gap-2">
            <span>06.</span> Gallery & Dokumentasi Event (Dinamis)
          </h2>
          <button @click="openGalleryModal()" class="bg-[#DC2626]/10 border border-[#DC2626]/20 text-[#DC2626] hover:bg-[#DC2626]/20 text-[10px] font-sora font-bold uppercase tracking-widest px-4 py-2 rounded-lg transition-all flex items-center gap-1 cursor-pointer">
            + Upload Foto Event
          </button>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 pt-2">
          <div v-for="img in galleryData" :key="img.id" class="group relative aspect-square rounded-xl overflow-hidden border border-white/5 bg-zinc-900 shadow-md">
            <img :src="img.image_url" class="w-full h-full object-cover" />
            <div class="absolute inset-0 bg-black/80 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex flex-col justify-between p-3">
              <div class="flex justify-end gap-2">
                <button @click="openGalleryModal(img)" class="bg-white/10 hover:bg-white/20 border border-white/20 text-white text-[10px] font-bold px-2 py-1 rounded transition-all cursor-pointer">Edit</button>
                <button @click="deleteGalleryItem(img.id)" class="bg-red-600/20 hover:bg-red-600 border border-red-500/30 text-white text-[10px] font-bold px-2 py-1 rounded transition-all cursor-pointer">Hapus</button>
              </div>
              <p class="text-[9px] font-sora font-bold uppercase tracking-wider text-white line-clamp-2">{{ img.title || 'Tanpa Judul' }}</p>
            </div>
          </div>
          <div v-if="galleryData.length === 0" class="col-span-full py-8 text-center text-zinc-600 italic border border-dashed border-white/10 rounded-xl text-xs">Belum ada data dokumentasi foto event.</div>
        </div>
      </div>

    </div>

    <!-- LIVE CHECK PREVIEW -->
    <div class="pt-6 border-t border-white/10">
      <h3 class="font-sora text-xs font-bold uppercase tracking-widest text-zinc-500 mb-4">// LIVE CONTENT PREVIEW CHECK</h3>
      <div class="bg-[#050505] border border-white/10 rounded-2xl p-6 space-y-4">
        <div class="border-l-2 border-[#DC2626] pl-4">
          <p class="font-sora text-lg font-extrabold uppercase text-white">{{ form.hero_headline || 'Headline Kosong' }}</p>
          <p class="text-zinc-500 text-xs mt-1">{{ form.hero_subheadline }}</p>
        </div>
        <div class="bg-[#0F0F0F] p-3 rounded-lg text-[11px] font-mono text-zinc-400 overflow-hidden text-ellipsis whitespace-nowrap">
          <span class="text-[#DC2626] font-bold">Marquee Realtime:</span> {{ form.marquee_text }}
        </div>
      </div>
    </div>

    <!-- 🔥 MODAL POPUP FORM CRUD UNTUK SUB-MODUL BENTO & GALLERY -->
    <div v-if="showModal" class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div class="bg-[#0A0A0A] border border-white/10 rounded-2xl p-6 max-w-sm w-full space-y-5 shadow-2xl">

        <h3 class="font-sora text-xs font-bold uppercase tracking-wider text-white border-b border-white/5 pb-2">
          <span v-if="modalType === 'bento'">{{ editingBentoId ? '✏️ Edit Fasilitas Bento' : '➕ Tambah Fasilitas Bento' }}</span>
          <span v-else>{{ editingGalleryId ? '✏️ Edit Dokumentasi Foto' : '📸 Upload Foto Event Baru' }}</span>
        </h3>

        <!-- FORM BENTO -->
        <div v-if="modalType === 'bento'" class="space-y-4 text-xs font-sora">
          <div>
            <label class="block uppercase text-zinc-500 mb-2 tracking-wide font-bold">Nama Fasilitas</label>
            <input v-model="bentoForm.title" type="text" placeholder="Contoh: WiFi 150Mbps" class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 focus:border-red-600 outline-none text-white font-bold" />
          </div>

          <!-- DROPDOWN ICON DINAMIS DENGAN PREVIEW -->
          <div>
            <label class="block uppercase text-zinc-500 mb-2 tracking-wide font-bold">Pilih Icon</label>
            <div class="grid grid-cols-6 gap-2 bg-white/5 p-2 rounded-xl border border-white/10">
              <button
                v-for="(comp, name) in iconMap"
                :key="name"
                @click="bentoForm.icon_name = name"
                :class="[
                  bentoForm.icon_name === name ? 'bg-red-600 text-white' : 'hover:bg-white/10 text-zinc-400',
                  'p-2 rounded-lg flex items-center justify-center transition-all'
                ]"
                type="button"
              >
                <component :is="comp" :size="16" />
              </button>
            </div>
            <p class="text-[9px] text-zinc-500 mt-1 uppercase font-bold tracking-wider">Terpilih: {{ bentoForm.icon_name }}</p>
          </div>

          <div>
            <label class="block uppercase text-zinc-500 mb-2 tracking-wide font-bold">Ukuran Grid Layout</label>
            <select v-model="bentoForm.size" class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 focus:border-red-600 outline-none text-white font-bold">
              <option value="normal" class="bg-[#0A0A0A]">Standard Card (1x1)</option>
              <option value="large" class="bg-[#0A0A0A]">Large Card (2x2)</option>
            </select>
          </div>
        </div>

        <!-- FORM GALLERY EVENT (FULL EDIT: JUDUL, KATEGORI, FOTO DENGAN CROP) -->
        <div v-if="modalType === 'gallery'" class="space-y-3 text-[11px] font-sora">
          <div class="space-y-1">
            <label class="block uppercase text-zinc-500 font-bold tracking-wide">Judul Event / Dokumentasi</label>
            <input v-model="galleryForm.title" type="text" placeholder="Contoh: Nobar Akbar Semifinal" class="w-full bg-white/5 border border-white/10 rounded-lg p-3 focus:border-red-600 outline-none text-white font-bold" />
          </div>

          <div class="space-y-1">
            <label class="block uppercase text-zinc-500 font-bold tracking-wide">Kategori</label>
            <input v-model="galleryForm.category" type="text" placeholder="Contoh: Suasana Kedai, Event, Best Seller" class="w-full bg-white/5 border border-white/10 rounded-lg p-3 focus:border-red-600 outline-none text-white" />
          </div>

          <div class="space-y-1">
            <label class="block uppercase text-zinc-500 font-bold tracking-wide">Foto Dokumentasi (1:1)</label>
            <div class="flex flex-col items-center gap-3 bg-white/5 border border-dashed border-white/10 rounded-lg p-4">
              <div
                @click="triggerImageCrop(null, 'gallery')"
                class="w-24 aspect-square bg-zinc-900 rounded-lg overflow-hidden border border-white/10 cursor-pointer group relative flex-shrink-0"
                title="Klik untuk pilih & potong foto"
              >
                <img v-if="galleryForm.image_url" :src="galleryForm.image_url" class="w-full h-full object-cover group-hover:opacity-60 transition" />
                <div v-else class="w-full h-full flex items-center justify-center text-[9px] text-white/20">No Image</div>
                <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
                  <span class="text-[9px] text-white font-bold bg-black/60 px-2 py-1 rounded">✏️ Ganti</span>
                </div>
              </div>
              <label class="inline-block bg-white/5 border border-white/10 hover:bg-white/10 text-white font-sora text-[10px] uppercase tracking-widest px-4 py-2.5 rounded-md font-bold transition cursor-pointer">
                Pilih & Potong Foto (1:1)
                <input type="file" accept="image/*" class="hidden" @change="triggerImageCrop($event, 'gallery')" />
              </label>
            </div>
          </div>
        </div>

        <!-- BUTTONS ACTION -->
        <div class="flex justify-end gap-2 pt-3 border-t border-white/5 text-[10px] font-bold uppercase tracking-wider">
          <button @click="showModal = false" class="bg-transparent border border-white/10 hover:bg-white/5 text-white px-4 py-2.5 rounded-lg cursor-pointer">Batal</button>
          <button @click="modalType === 'bento' ? saveBento() : saveGalleryItem()" :disabled="isSavingSub" class="bg-red-600 hover:bg-red-700 text-white px-5 py-2.5 rounded-lg disabled:opacity-50 cursor-pointer">
            {{ isSavingSub ? 'Menyimpan...' : 'Simpan Data' }}
          </button>
        </div>

      </div>
    </div>

    <!-- COMPONENT CROPPER BAWAAN LO -->
    <ImageCropper
      v-if="isCropping"
      :image="imageSrc"
      :type="cropType"
      @crop-complete="handleUploadToCloudinary"
      @cancel="isCropping = false"
    />

  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue";
import { toast } from "vue-sonner";
import axios from "axios";
import ImageCropper from "@/components/ui/ImageCropper.vue";
import {
  Coffee, Wifi, Zap, Utensils, DollarSign, Moon, Shield, Tv,
  Music, Gamepad2, Beer, BatteryCharging, Heart, Award, Smartphone
} from "lucide-vue-next";

// Objek mapping icon agar bisa di-looping di template
const iconMap = {
  Coffee, Wifi, Zap, Utensils, DollarSign, Moon, Shield, Tv,
  Music, Gamepad2, Beer, BatteryCharging, Heart, Award, Smartphone
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const CLOUDINARY_CLOUD_NAME = import.meta.env.VITE_CLOUDINARY_CLOUD_NAME;
const CLOUDINARY_UPLOAD_PRESET = import.meta.env.VITE_CLOUDINARY_UPLOAD_PRESET;
const CLOUDINARY_UPLOAD_URL = `https://api.cloudinary.com/v1_1/${CLOUDINARY_CLOUD_NAME}/image/upload`;

const isSaving = ref(false);
const isSavingSub = ref(false);
const isCropping = ref(false);
const showModal = ref(false);
const modalType = ref("bento");

const imageSrc = ref("");
const cropType = ref("hero");

// Form Teks Utama 01-04
const form = ref({
  hero_headline: "Warkop Level Up Masashimura",
  hero_subheadline: "Tempat nongkrong kasual modern di Bekasi.",
  hero_bg_image: null,
  hero_food_image: null,
  marquee_text: "MASA SIH MURAH? • WARKOP EVOLUTION • GOOD FOOD • GOOD VIBES",
  about_text: "",
  about_image: null,
  metric_1: "2024",
  metric_2: "50+",
  metric_3: "★★★★★",
})

// State Sub-Modul 05 & 06 Dinamis
const bentoFacilities = ref([]);
const galleryData = ref([]);

// Form State CRUD Modal Local
const editingBentoId = ref(null);
const bentoForm = ref({ title: "", icon_name: "Coffee", size: "normal", order: 0 });

const editingGalleryId = ref(null);
const galleryForm = ref({ title: "", image_url: "", category: "Event" });

// ================= INTEGRASI FETCH DATA SINKRONUS =================
const fetchHomepageData = async () => {
  try {
    const [coreRes, bentoRes, galleryRes] = await Promise.all([
      axios.get(`${API_BASE_URL}/api/homepage/config/current/`),
      axios.get(`${API_BASE_URL}/api/homepage/bento/`),
      axios.get(`${API_BASE_URL}/api/homepage/gallery/`)
    ]);

    if (coreRes.data) form.value = { ...form.value, ...coreRes.data };
    if (bentoRes.data) bentoFacilities.value = bentoRes.data;
    if (galleryRes.data) galleryData.value = galleryRes.data;
  } catch (err) {
    console.error("Gagal sinkronisasi data CMS homepage:", err);
    toast.error("Gagal memuat konfigurasi variabel homepage dari server database.");
  }
};

// ================= MANAJEMEN DATA 01-04 TEKS UTAMA =================
const saveHomepageData = async () => {
  const token = localStorage.getItem("token");
  if (!token) return toast.error("Sesi login tidak ditemukan. Silakan login ulang.");
  isSaving.value = true;

  const payload = { ...form.value };
  if (payload.hero_food_image === "") payload.hero_food_image = null;
  if (payload.hero_bg_image === "") payload.hero_bg_image = null;
  if (payload.about_image === "") payload.about_image = null;

  try {
    await axios.post(`${API_BASE_URL}/api/homepage/config/update/`, payload, {
      headers: { Authorization: `Token ${token}` },
    });
    toast.success("Konten Teks Utama Homepage berhasil dipublikasikan!");
  } catch (err) {
    console.error("Gagal menyimpan konfigurasi homepage:", err);
    toast.error("Gagal menyimpan konfigurasi teks ke database server.");
  } finally {
    isSaving.value = false;
  }
};

// ================= ENGINE CLOUDINARY UNTUK CROPPER (HERO, ABOUT, GALLERY) =================
// Satu jalur upload+crop terpusat dipakai bersama oleh hero/about/gallery — ngga ada lagi
// fungsi upload duplikat khusus galeri (uploadGalleryToCloudinary lama sudah dihapus).
const triggerImageCrop = (event, type) => {
  cropType.value = type

  if (event === null) {
    // Klik dari foto preview — buat hidden input secara programatis
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'image/*'
    input.onchange = (e) => {
      const file = e.target.files[0]
      if (!file) return
      imageSrc.value = URL.createObjectURL(file)
      isCropping.value = true
    }
    input.click()
    return
  }

  // Dari input file biasa
  const file = event.target.files[0]
  if (!file) return
  imageSrc.value = URL.createObjectURL(file)
  isCropping.value = true
}

onBeforeUnmount(() => {
  if (imageSrc.value) URL.revokeObjectURL(imageSrc.value);
});

const handleUploadToCloudinary = async (blobData) => {
  isCropping.value = false
  const toastId = toast.loading("Mengupload foto ke Cloudinary...")
  const formData = new FormData()
  formData.append("file", blobData)
  formData.append("upload_preset", CLOUDINARY_UPLOAD_PRESET)

  try {
    const { data } = await axios.post(CLOUDINARY_UPLOAD_URL, formData)
    if (data?.secure_url) {
      if (cropType.value === "hero_bg")   form.value.hero_bg_image   = data.secure_url
      if (cropType.value === "hero_food") form.value.hero_food_image = data.secure_url
      if (cropType.value === "hero")      form.value.hero_food_image = data.secure_url // legacy
      if (cropType.value === "about")     form.value.about_image     = data.secure_url
      if (cropType.value === "gallery")   galleryForm.value.image_url = data.secure_url
      toast.success("Foto berhasil diupload!", { id: toastId })
    }
  } catch {
    toast.error("Gagal upload gambar.", { id: toastId })
  }
}

// ================= CRUD SERVICES: 05. BENTO GRID =================
const openBentoModal = (bento = null) => {
  modalType.value = "bento";
  if (bento) {
    editingBentoId.value = bento.id;
    bentoForm.value = { title: bento.title, icon_name: bento.icon_name, size: bento.size, order: bento.order };
  } else {
    editingBentoId.value = null;
    bentoForm.value = { title: "", icon_name: "Coffee", size: "normal", order: bentoFacilities.value.length };
  }
  showModal.value = true;
};

const saveBento = async () => {
  if (!bentoForm.value.title.trim()) return toast.warning("Nama fasilitas bento tidak boleh kosong!");
  isSavingSub.value = true;
  const token = localStorage.getItem("token");
  const config = { headers: { Authorization: `Token ${token}` } };

  try {
    if (editingBentoId.value) {
      await axios.put(`${API_BASE_URL}/api/homepage/bento/${editingBentoId.value}/`, bentoForm.value, config);
      toast.success("Variabel bento grid diperbarui!");
    } else {
      await axios.post(`${API_BASE_URL}/api/homepage/bento/create/`, bentoForm.value, config);
      toast.success("Fasilitas bento baru ditambahkan!");
    }
    showModal.value = false;
    const res = await axios.get(`${API_BASE_URL}/api/homepage/bento/`);
    bentoFacilities.value = res.data;
  } catch (err) {
    toast.error("Gagal memproses data bento grid.");
  } finally {
    isSavingSub.value = false;
  }
};

const deleteBento = async (id) => {
  if (!confirm("Hapus item fasilitas bento grid ini?")) return;
  const token = localStorage.getItem("token");
  try {
    await axios.delete(`${API_BASE_URL}/api/homepage/bento/${id}/`, {
      headers: { Authorization: `Token ${token}` }
    });
    toast.success("Fasilitas bento sukses dibersihkan!");
    bentoFacilities.value = bentoFacilities.value.filter(b => b.id !== id);
  } catch (err) {
    toast.error("Gagal menghapus entitas bento.");
  }
};

// ================= CRUD SERVICES: 06. GALLERY EVENT (SEKARANG FULL EDIT) =================
const openGalleryModal = (item = null) => {
  modalType.value = "gallery";
  if (item) {
    // Mode edit: prefill judul, kategori, dan foto yang sudah ada
    editingGalleryId.value = item.id;
    galleryForm.value = {
      title: item.title || "",
      image_url: item.image_url,
      category: item.category || "Event",
    };
  } else {
    // Mode tambah baru
    editingGalleryId.value = null;
    galleryForm.value = { title: "", image_url: "", category: "Event" };
  }
  showModal.value = true;
};

const saveGalleryItem = async () => {
  if (!galleryForm.value.image_url) return toast.warning("Unggah berkas foto terlebih dahulu!");
  if (!galleryForm.value.title.trim()) return toast.warning("Judul event wajib diisi!");
  isSavingSub.value = true;
  const token = localStorage.getItem("token");
  const config = { headers: { Authorization: `Token ${token}` } };

  try {
    if (editingGalleryId.value) {
      // Update data yang sudah ada — tidak perlu hapus dulu
      await axios.put(`${API_BASE_URL}/api/homepage/gallery/${editingGalleryId.value}/`, galleryForm.value, config);
      toast.success("Dokumentasi event berhasil diperbarui!");
    } else {
      await axios.post(`${API_BASE_URL}/api/homepage/gallery/create/`, galleryForm.value, config);
      toast.success("Dokumentasi event berhasil dipublikasikan!");
    }
    showModal.value = false;
    const res = await axios.get(`${API_BASE_URL}/api/homepage/gallery/`);
    galleryData.value = res.data;
  } catch (err) {
    toast.error("Gagal menyimpan data dokumentasi foto ke database.");
  } finally {
    isSavingSub.value = false;
  }
};

const deleteGalleryItem = async (id) => {
  if (!confirm("Hapus dokumentasi foto ini dari server cloud Cloudinary?")) return;
  const token = localStorage.getItem("token");
  try {
    await axios.delete(`${API_BASE_URL}/api/homepage/gallery/${id}/`, {
      headers: { Authorization: `Token ${token}` }
    });
    toast.success("Foto event berhasil dibuang!");
    galleryData.value = galleryData.value.filter(g => g.id !== id);
  } catch (err) {
    toast.error("Gagal menghapus aset media galeri.");
  }
};

onMounted(fetchHomepageData);
</script>