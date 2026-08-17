<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-[99999] bg-black/90 backdrop-blur-sm flex items-center justify-center p-4"
      @click.stop
    >
      <div
        class="w-full max-w-2xl bg-[#121212] p-6 rounded-lg border border-white/10 shadow-2xl font-inter"
      >
        <!-- Judul dinamis menyesuaikan tipe -->
        <h3
          class="text-center mb-4 font-oswald uppercase tracking-widest text-amber-500 text-sm"
        >
          Potong Foto {{ cropLabel }} ({{ ratioLabel }} • Output {{ targetResolution.width }} × {{ targetResolution.height }})
        </h3>

        <div
          class="relative w-full h-[400px] bg-black overflow-hidden rounded-md border border-white/5"
        >
          <cropper
            ref="cropperRef"
            class="h-full w-full"
            :src="image"
            :stencil-props="{ aspectRatio: currentAspectRatio }"
          />

          <!-- Overlay loading saat proses resize/generate canvas -->
          <div
            v-if="isGenerating"
            class="absolute inset-0 bg-black/70 flex items-center justify-center"
          >
            <div class="animate-spin w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full"></div>
          </div>
        </div>

        <div class="mt-6 flex gap-4">
          <button
            type="button"
            @click="onCancel"
            :disabled="isGenerating"
            class="flex-1 py-3 bg-white/10 text-white uppercase text-xs font-bold rounded hover:bg-white/20 transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Batal
          </button>
          <button
            type="button"
            @click="handleGenerate"
            :disabled="isGenerating"
            class="flex-[2] py-3 bg-amber-600 text-black uppercase text-xs font-bold rounded hover:bg-amber-500 transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {{ isGenerating ? "Memproses..." : "Simpan Potongan" }}
          </button>
        </div>
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