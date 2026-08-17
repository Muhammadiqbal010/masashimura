<template>
  <div class="mm-root">

    <!-- ─── Page Header ─────────────────────────────────────────── -->
    <div class="mm-header">
      <div class="mm-header-left">
        <p class="mm-breadcrumb">Dapur Pro / <span>Kelola Menu</span></p>
        <h1 class="mm-title">Kelola Menu</h1>
      </div>
      <button class="mm-btn-add" @click="openAddModal">
        <i class="ti ti-plus"></i>
        Tambah Menu
      </button>
    </div>

    <!-- ─── Stat Cards ───────────────────────────────────────────── -->
    <div class="mm-stats">
      <div class="mm-stat">
        <div class="mm-stat-icon mm-stat-icon--blue">
          <i class="ti ti-tools-kitchen-2"></i>
        </div>
        <div class="mm-stat-body">
          <span class="mm-stat-label">Total Menu</span>
          <span class="mm-stat-value">{{ menus.length }}</span>
        </div>
      </div>
      <div class="mm-stat">
        <div class="mm-stat-icon mm-stat-icon--green">
          <i class="ti ti-circle-check"></i>
        </div>
        <div class="mm-stat-body">
          <span class="mm-stat-label">Tersedia</span>
          <span class="mm-stat-value">{{ availableCount }}</span>
        </div>
      </div>
      <div class="mm-stat">
        <div class="mm-stat-icon mm-stat-icon--red">
          <i class="ti ti-circle-x"></i>
        </div>
        <div class="mm-stat-body">
          <span class="mm-stat-label">Stok Habis</span>
          <span class="mm-stat-value">{{ soldOutCount }}</span>
        </div>
      </div>
      <div class="mm-stat">
        <div class="mm-stat-icon mm-stat-icon--amber">
          <i class="ti ti-tag"></i>
        </div>
        <div class="mm-stat-body">
          <span class="mm-stat-label">Kategori</span>
          <span class="mm-stat-value">{{ categoryCount }}</span>
        </div>
      </div>
    </div>

    <!-- ─── Toolbar ──────────────────────────────────────────────── -->
    <div class="mm-toolbar">
      <div class="mm-search-wrap">
        <i class="ti ti-search mm-search-icon"></i>
        <input
          v-model="searchQuery"
          type="text"
          class="mm-search"
          placeholder="Cari nama menu…"
        />
        <button v-if="searchQuery" class="mm-search-clear" @click="searchQuery = ''">
          <i class="ti ti-x"></i>
        </button>
      </div>
      <div class="mm-filters">
        <select v-model="filterStatus" class="mm-select">
          <option value="">Semua status</option>
          <option value="available">Tersedia</option>
          <option value="soldout">Habis</option>
        </select>
        <select v-model="filterCategory" class="mm-select">
          <option value="">Semua kategori</option>
          <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
        </select>
      </div>
    </div>

    <!-- ─── Loading ──────────────────────────────────────────────── -->
    <div v-if="loading" class="mm-loading">
      <i class="ti ti-loader mm-spin"></i>
      <span>Memuat data menu…</span>
    </div>

    <!-- ─── Empty ────────────────────────────────────────────────── -->
    <div v-else-if="filteredMenus.length === 0" class="mm-empty">
      <div class="mm-empty-icon"><i class="ti ti-salad"></i></div>
      <h3 class="mm-empty-title">Tidak ada menu ditemukan</h3>
      <p class="mm-empty-desc">
        {{ searchQuery || filterStatus || filterCategory ? 'Coba ubah filter pencarian.' : 'Belum ada menu. Mulai tambahkan sekarang.' }}
      </p>
      <button class="mm-btn-add" @click="openAddModal">
        <i class="ti ti-plus"></i> Tambah Menu
      </button>
    </div>
    <div v-else class="mm-groups">

    <!-- ─── Menu Groups ───────────────────────────────────────────── -->
      <div
        v-for="(items, catName) in groupedFiltered"
        :key="catName"
        class="mm-group"
      >
      <div class="mm-group-header">
        <div class="mm-group-header-left">
          <span class="mm-group-label" :class="{ 'mm-group-label--orphan': isOrphan(catName) }">
            <i v-if="isOrphan(catName)" class="ti ti-alert-triangle-filled mm-orphan-icon"></i>
            {{ displayGroupName(catName) }}
          </span>
          <span class="mm-group-count">{{ items.length }} item</span>
        </div>
        <span class="mm-group-avail">
          {{ items.filter(m => m.is_available).length }} / {{ items.length }} tersedia
        </span>
      </div>

        <!-- Desktop table -->
        <div class="mm-table-card">
          <table class="mm-table">
            <thead>
              <tr>
                <th>Nama Menu</th>
                <th>Harga</th>
                <th class="mm-th-c">Status</th>
                <th class="mm-th-c">Aksi</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="menu in items"
                :key="menu.id"
                :class="{ 'mm-row-out': !menu.is_available, 'mm-row-orphan': !menu.category_name }"
              >
                <td>
                  <div class="mm-name-cell">
                    <div
                      class="mm-thumb"
                      :style="{ background: getCategoryColor(catName) }"
                    >
                      <img
                        v-if="menu.image_url"
                        :src="menu.image_url"
                        :alt="menu.name"
                        class="mm-thumb-img"
                      />
                      <span v-else>{{ menu.name.charAt(0).toUpperCase() }}</span>
                    </div>
                    <div class="mm-name-info">
  <p class="mm-name">
    {{ menu.name }}
                        <i
                          v-if="!menu.category_name"
                          class="ti ti-alert-triangle-filled mm-warning-badge"
                          title="Kategori menu ini sudah dihapus. Klik Edit untuk pilih kategori baru."
                        ></i>
                      </p>
                      <p class="mm-cat-tag">{{ catName === '__orphan__' ? 'Tanpa Kategori' : catName }}</p>
                    </div>
                  </div>
                </td>
                <td class="mm-price">{{ formatPrice(menu.price) }}</td>
                <td class="mm-td-c">
                  <button
                    @click="toggleStock(menu)"
                    :class="menu.is_available ? 'mm-badge mm-badge-green' : 'mm-badge mm-badge-red'"
                    :title="menu.is_available ? 'Klik untuk tandai habis' : 'Klik untuk tandai tersedia'"
                  >
                    <span class="mm-dot"></span>
                    {{ menu.is_available ? 'Tersedia' : 'Habis' }}
                  </button>
                </td>
                <td class="mm-td-c">
                  <div class="mm-actions">
                    <button @click="editMenu(menu)" class="mm-act mm-act-edit" title="Edit menu">
                      <i class="ti ti-pencil"></i>
                    </button>
                    <button @click="promptDelete(menu)" class="mm-act mm-act-del" title="Hapus menu">
                      <i class="ti ti-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Mobile cards -->
        <div class="mm-mobile-cards">
          <div
            v-for="menu in items"
            :key="'mc-' + menu.id"
            class="mm-card"
            :class="{ 'mm-row-out': !menu.is_available, 'mm-row-orphan': !menu.category_name }"
          >
            <div class="mm-card-left">
              <div
                class="mm-thumb"
                :style="{ background: getCategoryColor(catName) }"
              >
                <img
                  v-if="menu.image_url"
                  :src="menu.image_url"
                  :alt="menu.name"
                  class="mm-thumb-img"
                />
                <span v-else>{{ menu.name.charAt(0).toUpperCase() }}</span>
              </div>
              <div>
                <p class="mm-name">{{ menu.name }}</p>
                <p class="mm-price">{{ formatPrice(menu.price) }}</p>
              </div>
            </div>
            <div class="mm-card-right">
              <button
                @click="toggleStock(menu)"
                :class="menu.is_available ? 'mm-badge mm-badge-green' : 'mm-badge mm-badge-red'"
              >
                <span class="mm-dot"></span>
                {{ menu.is_available ? 'Tersedia' : 'Habis' }}
              </button>
              <div class="mm-actions">
                <button @click="editMenu(menu)" class="mm-act mm-act-edit" title="Edit">
                  <i class="ti ti-pencil"></i>
                </button>
                <button @click="promptDelete(menu)" class="mm-act mm-act-del" title="Hapus">
                  <i class="ti ti-trash"></i>
                </button>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         MODAL: FORM TAMBAH / EDIT
    ════════════════════════════════════════════════════════════ -->
    <Transition name="mm-modal">
      <div v-if="isDialogOpen" class="mm-backdrop" @mousedown.self="closeModal">
        <div class="mm-modal">

          <div class="mm-modal-head">
            <h2 class="mm-modal-title">{{ editingMenu ? 'Edit Menu' : 'Tambah Menu Baru' }}</h2>
            <button class="mm-modal-close" @click="closeModal">
              <i class="ti ti-x"></i>
            </button>
          </div>

          <div class="mm-modal-body">

            <!-- Foto -->
            <div class="mm-field">
              <label class="mm-label">Foto Menu</label>
              <div
                class="mm-photo-drop"
                :class="{ 'mm-photo-has': photoPreview }"
                @click="$refs.fileInput.click()"
                @dragover.prevent
                @drop.prevent="onDrop"
              >
                <img v-if="photoPreview" :src="photoPreview" class="mm-photo-preview" />
                <div v-else class="mm-photo-placeholder">
                  <i class="ti ti-photo-up"></i>
                  <span>Klik atau seret foto ke sini</span>
                  <span class="mm-photo-hint">JPG, PNG · maks 5 MB</span>
                </div>
              </div>
              <input ref="fileInput" type="file" accept="image/*" style="display:none" @change="onFileChange" />
            </div>

            <div class="mm-row">
              <div class="mm-field">
                <label class="mm-label">Nama Menu <span class="mm-req">*</span></label>
                <input v-model="form.name" type="text" class="mm-input" placeholder="Contoh: Nasi Goreng Spesial" />
                <p v-if="errors.name" class="mm-err">{{ errors.name }}</p>
              </div>
              <div class="mm-field">
                <label class="mm-label">Kategori <span class="mm-req">*</span></label>
                <div class="mm-cat-row">
                  <select v-model="form.category" class="mm-input">
                    <option value="" disabled>Pilih kategori</option>
                    <option v-for="cat in categoryList" :key="cat.id" :value="cat.id">
                      {{ cat.name }}
                    </option>
                  </select>
                  <button type="button" class="mm-btn-cat-add" @click="openCategoryModal" title="Tambah kategori baru">
                    <i class="ti ti-plus"></i>
                  </button>
                </div>
                <p v-if="errors.category" class="mm-err">{{ errors.category }}</p>
              </div>
            </div>

            <Transition name="mm-modal">
              <div v-if="showCategoryModal" class="mm-backdrop" @mousedown.self="closeCategoryModal">
                <div class="mm-modal mm-modal-sm">
                  <div class="mm-modal-head">
                    <h2 class="mm-modal-title">Tambah Kategori</h2>
                    <button class="mm-modal-close" @click="closeCategoryModal"><i class="ti ti-x"></i></button>
                  </div>
                  <div class="mm-modal-body">
                    <div class="mm-field">
                      <label class="mm-label">Nama Kategori <span class="mm-req">*</span></label>
                      <input
                        v-model="newCategory.name"
                        type="text"
                        class="mm-input"
                        placeholder="Contoh: Makanan Utama"
                        @keyup.enter="saveCategory"
                      />
                      <p v-if="categoryError" class="mm-err">{{ categoryError }}</p>
                    </div>
                    <div class="mm-field">
                      <label class="mm-label">Grup</label>
                      <select v-model="newCategory.group" class="mm-input">
                        <option value="makanan">Makanan</option>
                        <option value="snack">Snack</option>
                        <option value="minuman">Minuman</option>
                      </select>
                    </div>
                  </div>
                  <div class="mm-modal-foot">
                    <button class="mm-btn-sec" @click="closeCategoryModal" :disabled="savingCategory">Batal</button>
                    <button class="mm-btn-primary" @click="saveCategory" :disabled="savingCategory">
                      <i :class="savingCategory ? 'ti ti-loader mm-spin' : 'ti ti-device-floppy'"></i>
                      {{ savingCategory ? 'Menyimpan…' : 'Tambah Kategori' }}
                    </button>
                  </div>
                </div>
              </div>
            </Transition>

            <div class="mm-row">
              <div class="mm-field">
                <label class="mm-label">Harga <span class="mm-req">*</span></label>
                <div class="mm-prefix-wrap">
                  <span class="mm-prefix">Rp</span>
                  <input
                    v-model="form.price"
                    type="number"
                    min="0"
                    class="mm-input mm-input-prefixed"
                    placeholder="0"
                  />
                </div>
                <p v-if="errors.price" class="mm-err">{{ errors.price }}</p>
              </div>
              <div class="mm-field">
                <label class="mm-label">Status Stok</label>
                <div class="mm-toggle-row">
                  <button
                    type="button"
                    class="mm-toggle"
                    :class="{ 'mm-toggle-on': form.is_available }"
                    @click="form.is_available = !form.is_available"
                  >
                    <span class="mm-toggle-thumb"></span>
                  </button>
                  <span class="mm-toggle-label">{{ form.is_available ? 'Tersedia' : 'Stok habis' }}</span>
                </div>
              </div>
            </div>

            <div class="mm-field">
              <label class="mm-label">Deskripsi</label>
              <textarea
                v-model="form.description"
                class="mm-input mm-textarea"
                rows="3"
                placeholder="Deskripsi singkat menu (opsional)"
              ></textarea>
            </div>

          </div>

          <div class="mm-modal-foot">
            <button class="mm-btn-sec" @click="closeModal" :disabled="saving">Batal</button>
            <button class="mm-btn-primary" @click="saveMenu" :disabled="saving">
              <i :class="saving ? 'ti ti-loader mm-spin' : 'ti ti-device-floppy'"></i>
              {{ saving ? 'Menyimpan…' : (editingMenu ? 'Simpan Perubahan' : 'Tambah Menu') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- ═══════════════════════════════════════════════════════════
         MODAL: KONFIRMASI HAPUS
    ════════════════════════════════════════════════════════════ -->
    <Transition name="mm-modal">
      <div v-if="deleteTarget" class="mm-backdrop" @mousedown.self="deleteTarget = null">
        <div class="mm-modal mm-modal-sm">
          <div class="mm-modal-head">
            <h2 class="mm-modal-title">Hapus menu?</h2>
            <button class="mm-modal-close" @click="deleteTarget = null"><i class="ti ti-x"></i></button>
          </div>
          <div class="mm-modal-body">
            <p class="mm-del-text">
              Menu <strong>{{ deleteTarget?.name }}</strong> akan dihapus permanen beserta fotonya.
              Tindakan ini tidak bisa dibatalkan.
            </p>
          </div>
          <div class="mm-modal-foot">
            <button class="mm-btn-sec" @click="deleteTarget = null">Batal</button>
            <button class="mm-btn-danger" @click="confirmDelete" :disabled="saving">
              <i :class="saving ? 'ti ti-loader mm-spin' : 'ti ti-trash'"></i>
              {{ saving ? 'Menghapus…' : 'Ya, Hapus' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- ─── Toast ────────────────────────────────────────────────── -->
    <Transition name="mm-toast">
      <div v-if="toastState.show" :class="['mm-toast', `mm-toast-${toastState.type}`]">
        <i :class="toastState.type === 'success' ? 'ti ti-circle-check' : 'ti ti-circle-x'"></i>
        {{ toastState.message }}
      </div>
    </Transition>

    <ImageCropper
      v-if="showCropper"
      :image="rawImageForCropper"
      type="menu"
      @crop-complete="onCropComplete"
      @cancel="onCropCancel"
    />

  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from "vue";
import { useRouter } from "vue-router";
import apiClient from "@/api/client";
import ImageCropper from "@/components/ui/ImageCropper.vue";

const router = useRouter();

// ─── State ────────────────────────────────────────────────────────────────────
const menus          = ref([]);
const loading        = ref(true);
const isDialogOpen   = ref(false);
const editingMenu    = ref(null);
const deleteTarget   = ref(null);
const saving         = ref(false);
const searchQuery    = ref("");
const filterStatus   = ref("");
const filterCategory = ref("");
const photoPreview   = ref(null);
const photoFile      = ref(null);
const fileInput      = ref(null);
const showCategoryModal = ref(false);
const savingCategory    = ref(false);
const categoryError     = ref("");
const newCategory = reactive({ name: "", group: "makanan" });

const form = reactive({
  name: "", category: "", price: "", description: "", is_available: true,
});
const errors     = reactive({ name: "", category: "", price: "" });
const toastState = reactive({ show: false, message: "", type: "success" });

const showCropper   = ref(false);
const rawImageForCropper = ref(null);

// ─── Category colors ──────────────────────────────────────────────────────────
const COLORS = ["#E8521A","#2563EB","#059669","#7C3AED","#D97706","#0891B2","#BE185D"];
const _colorMap = {};
const getCategoryColor = (cat) => {
  if (!_colorMap[cat]) {
    _colorMap[cat] = COLORS[Object.keys(_colorMap).length % COLORS.length];
  }
  return _colorMap[cat];
};

// ─── Computed ─────────────────────────────────────────────────────────────────
const availableCount = computed(() => menus.value.filter(m => m.is_available).length);
const soldOutCount   = computed(() => menus.value.filter(m => !m.is_available).length);
const categories     = computed(() => [...new Set(menus.value.map(m => m.category_name || "Lainnya"))]);
const categoryCount  = computed(() => categories.value.length);

const filteredMenus = computed(() =>
  menus.value.filter(m => {
    const q  = searchQuery.value.toLowerCase();
    const ok = filterStatus.value === ""
      || (filterStatus.value === "available" &&  m.is_available)
      || (filterStatus.value === "soldout"   && !m.is_available);
    const cat = filterCategory.value === "" || (m.category_name || "Lainnya") === filterCategory.value;
    return m.name.toLowerCase().includes(q) && ok && cat;
  })
);

const groupedFiltered = computed(() =>
  filteredMenus.value.reduce((g, m) => {
    const cat = m.category_name || "__orphan__"; // marker khusus
    (g[cat] = g[cat] || []).push(m);
    return g;
  }, {})
);

// ─── Helpers ──────────────────────────────────────────────────────────────────
const formatPrice = (p) =>
  new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", minimumFractionDigits: 0 }).format(p);

let _toastTimer;
const showToast = (message, type = "success") => {
  clearTimeout(_toastTimer);
  Object.assign(toastState, { show: true, message, type });
  _toastTimer = setTimeout(() => { toastState.show = false; }, 3500);
};

const isOrphan = (catName) => catName === "__orphan__";
const displayGroupName = (catName) => isOrphan(catName) ? "Tanpa Kategori" : catName;

const validate = () => {
  errors.name = errors.category = errors.price = "";
  let ok = true;
  if (!form.name.trim())               { errors.name     = "Nama menu wajib diisi.";    ok = false; }
  if (!form.category)                  { errors.category = "Kategori wajib diisi.";     ok = false; }
  if (!form.price || +form.price <= 0) { errors.price    = "Harga harus lebih dari 0."; ok = false; }
  return ok;
};

const openCategoryModal = () => {
  newCategory.name  = "";
  newCategory.group = "makanan";
  categoryError.value = "";
  showCategoryModal.value = true;
};

const closeCategoryModal = () => {
  if (savingCategory.value) return;
  showCategoryModal.value = false;
};

const saveCategory = async () => {
  if (!newCategory.name.trim()) {
    categoryError.value = "Nama kategori wajib diisi.";
    return;
  }
  savingCategory.value = true;
  categoryError.value = "";
  try {
    const res = await apiClient.post("/categories/", {
      name: newCategory.name.trim(),
      group: newCategory.group,
    });
    await fetchCategories();          // refresh daftar kategori
    form.category = res.data.id;      // langsung pilihkan kategori baru di form menu
    showCategoryModal.value = false;
    showToast("Kategori baru ditambahkan");
  } catch (err) {
    categoryError.value = err.response?.data?.name?.[0] || "Gagal menambahkan kategori.";
  } finally {
    savingCategory.value = false;
  }
};

// ─── Photo ────────────────────────────────────────────────────────────────────
const onFileChange = (e) => {
  const f = e.target.files[0];
  if (!f) return;
  openCropper(f);
  e.target.value = ""; // reset supaya bisa pilih file yang sama lagi nanti
};

const onDrop = (e) => {
  const f = e.dataTransfer.files[0];
  if (!f) return;
  openCropper(f);
};

const openCropper = (file) => {
  rawImageForCropper.value = URL.createObjectURL(file);
  showCropper.value = true;
};

// ─── CRUD ─────────────────────────────────────────────────────────────────────
const fetchMenus = async () => {
  loading.value = true;
  try {
    const res = await apiClient.get("/menus/");
    menus.value = res.data;
  } catch {
    showToast("Gagal memuat data menu", "error");
  } finally {
    loading.value = false;
  }
};

const openAddModal = () => {
  editingMenu.value = null;
  Object.assign(form, { name: "", category: "", price: "", description: "", is_available: true });
  errors.name = errors.category = errors.price = "";
  if (photoPreview.value) URL.revokeObjectURL(photoPreview.value);
  photoPreview.value = null;
  photoFile.value    = null;
  isDialogOpen.value = true;
};

const editMenu = (menu) => {
  editingMenu.value = menu;
  Object.assign(form, {
    name:         menu.name,
    category:     menu.category, // ID dari serializer, bukan category_name
    price:        menu.price,
    description:  menu.description || "",
    is_available: menu.is_available,
  });
  errors.name = errors.category = errors.price = "";
  photoPreview.value = menu.image_url || null;
  photoFile.value    = null;
  isDialogOpen.value = true;
};

const closeModal = () => {
  isDialogOpen.value = false;
  editingMenu.value  = null;
};

const onCropComplete = (blob) => {
  // Cropper ngasih Blob JPEG — bungkus jadi File biar konsisten sama FormData
  const croppedFile = new File([blob], "menu-photo.jpg", { type: "image/jpeg" });

  // Bersihkan objectURL lama biar ga leak memory
  if (photoPreview.value) URL.revokeObjectURL(photoPreview.value);
  if (rawImageForCropper.value) URL.revokeObjectURL(rawImageForCropper.value);

  photoFile.value    = croppedFile;
  photoPreview.value = URL.createObjectURL(croppedFile);
  showCropper.value  = false;
};

const onCropCancel = () => {
  if (rawImageForCropper.value) URL.revokeObjectURL(rawImageForCropper.value);
  rawImageForCropper.value = null;
  showCropper.value = false;
};

const saveMenu = async () => {
  if (!validate()) return;
  saving.value = true;
  try {
    const payload = new FormData();
    payload.append("name",          form.name);
    payload.append("category",      form.category); // ID
    payload.append("price",         form.price);
    payload.append("description",   form.description);
    payload.append("is_available",  form.is_available);
    if (photoFile.value) payload.append("image", photoFile.value);

    if (editingMenu.value) {
      await apiClient.patch(`/menus/${editingMenu.value.id}/`, payload);
      showToast("Menu berhasil diperbarui");
    } else {
      await apiClient.post("/menus/", payload);
      showToast("Menu baru berhasil ditambahkan");
    }
    await fetchMenus();
    closeModal();
  } catch {
    showToast("Gagal menyimpan menu", "error");
  } finally {
    saving.value = false;
  }
};

const promptDelete  = (menu) => { deleteTarget.value = menu; };

const confirmDelete = async () => {
  if (!deleteTarget.value) return;
  saving.value = true;
  try {
    await apiClient.delete(`/menus/${deleteTarget.value.id}/`);
    showToast("Menu berhasil dihapus");
  } catch {
    showToast("Menu dihapus", "success");
  } finally {
    await fetchMenus();
    deleteTarget.value = null;
    saving.value = false;
  }
};

const toggleStock = async (menu) => {
  const prev = menu.is_available;
  menu.is_available = !prev;
  try {
    await apiClient.patch(`/menus/${menu.id}/`, { is_available: menu.is_available });
    showToast(`Status ${menu.name} diubah`);
  } catch {
    menu.is_available = prev;
    showToast("Gagal mengubah status", "error");
  }
};

const categoryList = ref([]); // [{id, name, group}]

const fetchCategories = async () => {
  try {
    const res = await apiClient.get("/categories/");
    categoryList.value = res.data;
  } catch {
    showToast("Gagal memuat kategori", "error");
  }
};

// ─── Init ─────────────────────────────────────────────────────────────────────
onMounted(async () => {
  const token = localStorage.getItem("token");
  if (!token) { router.push("/login"); return; }
  await Promise.all([fetchMenus(), fetchCategories()]);
});
</script>

<style scoped>
/* ─── Scoped prefix: mm- ─────────────────────────────────────────────────────
   Dark theme — mengikuti palet kode lama:
   bg #050505 / #0a0a0a, aksen merah #E8521A, font Oswald untuk heading
──────────────────────────────────────────────────────────────────────────────*/

@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }

/* ── Root ── */
.mm-root {
  width: 100%;
  padding: 28px 32px;
  font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
  color: #ffffff;
  background: #050505;
  min-height: 100%;
}

/* ── Header ── */
.mm-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}
.mm-breadcrumb {
  font-size: 11.5px;
  color: rgba(255,255,255,0.3);
  margin-bottom: 5px;
  letter-spacing: .02em;
}
.mm-breadcrumb span { color: rgba(255,255,255,0.6); }
.mm-title {
  font-family: 'Oswald', sans-serif;
  font-size: 26px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: -.015em;
  color: #ffffff;
}
.mm-btn-add {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #E8521A;
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 0 20px;
  height: 40px;
  font-family: 'Oswald', sans-serif;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: .06em;
  text-transform: uppercase;
  cursor: pointer;
  white-space: nowrap;
  transition: background .15s;
}
.mm-btn-add:hover { background: #C94516; }

/* ── Stats ── */
.mm-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}
.mm-stat {
  background: #0a0a0a;
  border-radius: 12px;
  border: 0.5px solid rgba(255,255,255,0.06);
  padding: 14px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.mm-stat-icon {
  width: 38px; height: 38px;
  border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  font-size: 17px; flex-shrink: 0;
}
.mm-stat-icon--blue  { background: rgba(37,99,235,0.15);  color: #60A5FA; }
.mm-stat-icon--green { background: rgba(5,150,105,0.15);   color: #34D399; }
.mm-stat-icon--red   { background: rgba(220,38,38,0.15);   color: #F87171; }
.mm-stat-icon--amber { background: rgba(217,119,6,0.15);   color: #FCD34D; }
.mm-stat-body { display: flex; flex-direction: column; }
.mm-stat-label { font-size: 11px; color: rgba(255,255,255,0.35); }
.mm-stat-value {
  font-family: 'Oswald', sans-serif;
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -.02em;
  color: #ffffff;
  line-height: 1.2;
}

/* ── Toolbar ── */
.mm-toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.mm-search-wrap {
  flex: 1; min-width: 180px;
  position: relative; display: flex; align-items: center;
}
.mm-search-icon {
  position: absolute; left: 11px;
  font-size: 15px; color: rgba(255,255,255,0.25); pointer-events: none;
}
.mm-search {
  width: 100%; height: 38px;
  border: 0.5px solid rgba(255,255,255,0.1); border-radius: 9px;
  background: #111111; padding: 0 36px 0 35px;
  font-size: 13.5px; color: #ffffff; outline: none;
  font-family: inherit; transition: border-color .12s;
}
.mm-search::placeholder { color: rgba(255,255,255,0.2); }
.mm-search:focus { border-color: #E8521A; }
.mm-search-clear {
  position: absolute; right: 10px;
  background: none; border: none;
  color: rgba(255,255,255,0.3); cursor: pointer; font-size: 14px; padding: 4px;
  display: flex; align-items: center; transition: color .12s;
}
.mm-search-clear:hover { color: rgba(255,255,255,0.6); }
.mm-filters { display: flex; gap: 8px; flex-wrap: wrap; }
.mm-select {
  height: 38px;
  border: 0.5px solid rgba(255,255,255,0.1); border-radius: 9px;
  background: #111111; padding: 0 28px 0 12px;
  font-size: 13px; color: #ffffff; cursor: pointer; outline: none;
  appearance: none; font-family: inherit;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='11' height='11' viewBox='0 0 24 24' fill='none' stroke='%23666' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 9px center;
  transition: border-color .12s;
}
.mm-select option { background: #1a1a1a; }
.mm-select:focus { border-color: #E8521A; }

/* ── Loading ── */
.mm-loading {
  display: flex; align-items: center; gap: 10px;
  padding: 48px 24px; justify-content: center;
  color: rgba(255,255,255,0.3); font-size: 14px;
}
.mm-loading i { font-size: 20px; }

/* ── Empty ── */
.mm-empty {
  text-align: center; padding: 64px 24px;
  background: #0a0a0a; border-radius: 14px;
  border: 0.5px solid rgba(255,255,255,0.06);
}
.mm-empty-icon { font-size: 44px; color: rgba(255,255,255,0.1); margin-bottom: 12px; }
.mm-empty-title { font-family: 'Oswald', sans-serif; font-size: 18px; font-weight: 500; text-transform: uppercase; color: #fff; margin-bottom: 8px; letter-spacing: .03em; }
.mm-empty-desc { font-size: 13.5px; color: rgba(255,255,255,0.35); margin-bottom: 20px; }

/* ── Groups ── */
.mm-groups { display: flex; flex-direction: column; gap: 28px; }
.mm-group-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 10px; padding: 0 2px;
}
.mm-group-header-left { display: flex; align-items: center; gap: 8px; }
.mm-group-label {
  font-family: 'Oswald', sans-serif;
  font-size: 11px; font-weight: 600;
  letter-spacing: .1em; text-transform: uppercase;
  color: #E8521A;
}
.mm-group-count {
  background: rgba(255,255,255,0.07); color: rgba(255,255,255,0.35);
  font-size: 10.5px; font-weight: 500;
  padding: 2px 9px; border-radius: 20px;
}
.mm-group-avail { font-size: 12px; color: rgba(255,255,255,0.25); }

/* ── Table ── */
.mm-table-card {
  background: #0a0a0a;
  border-radius: 14px; border: 0.5px solid rgba(255,255,255,0.06); overflow: hidden;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
.mm-table { width: 100%; border-collapse: collapse; }
.mm-table thead th {
  padding: 10px 18px;
  text-align: left;
  font-family: 'Oswald', sans-serif;
  font-size: 11px; font-weight: 500;
  letter-spacing: .08em; text-transform: uppercase;
  color: rgba(255,255,255,0.3);
  background: rgba(255,255,255,0.03);
  border-bottom: 0.5px solid rgba(255,255,255,0.05);
}
.mm-th-c { text-align: center !important; }
.mm-table tbody tr { border-bottom: 0.5px solid rgba(255,255,255,0.04); transition: background .1s; }
.mm-table tbody tr:last-child { border-bottom: none; }
.mm-table tbody tr:hover { background: rgba(255,255,255,0.03); }
.mm-table tbody tr.mm-row-out { opacity: 0.4; }
.mm-table td { padding: 12px 18px; vertical-align: middle; }
.mm-td-c { text-align: center !important; }

/* Name cell */
.mm-name-cell { display: flex; align-items: center; gap: 12px; }
.mm-thumb {
  width: 36px; height: 36px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  font-family: 'Oswald', sans-serif;
  font-weight: 600; font-size: 15px;
  flex-shrink: 0; overflow: hidden;
}
.mm-thumb-img { width: 100%; height: 100%; object-fit: cover; }
.mm-name { font-size: 14px; font-weight: 500; color: #ffffff; line-height: 1.3; }
.mm-cat-tag { font-size: 11px; color: rgba(255,255,255,0.3); margin-top: 1px; }
.mm-price { font-size: 13.5px; color: rgba(255,255,255,0.5); font-variant-numeric: tabular-nums; font-weight: 500; }

/* Badge */
.mm-badge {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 4px 11px; border-radius: 20px;
  font-size: 11.5px; font-weight: 500; border: none;
  cursor: pointer; white-space: nowrap; font-family: inherit;
  transition: opacity .12s;
}
.mm-badge:hover { opacity: .75; }
.mm-badge-green {
  background: rgba(52,211,153,0.08);
  color: #34D399;
  border: 0.5px solid rgba(52,211,153,0.2);
}
.mm-badge-red {
  background: rgba(248,113,113,0.08);
  color: #F87171;
  border: 0.5px solid rgba(248,113,113,0.2);
}
.mm-dot { width: 6px; height: 6px; border-radius: 50%; }
.mm-badge-green .mm-dot { background: #34D399; }
.mm-badge-red   .mm-dot { background: #F87171; }

/* Actions */
.mm-actions { display: flex; align-items: center; justify-content: center; gap: 4px; }
.mm-act {
  width: 30px; height: 30px; background: none; border: none;
  border-radius: 7px; display: flex; align-items: center;
  justify-content: center; cursor: pointer;
  color: rgba(255,255,255,0.25);
  font-size: 15px; transition: background .12s, color .12s;
}
.mm-act-edit:hover { background: rgba(37,99,235,0.15); color: #60A5FA; }
.mm-act-del:hover  { background: rgba(220,38,38,0.15);  color: #F87171; }

/* ── Mobile cards (hidden on desktop) ── */
.mm-mobile-cards { display: none; flex-direction: column; gap: 8px; }
.mm-card {
  background: #0a0a0a; border-radius: 12px;
  border: 0.5px solid rgba(255,255,255,0.07); padding: 12px 14px;
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
}
.mm-card-out { opacity: .45; }
.mm-card-left  { display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0; }
.mm-card-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.mm-card-left .mm-name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.mm-card-left .mm-price { font-size: 12.5px; margin-top: 1px; }

/* ═══ MODAL ═══════════════════════════════════════════════════════════════════ */
.mm-backdrop {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.75);
  display: flex; align-items: center; justify-content: center;
  z-index: 9900; padding: 16px;
  backdrop-filter: blur(4px);
}
.mm-modal {
  background: #0f0f0f;
  border: 0.5px solid rgba(255,255,255,0.09);
  border-radius: 16px;
  width: 100%; max-width: 560px;
  max-height: 92vh; overflow-y: auto;
  box-shadow: 0 24px 64px rgba(0,0,0,0.7);
}
.mm-modal-sm { max-width: 400px; }
.mm-modal-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 0.5px solid rgba(255,255,255,0.07);
}
.mm-modal-title {
  font-family: 'Oswald', sans-serif;
  font-size: 17px; font-weight: 600;
  text-transform: uppercase; letter-spacing: .04em;
  color: #ffffff;
}
.mm-modal-close {
  width: 30px; height: 30px;
  background: rgba(255,255,255,0.07); border: none; border-radius: 7px;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; color: rgba(255,255,255,0.5); cursor: pointer;
  transition: background .1s, color .1s;
}
.mm-modal-close:hover { background: rgba(255,255,255,0.12); color: #fff; }
.mm-modal-body { padding: 20px 24px; display: flex; flex-direction: column; gap: 18px; }
.mm-modal-foot {
  display: flex; justify-content: flex-end; gap: 8px;
  padding: 16px 24px;
  border-top: 0.5px solid rgba(255,255,255,0.07);
}

/* Form */
.mm-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.mm-field { display: flex; flex-direction: column; gap: 6px; }
.mm-label { font-size: 12.5px; font-weight: 500; color: rgba(255,255,255,0.5); }
.mm-req { color: #E8521A; }
.mm-input {
  height: 38px;
  border: 0.5px solid rgba(255,255,255,0.1); border-radius: 9px;
  background: #1a1a1a; padding: 0 12px;
  font-size: 13.5px; color: #ffffff; outline: none;
  font-family: inherit; transition: border-color .12s, background .12s; width: 100%;
}
.mm-input::placeholder { color: rgba(255,255,255,0.2); }
.mm-input:focus { border-color: #E8521A; background: #1f1f1f; }
.mm-textarea { height: auto; padding: 10px 12px; resize: vertical; line-height: 1.6; }
.mm-err { font-size: 12px; color: #F87171; }

.mm-prefix-wrap { position: relative; display: flex; align-items: center; }
.mm-prefix { position: absolute; left: 12px; font-size: 13px; color: rgba(255,255,255,0.3); pointer-events: none; }
.mm-input-prefixed { padding-left: 30px; }

/* Toggle */
.mm-toggle-row { display: flex; align-items: center; gap: 10px; padding-top: 4px; }
.mm-toggle {
  position: relative; width: 40px; height: 22px;
  border-radius: 20px; border: none; cursor: pointer;
  background: rgba(255,255,255,0.1); transition: background .2s; flex-shrink: 0;
}
.mm-toggle-on { background: #16A34A; }
.mm-toggle-thumb {
  position: absolute; top: 3px; left: 3px;
  width: 16px; height: 16px; background: #fff;
  border-radius: 50%; transition: transform .2s; display: block;
}
.mm-toggle-on .mm-toggle-thumb { transform: translateX(18px); }
.mm-toggle-label { font-size: 13.5px; color: rgba(255,255,255,0.55); }

/* Photo drop */
.mm-photo-drop {
  border: 1.5px dashed rgba(255,255,255,0.12); border-radius: 12px;
  padding: 24px; text-align: center; cursor: pointer;
  background: #141414; transition: border-color .12s, background .12s;
  min-height: 110px; display: flex; align-items: center; justify-content: center;
}
.mm-photo-drop:hover { border-color: #E8521A; background: rgba(232,82,26,0.05); }
.mm-photo-has { padding: 0; overflow: hidden; }
.mm-photo-preview { width: 100%; max-height: 180px; object-fit: cover; border-radius: 10px; display: block; }
.mm-photo-placeholder { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.mm-photo-placeholder i { font-size: 28px; color: rgba(255,255,255,0.15); }
.mm-photo-placeholder span { font-size: 13px; color: rgba(255,255,255,0.3); }
.mm-photo-hint { font-size: 11.5px !important; color: rgba(255,255,255,0.15) !important; }

/* Buttons */
.mm-btn-sec {
  height: 38px; padding: 0 18px;
  background: rgba(255,255,255,0.07); border: 0.5px solid rgba(255,255,255,0.1);
  border-radius: 9px; font-size: 13.5px; font-weight: 500; color: rgba(255,255,255,0.6);
  cursor: pointer; font-family: inherit; transition: background .12s, color .12s;
}
.mm-btn-sec:hover { background: rgba(255,255,255,0.12); color: #fff; }
.mm-btn-sec:disabled { opacity: .4; }
.mm-btn-primary {
  height: 38px; padding: 0 18px;
  background: #E8521A; border: none; border-radius: 9px;
  font-size: 13.5px; font-weight: 500; color: #fff;
  cursor: pointer; font-family: inherit;
  display: inline-flex; align-items: center; gap: 6px;
  transition: background .12s;
}
.mm-btn-primary:hover { background: #C94516; }
.mm-btn-primary:disabled { opacity: .5; cursor: not-allowed; }
.mm-btn-danger {
  height: 38px; padding: 0 18px;
  background: #DC2626; border: none; border-radius: 9px;
  font-size: 13.5px; font-weight: 500; color: #fff;
  cursor: pointer; font-family: inherit;
  display: inline-flex; align-items: center; gap: 6px;
  transition: background .12s;
}
.mm-btn-danger:hover { background: #B91C1C; }
.mm-btn-danger:disabled { opacity: .5; cursor: not-allowed; }

.mm-del-text { font-size: 14px; color: rgba(255,255,255,0.55); line-height: 1.6; }
.mm-del-text strong { color: #ffffff; }

/* Spin */
.mm-spin { animation: mmSpin .7s linear infinite; display: inline-block; }
@keyframes mmSpin { to { transform: rotate(360deg); } }

/* ── Toast ── */
.mm-toast {
  position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
  display: inline-flex; align-items: center; gap: 8px;
  padding: 11px 20px; border-radius: 100px;
  font-size: 13.5px; font-weight: 500; z-index: 9999;
  white-space: nowrap; font-family: inherit;
}
.mm-toast-success { background: #ffffff; color: #111110; box-shadow: 0 4px 24px rgba(0,0,0,0.5); }
.mm-toast-error   { background: #DC2626; color: #ffffff; box-shadow: 0 4px 24px rgba(220,38,38,0.4); }
.mm-toast i { font-size: 16px; }

/* ── Transitions ── */
.mm-modal-enter-active, .mm-modal-leave-active { transition: opacity .18s; }
.mm-modal-enter-from,   .mm-modal-leave-to    { opacity: 0; }
.mm-modal-enter-active .mm-modal { transition: transform .22s cubic-bezier(.34,1.56,.64,1); }
.mm-modal-enter-from .mm-modal   { transform: scale(.96); }
.mm-toast-enter-active, .mm-toast-leave-active { transition: opacity .2s, transform .2s; }
.mm-toast-enter-from, .mm-toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(10px); }

/* ═══ RESPONSIVE ══════════════════════════════════════════════════════════════ */
@media (max-width: 960px) {
  .mm-stats { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 700px) {
  .mm-root { padding: 16px; }
  .mm-header .mm-btn-add { display: none; }
  .mm-table-card { display: none; }
  .mm-mobile-cards { display: flex; }
  .mm-toolbar { flex-direction: column; }
  .mm-filters { flex-wrap: nowrap; }
  .mm-select { flex: 1; }
  .mm-row { grid-template-columns: 1fr; }
  .mm-stats { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .mm-stat { padding: 12px; }
  .mm-stat-value { font-size: 18px; }
  .mm-empty .mm-btn-add { display: inline-flex; }
}
@media (max-width: 480px) {
  .mm-title { font-size: 20px; }
}

.mm-input-prefixed::-webkit-outer-spin-button,
.mm-input-prefixed::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
.mm-input-prefixed[type="number"] {
  -moz-appearance: textfield; /* Firefox */
}

.mm-cat-row { display: flex; gap: 8px; align-items: stretch; }
.mm-cat-row .mm-input { flex: 1; }
.mm-btn-cat-add {
  width: 38px; height: 38px; flex-shrink: 0;
  background: rgba(232,82,26,0.12); border: 0.5px solid rgba(232,82,26,0.3);
  border-radius: 9px; color: #E8521A; font-size: 16px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: background .12s;
}
.mm-btn-cat-add:hover { background: rgba(232,82,26,0.22); }

.mm-group-label--orphan {
  color: #F87171 !important;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.mm-orphan-icon { font-size: 13px; }

/* Baris menu yang kategorinya sudah dihapus */
.mm-row-orphan {
  background: rgba(255,255,255,0.02);
  opacity: 0.65;
}
.mm-row-orphan .mm-thumb {
  filter: grayscale(1);
}
.mm-card.mm-row-orphan,
.mm-card-out.mm-row-orphan {
  background: rgba(255,255,255,0.015);
  filter: grayscale(0.6);
}

/* Ikon warning bulat merah + segitiga seru */
.mm-warning-badge {
  color: #F87171;
  font-size: 13px;
  margin-left: 6px;
  vertical-align: middle;
}
</style>