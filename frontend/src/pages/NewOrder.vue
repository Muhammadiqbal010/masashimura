<template>
  <div class="pos-root">

    <!-- ── KATALOG MENU ─────────────────────────────────────────────── -->
    <div class="catalog-panel">

      <!-- Catalog header -->
      <div class="catalog-header">
        <div>
          <p class="pos-eyebrow">Masashimura · Kasir</p>
          <h1 class="pos-title">New Order (POS)</h1>
          <p class="pos-date">{{ liveFormattedDate }}</p>
        </div>
        <button @click="showUnpaidDrawer = true" class="unpaid-trigger">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          <span class="unpaid-label">Tagihan</span>
          <span v-if="unpaidOrders.length" class="unpaid-badge">{{ unpaidOrders.length }}</span>
        </button>
      </div>

      <!-- Loading skeleton -->
      <div v-if="isLoadingMenus" class="menu-grid">
        <div v-for="n in 6" :key="n" class="menu-skeleton"></div>
      </div>

      <!-- Error state -->
      <div v-else-if="menuLoadError" class="menu-error">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <p>Gagal memuat katalog menu dari database</p>
        <button @click="fetchMenus" class="retry-btn">Coba Lagi</button>
      </div>

      <!-- Empty state -->
      <div v-else-if="filteredMenus.length === 0" class="menu-empty">
        <div class="empty-icon">🍱</div>
        <p class="empty-text">Menu tidak ditemukan</p>
        <p class="empty-hint">Coba kata kunci atau kategori lain</p>
      </div>

      <!-- Menu grid -->
      <div v-else class="menu-grid">
        <button
          v-for="menu in filteredMenus"
          :key="menu.id"
          class="menu-card"
          :class="!menu.is_available ? 'menu-card-unavail' : 'menu-card-avail'"
          @click="addToOrder(menu)"
          :disabled="!menu.is_available"
        >
          <div v-if="!menu.is_available" class="menu-habis-overlay">
            <span class="habis-badge">Habis</span>
          </div>
          <div class="menu-card-body">
            <h3 class="menu-name">{{ menu.name }}</h3>
            <p class="menu-price">{{ formatPrice(menu.price) }}</p>
          </div>
          <div class="menu-add-indicator">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          </div>
        </button>
      </div>
    </div>

    <!-- ── RINGKASAN PESANAN ───────────────────────────────────────── -->
    <div class="order-panel">
      <div class="order-panel-head">
        <p class="pos-eyebrow">Transaksi Aktif</p>
        <h2 class="order-panel-title">Ringkasan Pesanan</h2>
      </div>

      <!-- Customer info -->
      <div class="order-section">
        <div class="field">
          <label class="field-label">Nomor HP Pelanggan</label>
          <div class="phone-input-row">
            <div class="phone-avatar">{{ customerInitial }}</div>
            <input
              v-model="customerPhone"
              @input="debounceTrackLoyalty"
              placeholder="081234567xxx"
              class="pos-input flex-1"
            />
          </div>
        </div>

        <div class="field">
          <label class="field-label">Nama Pelanggan <span class="field-optional">(Opsional)</span></label>
          <input
            v-model="customerName"
            type="text"
            placeholder="Nama pembeli..."
            class="pos-input"
          />
        </div>

        <!-- Loyalty status -->
        <div v-if="customerPhone.length >= 9" class="loyalty-status" :class="isTrackingLoyalty ? 'ls-loading' : isMember ? 'ls-loyal' : 'ls-regular'">
          <template v-if="isTrackingLoyalty">
            <div class="ls-spinner"></div>
            <span>Memeriksa status member...</span>
          </template>
          <template v-else-if="isMember">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            <span>Member — <strong>{{ memberPoints }} poin</strong>{{ pointsExpiringNote ? ` · ${pointsExpiringNote}` : '' }}</span>
          </template>
          <template v-else>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <span>Belum pernah order — belum ada poin</span>
          </template>
        </div>
      </div>

      <!-- Cart -->
      <div class="order-section cart-section">
        <div v-if="orderItems.length === 0" class="cart-empty">
          <div class="cart-empty-icon">🛒</div>
          <p>Keranjang masih kosong</p>
          <p class="cart-empty-hint">Tap menu di kiri untuk menambah item</p>
        </div>

        <div v-else class="cart-list">
          <div
            v-for="(item, index) in orderItems"
            :key="index"
            class="cart-item"
          >
            <div class="cart-item-top">
              <div class="cart-item-info">
                <p class="cart-item-name">{{ item.name }}</p>
                <p class="cart-item-price">{{ formatPrice(item.price) }}</p>
              </div>
              <div class="qty-control">
                <button @click="updateQty(index, -1)" class="qty-btn">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="5" y1="12" x2="19" y2="12"/></svg>
                </button>
                <span class="qty-val">{{ item.quantity }}</span>
                <button @click="updateQty(index, 1)" class="qty-btn">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                </button>
              </div>
            </div>
            <input
              type="text"
              v-model="item.notes"
              @input="handleNotesChange(index)"
              placeholder="Catatan koki: Level 5, Tanpa Bawang..."
              class="cart-notes-input"
            />
          </div>
        </div>
      </div>

      <!-- Order type -->
      <div class="order-section">
        <label class="field-label">Alur Konsumsi</label>
        <div class="toggle-grid">
          <button
            @click="orderType = 'dine_in_now'"
            class="toggle-btn"
            :class="orderType === 'dine_in_now' ? 'toggle-active-red' : 'toggle-inactive'"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            Bayar Sekarang
          </button>
          <button
            @click="orderType = 'dine_in_later'"
            :disabled="paymentMethod === 'qris_manual'"
            class="toggle-btn"
            :class="orderType === 'dine_in_later'
              ? 'toggle-active-amber'
              : paymentMethod === 'qris_manual'
                ? 'toggle-disabled'
                : 'toggle-inactive'"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            Makan Dulu
          </button>
        </div>
      </div>

      <!-- Payment method -->
      <div class="order-section">
        <label class="field-label">Metode Pembayaran</label>
        <div class="toggle-grid">
          <button
            @click="selectPaymentMethod('cash')"
            class="toggle-btn"
            :class="paymentMethod === 'cash' ? 'toggle-active-white' : 'toggle-inactive'"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="6" width="20" height="12" rx="2"/><path d="M12 12h.01"/></svg>
            Tunai (Cash)
          </button>
          <button
            @click="selectPaymentMethod('qris_manual')"
            class="toggle-btn"
            :class="paymentMethod === 'qris_manual' ? 'toggle-active-white' : 'toggle-inactive'"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
            QRIS Manual
          </button>
        </div>
      </div>

      <!-- Cash input -->
      <div v-if="paymentMethod === 'cash' && orderType === 'dine_in_now'" class="order-section">
        <label class="field-label">Uang Diterima</label>
        <input
          v-model.number="amountPaid"
          type="number"
          placeholder="0"
          class="pos-input font-mono"
        />
        <div v-if="amountPaid > 0 && amountPaid >= totalPrice" class="change-box change-ok">
          <span>Kembalian</span>
          <span>{{ formatPrice(changeDue) }}</span>
        </div>
        <div v-else-if="amountPaid > 0 && amountPaid < totalPrice" class="change-box change-err">
          <span>Kurang</span>
          <span>{{ formatPrice(totalPrice - amountPaid) }}</span>
        </div>
      </div>

      <!-- Kasir info -->
      <div class="kasir-strip">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
        Kasir: <span class="kasir-name">{{ kasirName }}</span>
      </div>

      <!-- Price summary -->
      <div class="price-summary">
        <div class="price-row">
          <span>Subtotal</span>
          <span>{{ formatPrice(subtotal) }}</span>
        </div>

        <PromoCodeBox
          ref="promoBoxRef"
          :subtotal="subtotal"
          @applied="onPromoApplied"
          @removed="onPromoRemoved"
        />

        <div v-if="appliedPromo" class="price-row price-discount">
          <span>Diskon Promo ({{ appliedPromo.code }})</span>
          <span>−{{ formatPrice(appliedPromo.discount_amount) }}</span>
        </div>

        <!-- 🎁 Tukar poin -->
        <PointRedeemBox
          v-if="isMember"
          :points="memberPoints"
          :affordable="affordableRewards"
          :locked="lockedRewards"
          v-model:selected-ids="selectedRewardIds"
        />

        <div
          v-for="reward in selectedRewards"
          :key="`reward-${reward.id}`"
          class="price-row price-discount"
        >
          <span>🎁 {{ reward.menu_name }} (gratis)</span>
          <span>−{{ reward.point_cost }} poin</span>
        </div>

        <div class="price-total">
          <span>Total Akhir</span>
          <span class="total-val">{{ formatPrice(totalPrice) }}</span>
        </div>
      </div>

      <!-- Submit -->
      <button
        @click="submitOrder"
        :disabled="isSubmitting || orderItems.length === 0"
        class="submit-btn"
      >
        <span v-if="isSubmitting" class="btn-spinner"></span>
        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
        {{ isSubmitting ? 'Memproses...' : 'Eksekusi Pesanan' }}
      </button>
    </div>
  </div>

  <!-- ── DRAWER TAGIHAN BELUM LUNAS ──────────────────────────────── -->
  <transition
    enter-active-class="drawer-enter-active" enter-from-class="drawer-enter-from"
    leave-active-class="drawer-leave-active" leave-to-class="drawer-leave-to"
  >
    <div v-if="showUnpaidDrawer" class="drawer-overlay" @click.self="showUnpaidDrawer = false">
      <div class="drawer-box">

        <div class="drawer-head">
          <div>
            <p class="pos-eyebrow">Antrian Kasir</p>
            <h2 class="drawer-title">Tagihan Belum Lunas</h2>
          </div>
          <button class="drawer-close" @click="showUnpaidDrawer = false">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>

        <div class="drawer-search-wrap">
          <svg class="drawer-search-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
          <input
            v-model="unpaidSearch"
            placeholder="Cari order, nama, no HP..."
            class="drawer-search"
          />
        </div>

        <div v-if="!filteredUnpaidOrders.length" class="drawer-empty">
          <div class="empty-icon">✓</div>
          <p>Tidak ada tagihan tertunda</p>
        </div>

        <div class="drawer-list">
          <div
            v-for="order in filteredUnpaidOrders"
            :key="order.id"
            class="drawer-order-card"
          >
            <div class="drawer-order-top">
              <div>
                <p class="drawer-order-num">{{ order.order_number }}</p>
                <p class="drawer-order-name">{{ order.customer_name || 'Walk In' }}</p>
                <p class="drawer-order-phone">{{ order.customer_phone || '—' }}</p>
              </div>
              <div class="drawer-order-right">
                <p class="drawer-order-total">{{ formatPrice(order.total_price) }}</p>
                <p class="drawer-order-items">{{ order.items.length }} item</p>
              </div>
            </div>
            <button class="drawer-pay-btn" @click="openPaymentModal(order)">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="2" y="6" width="20" height="12" rx="2"/><path d="M12 12h.01"/></svg>
              Bayar Sekarang
            </button>
          </div>
        </div>

      </div>
    </div>
  </transition>

  <!-- ── MODAL KONFIRMASI PEMBAYARAN ─────────────────────────────── -->
  <transition
    enter-active-class="modal-enter-active" enter-from-class="modal-enter-from"
    leave-active-class="modal-leave-active" leave-to-class="modal-leave-to"
  >
    <div
      v-if="showPaymentModal && selectedUnpaidOrder"
      class="modal-overlay"
      @click.self="showPaymentModal = false"
    >
      <div class="modal-box">

        <div class="modal-head">
          <div>
            <p class="pos-eyebrow">Konfirmasi Transaksi</p>
            <h2 class="modal-title">Pembayaran Order</h2>
            <p class="modal-ordnum">{{ selectedUnpaidOrder.order_number }}</p>
          </div>
          <button class="modal-close-btn" @click="showPaymentModal = false">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>

        <!-- Customer -->
        <div class="modal-customer">
          <p class="modal-cust-name">{{ selectedUnpaidOrder.customer_name || 'Walk In' }}</p>
          <p class="modal-cust-phone">{{ selectedUnpaidOrder.customer_phone || '—' }}</p>
        </div>

        <!-- Items -->
        <div class="modal-items">
          <div
            v-for="item in selectedUnpaidOrder.items"
            :key="item.id"
            class="modal-item"
          >
            <div class="modal-item-left">
              <p class="modal-item-name">{{ item.menu_name }} <span class="modal-item-qty">×{{ item.quantity }}</span></p>
              <p v-if="item.notes" class="modal-item-note">{{ item.notes }}</p>
            </div>
            <span class="modal-item-price">{{ formatPrice(item.price * item.quantity) }}</span>
          </div>
        </div>

        <!-- Totals -->
        <div class="modal-totals">
          <div class="modal-total-row">
            <span>Subtotal</span>
            <span>{{ formatPrice(selectedUnpaidOrder.subtotal) }}</span>
          </div>
          <div class="modal-total-final">
            <span>Total</span>
            <span>{{ formatPrice(selectedUnpaidOrder.total_price) }}</span>
          </div>
        </div>

        <!-- Payment method -->
        <div class="modal-section">
          <label class="field-label">Metode Pembayaran</label>
          <div class="toggle-grid">
            <button @click="selectedPaymentMethod = 'cash'" class="toggle-btn" :class="selectedPaymentMethod === 'cash' ? 'toggle-active-white' : 'toggle-inactive'">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="6" width="20" height="12" rx="2"/></svg>
              Cash
            </button>
            <button @click="selectedPaymentMethod = 'qris_manual'" class="toggle-btn" :class="selectedPaymentMethod === 'qris_manual' ? 'toggle-active-white' : 'toggle-inactive'">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
              QRIS
            </button>
          </div>
        </div>

        <!-- Cash input modal -->
        <div v-if="selectedPaymentMethod === 'cash'" class="modal-section">
          <label class="field-label">Uang Diterima</label>
          <input
            v-model.number="amountPaidModal"
            type="number"
            placeholder="0"
            class="pos-input font-mono"
          />
          <div v-if="amountPaidModal > 0 && amountPaidModal >= parseFloat(selectedUnpaidOrder.total_price)" class="change-box change-ok">
            <span>Kembalian</span>
            <span>{{ formatPrice(amountPaidModal - parseFloat(selectedUnpaidOrder.total_price)) }}</span>
          </div>
          <div v-else-if="amountPaidModal > 0 && amountPaidModal < parseFloat(selectedUnpaidOrder.total_price)" class="change-box change-err">
            <span>Kurang</span>
            <span>{{ formatPrice(parseFloat(selectedUnpaidOrder.total_price) - amountPaidModal) }}</span>
          </div>
        </div>

        <button
          @click="confirmPayment"
          :disabled="isPaying || (selectedPaymentMethod === 'cash' && amountPaidModal > 0 && amountPaidModal < parseFloat(selectedUnpaidOrder.total_price))"
          class="submit-btn"
        >
          <span v-if="isPaying" class="btn-spinner"></span>
          {{ isPaying ? 'Memproses...' : 'Konfirmasi Pembayaran' }}
        </button>

      </div>
    </div>
  </transition>

  <!-- ── STRUK TERSEMBUNYI ───────────────────────────────────────── -->
  <div
    ref="receiptRef"
    style="position:fixed;left:-9999px;top:0;width:380px;background:#fff;color:#000;padding:24px;font-family:'Courier New',monospace;font-size:12px;line-height:1.6;"
  >
    <div style="text-align:center;margin-bottom:12px;">
      <p style="font-size:15px;font-weight:900;text-transform:uppercase;letter-spacing:0.1em;">MASASHIMURA</p>
      <p style="font-size:10px;color:#666;">Jl. Pintu air no 48 Depan Pengadilan Bekasi</p>
      <p style="font-size:10px;color:#999;">{{ new Date().toLocaleString('id-ID') }}</p>
      <p style="color:#ccc;">========================================</p>
    </div>
    <div v-if="lastOrder" style="font-size:11px;margin-bottom:10px;">
      <div style="display:flex;justify-content:space-between;"><span>No. Nota</span><span style="font-weight:700;">{{ lastOrder.order_number }}</span></div>
      <div style="display:flex;justify-content:space-between;"><span>Kasir</span><span>{{ kasirName }}</span></div>
      <div style="display:flex;justify-content:space-between;"><span>Pelanggan</span><span>{{ lastOrder.customer_name || lastOrder.customer_phone || 'Walk In' }}</span></div>
    </div>
    <p style="color:#ccc;margin-bottom:10px;">----------------------------------------</p>
    <div v-if="lastOrder" style="margin-bottom:10px;">
      <div v-for="(item, idx) in lastOrderItems" :key="idx" style="margin-bottom:6px;">
        <div style="display:flex;justify-content:space-between;font-weight:600;"><span>{{ item.quantity }}x {{ item.name }}</span><span>{{ formatPrice(item.price * item.quantity) }}</span></div>
        <div v-if="item.notes" style="color:#b45309;font-size:10px;padding-left:10px;font-style:italic;">📋 {{ item.notes }}</div>
      </div>
    </div>
    <p style="color:#ccc;margin-bottom:10px;">----------------------------------------</p>
    <div v-if="lastOrder" style="font-size:11px;margin-bottom:10px;">
      <div style="display:flex;justify-content:space-between;margin-bottom:3px;"><span>Subtotal</span><span>{{ formatPrice(lastOrder.subtotal || lastOrder.total_price) }}</span></div>
      <div v-if="parseFloat(lastOrder.promo_discount_amount) > 0" style="display:flex;justify-content:space-between;color:#16a34a;margin-bottom:3px;"><span>Diskon Promo</span><span>-{{ formatPrice(lastOrder.promo_discount_amount) }}</span></div>
      <div style="display:flex;justify-content:space-between;font-size:14px;font-weight:900;border-top:1px solid #eee;padding-top:4px;margin-bottom:4px;"><span>TOTAL</span><span>{{ formatPrice(lastOrder.total_price) }}</span></div>
      <div v-if="lastOrder.amount_paid > 0" style="display:flex;justify-content:space-between;"><span>Bayar</span><span>{{ formatPrice(lastOrder.amount_paid) }}</span></div>
      <div v-if="lastOrder.change_amount > 0" style="display:flex;justify-content:space-between;color:#16a34a;font-weight:700;"><span>Kembalian</span><span>{{ formatPrice(lastOrder.change_amount) }}</span></div>
    </div>
    <p style="color:#ccc;margin-bottom:10px;">========================================</p>
    <div style="text-align:center;font-size:10px;color:#888;">
      <p>Metode: {{ lastOrder?.payment_method?.toUpperCase() || 'CASH' }}</p>
      <p style="font-weight:700;margin-top:4px;">Terima kasih sudah makan di Masashimura! 🙏</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { menuAPI, orderAPI, apiClient } from "@/api";
import { toast } from "vue-sonner";
import { useAuthStore } from '@/stores/auth';
import html2canvas from 'html2canvas';
import PromoCodeBox from "@/components/ui/PromoCodeBox.vue";
import PointRedeemBox from "@/components/ui/PointRedeemBox.vue";

const authStore  = useAuthStore();
const kasirName  = computed(() => authStore.user?.name || authStore.user?.username || 'Staff');

const menus             = ref([]);
const isLoadingMenus    = ref(false);
const menuLoadError     = ref(false);
const searchQuery       = ref("");
const unpaidSearch      = ref("");
const selectedCategory  = ref("Semua");
const orderItems        = ref([]);
const customerPhone     = ref("");
const customerName      = ref("");
const isMember          = ref(false);
const memberPoints      = ref(0);
const pointsExpiringNote = ref(null);
const paymentMethod     = ref("cash");
const orderType         = ref("dine_in_now");
const isSubmitting      = ref(false);
const isTrackingLoyalty = ref(false);
let debounceTimeout     = null;

// ── Promo code ──────────────────────────────────────────────────────
const promoBoxRef  = ref(null);
const appliedPromo = ref(null); // { promo_id, code, discount_amount }
const onPromoApplied = (promo) => { appliedPromo.value = promo; };
const onPromoRemoved = () => { appliedPromo.value = null; };

const unpaidOrders          = ref([]);
const showUnpaidDrawer      = ref(false);
const isLoadingUnpaid       = ref(false);
const selectedUnpaidOrder   = ref(null);
const showPaymentModal      = ref(false);
const selectedPaymentMethod = ref("cash");
const isPaying              = ref(false);
const amountPaidModal       = ref(0);
const amountPaid            = ref(0);
const receiptRef            = ref(null);
const lastOrder              = ref(null);
const lastOrderItems        = ref([]);
const affordableRewards = ref([]);
const lockedRewards     = ref([]);
const selectedRewardIds = ref([]);

const changeDue = computed(() => {
  if (paymentMethod.value !== 'cash' || orderType.value !== 'dine_in_now') return 0;
  return amountPaid.value >= totalPrice.value ? amountPaid.value - totalPrice.value : 0;
});

const liveFormattedDate = computed(() =>
  new Date().toLocaleDateString('id-ID', { weekday:'long', year:'numeric', month:'long', day:'numeric' })
);
const customerInitial = computed(() =>
  customerPhone.value ? customerPhone.value.trim().charAt(0).toUpperCase() : "?"
);
const filteredMenus = computed(() => {
  const query = searchQuery.value.trim().toLowerCase();
  return menus.value
    .filter(menu => {
      const matchCat = selectedCategory.value === "Semua" || (menu.category || "Makanan") === selectedCategory.value;
      const matchQ   = !query || menu.name?.toLowerCase().includes(query);
      return matchCat && matchQ;
    })
    .sort((a, b) => b.is_available - a.is_available);
});

// ── Kalkulasi harga: subtotal → diskon promo → total (diskon member % udah dihapus) ──
const subtotal       = computed(() => orderItems.value.reduce((acc, item) => acc + item.price * item.quantity, 0));
const totalPrice     = computed(() => {
  const promoDiscount = appliedPromo.value?.discount_amount || 0;
  return Math.max(subtotal.value - promoDiscount, 0);
});

const filteredUnpaidOrders = computed(() => {
  const q = unpaidSearch.value.toLowerCase().trim();
  if (!q) return unpaidOrders.value;
  return unpaidOrders.value.filter(o =>
    o.order_number?.toLowerCase().includes(q) ||
    o.customer_name?.toLowerCase().includes(q) ||
    o.customer_phone?.includes(q)
  );
});

const fetchMenus = async () => {
  isLoadingMenus.value = true; menuLoadError.value = false;
  try { const res = await menuAPI.getAll(); menus.value = res.data; }
  catch { menuLoadError.value = true; }
  finally { isLoadingMenus.value = false; }
};

const fetchUnpaidOrders = async () => {
  isLoadingUnpaid.value = true;
  try { const { data } = await apiClient.get("/orders/unpaid/"); unpaidOrders.value = data; }
  catch (err) { console.error(err); }
  finally { isLoadingUnpaid.value = false; }
};

const debounceTrackLoyalty = () => {
  clearTimeout(debounceTimeout);
  if (customerPhone.value.length < 9) {
    isMember.value = false; memberPoints.value = 0; pointsExpiringNote.value = null;
    resetPointRewards();
    return;
  }
  isTrackingLoyalty.value = true;
  debounceTimeout = setTimeout(checkLoyalty, 800);
};

const checkLoyalty = async () => {
  try {
    const { data } = await apiClient.get("/orders/check_loyalty_status/", { params: { phone: customerPhone.value } });
    isMember.value = data.is_member ?? false;
    memberPoints.value = data.points ?? 0;
    pointsExpiringNote.value = data.points_expiring_note ?? null;
  } catch {
    isMember.value = false; memberPoints.value = 0; pointsExpiringNote.value = null;
  } finally {
    isTrackingLoyalty.value = false;
  }
  // narik reward yang bisa ditukar, terpisah biar loyalty status gak nge-block kalo ini gagal
  fetchPointRewards(customerPhone.value);
};

const selectedRewards = computed(() =>
  affordableRewards.value.filter(r => selectedRewardIds.value.includes(r.id))
);

const resetPointRewards = () => {
  affordableRewards.value = [];
  lockedRewards.value = [];
  selectedRewardIds.value = [];
};

const fetchPointRewards = async (phoneNumber) => {
  try {
    const { data } = await orderAPI.getAvailablePointRewards(phoneNumber);
    affordableRewards.value = data.affordable ?? [];
    lockedRewards.value     = data.locked ?? [];
  } catch {
    resetPointRewards();
  }
};

const addToOrder = (menu) => {
  if (!menu.is_available) { toast.error("Menu ini sedang habis!"); return; }
  const existing = orderItems.value.find(i => i.id === menu.id && i.notes === "");
  if (existing) existing.quantity++;
  else orderItems.value.push({ ...menu, quantity: 1, notes: "" });
};

const handleNotesChange = (index) => {
  const cur = orderItems.value[index];
  const dup = orderItems.value.findIndex((item, idx) =>
    idx !== index && item.id === cur.id && item.notes.trim().toLowerCase() === cur.notes.trim().toLowerCase()
  );
  if (dup > -1) { orderItems.value[dup].quantity += cur.quantity; orderItems.value.splice(index, 1); toast.info("Item dengan catatan sama digabungkan!"); }
};

const updateQty = (index, delta) => {
  orderItems.value[index].quantity += delta;
  if (orderItems.value[index].quantity <= 0) orderItems.value.splice(index, 1);
};

const selectPaymentMethod = (method) => {
  paymentMethod.value = method;
  if (method === 'qris_manual') orderType.value = 'dine_in_now';
};

const openPaymentModal = (order) => {
  selectedUnpaidOrder.value = order; selectedPaymentMethod.value = "cash";
  amountPaidModal.value = 0; showPaymentModal.value = true;
};

const confirmPayment = async () => {
  if (!selectedUnpaidOrder.value) return;
  isPaying.value = true;
  try {
    await apiClient.patch(`/orders/${selectedUnpaidOrder.value.id}/pay/`, {
      payment_method: selectedPaymentMethod.value,
      amount_paid: selectedPaymentMethod.value === 'cash' ? amountPaidModal.value : 0,
      kasir_name: kasirName.value,
    });
    toast.success("Pembayaran berhasil");
    showPaymentModal.value = false; selectedUnpaidOrder.value = null; amountPaidModal.value = 0;
    fetchUnpaidOrders();
  } catch { toast.error("Pembayaran gagal"); }
  finally { isPaying.value = false; }
};

const shareReceiptAsImage = async (orderData) => {
  await new Promise(r => setTimeout(r, 300));
  try {
    const canvas = await html2canvas(receiptRef.value, { backgroundColor: '#ffffff', scale: 2, useCORS: true });
    canvas.toBlob(async (blob) => {
      if (!blob) { toast.error("Gagal membuat gambar struk"); return; }
      if (navigator.share && navigator.canShare?.({ files: [new File([blob], 'struk.png', { type: 'image/png' })] })) {
        const file = new File([blob], `struk-${orderData.order_number}.png`, { type: 'image/png' });
        await navigator.share({ files: [file], text: 'Bukti Pembelian di Masashimura 🙏' });
      } else {
        const url = URL.createObjectURL(blob); const a = document.createElement('a');
        a.href = url; a.download = `struk-${orderData.order_number}.png`; a.click(); URL.revokeObjectURL(url);
        const caption = encodeURIComponent('Bukti Pembelian di Masashimura 🙏');
        const phone = (customerPhone.value || '').startsWith('0') ? '62' + customerPhone.value.slice(1) : customerPhone.value;
        setTimeout(() => window.open(phone ? `https://wa.me/${phone}?text=${caption}` : `https://wa.me/?text=${caption}`, '_blank'), 500);
        toast.info("Gambar diunduh. Lampirkan ke WhatsApp secara manual.");
      }
    }, 'image/png');
  } catch (err) { console.error(err); toast.error("Gagal membuat screenshot struk"); }
};

const submitOrder = async () => {
  if (orderItems.value.length === 0) return toast.error("Keranjang kosong!");
  isSubmitting.value = true;
  const payload = {
  source: 'pos',
  customer: customerPhone.value ? { phone: customerPhone.value, name: customerName.value || "Member Baru" } : null,
  payment_method: paymentMethod.value,
  payment_status: orderType.value === 'dine_in_later' ? 'pending' : 'paid',
  status: 'pending',
  amount_paid: paymentMethod.value === 'cash' ? amountPaid.value : 0,
  kasir_name: kasirName.value,
  promo_id: appliedPromo.value?.promo_id || null,
  promo_discount_amount: appliedPromo.value?.discount_amount || 0,
  redeem_reward_ids: selectedRewardIds.value,
  items: orderItems.value.map(item => ({ menu_id: item.id, quantity: item.quantity, price: item.price, notes: item.notes })),
};
  try {
    const res = await apiClient.post("/orders/", payload);
    lastOrder.value = res.data; lastOrderItems.value = [...orderItems.value];
    toast.success("Pesanan berhasil masuk ke sistem!");
    orderItems.value = []; customerPhone.value = ""; customerName.value = "";
    isMember.value = false; memberPoints.value = 0; pointsExpiringNote.value = null;
    paymentMethod.value = "cash"; orderType.value = "dine_in_now"; amountPaid.value = 0;
    promoBoxRef.value?.removePromo();
    resetPointRewards();
    fetchUnpaidOrders();
    await shareReceiptAsImage(res.data);
  } catch (e) { console.error(e); toast.error("Gagal menyimpan transaksi ke server."); }
  finally { isSubmitting.value = false; }
};

const formatPrice = (p) =>
  new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", minimumFractionDigits: 0 }).format(p || 0);

onMounted(() => { fetchMenus(); fetchUnpaidOrders(); });
</script>

<style scoped>
/* ── Root layout ─────────────────────────────────────────────────── */
.pos-root {
  display: flex;
  gap: 1.25rem;
  min-height: 100vh;
  background: #080808;
  color: #fff;
  font-family: 'Inter', sans-serif;
  padding: 1.5rem;
  align-items: flex-start;
}
@media (max-width: 1024px) { .pos-root { flex-direction: column; padding: 1rem; } }

/* ── Shared tokens ───────────────────────────────────────────────── */
.pos-eyebrow {
  font-family: 'Oswald', sans-serif; font-size: 0.58rem;
  letter-spacing: 0.2em; text-transform: uppercase; color: #dc2626;
  margin: 0 0 0.2rem;
}

/* ── Catalog panel ───────────────────────────────────────────────── */
.catalog-panel {
  flex: 1; min-width: 0;
  display: flex; flex-direction: column; gap: 1.25rem;
}

.catalog-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 1rem; flex-wrap: wrap;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.pos-title {
  font-family: 'Oswald', sans-serif; font-size: 1.6rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.04em; margin: 0 0 0.2rem;
}
.pos-date { font-size: 0.68rem; color: rgba(255,255,255,0.28); margin: 0; }

.unpaid-trigger {
  display: flex; align-items: center; gap: 0.45rem;
  padding: 0.55rem 1rem;
  background: #0f0f0f; border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px; color: rgba(255,255,255,0.5);
  font-family: 'Oswald', sans-serif; font-size: 0.68rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: all 0.15s; position: relative;
  white-space: nowrap;
}
.unpaid-trigger:hover { border-color: rgba(255,255,255,0.18); color: #fff; }
.unpaid-label { }
.unpaid-badge {
  display: inline-flex; align-items: center; justify-content: center;
  width: 18px; height: 18px; border-radius: 50%;
  background: #dc2626; color: #fff; font-size: 0.6rem; font-weight: 700;
}

/* ── Menu grid ───────────────────────────────────────────────────── */
.menu-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.75rem;
}
@media (max-width: 640px) { .menu-grid { grid-template-columns: repeat(2, 1fr); } }

.menu-skeleton {
  background: #0f0f0f; border: 1px solid rgba(255,255,255,0.04);
  border-radius: 12px; min-height: 110px;
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.5; } }

.menu-error, .menu-empty {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 0.6rem; padding: 3rem 2rem;
  background: #0f0f0f; border: 1px solid rgba(255,255,255,0.05);
  border-radius: 14px; text-align: center;
  color: rgba(255,255,255,0.3); font-size: 0.8rem;
}
.empty-icon { font-size: 1.75rem; margin-bottom: 0.25rem; }
.empty-text { color: rgba(255,255,255,0.3); margin: 0; font-size: 0.85rem; }
.empty-hint { color: rgba(255,255,255,0.15); margin: 0; font-size: 0.7rem; }
.retry-btn {
  padding: 0.5rem 1.25rem; border-radius: 8px;
  background: #dc2626; border: none; color: #fff;
  font-family: 'Oswald', sans-serif; font-size: 0.68rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: background 0.15s;
}
.retry-btn:hover { background: #b91c1c; }

.menu-card {
  position: relative; background: #0f0f0f;
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 12px; padding: 1rem;
  display: flex; flex-direction: column; justify-content: space-between;
  min-height: 110px; cursor: pointer; text-align: left;
  transition: border-color 0.15s, background 0.15s;
  overflow: hidden;
}
.menu-card-avail:hover { border-color: rgba(220,38,38,0.5); background: rgba(220,38,38,0.04); }
.menu-card-avail:hover .menu-add-indicator { opacity: 1; }
.menu-card-unavail { opacity: 0.45; cursor: not-allowed; filter: grayscale(0.7); }

.menu-habis-overlay {
  position: absolute; inset: 0; z-index: 10;
  background: rgba(0,0,0,0.65); border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
}
.habis-badge {
  font-family: 'Oswald', sans-serif; font-size: 0.62rem; font-weight: 600;
  letter-spacing: 0.15em; text-transform: uppercase;
  color: #f87171; border: 1px solid rgba(239,68,68,0.4);
  padding: 0.2rem 0.65rem; border-radius: 100px;
}
.menu-card-body { flex: 1; }
.menu-name { font-weight: 600; font-size: 0.82rem; color: rgba(255,255,255,0.85); margin: 0 0 0.35rem; line-height: 1.3; }
.menu-price { font-family: monospace; font-size: 0.78rem; font-weight: 700; color: #dc2626; margin: 0; }
.menu-add-indicator {
  display: flex; align-items: center; justify-content: center;
  width: 22px; height: 22px; border-radius: 6px;
  background: rgba(220,38,38,0.1); border: 1px solid rgba(220,38,38,0.2);
  color: #f87171; margin-top: 0.5rem; align-self: flex-end;
  opacity: 0; transition: opacity 0.15s;
}

/* ── Order panel ─────────────────────────────────────────────────── */
.order-panel {
  width: 360px; flex-shrink: 0;
  background: #0f0f0f; border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px; overflow: hidden;
  position: sticky; top: 1.5rem;
  display: flex; flex-direction: column;
  max-height: calc(100vh - 3rem); overflow-y: auto;
}
@media (max-width: 1024px) { .order-panel { width: 100%; position: static; max-height: none; } }

.order-panel-head {
  padding: 1.25rem 1.4rem 1rem;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.order-panel-title {
  font-family: 'Oswald', sans-serif; font-size: 1rem; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.08em; margin: 0;
}

.order-section {
  padding: 1rem 1.4rem;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  display: flex; flex-direction: column; gap: 0.6rem;
}

/* Fields */
.field { display: flex; flex-direction: column; gap: 0.35rem; }
.field-label {
  font-family: 'Oswald', sans-serif; font-size: 0.56rem;
  letter-spacing: 0.15em; text-transform: uppercase; color: rgba(255,255,255,0.28);
}
.field-optional { font-size: 0.5rem; color: rgba(255,255,255,0.18); }

.phone-input-row { display: flex; align-items: center; gap: 0.6rem; }
.phone-avatar {
  width: 34px; height: 34px; border-radius: 50%; flex-shrink: 0;
  background: rgba(220,38,38,0.1); border: 1px solid rgba(220,38,38,0.2);
  display: flex; align-items: center; justify-content: center;
  font-family: monospace; font-size: 0.75rem; font-weight: 700; color: #dc2626;
}

.pos-input {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px; padding: 0.65rem 0.85rem;
  color: #fff; font-size: 0.82rem; font-family: 'Inter', sans-serif;
  outline: none; transition: border-color 0.15s; width: 100%;
}
.pos-input::placeholder { color: rgba(255,255,255,0.18); }
.pos-input:focus { border-color: rgba(220,38,38,0.45); }

/* Loyalty status */
.loyalty-status {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.6rem 0.85rem; border-radius: 10px; border: 1px solid;
  font-size: 0.72rem; line-height: 1.4;
}
.ls-loading { background: rgba(255,255,255,0.02); border-color: rgba(255,255,255,0.06); color: rgba(255,255,255,0.4); }
.ls-loyal   { background: rgba(34,197,94,0.07);  border-color: rgba(34,197,94,0.18); color: #4ade80; }
.ls-regular { background: rgba(255,255,255,0.02); border-color: rgba(255,255,255,0.06); color: rgba(255,255,255,0.35); }
.ls-spinner {
  width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0;
  border: 2px solid rgba(255,255,255,0.2); border-top-color: rgba(255,255,255,0.6);
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Cart */
.cart-section { }
.cart-empty {
  padding: 2rem 0; text-align: center;
  color: rgba(255,255,255,0.2); font-size: 0.78rem;
  display: flex; flex-direction: column; align-items: center; gap: 0.3rem;
}
.cart-empty-icon { font-size: 1.75rem; margin-bottom: 0.25rem; }
.cart-empty-hint { font-size: 0.65rem; color: rgba(255,255,255,0.12); }

.cart-list { display: flex; flex-direction: column; gap: 0.6rem; max-height: 300px; overflow-y: auto; padding-right: 2px; }
.cart-list::-webkit-scrollbar { width: 3px; }
.cart-list::-webkit-scrollbar-track { background: transparent; }
.cart-list::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }

.cart-item {
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px; padding: 0.75rem; display: flex; flex-direction: column; gap: 0.5rem;
}
.cart-item-top { display: flex; align-items: flex-start; gap: 0.5rem; }
.cart-item-info { flex: 1; min-width: 0; }
.cart-item-name { font-size: 0.8rem; font-weight: 600; color: rgba(255,255,255,0.85); margin: 0 0 0.15rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cart-item-price { font-family: monospace; font-size: 0.7rem; color: rgba(255,255,255,0.35); margin: 0; }

.qty-control {
  display: flex; align-items: center; gap: 0.4rem;
  background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px; padding: 3px; flex-shrink: 0;
}
.qty-btn {
  width: 22px; height: 22px; border-radius: 5px; border: none;
  background: transparent; color: rgba(255,255,255,0.5);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all 0.12s;
}
.qty-btn:hover { background: rgba(255,255,255,0.1); color: #fff; }
.qty-val { font-family: monospace; font-size: 0.78rem; font-weight: 700; min-width: 18px; text-align: center; }

.cart-notes-input {
  background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.05);
  border-radius: 7px; padding: 0.45rem 0.65rem;
  font-size: 0.68rem; color: #fbbf24; font-family: 'Inter', sans-serif;
  outline: none; transition: border-color 0.15s; width: 100%;
}
.cart-notes-input::placeholder { color: rgba(255,255,255,0.18); font-style: italic; }
.cart-notes-input:focus { border-color: rgba(251,191,36,0.3); }

/* Toggle buttons */
.toggle-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
.toggle-btn {
  display: flex; align-items: center; justify-content: center; gap: 0.35rem;
  padding: 0.6rem; border-radius: 9px; border: 1px solid;
  font-family: 'Oswald', sans-serif; font-size: 0.65rem;
  letter-spacing: 0.08em; text-transform: uppercase;
  cursor: pointer; transition: all 0.15s;
}
.toggle-inactive { background: transparent; border-color: rgba(255,255,255,0.08); color: rgba(255,255,255,0.35); }
.toggle-inactive:hover { border-color: rgba(255,255,255,0.2); color: rgba(255,255,255,0.7); }
.toggle-active-red   { background: rgba(220,38,38,0.12); border-color: #dc2626; color: #fff; }
.toggle-active-amber { background: rgba(217,119,6,0.12); border-color: #d97706; color: #fbbf24; }
.toggle-active-white { background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.2); color: #fff; }
.toggle-disabled { background: transparent; border-color: rgba(255,255,255,0.04); color: rgba(255,255,255,0.12); cursor: not-allowed; }

/* Change box */
.change-box {
  display: flex; justify-content: space-between;
  padding: 0.55rem 0.85rem; border-radius: 9px;
  font-family: monospace; font-size: 0.78rem; font-weight: 700; border: 1px solid;
}
.change-ok  { background: rgba(34,197,94,0.07);  border-color: rgba(34,197,94,0.2);  color: #4ade80; }
.change-err { background: rgba(239,68,68,0.07);  border-color: rgba(239,68,68,0.2);  color: #f87171; }

/* Kasir strip */
.kasir-strip {
  padding: 0.7rem 1.4rem;
  display: flex; align-items: center; gap: 0.4rem;
  font-size: 0.7rem; color: rgba(255,255,255,0.25);
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.kasir-name { color: rgba(255,255,255,0.55); font-weight: 600; }

/* Price summary */
.price-summary {
  padding: 1rem 1.4rem;
  display: flex; flex-direction: column; gap: 0.6rem;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.price-row {
  display: flex; justify-content: space-between;
  font-size: 0.78rem; font-family: monospace; color: rgba(255,255,255,0.45);
}
.price-discount { color: #4ade80; }
.price-total {
  display: flex; justify-content: space-between;
  padding-top: 0.5rem; border-top: 1px solid rgba(255,255,255,0.08);
  font-family: 'Oswald', sans-serif; font-size: 0.8rem;
  letter-spacing: 0.08em; text-transform: uppercase;
  color: rgba(255,255,255,0.6); font-weight: 500;
}
.total-val { font-family: monospace; font-size: 1.15rem; font-weight: 800; color: #dc2626; }

/* Submit */
.submit-btn {
  display: flex; align-items: center; justify-content: center; gap: 0.45rem;
  margin: 1rem 1.4rem 1.25rem;
  padding: 0.85rem; border-radius: 12px; border: none;
  background: #dc2626; color: #fff;
  font-family: 'Oswald', sans-serif; font-size: 0.8rem;
  letter-spacing: 0.12em; text-transform: uppercase;
  cursor: pointer; transition: background 0.15s;
  box-shadow: 0 4px 20px rgba(220,38,38,0.2);
}
.submit-btn:hover:not(:disabled) { background: #b91c1c; }
.submit-btn:disabled { background: rgba(255,255,255,0.06); color: rgba(255,255,255,0.25); cursor: not-allowed; box-shadow: none; }
.btn-spinner {
  width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0;
  border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff;
  animation: spin 0.75s linear infinite;
}

/* ── Drawer ──────────────────────────────────────────────────────── */
.drawer-overlay {
  position: fixed; inset: 0; z-index: 50;
  background: rgba(0,0,0,0.7); backdrop-filter: blur(3px);
}
.drawer-enter-active { transition: opacity 0.25s ease; }
.drawer-enter-from   { opacity: 0; }
.drawer-leave-active { transition: opacity 0.2s ease; }
.drawer-leave-to     { opacity: 0; }

.drawer-box {
  position: absolute; right: 0; top: 0; bottom: 0;
  width: 400px; max-width: 100%;
  background: #0d0d0d; border-left: 1px solid rgba(255,255,255,0.07);
  display: flex; flex-direction: column; overflow: hidden;
}
.drawer-head {
  display: flex; align-items: flex-start; justify-content: space-between;
  padding: 1.5rem 1.5rem 1.1rem;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.drawer-title {
  font-family: 'Oswald', sans-serif; font-size: 1.05rem; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.06em; margin: 0;
}
.drawer-close {
  width: 30px; height: 30px; border-radius: 8px;
  background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.4); cursor: pointer;
  display: flex; align-items: center; justify-content: center; transition: all 0.15s;
}
.drawer-close:hover { background: rgba(255,255,255,0.1); color: #fff; }

.drawer-search-wrap { position: relative; padding: 0.85rem 1.25rem; border-bottom: 1px solid rgba(255,255,255,0.05); }
.drawer-search-icon { position: absolute; left: 2rem; top: 50%; transform: translateY(-50%); color: rgba(255,255,255,0.2); pointer-events: none; }
.drawer-search {
  width: 100%; background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08); border-radius: 9px;
  padding: 0.6rem 0.85rem 0.6rem 2.2rem;
  color: #fff; font-size: 0.8rem; outline: none; transition: border-color 0.15s;
}
.drawer-search::placeholder { color: rgba(255,255,255,0.18); }
.drawer-search:focus { border-color: rgba(220,38,38,0.4); }

.drawer-empty {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 0.4rem; padding: 3rem;
  color: rgba(255,255,255,0.2); font-size: 0.8rem;
}
.drawer-list { flex: 1; overflow-y: auto; padding: 1rem 1.25rem; display: flex; flex-direction: column; gap: 0.75rem; }

.drawer-order-card {
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px; padding: 1rem; display: flex; flex-direction: column; gap: 0.75rem;
}
.drawer-order-top { display: flex; justify-content: space-between; gap: 0.5rem; }
.drawer-order-num { font-family: monospace; font-weight: 700; font-size: 0.82rem; color: #fff; margin: 0 0 0.2rem; }
.drawer-order-name { font-size: 0.76rem; color: rgba(255,255,255,0.55); margin: 0 0 0.15rem; }
.drawer-order-phone { font-family: monospace; font-size: 0.68rem; color: rgba(255,255,255,0.3); margin: 0; }
.drawer-order-right { text-align: right; flex-shrink: 0; }
.drawer-order-total { font-family: monospace; font-weight: 700; color: #dc2626; font-size: 0.9rem; margin: 0 0 0.2rem; }
.drawer-order-items { font-size: 0.65rem; color: rgba(255,255,255,0.3); margin: 0; }
.drawer-pay-btn {
  display: flex; align-items: center; justify-content: center; gap: 0.4rem;
  width: 100%; padding: 0.6rem; border-radius: 9px; border: none;
  background: #dc2626; color: #fff;
  font-family: 'Oswald', sans-serif; font-size: 0.68rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: background 0.15s;
}
.drawer-pay-btn:hover { background: #b91c1c; }

/* ── Modal ───────────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed; inset: 0; z-index: 70;
  background: rgba(0,0,0,0.8); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; padding: 1rem;
}
.modal-enter-active { transition: all 0.2s ease; }
.modal-enter-from   { opacity: 0; transform: scale(0.95); }
.modal-leave-active { transition: all 0.15s ease; }
.modal-leave-to     { opacity: 0; transform: scale(0.95); }

.modal-box {
  background: #0f0f0f; border: 1px solid rgba(255,255,255,0.08);
  border-radius: 18px; width: 100%; max-width: 460px;
  max-height: 90vh; overflow-y: auto;
  display: flex; flex-direction: column; gap: 0;
}
.modal-head {
  display: flex; align-items: flex-start; justify-content: space-between;
  padding: 1.5rem 1.5rem 1rem; border-bottom: 1px solid rgba(255,255,255,0.05);
}
.modal-title {
  font-family: 'Oswald', sans-serif; font-size: 1.05rem; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.06em; margin: 0 0 0.2rem;
}
.modal-ordnum { font-family: monospace; font-size: 0.78rem; color: rgba(255,255,255,0.35); margin: 0; }
.modal-close-btn {
  width: 30px; height: 30px; border-radius: 8px;
  background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.4); cursor: pointer;
  display: flex; align-items: center; justify-content: center; transition: all 0.15s;
}
.modal-close-btn:hover { background: rgba(255,255,255,0.1); color: #fff; }

.modal-customer {
  padding: 0.85rem 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.04);
}
.modal-cust-name { font-weight: 600; font-size: 0.88rem; margin: 0 0 0.15rem; }
.modal-cust-phone { font-family: monospace; font-size: 0.72rem; color: rgba(255,255,255,0.35); margin: 0; }

.modal-items {
  padding: 0.85rem 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.04);
  display: flex; flex-direction: column; gap: 0.5rem; max-height: 200px; overflow-y: auto;
}
.modal-item { display: flex; justify-content: space-between; gap: 0.5rem; align-items: flex-start; }
.modal-item-left { flex: 1; min-width: 0; }
.modal-item-name { font-size: 0.82rem; font-weight: 600; color: rgba(255,255,255,0.8); margin: 0 0 0.15rem; }
.modal-item-qty { color: rgba(255,255,255,0.4); font-weight: 400; font-size: 0.75rem; }
.modal-item-note { font-size: 0.67rem; color: #fbbf24; font-style: italic; margin: 0; }
.modal-item-price { font-family: monospace; font-size: 0.8rem; color: rgba(255,255,255,0.6); flex-shrink: 0; }

.modal-totals {
  padding: 0.85rem 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.04);
  display: flex; flex-direction: column; gap: 0.35rem;
}
.modal-total-row { display: flex; justify-content: space-between; font-size: 0.78rem; font-family: monospace; color: rgba(255,255,255,0.45); }
.modal-discount { color: #4ade80; }
.modal-total-final {
  display: flex; justify-content: space-between;
  padding-top: 0.5rem; border-top: 1px solid rgba(255,255,255,0.07);
  font-family: 'Oswald', sans-serif; font-size: 0.82rem; letter-spacing: 0.06em;
  text-transform: uppercase; color: rgba(255,255,255,0.6); font-weight: 500;
}
.modal-total-final span:last-child { font-family: monospace; font-size: 1.05rem; font-weight: 800; color: #dc2626; }

.modal-section { padding: 0.85rem 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.04); display: flex; flex-direction: column; gap: 0.55rem; }

.modal-box > .submit-btn { margin: 1rem 1.5rem 1.25rem; }

/* Scrollbar hide for number */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
input[type="number"] { -moz-appearance: textfield; }
</style>