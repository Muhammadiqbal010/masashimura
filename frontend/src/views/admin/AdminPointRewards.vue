<template>
  <div class="dashboard-root">

    <!-- ── HEADER ──────────────────────────────────────────────────── -->
    <div class="dash-header">
      <div>
        <p class="dash-eyebrow">Masashimura · Admin</p>
        <h1 class="dash-title">Kelola Reward Poin</h1>
        <p class="dash-sub">Katalog menu yang bisa ditukar pakai poin loyalty customer</p>
      </div>
      <button class="new-promo-btn" @click="openCreateModal">
        <Plus :size="14" /> Tambah Reward
      </button>
    </div>

    <!-- ── STAT CARDS ──────────────────────────────────────────────── -->
    <div class="stats-grid">
      <div class="stat-card">
        <span class="stat-icon-wrap ic-red"><Gift :size="15" /></span>
        <div>
          <p class="stat-value">{{ totalRewards }}</p>
          <p class="stat-label">Total Reward</p>
        </div>
      </div>
      <div class="stat-card">
        <span class="stat-icon-wrap ic-green"><CheckCircle2 :size="15" /></span>
        <div>
          <p class="stat-value">{{ activeRewards }}</p>
          <p class="stat-label">Reward Aktif</p>
        </div>
      </div>
      <div class="stat-card">
        <span class="stat-icon-wrap ic-amber"><Coins :size="15" /></span>
        <div>
          <p class="stat-value">{{ avgPointCost.toLocaleString('id-ID') }}</p>
          <p class="stat-label">Rata-rata Biaya Poin</p>
        </div>
      </div>
    </div>

    <!-- ── PENGATURAN RATE POIN MASUK ──────────────────────────────── -->
    <div class="settings-card">
      <div class="settings-info">
        <span class="settings-icon-wrap"><Settings2 :size="15" /></span>
        <div>
          <p class="settings-label">Rate Poin Masuk</p>
          <p class="settings-hint">Belanja Rp berapa yang setara 1 poin? (redeem-nya diatur per-menu di tabel bawah)</p>
        </div>
      </div>
      <div class="settings-input-row">
        <span class="settings-prefix">Rp</span>
        <input
          v-model.number="rupiahPerPoint"
          type="number" min="1" step="1000"
          class="form-input mono settings-input"
        />
        <span class="settings-suffix">= 1 poin</span>
        <button
          class="btn-primary settings-save-btn"
          :disabled="isSavingSettings || rupiahPerPoint === savedRupiahPerPoint"
          @click="saveLoyaltySettings"
        >
          {{ isSavingSettings ? 'Menyimpan...' : 'Simpan' }}
        </button>
      </div>
    </div>

    <!-- ── TOOLBAR: SEARCH + FILTER ────────────────────────────────── -->
    <div v-if="!isLoading && !loadError && rewards.length > 0" class="table-toolbar">
      <div class="search-box">
        <Search :size="14" class="search-icon" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Cari nama menu..."
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
        <p class="empty-text">Gagal memuat data reward poin</p>
        <button class="retry-btn" @click="fetchRewards">Coba Lagi</button>
      </div>
    </div>

    <!-- ── EMPTY (belum ada reward sama sekali) ─────────────────────── -->
    <div v-else-if="!isLoading && rewards.length === 0" class="table-card">
      <div class="empty-state">
        <div class="empty-icon">🎁</div>
        <p class="empty-text">Belum ada reward poin</p>
        <p class="empty-hint">Klik "Tambah Reward" buat bikin yang pertama — pilih menu HPP kecil biar aman</p>
      </div>
    </div>

    <!-- ── TABLE ───────────────────────────────────────────────────── -->
    <div v-else-if="!isLoading" class="table-card">
      <table v-if="filteredRewards.length" class="promo-table">
        <thead>
          <tr>
            <th>Menu</th>
            <th>Harga Menu</th>
            <th>Biaya Poin</th>
            <th>Status</th>
            <th class="col-aksi">Aksi</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="reward in filteredRewards" :key="reward.id">
            <td>
              <span class="promo-code">{{ reward.menu_name }}</span>
            </td>
            <td class="mono-cell">{{ formatPrice(reward.menu_price) }}</td>
            <td>
              <span class="promo-discount">{{ reward.point_cost.toLocaleString('id-ID') }} poin</span>
            </td>
            <td>
              <button
                class="status-badge"
                :class="reward.is_active ? 'badge-green' : 'badge-gray'"
                :disabled="togglingId === reward.id"
                @click="toggleActive(reward)"
              >
                {{ reward.is_active ? 'Aktif' : 'Nonaktif' }}
              </button>
            </td>
            <td class="col-aksi">
              <div class="row-actions">
                <button class="icon-btn" title="Edit" @click="openEditModal(reward)">
                  <Pencil :size="13" />
                </button>
                <button class="icon-btn icon-btn-danger" title="Hapus" @click="deleteReward(reward)">
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
        <p class="empty-text">Tidak ada reward yang cocok</p>
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
            <h2 class="modal-title">{{ editingId ? 'Edit Reward' : 'Tambah Reward Baru' }}</h2>
            <button class="modal-close-btn" @click="closeModal"><X :size="15" /></button>
          </div>

          <form class="modal-form" @submit.prevent="submitForm">
            <div class="field">
              <label class="field-label">Menu</label>
              <div class="custom-select" ref="menuDropdownRef">
                <button
                  type="button"
                  class="form-input custom-select-trigger"
                  @click="menuOpen = !menuOpen"
                >
                  <span>{{ selectedMenuLabel }}</span>
                  <ChevronDown :size="14" class="custom-select-chevron" :class="{ 'is-open': menuOpen }" />
                </button>
                <div v-if="menuOpen" class="custom-select-panel">
                  <button
                    type="button"
                    v-for="menu in menus"
                    :key="menu.id"
                    class="custom-select-option"
                    :class="{ 'is-selected': form.menu === menu.id }"
                    @click="selectMenu(menu.id)"
                  >
                    <span>{{ menu.name }} — {{ formatPrice(menu.price) }}</span>
                    <Check v-if="form.menu === menu.id" :size="13" />
                  </button>
                </div>
              </div>
              <p class="field-hint">Pilih menu HPP kecil (minuman/side dish), hindari menu signature yang mahal</p>
            </div>

            <div class="field">
              <label class="field-label">Biaya Poin</label>
              <input
                v-model.number="form.point_cost"
                type="number" min="1"
                class="form-input mono"
                placeholder="cth: 500"
                required
              />
            </div>

            <label class="checkbox-row">
              <input type="checkbox" v-model="form.is_active" />
              <span>Aktifkan reward ini sekarang</span>
            </label>

            <p v-if="formError" class="form-error">{{ formError }}</p>

            <div class="modal-actions">
              <button type="button" class="btn-secondary" @click="closeModal">Batal</button>
              <button type="submit" class="btn-primary" :disabled="isSaving">
                {{ editingId ? 'Simpan Perubahan' : 'Tambah Reward' }}
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
import { Plus, Pencil, Trash2, X, ChevronDown, Check, Gift, CheckCircle2, Coins, Settings2, Search } from 'lucide-vue-next';
import { pointRewardAPI, loyaltySettingsAPI } from '@/api';
import { menuAPI } from '@/api';
import { toast } from 'vue-sonner';

const rewards    = ref([]);
const menus      = ref([]);
const isLoading  = ref(true);
const loadError  = ref(false);
const togglingId = ref(null);

// ── Pencarian & filter status ───────────────────────────────────────
const searchQuery  = ref('');
const statusFilter = ref('all');
const statusFilters = [
  { key: 'all',      label: 'Semua' },
  { key: 'active',   label: 'Aktif' },
  { key: 'inactive', label: 'Nonaktif' },
];
const filteredRewards = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  return rewards.value.filter((r) => {
    const matchesSearch = !q || r.menu_name.toLowerCase().includes(q);
    const matchesStatus =
      statusFilter.value === 'all' ? true :
      statusFilter.value === 'active' ? r.is_active : !r.is_active;
    return matchesSearch && matchesStatus;
  });
});
const resetFilters = () => { searchQuery.value = ''; statusFilter.value = 'all'; };

// ── Stat ringkasan (derived, tanpa API baru) ────────────────────────
const totalRewards  = computed(() => rewards.value.length);
const activeRewards = computed(() => rewards.value.filter((r) => r.is_active).length);
const avgPointCost  = computed(() => {
  if (!rewards.value.length) return 0;
  return Math.round(rewards.value.reduce((a, r) => a + r.point_cost, 0) / rewards.value.length);
});

// ── Pengaturan rate poin masuk ──────────────────────────────────────
const rupiahPerPoint      = ref(10000);
const savedRupiahPerPoint = ref(10000);
const isSavingSettings    = ref(false);

const fetchLoyaltySettings = async () => {
  try {
    const { data } = await loyaltySettingsAPI.get();
    rupiahPerPoint.value = data.rupiah_per_point ?? 10000;
    savedRupiahPerPoint.value = rupiahPerPoint.value;
  } catch (err) {
    console.error('Gagal memuat pengaturan poin', err);
  }
};

const saveLoyaltySettings = async () => {
  if (!rupiahPerPoint.value || rupiahPerPoint.value <= 0) {
    toast.error('Nominal harus lebih dari 0');
    return;
  }
  isSavingSettings.value = true;
  try {
    const { data } = await loyaltySettingsAPI.update({ rupiah_per_point: rupiahPerPoint.value });
    rupiahPerPoint.value = data.rupiah_per_point;
    savedRupiahPerPoint.value = data.rupiah_per_point;
    toast.success('Rate poin berhasil diperbarui');
  } catch (err) {
    toast.error('Gagal menyimpan pengaturan poin');
  } finally {
    isSavingSettings.value = false;
  }
};

const showModal = ref(false);
const editingId = ref(null);
const isSaving  = ref(false);
const formError = ref('');

const emptyForm = () => ({
  menu: null,
  point_cost: null,
  is_active: true,
});
const form = ref(emptyForm());

// ── Custom dropdown "Menu" ──────────────────────────────────────────
const menuOpen        = ref(false);
const menuDropdownRef = ref(null);
const selectedMenuLabel = computed(() => {
  const m = menus.value.find((x) => x.id === form.value.menu);
  return m ? `${m.name} — ${formatPrice(m.price)}` : 'Pilih menu...';
});
const selectMenu = (id) => {
  form.value.menu = id;
  menuOpen.value = false;
};
const handleClickOutsideDropdown = (e) => {
  if (menuDropdownRef.value && !menuDropdownRef.value.contains(e.target)) {
    menuOpen.value = false;
  }
};
onMounted(() => document.addEventListener('mousedown', handleClickOutsideDropdown));
onUnmounted(() => document.removeEventListener('mousedown', handleClickOutsideDropdown));

// ── Format helpers ────────────────────────────────────────────────
const formatPrice = (p) =>
  new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(p || 0);

// ── Fetch ────────────────────────────────────────────────────────
const fetchRewards = async () => {
  isLoading.value = true;
  loadError.value = false;
  try {
    const { data } = await pointRewardAPI.getAll();
    rewards.value = Array.isArray(data) ? data : (data.results || []);
  } catch (err) {
    loadError.value = true;
  } finally {
    isLoading.value = false;
  }
};

const fetchMenus = async () => {
  try {
    const { data } = await menuAPI.getAll();
    menus.value = Array.isArray(data) ? data : (data.results || []);
  } catch (err) {
    console.error('Gagal memuat daftar menu', err);
  }
};

onMounted(() => {
  fetchRewards();
  fetchMenus();
  fetchLoyaltySettings();
});

// ── Toggle aktif/nonaktif cepat dari badge ──────────────────────────
const toggleActive = async (reward) => {
  if (togglingId.value === reward.id) return;
  togglingId.value = reward.id;
  try {
    const { data } = await pointRewardAPI.update(reward.id, { is_active: !reward.is_active });
    const idx = rewards.value.findIndex((r) => r.id === reward.id);
    if (idx > -1) rewards.value[idx] = data;
    toast.success(data.is_active ? 'Reward diaktifkan' : 'Reward dinonaktifkan');
  } catch (err) {
    toast.error('Gagal mengubah status reward');
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

const openEditModal = (reward) => {
  editingId.value = reward.id;
  form.value = {
    menu: reward.menu,
    point_cost: reward.point_cost,
    is_active: reward.is_active,
  };
  formError.value = '';
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
  menuOpen.value = false;
};

// ── Submit (create / update) ────────────────────────────────────
const submitForm = async () => {
  formError.value = '';

  if (!form.value.menu) { formError.value = 'Menu wajib dipilih'; return; }
  if (!form.value.point_cost || form.value.point_cost <= 0) { formError.value = 'Biaya poin harus lebih dari 0'; return; }

  const payload = {
    menu:       form.value.menu,
    point_cost: form.value.point_cost,
    is_active:  form.value.is_active,
  };

  isSaving.value = true;
  try {
    if (editingId.value) {
      const { data } = await pointRewardAPI.update(editingId.value, payload);
      const idx = rewards.value.findIndex((r) => r.id === editingId.value);
      if (idx > -1) rewards.value[idx] = data;
      toast.success('Reward berhasil diperbarui');
    } else {
      const { data } = await pointRewardAPI.create(payload);
      rewards.value.unshift(data);
      toast.success('Reward berhasil ditambahkan');
    }
    showModal.value = false;
  } catch (err) {
    const errData = err.response?.data;
    if (errData && typeof errData === 'object') {
      const firstKey = Object.keys(errData)[0];
      const firstMsg = Array.isArray(errData[firstKey]) ? errData[firstKey][0] : errData[firstKey];
      formError.value = firstMsg || 'Gagal menyimpan reward';
    } else {
      formError.value = 'Gagal menyimpan reward';
    }
  } finally {
    isSaving.value = false;
  }
};

// ── Delete ───────────────────────────────────────────────────────
const deleteReward = async (reward) => {
  if (!confirm(`Hapus reward "${reward.menu_name}"? Aksi ini tidak bisa dibatalkan.`)) return;
  try {
    await pointRewardAPI.remove(reward.id);
    rewards.value = rewards.value.filter((r) => r.id !== reward.id);
    toast.success('Reward dihapus');
  } catch (err) {
    toast.error('Gagal menghapus reward');
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

/* ── Pengaturan rate poin ────────────────────────────────────────── */
.settings-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 1.1rem 1.25rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
}
.settings-info { display: flex; align-items: flex-start; gap: 0.75rem; }
.settings-icon-wrap {
  width: 30px; height: 30px; border-radius: var(--r-sm);
  background: rgba(255,255,255,0.05); color: var(--text-dim);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  margin-top: 0.1rem;
}
.settings-label {
  font-family: 'Oswald', sans-serif;
  font-size: 0.75rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #fff;
  margin: 0 0 0.2rem;
}
.settings-hint { font-size: 0.72rem; color: var(--text-dim); margin: 0; max-width: 420px; }

.settings-input-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}
.settings-prefix, .settings-suffix {
  font-family: monospace;
  font-size: 0.78rem;
  color: rgba(255,255,255,0.5);
  white-space: nowrap;
}
.settings-input {
  width: 110px;
  text-align: right;
}
.settings-save-btn { padding: 0.6rem 1.1rem; }

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
  padding: 3px; gap: 2px;
}
.chip-btn {
  padding: 0.42rem 0.85rem; border-radius: 8px; border: none; background: transparent;
  color: var(--text-faint);
  font-family: 'Oswald', sans-serif; font-size: 0.62rem;
  letter-spacing: 0.1em; text-transform: uppercase; cursor: pointer; transition: all 0.15s;
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

.promo-code { font-family: monospace; font-weight: 700; font-size: 0.85rem; color: #fff; letter-spacing: 0.03em; }
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
.field-label {
  font-family: 'Oswald', sans-serif; font-size: 0.6rem;
  letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-dim);
}
.field-hint { font-size: 0.68rem; color: var(--text-faint); margin: 0.1rem 0 0; }

.form-input {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1);
  border-radius: 9px; padding: 0.6rem 0.8rem;
  color: #fff; font-size: 0.82rem; font-family: 'Inter', sans-serif;
  outline: none; transition: border-color 0.15s; width: 100%;
  color-scheme: dark;
}
.form-input.mono { font-family: monospace; }
.form-input:focus { border-color: rgba(220,38,38,0.5); }
.form-input::placeholder { color: rgba(255,255,255,0.2); }

.form-input[type="number"]::-webkit-inner-spin-button,
.form-input[type="number"]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
.form-input[type="number"] { -moz-appearance: textfield; }

/* ── Custom dropdown "Menu" ──────────────────────────────────────── */
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
  max-height: 260px; overflow-y: auto;
  box-shadow: 0 8px 24px rgba(0,0,0,0.5);
}
.custom-select-option {
  width: 100%; display: flex; align-items: center; justify-content: space-between;
  gap: 0.5rem;
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
  .promo-table { font-size: 0.72rem; }
}
</style>