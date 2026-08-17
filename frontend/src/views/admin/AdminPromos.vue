<template>
  <div class="dashboard-root">

    <!-- ── HEADER ──────────────────────────────────────────────────── -->
    <div class="dash-header">
      <div>
        <p class="dash-eyebrow">Masashimura · Admin</p>
        <h1 class="dash-title">Kelola Promo</h1>
        <p class="dash-sub">Kode diskon buat customer web & POS</p>
      </div>
      <button class="new-promo-btn" @click="openCreateModal">
        <Plus :size="14" /> Buat Promo
      </button>
    </div>

    <!-- ── STAT CARDS ──────────────────────────────────────────────── -->
    <div class="stats-grid">
      <div class="stat-card">
        <span class="stat-icon-wrap ic-red"><Tag :size="15" /></span>
        <div>
          <p class="stat-value">{{ totalPromos }}</p>
          <p class="stat-label">Total Promo</p>
        </div>
      </div>
      <div class="stat-card">
        <span class="stat-icon-wrap ic-green"><CheckCircle2 :size="15" /></span>
        <div>
          <p class="stat-value">{{ activePromoCount }}</p>
          <p class="stat-label">Sedang Aktif</p>
        </div>
      </div>
      <div class="stat-card">
        <span class="stat-icon-wrap ic-amber"><Ticket :size="15" /></span>
        <div>
          <p class="stat-value">{{ totalUsage.toLocaleString('id-ID') }}</p>
          <p class="stat-label">Total Pemakaian</p>
        </div>
      </div>
    </div>

    <!-- ── TOOLBAR: SEARCH + FILTER ────────────────────────────────── -->
    <div v-if="!isLoading && !loadError && promos.length > 0" class="table-toolbar">
      <div class="search-box">
        <Search :size="14" class="search-icon" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Cari kode promo..."
          class="search-input"
        />
      </div>
      <div class="filter-chips">
        <button
          v-for="f in statusFilters"
          :key="f.key"
          class="chip-btn"
          :class="{ active: statusFilter === f.key }"
          @click="statusFilter = f.key"
        >
          {{ f.label }}
        </button>
      </div>
    </div>

    <!-- ── ERROR ───────────────────────────────────────────────────── -->
    <div v-if="!isLoading && loadError" class="table-card">
      <div class="empty-state">
        <div class="empty-icon">⚠️</div>
        <p class="empty-text">Gagal memuat data promo</p>
        <button class="retry-btn" @click="fetchPromos">Coba Lagi</button>
      </div>
    </div>

    <!-- ── EMPTY (belum ada promo sama sekali) ───────────────────────── -->
    <div v-else-if="!isLoading && promos.length === 0" class="table-card">
      <div class="empty-state">
        <div class="empty-icon">🏷️</div>
        <p class="empty-text">Belum ada kode promo</p>
        <p class="empty-hint">Klik "Buat Promo" buat bikin yang pertama</p>
      </div>
    </div>

    <!-- ── TABLE ───────────────────────────────────────────────────── -->
    <div v-else-if="!isLoading" class="table-card">
      <table v-if="filteredPromos.length" class="promo-table">
        <thead>
          <tr>
            <th>Kode</th>
            <th>Diskon</th>
            <th>Min. Belanja</th>
            <th>Kuota</th>
            <th>Berlaku</th>
            <th>Status</th>
            <th class="col-aksi">Aksi</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="promo in filteredPromos" :key="promo.id">
            <td>
              <span class="promo-code">{{ promo.code }}</span>
              <p v-if="promo.description" class="promo-desc">{{ promo.description }}</p>
            </td>
            <td>
              <span class="promo-discount">{{ formatDiscount(promo) }}</span>
              <p v-if="promo.discount_type === 'percentage' && promo.max_discount_amount" class="promo-desc">
                Maks {{ formatPrice(promo.max_discount_amount) }}
              </p>
            </td>
            <td class="mono-cell">{{ formatPrice(promo.min_purchase) }}</td>
            <td class="mono-cell">
              {{ promo.used_count }}<span v-if="promo.max_usage !== null">/{{ promo.max_usage }}</span>
              <span v-else class="text-dim"> / ∞</span>
            </td>
            <td class="mono-cell period-cell">
              {{ formatDateShort(promo.valid_from) }} – {{ formatDateShort(promo.valid_until) }}
            </td>
            <td>
              <button
                class="status-badge"
                :class="statusClass(promo)"
                @click="toggleActive(promo)"
              >
                {{ statusLabel(promo) }}
              </button>
            </td>
            <td class="col-aksi">
              <div class="row-actions">
                <button class="icon-btn" title="Edit" @click="openEditModal(promo)">
                  <Pencil :size="13" />
                </button>
                <button class="icon-btn icon-btn-danger" title="Hapus" @click="deletePromo(promo)">
                  <Trash2 :size="13" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Filter tidak menemukan hasil -->
      <div v-else class="empty-state">
        <div class="empty-icon">🔍</div>
        <p class="empty-text">Tidak ada promo yang cocok</p>
        <p class="empty-hint">Coba ubah kata kunci pencarian atau filter status</p>
        <button class="retry-btn" @click="resetFilters">Reset Filter</button>
      </div>
    </div>

    <!-- ── MODAL CREATE/EDIT ─────────────────────────────────────── -->
    <transition
      enter-active-class="modal-enter-active" enter-from-class="modal-enter-from"
      leave-active-class="modal-leave-active" leave-to-class="modal-leave-to"
    >
      <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
        <div class="modal-box">
          <div class="modal-head">
            <h2 class="modal-title">{{ editingId ? 'Edit Promo' : 'Buat Promo Baru' }}</h2>
            <button class="modal-close-btn" @click="closeModal"><X :size="15" /></button>
          </div>

          <form class="modal-form" @submit.prevent="submitForm">
            <div class="field">
              <label class="field-label">Kode Promo</label>
              <input
                v-model="form.code"
                @input="form.code = form.code.toUpperCase()"
                type="text"
                class="form-input mono"
                placeholder="MERDEKA17"
                required
              />
            </div>

            <div class="field">
              <label class="field-label">Deskripsi <span class="field-optional">(opsional)</span></label>
              <input v-model="form.description" type="text" class="form-input" placeholder="Diskon spesial 17 Agustus" />
            </div>

            <div class="field-row">
              <div class="field">
                <label class="field-label">Tipe Diskon</label>
                <div class="custom-select" ref="discountTypeDropdownRef">
                  <button
                    type="button"
                    class="form-input custom-select-trigger"
                    @click="discountTypeOpen = !discountTypeOpen"
                  >
                    <span>{{ discountTypeLabel }}</span>
                    <ChevronDown :size="14" class="custom-select-chevron" :class="{ 'is-open': discountTypeOpen }" />
                  </button>
                  <div v-if="discountTypeOpen" class="custom-select-panel">
                    <button
                      type="button"
                      v-for="opt in discountTypeOptions"
                      :key="opt.value"
                      class="custom-select-option"
                      :class="{ 'is-selected': form.discount_type === opt.value }"
                      @click="selectDiscountType(opt.value)"
                    >
                      <span>{{ opt.label }}</span>
                      <Check v-if="form.discount_type === opt.value" :size="13" />
                    </button>
                  </div>
                </div>
              </div>
              <div class="field">
                <label class="field-label">{{ form.discount_type === 'percentage' ? 'Nilai (%)' : 'Nilai (Rp)' }}</label>
                <input
                  v-model.number="form.discount_value"
                  type="number" min="0"
                  :max="form.discount_type === 'percentage' ? 100 : undefined"
                  class="form-input mono"
                  required
                />
              </div>
            </div>

            <div v-if="form.discount_type === 'percentage'" class="field">
              <label class="field-label">Cap Maksimal Diskon (Rp) <span class="field-optional">(opsional)</span></label>
              <input v-model.number="form.max_discount_amount" type="number" min="0" class="form-input mono" placeholder="Kosongkan = tanpa batas" />
            </div>

            <div class="field-row">
              <div class="field">
                <label class="field-label">Minimal Belanja (Rp)</label>
                <input v-model.number="form.min_purchase" type="number" min="0" class="form-input mono" />
              </div>
              <div class="field">
                <label class="field-label">Kuota Pemakaian <span class="field-optional">(opsional)</span></label>
                <input v-model.number="form.max_usage" type="number" min="1" class="form-input mono" placeholder="Tanpa batas" />
              </div>
            </div>

            <div class="field-row">
              <div class="field">
                <label class="field-label">Berlaku Dari</label>
                <input v-model="form.valid_from" type="datetime-local" class="form-input mono" required />
              </div>
              <div class="field">
                <label class="field-label">Berlaku Sampai</label>
                <input v-model="form.valid_until" type="datetime-local" class="form-input mono" required />
              </div>
            </div>

            <label class="checkbox-row">
              <input type="checkbox" v-model="form.is_active" />
              <span>Aktifkan promo ini sekarang</span>
            </label>

            <p v-if="formError" class="form-error">{{ formError }}</p>

            <div class="modal-actions">
              <button type="button" class="btn-secondary" @click="closeModal">Batal</button>
              <button type="submit" class="btn-primary" :disabled="isSaving">
                {{ editingId ? 'Simpan Perubahan' : 'Buat Promo' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { Plus, Pencil, Trash2, X, ChevronDown, Check, Tag, CheckCircle2, Ticket, Search } from 'lucide-vue-next';
import apiClient from '@/api/client';
import { toast } from 'vue-sonner';

const promos      = ref([]);
const isLoading    = ref(true);
const loadError    = ref(false);
const togglingId   = ref(null);

// ── Pencarian & filter status ───────────────────────────────────────
const searchQuery  = ref('');
const statusFilter = ref('all');
const statusFilters = [
  { key: 'all',      label: 'Semua' },
  { key: 'active',    label: 'Aktif' },
  { key: 'inactive',  label: 'Nonaktif' },
  { key: 'expired',   label: 'Kedaluwarsa' },
  { key: 'other',     label: 'Lainnya' },
];
const filteredPromos = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  return promos.value.filter((p) => {
    const matchesSearch = !q || p.code.toLowerCase().includes(q) || (p.description || '').toLowerCase().includes(q);
    if (!matchesSearch) return false;
    if (statusFilter.value === 'all') return true;
    const cls = statusClass(p);
    if (statusFilter.value === 'active')   return cls === 'badge-green';
    if (statusFilter.value === 'inactive') return cls === 'badge-gray';
    if (statusFilter.value === 'expired')  return cls === 'badge-red';
    if (statusFilter.value === 'other')    return cls === 'badge-amber';
    return true;
  });
});
const resetFilters = () => { searchQuery.value = ''; statusFilter.value = 'all'; };

// ── Stat ringkasan (derived, tanpa API baru) ────────────────────────
const totalPromos      = computed(() => promos.value.length);
const activePromoCount = computed(() => promos.value.filter((p) => statusClass(p) === 'badge-green').length);
const totalUsage       = computed(() => promos.value.reduce((a, p) => a + (p.used_count || 0), 0));

const showModal  = ref(false);
const editingId  = ref(null);
const isSaving   = ref(false);
const formError  = ref('');

const emptyForm = () => ({
  code: '',
  description: '',
  discount_type: 'percentage',
  discount_value: null,
  max_discount_amount: null,
  min_purchase: 0,
  max_usage: null,
  valid_from: '',
  valid_until: '',
  is_active: true,
});
const form = ref(emptyForm());

// ── Custom dropdown "Tipe Diskon" (ganti native <select> yang stylingnya
// gak konsisten antar browser) ──────────────────────────────────────
const discountTypeOptions = [
  { value: 'percentage', label: 'Persentase (%)' },
  { value: 'fixed',      label: 'Nominal Tetap (Rp)' },
];
const discountTypeOpen         = ref(false);
const discountTypeDropdownRef  = ref(null);
const discountTypeLabel = computed(() =>
  discountTypeOptions.find((o) => o.value === form.value.discount_type)?.label || ''
);
const selectDiscountType = (value) => {
  form.value.discount_type = value;
  discountTypeOpen.value = false;
};
const handleClickOutsideDropdown = (e) => {
  if (discountTypeDropdownRef.value && !discountTypeDropdownRef.value.contains(e.target)) {
    discountTypeOpen.value = false;
  }
};
onMounted(() => document.addEventListener('mousedown', handleClickOutsideDropdown));
onUnmounted(() => document.removeEventListener('mousedown', handleClickOutsideDropdown));

// ── Format helpers ────────────────────────────────────────────────
const formatPrice = (p) =>
  new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(p || 0);

const formatDateShort = (iso) =>
  new Date(iso).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: '2-digit' });

const formatDiscount = (promo) =>
  promo.discount_type === 'percentage' ? `${promo.discount_value}%` : formatPrice(promo.discount_value);

// Konversi ISO <-> value input datetime-local (yang formatnya "YYYY-MM-DDTHH:mm")
const toDatetimeLocal = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
};

// ── Status badge (aktif / nonaktif / kedaluwarsa / kuota habis) ────
const statusInfo = (promo) => {
  const now = new Date();
  if (!promo.is_active) return { label: 'Nonaktif', cls: 'badge-gray' };
  if (new Date(promo.valid_until) < now) return { label: 'Kedaluwarsa', cls: 'badge-red' };
  if (new Date(promo.valid_from) > now) return { label: 'Belum Mulai', cls: 'badge-amber' };
  if (promo.max_usage !== null && promo.used_count >= promo.max_usage) return { label: 'Kuota Habis', cls: 'badge-amber' };
  return { label: 'Aktif', cls: 'badge-green' };
};
const statusLabel = (promo) => statusInfo(promo).label;
const statusClass = (promo) => statusInfo(promo).cls;

// ── Fetch ────────────────────────────────────────────────────────
const fetchPromos = async () => {
  isLoading.value = true;
  loadError.value = false;
  try {
    const { data } = await apiClient.get('/promotions/');
    promos.value = Array.isArray(data) ? data : (data.results || []);
  } catch (err) {
    loadError.value = true;
  } finally {
    isLoading.value = false;
  }
};
onMounted(fetchPromos);

// ── Toggle aktif/nonaktif cepat dari badge ──────────────────────────
const toggleActive = async (promo) => {
  if (togglingId.value === promo.id) return; // cegah double-klik nge-fire 2 request
  togglingId.value = promo.id;
  try {
    const { data } = await apiClient.patch(`/promotions/${promo.id}/`, { is_active: !promo.is_active });
    const idx = promos.value.findIndex((p) => p.id === promo.id);
    if (idx > -1) promos.value[idx] = data;
    toast.success(data.is_active ? 'Promo diaktifkan' : 'Promo dinonaktifkan');
  } catch (err) {
    toast.error('Gagal mengubah status promo');
  } finally {
    togglingId.value = null;
  }
};

// ── Modal ────────────────────────────────────────────────────────
const openCreateModal = () => {
  editingId.value = null;
  form.value = emptyForm();
  formError.value = '';
  showModal.value = true;
};

const openEditModal = (promo) => {
  editingId.value = promo.id;
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
  };
  formError.value = '';
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
  discountTypeOpen.value = false;
};

// ── Submit (create / update) ────────────────────────────────────
const submitForm = async () => {
  formError.value = '';

  if (!form.value.code.trim()) { formError.value = 'Kode promo wajib diisi'; return; }
  if (!form.value.discount_value || form.value.discount_value <= 0) { formError.value = 'Nilai diskon harus lebih dari 0'; return; }
  if (form.value.discount_type === 'percentage' && form.value.discount_value > 100) { formError.value = 'Persentase diskon maksimal 100%'; return; }
  if (!form.value.valid_from || !form.value.valid_until) { formError.value = 'Tanggal berlaku wajib diisi'; return; }
  if (new Date(form.value.valid_from) >= new Date(form.value.valid_until)) { formError.value = 'Tanggal "Berlaku Sampai" harus setelah "Berlaku Dari"'; return; }

  const payload = {
    code:                 form.value.code.trim().toUpperCase(),
    description:          form.value.description,
    discount_type:        form.value.discount_type,
    discount_value:       form.value.discount_value,
    max_discount_amount:  form.value.discount_type === 'percentage' ? (form.value.max_discount_amount || null) : null,
    min_purchase:         form.value.min_purchase || 0,
    max_usage:            form.value.max_usage || null,
    valid_from:           new Date(form.value.valid_from).toISOString(),
    valid_until:          new Date(form.value.valid_until).toISOString(),
    is_active:            form.value.is_active,
  };

  isSaving.value = true;
  try {
    if (editingId.value) {
      const { data } = await apiClient.patch(`/promotions/${editingId.value}/`, payload);
      const idx = promos.value.findIndex((p) => p.id === editingId.value);
      if (idx > -1) promos.value[idx] = data;
      toast.success('Promo berhasil diperbarui');
    } else {
      const { data } = await apiClient.post('/promotions/', payload);
      promos.value.unshift(data);
      toast.success('Promo berhasil dibuat');
    }
    showModal.value = false;
  } catch (err) {
    const errData = err.response?.data;
    if (errData && typeof errData === 'object') {
      const firstKey = Object.keys(errData)[0];
      const firstMsg = Array.isArray(errData[firstKey]) ? errData[firstKey][0] : errData[firstKey];
      formError.value = firstKey === 'code' ? `Kode: ${firstMsg}` : (firstMsg || 'Gagal menyimpan promo');
    } else {
      formError.value = 'Gagal menyimpan promo';
    }
  } finally {
    isSaving.value = false;
  }
};

// ── Delete ───────────────────────────────────────────────────────
const deletePromo = async (promo) => {
  if (!confirm(`Hapus promo "${promo.code}"? Aksi ini tidak bisa dibatalkan.`)) return;
  try {
    await apiClient.delete(`/promotions/${promo.id}/`);
    promos.value = promos.value.filter((p) => p.id !== promo.id);
    toast.success('Promo dihapus');
  } catch (err) {
    toast.error('Gagal menghapus promo');
  }
};
</script>

<style scoped>
.dashboard-root {
  --bg: #08080a;
  --surface: #0f0f10;
  --border: rgba(255,255,255,0.06);
  --border-strong: rgba(255,255,255,0.12);
  --text-dim: rgba(255,255,255,0.4);
  --text-faint: rgba(255,255,255,0.2);
  --accent: #dc2626;
  --accent-hover: #b91c1c;
  --green: #22c55e;
  --green-soft: #4ade80;
  --amber: #f59e0b;
  --amber-soft: #fbbf24;
  --red-soft: #f87171;
  --r-sm: 8px;
  --r-md: 12px;
  --r-lg: 16px;

  min-height: 100vh;
  background: var(--bg);
  color: #fff;
  font-family: 'Inter', sans-serif;
  padding: 2rem 2.5rem 3rem;
  max-width: 1280px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

/* ── Header ──────────────────────────────────────────────────────── */
.dash-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border);
}
.dash-eyebrow {
  font-family: 'Oswald', sans-serif;
  font-size: 0.62rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--accent);
  margin: 0 0 0.25rem;
}
.dash-title {
  font-family: 'Oswald', sans-serif;
  font-size: 1.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.02em;
  margin: 0 0 0.25rem;
}
.dash-sub { font-size: 0.78rem; color: var(--text-dim); margin: 0; }

.new-promo-btn {
  display: flex; align-items: center; gap: 0.4rem;
  padding: 0.7rem 1.25rem;
  background: var(--accent); border: none; border-radius: var(--r-md);
  color: #fff; font-family: 'Oswald', sans-serif;
  font-size: 0.72rem; letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: background 0.15s;
  flex-shrink: 0;
}
.new-promo-btn:hover { background: var(--accent-hover); }

/* ── Stat cards ──────────────────────────────────────────────────── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}
@media (max-width: 720px) { .stats-grid { grid-template-columns: 1fr; } }

.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 1.1rem 1.25rem;
  display: flex; align-items: center; gap: 0.85rem;
}
.stat-icon-wrap {
  width: 34px; height: 34px; border-radius: var(--r-sm);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.ic-red   { background: rgba(220,38,38,0.1);  color: #f87171; }
.ic-green { background: rgba(34,197,94,0.1);  color: var(--green-soft); }
.ic-amber { background: rgba(245,158,11,0.1); color: var(--amber-soft); }
.stat-value { font-family: monospace; font-size: 1.25rem; font-weight: 700; color: #fff; margin: 0 0 0.15rem; line-height: 1; }
.stat-label { font-family: 'Oswald', sans-serif; font-size: 0.6rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-dim); margin: 0; }

/* ── Toolbar: search + filter ─────────────────────────────────────── */
.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
}
.search-box {
  position: relative;
  flex: 1;
  min-width: 220px;
  max-width: 320px;
}
.search-icon {
  position: absolute; left: 0.8rem; top: 50%; transform: translateY(-50%);
  color: var(--text-faint); pointer-events: none;
}
.search-input {
  width: 100%;
  background: var(--surface);
  border: 1px solid var(--border-strong);
  border-radius: var(--r-md);
  padding: 0.6rem 0.9rem 0.6rem 2.15rem;
  color: #fff; font-size: 0.8rem; font-family: 'Inter', sans-serif;
  outline: none; transition: border-color 0.15s;
}
.search-input::placeholder { color: var(--text-faint); }
.search-input:focus { border-color: rgba(220,38,38,0.45); }

.filter-chips {
  display: flex; background: var(--surface);
  border: 1px solid var(--border); border-radius: var(--r-md);
  padding: 3px; gap: 2px; flex-wrap: wrap;
}
.chip-btn {
  padding: 0.42rem 0.8rem; border-radius: 8px; border: none; background: transparent;
  color: var(--text-faint);
  font-family: 'Oswald', sans-serif; font-size: 0.6rem;
  letter-spacing: 0.09em; text-transform: uppercase; cursor: pointer; transition: all 0.15s;
  white-space: nowrap;
}
.chip-btn:hover { color: rgba(255,255,255,0.65); }
.chip-btn.active { background: var(--accent); color: #fff; }

/* ── Table ───────────────────────────────────────────────────────── */
.table-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  overflow: hidden;
}
.promo-table { width: 100%; border-collapse: collapse; }
.promo-table thead th {
  text-align: left;
  padding: 0.9rem 1.25rem;
  font-family: 'Oswald', sans-serif;
  font-size: 0.6rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-faint);
  background: rgba(255,255,255,0.015);
  border-bottom: 1px solid var(--border);
}
.promo-table tbody td {
  padding: 0.9rem 1.25rem;
  font-size: 0.8rem;
  color: rgba(255,255,255,0.75);
  border-bottom: 1px solid rgba(255,255,255,0.03);
  vertical-align: middle;
}
.promo-table tbody tr { transition: background 0.12s; }
.promo-table tbody tr:hover { background: rgba(255,255,255,0.02); }
.promo-table tbody tr:last-child td { border-bottom: none; }
.mono-cell { font-family: monospace; font-size: 0.75rem; color: rgba(255,255,255,0.5); }
.period-cell { white-space: nowrap; }
.text-dim { color: var(--text-faint); }

.promo-code { font-family: monospace; font-weight: 700; font-size: 0.85rem; color: #fff; letter-spacing: 0.03em; }
.promo-desc { font-size: 0.68rem; color: rgba(255,255,255,0.3); margin: 0.2rem 0 0; }
.promo-discount { font-family: monospace; font-weight: 700; color: var(--accent); font-size: 0.85rem; }

.col-aksi { text-align: right; }
.row-actions { display: flex; justify-content: flex-end; gap: 0.4rem; }
.icon-btn {
  width: 28px; height: 28px; border-radius: 7px;
  background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.5);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all 0.15s;
}
.icon-btn:hover { background: rgba(255,255,255,0.1); color: #fff; }
.icon-btn-danger:hover { background: rgba(239,68,68,0.15); color: var(--red-soft); border-color: rgba(239,68,68,0.3); }

.status-badge {
  padding: 0.3rem 0.7rem; border-radius: 100px; border: 1px solid;
  font-family: 'Oswald', sans-serif; font-size: 0.6rem;
  letter-spacing: 0.08em; text-transform: uppercase;
  cursor: pointer; transition: opacity 0.15s; white-space: nowrap;
}
.status-badge:hover { opacity: 0.8; }
.status-badge:disabled { opacity: 0.5; cursor: not-allowed; }
.badge-green { background: rgba(34,197,94,0.1); border-color: rgba(34,197,94,0.3); color: var(--green-soft); }
.badge-gray  { background: rgba(255,255,255,0.05); border-color: rgba(255,255,255,0.12); color: rgba(255,255,255,0.4); }
.badge-red   { background: rgba(239,68,68,0.1); border-color: rgba(239,68,68,0.3); color: var(--red-soft); }
.badge-amber { background: rgba(217,119,6,0.1); border-color: rgba(217,119,6,0.3); color: var(--amber-soft); }

/* ── Empty / error state ─────────────────────────────────────────── */
.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 0.6rem; padding: 4rem 2rem; text-align: center;
}
.empty-icon { font-size: 2rem; }
.empty-text { color: rgba(255,255,255,0.4); margin: 0; font-size: 0.9rem; }
.empty-hint { color: var(--text-faint); margin: 0; font-size: 0.75rem; }
.retry-btn {
  margin-top: 0.5rem; padding: 0.5rem 1.25rem; border-radius: 8px;
  background: var(--accent); border: none; color: #fff;
  font-family: 'Oswald', sans-serif; font-size: 0.68rem;
  letter-spacing: 0.1em; text-transform: uppercase; cursor: pointer;
}
.retry-btn:hover { background: var(--accent-hover); }

/* ── Modal ───────────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed; inset: 0; z-index: 70;
  background: rgba(0,0,0,0.8); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; padding: 1rem;
}
.modal-enter-active { transition: all 0.2s ease; }
.modal-enter-from   { opacity: 0; transform: scale(0.96); }
.modal-leave-active { transition: all 0.15s ease; }
.modal-leave-to     { opacity: 0; transform: scale(0.96); }

.modal-box {
  background: var(--surface); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 18px; width: 100%; max-width: 480px;
  max-height: 90vh; overflow-y: auto;
}
.modal-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 1.4rem 1.5rem 1rem;
  border-bottom: 1px solid var(--border);
}
.modal-title {
  font-family: 'Oswald', sans-serif; font-size: 1rem; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.05em; margin: 0;
}
.modal-close-btn {
  width: 28px; height: 28px; border-radius: 7px;
  background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.4); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.modal-close-btn:hover { background: rgba(255,255,255,0.1); color: #fff; }

.modal-form { padding: 1.25rem 1.5rem 1.5rem; display: flex; flex-direction: column; gap: 1rem; }

.field { display: flex; flex-direction: column; gap: 0.4rem; }
.field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.field-label {
  font-family: 'Oswald', sans-serif; font-size: 0.6rem;
  letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-dim);
}
.field-optional { color: var(--text-faint); text-transform: none; letter-spacing: normal; }

.form-input {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1);
  border-radius: 9px; padding: 0.6rem 0.8rem;
  color: #fff; font-size: 0.82rem; font-family: 'Inter', sans-serif;
  outline: none; transition: border-color 0.15s; width: 100%;
  color-scheme: dark; /* bikin date/time picker bawaan browser jadi gelap */
}
.form-input.mono { font-family: monospace; }
.form-input:focus { border-color: rgba(220,38,38,0.5); }
.form-input::placeholder { color: rgba(255,255,255,0.2); }

/* Hilangin tombol naik/turun (spinner) bawaan browser di input angka */
.form-input[type="number"]::-webkit-inner-spin-button,
.form-input[type="number"]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
.form-input[type="number"] { -moz-appearance: textfield; }

/* ── Custom dropdown "Tipe Diskon" ──────────────────────────────── */
.custom-select { position: relative; }
.custom-select-trigger {
  display: flex; align-items: center; justify-content: space-between;
  cursor: pointer; text-align: left;
}
.custom-select-chevron { color: rgba(255,255,255,0.35); transition: transform 0.15s; flex-shrink: 0; }
.custom-select-chevron.is-open { transform: rotate(180deg); }

.custom-select-panel {
  position: absolute; top: calc(100% + 6px); left: 0; right: 0; z-index: 20;
  background: #161616; border: 1px solid rgba(255,255,255,0.1);
  border-radius: 9px; padding: 0.3rem;
  box-shadow: 0 8px 24px rgba(0,0,0,0.5);
}
.custom-select-option {
  width: 100%; display: flex; align-items: center; justify-content: space-between;
  padding: 0.55rem 0.65rem; border-radius: 6px; border: none;
  background: transparent; color: rgba(255,255,255,0.7);
  font-size: 0.8rem; font-family: 'Inter', sans-serif; text-align: left;
  cursor: pointer; transition: background 0.12s;
}
.custom-select-option:hover { background: rgba(255,255,255,0.06); color: #fff; }
.custom-select-option.is-selected { color: var(--red-soft); }
.custom-select-option.is-selected svg { color: var(--red-soft); flex-shrink: 0; }

.checkbox-row {
  display: flex; align-items: center; gap: 0.55rem;
  font-size: 0.78rem; color: rgba(255,255,255,0.6); cursor: pointer;
}
.checkbox-row input[type="checkbox"] { width: 15px; height: 15px; accent-color: var(--accent); cursor: pointer; }

.form-error {
  font-size: 0.75rem; color: var(--red-soft); margin: 0;
  background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.2);
  padding: 0.6rem 0.8rem; border-radius: 8px;
}

.modal-actions { display: flex; justify-content: flex-end; gap: 0.6rem; margin-top: 0.25rem; }
.btn-secondary, .btn-primary {
  padding: 0.65rem 1.25rem; border-radius: 9px; border: none;
  font-family: 'Oswald', sans-serif; font-size: 0.7rem;
  letter-spacing: 0.08em; text-transform: uppercase; cursor: pointer;
  transition: all 0.15s;
}
.btn-secondary { background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.5); }
.btn-secondary:hover { background: rgba(255,255,255,0.1); color: #fff; }
.btn-primary { background: var(--accent); color: #fff; }
.btn-primary:hover:not(:disabled) { background: var(--accent-hover); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

@media (max-width: 640px) {
  .dashboard-root { padding: 1.25rem 1rem 2rem; }
  .dash-header { flex-direction: column; }
  .new-promo-btn { width: 100%; justify-content: center; }
  .table-toolbar { flex-direction: column; align-items: stretch; }
  .search-box { max-width: none; }
  .field-row { grid-template-columns: 1fr; }
  .promo-table { font-size: 0.72rem; }
  .period-cell { white-space: normal; }
}
</style>