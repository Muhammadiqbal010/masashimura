<template>
  <div class="lc-root">

    <!-- ── PAGE HEADER ─────────────────────────────────────────────── -->
    <div class="lc-header">
      <div>
        <p class="lc-eyebrow">Masashimura · Program Loyalitas</p>
        <h1 class="lc-title">Loyal Customers</h1>
        <p class="lc-subtitle">Poin didapat dari belanja, ditukar jadi menu gratis — hangus kalau {{ expiryLabel }}</p>
      </div>
      <button @click="refreshData" class="refresh-btn">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
        </svg>
        Refresh
      </button>
    </div>

    <!-- ── STAT CARDS ─────────────────────────────────────────────── -->
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-top">
          <span class="stat-label">Total Member</span>
          <span class="stat-dot dot-white"></span>
        </div>
        <div class="stat-val">{{ loyalty.loyalCustomers.length }}</div>
        <div class="stat-note">terdaftar di sistem</div>
      </div>
      <div class="stat-card stat-green">
        <div class="stat-top">
          <span class="stat-label">Punya Poin Aktif</span>
          <span class="stat-dot dot-green"></span>
        </div>
        <div class="stat-val val-green">{{ activePointsCount }}</div>
        <div class="stat-note">saldo poin &gt; 0</div>
      </div>
      <div class="stat-card stat-amber">
        <div class="stat-top">
          <span class="stat-label">Total Poin Beredar</span>
          <span class="stat-dot dot-amber"></span>
        </div>
        <div class="stat-val val-amber">{{ totalPointsOutstanding }}</div>
        <div class="stat-note">akumulasi semua member</div>
      </div>
    </div>

    <!-- ── LOADING ─────────────────────────────────────────────────── -->
    <div v-if="loyalty.loading" class="loading-state">
      <div class="spinner"></div>
      <p>Memuat data pelanggan...</p>
    </div>

    <!-- ── ERROR ──────────────────────────────────────────────────── -->
    <div v-else-if="loyalty.error" class="table-card">
      <div class="empty-cell">
        <div class="empty-icon">⚠️</div>
        <p class="empty-text">{{ loyalty.error }}</p>
        <button type="button" class="action-btn action-active" @click="fetchAdminLoyalData">Coba lagi</button>
      </div>
    </div>

    <!-- ── TABLE ──────────────────────────────────────────────────── -->
    <div v-else class="table-card">
      <div class="table-card-head">
        <p class="card-eyebrow">Daftar Pelanggan</p>
        <h3 class="card-title-sm">{{ filteredCustomers.length }} dari {{ loyalty.loyalCustomers.length }} customer</h3>
      </div>

      <p class="exp-rule">
        <template v-if="expiryMonths > 0">
          Poin hangus kalau pelanggan <strong>tidak belanja selama {{ expiryMonths }} bulan</strong> sejak order terakhir.
          Setiap order baru memulai hitungan dari awal. Kolom Hangus adalah perkiraan bila pelanggan tidak order lagi.
        </template>
        <template v-else>Kedaluwarsa poin sedang dimatikan, jadi poin tidak pernah hangus. Atur di Pengaturan Loyalty.</template>
      </p>

      <!-- Segmentasi: klik chip untuk menyaring -->
      <div v-if="loyalty.segments.length" class="seg-chips" role="group" aria-label="Saring menurut segmen">
        <button
          v-for="s in loyalty.segments"
          :key="s.key"
          type="button"
          class="seg-chip"
          :class="[`seg-${s.key}`, { 'is-on': segmentFilter === s.key }]"
          :aria-pressed="segmentFilter === s.key"
          :title="s.hint"
          @click="segmentFilter = segmentFilter === s.key ? null : s.key"
        >
          <span class="seg-chip-n">{{ s.count }}</span>
          <span class="seg-chip-l">{{ s.label }}</span>
        </button>
      </div>
      <p v-if="activeSegmentHint" class="seg-hint">{{ activeSegmentHint }}</p>

      <!-- Toolbar hapus -->
      <div v-if="loyalty.loyalCustomers.length" class="del-bar">
        <label class="del-all">
          <input type="checkbox" :checked="allVisibleSelected" :indeterminate.prop="someSelected && !allVisibleSelected" @change="toggleAllVisible" />
          Pilih semua yang tampil
        </label>
        <div class="del-actions">
          <button type="button" class="action-btn del-btn" :disabled="!selected.size" @click="openBulkDelete('selected')">
            Hapus terpilih ({{ selected.size }})
          </button>
          <button type="button" class="action-btn del-btn" @click="openBulkDelete('all')">Hapus semua</button>
        </div>
      </div>

      <div class="table-scroll">
        <table class="lc-table lc-table--stack">
          <thead>
            <tr>
              <th class="th-center th-check"><span class="sr-only">Pilih</span></th>
              <th>Pelanggan</th>
              <th class="th-center">Segmen</th>
              <th>Order Terakhir</th>
              <th class="th-center">Total Order</th>
              <th class="th-right">Total Belanja</th>
              <th class="th-center">Poin</th>
              <th class="th-center">Hangus</th>
              <th class="th-center">Status</th>
              <th class="th-center">PIN</th>
              <th class="th-center">Aksi</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="customer in filteredCustomers"
              :key="customer.phone"
              class="lc-row"
            >
              <td class="td-center td-check" data-label="Pilih">
                <input type="checkbox" :checked="selected.has(customer.phone)" :aria-label="'Pilih ' + customer.phone" @change="toggleOne(customer.phone)" />
              </td>

              <!-- Phone -->
              <td class="td-phone td-first">
                <span class="phone-val">{{ customer.phone }}</span>
                <span v-if="customer.name" class="phone-name">{{ customer.name }}</span>
              </td>

              <!-- Segmen -->
              <td class="td-center" data-label="Segmen">
                <span class="seg-pill" :class="`seg-${customer.segment}`" :title="segmentHint(customer.segment)">
                  {{ segmentLabel(customer.segment) }}
                </span>
                <span v-if="customer.days_since_last_order != null" class="seg-days">{{ customer.days_since_last_order }} hari lalu</span>
              </td>

              <!-- Order terakhir -->
              <td class="td-period" data-label="Order terakhir">{{ customer.last_order_at ? formatDate(customer.last_order_at) : '—' }}</td>

              <!-- Total order -->
              <td class="td-center" data-label="Total order">
                <span class="order-count">{{ customer.total_orders || 0 }}</span>
                <span class="order-unit">order</span>
              </td>

              <!-- Belanja -->
              <td class="td-right td-spend" data-label="Total belanja">{{ formatPrice(customer.total_spent) }}</td>

              <!-- Poin -->
              <td class="td-center" data-label="Poin">
                <div v-if="customer.points > 0" class="discount-badge badge-green">
                  <span class="discount-pct">{{ customer.points }}</span>
                  <span class="discount-lbl">Poin</span>
                </div>
                <span v-else class="no-discount">0</span>
              </td>

              <!-- Kapan poin hangus -->
              <td class="td-center" data-label="Hangus">
                <span v-if="customer.expiry_state === 'off' || customer.expiry_state === 'none'" class="no-discount">—</span>
                <span v-else-if="customer.expiry_state === 'expired'" class="exp-pill">Sudah hangus</span>
                <template v-else>
                  <span class="exp-date">{{ formatDate(customer.expiry_estimate) }}</span>
                  <span class="exp-days" :class="{ 'is-soon': customer.expiry_state === 'soon' }">
                    {{ customer.days_until_expiry > 0 ? customer.days_until_expiry + ' hari lagi' : 'hari ini' }}
                  </span>
                </template>
              </td>

              <!-- Status -->
              <td class="td-center" data-label="Status">
                <span
                  v-if="customer.points_expired"
                  class="status-pill pill-regular"
                  :title="'Poin sudah hangus (order terakhir ' + formatDate(customer.last_order_at) + ')'"
                >
                  Poin Hangus
                </span>
                <span v-else-if="customer.points > 0" class="status-pill pill-loyal">Aktif</span>
                <span v-else class="status-pill pill-regular">Belum Ada Poin</span>
              </td>

              <!-- PIN -->
              <td class="td-center" data-label="PIN">
                <span v-if="customer.pin_locked" class="pin-state pin-state--locked">Terkunci</span>
                <span v-else-if="customer.has_pin" class="pin-state">Diatur {{ formatShortDate(customer.pin_set_at) }}</span>
                <span v-else class="pin-state pin-state--none">Belum diatur</span>
              </td>

              <!-- Aksi -->
              <td class="td-center td-action">
                <button @click="openAdjustModal(customer)" class="action-btn action-active">
                  Adjust Poin
                </button>
                <button type="button" class="action-btn" @click="openPin(customer)">
                  {{ customer.has_pin ? 'Ganti PIN' : 'Atur PIN' }}
                </button>
                <button type="button" class="action-btn del-btn" @click="openSingleDelete(customer)">Hapus</button>
              </td>
            </tr>

            <tr v-if="filteredCustomers.length === 0">
              <td colspan="11" class="empty-cell">
                <div class="empty-icon">👥</div>
                <p class="empty-text">{{ segmentFilter ? 'Tidak ada pelanggan di segmen ini' : 'Belum ada data pelanggan' }}</p>
                <p class="empty-hint">{{ segmentFilter ? 'Pilih segmen lain atau hapus saringan.' : 'Data muncul setelah ada transaksi pertama dari nomor HP customer' }}</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── MODAL DISKON ───────────────────────────────────────────── -->
    <transition
      enter-active-class="modal-enter-active"
      enter-from-class="modal-enter-from"
      leave-active-class="modal-leave-active"
      leave-to-class="modal-leave-to"
    >
      <div
        v-if="showAdjustModal"
        class="modal-overlay"
        @click.self="showAdjustModal = false"
      >
        <div class="modal-box">

          <!-- Modal header -->
          <div class="modal-header">
            <div>
              <p class="modal-eyebrow">Program Loyalitas</p>
              <h3 class="modal-title">Adjust Poin</h3>
              <p class="modal-phone">{{ selectedCustomer?.phone }}</p>
            </div>
            <button class="modal-close" @click="showAdjustModal = false">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M18 6L6 18M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <!-- Saldo saat ini -->
          <div class="current-discount">
            <p class="current-label">Saldo Poin Saat Ini</p>
            <div class="current-val-wrap">
              <span class="current-pct current-green">{{ selectedCustomer?.points ?? 0 }}</span>
              <span class="current-type">Poin</span>
            </div>
          </div>

          <!-- Input jumlah -->
          <div class="modal-field">
            <label class="modal-field-label">Jumlah Adjust (+ nambah / - kurangin)</label>
            <input
              v-model.number="adjustAmount"
              type="number"
              placeholder="Contoh: 10 atau -5"
              class="modal-input"
            />
            <p class="modal-hint">Saldo baru: {{ (selectedCustomer?.points ?? 0) + (adjustAmount || 0) }} poin</p>
          </div>

          <!-- Alasan (wajib) -->
          <div class="modal-field">
            <label class="modal-field-label">Alasan <span style="color:#D71920;">*</span></label>
            <input
              v-model="adjustNote"
              type="text"
              placeholder="Contoh: kompensasi komplain, bonus ulang tahun"
              class="modal-input"
            />
          </div>

          <!-- Actions -->
          <div class="modal-actions">
            <button @click="saveAdjustPoints" :disabled="isSaving" class="modal-save-btn">
              <span v-if="isSaving" class="btn-spinner"></span>
              {{ isSaving ? 'Menyimpan...' : 'Simpan Adjustment' }}
            </button>
            <button @click="showAdjustModal = false" class="modal-cancel-btn">Batal</button>
          </div>

        </div>
      </div>
    </transition>

    <!-- ── MODAL PIN MEMBER ─────────────────────────────────────────── -->
    <div v-if="pinModal.open" class="modal-overlay" @click.self="closePin">
      <div class="modal-box" role="dialog" aria-modal="true" aria-labelledby="pin-title">
        <div class="modal-header">
          <div>
            <p class="modal-eyebrow">PIN member</p>
            <h3 id="pin-title" class="modal-title">{{ pinModal.customer?.has_pin ? 'Ganti PIN' : 'Atur PIN' }}</h3>
            <p class="modal-phone">{{ pinModal.customer?.phone }}</p>
          </div>
          <button class="modal-close" aria-label="Tutup" @click="closePin">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>

        <!-- Langkah 1: buat -->
        <template v-if="!pinModal.result">
          <ul class="del-list">
            <li v-if="pinModal.customer?.has_pin"><strong>Pastikan permintaan datang dari WhatsApp nomor ini sendiri.</strong> Jangan mengganti PIN atas permintaan orang lain.</li>
            <li>PIN 4 digit hanya muncul <strong>sekali</strong> setelah dibuat. Setelah dialog ditutup, PIN tidak bisa dilihat lagi dan harus dibuat ulang.</li>
            <li>Mengganti PIN juga membuka kunci akun bila terkunci.</li>
          </ul>
          <div class="modal-field">
            <label class="modal-field-label" for="pin-custom">PIN sendiri (kosongkan untuk PIN acak)</label>
            <input id="pin-custom" v-model="pinModal.custom" type="text" inputmode="numeric" maxlength="4" autocomplete="off" class="modal-input" placeholder="Acak" />
          </div>
          <p v-if="pinModal.error" class="pin-err" role="alert">{{ pinModal.error }}</p>
          <div class="modal-actions">
            <button class="modal-save-btn" :disabled="pinModal.busy" @click="createPin">
              <span v-if="pinModal.busy" class="btn-spinner"></span>
              {{ pinModal.busy ? 'Membuat...' : (pinModal.customer?.has_pin ? 'Buat PIN baru' : 'Buat PIN') }}
            </button>
            <button class="modal-cancel-btn" @click="closePin">Batal</button>
          </div>
        </template>

        <!-- Langkah 2: tampil sekali + bagikan -->
        <template v-else>
          <p class="pin-once-label">PIN {{ pinModal.result.had_pin ? 'baru' : '' }} untuk {{ pinModal.customer?.phone }}</p>
          <p class="pin-once" aria-live="polite">{{ pinModal.result.pin }}</p>
          <p class="pin-once-warn">Catat atau kirim sekarang. PIN ini tidak bisa dilihat lagi setelah dialog ditutup.</p>
          <div class="modal-actions">
            <button class="modal-save-btn" @click="shareWa">Kirim lewat WhatsApp</button>
            <button class="modal-cancel-btn" @click="copyPin">Salin PIN</button>
            <button class="modal-cancel-btn" @click="closePin">Selesai</button>
          </div>
        </template>
      </div>
    </div>

    <!-- ── MODAL HAPUS (hard delete, konfirmasi kuat) ─────────────── -->
    <div v-if="delModal.open" class="modal-overlay" @click.self="closeDelete">
      <div class="modal-box" role="dialog" aria-modal="true" aria-labelledby="del-title">
        <div class="modal-header">
          <div>
            <p class="modal-eyebrow">Tidak bisa dibatalkan</p>
            <h3 id="del-title" class="modal-title">{{ delTitle }}</h3>
          </div>
          <button class="modal-close" aria-label="Tutup" @click="closeDelete">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <ul class="del-list">
          <li>Member dihapus <strong>permanen</strong>, termasuk saldo poin dan seluruh riwayat penyesuaian poin (jejak audit ikut hilang).</li>
          <li>Pesanan lama <strong>tidak</strong> ikut terhapus, jadi laporan omzet dan prediksi tidak berubah.</li>
          <li>Kalau nomor ini memesan lagi, member baru dibuat dari nol.</li>
        </ul>
        <div v-if="delModal.mode !== 'single'" class="modal-field">
          <label class="modal-field-label" for="del-confirm">Ketik <strong>HAPUS</strong> untuk melanjutkan</label>
          <input id="del-confirm" v-model="delModal.text" type="text" autocomplete="off" class="modal-input" placeholder="HAPUS" />
        </div>
        <div class="modal-actions">
          <button class="modal-save-btn del-confirm-btn" :disabled="!canConfirmDelete || delModal.busy" @click="confirmDelete">
            <span v-if="delModal.busy" class="btn-spinner"></span>
            {{ delModal.busy ? 'Menghapus...' : 'Hapus permanen' }}
          </button>
          <button class="modal-cancel-btn" @click="closeDelete">Batal</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useLoyaltyStore } from "@/stores/loyalty";
import { toast } from "vue-sonner";
import apiClient from "@/api/client";
import { statsAPI } from "@/api/stats";

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
const filteredCustomers = computed(() =>
  segmentFilter.value
    ? loyalty.loyalCustomers.filter(c => c.segment === segmentFilter.value)
    : loyalty.loyalCustomers
);
const segmentInfo = (key) => loyalty.segments.find(s => s.key === key);
const segmentLabel = (key) => segmentInfo(key)?.label || key || '—';
const segmentHint = (key) => segmentInfo(key)?.hint || '';
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
/* ── Root ─────────────────────────────────────────────────────────── */
.lc-root {
  min-height: 100vh; min-height: 100dvh;
  background: var(--bg);
  color: var(--text);
  padding: 2rem 1.5rem;
  max-width: 1280px;
  margin: 0 auto;
  font-family: 'Inter', sans-serif;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* ── Header ──────────────────────────────────────────────────────── */
.lc-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgb(var(--ink) / 0.06);
  flex-wrap: wrap;
}
.lc-eyebrow {
  font-family: 'Manrope', system-ui, sans-serif;
  font-size: 0.72rem; letter-spacing: 0.2em;
  text-transform: uppercase; color: var(--accent-text);
  margin: 0 0 0.3rem;
}
.lc-title {
  font-family: 'Manrope', system-ui, sans-serif;
  font-size: 1.75rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.04em; margin: 0 0 0.3rem;
}
.lc-subtitle { font-size: 0.7rem; color: var(--text-faint); margin: 0; }

.refresh-btn {
  display: flex; align-items: center; gap: 0.45rem;
  padding: 0.55rem 1rem;
  background: rgb(var(--ink) / 0.04);
  border: 1px solid rgb(var(--ink) / 0.08);
  border-radius: 10px; color: var(--text-dim);
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.72rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: all 0.15s;
}
.refresh-btn:hover { background: rgb(var(--ink) / 0.08); color: var(--text); border-color: rgb(var(--ink) / 0.15); }

/* ── Stat grid ───────────────────────────────────────────────────── */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}
@media (max-width: 640px) { .stat-grid { grid-template-columns: 1fr; } }

.stat-card {
  background: var(--surface);
  border: 1px solid rgb(var(--ink) / 0.05);
  border-radius: 16px; padding: 1.3rem 1.5rem;
  position: relative; overflow: hidden;
}
.stat-card::before {
  content: ''; position: absolute;
  top: 0; left: 0; right: 0; height: 2px;
  background: rgb(var(--ink) / 0.06);
}
.stat-green::before { background: #22c55e; }
.stat-amber::before { background: #FFD400; }

.stat-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.65rem; }
.stat-label {
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.72rem;
  letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--text-faint);
}
.stat-dot { width: 6px; height: 6px; border-radius: 50%; }
.dot-white { background: rgb(var(--ink) / 0.2); }
.dot-green { background: #22c55e; }
.dot-amber { background: #FFD400; }

.stat-val {
  font-family: monospace; font-size: 1.8rem; font-weight: 700;
  color: var(--text); letter-spacing: -0.02em; margin-bottom: 0.3rem;
}
.val-green { color: var(--green-soft); }
.val-amber { color: var(--amber-soft); }
.stat-note { font-size: 0.72rem; color: var(--text-faint); }

/* ── Loading ─────────────────────────────────────────────────────── */
.loading-state {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 1rem; padding: 5rem 2rem;
  background: var(--surface); border: 1px solid rgb(var(--ink) / 0.05);
  border-radius: 16px;
  color: var(--text-faint); font-family: 'Manrope', system-ui, sans-serif;
  font-size: 0.7rem; letter-spacing: 0.15em; text-transform: uppercase;
}
.spinner {
  width: 28px; height: 28px;
  border: 2px solid rgb(var(--ink) / 0.07); border-top-color: #D71920;
  border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Table card ──────────────────────────────────────────────────── */
.table-card {
  background: var(--surface);
  border: 1px solid rgb(var(--ink) / 0.05);
  border-radius: 16px; overflow: hidden;
}
.table-card-head {
  padding: 1.1rem 1.5rem;
  border-bottom: 1px solid rgb(var(--ink) / 0.05);
}
.card-eyebrow {
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.72rem;
  letter-spacing: 0.18em; text-transform: uppercase;
  color: var(--accent-text); margin: 0 0 0.15rem;
}
.card-title-sm {
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.82rem;
  font-weight: 500; text-transform: uppercase;
  letter-spacing: 0.08em; color: var(--text-dim); margin: 0;
}

.table-scroll { overflow-x: auto; }
.lc-table { width: 100%; border-collapse: collapse; min-width: 700px; }

.lc-table th {
  padding: 0.65rem 1.25rem;
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.72rem; font-weight: 400;
  letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--text-faint); text-align: left;
  background: rgb(var(--ink) / 0.015);
  border-bottom: 1px solid rgb(var(--ink) / 0.04);
  white-space: nowrap;
}
.th-center { text-align: center; }
.th-right  { text-align: right; }

.lc-row {
  border-bottom: 1px solid rgb(var(--ink) / 0.04);
  transition: background 0.12s;
}
.lc-row:hover { background: rgb(var(--ink) / 0.02); }
.lc-row:last-child { border-bottom: none; }

.lc-table td { padding: 0.9rem 1.25rem; font-size: 0.83rem; vertical-align: middle; }

.td-phone .phone-val { font-family: monospace; font-weight: 700; color: var(--text); letter-spacing: 0.04em; }
.td-phone { display: flex; flex-direction: column; gap: 0.15rem; }
.td-phone .phone-name { font-size: 0.72rem; color: var(--text-dim); }
.td-period { font-size: 0.75rem; color: var(--text-faint); font-family: monospace; }
.td-center { text-align: center; }
.td-right  { text-align: right; }
.td-spend  { font-family: monospace; font-weight: 700; color: var(--amber-soft); }

.order-count { font-family: monospace; font-size: 1.1rem; font-weight: 700; color: var(--text); }
.order-unit  { font-size: 0.72rem; color: var(--text-faint); margin-left: 0.25rem; }

/* Discount badge */
.discount-badge {
  display: inline-flex; flex-direction: column; align-items: center; gap: 0.1rem;
  padding: 0.25rem 0.65rem; border-radius: 8px;
}
.badge-red  { background: color-mix(in srgb, var(--accent) 8%, transparent);  border: 1px solid color-mix(in srgb, var(--accent) 18%, transparent); }
.badge-green{ background: color-mix(in srgb, var(--green) 8%, transparent);  border: 1px solid color-mix(in srgb, var(--green) 18%, transparent); }
.discount-pct {
  font-family: 'Manrope', system-ui, sans-serif; font-size: 1rem; font-weight: 600; line-height: 1;
}
.badge-red  .discount-pct { color: var(--red-soft); }
.badge-green .discount-pct { color: var(--green-soft); }
.discount-lbl {
  font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--text-faint); font-family: 'Manrope', system-ui, sans-serif;
}
.no-discount { color: var(--text-faint); font-size: 0.85rem; }

/* Status pill */
.status-pill {
  display: inline-block; padding: 0.22rem 0.7rem;
  border-radius: 100px; font-size: 0.72rem;
  font-family: 'Manrope', system-ui, sans-serif; letter-spacing: 0.1em; text-transform: uppercase;
}
.pill-loyal   { background: color-mix(in srgb, var(--green) 10%, transparent);  color: var(--green-soft); border: 1px solid color-mix(in srgb, var(--green) 20%, transparent); }
.pill-regular { background: rgb(var(--ink) / 0.04); color: var(--text-faint); border: 1px solid rgb(var(--ink) / 0.08); }

/* Action button */
.action-btn {
  padding: 0.35rem 0.85rem; border-radius: 8px;
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.72rem;
  letter-spacing: 0.08em; text-transform: uppercase; cursor: pointer;
  transition: all 0.15s; border: 1px solid;
}
.action-active {
  background: color-mix(in srgb, var(--accent) 8%, transparent); border-color: color-mix(in srgb, var(--accent) 25%, transparent); color: var(--red-soft);
}
.action-active:hover { background: #D71920; border-color: #D71920; color: #fff; }
.action-disabled {
  background: transparent; border-color: rgb(var(--ink) / 0.05);
  color: var(--text-faint); cursor: not-allowed;
}

/* Empty state */
.empty-cell { padding: 4rem !important; text-align: center; }
.empty-icon { font-size: 2rem; margin-bottom: 0.75rem; }
.empty-text { color: var(--text-faint); font-size: 0.85rem; margin: 0 0 0.3rem; }
.empty-hint { color: var(--text-faint); font-size: 0.7rem; margin: 0; }

/* ── Modal ───────────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed; inset: 0; z-index: 50;
  background: var(--overlay); backdrop-filter: blur(5px);
  display: flex; align-items: center; justify-content: center; padding: 1rem;
}
.modal-enter-active { transition: all 0.2s ease; }
.modal-enter-from   { opacity: 0; transform: scale(0.95); }
.modal-leave-active { transition: all 0.15s ease; }
.modal-leave-to     { opacity: 0; transform: scale(0.95); }

.modal-box {
  background: var(--surface); border: 1px solid rgb(var(--ink) / 0.08);
  border-radius: 20px; padding: 1.75rem;
  width: 100%; max-width: 400px;
  display: flex; flex-direction: column; gap: 1.25rem;
  box-shadow: var(--shadow-lg);
}
.modal-header {
  display: flex; align-items: flex-start; justify-content: space-between;
}
.modal-eyebrow {
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.72rem;
  letter-spacing: 0.18em; text-transform: uppercase;
  color: var(--accent-text); margin: 0 0 0.2rem;
}
.modal-title {
  font-family: 'Manrope', system-ui, sans-serif; font-size: 1.1rem;
  font-weight: 500; text-transform: uppercase; letter-spacing: 0.06em; margin: 0 0 0.2rem;
}
.modal-phone { font-family: monospace; font-size: 0.78rem; color: var(--text-faint); margin: 0; }
.modal-close {
  width: 30px; height: 30px; border-radius: 8px;
  background: rgb(var(--ink) / 0.05); border: 1px solid rgb(var(--ink) / 0.08);
  color: var(--text-dim); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s; flex-shrink: 0;
}
.modal-close:hover { background: rgb(var(--ink) / 0.1); color: var(--text); }

/* Current discount display */
.current-discount {
  background: rgb(var(--ink) / 0.03); border: 1px solid rgb(var(--ink) / 0.06);
  border-radius: 12px; padding: 1rem 1.1rem;
}
.current-label {
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.72rem;
  letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--text-faint); margin: 0 0 0.4rem;
}
.current-val-wrap { display: flex; align-items: baseline; gap: 0.6rem; }
.current-pct {
  font-family: 'Manrope', system-ui, sans-serif; font-size: 1.6rem; font-weight: 600;
}
.current-red   { color: var(--red-soft); }
.current-green { color: var(--green-soft); }
.current-type  { font-size: 0.7rem; color: var(--text-faint); }

/* Modal field */
.modal-field { display: flex; flex-direction: column; gap: 0.4rem; }
.modal-field-label {
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.72rem;
  letter-spacing: 0.15em; text-transform: uppercase; color: var(--text-faint);
}
.modal-input {
  background: rgb(var(--ink) / 0.04); border: 1px solid rgb(var(--ink) / 0.08);
  border-radius: 10px; padding: 0.75rem 1rem;
  color: var(--text); font-family: monospace; font-size: 0.95rem;
  outline: none; transition: border-color 0.15s;
}
.modal-input::placeholder { color: var(--text-faint); }
.modal-input:focus { border-color: color-mix(in srgb, var(--accent) 45%, transparent); }
.modal-hint { font-size: 0.72rem; color: var(--text-faint); margin: 0; }

/* Modal actions */
.modal-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; }
.modal-save-btn {
  display: flex; align-items: center; justify-content: center; gap: 0.4rem;
  padding: 0.8rem; border-radius: 10px; border: none;
  background: #D71920; color: #fff;
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.72rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: background 0.15s;
}
.modal-save-btn:hover:not(:disabled) { background: #B5121B; }
.modal-save-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.modal-cancel-btn {
  padding: 0.8rem; border-radius: 10px;
  background: rgb(var(--ink) / 0.04); border: 1px solid rgb(var(--ink) / 0.08);
  color: var(--text-dim);
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.72rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: all 0.15s;
}
.modal-cancel-btn:hover { background: rgb(var(--ink) / 0.08); color: var(--text); }

.modal-reset-btn {
  display: flex; align-items: center; justify-content: center; gap: 0.35rem;
  width: 100%; background: none; border: none;
  color: var(--text-faint);
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.72rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: color 0.15s; padding: 0.25rem;
}
.modal-reset-btn:hover { color: var(--red-soft); }

/* Spinner */
.btn-spinner {
  width: 13px; height: 13px; border-radius: 50%;
  border: 2px solid rgb(var(--ink) / 0.3); border-top-color: #fff;
  animation: spin 0.75s linear infinite; flex-shrink: 0;
}

/* ── Responsive ─────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .lc-root { padding: 1.25rem 1rem; }
  .lc-header { flex-direction: column; align-items: flex-start; }
  .lc-title { font-size: 1.4rem; }
}

/* Hide number spinners */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
input[type="number"] { -moz-appearance: textfield; }

/* Tabel jadi kartu bertumpuk di HP (tanpa scroll horizontal) */
@media (max-width: 720px) {
  .lc-table { min-width: 0; }
  .lc-table--stack thead { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
  .lc-table--stack, .lc-table--stack tbody, .lc-table--stack tr, .lc-table--stack td { display: block; width: 100%; }
  .lc-table--stack tr.lc-row { padding: 0.6rem 0; border-bottom: 1px solid var(--border); }
  .lc-table--stack td { display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: 0.35rem 1.1rem; border: none !important; text-align: right !important; }
  .lc-table--stack td[data-label]::before { content: attr(data-label); flex-shrink: 0; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-faint); }
  .lc-table--stack td.td-first { flex-direction: column; align-items: flex-start; gap: 0.1rem; text-align: left !important; padding-top: 0.5rem; }
  .lc-table--stack td.td-action { padding-top: 0.6rem; }
  .lc-table--stack td.td-action .action-btn { width: 100%; min-height: 44px; }
  .lc-table--stack td[colspan] { display: block; text-align: center !important; }
}
@media (pointer: coarse) { .action-btn, .refresh-btn, .modal-save-btn, .modal-cancel-btn { min-height: 44px; } }
html[data-admin-theme] .lc-root :focus-visible { outline-offset: 2px; }

/* ── Hangus & PIN ─────────────────────────────────────────────────── */
.exp-rule { margin: 4px 20px 10px; font-size: 12px; line-height: 1.55; opacity: .75; }
.exp-date { display: block; font-size: 12.5px; }
.exp-days { display: block; margin-top: 2px; font-size: 11px; opacity: .65; }
.exp-days.is-soon { opacity: 1; font-weight: 600; color: #d97706; }
.exp-pill { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 11.5px; font-weight: 600; background: rgba(128,128,128,.16); }
.pin-state { font-size: 12px; }
.pin-state--none { opacity: .55; }
.pin-state--locked { color: #D71920; font-weight: 600; }
.pin-err { margin: 0 0 10px; font-size: 13px; color: #D71920; }
.pin-once-label { margin: 6px 0 0; font-size: 13px; opacity: .75; }
.pin-once { margin: 6px 0 4px; font-family: monospace; font-size: 40px; font-weight: 700; letter-spacing: .3em; text-align: center; }
.pin-once-warn { margin: 0 0 14px; font-size: 12.5px; text-align: center; color: #d97706; }

/* ── Segmentasi & hapus ───────────────────────────────────────────── */
.seg-chips { display: flex; flex-wrap: wrap; gap: 8px; padding: 0 20px 4px; }
.seg-chip {
  display: inline-flex; align-items: baseline; gap: 6px; padding: 6px 12px;
  border-radius: 999px; border: 1px solid rgba(128,128,128,.28); background: transparent;
  color: inherit; font: inherit; font-size: 12.5px; cursor: pointer;
}
.seg-chip.is-on { border-color: currentColor; background: rgba(128,128,128,.14); font-weight: 600; }
.seg-chip-n { font-weight: 700; font-variant-numeric: tabular-nums; }
.seg-hint { margin: 6px 20px 0; font-size: 12px; opacity: .7; }
.seg-pill {
  display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 11.5px; font-weight: 600;
  background: rgba(128,128,128,.16);
}
.seg-pill.seg-setia    { background: rgba(255,212,0,.2); }
.seg-pill.seg-aktif    { background: rgba(34,160,90,.18); }
.seg-pill.seg-baru     { background: rgba(60,130,220,.18); }
.seg-pill.seg-berisiko { background: rgba(230,140,30,.22); }
.seg-pill.seg-tidur    { background: rgba(128,128,128,.16); }
.seg-days { display: block; margin-top: 3px; font-size: 11px; opacity: .6; }
.th-check, .td-check { width: 36px; }
.del-bar { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px; padding: 12px 20px 4px; font-size: 12.5px; }
.del-all { display: inline-flex; align-items: center; gap: 8px; cursor: pointer; }
.del-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.del-btn { color: #D71920; border-color: rgba(215,25,32,.4); background: transparent; }
.del-btn:disabled { opacity: .4; cursor: not-allowed; }
.td-action .del-btn { margin-left: 6px; }
.del-list { margin: 4px 0 14px; padding-left: 18px; font-size: 13px; line-height: 1.55; }
.del-confirm-btn { background: #D71920; color: #fff; }
.del-confirm-btn:disabled { opacity: .45; cursor: not-allowed; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
</style>