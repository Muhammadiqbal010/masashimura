<template>
  <div class="adm-page">

    <!-- ── Header ──────────────────────────────────────────────────── -->
    <header class="adm-header">
      <div>
        <p class="adm-eyebrow">Masashimura · Admin</p>
        <h1 class="adm-title">Kelola Promo</h1>
        <p class="adm-sub">Kode diskon untuk customer web & POS.</p>
      </div>
      <div class="adm-header-actions">
        <button type="button" class="adm-btn adm-btn--primary pr-new" @click="openCreateModal">
          <Plus :size="15" /> Buat Promo
        </button>
      </div>
    </header>

    <!-- ── Stat ────────────────────────────────────────────────────── -->
    <div class="adm-stats">
      <div class="adm-stat">
        <span class="adm-stat-icon tone-accent"><Tag :size="17" /></span>
        <div><p class="adm-stat-value">{{ totalPromos }}</p><p class="adm-stat-label">Total promo</p></div>
      </div>
      <div class="adm-stat">
        <span class="adm-stat-icon tone-green"><CheckCircle2 :size="17" /></span>
        <div><p class="adm-stat-value">{{ activePromoCount }}</p><p class="adm-stat-label">Sedang aktif</p></div>
      </div>
      <div class="adm-stat">
        <span class="adm-stat-icon tone-amber"><Ticket :size="17" /></span>
        <div><p class="adm-stat-value">{{ totalUsage.toLocaleString('id-ID') }}</p><p class="adm-stat-label">Total pemakaian</p></div>
      </div>
    </div>

    <!-- ── Toolbar ─────────────────────────────────────────────────── -->
    <div v-if="!isLoading && !loadError && promos.length > 0" class="adm-toolbar">
      <div class="adm-search">
        <Search :size="15" class="adm-search-icon" />
        <input v-model="searchQuery" type="search" class="adm-input" placeholder="Cari kode atau deskripsi…" aria-label="Cari promo" />
      </div>
      <div class="adm-seg" role="group" aria-label="Filter status">
        <button
          v-for="f in statusFilters" :key="f.key" type="button" class="adm-seg-btn"
          :aria-pressed="statusFilter === f.key" @click="statusFilter = f.key"
        >
          {{ f.label }}
        </button>
      </div>
    </div>

    <!-- ── Konten ──────────────────────────────────────────────────── -->
    <section class="adm-card adm-card--flush" aria-live="polite">
      <!-- Loading -->
      <div v-if="isLoading" class="pr-skeletons" aria-busy="true">
        <div v-for="n in 4" :key="n" class="pr-skel-row">
          <span class="adm-skel" style="height: 14px; width: 22%"></span>
          <span class="adm-skel" style="height: 14px; width: 12%"></span>
          <span class="adm-skel" style="height: 14px; width: 30%"></span>
        </div>
      </div>

      <!-- Error -->
      <div v-else-if="loadError" class="adm-empty">
        <div class="adm-empty-icon"><AlertTriangle :size="22" /></div>
        <p class="adm-empty-title">Gagal memuat data promo</p>
        <p class="adm-empty-text">Periksa koneksi lalu coba lagi.</p>
        <button type="button" class="adm-btn adm-btn--primary" @click="fetchPromos">Coba Lagi</button>
      </div>

      <!-- Belum ada promo -->
      <div v-else-if="promos.length === 0" class="adm-empty">
        <div class="adm-empty-icon"><Tag :size="22" /></div>
        <p class="adm-empty-title">Belum ada kode promo</p>
        <p class="adm-empty-text">Buat kode diskon pertama untuk menarik lebih banyak pesanan.</p>
        <button type="button" class="adm-btn adm-btn--primary" @click="openCreateModal"><Plus :size="15" /> Buat Promo</button>
      </div>

      <!-- Tabel -->
      <div v-else-if="filteredPromos.length" class="adm-table-wrap">
        <table class="adm-table adm-table--stack">
          <thead>
            <tr>
              <th>Kode</th>
              <th>Diskon</th>
              <th>Min. belanja</th>
              <th>Kuota</th>
              <th>Berlaku</th>
              <th>Status</th>
              <th class="adm-th-r">Aksi</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="promo in filteredPromos" :key="promo.id">
              <td class="adm-td-first">
                <span class="pr-code adm-mono">{{ promo.code }}</span>
                <p v-if="promo.description" class="pr-desc">{{ promo.description }}</p>
              </td>
              <td data-label="Diskon">
                <div class="pr-stack-right">
                  <span class="pr-discount adm-mono">{{ formatDiscount(promo) }}</span>
                  <p v-if="promo.discount_type === 'percentage' && promo.max_discount_amount" class="pr-desc">
                    Maks {{ formatPrice(promo.max_discount_amount) }}
                  </p>
                </div>
              </td>
              <td data-label="Min. belanja" class="adm-mono">{{ formatPrice(promo.min_purchase) }}</td>
              <td data-label="Kuota" class="adm-mono">
                {{ promo.used_count }}<template v-if="promo.max_usage !== null">/{{ promo.max_usage }}</template><span v-else class="pr-faint"> / ∞</span>
              </td>
              <td data-label="Berlaku" class="adm-mono pr-period">
                {{ formatDateShort(promo.valid_from) }} – {{ formatDateShort(promo.valid_until) }}
              </td>
              <td data-label="Status">
                <button
                  type="button"
                  class="adm-badge"
                  :class="`adm-badge--${statusInfo(promo).tone}`"
                  :disabled="togglingId === promo.id"
                  :title="promo.is_active ? 'Klik untuk menonaktifkan' : 'Klik untuk mengaktifkan'"
                  :aria-label="`Status ${promo.code}: ${statusInfo(promo).label}. ${promo.is_active ? 'Klik untuk menonaktifkan' : 'Klik untuk mengaktifkan'}`"
                  @click="toggleActive(promo)"
                >
                  <span class="adm-dot"></span>{{ statusInfo(promo).label }}
                </button>
              </td>
              <td class="adm-td-r">
                <div class="pr-actions">
                  <button type="button" class="adm-icon-btn adm-icon-btn--bordered" :aria-label="`Edit ${promo.code}`" @click="openEditModal(promo)"><Pencil :size="14" /></button>
                  <button type="button" class="adm-icon-btn adm-icon-btn--bordered adm-icon-btn--danger" :aria-label="`Hapus ${promo.code}`" @click="deletePromo(promo)"><Trash2 :size="14" /></button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Filter tidak menemukan hasil -->
      <div v-else class="adm-empty">
        <div class="adm-empty-icon"><Search :size="22" /></div>
        <p class="adm-empty-title">Tidak ada promo yang cocok</p>
        <p class="adm-empty-text">Coba ubah kata kunci pencarian atau filter status.</p>
        <button type="button" class="adm-btn adm-btn--ghost" @click="resetFilters">Reset Filter</button>
      </div>
    </section>

    <!-- ── Modal buat / edit ───────────────────────────────────────── -->
    <AdminModal v-model="showModal" :title="editingId ? 'Edit Promo' : 'Buat Promo Baru'" :persistent="isSaving">
      <form id="promo-form" class="pr-form" novalidate @submit.prevent="submitForm">
        <div class="adm-field">
          <label class="adm-label" for="promo-code">Kode promo <span class="adm-req">*</span></label>
          <input
            id="promo-code" v-model="form.code" data-autofocus type="text" class="adm-input adm-input--mono"
            placeholder="MERDEKA17" autocomplete="off" autocapitalize="characters" spellcheck="false"
            @input="form.code = form.code.toUpperCase().replace(/\s/g, '')"
          />
        </div>

        <div class="adm-field">
          <label class="adm-label" for="promo-desc">Deskripsi <span class="adm-opt">(opsional)</span></label>
          <input id="promo-desc" v-model="form.description" type="text" class="adm-input" placeholder="Diskon spesial 17 Agustus" />
        </div>

        <div class="adm-grid-2">
          <div class="adm-field">
            <span id="type-label" class="adm-label">Tipe diskon</span>
            <div class="adm-seg adm-seg--fill" role="radiogroup" aria-labelledby="type-label">
              <button
                v-for="opt in discountTypeOptions" :key="opt.value" type="button" role="radio" class="adm-seg-btn"
                :aria-checked="form.discount_type === opt.value" @click="form.discount_type = opt.value"
              >
                {{ opt.label }}
              </button>
            </div>
          </div>
          <div class="adm-field">
            <label class="adm-label" for="promo-value">{{ form.discount_type === 'percentage' ? 'Nilai (%)' : 'Nilai (Rp)' }} <span class="adm-req">*</span></label>
            <input
              id="promo-value" v-model.number="form.discount_value" type="number" inputmode="numeric" min="0"
              :max="form.discount_type === 'percentage' ? 100 : undefined" class="adm-input adm-input--mono"
            />
          </div>
        </div>

        <div v-if="form.discount_type === 'percentage'" class="adm-field">
          <label class="adm-label" for="promo-cap">Cap maksimal diskon (Rp) <span class="adm-opt">(opsional)</span></label>
          <input id="promo-cap" v-model.number="form.max_discount_amount" type="number" inputmode="numeric" min="0" class="adm-input adm-input--mono" placeholder="Kosongkan = tanpa batas" />
        </div>

        <div class="adm-grid-2">
          <div class="adm-field">
            <label class="adm-label" for="promo-min">Minimal belanja (Rp)</label>
            <input id="promo-min" v-model.number="form.min_purchase" type="number" inputmode="numeric" min="0" class="adm-input adm-input--mono" />
          </div>
          <div class="adm-field">
            <label class="adm-label" for="promo-quota">Kuota pemakaian <span class="adm-opt">(opsional)</span></label>
            <input id="promo-quota" v-model.number="form.max_usage" type="number" inputmode="numeric" min="1" class="adm-input adm-input--mono" placeholder="Tanpa batas" />
          </div>
        </div>

        <div class="adm-grid-2">
          <div class="adm-field">
            <label class="adm-label" for="promo-from">Berlaku dari <span class="adm-req">*</span></label>
            <input id="promo-from" v-model="form.valid_from" type="datetime-local" class="adm-input adm-input--mono" />
          </div>
          <div class="adm-field">
            <label class="adm-label" for="promo-until">Berlaku sampai <span class="adm-req">*</span></label>
            <input id="promo-until" v-model="form.valid_until" type="datetime-local" class="adm-input adm-input--mono" />
          </div>
        </div>

        <label class="adm-check">
          <input v-model="form.is_active" type="checkbox" />
          <span>Aktifkan promo ini sekarang</span>
        </label>

        <p v-if="formError" class="adm-alert" role="alert"><AlertTriangle :size="15" style="flex-shrink: 0; margin-top: 2px" />{{ formError }}</p>
      </form>

      <template #footer>
        <button type="button" class="adm-btn adm-btn--ghost" :disabled="isSaving" @click="closeModal">Batal</button>
        <button type="submit" form="promo-form" class="adm-btn adm-btn--primary" :disabled="isSaving">
          <span v-if="isSaving" class="adm-spinner"></span>
          {{ isSaving ? 'Menyimpan…' : editingId ? 'Simpan Perubahan' : 'Buat Promo' }}
        </button>
      </template>
    </AdminModal>

    <AdminConfirm :state="confirmState" @confirm="acceptConfirm" @cancel="cancelConfirm" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Plus, Pencil, Trash2, Tag, CheckCircle2, Ticket, Search, AlertTriangle } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import apiClient from '@/api/client'
import AdminModal from '@/components/ui/admin/Adminmodal.vue'
import AdminConfirm from '@/components/ui/admin/Adminconfirm.vue'
import { useAdminConfirm } from '@/composables/useAdminConfirm'

const { state: confirmState, ask, accept: acceptConfirm, cancel: cancelConfirm } = useAdminConfirm()

const promos     = ref([])
const isLoading  = ref(true)
const loadError  = ref(false)
const togglingId = ref(null)

// ── Status ──────────────────────────────────────────────────────────
// key dipakai untuk filter, tone untuk warna badge
const statusInfo = (promo) => {
  const now = new Date()
  if (!promo.is_active) return { key: 'inactive', label: 'Nonaktif', tone: 'gray' }
  if (new Date(promo.valid_until) < now) return { key: 'expired', label: 'Kedaluwarsa', tone: 'red' }
  if (new Date(promo.valid_from) > now) return { key: 'other', label: 'Belum Mulai', tone: 'amber' }
  if (promo.max_usage !== null && promo.used_count >= promo.max_usage) return { key: 'other', label: 'Kuota Habis', tone: 'amber' }
  return { key: 'active', label: 'Aktif', tone: 'green' }
}

// ── Pencarian & filter ──────────────────────────────────────────────
const searchQuery  = ref('')
const statusFilter = ref('all')
const statusFilters = [
  { key: 'all',      label: 'Semua' },
  { key: 'active',   label: 'Aktif' },
  { key: 'inactive', label: 'Nonaktif' },
  { key: 'expired',  label: 'Kedaluwarsa' },
  { key: 'other',    label: 'Lainnya' },
]
const filteredPromos = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  return promos.value.filter((p) => {
    const hit = !q || p.code.toLowerCase().includes(q) || (p.description || '').toLowerCase().includes(q)
    return hit && (statusFilter.value === 'all' || statusInfo(p).key === statusFilter.value)
  })
})
const resetFilters = () => { searchQuery.value = ''; statusFilter.value = 'all' }

// ── Ringkasan ───────────────────────────────────────────────────────
const totalPromos      = computed(() => promos.value.length)
const activePromoCount = computed(() => promos.value.filter((p) => statusInfo(p).key === 'active').length)
const totalUsage       = computed(() => promos.value.reduce((a, p) => a + (p.used_count || 0), 0))

// ── Format ──────────────────────────────────────────────────────────
const formatPrice = (p) =>
  new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(p || 0)
const formatDateShort = (iso) =>
  new Date(iso).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: '2-digit' })
const formatDiscount = (promo) =>
  promo.discount_type === 'percentage' ? `${promo.discount_value}%` : formatPrice(promo.discount_value)

// ISO <-> value input datetime-local ("YYYY-MM-DDTHH:mm")
const toDatetimeLocal = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// ── Form ────────────────────────────────────────────────────────────
const showModal = ref(false)
const editingId = ref(null)
const isSaving  = ref(false)
const formError = ref('')

const discountTypeOptions = [
  { value: 'percentage', label: 'Persen (%)' },
  { value: 'fixed',      label: 'Nominal (Rp)' },
]

// Promo baru: default berlaku mulai sekarang selama 30 hari
const emptyForm = () => {
  const now = new Date()
  const end = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000)
  return {
    code: '',
    description: '',
    discount_type: 'percentage',
    discount_value: null,
    max_discount_amount: null,
    min_purchase: 0,
    max_usage: null,
    valid_from: toDatetimeLocal(now.toISOString()),
    valid_until: toDatetimeLocal(end.toISOString()),
    is_active: true,
  }
}
const form = ref(emptyForm())

// ── Fetch ───────────────────────────────────────────────────────────
const fetchPromos = async () => {
  isLoading.value = true
  loadError.value = false
  try {
    const { data } = await apiClient.get('/promotions/')
    promos.value = Array.isArray(data) ? data : data.results || []
  } catch {
    loadError.value = true
  } finally {
    isLoading.value = false
  }
}
onMounted(fetchPromos)

// ── Toggle cepat dari badge ─────────────────────────────────────────
const toggleActive = async (promo) => {
  if (togglingId.value === promo.id) return // cegah double-klik
  togglingId.value = promo.id
  try {
    const { data } = await apiClient.patch(`/promotions/${promo.id}/`, { is_active: !promo.is_active })
    const idx = promos.value.findIndex((p) => p.id === promo.id)
    if (idx > -1) promos.value[idx] = data
    toast.success(data.is_active ? 'Promo diaktifkan' : 'Promo dinonaktifkan')
  } catch {
    toast.error('Gagal mengubah status promo')
  } finally {
    togglingId.value = null
  }
}

// ── Modal ───────────────────────────────────────────────────────────
const openCreateModal = () => {
  editingId.value = null
  form.value = emptyForm()
  formError.value = ''
  showModal.value = true
}

const openEditModal = (promo) => {
  editingId.value = promo.id
  form.value = {
    code: promo.code,
    description: promo.description || '',
    discount_type: promo.discount_type,
    discount_value: Number(promo.discount_value),
    max_discount_amount: promo.max_discount_amount !== null ? Number(promo.max_discount_amount) : null,
    min_purchase: Number(promo.min_purchase),
    max_usage: promo.max_usage,
    valid_from: toDatetimeLocal(promo.valid_from),
    valid_until: toDatetimeLocal(promo.valid_until),
    is_active: promo.is_active,
  }
  formError.value = ''
  showModal.value = true
}

const closeModal = () => { showModal.value = false }

// ── Submit ──────────────────────────────────────────────────────────
const submitForm = async () => {
  formError.value = ''
  const f = form.value

  if (!f.code.trim()) return (formError.value = 'Kode promo wajib diisi')
  if (!f.discount_value || f.discount_value <= 0) return (formError.value = 'Nilai diskon harus lebih dari 0')
  if (f.discount_type === 'percentage' && f.discount_value > 100) return (formError.value = 'Persentase diskon maksimal 100%')
  if (!f.valid_from || !f.valid_until) return (formError.value = 'Tanggal berlaku wajib diisi')
  if (new Date(f.valid_from) >= new Date(f.valid_until)) return (formError.value = 'Tanggal "Berlaku Sampai" harus setelah "Berlaku Dari"')

  const payload = {
    code:                f.code.trim().toUpperCase(),
    description:         f.description,
    discount_type:       f.discount_type,
    discount_value:      f.discount_value,
    max_discount_amount: f.discount_type === 'percentage' ? f.max_discount_amount || null : null,
    min_purchase:        f.min_purchase || 0,
    max_usage:           f.max_usage || null,
    valid_from:          new Date(f.valid_from).toISOString(),
    valid_until:         new Date(f.valid_until).toISOString(),
    is_active:           f.is_active,
  }

  isSaving.value = true
  try {
    if (editingId.value) {
      const { data } = await apiClient.patch(`/promotions/${editingId.value}/`, payload)
      const idx = promos.value.findIndex((p) => p.id === editingId.value)
      if (idx > -1) promos.value[idx] = data
      toast.success('Promo berhasil diperbarui')
    } else {
      const { data } = await apiClient.post('/promotions/', payload)
      promos.value.unshift(data)
      toast.success('Promo berhasil dibuat')
    }
    showModal.value = false
  } catch (err) {
    const errData = err.response?.data
    if (errData && typeof errData === 'object') {
      const firstKey = Object.keys(errData)[0]
      const firstMsg = Array.isArray(errData[firstKey]) ? errData[firstKey][0] : errData[firstKey]
      formError.value = firstKey === 'code' ? `Kode: ${firstMsg}` : firstMsg || 'Gagal menyimpan promo'
    } else {
      formError.value = 'Gagal menyimpan promo'
    }
  } finally {
    isSaving.value = false
  }
}

// ── Hapus ───────────────────────────────────────────────────────────
const deletePromo = async (promo) => {
  const ok = await ask({
    title: 'Hapus promo?',
    message: `Kode "${promo.code}" akan dihapus permanen. Tindakan ini tidak bisa dibatalkan.`,
    confirmText: 'Ya, hapus',
    danger: true,
  })
  if (!ok) return
  try {
    await apiClient.delete(`/promotions/${promo.id}/`)
    promos.value = promos.value.filter((p) => p.id !== promo.id)
    toast.success('Promo dihapus')
  } catch {
    toast.error('Gagal menghapus promo')
  }
}
</script>

<style scoped>
.pr-form { display: flex; flex-direction: column; gap: 1rem; }

.pr-code { font-size: 0.875rem; font-weight: 700; letter-spacing: 0.03em; color: var(--text); }
.pr-desc { margin: 0.2rem 0 0; font-size: 0.7rem; color: var(--text-faint); font-family: var(--font-body); }
.pr-discount { font-size: 0.875rem; font-weight: 700; color: var(--accent-text); }
.pr-faint { color: var(--text-faint); }
.pr-period { white-space: nowrap; }
.pr-stack-right { display: flex; flex-direction: column; }
.pr-actions { display: flex; justify-content: flex-end; gap: 0.4rem; }

.pr-skeletons { display: flex; flex-direction: column; }
.pr-skel-row { display: flex; align-items: center; gap: 1.5rem; padding: 1.1rem 1.25rem; border-bottom: 1px solid var(--border); }
.pr-skel-row:last-child { border-bottom: none; }

@media (max-width: 720px) {
  .pr-new { width: 100%; }
  .adm-header-actions { width: 100%; }
  .pr-period { white-space: normal; text-align: right; }
  .pr-stack-right { align-items: flex-end; }
  .pr-actions { width: 100%; justify-content: flex-end; }
}
@media (max-width: 640px) {
  .adm-search { max-width: none; flex-basis: 100%; }
}
</style>