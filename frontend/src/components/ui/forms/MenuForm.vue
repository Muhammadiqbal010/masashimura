<template>
  <AdminModal v-model="isOpen" :title="editingMenu ? 'Edit Menu' : 'Tambah Menu Baru'" size="lg" :persistent="loading || showCropper">
    <form id="menu-form" class="mf-form" @submit.prevent="handleSubmit">
      <p class="adm-hint">Lengkapi data menu di bawah ini.</p>

      <div class="adm-field">
        <label class="adm-label" for="mf-name">Nama Menu <span class="adm-req">*</span></label>
        <input id="mf-name" v-model="form.name" data-autofocus type="text" required placeholder="Contoh: Mie Jebew Spesial" class="adm-input" />
      </div>

      <div class="adm-field">
        <label class="adm-label" for="mf-desc">Deskripsi <span class="adm-opt">(opsional)</span></label>
        <textarea id="mf-desc" v-model="form.description" rows="3" placeholder="Jelaskan menu ini..." class="adm-input"></textarea>
      </div>

      <div class="adm-grid-2">
        <div class="adm-field">
          <label class="adm-label" for="mf-cat">Kategori <span class="adm-req">*</span></label>
          <select id="mf-cat" v-model="form.category" class="adm-input">
            <option value="" disabled>Pilih Kategori</option>
            <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
          </select>
        </div>

        <div class="adm-field">
          <label class="adm-label" for="mf-price">Harga (Rp) <span class="adm-req">*</span></label>
          <input id="mf-price" v-model="form.price" type="number" required min="0" placeholder="25000" class="adm-input" />
        </div>
      </div>

      <div class="adm-field">
        <span class="adm-label">Foto Menu</span>

        <input ref="fileInput" type="file" accept="image/*" class="adm-sr" tabindex="-1" @change="onFileChange" />

        <button v-if="previewImage" type="button" class="mf-preview" title="Klik untuk ganti atau crop ulang foto" @click="openFilePicker">
          <img :src="previewImage" alt="Pratinjau foto menu" />
          <span class="mf-preview-hint"><Pencil :size="18" /> Klik untuk ganti foto</span>
        </button>

        <button v-else type="button" class="mf-drop" @click="openFilePicker">
          <Camera :size="24" />
          <span class="mf-drop-title">Unggah Foto Menu</span>
          <span class="adm-hint">Klik untuk pilih gambar · Akan dicrop otomatis</span>
        </button>

        <button v-if="previewImage" type="button" class="adm-btn adm-btn--ghost adm-btn--sm" @click="openFilePicker">Ganti Foto</button>
      </div>
    </form>

    <template #footer>
      <button type="button" class="adm-btn adm-btn--ghost" :disabled="loading" @click="emit('close')">Batal</button>
      <button type="submit" form="menu-form" class="adm-btn adm-btn--primary" :disabled="loading">
        <span v-if="loading" class="adm-spinner"></span>
        {{ loading ? "Menyimpan..." : editingMenu ? "Simpan Perubahan" : "Tambah Menu" }}
      </button>
    </template>
  </AdminModal>

  <!-- ImageCropper di luar modal agar z-index tidak konflik (ter-teleport ke body) -->
  <ImageCropper
    v-if="showCropper"
    :image="rawImageForCrop"
    type="menu"
    @crop-complete="onCropComplete"
    @cancel="onCropCancel"
  />
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from "vue"
import { toast } from "vue-sonner"
import apiClient from "@/api/client"
import { Camera, Pencil } from "lucide-vue-next"
import AdminModal from "@/components/ui/admin/Adminmodal.vue"
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
const showCropper     = ref(false)
const rawImageForCrop = ref(null)

const categories = [
  { id: 1, name: "Makanan" },
  { id: 2, name: "Minuman" },
  { id: 3, name: "Snacks"  },
]

// ── Helpers ───────────────────────────────────────────────────────────────────
// AdminModal memakai v-model; komponen ini tampil selama ter-mount dan menutup lewat emit("close").
const isOpen = computed({
  get: () => true,
  set: (v) => { if (!v) emit("close") },
})

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

onBeforeUnmount(() => {
  cleanupPreview()
  cleanupRaw()
})
</script>

<style scoped>
.mf-form { display: flex; flex-direction: column; gap: 1rem; }

.mf-preview {
  position: relative; display: block; width: 100%; padding: 0; overflow: hidden; cursor: pointer;
  border: 1px solid var(--border-strong); border-radius: var(--r-md); background: var(--surface-2);
}
.mf-preview img { display: block; width: 100%; height: 14rem; object-fit: cover; transition: opacity 0.15s; }
.mf-preview-hint {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; gap: 0.5rem;
  background: var(--overlay); color: var(--text); font-size: 0.8125rem; font-weight: 600;
  opacity: 0; transition: opacity 0.15s;
}
.mf-preview:hover .mf-preview-hint, .mf-preview:focus-visible .mf-preview-hint { opacity: 1; }

.mf-drop {
  display: flex; flex-direction: column; align-items: center; gap: 0.35rem; width: 100%;
  padding: 2rem 1rem; cursor: pointer; color: var(--text-dim);
  border: 1px dashed var(--border-strong); border-radius: var(--r-md); background: transparent;
  transition: border-color 0.15s, color 0.15s, background 0.15s;
}
.mf-drop:hover { border-color: var(--accent); color: var(--text); background: var(--surface-hover); }
.mf-drop-title { font-size: 0.875rem; font-weight: 600; }
</style>
