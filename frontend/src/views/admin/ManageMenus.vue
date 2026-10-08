<template>
  <div class="adm-page">

    <!-- ── Header ──────────────────────────────────────────────────── -->
    <header class="adm-header">
      <div>
        <p class="adm-eyebrow">Dapur Pro · Kelola Menu</p>
        <h1 class="adm-title">Kelola Menu</h1>
        <p class="adm-sub">Atur daftar menu, harga, kategori, dan ketersediaan stok.</p>
      </div>
      <div class="adm-header-actions mm-head-actions">
        <button type="button" class="adm-btn adm-btn--primary" @click="openAddModal">
          <Plus :size="15" /> Tambah Menu
        </button>
      </div>
    </header>

    <!-- ── Stat ────────────────────────────────────────────────────── -->
    <div class="adm-stats">
      <div class="adm-stat">
        <span class="adm-stat-icon tone-blue"><UtensilsCrossed :size="17" /></span>
        <div><p class="adm-stat-value">{{ menus.length }}</p><p class="adm-stat-label">Total menu</p></div>
      </div>
      <div class="adm-stat">
        <span class="adm-stat-icon tone-green"><CheckCircle2 :size="17" /></span>
        <div><p class="adm-stat-value">{{ availableCount }}</p><p class="adm-stat-label">Tersedia</p></div>
      </div>
      <div class="adm-stat">
        <span class="adm-stat-icon tone-accent"><XCircle :size="17" /></span>
        <div><p class="adm-stat-value">{{ soldOutCount }}</p><p class="adm-stat-label">Stok habis</p></div>
      </div>
      <div class="adm-stat">
        <span class="adm-stat-icon tone-amber"><Tag :size="17" /></span>
        <div><p class="adm-stat-value">{{ categoryCount }}</p><p class="adm-stat-label">Kategori</p></div>
      </div>
    </div>

    <!-- ── Toolbar ─────────────────────────────────────────────────── -->
    <div class="adm-toolbar">
      <div class="adm-search">
        <Search :size="15" class="adm-search-icon" />
        <input v-model="searchQuery" type="search" class="adm-input" placeholder="Cari nama menu…" aria-label="Cari menu" />
        <button v-if="searchQuery" type="button" class="adm-search-clear" aria-label="Hapus pencarian" @click="searchQuery = ''">
          <X :size="14" />
        </button>
      </div>
      <div class="mm-filters">
        <select v-model="filterStatus" class="adm-input" aria-label="Filter status">
          <option value="">Semua status</option>
          <option value="available">Tersedia</option>
          <option value="soldout">Habis</option>
          <option value="recommended">Rekomendasi</option>
          <option value="secret">Secret menu</option>
        </select>
        <select v-model="filterCategory" class="adm-input" aria-label="Filter kategori">
          <option value="">Semua kategori</option>
          <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
        </select>
      </div>
    </div>

    <!-- ── Loading ─────────────────────────────────────────────────── -->
    <div v-if="loading" class="adm-card adm-card--flush" aria-busy="true">
      <div v-for="n in 5" :key="n" class="mm-item">
        <span class="adm-skel" style="width: 44px; height: 44px; grid-area: thumb"></span>
        <span class="adm-skel" style="height: 14px; width: 60%; grid-area: info"></span>
      </div>
    </div>

    <!-- ── Kosong ──────────────────────────────────────────────────── -->
    <div v-else-if="filteredMenus.length === 0" class="adm-card">
      <div class="adm-empty">
        <div class="adm-empty-icon"><Salad :size="22" /></div>
        <template v-if="hasActiveFilter">
          <p class="adm-empty-title">Tidak ada menu yang cocok</p>
          <p class="adm-empty-text">Coba ubah kata kunci atau filter pencarian.</p>
          <button type="button" class="adm-btn adm-btn--ghost" @click="resetFilters">Reset Filter</button>
        </template>
        <template v-else>
          <p class="adm-empty-title">Belum ada menu</p>
          <p class="adm-empty-text">Mulai dengan menambahkan menu pertama Anda.</p>
          <button type="button" class="adm-btn adm-btn--primary" @click="openAddModal"><Plus :size="15" /> Tambah Menu</button>
        </template>
      </div>
    </div>

    <!-- ── Grup menu ───────────────────────────────────────────────── -->
    <div v-else class="mm-groups">
      <section v-for="(items, catName) in groupedFiltered" :key="catName" class="mm-group">
        <div class="mm-group-head">
          <h2 class="mm-group-label" :class="{ 'is-orphan': isOrphan(catName) }">
            <AlertTriangle v-if="isOrphan(catName)" :size="13" />
            {{ displayGroupName(catName) }}
            <span class="adm-badge">{{ items.length }} item</span>
          </h2>
          <span class="mm-group-avail">{{ items.filter((m) => m.is_available).length }} / {{ items.length }} tersedia</span>
        </div>

        <div class="adm-card adm-card--flush">
          <ul class="mm-list">
            <li
              v-for="menu in items" :key="menu.id" class="mm-item"
              :class="{ 'is-out': !menu.is_available, 'is-orphan': !menu.category_name }"
            >
              <div class="mm-thumb" :style="{ background: getCategoryColor(catName) }">
                <img v-if="menu.image_url" :src="menu.image_url" :alt="menu.name" loading="lazy" />
                <span v-else>{{ menu.name.charAt(0).toUpperCase() }}</span>
              </div>

              <div class="mm-info">
                <p class="mm-name">
                  <span class="adm-truncate">{{ menu.name }}</span>
                  <ThumbsUp v-if="menu.is_recommended" :size="13" class="mm-flag mm-flag--rec" title="Rekomendasi (badge jempol di halaman Menu)" />
                  <EyeOff v-if="menu.is_secret" :size="13" class="mm-flag mm-flag--secret" title="Secret menu: hanya muncul di New Order" />
                  <ListChecks v-if="menu.options?.length" :size="13" class="mm-flag mm-flag--opt" :title="`${menu.options.length} grup opsi`" />
                  <AlertTriangle
                    v-if="!menu.category_name" :size="13" class="mm-warn"
                    title="Kategori menu ini sudah dihapus. Klik Edit untuk memilih kategori baru."
                  />
                </p>
                <p class="mm-cat">{{ isOrphan(catName) ? 'Tanpa kategori' : catName }}</p>
              </div>

              <p class="mm-price">{{ formatPrice(menu.price) }}</p>

              <button
                type="button" class="adm-badge mm-status"
                :class="menu.is_available ? 'adm-badge--green' : 'adm-badge--red'"
                :title="menu.is_available ? 'Klik untuk tandai habis' : 'Klik untuk tandai tersedia'"
                :aria-label="`${menu.name}: ${menu.is_available ? 'tersedia' : 'habis'}. Klik untuk mengubah.`"
                @click="toggleStock(menu)"
              >
                <span class="adm-dot"></span>{{ menu.is_available ? 'Tersedia' : 'Habis' }}
              </button>

              <div class="mm-actions">
                <button type="button" class="adm-icon-btn" :aria-label="`Edit ${menu.name}`" @click="editMenu(menu)"><Pencil :size="15" /></button>
                <button type="button" class="adm-icon-btn adm-icon-btn--danger" :aria-label="`Hapus ${menu.name}`" @click="promptDelete(menu)"><Trash2 :size="15" /></button>
              </div>
            </li>
          </ul>
        </div>
      </section>
    </div>

    <!-- ══ Modal: tambah / edit menu ═════════════════════════════════
         Disembunyikan sementara saat cropper terbuka; isi form tetap aman. -->
    <AdminModal
      :model-value="isDialogOpen && !showCropper"
      :title="editingMenu ? 'Edit Menu' : 'Tambah Menu Baru'"
      :persistent="saving"
      @update:model-value="(v) => !v && closeModal()"
    >
      <form id="menu-form" class="mm-form" novalidate @submit.prevent="saveMenu">
        <!-- Foto -->
        <div class="adm-field">
          <span class="adm-label">Foto menu</span>
          <button
            type="button" class="mm-drop" :class="{ 'has-photo': photoPreview, 'is-over': dragOver }"
            :aria-label="photoPreview ? 'Ganti foto menu' : 'Pilih foto menu'"
            @click="fileInput.click()"
            @dragover.prevent="dragOver = true" @dragleave="dragOver = false" @drop.prevent="onDrop"
          >
            <img v-if="photoPreview" :src="photoPreview" alt="Pratinjau foto menu" />
            <span v-else class="mm-drop-empty">
              <ImagePlus :size="26" />
              <span>Klik atau seret foto ke sini</span>
              <small>JPG, PNG · maks 5 MB</small>
            </span>
            <span v-if="photoPreview" class="mm-drop-change"><Pencil :size="13" /> Ganti foto</span>
          </button>
          <input ref="fileInput" type="file" accept="image/*" hidden @change="onFileChange" />
        </div>

        <div class="adm-grid-2">
          <div class="adm-field">
            <label class="adm-label" for="menu-name">Nama menu <span class="adm-req">*</span></label>
            <input id="menu-name" v-model="form.name" data-autofocus type="text" class="adm-input" placeholder="Contoh: Nasi Goreng Spesial" :aria-invalid="!!errors.name" />
            <p v-if="errors.name" class="adm-error">{{ errors.name }}</p>
          </div>
          <div class="adm-field">
            <label class="adm-label" for="menu-cat">Kategori <span class="adm-req">*</span></label>
            <div class="mm-cat-row">
              <select id="menu-cat" v-model="form.category" class="adm-input" :aria-invalid="!!errors.category">
                <option value="" disabled>Pilih kategori</option>
                <option v-for="cat in categoryList" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
              </select>
              <button type="button" class="adm-btn adm-btn--soft mm-cat-add" aria-label="Tambah kategori baru" title="Tambah kategori baru" @click="openCategoryModal">
                <Plus :size="16" />
              </button>
            </div>
            <p v-if="errors.category" class="adm-error">{{ errors.category }}</p>
          </div>
        </div>

        <div class="adm-grid-2">
          <div class="adm-field">
            <label class="adm-label" for="menu-price">Harga <span class="adm-req">*</span></label>
            <div class="adm-affix">
              <span class="adm-affix-pre" aria-hidden="true">Rp</span>
              <input id="menu-price" v-model="form.price" type="number" inputmode="numeric" min="0" class="adm-input adm-input--mono has-pre" placeholder="0" :aria-invalid="!!errors.price" />
            </div>
            <p v-if="errors.price" class="adm-error">{{ errors.price }}</p>
          </div>
          <div class="adm-field">
            <span id="menu-stock-label" class="adm-label">Status stok</span>
            <div class="mm-toggle-row">
              <button
                type="button" class="adm-switch" role="switch" aria-labelledby="menu-stock-label"
                :aria-checked="form.is_available" @click="form.is_available = !form.is_available"
              ></button>
              <span class="mm-toggle-text">{{ form.is_available ? 'Tersedia' : 'Stok habis' }}</span>
            </div>
          </div>
        </div>

        <div class="adm-field">
          <label class="adm-label" for="menu-desc">Deskripsi <span class="adm-opt">(opsional)</span></label>
          <textarea id="menu-desc" v-model="form.description" class="adm-input" rows="3" placeholder="Deskripsi singkat menu"></textarea>
        </div>

        <div class="adm-grid-2">
          <div class="adm-field">
            <span id="menu-rec-label" class="adm-label">Rekomendasi</span>
            <div class="mm-toggle-row">
              <button
                type="button" class="adm-switch" role="switch" aria-labelledby="menu-rec-label"
                :aria-checked="form.is_recommended" @click="form.is_recommended = !form.is_recommended"
              ></button>
              <span class="mm-toggle-text">{{ form.is_recommended ? 'Tampil badge jempol' : 'Tanpa badge' }}</span>
            </div>
          </div>
          <div class="adm-field">
            <span id="menu-secret-label" class="adm-label">Secret menu</span>
            <div class="mm-toggle-row">
              <button
                type="button" class="adm-switch" role="switch" aria-labelledby="menu-secret-label"
                :aria-checked="form.is_secret" @click="form.is_secret = !form.is_secret"
              ></button>
              <span class="mm-toggle-text">{{ form.is_secret ? 'Hanya di New Order' : 'Tampil di halaman Menu' }}</span>
            </div>
          </div>
        </div>

        <!-- Opsi pilihan (pedas, suhu, ukuran, add-on) -->
        <div class="adm-field">
          <span class="adm-label">Opsi pilihan <span class="adm-opt">(opsional)</span></span>
          <p class="mm-opt-hint">
            Contoh: Level Pedas (pilih satu) atau Tambahan (boleh banyak, berbayar). Kosongkan harga kalau gratis.
          </p>

          <div v-for="(group, gi) in form.options" :key="gi" class="mm-opt-group">
            <div class="mm-opt-head">
              <input
                v-model="group.name" type="text" class="adm-input" maxlength="50"
                placeholder="Nama grup, mis. Level Pedas" :aria-label="`Nama grup opsi ${gi + 1}`"
              />
              <button type="button" class="adm-icon-btn adm-icon-btn--danger" :aria-label="`Hapus grup ${group.name || gi + 1}`" @click="removeGroup(gi)">
                <Trash2 :size="15" />
              </button>
            </div>

            <div class="mm-opt-flags">
              <label class="mm-opt-check"><input v-model="group.required" type="checkbox" /> Wajib dipilih</label>
              <label class="mm-opt-check"><input v-model="group.multiple" type="checkbox" /> Boleh pilih banyak</label>
            </div>

            <div v-for="(choice, ci) in group.choices" :key="ci" class="mm-opt-choice">
              <input
                v-model="choice.label" type="text" class="adm-input" maxlength="50"
                placeholder="Nama pilihan" :aria-label="`Pilihan ${ci + 1} di ${group.name || 'grup'}`"
              />
              <div class="adm-affix mm-opt-price">
                <span class="adm-affix-pre" aria-hidden="true">+Rp</span>
                <input
                  v-model="choice.price" type="number" inputmode="numeric" min="0" step="500"
                  class="adm-input adm-input--mono has-pre" placeholder="0" aria-label="Harga tambahan"
                />
              </div>
              <button
                type="button" class="adm-icon-btn" :disabled="group.choices.length <= 1"
                :aria-label="`Hapus pilihan ${choice.label || ci + 1}`" @click="removeChoice(group, ci)"
              >
                <X :size="14" />
              </button>
            </div>

            <button
              type="button" class="adm-btn adm-btn--ghost mm-opt-add"
              :disabled="group.choices.length >= MAX_CHOICES" @click="addChoice(group)"
            >
              <Plus :size="14" /> Tambah pilihan
            </button>
          </div>

          <div class="mm-opt-actions">
            <button type="button" class="adm-btn adm-btn--soft" :disabled="form.options.length >= MAX_GROUPS" @click="addGroup()">
              <Plus :size="14" /> Grup opsi
            </button>
            <button type="button" class="adm-btn adm-btn--ghost" :disabled="form.options.length >= MAX_GROUPS" @click="addSpicyPreset">
              Preset Level Pedas
            </button>
          </div>
          <p v-if="errors.options" class="adm-error">{{ errors.options }}</p>
        </div>
      </form>

      <template #footer>
        <button type="button" class="adm-btn adm-btn--ghost" :disabled="saving" @click="closeModal">Batal</button>
        <button type="submit" form="menu-form" class="adm-btn adm-btn--primary" :disabled="saving">
          <span v-if="saving" class="adm-spinner"></span><Save v-else :size="15" />
          {{ saving ? 'Menyimpan…' : editingMenu ? 'Simpan Perubahan' : 'Tambah Menu' }}
        </button>
      </template>
    </AdminModal>

    <!-- ══ Modal: tambah kategori (sejajar, bukan di dalam modal menu) ══ -->
    <AdminModal v-model="showCategoryModal" title="Tambah Kategori" size="sm" :persistent="savingCategory">
      <form id="cat-form" class="mm-form" @submit.prevent="saveCategory">
        <div class="adm-field">
          <label class="adm-label" for="cat-name">Nama kategori <span class="adm-req">*</span></label>
          <input id="cat-name" v-model="newCategory.name" data-autofocus type="text" class="adm-input" placeholder="Contoh: Makanan Utama" :aria-invalid="!!categoryError" />
          <p v-if="categoryError" class="adm-error">{{ categoryError }}</p>
        </div>
        <div class="adm-field">
          <label class="adm-label" for="cat-group">Grup</label>
          <select id="cat-group" v-model="newCategory.group" class="adm-input">
            <option value="makanan">Makanan</option>
            <option value="snack">Snack</option>
            <option value="minuman">Minuman</option>
          </select>
        </div>
      </form>
      <template #footer>
        <button type="button" class="adm-btn adm-btn--ghost" :disabled="savingCategory" @click="closeCategoryModal">Batal</button>
        <button type="submit" form="cat-form" class="adm-btn adm-btn--primary" :disabled="savingCategory">
          <span v-if="savingCategory" class="adm-spinner"></span>
          {{ savingCategory ? 'Menyimpan…' : 'Tambah Kategori' }}
        </button>
      </template>
    </AdminModal>

    <!-- ══ Modal: konfirmasi hapus ═══════════════════════════════════ -->
    <AdminModal
      :model-value="!!deleteTarget" title="Hapus menu?" size="sm" :persistent="saving"
      @update:model-value="(v) => !v && (deleteTarget = null)"
    >
      <p class="adm-modal-text">
        Menu <strong>{{ deleteTarget?.name }}</strong> akan dihapus permanen beserta fotonya. Tindakan ini tidak bisa dibatalkan.
      </p>
      <template #footer>
        <button type="button" class="adm-btn adm-btn--ghost" :disabled="saving" @click="deleteTarget = null">Batal</button>
        <button type="button" class="adm-btn adm-btn--danger" data-autofocus :disabled="saving" @click="confirmDelete">
          <span v-if="saving" class="adm-spinner"></span><Trash2 v-else :size="15" />
          {{ saving ? 'Menghapus…' : 'Ya, hapus' }}
        </button>
      </template>
    </AdminModal>

    <ImageCropper v-if="showCropper" :image="rawImageForCropper" type="menu" @crop-complete="onCropComplete" @cancel="onCropCancel" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import {
  Plus, Search, X, Pencil, Trash2, Save, ImagePlus, Salad, AlertTriangle,
  UtensilsCrossed, CheckCircle2, XCircle, Tag, ThumbsUp, EyeOff, ListChecks,
} from 'lucide-vue-next'
import apiClient from '@/api/client'
import ImageCropper from '@/components/ui/ImageCropper.vue'
import AdminModal from '@/components/ui/admin/Adminmodal.vue'

const router = useRouter()

// ── State ───────────────────────────────────────────────────────────
const menus          = ref([])
const loading        = ref(true)
const isDialogOpen   = ref(false)
const editingMenu    = ref(null)
const deleteTarget   = ref(null)
const saving         = ref(false)
const searchQuery    = ref('')
const filterStatus   = ref('')
const filterCategory = ref('')
const photoPreview   = ref(null)
const photoFile      = ref(null)
const fileInput      = ref(null)
const dragOver       = ref(false)

const showCategoryModal = ref(false)
const savingCategory    = ref(false)
const categoryError     = ref('')
const newCategory       = reactive({ name: '', group: 'makanan' })
const categoryList      = ref([]) // [{id, name, group}]

const blankForm = () => ({
  name: '', category: '', price: '', description: '',
  is_available: true, is_recommended: false, is_secret: false,
  options: [],
})
const form   = reactive(blankForm())
const errors = reactive({ name: '', category: '', price: '', options: '' })

// Batas ini sama dengan menu/options.py (server tetap validasi ulang)
const MAX_GROUPS  = 6
const MAX_CHOICES = 15

const showCropper = ref(false)
const rawImageForCropper = ref(null)

// ── Warna kategori (thumbnail tanpa foto) ───────────────────────────
const COLORS = ['#E8521A', '#2563EB', '#059669', '#7C3AED', '#D97706', '#0891B2', '#BE185D']
const _colorMap = {}
const getCategoryColor = (cat) => {
  if (!_colorMap[cat]) _colorMap[cat] = COLORS[Object.keys(_colorMap).length % COLORS.length]
  return _colorMap[cat]
}

// ── Computed ────────────────────────────────────────────────────────
const availableCount = computed(() => menus.value.filter((m) => m.is_available).length)
const soldOutCount   = computed(() => menus.value.filter((m) => !m.is_available).length)
const categories     = computed(() => [...new Set(menus.value.map((m) => m.category_name || 'Lainnya'))])
const categoryCount  = computed(() => categories.value.length)
const hasActiveFilter = computed(() => !!(searchQuery.value || filterStatus.value || filterCategory.value))

const filteredMenus = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  return menus.value.filter((m) => {
    const okStatus =
      filterStatus.value === '' ||
      (filterStatus.value === 'available' && m.is_available) ||
      (filterStatus.value === 'soldout' && !m.is_available) ||
      (filterStatus.value === 'recommended' && m.is_recommended) ||
      (filterStatus.value === 'secret' && m.is_secret)
    const okCat = filterCategory.value === '' || (m.category_name || 'Lainnya') === filterCategory.value
    return m.name.toLowerCase().includes(q) && okStatus && okCat
  })
})

const groupedFiltered = computed(() =>
  filteredMenus.value.reduce((g, m) => {
    const cat = m.category_name || '__orphan__' // marker khusus
    ;(g[cat] = g[cat] || []).push(m)
    return g
  }, {})
)

const resetFilters = () => { searchQuery.value = ''; filterStatus.value = ''; filterCategory.value = '' }

// ── Helpers ─────────────────────────────────────────────────────────
const formatPrice = (p) =>
  new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(p)

const isOrphan = (catName) => catName === '__orphan__'
const displayGroupName = (catName) => (isOrphan(catName) ? 'Tanpa Kategori' : catName)

const clearErrors = () => { errors.name = errors.category = errors.price = errors.options = '' }

// ── Editor opsi ─────────────────────────────────────────────────────
const addGroup = (name = '', required = false, labels = ['']) => {
  if (form.options.length >= MAX_GROUPS) return
  form.options.push({
    name, required, multiple: false,
    choices: labels.map((label) => ({ label, price: '' })),
  })
}
const addSpicyPreset = () => addGroup('Level Pedas', true, ['Nggak pedas', 'Sedeng', 'Pedas'])
const removeGroup = (gi) => { form.options.splice(gi, 1) }
const addChoice = (group) => { if (group.choices.length < MAX_CHOICES) group.choices.push({ label: '', price: '' }) }
const removeChoice = (group, ci) => { if (group.choices.length > 1) group.choices.splice(ci, 1) }

// Bersihkan + cek opsi sebelum dikirim. Return { list } atau { error }.
const buildOptions = () => {
  const list = []
  const seenGroups = new Set()
  for (const g of form.options) {
    const name = (g.name || '').trim()
    if (!name) return { error: 'Nama grup opsi wajib diisi (atau hapus grupnya).' }
    if (seenGroups.has(name.toLowerCase())) return { error: `Grup "${name}" dobel.` }
    seenGroups.add(name.toLowerCase())

    const seenLabels = new Set()
    const choices = []
    for (const c of g.choices) {
      const label = (c.label || '').trim()
      if (!label) return { error: `Ada pilihan kosong di grup "${name}".` }
      if (seenLabels.has(label.toLowerCase())) return { error: `Pilihan "${label}" dobel di grup "${name}".` }
      seenLabels.add(label.toLowerCase())
      const price = c.price === '' || c.price == null ? 0 : Number(c.price)
      if (!Number.isInteger(price) || price < 0) return { error: `Harga "${label}" harus bilangan bulat, tidak negatif.` }
      choices.push({ label, price })
    }
    if (!choices.length) return { error: `Grup "${name}" minimal punya 1 pilihan.` }
    list.push({ name, required: !!g.required, multiple: !!g.multiple, choices })
  }
  return { list }
}
const validate = () => {
  clearErrors()
  let ok = true
  if (!form.name.trim())               { errors.name = 'Nama menu wajib diisi.'; ok = false }
  if (!form.category)                  { errors.category = 'Kategori wajib diisi.'; ok = false }
  if (!form.price || +form.price <= 0) { errors.price = 'Harga harus lebih dari 0.'; ok = false }
  const opt = buildOptions()
  if (opt.error) { errors.options = opt.error; ok = false }
  return ok
}

// ── Kategori ────────────────────────────────────────────────────────
const openCategoryModal = () => {
  newCategory.name = ''
  newCategory.group = 'makanan'
  categoryError.value = ''
  showCategoryModal.value = true
}
const closeCategoryModal = () => { if (!savingCategory.value) showCategoryModal.value = false }

const fetchCategories = async () => {
  try {
    const res = await apiClient.get('/categories/')
    categoryList.value = res.data
  } catch {
    toast.error('Gagal memuat kategori')
  }
}

const saveCategory = async () => {
  if (!newCategory.name.trim()) { categoryError.value = 'Nama kategori wajib diisi.'; return }
  savingCategory.value = true
  categoryError.value = ''
  try {
    const res = await apiClient.post('/categories/', { name: newCategory.name.trim(), group: newCategory.group })
    await fetchCategories()
    form.category = res.data.id // langsung pilih kategori baru di form menu
    errors.category = ''
    showCategoryModal.value = false
    toast.success('Kategori baru ditambahkan')
  } catch (err) {
    categoryError.value = err.response?.data?.name?.[0] || 'Gagal menambahkan kategori.'
  } finally {
    savingCategory.value = false
  }
}

// ── Foto ────────────────────────────────────────────────────────────
const openCropper = (file) => {
  if (rawImageForCropper.value) URL.revokeObjectURL(rawImageForCropper.value)
  rawImageForCropper.value = URL.createObjectURL(file)
  showCropper.value = true
}
const onFileChange = (e) => {
  const f = e.target.files[0]
  if (!f) return
  openCropper(f)
  e.target.value = '' // supaya file yang sama bisa dipilih lagi
}
const onDrop = (e) => {
  dragOver.value = false
  const f = e.dataTransfer.files[0]
  if (f && f.type.startsWith('image/')) openCropper(f)
  else if (f) toast.error('File harus berupa gambar (JPG/PNG).')
}
const onCropComplete = (blob) => {
  // Cropper memberi Blob JPEG — bungkus jadi File agar konsisten dengan FormData
  const croppedFile = new File([blob], 'menu-photo.jpg', { type: 'image/jpeg' })
  if (photoPreview.value?.startsWith('blob:')) URL.revokeObjectURL(photoPreview.value)
  if (rawImageForCropper.value) URL.revokeObjectURL(rawImageForCropper.value)
  rawImageForCropper.value = null
  photoFile.value = croppedFile
  photoPreview.value = URL.createObjectURL(croppedFile)
  showCropper.value = false
}
const onCropCancel = () => {
  if (rawImageForCropper.value) URL.revokeObjectURL(rawImageForCropper.value)
  rawImageForCropper.value = null
  showCropper.value = false
}

// ── CRUD ────────────────────────────────────────────────────────────
// silent=true → refresh tanpa mengganti daftar dengan skeleton (tidak loncat scroll)
const fetchMenus = async ({ silent = false } = {}) => {
  if (!silent) loading.value = true
  try {
    const res = await apiClient.get('/menus/')
    menus.value = res.data
  } catch {
    toast.error('Gagal memuat data menu')
  } finally {
    loading.value = false
  }
}

const resetPhoto = () => {
  if (photoPreview.value?.startsWith('blob:')) URL.revokeObjectURL(photoPreview.value)
  photoPreview.value = null
  photoFile.value = null
}

const openAddModal = () => {
  editingMenu.value = null
  Object.assign(form, blankForm())
  clearErrors()
  resetPhoto()
  isDialogOpen.value = true
}

const editMenu = (menu) => {
  editingMenu.value = menu
  Object.assign(form, {
    name: menu.name,
    category: menu.category, // ID dari serializer, bukan category_name
    price: menu.price,
    description: menu.description || '',
    is_available: menu.is_available,
    is_recommended: !!menu.is_recommended,
    is_secret: !!menu.is_secret,
    // Salin dalam supaya mengetik di editor tidak mengubah daftar menu sebelum disimpan
    options: (menu.options || []).map((g) => ({
      name: g.name,
      required: !!g.required,
      multiple: !!g.multiple,
      choices: (g.choices || []).map((c) => ({ label: c.label, price: c.price || '' })),
    })),
  })
  clearErrors()
  resetPhoto()
  photoPreview.value = menu.image_url || null
  isDialogOpen.value = true
}

const closeModal = () => {
  isDialogOpen.value = false
  editingMenu.value = null
}

const saveMenu = async () => {
  if (!validate()) return
  saving.value = true
  try {
    const payload = new FormData()
    payload.append('name', form.name)
    payload.append('category', form.category) // ID
    payload.append('price', form.price)
    payload.append('description', form.description)
    payload.append('is_available', form.is_available)
    payload.append('is_recommended', form.is_recommended)
    payload.append('is_secret', form.is_secret)
    payload.append('options', JSON.stringify(buildOptions().list))
    if (photoFile.value) payload.append('image', photoFile.value)

    if (editingMenu.value) {
      await apiClient.patch(`/menus/${editingMenu.value.id}/`, payload)
      toast.success('Menu berhasil diperbarui')
    } else {
      await apiClient.post('/menus/', payload)
      toast.success('Menu baru berhasil ditambahkan')
    }
    await fetchMenus({ silent: true })
    closeModal()
  } catch (err) {
    // Pesan validasi dari server (mis. opsi tidak valid) ditampilkan di tempatnya
    const data = err.response?.data
    const optMsg = Array.isArray(data?.options) ? data.options[0] : data?.options
    if (optMsg) errors.options = String(optMsg)
    toast.error(optMsg ? 'Opsi menu belum valid' : 'Gagal menyimpan menu')
  } finally {
    saving.value = false
  }
}

const promptDelete = (menu) => { deleteTarget.value = menu }

const confirmDelete = async () => {
  const target = deleteTarget.value
  if (!target) return
  saving.value = true
  try {
    await apiClient.delete(`/menus/${target.id}/`)
  } catch {
    // Server kadang membalas error padahal data sudah terhapus — cek kenyataannya di bawah.
  }
  await fetchMenus({ silent: true })
  if (menus.value.some((m) => m.id === target.id)) toast.error('Gagal menghapus menu')
  else toast.success('Menu berhasil dihapus')
  deleteTarget.value = null
  saving.value = false
}

const toggleStock = async (menu) => {
  const prev = menu.is_available
  menu.is_available = !prev
  try {
    await apiClient.patch(`/menus/${menu.id}/`, { is_available: menu.is_available })
    toast.success(`${menu.name} ditandai ${menu.is_available ? 'tersedia' : 'habis'}`)
  } catch {
    menu.is_available = prev
    toast.error('Gagal mengubah status')
  }
}

// ── Init ────────────────────────────────────────────────────────────
onMounted(async () => {
  const token = localStorage.getItem('token')
  if (!token) { router.push('/login'); return }
  await Promise.all([fetchMenus(), fetchCategories()])
})
</script>

<style scoped>
/* Filter */
.mm-filters { display: flex; gap: 0.5rem; }
.mm-filters .adm-input { width: auto; min-width: 9.5rem; }

/* Grup */
.mm-groups { display: flex; flex-direction: column; gap: 1.5rem; }
.mm-group-head { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; margin-bottom: 0.6rem; padding: 0 0.15rem; }
.mm-group-label {
  display: inline-flex; align-items: center; gap: 0.5rem; margin: 0;
  font-family: var(--font-display); font-size: 0.8rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--accent-text);
}
.mm-group-label.is-orphan { color: var(--red-soft); }
.mm-group-label .adm-badge { font-family: var(--font-body); letter-spacing: 0; text-transform: none; }
.mm-group-avail { font-size: 0.75rem; color: var(--text-faint); }

/* Baris menu: satu markup, grid berubah di layar kecil */
.mm-list { margin: 0; padding: 0; list-style: none; }
.mm-item {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr) 8rem auto auto;
  grid-template-areas: 'thumb info price status actions';
  align-items: center;
  gap: 0.75rem 1rem;
  padding: 0.75rem 1.1rem;
  border-bottom: 1px solid var(--border);
  transition: background 0.12s;
}
.mm-item:last-child { border-bottom: none; }
.mm-item:hover { background: var(--surface-hover); }
.mm-item.is-orphan { background: rgb(var(--ink) / 0.025); }
.mm-item.is-out .mm-thumb, .mm-item.is-out .mm-info, .mm-item.is-out .mm-price { opacity: 0.5; }

.mm-thumb {
  grid-area: thumb;
  display: flex; align-items: center; justify-content: center;
  width: 44px; height: 44px; overflow: hidden; border-radius: var(--r-sm);
  color: #fff; font-family: var(--font-display); font-size: 1rem; font-weight: 600;
}
.mm-item.is-orphan .mm-thumb { filter: grayscale(1); }
.mm-thumb img { width: 100%; height: 100%; object-fit: cover; }

.mm-info { grid-area: info; min-width: 0; }
.mm-name { display: flex; align-items: center; gap: 0.4rem; margin: 0; font-size: 0.875rem; font-weight: 600; color: var(--text); }
.mm-warn { flex-shrink: 0; color: var(--red-soft); }
.mm-cat { margin: 0.15rem 0 0; font-size: 0.72rem; color: var(--text-faint); }
.mm-price { grid-area: price; margin: 0; font-size: 0.8125rem; font-weight: 600; color: var(--text-2); text-align: right; font-variant-numeric: tabular-nums; }
.mm-status { grid-area: status; justify-self: end; }
.mm-actions { grid-area: actions; display: flex; gap: 0.1rem; }

@media (max-width: 640px) {
  .mm-item {
    grid-template-columns: 44px minmax(0, 1fr) auto;
    grid-template-areas:
      'thumb info   actions'
      'thumb price  status';
    gap: 0.35rem 0.85rem;
    padding: 0.85rem 1rem;
  }
  .mm-price { text-align: left; }
  .mm-thumb { align-self: start; }
  .mm-head-actions, .mm-head-actions .adm-btn { width: 100%; }
  .mm-filters { width: 100%; }
  .mm-filters .adm-input { flex: 1; min-width: 0; }
  .adm-search { max-width: none; flex-basis: 100%; }
}

/* Form */
.mm-form { display: flex; flex-direction: column; gap: 1rem; }
.mm-cat-row { display: flex; gap: 0.5rem; }
.mm-cat-row .adm-input { flex: 1; min-width: 0; }
.mm-cat-add { flex-shrink: 0; width: 42px; padding: 0; }
.mm-toggle-row { display: flex; align-items: center; gap: 0.7rem; min-height: 42px; }
.mm-toggle-text { font-size: 0.8125rem; color: var(--text-2); }

/* Penanda di baris menu */
.mm-flag { flex-shrink: 0; }
.mm-flag--rec { color: var(--accent-text); }
.mm-flag--secret { color: var(--red-soft); }
.mm-flag--opt { color: var(--text-faint); }

/* Editor opsi */
.mm-opt-hint { margin: 0 0 0.6rem; font-size: 0.75rem; color: var(--text-faint); }
.mm-opt-group {
  display: flex; flex-direction: column; gap: 0.6rem; margin-bottom: 0.75rem; padding: 0.8rem;
  border: 1px solid var(--border); border-radius: var(--r-md); background: var(--surface-2);
}
.mm-opt-head { display: flex; gap: 0.5rem; align-items: center; }
.mm-opt-head .adm-input { flex: 1; min-width: 0; }
.mm-opt-flags { display: flex; flex-wrap: wrap; gap: 0.4rem 1.1rem; }
.mm-opt-check { display: inline-flex; align-items: center; gap: 0.4rem; font-size: 0.78rem; color: var(--text-2); cursor: pointer; }
.mm-opt-choice { display: grid; grid-template-columns: minmax(0, 1fr) 8.5rem auto; gap: 0.5rem; align-items: center; }
.mm-opt-price { min-width: 0; }
.mm-opt-add { align-self: flex-start; }
.mm-opt-actions { display: flex; flex-wrap: wrap; gap: 0.5rem; }
@media (max-width: 640px) {
  .mm-opt-choice { grid-template-columns: minmax(0, 1fr) 7rem auto; }
}

/* Dropzone foto */
.mm-drop {
  position: relative; display: flex; align-items: center; justify-content: center;
  width: 100%; min-height: 7rem; padding: 0; overflow: hidden;
  border: 1.5px dashed var(--border-strong); border-radius: var(--r-md);
  background: var(--surface-2); color: var(--text-faint); font-family: inherit; cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.mm-drop:hover, .mm-drop.is-over { border-color: var(--accent); background: var(--tint-accent); }
.mm-drop.has-photo { border-style: solid; }
.mm-drop img { display: block; width: 100%; max-height: 12rem; object-fit: cover; }
.mm-drop-empty { display: flex; flex-direction: column; align-items: center; gap: 0.3rem; padding: 1.25rem; font-size: 0.8125rem; color: var(--text-dim); }
.mm-drop-empty small { font-size: 0.7rem; color: var(--text-faint); }
.mm-drop-change {
  position: absolute; right: 0.6rem; bottom: 0.6rem;
  display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.3rem 0.6rem;
  border-radius: 99px; background: rgb(0 0 0 / 0.65); color: #fff; font-size: 0.7rem; font-weight: 600;
}
</style>