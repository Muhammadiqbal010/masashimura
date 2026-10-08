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
          id="rate-input"
          v-model.number="rupiahPerPoint"
          type="number" min="1" step="1000" inputmode="numeric"
          aria-label="Nominal belanja (Rupiah) yang setara 1 poin"
          class="form-input mono settings-input"
          @keydown.enter="saveLoyaltySettings"
        />
        <span class="settings-suffix">= 1 poin</span>
        <button
          class="btn-primary settings-save-btn"
          :disabled="isSavingSettings || !rupiahPerPoint || rupiahPerPoint === savedRupiahPerPoint"
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
          type="search"
          placeholder="Cari nama menu..."
          aria-label="Cari reward berdasarkan nama menu"
          class="search-input"
        />
      </div>
      <div class="filter-chips" role="group" aria-label="Filter status">
        <button
          v-for="f in statusFilters"
          :key="f.key"
          class="chip-btn"
          :class="{ active: statusFilter === f.key }"
          :aria-pressed="statusFilter === f.key"
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
            <td class="td-menu">
              <span class="promo-code">{{ reward.menu_name }}</span>
            </td>
            <td class="mono-cell td-price" data-label="Harga menu">{{ formatPrice(reward.menu_price) }}</td>
            <td class="td-cost" data-label="Biaya poin">
              <span class="promo-discount">{{ reward.point_cost.toLocaleString('id-ID') }} poin</span>
            </td>
            <td class="td-status">
              <button
                class="status-badge"
                :class="reward.is_active ? 'badge-green' : 'badge-gray'"
                :disabled="togglingId === reward.id"
                :aria-pressed="reward.is_active"
                :title="reward.is_active ? 'Klik untuk nonaktifkan' : 'Klik untuk aktifkan'"
                @click="toggleActive(reward)"
              >
                {{ reward.is_active ? 'Aktif' : 'Nonaktif' }}
              </button>
            </td>
            <td class="col-aksi td-actions">
              <div class="row-actions">
                <button class="icon-btn" title="Edit" :aria-label="`Edit reward ${reward.menu_name}`" @click="openEditModal(reward)">
                  <Pencil :size="14" />
                </button>
                <button class="icon-btn icon-btn-danger" title="Hapus" :aria-label="`Hapus reward ${reward.menu_name}`" @click="askDelete(reward)">
                  <Trash2 :size="14" />
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
        <div class="modal-box" role="dialog" aria-modal="true" aria-labelledby="reward-modal-title">
          <div class="modal-head">
            <h2 id="reward-modal-title" class="modal-title">{{ editingId ? 'Edit Reward' : 'Tambah Reward Baru' }}</h2>
            <button type="button" class="modal-close-btn" aria-label="Tutup" @click="closeModal"><X :size="15" /></button>
          </div>

          <form class="modal-form" @submit.prevent="submitForm">
            <div class="field">
              <label id="reward-menu-label" class="field-label">Menu</label>
              <div class="custom-select" ref="menuDropdownRef">
                <button
                  type="button"
                  class="form-input custom-select-trigger"
                  aria-haspopup="listbox"
                  :aria-expanded="menuOpen ? 'true' : 'false'"
                  aria-labelledby="reward-menu-label"
                  @click="menuOpen = !menuOpen"
                >
                  <span>{{ selectedMenuLabel }}</span>
                  <ChevronDown :size="14" class="custom-select-chevron" :class="{ 'is-open': menuOpen }" />
                </button>
                <div v-if="menuOpen" class="custom-select-panel" role="listbox" aria-labelledby="reward-menu-label">
                  <p v-if="!menus.length" class="custom-select-empty">Belum ada menu</p>
                  <button
                    type="button"
                    v-for="menu in menus"
                    :key="menu.id"
                    class="custom-select-option"
                    role="option"
                    :aria-selected="form.menu === menu.id"
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
              <label class="field-label" for="reward-cost">Biaya Poin</label>
              <input
                id="reward-cost"
                v-model.number="form.point_cost"
                type="number" min="1" inputmode="numeric"
                class="form-input mono"
                placeholder="cth: 500"
                required
              />
            </div>

            <label class="checkbox-row">
              <input type="checkbox" v-model="form.is_active" />
              <span>Aktifkan reward ini sekarang</span>
            </label>

            <p v-if="formError" class="form-error" role="alert">{{ formError }}</p>

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

    <!-- ── MODAL KONFIRMASI HAPUS ─────────────────────────────────── -->
    <transition
      enter-active-class="modal-enter-active" enter-from-class="modal-enter-from"
      leave-active-class="modal-leave-active" leave-to-class="modal-leave-to"
    >
      <div v-if="deleteTarget" class="modal-overlay" @click.self="closeDelete">
        <div class="modal-box modal-sm" role="alertdialog" aria-modal="true" aria-labelledby="del-title" aria-describedby="del-desc">
          <div class="confirm-body">
            <div class="confirm-icon"><Trash2 :size="18" /></div>
            <h2 id="del-title" class="modal-title">Hapus reward ini?</h2>
            <p id="del-desc" class="confirm-text">
              <strong>{{ deleteTarget.menu_name }}</strong> ({{ deleteTarget.point_cost.toLocaleString('id-ID') }} poin)
              akan dihapus dari katalog. Aksi ini tidak bisa dibatalkan.
            </p>
            <div class="modal-actions">
              <button ref="cancelDeleteBtn" type="button" class="btn-secondary" @click="closeDelete">Batal</button>
              <button type="button" class="btn-primary" :disabled="isDeleting" @click="confirmDelete">
                {{ isDeleting ? 'Menghapus...' : 'Hapus reward' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import { Plus, Pencil, Trash2, X, ChevronDown, Check, Gift, CheckCircle2, Coins, Settings2, Search } from 'lucide-vue-next';
import { pointRewardAPI, loyaltySettingsAPI, menuAPI } from '@/api';
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
// Esc menutup lapisan paling atas: konfirmasi hapus → dropdown → modal form
const handleKeydown = (e) => {
  if (e.key !== 'Escape') return;
  if (deleteTarget.value) { closeDelete(); return; }
  if (menuOpen.value) { menuOpen.value = false; return; }
  if (showModal.value) closeModal();
};
onMounted(() => {
  document.addEventListener('mousedown', handleClickOutsideDropdown);
  document.addEventListener('keydown', handleKeydown);
});
onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutsideDropdown);
  document.removeEventListener('keydown', handleKeydown);
});

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

// ── Delete (dengan modal konfirmasi) ─────────────────────────────
const deleteTarget    = ref(null);
const isDeleting      = ref(false);
const cancelDeleteBtn = ref(null);

const askDelete = (reward) => {
  deleteTarget.value = reward;
  nextTick(() => cancelDeleteBtn.value?.focus());
};
const closeDelete = () => { if (!isDeleting.value) deleteTarget.value = null; };

const confirmDelete = async () => {
  const reward = deleteTarget.value;
  if (!reward) return;
  isDeleting.value = true;
  try {
    await pointRewardAPI.remove(reward.id);
    rewards.value = rewards.value.filter((r) => r.id !== reward.id);
    toast.success('Reward dihapus');
    deleteTarget.value = null;
  } catch (err) {
    toast.error('Gagal menghapus reward');
  } finally {
    isDeleting.value = false;
  }
};
</script>

<style scoped>
.dashboard-root {

  --page-max: 1280px;
  min-height: 100%;
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', sans-serif;
  -webkit-font-smoothing: antialiased;
  padding: clamp(1.1rem, 3vw, 2rem) max(clamp(1rem, 3vw, 2.5rem), calc((100% - var(--page-max)) / 2)) 3rem;
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
  font-size: 0.68rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--accent-text);
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
  color: var(--on-accent); font-family: 'Oswald', sans-serif;
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
.ic-red   { background: rgba(220,38,38,0.1);  color: var(--red-soft); }
.ic-green { background: rgba(34,197,94,0.1);  color: var(--green-soft); }
.ic-amber { background: rgba(245,158,11,0.1); color: var(--amber-soft); }
.stat-value { font-family: monospace; font-size: 1.25rem; font-weight: 700; color: var(--text); margin: 0 0 0.15rem; line-height: 1; }
.stat-label { font-family: 'Oswald', sans-serif; font-size: 0.68rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-dim); margin: 0; }

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
  background: rgb(var(--ink) / 0.05); color: var(--text-dim);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  margin-top: 0.1rem;
}
.settings-label {
  font-family: 'Oswald', sans-serif;
  font-size: 0.75rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text);
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
  color: var(--text-dim);
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
  color: var(--text); font-size: 0.8rem; font-family: 'Inter', sans-serif;
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
  font-family: 'Oswald', sans-serif; font-size: 0.68rem;
  letter-spacing: 0.1em; text-transform: uppercase; cursor: pointer; transition: all 0.15s;
}
.chip-btn:hover { color: var(--text-2); }
.chip-btn.active { background: var(--accent); color: var(--on-accent); }

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
  font-size: 0.68rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-faint);
  background: rgb(var(--ink) / 0.015);
  border-bottom: 1px solid var(--border);
}
.promo-table tbody td {
  padding: 0.9rem 1.25rem;
  font-size: 0.8rem;
  color: var(--text-2);
  border-bottom: 1px solid rgb(var(--ink) / 0.03);
  vertical-align: middle;
}
.promo-table tbody tr { transition: background 0.12s; }
.promo-table tbody tr:hover { background: rgb(var(--ink) / 0.02); }
.promo-table tbody tr:last-child td { border-bottom: none; }
.mono-cell { font-family: monospace; font-size: 0.75rem; color: var(--text-dim); }

.promo-code { font-family: monospace; font-weight: 700; font-size: 0.85rem; color: var(--text); letter-spacing: 0.03em; }
.promo-discount { font-family: monospace; font-weight: 700; color: var(--accent-text); font-size: 0.85rem; }

.col-aksi { text-align: right; }
.row-actions { display: flex; justify-content: flex-end; gap: 0.4rem; }
.icon-btn {
  width: 28px; height: 28px; border-radius: 7px;
  background: rgb(var(--ink) / 0.05); border: 1px solid rgb(var(--ink) / 0.08);
  color: var(--text-dim);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all 0.15s;
}
.icon-btn:hover { background: rgb(var(--ink) / 0.1); color: var(--text); }
.icon-btn-danger:hover { background: rgba(239,68,68,0.15); color: var(--red-soft); border-color: rgba(239,68,68,0.3); }

.status-badge {
  padding: 0.3rem 0.7rem; border-radius: 100px; border: 1px solid;
  font-family: 'Oswald', sans-serif; font-size: 0.68rem;
  letter-spacing: 0.08em; text-transform: uppercase;
  cursor: pointer; transition: opacity 0.15s; white-space: nowrap;
}
.status-badge:hover { opacity: 0.8; }
.status-badge:disabled { opacity: 0.5; cursor: not-allowed; }
.badge-green { background: rgba(34,197,94,0.1); border-color: rgba(34,197,94,0.3); color: var(--green-soft); }
.badge-gray  { background: rgb(var(--ink) / 0.05); border-color: rgb(var(--ink) / 0.12); color: var(--text-dim); }

/* ── Empty / error state ─────────────────────────────────────────── */
.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 0.6rem; padding: 4rem 2rem; text-align: center;
}
.empty-icon { font-size: 2rem; }
.empty-text { color: var(--text-dim); margin: 0; font-size: 0.9rem; }
.empty-hint { color: var(--text-faint); margin: 0; font-size: 0.75rem; }
.retry-btn {
  margin-top: 0.5rem; padding: 0.5rem 1.25rem; border-radius: 8px;
  background: var(--accent); border: none; color: var(--on-accent);
  font-family: 'Oswald', sans-serif; font-size: 0.68rem;
  letter-spacing: 0.1em; text-transform: uppercase; cursor: pointer;
}
.retry-btn:hover { background: var(--accent-hover); }

/* ── Modal ───────────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed; inset: 0; z-index: 70;
  background: var(--overlay); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; padding: 1rem;
}
.modal-enter-active { transition: all 0.2s ease; }
.modal-enter-from   { opacity: 0; transform: scale(0.96); }
.modal-leave-active { transition: all 0.15s ease; }
.modal-leave-to     { opacity: 0; transform: scale(0.96); }

.modal-box {
  background: var(--surface); border: 1px solid rgb(var(--ink) / 0.08);
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
  background: rgb(var(--ink) / 0.05); border: 1px solid rgb(var(--ink) / 0.08);
  color: var(--text-dim); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.modal-close-btn:hover { background: rgb(var(--ink) / 0.1); color: var(--text); }

.modal-form { padding: 1.25rem 1.5rem 1.5rem; display: flex; flex-direction: column; gap: 1rem; }

.field { display: flex; flex-direction: column; gap: 0.4rem; }
.field-label {
  font-family: 'Oswald', sans-serif; font-size: 0.68rem;
  letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-dim);
}
.field-hint { font-size: 0.68rem; color: var(--text-faint); margin: 0.1rem 0 0; }

.form-input {
  background: rgb(var(--ink) / 0.04); border: 1px solid rgb(var(--ink) / 0.1);
  border-radius: 9px; padding: 0.6rem 0.8rem;
  color: var(--text); font-size: 0.82rem; font-family: 'Inter', sans-serif;
  outline: none; transition: border-color 0.15s; width: 100%;

}
.form-input.mono { font-family: monospace; }
.form-input:focus { border-color: rgba(220,38,38,0.5); }
.form-input::placeholder { color: var(--text-faint); }

.form-input[type="number"]::-webkit-inner-spin-button,
.form-input[type="number"]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
.form-input[type="number"] { -moz-appearance: textfield; }

/* ── Custom dropdown "Menu" ──────────────────────────────────────── */
.custom-select { position: relative; }
.custom-select-trigger {
  display: flex; align-items: center; justify-content: space-between;
  cursor: pointer; text-align: left;
}
.custom-select-chevron { color: var(--text-dim); transition: transform 0.15s; flex-shrink: 0; }
.custom-select-chevron.is-open { transform: rotate(180deg); }

.custom-select-panel {
  position: absolute; top: calc(100% + 6px); left: 0; right: 0; z-index: 20;
  background: var(--surface-2); border: 1px solid rgb(var(--ink) / 0.1);
  border-radius: 9px; padding: 0.3rem;
  max-height: 260px; overflow-y: auto;
  box-shadow: var(--shadow-lg);
}
.custom-select-option {
  width: 100%; display: flex; align-items: center; justify-content: space-between;
  gap: 0.5rem;
  padding: 0.55rem 0.65rem; border-radius: 6px; border: none;
  background: transparent; color: var(--text-2);
  font-size: 0.8rem; font-family: 'Inter', sans-serif; text-align: left;
  cursor: pointer; transition: background 0.12s;
}
.custom-select-option:hover { background: rgb(var(--ink) / 0.06); color: var(--text); }
.custom-select-option.is-selected { color: var(--red-soft); }
.custom-select-option.is-selected svg { color: var(--red-soft); flex-shrink: 0; }

.checkbox-row {
  display: flex; align-items: center; gap: 0.55rem;
  font-size: 0.78rem; color: var(--text-2); cursor: pointer;
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
.btn-secondary { background: rgb(var(--ink) / 0.05); color: var(--text-dim); }
.btn-secondary:hover { background: rgb(var(--ink) / 0.1); color: var(--text); }
.btn-primary { background: var(--accent); color: var(--on-accent); }
.btn-primary:hover:not(:disabled) { background: var(--accent-hover); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }


/* ══ Tambahan: tema, UX, responsif ═════════════════════════════════ */
.stat-card, .settings-card, .table-card, .search-input, .filter-chips { box-shadow: var(--shadow-sm); }
.stat-value, .mono-cell, .promo-discount { font-variant-numeric: tabular-nums; }
.dash-title { font-size: clamp(1.4rem, 4vw, 1.75rem); }
.new-promo-btn { color: var(--on-accent); min-height: 44px; }

.icon-btn { width: 32px; height: 32px; }
.promo-table tbody tr:hover { background: var(--surface-hover); }
.status-badge { min-height: 28px; }
.status-badge.badge-gray { color: var(--text-dim); }
.chip-btn.active, .btn-primary, .retry-btn { color: var(--on-accent); }
.settings-icon-wrap { color: var(--text-dim); }
.settings-hint { max-width: 46ch; }

.custom-select-empty { margin: 0; padding: 0.7rem; font-size: 0.78rem; color: var(--text-faint); }
.custom-select-option { min-height: 38px; }

/* modal konfirmasi hapus */
.modal-sm { max-width: 400px; }
.confirm-body { padding: 1.5rem; display: flex; flex-direction: column; align-items: center; text-align: center; gap: 0.6rem; }
.confirm-icon {
  display: flex; align-items: center; justify-content: center;
  width: 44px; height: 44px; border-radius: 12px; margin-bottom: 0.25rem;
  background: rgb(239 68 68 / 0.12); color: var(--red-soft);
}
.confirm-text { margin: 0 0 0.75rem; font-size: 0.82rem; line-height: 1.55; color: var(--text-dim); }
.confirm-text strong { color: var(--text); font-weight: 600; }
.confirm-body .modal-actions { width: 100%; }
.confirm-body .modal-actions > button { flex: 1; }

.modal-box { animation: none; }
.btn-secondary, .btn-primary { min-height: 40px; }

/* ── Tablet & mobile ── */
@media (max-width: 900px) {
  .settings-card { align-items: stretch; }
  .settings-input-row { flex-wrap: wrap; }
}

@media (max-width: 720px) {
  .dashboard-root { gap: 1rem; }
  .dash-header { flex-direction: column; align-items: stretch; padding-bottom: 1.1rem; }
  .new-promo-btn { width: 100%; justify-content: center; }

  /* ringkasan: 3 tile ringkas sebaris */
  .stats-grid { grid-template-columns: repeat(3, 1fr); gap: 0.6rem; }
  .stat-card { flex-direction: column; align-items: flex-start; gap: 0.55rem; padding: 0.8rem; }
  .stat-value { font-size: 1.1rem; }
  .stat-label { line-height: 1.3; }

  .settings-input-row { width: 100%; }
  .settings-input { flex: 1; min-width: 0; width: auto; }
  .settings-save-btn { width: 100%; min-height: 44px; }

  .table-toolbar { flex-direction: column; align-items: stretch; }
  .search-box { max-width: none; min-width: 0; }
  .filter-chips { width: 100%; }
  .chip-btn { flex: 1; min-height: 36px; }

  /* tabel → kartu */
  .promo-table, .promo-table tbody { display: block; width: 100%; }
  .promo-table thead {
    position: absolute; width: 1px; height: 1px; overflow: hidden;
    clip: rect(0 0 0 0); white-space: nowrap;
  }
  .promo-table tbody tr {
    display: grid;
    grid-template-columns: 1fr 1fr auto;
    grid-template-areas: "menu menu status" "price cost actions";
    gap: 0.7rem 0.75rem;
    align-items: center;
    padding: 0.95rem 1rem;
    border-bottom: 1px solid var(--border);
  }
  .promo-table tbody tr:last-child { border-bottom: none; }
  .promo-table tbody td { display: block; padding: 0; border: 0; }
  .td-menu    { grid-area: menu; min-width: 0; }
  .td-price   { grid-area: price; }
  .td-cost    { grid-area: cost; }
  .td-status  { grid-area: status; justify-self: end; }
  .td-actions { grid-area: actions; justify-self: end; }
  .promo-code { word-break: break-word; }
  .promo-table tbody td[data-label]::before {
    content: attr(data-label);
    display: block; margin-bottom: 0.15rem;
    font-family: 'Oswald', sans-serif; font-size: 0.68rem;
    letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-faint);
  }
  .promo-table { font-size: 0.8rem; }
}

/* modal jadi bottom-sheet di layar kecil */
@media (max-width: 560px) {
  .modal-overlay { align-items: flex-end; padding: 0; }
  .modal-box {
    max-width: none; max-height: 92vh; max-height: 92dvh;
    border-radius: 20px 20px 0 0;
    padding-bottom: env(safe-area-inset-bottom, 0px);
  }
  .modal-enter-from, .modal-leave-to { opacity: 0; transform: translateY(24px); }
  .modal-actions { flex-direction: column-reverse; }
  .modal-actions > button { width: 100%; min-height: 46px; }
  .form-input { font-size: 1rem; min-height: 44px; } /* 16px → iOS tidak auto-zoom */
  .custom-select-option { min-height: 44px; }
  .checkbox-row { min-height: 40px; }
}

@media (pointer: coarse) {
  .icon-btn { width: 40px; height: 40px; }
  .status-badge { min-height: 34px; padding-inline: 0.9rem; }
  .chip-btn { min-height: 40px; }
}

</style>