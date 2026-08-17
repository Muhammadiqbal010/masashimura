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

    <!-- ── TABLE ──────────────────────────────────────────────────── -->
    <div v-else class="table-card">
      <div class="table-card-head">
        <p class="card-eyebrow">Daftar Pelanggan</p>
        <h3 class="card-title-sm">{{ loyalty.loyalCustomers.length }} customer terdaftar</h3>
      </div>

      <div class="table-scroll">
        <table class="lc-table">
          <thead>
            <tr>
              <th>Pelanggan</th>
              <th>Order Terakhir</th>
              <th class="th-center">Total Order</th>
              <th class="th-right">Total Belanja</th>
              <th class="th-center">Poin</th>
              <th class="th-center">Status</th>
              <th class="th-center">Aksi</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="customer in loyalty.loyalCustomers"
              :key="customer.phone"
              class="lc-row"
            >
              <!-- Phone -->
              <td class="td-phone">
                <span class="phone-val">{{ customer.phone }}</span>
                <span v-if="customer.name" class="phone-name">{{ customer.name }}</span>
              </td>

              <!-- Order terakhir -->
              <td class="td-period">{{ customer.last_order_at ? formatDate(customer.last_order_at) : '—' }}</td>

              <!-- Total order -->
              <td class="td-center">
                <span class="order-count">{{ customer.total_orders || 0 }}</span>
                <span class="order-unit">order</span>
              </td>

              <!-- Belanja -->
              <td class="td-right td-spend">{{ formatPrice(customer.total_spent) }}</td>

              <!-- Poin -->
              <td class="td-center">
                <div v-if="customer.points > 0" class="discount-badge badge-green">
                  <span class="discount-pct">{{ customer.points }}</span>
                  <span class="discount-lbl">Poin</span>
                </div>
                <span v-else class="no-discount">0</span>
              </td>

              <!-- Status -->
              <td class="td-center">
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

              <!-- Aksi -->
              <td class="td-center">
                <button @click="openAdjustModal(customer)" class="action-btn action-active">
                  Adjust Poin
                </button>
              </td>
            </tr>

            <tr v-if="loyalty.loyalCustomers.length === 0">
              <td colspan="7" class="empty-cell">
                <div class="empty-icon">👥</div>
                <p class="empty-text">Belum ada data pelanggan</p>
                <p class="empty-hint">Data muncul setelah ada transaksi pertama dari nomor HP customer</p>
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
            <label class="modal-field-label">Alasan <span style="color:#dc2626;">*</span></label>
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

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useLoyaltyStore } from "@/stores/loyalty";
import { toast } from "vue-sonner";
import apiClient from "@/api/client";

const auth    = useAuthStore();
const loyalty = useLoyaltyStore();
const router  = useRouter();

const showAdjustModal = ref(false);
const selectedCustomer  = ref(null);
const adjustAmount      = ref(null);
const adjustNote        = ref("");
const isSaving          = ref(false);
const expiryMonths      = ref(0);

const fetchAdminLoyalData = async () => {
  try {
    const res  = await apiClient.get("/orders/loyal-customers/");
    const data = res.data;
    if (data?.customers) {
      loyalty.loyalCustomers = data.customers;
      expiryMonths.value     = data.settings?.points_expiry_months ?? 0;
    } else if (Array.isArray(data)) {
      loyalty.loyalCustomers = data;
    }
  } catch {
    loyalty.fetchLoyalCustomers();
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
  min-height: 100vh;
  background: #080808;
  color: #fff;
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
  border-bottom: 1px solid rgba(255,255,255,0.06);
  flex-wrap: wrap;
}
.lc-eyebrow {
  font-family: 'Oswald', sans-serif;
  font-size: 0.6rem; letter-spacing: 0.2em;
  text-transform: uppercase; color: #dc2626;
  margin: 0 0 0.3rem;
}
.lc-title {
  font-family: 'Oswald', sans-serif;
  font-size: 1.75rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.04em; margin: 0 0 0.3rem;
}
.lc-subtitle { font-size: 0.7rem; color: rgba(255,255,255,0.28); margin: 0; }

.refresh-btn {
  display: flex; align-items: center; gap: 0.45rem;
  padding: 0.55rem 1rem;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px; color: rgba(255,255,255,0.45);
  font-family: 'Oswald', sans-serif; font-size: 0.68rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: all 0.15s;
}
.refresh-btn:hover { background: rgba(255,255,255,0.08); color: #fff; border-color: rgba(255,255,255,0.15); }

/* ── Stat grid ───────────────────────────────────────────────────── */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}
@media (max-width: 640px) { .stat-grid { grid-template-columns: 1fr; } }

.stat-card {
  background: #0f0f0f;
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 16px; padding: 1.3rem 1.5rem;
  position: relative; overflow: hidden;
}
.stat-card::before {
  content: ''; position: absolute;
  top: 0; left: 0; right: 0; height: 2px;
  background: rgba(255,255,255,0.06);
}
.stat-green::before { background: #22c55e; }
.stat-amber::before { background: #f59e0b; }

.stat-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.65rem; }
.stat-label {
  font-family: 'Oswald', sans-serif; font-size: 0.62rem;
  letter-spacing: 0.14em; text-transform: uppercase;
  color: rgba(255,255,255,0.3);
}
.stat-dot { width: 6px; height: 6px; border-radius: 50%; }
.dot-white { background: rgba(255,255,255,0.2); }
.dot-green { background: #22c55e; }
.dot-amber { background: #f59e0b; }

.stat-val {
  font-family: monospace; font-size: 1.8rem; font-weight: 700;
  color: #fff; letter-spacing: -0.02em; margin-bottom: 0.3rem;
}
.val-green { color: #4ade80; }
.val-amber { color: #fbbf24; }
.stat-note { font-size: 0.66rem; color: rgba(255,255,255,0.2); }

/* ── Loading ─────────────────────────────────────────────────────── */
.loading-state {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 1rem; padding: 5rem 2rem;
  background: #0f0f0f; border: 1px solid rgba(255,255,255,0.05);
  border-radius: 16px;
  color: rgba(255,255,255,0.25); font-family: 'Oswald', sans-serif;
  font-size: 0.7rem; letter-spacing: 0.15em; text-transform: uppercase;
}
.spinner {
  width: 28px; height: 28px;
  border: 2px solid rgba(255,255,255,0.07); border-top-color: #dc2626;
  border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Table card ──────────────────────────────────────────────────── */
.table-card {
  background: #0f0f0f;
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 16px; overflow: hidden;
}
.table-card-head {
  padding: 1.1rem 1.5rem;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.card-eyebrow {
  font-family: 'Oswald', sans-serif; font-size: 0.58rem;
  letter-spacing: 0.18em; text-transform: uppercase;
  color: #dc2626; margin: 0 0 0.15rem;
}
.card-title-sm {
  font-family: 'Oswald', sans-serif; font-size: 0.82rem;
  font-weight: 500; text-transform: uppercase;
  letter-spacing: 0.08em; color: rgba(255,255,255,0.5); margin: 0;
}

.table-scroll { overflow-x: auto; }
.lc-table { width: 100%; border-collapse: collapse; min-width: 700px; }

.lc-table th {
  padding: 0.65rem 1.25rem;
  font-family: 'Oswald', sans-serif; font-size: 0.58rem; font-weight: 400;
  letter-spacing: 0.14em; text-transform: uppercase;
  color: rgba(255,255,255,0.22); text-align: left;
  background: rgba(255,255,255,0.015);
  border-bottom: 1px solid rgba(255,255,255,0.04);
  white-space: nowrap;
}
.th-center { text-align: center; }
.th-right  { text-align: right; }

.lc-row {
  border-bottom: 1px solid rgba(255,255,255,0.04);
  transition: background 0.12s;
}
.lc-row:hover { background: rgba(255,255,255,0.02); }
.lc-row:last-child { border-bottom: none; }

.lc-table td { padding: 0.9rem 1.25rem; font-size: 0.83rem; vertical-align: middle; }

.td-phone .phone-val { font-family: monospace; font-weight: 700; color: #fff; letter-spacing: 0.04em; }
.td-phone { display: flex; flex-direction: column; gap: 0.15rem; }
.td-phone .phone-name { font-size: 0.68rem; color: rgba(255,255,255,0.4); }
.td-period { font-size: 0.75rem; color: rgba(255,255,255,0.35); font-family: monospace; }
.td-center { text-align: center; }
.td-right  { text-align: right; }
.td-spend  { font-family: monospace; font-weight: 700; color: #fbbf24; }

.order-count { font-family: monospace; font-size: 1.1rem; font-weight: 700; color: #fff; }
.order-unit  { font-size: 0.65rem; color: rgba(255,255,255,0.25); margin-left: 0.25rem; }

/* Discount badge */
.discount-badge {
  display: inline-flex; flex-direction: column; align-items: center; gap: 0.1rem;
  padding: 0.25rem 0.65rem; border-radius: 8px;
}
.badge-red  { background: rgba(220,38,38,0.08);  border: 1px solid rgba(220,38,38,0.18); }
.badge-green{ background: rgba(34,197,94,0.08);  border: 1px solid rgba(34,197,94,0.18); }
.discount-pct {
  font-family: 'Oswald', sans-serif; font-size: 1rem; font-weight: 600; line-height: 1;
}
.badge-red  .discount-pct { color: #f87171; }
.badge-green .discount-pct { color: #4ade80; }
.discount-lbl {
  font-size: 0.5rem; letter-spacing: 0.12em; text-transform: uppercase;
  color: rgba(255,255,255,0.25); font-family: 'Oswald', sans-serif;
}
.no-discount { color: rgba(255,255,255,0.15); font-size: 0.85rem; }

/* Status pill */
.status-pill {
  display: inline-block; padding: 0.22rem 0.7rem;
  border-radius: 100px; font-size: 0.6rem;
  font-family: 'Oswald', sans-serif; letter-spacing: 0.1em; text-transform: uppercase;
}
.pill-loyal   { background: rgba(34,197,94,0.1);  color: #4ade80; border: 1px solid rgba(34,197,94,0.2); }
.pill-regular { background: rgba(255,255,255,0.04); color: rgba(255,255,255,0.25); border: 1px solid rgba(255,255,255,0.08); }

/* Action button */
.action-btn {
  padding: 0.35rem 0.85rem; border-radius: 8px;
  font-family: 'Oswald', sans-serif; font-size: 0.62rem;
  letter-spacing: 0.08em; text-transform: uppercase; cursor: pointer;
  transition: all 0.15s; border: 1px solid;
}
.action-active {
  background: rgba(220,38,38,0.08); border-color: rgba(220,38,38,0.25); color: #f87171;
}
.action-active:hover { background: #dc2626; border-color: #dc2626; color: #fff; }
.action-disabled {
  background: transparent; border-color: rgba(255,255,255,0.05);
  color: rgba(255,255,255,0.12); cursor: not-allowed;
}

/* Empty state */
.empty-cell { padding: 4rem !important; text-align: center; }
.empty-icon { font-size: 2rem; margin-bottom: 0.75rem; }
.empty-text { color: rgba(255,255,255,0.28); font-size: 0.85rem; margin: 0 0 0.3rem; }
.empty-hint { color: rgba(255,255,255,0.15); font-size: 0.7rem; margin: 0; }

/* ── Modal ───────────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed; inset: 0; z-index: 50;
  background: rgba(0,0,0,0.8); backdrop-filter: blur(5px);
  display: flex; align-items: center; justify-content: center; padding: 1rem;
}
.modal-enter-active { transition: all 0.2s ease; }
.modal-enter-from   { opacity: 0; transform: scale(0.95); }
.modal-leave-active { transition: all 0.15s ease; }
.modal-leave-to     { opacity: 0; transform: scale(0.95); }

.modal-box {
  background: #0f0f0f; border: 1px solid rgba(255,255,255,0.08);
  border-radius: 20px; padding: 1.75rem;
  width: 100%; max-width: 400px;
  display: flex; flex-direction: column; gap: 1.25rem;
  box-shadow: 0 20px 60px rgba(0,0,0,0.6);
}
.modal-header {
  display: flex; align-items: flex-start; justify-content: space-between;
}
.modal-eyebrow {
  font-family: 'Oswald', sans-serif; font-size: 0.58rem;
  letter-spacing: 0.18em; text-transform: uppercase;
  color: #dc2626; margin: 0 0 0.2rem;
}
.modal-title {
  font-family: 'Oswald', sans-serif; font-size: 1.1rem;
  font-weight: 500; text-transform: uppercase; letter-spacing: 0.06em; margin: 0 0 0.2rem;
}
.modal-phone { font-family: monospace; font-size: 0.78rem; color: rgba(255,255,255,0.35); margin: 0; }
.modal-close {
  width: 30px; height: 30px; border-radius: 8px;
  background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.4); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s; flex-shrink: 0;
}
.modal-close:hover { background: rgba(255,255,255,0.1); color: #fff; }

/* Current discount display */
.current-discount {
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px; padding: 1rem 1.1rem;
}
.current-label {
  font-family: 'Oswald', sans-serif; font-size: 0.58rem;
  letter-spacing: 0.14em; text-transform: uppercase;
  color: rgba(255,255,255,0.28); margin: 0 0 0.4rem;
}
.current-val-wrap { display: flex; align-items: baseline; gap: 0.6rem; }
.current-pct {
  font-family: 'Oswald', sans-serif; font-size: 1.6rem; font-weight: 600;
}
.current-red   { color: #f87171; }
.current-green { color: #4ade80; }
.current-type  { font-size: 0.7rem; color: rgba(255,255,255,0.3); }

/* Modal field */
.modal-field { display: flex; flex-direction: column; gap: 0.4rem; }
.modal-field-label {
  font-family: 'Oswald', sans-serif; font-size: 0.58rem;
  letter-spacing: 0.15em; text-transform: uppercase; color: rgba(255,255,255,0.3);
}
.modal-input {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px; padding: 0.75rem 1rem;
  color: #fff; font-family: monospace; font-size: 0.95rem;
  outline: none; transition: border-color 0.15s;
}
.modal-input::placeholder { color: rgba(255,255,255,0.15); }
.modal-input:focus { border-color: rgba(220,38,38,0.45); }
.modal-hint { font-size: 0.65rem; color: rgba(255,255,255,0.2); margin: 0; }

/* Modal actions */
.modal-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; }
.modal-save-btn {
  display: flex; align-items: center; justify-content: center; gap: 0.4rem;
  padding: 0.8rem; border-radius: 10px; border: none;
  background: #dc2626; color: #fff;
  font-family: 'Oswald', sans-serif; font-size: 0.72rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: background 0.15s;
}
.modal-save-btn:hover:not(:disabled) { background: #b91c1c; }
.modal-save-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.modal-cancel-btn {
  padding: 0.8rem; border-radius: 10px;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.45);
  font-family: 'Oswald', sans-serif; font-size: 0.72rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: all 0.15s;
}
.modal-cancel-btn:hover { background: rgba(255,255,255,0.08); color: #fff; }

.modal-reset-btn {
  display: flex; align-items: center; justify-content: center; gap: 0.35rem;
  width: 100%; background: none; border: none;
  color: rgba(255,255,255,0.2);
  font-family: 'Oswald', sans-serif; font-size: 0.6rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: color 0.15s; padding: 0.25rem;
}
.modal-reset-btn:hover { color: #f87171; }

/* Spinner */
.btn-spinner {
  width: 13px; height: 13px; border-radius: 50%;
  border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff;
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
</style>