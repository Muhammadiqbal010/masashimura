<template>
  <div class="adm-page">

    <!-- ── PAGE HEADER ─────────────────────────────────────────────── -->
    <header class="adm-header">
      <div>
        <p class="adm-eyebrow">Masashimura · Program Loyalitas</p>
        <h1 class="adm-title">Loyal Customers</h1>
        <p class="adm-sub">Poin didapat dari belanja, ditukar jadi menu gratis — hangus kalau {{ expiryLabel }}</p>
      </div>
      <div class="adm-header-actions">
        <button type="button" class="adm-btn adm-btn--ghost adm-btn--sm" @click="refreshData">
          <RefreshCw :size="14" aria-hidden="true" /> Refresh
        </button>
      </div>
    </header>

    <!-- ── STAT CARDS ─────────────────────────────────────────────── -->
    <div class="adm-stats">
      <div class="adm-stat">
        <span class="adm-stat-icon tone-accent"><Users :size="17" /></span>
        <div>
          <p class="adm-stat-value">{{ loyalty.loyalCustomers.length }}</p>
          <p class="adm-stat-label">Total Member · terdaftar di sistem</p>
        </div>
      </div>
      <div class="adm-stat">
        <span class="adm-stat-icon tone-green"><UserCheck :size="17" /></span>
        <div>
          <p class="adm-stat-value">{{ activePointsCount }}</p>
          <p class="adm-stat-label">Punya Poin Aktif · saldo &gt; 0</p>
        </div>
      </div>
      <div class="adm-stat">
        <span class="adm-stat-icon tone-amber"><Coins :size="17" /></span>
        <div>
          <p class="adm-stat-value">{{ totalPointsOutstanding }}</p>
          <p class="adm-stat-label">Total Poin Beredar · semua member</p>
        </div>
      </div>
    </div>

    <!-- ── LOADING ─────────────────────────────────────────────────── -->
    <div v-if="loyalty.loading" class="adm-card">
      <div class="adm-empty" aria-busy="true">
        <span class="adm-spinner lc-spinner"></span>
        <p class="adm-empty-text">Memuat data pelanggan...</p>
      </div>
    </div>

    <!-- ── ERROR ──────────────────────────────────────────────────── -->
    <div v-else-if="loyalty.error" class="adm-card adm-card--flush">
      <div class="adm-empty">
        <div class="adm-empty-icon"><AlertTriangle :size="22" /></div>
        <p class="adm-empty-title">{{ loyalty.error }}</p>
        <button type="button" class="adm-btn adm-btn--primary" @click="fetchAdminLoyalData">Coba lagi</button>
      </div>
    </div>

    <!-- ── TABLE ──────────────────────────────────────────────────── -->
    <div v-else class="adm-card adm-card--flush">
      <div class="adm-card-head">
        <div class="adm-card-head-main">
          <h2 class="adm-card-title">Daftar Pelanggan</h2>
          <p class="adm-card-desc">{{ filteredCustomers.length }} dari {{ loyalty.loyalCustomers.length }} customer</p>
        </div>
      </div>

      <div class="lc-body">
        <input v-model="searchQuery" type="search" class="adm-input" placeholder="Cari nama atau nomor HP…" aria-label="Cari pelanggan" />
        <p class="adm-hint">
          <template v-if="expiryMonths > 0">
            Poin hangus kalau pelanggan <strong>tidak belanja selama {{ expiryMonths }} bulan</strong> sejak order terakhir.
            Setiap order baru memulai hitungan dari awal. Kolom Hangus adalah perkiraan bila pelanggan tidak order lagi.
          </template>
          <template v-else>Kedaluwarsa poin sedang dimatikan, jadi poin tidak pernah hangus. Atur di Pengaturan Loyalty.</template>
        </p>

        <!-- Segmentasi: klik chip untuk menyaring -->
        <div v-if="loyalty.segments.length" class="adm-seg lc-seg" role="group" aria-label="Saring menurut segmen">
          <button
            v-for="s in loyalty.segments"
            :key="s.key"
            type="button"
            class="adm-seg-btn"
            :aria-pressed="segmentFilter === s.key"
            :title="s.hint"
            @click="segmentFilter = segmentFilter === s.key ? null : s.key"
          >
            <strong class="tabular">{{ s.count }}</strong>
            <span>{{ s.label }}</span>
          </button>
        </div>
        <p v-if="activeSegmentHint" class="adm-hint">{{ activeSegmentHint }}</p>

        <!-- Toolbar hapus -->
        <div v-if="loyalty.loyalCustomers.length" class="lc-del-bar">
          <label class="adm-check">
            <input type="checkbox" :checked="allVisibleSelected" :indeterminate.prop="someSelected && !allVisibleSelected" @change="toggleAllVisible" />
            Pilih semua yang tampil
          </label>
          <div class="lc-del-actions">
            <button type="button" class="adm-btn adm-btn--danger adm-btn--sm" :disabled="!selected.size" @click="openBulkDelete('selected')">
              Hapus terpilih ({{ selected.size }})
            </button>
            <button type="button" class="adm-btn adm-btn--danger adm-btn--sm" @click="openBulkDelete('all')">Hapus semua</button>
          </div>
        </div>
      </div>

      <div class="adm-table-wrap">
        <table class="adm-table adm-table--stack lc-table">
          <thead>
            <tr>
              <th class="adm-th-c lc-check"><span class="adm-sr">Pilih</span></th>
              <th>Pelanggan</th>
              <th class="adm-th-c">Segmen</th>
              <th>Order Terakhir</th>
              <th class="adm-th-c">Total Order</th>
              <th class="adm-th-r">Total Belanja</th>
              <th class="adm-th-c">Poin</th>
              <th class="adm-th-c">Hangus</th>
              <th class="adm-th-c">Status</th>
              <th class="adm-th-c">PIN</th>
              <th class="adm-th-c">Aksi</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="customer in filteredCustomers" :key="customer.phone">
              <td class="adm-td-c lc-check" data-label="Pilih">
                <input type="checkbox" :checked="selected.has(customer.phone)" :aria-label="'Pilih ' + customer.phone" @change="toggleOne(customer.phone)" />
              </td>

              <!-- Phone -->
              <td class="adm-td-first">
                <div class="lc-phone">
                  <span class="lc-phone-val adm-mono">{{ customer.phone }}</span>
                  <span v-if="customer.name" class="lc-sub">{{ customer.name }}</span>
                </div>
              </td>

              <!-- Segmen -->
              <td class="adm-td-c" data-label="Segmen">
                <span class="adm-badge" :class="segmentBadge(customer.segment)" :title="segmentHint(customer.segment)">
                  {{ segmentLabel(customer.segment) }}
                </span>
                <span v-if="customer.days_since_last_order != null" class="lc-sub lc-block">{{ customer.days_since_last_order }} hari lalu</span>
              </td>

              <!-- Order terakhir -->
              <td class="adm-mono lc-dim" data-label="Order terakhir">{{ customer.last_order_at ? formatDate(customer.last_order_at) : '—' }}</td>

              <!-- Total order -->
              <td class="adm-td-c" data-label="Total order">
                <span class="lc-strong adm-mono">{{ customer.total_orders || 0 }}</span>
                <span class="lc-sub"> order</span>
              </td>

              <!-- Belanja -->
              <td class="adm-td-r lc-spend adm-mono" data-label="Total belanja">{{ formatPrice(customer.total_spent) }}</td>

              <!-- Poin -->
              <td class="adm-td-c" data-label="Poin">
                <span v-if="customer.points > 0" class="adm-badge adm-badge--green">{{ customer.points }} Poin</span>
                <span v-else class="lc-sub">0</span>
              </td>

              <!-- Kapan poin hangus -->
              <td class="adm-td-c" data-label="Hangus">
                <span v-if="customer.expiry_state === 'off' || customer.expiry_state === 'none'" class="lc-sub">—</span>
                <span v-else-if="customer.expiry_state === 'expired'" class="adm-badge">Sudah hangus</span>
                <template v-else>
                  <span class="lc-block">{{ formatDate(customer.expiry_estimate) }}</span>
                  <span class="lc-sub lc-block" :class="{ 'is-soon': customer.expiry_state === 'soon' }">
                    {{ customer.days_until_expiry > 0 ? customer.days_until_expiry + ' hari lagi' : 'hari ini' }}
                  </span>
                </template>
              </td>

              <!-- Status -->
              <td class="adm-td-c" data-label="Status">
                <span
                  v-if="customer.points_expired"
                  class="adm-badge"
                  :title="'Poin sudah hangus (order terakhir ' + formatDate(customer.last_order_at) + ')'"
                >
                  Poin Hangus
                </span>
                <span v-else-if="customer.points > 0" class="adm-badge adm-badge--green">Aktif</span>
                <span v-else class="adm-badge">Belum Ada Poin</span>
              </td>

              <!-- PIN -->
              <td class="adm-td-c" data-label="PIN">
                <span v-if="customer.pin_locked" class="adm-badge adm-badge--red">Terkunci</span>
                <span v-else-if="customer.has_pin" class="lc-sub">Diatur {{ formatShortDate(customer.pin_set_at) }}</span>
                <span v-else class="lc-sub">Belum diatur</span>
              </td>

              <!-- Aksi -->
              <td class="adm-td-c">
                <div class="lc-actions">
                  <button type="button" class="adm-btn adm-btn--soft adm-btn--sm" @click="openAdjustModal(customer)">Adjust Poin</button>
                  <button type="button" class="adm-btn adm-btn--ghost adm-btn--sm" @click="openPin(customer)">
                    {{ customer.has_pin ? 'Ganti PIN' : 'Atur PIN' }}
                  </button>
                  <button type="button" class="adm-btn adm-btn--danger adm-btn--sm" @click="openSingleDelete(customer)">Hapus</button>
                </div>
              </td>
            </tr>

            <tr v-if="filteredCustomers.length === 0">
              <td colspan="11">
                <div class="adm-empty">
                  <div class="adm-empty-icon"><Users :size="22" /></div>
                  <p class="adm-empty-title">{{ segmentFilter ? 'Tidak ada pelanggan di segmen ini' : 'Belum ada data pelanggan' }}</p>
                  <p class="adm-empty-text">{{ segmentFilter ? 'Pilih segmen lain atau hapus saringan.' : 'Data muncul setelah ada transaksi pertama dari nomor HP customer' }}</p>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── MODAL ADJUST POIN ──────────────────────────────────────── -->
    <AdminModal
      :model-value="showAdjustModal"
      :title="`Adjust Poin — ${selectedCustomer?.phone ?? ''}`"
      size="sm"
      :persistent="isSaving"
      @close="showAdjustModal = false"
    >
      <!-- Saldo saat ini -->
      <div class="lc-balance">
        <p class="adm-hint">Saldo Poin Saat Ini</p>
        <p class="lc-balance-val">{{ selectedCustomer?.points ?? 0 }} <span class="lc-sub">Poin</span></p>
      </div>

      <div class="adm-field">
        <label class="adm-label" for="adjust-amount">Jumlah Adjust (+ nambah / - kurangin)</label>
        <input
          id="adjust-amount"
          v-model.number="adjustAmount"
          data-autofocus
          type="number"
          placeholder="Contoh: 10 atau -5"
          class="adm-input adm-input--mono"
        />
        <p class="adm-hint">Saldo baru: {{ (selectedCustomer?.points ?? 0) + (adjustAmount || 0) }} poin</p>
      </div>

      <div class="adm-field">
        <label class="adm-label" for="adjust-note">Alasan <span class="adm-req">*</span></label>
        <input
          id="adjust-note"
          v-model="adjustNote"
          type="text"
          placeholder="Contoh: kompensasi komplain, bonus ulang tahun"
          class="adm-input"
        />
      </div>

      <template #footer>
        <button type="button" class="adm-btn adm-btn--ghost" :disabled="isSaving" @click="showAdjustModal = false">Batal</button>
        <button type="button" class="adm-btn adm-btn--primary" :disabled="isSaving" @click="saveAdjustPoints">
          <span v-if="isSaving" class="adm-spinner"></span>
          {{ isSaving ? 'Menyimpan...' : 'Simpan Adjustment' }}
        </button>
      </template>
    </AdminModal>

    <!-- ── MODAL PIN MEMBER ─────────────────────────────────────────── -->
    <AdminModal
      :model-value="pinModal.open"
      :title="`${pinModal.customer?.has_pin ? 'Ganti PIN' : 'Atur PIN'} — ${pinModal.customer?.phone ?? ''}`"
      :persistent="pinModal.busy"
      @close="closePin"
    >
      <!-- Langkah 1: buat -->
      <template v-if="!pinModal.result">
        <ul class="lc-list">
          <li v-if="pinModal.customer?.has_pin"><strong>Pastikan permintaan datang dari WhatsApp nomor ini sendiri.</strong> Jangan mengganti PIN atas permintaan orang lain.</li>
          <li>PIN 4 digit hanya muncul <strong>sekali</strong> setelah dibuat. Setelah dialog ditutup, PIN tidak bisa dilihat lagi dan harus dibuat ulang.</li>
          <li>Mengganti PIN juga membuka kunci akun bila terkunci.</li>
        </ul>
        <div class="adm-field">
          <label class="adm-label" for="pin-custom">PIN sendiri (kosongkan untuk PIN acak)</label>
          <input id="pin-custom" v-model="pinModal.custom" data-autofocus type="text" inputmode="numeric" maxlength="4" autocomplete="off" class="adm-input adm-input--mono" placeholder="Acak" />
        </div>
        <p v-if="pinModal.error" class="adm-alert" role="alert">{{ pinModal.error }}</p>
      </template>

      <!-- Langkah 2: tampil sekali + bagikan -->
      <template v-else>
        <p class="adm-hint">PIN {{ pinModal.result.had_pin ? 'baru' : '' }} untuk {{ pinModal.customer?.phone }}</p>
        <p class="lc-pin-once adm-mono" aria-live="polite">{{ pinModal.result.pin }}</p>
        <p class="lc-pin-warn">Catat atau kirim sekarang. PIN ini tidak bisa dilihat lagi setelah dialog ditutup.</p>
      </template>

      <template #footer>
        <template v-if="!pinModal.result">
          <button type="button" class="adm-btn adm-btn--ghost" :disabled="pinModal.busy" @click="closePin">Batal</button>
          <button type="button" class="adm-btn adm-btn--primary" :disabled="pinModal.busy" @click="createPin">
            <span v-if="pinModal.busy" class="adm-spinner"></span>
            {{ pinModal.busy ? 'Membuat...' : (pinModal.customer?.has_pin ? 'Buat PIN baru' : 'Buat PIN') }}
          </button>
        </template>
        <template v-else>
          <button type="button" class="adm-btn adm-btn--ghost" @click="closePin">Selesai</button>
          <button type="button" class="adm-btn adm-btn--ghost" @click="copyPin">Salin PIN</button>
          <button type="button" class="adm-btn adm-btn--primary" @click="shareWa">Kirim lewat WhatsApp</button>
        </template>
      </template>
    </AdminModal>

    <!-- ── MODAL HAPUS (hard delete, konfirmasi kuat) ─────────────── -->
    <AdminModal
      :model-value="delModal.open"
      :title="delTitle"
      :persistent="delModal.busy"
      @close="closeDelete"
    >
      <p class="adm-error">Tidak bisa dibatalkan</p>
      <ul class="lc-list">
        <li>Member dihapus <strong>permanen</strong>, termasuk saldo poin dan seluruh riwayat penyesuaian poin (jejak audit ikut hilang).</li>
        <li>Pesanan lama <strong>tidak</strong> ikut terhapus, jadi laporan omzet dan prediksi tidak berubah.</li>
        <li>Kalau nomor ini memesan lagi, member baru dibuat dari nol.</li>
      </ul>
      <div v-if="delModal.mode !== 'single'" class="adm-field">
        <label class="adm-label" for="del-confirm">Ketik <strong>HAPUS</strong> untuk melanjutkan</label>
        <input id="del-confirm" v-model="delModal.text" data-autofocus type="text" autocomplete="off" class="adm-input" placeholder="HAPUS" />
      </div>

      <template #footer>
        <button type="button" class="adm-btn adm-btn--ghost" :disabled="delModal.busy" @click="closeDelete">Batal</button>
        <button type="button" class="adm-btn adm-btn--primary" :disabled="!canConfirmDelete || delModal.busy" @click="confirmDelete">
          <span v-if="delModal.busy" class="adm-spinner"></span>
          {{ delModal.busy ? 'Menghapus...' : 'Hapus permanen' }}
        </button>
      </template>
    </AdminModal>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useRouteSearch } from "@/composables/useRouteSearch";
import { useAuthStore } from "@/stores/auth";
import { useLoyaltyStore } from "@/stores/loyalty";
import { toast } from "vue-sonner";
import apiClient from "@/api/client";
import { statsAPI } from "@/api/stats";
import { RefreshCw, Users, UserCheck, Coins, AlertTriangle } from "lucide-vue-next";
import AdminModal from "@/components/ui/admin/Adminmodal.vue";

const auth    = useAuthStore();
const loyalty = useLoyaltyStore();
const router  = useRouter();

const showAdjustModal = ref(false);
const selectedCustomer  = ref(null);
const adjustAmount      = ref(null);
const adjustNote        = ref("");
const isSaving          = ref(false);
const expiryMonths      = computed(() => loyalty.expiryMonths);

const fetchAdminLoyalData = () => loyalty.fetchLoyalCustomers();

// ── Segmentasi & saringan ───────────────────────────────────────────
const segmentFilter = ref(null);
const searchQuery = ref("");
useRouteSearch(searchQuery); // ?q= dari pencarian global
const filteredCustomers = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  return loyalty.loyalCustomers.filter(c =>
    (!segmentFilter.value || c.segment === segmentFilter.value) &&
    (!q || String(c.name || "").toLowerCase().includes(q) || String(c.phone || "").includes(q))
  );
});
const segmentInfo = (key) => loyalty.segments.find(s => s.key === key);
const segmentLabel = (key) => segmentInfo(key)?.label || key || '—';
const segmentHint = (key) => segmentInfo(key)?.hint || '';
const SEGMENT_BADGE = { setia: 'adm-badge--purple', aktif: 'adm-badge--green', baru: 'adm-badge--blue', berisiko: 'adm-badge--amber' };
const segmentBadge = (key) => SEGMENT_BADGE[key] || '';
const activeSegmentHint = computed(() => (segmentFilter.value ? segmentHint(segmentFilter.value) : ''));

// ── Pilih & hapus ───────────────────────────────────────────────────
const selected = ref(new Set());
const someSelected = computed(() => selected.value.size > 0);
const allVisibleSelected = computed(
  () => filteredCustomers.value.length > 0 && filteredCustomers.value.every(c => selected.value.has(c.phone))
);
const toggleOne = (phone) => {
  const next = new Set(selected.value);
  next.has(phone) ? next.delete(phone) : next.add(phone);
  selected.value = next;
};
const toggleAllVisible = () => {
  const next = new Set(selected.value);
  if (allVisibleSelected.value) filteredCustomers.value.forEach(c => next.delete(c.phone));
  else filteredCustomers.value.forEach(c => next.add(c.phone));
  selected.value = next;
};

// ── PIN member ──────────────────────────────────────────────────────
const formatShortDate = (iso) =>
  iso ? new Date(iso).toLocaleDateString("id-ID", { day: "numeric", month: "short" }) : "—";

const pinModal = ref({ open: false, customer: null, custom: "", busy: false, error: "", result: null, shared: false });

const openPin = (customer) => {
  pinModal.value = { open: true, customer, custom: "", busy: false, error: "", result: null, shared: false };
};

const closePin = () => {
  const m = pinModal.value;
  if (m.busy) return;
  if (m.result && !m.shared && !window.confirm("PIN belum dikirim dan tidak bisa dilihat lagi setelah ditutup. Tutup juga?")) return;
  m.open = false;
  m.result = null;
};

const createPin = async () => {
  const m = pinModal.value;
  const custom = m.custom.trim();
  if (custom && !/^\d{4}$/.test(custom)) { m.error = "PIN harus 4 digit angka"; return; }
  m.busy = true;
  m.error = "";
  try {
    const { data } = await statsAPI.setLoyalCustomerPin(m.customer.phone, custom);
    m.result = { pin: data.pin, had_pin: data.had_pin };
    fetchAdminLoyalData();
  } catch (err) {
    m.error = err?.response?.data?.detail || "Gagal membuat PIN";
  } finally {
    m.busy = false;
  }
};

// 08xx → 628xx (sama seperti nomor admin di Pengaturan Toko)
const toWaNumber = (phone) => {
  const d = String(phone || "").replace(/\D/g, "");
  if (d.startsWith("62")) return d;
  if (d.startsWith("0")) return "62" + d.slice(1);
  return "62" + d;
};

const pinMessage = (phone, pin, changed) =>
  changed
    ? `Halo Kak, PIN member Masashimura untuk nomor ${phone} telah diganti. PIN baru Kakak: ${pin}. Mohon dijaga kerahasiaannya dan tidak dibagikan kepada siapa pun. Jika lupa PIN atau ingin menggantinya lagi, cukup balas pesan ini dan admin akan membantu.`
    : `Halo Kak, PIN member Masashimura untuk nomor ${phone} adalah ${pin}. PIN ini rahasia, mohon tidak dibagikan kepada siapa pun, termasuk pihak kami. Gunakan PIN ini untuk melihat dan menukar poin di web. Jika lupa PIN atau ingin menggantinya, cukup balas pesan ini dan admin akan membantu.`;

const shareWa = () => {
  const m = pinModal.value;
  if (!m.result) return;
  const text = pinMessage(m.customer.phone, m.result.pin, m.result.had_pin);
  window.open(`https://wa.me/${toWaNumber(m.customer.phone)}?text=${encodeURIComponent(text)}`, "_blank", "noopener");
  m.shared = true;
};

const copyPin = async () => {
  const m = pinModal.value;
  try {
    await navigator.clipboard.writeText(m.result.pin);
    m.shared = true;
    toast.success("PIN disalin");
  } catch {
    toast.error("Gagal menyalin, catat PIN secara manual");
  }
};

const CONFIRM_TEXT = "HAPUS";
const delModal = ref({ open: false, mode: "single", phones: [], text: "", busy: false });
const delTitle = computed(() => {
  const m = delModal.value;
  if (m.mode === "all") return `Hapus SEMUA member (${loyalty.loyalCustomers.length})`;
  if (m.mode === "selected") return `Hapus ${m.phones.length} member terpilih`;
  return `Hapus member ${m.phones[0] || ""}`;
});
const canConfirmDelete = computed(
  () => delModal.value.mode === "single" || delModal.value.text.trim() === CONFIRM_TEXT
);
const openSingleDelete = (c) => { delModal.value = { open: true, mode: "single", phones: [c.phone], text: "", busy: false }; };
const openBulkDelete = (mode) => {
  const phones = mode === "all" ? [] : [...selected.value];
  if (mode === "selected" && !phones.length) return;
  delModal.value = { open: true, mode, phones, text: "", busy: false };
};
const closeDelete = () => { if (!delModal.value.busy) delModal.value.open = false; };

const confirmDelete = async () => {
  const m = delModal.value;
  if (!canConfirmDelete.value || m.busy) return;
  m.busy = true;
  try {
    let res;
    if (m.mode === "single") res = await statsAPI.deleteLoyalCustomer(m.phones[0]);
    else if (m.mode === "all") res = await statsAPI.bulkDeleteLoyalCustomers({ all: true, confirm: CONFIRM_TEXT });
    else res = await statsAPI.bulkDeleteLoyalCustomers({ phones: m.phones, confirm: CONFIRM_TEXT });
    toast.success(`${res.data?.deleted ?? 0} member dihapus permanen`);
    selected.value = new Set();
    m.open = false;
    fetchAdminLoyalData();
  } catch (err) {
    toast.error(err?.response?.data?.detail || "Gagal menghapus member");
  } finally {
    m.busy = false;
  }
};

const expiryLabel = computed(() =>
  expiryMonths.value > 0 ? `${expiryMonths.value} bulan tidak order` : 'tidak pernah hangus (nonaktif)'
);
const activePointsCount = computed(() => loyalty.loyalCustomers.filter(c => c.points > 0).length);
const totalPointsOutstanding = computed(() =>
  loyalty.loyalCustomers.reduce((sum, c) => sum + (c.points || 0), 0)
);

const formatPrice = (price) =>
  new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", minimumFractionDigits: 0 }).format(price || 0);

const formatDate = (iso) => {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" });
};

const openAdjustModal = (customer) => {
  selectedCustomer.value  = customer;
  adjustAmount.value      = null;
  adjustNote.value        = "";
  showAdjustModal.value   = true;
};

const saveAdjustPoints = async () => {
  if (!adjustAmount.value) { toast.error("Masukkan jumlah poin (bukan 0)"); return; }
  if (!adjustNote.value.trim()) { toast.error("Alasan wajib diisi"); return; }

  isSaving.value = true;
  try {
    await apiClient.post(`/orders/adjust-points/${selectedCustomer.value.phone}/`, {
      amount: adjustAmount.value,
      note:   adjustNote.value.trim(),
    });
    toast.success(`Poin ${selectedCustomer.value.phone} disesuaikan (${adjustAmount.value > 0 ? '+' : ''}${adjustAmount.value})`);
    showAdjustModal.value = false;
    fetchAdminLoyalData();
  } catch (err) {
    toast.error(err?.response?.data?.detail || "Gagal menyimpan adjustment poin");
  } finally {
    isSaving.value = false;
  }
};

const refreshData = () => fetchAdminLoyalData();

onMounted(() => {
  if (!auth.user) { router.push("/login"); return; }
  fetchAdminLoyalData();
});
</script>

<style scoped>
/* Halaman memakai primitif bersama (admin-ui.css); di sini hanya yang spesifik. */
.lc-body { display: flex; flex-direction: column; gap: 0.75rem; padding: 1rem 1.35rem 0.85rem; }
.lc-spinner { width: 28px; height: 28px; border-top-color: var(--accent); }

.lc-seg { flex-wrap: wrap; overflow: visible; }
.lc-seg .adm-seg-btn strong { font-variant-numeric: tabular-nums; }

.lc-del-bar { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0.75rem; }
.lc-del-actions { display: flex; flex-wrap: wrap; gap: 0.5rem; }

.lc-table { min-width: 0; }
.lc-check { width: 36px; }
.lc-phone { display: flex; flex-direction: column; gap: 0.15rem; }
.lc-phone-val { font-weight: 700; color: var(--text); letter-spacing: 0.04em; }
.lc-sub { font-size: 0.75rem; color: var(--text-dim); }
.lc-sub.is-soon { color: var(--amber-soft); font-weight: 600; }
.lc-block { display: block; margin-top: 0.15rem; }
.lc-dim { font-size: 0.75rem; color: var(--text-dim); }
.lc-strong { font-size: 1.05rem; font-weight: 700; color: var(--text); }
.lc-spend { font-weight: 700; color: var(--amber-soft); }
.lc-actions { display: flex; flex-wrap: wrap; justify-content: center; gap: 0.4rem; }

.lc-balance { padding: 0.9rem 1.1rem; border: 1px solid var(--border); border-radius: var(--r-md); background: var(--surface-2); }
.lc-balance-val { margin: 0.2rem 0 0; font-family: var(--font-display); font-size: 1.6rem; color: var(--green-soft); }

.lc-list { margin: 0; padding-left: 1.1rem; font-size: 0.875rem; line-height: 1.6; color: var(--text-dim); }
.lc-list strong { color: var(--text); }
.lc-pin-once { margin: 0; font-size: 2.5rem; font-weight: 700; letter-spacing: 0.3em; text-align: center; color: var(--text); }
.lc-pin-warn { margin: 0; font-size: 0.8125rem; text-align: center; color: var(--amber-soft); }

@media (max-width: 720px) {
  .lc-actions { width: 100%; flex-direction: column; }
  .lc-actions .adm-btn { width: 100%; }
  .lc-phone { align-items: flex-start; }
}
</style>
