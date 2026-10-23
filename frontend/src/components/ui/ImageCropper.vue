<template>
  <Teleport to="body">
    <div class="adm-overlay ic-overlay" @click.stop>
      <div class="adm-modal adm-modal--lg" role="dialog" aria-modal="true" aria-labelledby="ic-title">
        <header class="adm-modal-head">
          <h3 id="ic-title" class="adm-modal-title">Potong Foto {{ cropLabel }}</h3>
          <span class="adm-badge adm-mono">{{ ratioLabel }} · {{ targetResolution.width }} × {{ targetResolution.height }}</span>
        </header>

        <div class="adm-modal-body">
          <!-- Kanvas edit foto tetap gelap supaya kontras dengan gambar, di kedua tema -->
          <div class="ic-stage">
            <cropper
              ref="cropperRef"
              class="ic-cropper"
              :src="image"
              :stencil-props="{ aspectRatio: currentAspectRatio }"
            />

            <div v-if="isGenerating" class="ic-loading">
              <span class="adm-spinner ic-spinner"></span>
            </div>
          </div>
        </div>

        <footer class="adm-modal-foot">
          <button type="button" class="adm-btn adm-btn--ghost" :disabled="isGenerating" @click="onCancel">
            Batal
          </button>
          <button type="button" class="adm-btn adm-btn--primary" :disabled="isGenerating" @click="handleGenerate">
            <span v-if="isGenerating" class="adm-spinner"></span>
            {{ isGenerating ? "Memproses..." : "Simpan Potongan" }}
          </button>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed } from "vue";
import { Cropper } from "vue-advanced-cropper";
import "vue-advanced-cropper/dist/style.css";

const props = defineProps({
  image: String,
  type: {
    type: String,
    default: "menu", // Pilihan: 'menu', 'hero', 'gallery', 'about'
  },
});

const emit = defineEmits(["crop-complete", "cancel"]);
const cropperRef = ref(null);
const isGenerating = ref(false);

// Resolusi output & rasio dihitung otomatis berdasarkan tipe foto.
// PENTING: rasio di sini harus selalu sinkron dengan label tombol upload
// di halaman pemanggil (mis. EditHomepage.vue) dan class aspect-* pada
// preview/tampilan akhirnya (EditHomepage.vue & Home.vue).
const targetResolution = computed(() => {
  switch (props.type) {
    case "hero_bg":
      return { width: 1920, height: 1080 } // Background parallax — 16:9
    case "hero_food":
      return { width: 800, height: 800 }
    case "hero":  // legacy, tetap ada
      return { width: 1920, height: 1080 }
    case "gallery":
      return { width: 800, height: 800 }; // Galeri outlet — 1:1
    case "about":
      return { width: 1000, height: 1000 }; // Foto tentang kedai — 1:1
    case "menu":
    default:
      return { width: 1147, height: 644 }; // Foto menu makanan/minuman — ~16:9
  }
});

const currentAspectRatio = computed(() => {
  const { width, height } = targetResolution.value;
  return width / height;
});

// Label rasio yang ditampilkan, dijaga konsisten dengan targetResolution
// supaya tidak ada lagi mismatch seperti sebelumnya (label "4:3" vs output 1:1).
const ratioLabel = computed(() => {
  const { width, height } = targetResolution.value;
  const divisor = gcd(width, height);
  return `${width / divisor}:${height / divisor}`;
});

const gcd = (a, b) => (b === 0 ? a : gcd(b, a % b));

const cropLabel = computed(() => {
  if (props.type === "hero_bg")   return "Background Hero (Parallax)"
  if (props.type === "hero_food") return "Foto Makanan (Kotak Kanan)"
  if (props.type === "hero") return "Hero Banner Website";
  if (props.type === "gallery") return "Gallery Outlet";
  if (props.type === "about") return "Tentang Toko";
  return "Menu Makanan/Minuman";
});

/**
 * Ambil hasil crop dari cropper, resize ke resolusi target, lalu emit sebagai blob JPEG.
 * Dibungkus state isGenerating agar tombol tidak bisa diklik dobel selama proses berjalan.
 */
const handleGenerate = () => {
  if (!cropperRef.value || isGenerating.value) return;

  isGenerating.value = true;

  const { canvas } = cropperRef.value.getResult();
  if (!canvas) {
    isGenerating.value = false;
    return;
  }

  const { width, height } = targetResolution.value;
  const resized = document.createElement("canvas");
  resized.width = width;
  resized.height = height;
  const ctx = resized.getContext("2d");

  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = "high";
  ctx.drawImage(canvas, 0, 0, width, height);

  resized.toBlob(
    (blob) => {
      isGenerating.value = false;
      if (blob) emit("crop-complete", blob);
    },
    "image/jpeg",
    0.92,
  );
};

const onCancel = () => {
  if (isGenerating.value) return;
  emit("cancel");
};
</script>

<style scoped>
/* Di atas modal admin lain (AdminModal z-index 9000) */
.ic-overlay { z-index: 9500; }
.ic-stage {
  position: relative; width: 100%; height: 400px; overflow: hidden;
  border: 1px solid var(--border); border-radius: var(--r-md);
  background: #000;
}
.ic-cropper { height: 100%; width: 100%; }
.ic-loading {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  background: var(--overlay);
}
.ic-spinner { width: 24px; height: 24px; color: var(--accent-text); }
</style>
