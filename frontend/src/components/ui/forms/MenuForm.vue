<template>
  <!-- Overlay -->
  <div
    class="fixed inset-0 z-[9999] bg-black/70 backdrop-blur-sm flex items-center justify-center p-4"
    @click.self="emit('close')"
  >
    <!-- Modal -->
    <div
      class="w-full max-w-2xl bg-[#111] rounded-2xl border border-white/10 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
    >
      <!-- Header -->
      <div class="flex items-center justify-between px-8 py-5 border-b border-white/10 bg-[#161616]">
        <div>
          <h2 class="text-xl font-oswald uppercase tracking-widest text-white">
            {{ editingMenu ? "Edit Menu" : "Tambah Menu Baru" }}
          </h2>
          <p class="text-xs text-white/40 mt-1">Lengkapi data menu di bawah ini.</p>
        </div>
        <button type="button" @click="emit('close')" class="text-white/50 hover:text-white text-xl transition">
          ✕
        </button>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit" class="flex flex-col flex-1 overflow-hidden">

        <!-- Body -->
        <div class="flex-1 overflow-y-auto p-8 space-y-6 custom-scroll">

          <!-- Nama -->
          <div>
            <label class="block mb-2 text-[10px] uppercase tracking-widest text-white/40 font-oswald">
              Nama Menu
            </label>
            <input
              v-model="form.name"
              type="text"
              required
              placeholder="Contoh: Mie Jebew Spesial"
              class="w-full rounded-xl border border-white/10 bg-black px-5 py-3 text-white outline-none transition focus:border-red-600 focus:ring-1 focus:ring-red-600"
            />
          </div>

          <!-- Deskripsi -->
          <div>
            <label class="block mb-2 text-[10px] uppercase tracking-widest text-white/40 font-oswald">
              Deskripsi
            </label>
            <textarea
              v-model="form.description"
              rows="3"
              placeholder="Jelaskan menu ini..."
              class="w-full rounded-xl border border-white/10 bg-black px-5 py-3 text-white outline-none transition focus:border-red-600"
            />
          </div>

          <!-- Category + Price -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">

            <!-- Category -->
            <div class="relative">
              <label class="block mb-2 text-[10px] uppercase tracking-widest text-white/40 font-oswald">
                Kategori
              </label>
              <button
                type="button"
                @click="showCatDropdown = !showCatDropdown"
                class="w-full rounded-xl border border-white/10 bg-black px-5 py-3 text-left text-white flex items-center justify-between hover:border-red-600 transition"
              >
                <span>{{ getCategoryLabel() }}</span>
                <svg
                  class="w-4 h-4 transition"
                  :class="{ 'rotate-180': showCatDropdown }"
                  fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <div
                v-if="showCatDropdown"
                class="absolute left-0 right-0 mt-2 rounded-xl border border-white/10 bg-[#181818] overflow-hidden shadow-2xl z-50"
              >
                <button
                  v-for="cat in categories"
                  :key="cat.id"
                  type="button"
                  @click="form.category = cat.id; showCatDropdown = false"
                  class="block w-full text-left px-5 py-3 hover:bg-red-600/20 transition text-white"
                >
                  {{ cat.name }}
                </button>
              </div>
            </div>

            <!-- Price -->
            <div>
              <label class="block mb-2 text-[10px] uppercase tracking-widest text-white/40 font-oswald">
                Harga (Rp)
              </label>
              <input
                v-model="form.price"
                type="number"
                required
                min="0"
                placeholder="25000"
                class="no-spinner w-full rounded-xl border border-white/10 bg-black px-5 py-3 text-white outline-none transition focus:border-red-600"
              />
            </div>

          </div>

          <!-- Foto Menu -->
          <div>
            <label class="block mb-3 text-[10px] uppercase tracking-widest text-white/40 font-oswald">
              Foto Menu
            </label>

            <!-- Preview foto — klik untuk ganti/crop -->
            <div
              v-if="previewImage"
              @click="openFilePicker"
              class="mb-3 overflow-hidden rounded-xl border border-white/10 cursor-pointer group relative"
              title="Klik untuk ganti atau crop ulang foto"
            >
              <img :src="previewImage" class="h-56 w-full object-cover transition group-hover:opacity-60" />
              <!-- Overlay hint -->
              <div class="absolute inset-0 flex flex-col items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition bg-black/40">
                <span class="text-2xl">✏️</span>
                <span class="font-oswald text-xs uppercase tracking-widest text-white">Klik untuk ganti foto</span>
              </div>
            </div>

            <!-- Hidden file input -->
            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              class="hidden"
              @change="onFileChange"
            />

            <!-- Tombol upload — muncul jika belum ada foto -->
            <button
              v-if="!previewImage"
              type="button"
              @click="openFilePicker"
              class="w-full rounded-xl border border-dashed border-white/20 py-8 flex flex-col items-center gap-2 text-xs uppercase tracking-widest text-white/40 transition hover:border-red-600 hover:text-white"
            >
              <span class="text-2xl">📷</span>
              <span>Unggah Foto Menu</span>
              <span class="text-[10px] normal-case text-white/20 tracking-normal">Klik untuk pilih gambar · Akan dicrop otomatis</span>
            </button>

            <!-- Tombol ganti — muncul jika sudah ada foto, sebagai alternatif klik gambar -->
            <button
              v-if="previewImage"
              type="button"
              @click="openFilePicker"
              class="mt-2 w-full rounded-xl border border-white/10 py-2.5 text-[10px] uppercase tracking-widest text-white/40 transition hover:border-red-600 hover:text-white"
            >
              Ganti Foto
            </button>
          </div>

        </div>

        <!-- Footer -->
        <div class="border-t border-white/10 bg-[#161616] px-8 py-5 flex gap-4">
          <button
            type="button"
            @click="emit('close')"
            class="flex-1 rounded-xl border border-white/10 py-4 text-xs uppercase tracking-widest text-white/50 transition hover:bg-white/5 hover:text-white"
          >
            Batal
          </button>
          <button
            type="submit"
            :disabled="loading"
            class="flex-1 rounded-xl bg-red-600 py-4 text-xs font-bold uppercase tracking-widest text-white transition hover:bg-red-500 disabled:opacity-50"
          >
            {{ loading ? "Menyimpan..." : editingMenu ? "Simpan Perubahan" : "Tambah Menu" }}
          </button>
        </div>

      </form>
    </div>

    <!-- ImageCropper — ditaruh di luar modal agar z-index tidak konflik -->
    <ImageCropper
      v-if="showCropper"
      :image="rawImageForCrop"
      type="menu"
      @crop-complete="onCropComplete"
      @cancel="onCropCancel"
    />

  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from "vue"
import { toast } from "vue-sonner"
import apiClient from "@/api/client"
import ImageCropper from "../ImageCropper.vue"

const props = defineProps({
  editingMenu: { type: Object, default: null },
})

const emit = defineEmits(["close", "saved"])

// ── State ─────────────────────────────────────────────────────────────────────
const form = ref({ name: "", description: "", category: "", price: "", image: null })
const loading         = ref(false)
const previewImage    = ref(null)
const fileInput       = ref(null)
const showCatDropdown = ref(false)
const showCropper     = ref(false)
const rawImageForCrop = ref(null)

const categories = [
  { id: 1, name: "Makanan" },
  { id: 2, name: "Minuman" },
  { id: 3, name: "Snacks"  },
]

// ── Helpers ───────────────────────────────────────────────────────────────────
const getCategoryLabel = () => {
  const cat = categories.find(c => c.id == form.value.category)
  return cat ? cat.name : "Pilih Kategori"
}

const normalizeCategory = (category) => {
  if (!category) return ""
  if (typeof category === "object") return category.id
  const byName = categories.find(c => c.name === category)
  return byName ? byName.id : category
}

// ── Reset ─────────────────────────────────────────────────────────────────────
const resetForm = () => {
  form.value = { name: "", description: "", category: "", price: "", image: null }
  cleanupPreview()
  if (fileInput.value) fileInput.value.value = ""
}

const cleanupPreview = () => {
  if (previewImage.value?.startsWith("blob:")) {
    URL.revokeObjectURL(previewImage.value)
  }
  previewImage.value = null
}

const cleanupRaw = () => {
  if (rawImageForCrop.value?.startsWith("blob:")) {
    URL.revokeObjectURL(rawImageForCrop.value)
  }
  rawImageForCrop.value = null
}

// ── Watch editingMenu → isi form ──────────────────────────────────────────────
watch(
  () => props.editingMenu,
  (menu) => {
    resetForm()
    if (!menu) return
    form.value = {
      name:        menu.name,
      description: menu.description || "",
      category:    normalizeCategory(menu.category),
      price:       menu.price,
      image:       null,
    }
    // Tampilkan foto existing dari Cloudinary (bukan blob)
    previewImage.value = menu.image_url || menu.image || null
  },
  { immediate: true }
)

// ── File picker & cropper ─────────────────────────────────────────────────────
const openFilePicker = () => fileInput.value?.click()

const onFileChange = (event) => {
  const file = event.target.files[0]
  if (!file) return
  // Reset input value agar onChange tetap terpanggil jika pilih file yang sama
  event.target.value = ""

  cleanupRaw()
  rawImageForCrop.value = URL.createObjectURL(file)
  showCropper.value     = true
}

const onCropComplete = (blob) => {
  // Cleanup blob lama
  cleanupPreview()
  cleanupRaw()

  previewImage.value = URL.createObjectURL(blob)
  form.value.image   = new File([blob], "menu-image.jpg", { type: "image/jpeg" })
  showCropper.value  = false
}

const onCropCancel = () => {
  cleanupRaw()
  showCropper.value = false
  // Foto preview tetap yang sebelumnya (tidak dihapus)
}

// ── Submit ────────────────────────────────────────────────────────────────────
const handleSubmit = async () => {
  if (!form.value.category) {
    toast.error("Pilih kategori terlebih dahulu")
    return
  }

  loading.value = true
  const payload = new FormData()
  payload.append("name",        form.value.name)
  payload.append("price",       Number(form.value.price))
  payload.append("category",    Number(form.value.category))
  payload.append("description", form.value.description || "")

  if (form.value.image) {
    payload.append("image", form.value.image)
  }

  try {
    const url    = props.editingMenu ? `/menus/${props.editingMenu.id}/` : "/menus/"
    const method = props.editingMenu ? "patch" : "post"
    await apiClient[method](url, payload, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    toast.success(props.editingMenu ? "Menu berhasil diperbarui!" : "Menu berhasil ditambahkan!")
    emit("saved")
    emit("close")
  } catch (err) {
    console.error("Gagal simpan:", err.response?.data)
    toast.error("Gagal menyimpan menu. Coba lagi.")
  } finally {
    loading.value = false
  }
}

// ── Keyboard escape ───────────────────────────────────────────────────────────
const handleEscape = (e) => { if (e.key === "Escape") emit("close") }

onMounted(() => document.addEventListener("keydown", handleEscape))

onBeforeUnmount(() => {
  document.removeEventListener("keydown", handleEscape)
  cleanupPreview()
  cleanupRaw()
})
</script>

<style scoped>
.no-spinner::-webkit-outer-spin-button,
.no-spinner::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
.no-spinner { -moz-appearance: textfield; }

.custom-scroll::-webkit-scrollbar { width: 4px; }
.custom-scroll::-webkit-scrollbar-track { background: transparent; }
.custom-scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }
</style>