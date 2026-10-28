<template>
  <div class="adm-page">

    <!-- ── HEADER ──────────────────────────────────────────────────── -->
    <header class="adm-header">
      <div>
        <p class="adm-eyebrow">Masashimura · Admin</p>
        <h1 class="adm-title">Kelola Reward Poin</h1>
        <p class="adm-sub">Katalog menu yang bisa ditukar pakai poin loyalty customer</p>
      </div>
      <div class="adm-header-actions">
        <button type="button" class="adm-btn adm-btn--primary" @click="openCreateModal">
          <Plus :size="15" /> Tambah Reward
        </button>
      </div>
    </header>

    <!-- ── STAT CARDS ──────────────────────────────────────────────── -->
    <div class="adm-stats">
      <div class="adm-stat">
        <span class="adm-stat-icon tone-accent"><Gift :size="17" /></span>
        <div>
          <p class="adm-stat-value">{{ totalRewards }}</p>
          <p class="adm-stat-label">Total Reward</p>
        </div>
      </div>
      <div class="adm-stat">
        <span class="adm-stat-icon tone-green"><CheckCircle2 :size="17" /></span>
        <div>
          <p class="adm-stat-value">{{ activeRewards }}</p>
          <p class="adm-stat-label">Reward Aktif</p>
        </div>
      </div>
      <div class="adm-stat">
        <span class="adm-stat-icon tone-amber"><Coins :size="17" /></span>
        <div>
          <p class="adm-stat-value">{{ avgPointCost.toLocaleString('id-ID') }}</p>
          <p class="adm-stat-label">Rata-rata Biaya Poin</p>
        </div>
      </div>
    </div>

    <!-- ── PENGATURAN RATE POIN MASUK ──────────────────────────────── -->
    <section class="adm-card">
      <div class="adm-card-head pr-settings">
        <span class="adm-card-icon"><Settings2 :size="16" /></span>
        <div class="adm-card-head-main">
          <h2 class="adm-card-title">Rate Poin Masuk</h2>
          <p class="adm-card-desc">Belanja Rp berapa yang setara 1 poin? (redeem-nya diatur per-menu di tabel bawah)</p>
        </div>
        <div class="pr-rate-row">
          <span class="pr-affix adm-mono">Rp</span>
          <input
            id="rate-input"
            v-model.number="rupiahPerPoint"
            type="number" min="1" step="1000" inputmode="numeric"
            aria-label="Nominal belanja (Rupiah) yang setara 1 poin"
            class="adm-input adm-input--mono pr-rate-input"
            @keydown.enter="saveLoyaltySettings"
          />
          <span class="pr-affix adm-mono">= 1 poin</span>
          <button
            type="button"
            class="adm-btn adm-btn--primary pr-rate-save"
            :disabled="isSavingSettings || !rupiahPerPoint || rupiahPerPoint === savedRupiahPerPoint"
            @click="saveLoyaltySettings"
          >
            {{ isSavingSettings ? 'Menyimpan...' : 'Simpan' }}
          </button>
        </div>
      </div>
    </section>

    <!-- ── TOOLBAR: SEARCH + FILTER ────────────────────────────────── -->
    <div v-if="!isLoading && !loadError && rewards.length > 0" class="adm-toolbar">
      <div class="adm-search">
        <Search :size="15" class="adm-search-icon" />
        <input
          v-model="searchQuery"
          type="search"
          placeholder="Cari nama menu..."
          aria-label="Cari reward berdasarkan nama menu"
          class="adm-input"
        />
      </div>
      <div class="adm-seg" role="group" aria-label="Filter status">
        <button
          v-for="f in statusFilters"
          :key="f.key"
          type="button"
          class="adm-seg-btn"
          :aria-pressed="statusFilter === f.key"
          @click="statusFilter = f.key"
        >
          {{ f.label }}
        </button>
      </div>
    </div>

    <!-- ── ERROR ───────────────────────────────────────────────────── -->
    <div v-if="!isLoading && loadError" class="adm-card adm-card--flush">
      <div class="adm-empty">
        <div class="adm-empty-icon"><AlertTriangle :size="22" /></div>
        <p class="adm-empty-title">Gagal memuat data reward poin</p>
        <button type="button" class="adm-btn adm-btn--primary" @click="fetchRewards">Coba Lagi</button>
      </div>
    </div>

    <!-- ── EMPTY (belum ada reward sama sekali) ─────────────────────── -->
    <div v-else-if="!isLoading && rewards.length === 0" class="adm-card adm-card--flush">
      <div class="adm-empty">
        <div class="adm-empty-icon"><Gift :size="22" /></div>
        <p class="adm-empty-title">Belum ada reward poin</p>
        <p class="adm-empty-text">Klik "Tambah Reward" buat bikin yang pertama — pilih menu HPP kecil biar aman</p>
      </div>
    </div>

    <!-- ── TABLE ───────────────────────────────────────────────────── -->
    <div v-else-if="!isLoading" class="adm-card adm-card--flush">
      <div v-if="filteredRewards.length" class="adm-table-wrap">
        <table class="adm-table adm-table--stack">
          <thead>
            <tr>
              <th>Menu</th>
              <th>Harga Menu</th>
              <th>Biaya Poin</th>
              <th>Status</th>
              <th class="adm-th-r">Aksi</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="reward in filteredRewards" :key="reward.id">
              <td class="adm-td-first" data-label="Menu">
                <span class="pr-name">{{ reward.menu_name }}</span>
              </td>
              <td class="adm-mono" data-label="Harga menu">{{ formatPrice(reward.menu_price) }}</td>
              <td data-label="Biaya poin">
                <span class="pr-cost adm-mono">{{ reward.point_cost.toLocaleString('id-ID') }} poin</span>
              </td>
              <td data-label="Status">
                <button
                  type="button"
                  class="adm-badge"
                  :class="reward.is_active ? 'adm-badge--green' : ''"
                  :disabled="togglingId === reward.id"
                  :aria-pressed="reward.is_active"
                  :title="reward.is_active ? 'Klik untuk nonaktifkan' : 'Klik untuk aktifkan'"
                  @click="toggleActive(reward)"
                >
                  {{ reward.is_active ? 'Aktif' : 'Nonaktif' }}
                </button>
              </td>
              <td class="adm-td-r" data-label="">
                <div class="pr-row-actions">
                  <button type="button" class="adm-icon-btn adm-icon-btn--bordered" title="Edit" :aria-label="`Edit reward ${reward.menu_name}`" @click="openEditModal(reward)">
                    <Pencil :size="14" />
                  </button>
                  <button type="button" class="adm-icon-btn adm-icon-btn--bordered adm-icon-btn--danger" title="Hapus" :aria-label="`Hapus reward ${reward.menu_name}`" @click="askDelete(reward)">
                    <Trash2 :size="14" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Filter tidak menemukan hasil -->
      <div v-else class="adm-empty">
        <div class="adm-empty-icon"><Search :size="22" /></div>
        <p class="adm-empty-title">Tidak ada reward yang cocok</p>
        <p class="adm-empty-text">Coba ubah kata kunci pencarian atau filter status</p>
        <button type="button" class="adm-btn adm-btn--ghost" @click="resetFilters">Reset Filter</button>
      </div>
    </div>

    <!-- ── MODAL CREATE/EDIT ─────────────────────────────────────── -->
    <AdminModal
      :model-value="showModal"
      :title="editingId ? 'Edit Reward' : 'Tambah Reward Baru'"
      :persistent="isSaving"
      @close="closeModal"
    >
      <form id="reward-form" class="adm-modal-form" @submit.prevent="submitForm">
        <div class="adm-field">
          <label id="reward-menu-label" class="adm-label">Menu</label>
          <div class="custom-select" ref="menuDropdownRef">
            <button
              type="button"
              class="adm-input custom-select-trigger"
              aria-haspopup="listbox"
              :aria-expanded="menuOpen ? 'true' : 'false'"
              aria-labelledby="reward-menu-label"
              @click="menuOpen = !menuOpen"
            >
              <span class="adm-truncate">{{ selectedMenuLabel }}</span>
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
          <p class="adm-hint">Pilih menu HPP kecil (minuman/side dish), hindari menu signature yang mahal</p>
        </div>

        <div class="adm-field">
          <label class="adm-label" for="reward-cost">Biaya Poin</label>
          <input
            id="reward-cost"
            v-model.number="form.point_cost"
            type="number" min="1" inputmode="numeric"
            class="adm-input adm-input--mono"
            placeholder="cth: 500"
            required
          />
        </div>

        <label class="adm-check">
          <input type="checkbox" v-model="form.is_active" />
          <span>Aktifkan reward ini sekarang</span>
        </label>

        <p v-if="formError" class="adm-alert" role="alert">{{ formError }}</p>
      </form>

      <template #footer>
        <button type="button" class="adm-btn adm-btn--ghost" :disabled="isSaving" @click="closeModal">Batal</button>
        <button type="submit" form="reward-form" class="adm-btn adm-btn--primary" :disabled="isSaving">
          <span v-if="isSaving" class="adm-spinner"></span>
          {{ editingId ? 'Simpan Perubahan' : 'Tambah Reward' }}
        </button>
      </template>
    </AdminModal>

    <!-- ── MODAL KONFIRMASI HAPUS ─────────────────────────────────── -->
    <AdminModal
      v-if="deleteTarget"
      :model-value="true"
      title="Hapus reward ini?"
      size="sm"
      :persistent="isDeleting"
      @close="closeDelete"
    >
      <p class="adm-modal-text">
        <strong>{{ deleteTarget.menu_name }}</strong> ({{ deleteTarget.point_cost.toLocaleString('id-ID') }} poin)
        akan dihapus dari katalog. Aksi ini tidak bisa dibatalkan.
      </p>
      <template #footer>
        <button ref="cancelDeleteBtn" data-autofocus type="button" class="adm-btn adm-btn--ghost" :disabled="isDeleting" @click="closeDelete">Batal</button>
        <button type="button" class="adm-btn adm-btn--danger" :disabled="isDeleting" @click="confirmDelete">
          <span v-if="isDeleting" class="adm-spinner"></span>
          {{ isDeleting ? 'Menghapus...' : 'Hapus reward' }}
        </button>
      </template>
    </AdminModal>

    <!-- ── Efektivitas poin (#15) ──────────────────────────────────── -->
    <PointEffectiveness />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import { useRouteSearch } from '@/composables/useRouteSearch';
import { Plus, Pencil, Trash2, ChevronDown, Check, Gift, CheckCircle2, Coins, Settings2, Search, AlertTriangle } from 'lucide-vue-next';
import { pointRewardAPI, loyaltySettingsAPI, menuAPI } from '@/api';
import { toast } from 'vue-sonner';
import PointEffectiveness from '@/components/ui/admin/PointEffectiveness.vue';
import AdminModal from '@/components/ui/admin/Adminmodal.vue';

const rewards    = ref([]);
const menus      = ref([]);
const isLoading  = ref(true);
const loadError  = ref(false);
const togglingId = ref(null);

// ── Pencarian & filter status ───────────────────────────────────────
const searchQuery  = ref('');
useRouteSearch(searchQuery); // ?q= dari pencarian global
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
  // AdminModal juga menutup dirinya lewat Esc; stopImmediatePropagation mencegah
  // satu kali Esc menutup dropdown SEKALIGUS modal di bawahnya.
  if (menuOpen.value) { e.stopImmediatePropagation(); menuOpen.value = false; }
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
/* Halaman memakai primitif bersama (admin-ui.css); di sini hanya yang spesifik. */

/* Kartu "Rate Poin Masuk": judul di kiri, input di kanan */
.pr-settings { align-items: center; flex-wrap: wrap; }
.pr-rate-row { display: flex; align-items: center; gap: 0.5rem; flex-shrink: 0; margin-left: auto; }
.pr-affix { font-size: 0.8125rem; color: var(--text-dim); white-space: nowrap; }
.pr-rate-input { width: 7.5rem; text-align: right; }

.pr-name { font-weight: 700; color: var(--text); }
.pr-cost { font-weight: 700; color: var(--accent-text); }
.pr-row-actions { display: flex; justify-content: flex-end; gap: 0.4rem; }

.adm-modal-form { display: flex; flex-direction: column; gap: 1rem; }

/* ── Dropdown "Menu" ─────────────────────────────────────────────── */
.custom-select { position: relative; }
.custom-select-trigger { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; cursor: pointer; text-align: left; }
.custom-select-chevron { color: var(--text-dim); transition: transform 0.15s; flex-shrink: 0; }
.custom-select-chevron.is-open { transform: rotate(180deg); }
.custom-select-panel {
  position: absolute; top: calc(100% + 6px); left: 0; right: 0; z-index: 20;
  max-height: 260px; overflow-y: auto; padding: 0.3rem;
  background: var(--surface-2); border: 1px solid var(--border-strong);
  border-radius: var(--r-md); box-shadow: var(--shadow-lg);
}
.custom-select-option {
  display: flex; align-items: center; justify-content: space-between; gap: 0.5rem;
  width: 100%; min-height: 38px; padding: 0.55rem 0.65rem;
  border: none; border-radius: var(--r-sm); background: transparent;
  color: var(--text-2); font-family: var(--font-body); font-size: 0.8125rem; text-align: left; cursor: pointer;
  transition: background 0.12s;
}
.custom-select-option:hover { background: var(--surface-hover); color: var(--text); }
.custom-select-option.is-selected { color: var(--accent-text); }
.custom-select-empty { margin: 0; padding: 0.7rem; font-size: 0.8125rem; color: var(--text-faint); }

@media (max-width: 720px) {
  .pr-rate-row { width: 100%; margin-left: 0; flex-wrap: wrap; }
  .pr-rate-input { flex: 1; min-width: 0; width: auto; }
  .pr-rate-save { width: 100%; }
  .adm-toolbar .adm-search { max-width: none; }
  .adm-toolbar .adm-seg { width: 100%; }
  .adm-toolbar .adm-seg-btn { flex: 1; }
}
@media (max-width: 560px) {
  .custom-select-option { min-height: 44px; }
}
</style>
