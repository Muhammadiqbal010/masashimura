<template>
  <div class="pos-root">

    <!-- ── KATALOG MENU ─────────────────────────────────────────────── -->
    <div class="catalog-panel">

      <div class="catalog-header">
        <div>
          <p class="pos-eyebrow">Masashimura · Kasir</p>
          <h1 class="pos-title">New Order (POS)</h1>
          <p class="pos-date">{{ liveFormattedDate }}</p>
        </div>
        <button @click="showUnpaidDrawer = true" class="unpaid-trigger">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          <span>Tagihan</span>
          <span v-if="unpaidOrders.length" class="unpaid-badge">{{ unpaidOrders.length }}</span>
        </button>
      </div>

      <div class="search-bar">
        <svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
        <input v-model="searchQuery" type="text" placeholder="Cari menu..." class="search-input" />
        <button v-if="searchQuery" @click="searchQuery = ''" class="search-clear-btn" aria-label="Hapus pencarian">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </button>
      </div>

      <div v-if="isLoadingMenus" class="menu-grid">
        <div v-for="n in 6" :key="n" class="menu-skeleton"></div>
      </div>

      <div v-else-if="menuLoadError" class="menu-error">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <p>Gagal memuat katalog menu dari database</p>
        <button @click="fetchMenus" class="retry-btn">Coba Lagi</button>
      </div>

      <div v-else-if="filteredMenus.length === 0" class="menu-empty">
        <div class="empty-icon">🍱</div>
        <p class="empty-text">Menu tidak ditemukan</p>
        <p class="empty-hint">Coba kata kunci lain</p>
      </div>

      <div v-else class="menu-grid">
        <button
          v-for="menu in filteredMenus"
          :key="menu.id"
          class="menu-card"
          :class="menu.is_available ? 'menu-card-avail' : 'menu-card-unavail'"
          :disabled="!menu.is_available"
          @click="addToOrder(menu)"
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
    <div class="order-panel" :class="{ 'mobile-cart-open': showMobileCart }">
      <div class="order-panel-head">
        <div>
          <p class="pos-eyebrow">Transaksi Aktif</p>
          <h2 class="order-panel-title">Ringkasan Pesanan</h2>
        </div>
        <button class="order-panel-close" @click="showMobileCart = false" aria-label="Tutup keranjang">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </button>
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
              inputmode="tel"
              placeholder="081234567xxx"
              class="pos-input flex-1"
            />
          </div>
        </div>

        <div class="field">
          <label class="field-label">Nama Pelanggan <span class="field-optional">(Opsional)</span></label>
          <input v-model="customerName" type="text" placeholder="Nama pembeli..." class="pos-input" />
        </div>

        <div
          v-if="customerPhone.length >= 9"
          class="loyalty-status"
          :class="isTrackingLoyalty ? 'ls-loading' : isMember ? 'ls-loyal' : 'ls-regular'"
        >
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
      <div class="order-section">
        <div v-if="orderItems.length === 0" class="cart-empty">
          <div class="cart-empty-icon">🛒</div>
          <p>Keranjang masih kosong</p>
          <p class="cart-empty-hint">Tap menu di kiri untuk menambah item</p>
        </div>

        <div v-else class="cart-list">
          <div v-for="(item, index) in orderItems" :key="index" class="cart-item">
            <div class="cart-item-top">
              <div class="cart-item-info">
                <p class="cart-item-name">{{ item.name }}</p>
                <p class="cart-item-price">{{ formatPrice(item.price) }}</p>
              </div>
              <div class="qty-control">
                <button @click="updateQty(index, -1)" class="qty-btn" aria-label="Kurangi">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="5" y1="12" x2="19" y2="12"/></svg>
                </button>
                <span class="qty-val">{{ item.quantity }}</span>
                <button @click="updateQty(index, 1)" class="qty-btn" aria-label="Tambah">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                </button>
              </div>
            </div>
            <input
              type="text"
              v-model="item.notes"
              @change="handleNotesChange(index)"
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
              : paymentMethod === 'qris_manual' ? 'toggle-disabled' : 'toggle-inactive'"
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
      <div v-if="isCashNow" class="order-section">
        <label class="field-label">Uang Diterima</label>
        <input v-model.number="amountPaid" type="number" min="0" placeholder="0" class="pos-input font-mono" />
        <div v-if="amountPaid > 0 && amountPaid >= totalPrice" class="change-box change-ok">
          <span>Kembalian</span>
          <span>{{ formatPrice(changeDue) }}</span>
        </div>
        <div v-else-if="amountPaid > 0 && amountPaid < totalPrice" class="change-box change-err">
          <span>Kurang</span>
          <span>{{ formatPrice(totalPrice - amountPaid) }}</span>
        </div>
      </div>

      <!-- Kasir -->
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

  <!-- ── BACKDROP + FLOATING CART (MOBILE) ───────────────────────── -->
  <div v-if="showMobileCart" class="mobile-cart-backdrop" @click="showMobileCart = false"></div>

  <button
    v-if="orderItems.length && !showMobileCart"
    @click="showMobileCart = true"
    class="mobile-cart-fab"
  >
    <span class="mcf-count">{{ cartItemCount }}</span>
    <span class="mcf-label">Lihat Pesanan</span>
    <span class="mcf-total">{{ formatPrice(totalPrice) }}</span>
  </button>

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
          <button class="drawer-close" @click="showUnpaidDrawer = false" aria-label="Tutup">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>

        <div class="drawer-search-wrap">
          <svg class="drawer-search-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
          <input v-model="unpaidSearch" placeholder="Cari order, nama, no HP..." class="drawer-search" />
        </div>

        <div v-if="filteredUnpaidOrders.length" class="drawer-summary">
          <span>{{ filteredUnpaidOrders.length }} tagihan</span>
          <strong>{{ formatPrice(unpaidGrandTotal) }}</strong>
        </div>

        <!-- Area scroll: WAJIB dibungkus .drawer-list supaya bisa di-scroll -->
        <div class="drawer-list">
          <div v-if="isLoadingUnpaid && !unpaidOrders.length" class="drawer-empty">
            <div class="ls-spinner"></div>
            <p>Memuat tagihan...</p>
          </div>

          <div v-else-if="!filteredUnpaidOrders.length" class="drawer-empty">
            <div class="empty-icon">✓</div>
            <p>Tidak ada tagihan tertunda</p>
          </div>

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

            <ul class="drawer-items">
              <li v-for="item in order.items" :key="item.id" class="drawer-item">
                <div class="drawer-item-info">
                  <span class="drawer-item-name">{{ item.menu_name }}</span>
                  <span v-if="item.is_point_redemption" class="drawer-item-note">Reward poin</span>
                  <span v-else-if="item.notes" class="drawer-item-note">{{ item.notes }}</span>
                </div>

                <div v-if="isMode(order, 'edit') && !item.is_point_redemption" class="qty-stepper">
                  <button :disabled="isBusy" @click="changeQty(order, item, -1)" aria-label="Kurangi">−</button>
                  <span>{{ item.quantity }}</span>
                  <button :disabled="isBusy" @click="changeQty(order, item, 1)" aria-label="Tambah">+</button>
                </div>

                <div v-else-if="isMode(order, 'split') && !item.is_point_redemption" class="qty-stepper">
                  <button @click="stepSplit(item, -1)" aria-label="Kurangi">−</button>
                  <span>{{ splitQty[item.id] || 0 }}/{{ item.quantity }}</span>
                  <button @click="stepSplit(item, 1)" aria-label="Tambah">+</button>
                </div>

                <span v-else class="drawer-item-qty">×{{ item.quantity }}</span>
                <span class="drawer-item-price">{{ formatPrice(Number(item.price) * item.quantity) }}</span>
              </li>
            </ul>

            <!-- Tambah menu (mode ubah) -->
            <div v-if="isMode(order, 'edit')" class="drawer-add-row">
              <select
                v-model="addMenuId"
                class="pos-input"
                :disabled="isBusy"
                @change="addItemToOrder(order)"
              >
                <option value="" disabled>+ Tambah menu…</option>
                <option v-for="m in addableMenus" :key="m.id" :value="m.id">
                  {{ m.name }} — {{ formatPrice(m.price) }}
                </option>
              </select>
            </div>

            <!-- Panel pisah bayar -->
            <div v-if="isMode(order, 'split')" class="drawer-split-box">
              <p class="drawer-hint">Atur jumlah yang dipindah ke nota baru (yang tidak dipilih tetap di nota ini).</p>
              <input v-model="splitName" class="pos-input" placeholder="Nama nota baru (opsional)" />
              <div class="drawer-split-total">
                <span>Nota baru</span>
                <span>{{ formatPrice(splitSelectedTotal(order)) }}</span>
              </div>
              <button class="drawer-pay-btn" :disabled="isBusy" @click="submitSplit(order)">
                Buat Nota Terpisah
              </button>
            </div>

            <div class="drawer-actions">
              <button
                class="drawer-ghost-btn"
                :class="{ active: isMode(order, 'edit') }"
                @click="toggleCardMode(order, 'edit')"
              >{{ isMode(order, 'edit') ? 'Selesai' : 'Ubah' }}</button>

              <button
                v-if="canSplit(order)"
                class="drawer-ghost-btn"
                :class="{ active: isMode(order, 'split') }"
                @click="toggleCardMode(order, 'split')"
              >{{ isMode(order, 'split') ? 'Batal' : 'Pisah' }}</button>

              <button class="drawer-pay-btn" @click="openPaymentModal(order)">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="2" y="6" width="20" height="12" rx="2"/><path d="M12 12h.01"/></svg>
                Bayar Sekarang
              </button>
            </div>
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
          <button class="modal-close-btn" @click="showPaymentModal = false" aria-label="Tutup">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>

        <div class="modal-customer">
          <p class="modal-cust-name">{{ selectedUnpaidOrder.customer_name || 'Walk In' }}</p>
          <p class="modal-cust-phone">{{ selectedUnpaidOrder.customer_phone || '—' }}</p>
        </div>

        <div class="modal-items">
          <div v-for="item in selectedUnpaidOrder.items" :key="item.id" class="modal-item">
            <div class="modal-item-left">
              <p class="modal-item-name">{{ item.menu_name }} <span class="modal-item-qty">×{{ item.quantity }}</span></p>
              <p v-if="item.is_point_redemption" class="modal-item-note">Reward poin</p>
              <p v-else-if="item.notes" class="modal-item-note">{{ item.notes }}</p>
            </div>
            <span class="modal-item-price">{{ formatPrice(Number(item.price) * item.quantity) }}</span>
          </div>
        </div>

        <div class="modal-totals">
          <div class="modal-total-row">
            <span>Subtotal</span>
            <span>{{ formatPrice(selectedUnpaidOrder.subtotal) }}</span>
          </div>
          <div v-if="Number(selectedUnpaidOrder.promo_discount_amount) > 0" class="modal-total-row modal-discount">
            <span>Diskon Promo{{ selectedUnpaidOrder.promo_code ? ` (${selectedUnpaidOrder.promo_code})` : '' }}</span>
            <span>−{{ formatPrice(selectedUnpaidOrder.promo_discount_amount) }}</span>
          </div>
          <div class="modal-total-final">
            <span>Total</span>
            <span>{{ formatPrice(selectedUnpaidOrder.total_price) }}</span>
          </div>
        </div>

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

        <div v-if="selectedPaymentMethod === 'cash'" class="modal-section">
          <label class="field-label">Uang Diterima</label>
          <input v-model.number="amountPaidModal" type="number" min="0" placeholder="0" class="pos-input font-mono" />
          <div v-if="amountPaidModal > 0 && amountPaidModal >= modalTotal" class="change-box change-ok">
            <span>Kembalian</span>
            <span>{{ formatPrice(amountPaidModal - modalTotal) }}</span>
          </div>
          <div v-else-if="amountPaidModal > 0 && amountPaidModal < modalTotal" class="change-box change-err">
            <span>Kurang</span>
            <span>{{ formatPrice(modalTotal - amountPaidModal) }}</span>
          </div>
        </div>

        <button
          @click="confirmPayment"
          :disabled="isPaying || modalUnderpaid"
          class="submit-btn"
        >
          <span v-if="isPaying" class="btn-spinner"></span>
          {{ isPaying ? 'Memproses...' : 'Konfirmasi Pembayaran' }}
        </button>

      </div>
    </div>
  </transition>

  <!-- ── STRUK TERSEMBUNYI (dirender dari data server: lastOrder) ──── -->
  <div
    ref="receiptRef"
    style="position:fixed;left:-9999px;top:0;width:380px;background:#fff;color:#000;padding:24px;font-family:'Courier New',monospace;font-size:12px;line-height:1.6;"
  >
    <div style="text-align:center;margin-bottom:12px;">
      <p style="font-size:15px;font-weight:900;text-transform:uppercase;letter-spacing:0.1em;">MASASHIMURA</p>
      <p style="font-size:10px;color:#666;">Jl. Pintu air no 48 Depan Pengadilan Bekasi</p>
      <p style="font-size:10px;color:#999;">{{ receiptDate }}</p>
      <p style="color:#ccc;">========================================</p>
    </div>

    <template v-if="lastOrder">
      <div style="font-size:11px;margin-bottom:10px;">
        <div style="display:flex;justify-content:space-between;"><span>No. Nota</span><span style="font-weight:700;">{{ lastOrder.order_number }}</span></div>
        <div style="display:flex;justify-content:space-between;"><span>Kasir</span><span>{{ lastOrder.kasir_name || kasirName }}</span></div>
        <div style="display:flex;justify-content:space-between;"><span>Pelanggan</span><span>{{ lastOrder.customer_name || lastOrder.customer_phone || 'Walk In' }}</span></div>
      </div>
      <p style="color:#ccc;margin-bottom:10px;">----------------------------------------</p>

      <div style="margin-bottom:10px;">
        <div v-for="item in lastOrder.items" :key="item.id" style="margin-bottom:6px;">
          <div style="display:flex;justify-content:space-between;font-weight:600;">
            <span>{{ item.quantity }}x {{ item.menu_name }}</span>
            <span>{{ item.is_point_redemption ? 'GRATIS' : formatPrice(Number(item.price) * item.quantity) }}</span>
          </div>
          <div v-if="item.is_point_redemption" style="color:#16a34a;font-size:10px;padding-left:10px;">🎁 Reward poin</div>
          <div v-else-if="item.notes" style="color:#b45309;font-size:10px;padding-left:10px;font-style:italic;">📋 {{ item.notes }}</div>
        </div>
      </div>
      <p style="color:#ccc;margin-bottom:10px;">----------------------------------------</p>

      <div style="font-size:11px;margin-bottom:10px;">
        <div style="display:flex;justify-content:space-between;margin-bottom:3px;"><span>Subtotal</span><span>{{ formatPrice(lastOrder.subtotal || lastOrder.total_price) }}</span></div>
        <div v-if="Number(lastOrder.promo_discount_amount) > 0" style="display:flex;justify-content:space-between;color:#16a34a;margin-bottom:3px;"><span>Diskon Promo</span><span>-{{ formatPrice(lastOrder.promo_discount_amount) }}</span></div>
        <div style="display:flex;justify-content:space-between;font-size:14px;font-weight:900;border-top:1px solid #eee;padding-top:4px;margin-bottom:4px;"><span>TOTAL</span><span>{{ formatPrice(lastOrder.total_price) }}</span></div>
        <div v-if="Number(lastOrder.amount_paid) > 0" style="display:flex;justify-content:space-between;"><span>Bayar</span><span>{{ formatPrice(lastOrder.amount_paid) }}</span></div>
        <div v-if="Number(lastOrder.change_amount) > 0" style="display:flex;justify-content:space-between;color:#16a34a;font-weight:700;"><span>Kembalian</span><span>{{ formatPrice(lastOrder.change_amount) }}</span></div>
      </div>
      <p style="color:#ccc;margin-bottom:10px;">========================================</p>

      <div style="text-align:center;font-size:10px;color:#888;">
        <p v-if="lastOrder.payment_status !== 'paid'" style="font-weight:700;color:#b45309;">BELUM LUNAS</p>
        <p>Metode: {{ receiptMethod }}</p>
        <p style="font-weight:700;margin-top:4px;">Terima kasih sudah makan di Masashimura! 🙏</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from "vue";
import { menuAPI, orderAPI, apiClient } from "@/api";
import { toast } from "vue-sonner";
import { useAuthStore } from "@/stores/auth";
import PromoCodeBox from "@/components/ui/PromoCodeBox.vue";
import PointRedeemBox from "@/components/ui/PointRedeemBox.vue";

const authStore = useAuthStore();
const kasirName = computed(() => authStore.user?.name || authStore.user?.username || "Staff");

// ── State: katalog & keranjang ───────────────────────────────────────
const menus          = ref([]);
const isLoadingMenus = ref(false);
const menuLoadError  = ref(false);
const searchQuery    = ref("");
const orderItems     = ref([]);
const showMobileCart = ref(false);

// ── State: pelanggan & loyalty ───────────────────────────────────────
const customerPhone      = ref("");
const customerName       = ref("");
const isMember           = ref(false);
const memberPoints       = ref(0);
const pointsExpiringNote = ref(null);
const isTrackingLoyalty  = ref(false);
const affordableRewards  = ref([]);
const lockedRewards      = ref([]);
const selectedRewardIds  = ref([]);
let debounceTimeout = null;

// ── State: pembayaran ────────────────────────────────────────────────
const paymentMethod = ref("cash");
const orderType     = ref("dine_in_now");
const amountPaid    = ref(0);
const isSubmitting  = ref(false);

// ── State: promo ─────────────────────────────────────────────────────
const promoBoxRef  = ref(null);
const appliedPromo = ref(null); // { promo_id, code, discount_amount }
const onPromoApplied = (promo) => { appliedPromo.value = promo; };
const onPromoRemoved = () => { appliedPromo.value = null; };

// ── State: tagihan belum lunas ───────────────────────────────────────
const unpaidOrders          = ref([]);
const unpaidSearch          = ref("");
const showUnpaidDrawer      = ref(false);
const isLoadingUnpaid       = ref(false);
const selectedUnpaidOrder   = ref(null);
const showPaymentModal      = ref(false);
const selectedPaymentMethod = ref("cash");
const amountPaidModal       = ref(0);
const isPaying              = ref(false);

// ── State: ubah item & pisah bayar ───────────────────────────────────
const cardMode  = ref({ id: null, mode: null }); // mode: 'edit' | 'split'
const isBusy    = ref(false);
const addMenuId = ref("");
const splitQty  = ref({});   // { [itemId]: jumlah yang dipindah ke nota baru }
const splitName = ref("");

// ── State: struk ─────────────────────────────────────────────────────
const receiptRef = ref(null);
const lastOrder  = ref(null);

// ── Computed ─────────────────────────────────────────────────────────
const liveFormattedDate = computed(() =>
  new Date().toLocaleDateString("id-ID", { weekday: "long", year: "numeric", month: "long", day: "numeric" })
);

const customerInitial = computed(() =>
  customerPhone.value ? customerPhone.value.trim().charAt(0).toUpperCase() : "?"
);

const cartItemCount = computed(() =>
  orderItems.value.reduce((acc, i) => acc + i.quantity, 0)
);

const filteredMenus = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  return menus.value
    .filter((m) => !q || m.name?.toLowerCase().includes(q))
    .sort((a, b) => Number(b.is_available) - Number(a.is_available));
});

// subtotal → diskon promo → total (diskon member % sudah dihapus; reward poin = item gratis)
const subtotal = computed(() =>
  orderItems.value.reduce((acc, item) => acc + Number(item.price) * item.quantity, 0)
);
const totalPrice = computed(() =>
  Math.max(subtotal.value - (appliedPromo.value?.discount_amount || 0), 0)
);

const isCashNow = computed(() => paymentMethod.value === "cash" && orderType.value === "dine_in_now");
const changeDue = computed(() =>
  isCashNow.value && amountPaid.value >= totalPrice.value ? amountPaid.value - totalPrice.value : 0
);

const selectedRewards = computed(() =>
  affordableRewards.value.filter((r) => selectedRewardIds.value.includes(r.id))
);

const filteredUnpaidOrders = computed(() => {
  const q = unpaidSearch.value.toLowerCase().trim();
  if (!q) return unpaidOrders.value;
  return unpaidOrders.value.filter((o) =>
    o.order_number?.toLowerCase().includes(q) ||
    o.customer_name?.toLowerCase().includes(q) ||
    o.customer_phone?.includes(q)
  );
});

const unpaidGrandTotal = computed(() =>
  filteredUnpaidOrders.value.reduce((sum, o) => sum + Number(o.total_price || 0), 0)
);

const addableMenus = computed(() => menus.value.filter((m) => m.is_available !== false));

const modalTotal = computed(() => Number(selectedUnpaidOrder.value?.total_price || 0));
const modalUnderpaid = computed(() =>
  selectedPaymentMethod.value === "cash" && amountPaidModal.value > 0 && amountPaidModal.value < modalTotal.value
);

const receiptDate = computed(() =>
  new Date(lastOrder.value?.created_at || Date.now()).toLocaleString("id-ID")
);
const RECEIPT_METHOD_LABEL = { cash: "CASH", qris: "QRIS", qris_manual: "QRIS", gateway: "GATEWAY", mixed: "CAMPURAN" };
const receiptMethod = computed(() => {
  const m = lastOrder.value?.payment_method;
  return RECEIPT_METHOD_LABEL[m] || (m ? m.toUpperCase() : "CASH");
});

// ── Helpers ──────────────────────────────────────────────────────────
const formatPrice = (p) =>
  new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", minimumFractionDigits: 0 }).format(Number(p) || 0);

const apiError = (e, fallback) =>
  toast.error(e.response?.data?.detail || e.response?.data?.error || fallback);

// ── Fetch ────────────────────────────────────────────────────────────
const fetchMenus = async () => {
  isLoadingMenus.value = true;
  menuLoadError.value = false;
  try {
    const res = await menuAPI.getAll();
    menus.value = res.data;
  } catch {
    menuLoadError.value = true;
  } finally {
    isLoadingMenus.value = false;
  }
};

const fetchUnpaidOrders = async () => {
  isLoadingUnpaid.value = true;
  try {
    const { data } = await apiClient.get("/orders/unpaid/");
    unpaidOrders.value = data;
  } catch (err) {
    console.error(err);
  } finally {
    isLoadingUnpaid.value = false;
  }
};

// ── Loyalty & point rewards ──────────────────────────────────────────
const resetLoyalty = () => {
  isMember.value = false;
  memberPoints.value = 0;
  pointsExpiringNote.value = null;
};

const resetPointRewards = () => {
  affordableRewards.value = [];
  lockedRewards.value = [];
  selectedRewardIds.value = [];
};

const debounceTrackLoyalty = () => {
  clearTimeout(debounceTimeout);
  if (customerPhone.value.length < 9) {
    isTrackingLoyalty.value = false;
    resetLoyalty();
    resetPointRewards();
    return;
  }
  isTrackingLoyalty.value = true;
  debounceTimeout = setTimeout(checkLoyalty, 800);
};

const checkLoyalty = async () => {
  const phone = customerPhone.value;
  const isStale = () => phone !== customerPhone.value; // nomor sudah berubah selama request

  try {
    const { data } = await apiClient.get("/orders/check_loyalty_status/", { params: { phone } });
    if (isStale()) return;
    isMember.value = data.is_member ?? false;
    memberPoints.value = data.points ?? 0;
    pointsExpiringNote.value = data.points_expiring_note ?? null;
  } catch {
    if (isStale()) return;
    resetLoyalty();
  } finally {
    if (!isStale()) isTrackingLoyalty.value = false;
  }

  // terpisah supaya status loyalty tidak ke-block kalau ini gagal
  if (!isStale()) fetchPointRewards(phone);
};

const fetchPointRewards = async (phone) => {
  try {
    const { data } = await orderAPI.getAvailablePointRewards(phone);
    if (phone !== customerPhone.value) return;
    affordableRewards.value = data.affordable ?? [];
    lockedRewards.value = data.locked ?? [];
  } catch {
    if (phone === customerPhone.value) resetPointRewards();
  }
};

// ── Keranjang ────────────────────────────────────────────────────────
const addToOrder = (menu) => {
  if (!menu.is_available) { toast.error("Menu ini sedang habis!"); return; }
  const existing = orderItems.value.find((i) => i.id === menu.id && i.notes === "");
  if (existing) existing.quantity++;
  else orderItems.value.push({ ...menu, quantity: 1, notes: "" });
};

// Dipanggil saat input catatan selesai diedit (@change), bukan tiap ketikan,
// supaya item tidak ke-merge di tengah mengetik.
const handleNotesChange = (index) => {
  const cur = orderItems.value[index];
  if (!cur) return;
  const norm = (s) => (s || "").trim().toLowerCase();
  const dup = orderItems.value.findIndex(
    (item, idx) => idx !== index && item.id === cur.id && norm(item.notes) === norm(cur.notes)
  );
  if (dup > -1) {
    orderItems.value[dup].quantity += cur.quantity;
    orderItems.value.splice(index, 1);
    toast.info("Item dengan catatan sama digabungkan!");
  }
};

const updateQty = (index, delta) => {
  orderItems.value[index].quantity += delta;
  if (orderItems.value[index].quantity <= 0) orderItems.value.splice(index, 1);
};

const selectPaymentMethod = (method) => {
  paymentMethod.value = method;
  if (method === "qris_manual") orderType.value = "dine_in_now";
};

// ── Submit order baru ────────────────────────────────────────────────
const resetForm = () => {
  orderItems.value = [];
  customerPhone.value = "";
  customerName.value = "";
  resetLoyalty();
  resetPointRewards();
  paymentMethod.value = "cash";
  orderType.value = "dine_in_now";
  amountPaid.value = 0;
  promoBoxRef.value?.removePromo();
  showMobileCart.value = false;
};

const submitOrder = async () => {
  if (orderItems.value.length === 0) return toast.error("Keranjang kosong!");
  if (isCashNow.value && amountPaid.value > 0 && amountPaid.value < totalPrice.value) {
    return toast.error("Uang diterima kurang dari total tagihan");
  }

  isSubmitting.value = true;

  // Harga, diskon promo, dan status dihitung ulang di server — client hanya kirim niat.
  const payload = {
    source: "pos",
    customer: customerPhone.value
      ? { phone: customerPhone.value, name: customerName.value || "Member Baru" }
      : null,
    payment_method: paymentMethod.value,
    payment_status: orderType.value === "dine_in_later" ? "pending" : "paid",
    amount_paid: isCashNow.value ? amountPaid.value || 0 : 0,
    kasir_name: kasirName.value,
    promo_id: appliedPromo.value?.promo_id || null,
    redeem_reward_ids: selectedRewardIds.value,
    items: orderItems.value.map((item) => ({
      menu_id: item.id,
      quantity: item.quantity,
      notes: item.notes,
    })),
  };

  try {
    const res = await apiClient.post("/orders/", payload);
    lastOrder.value = res.data;
    toast.success("Pesanan berhasil masuk ke sistem!");
    resetForm();
    fetchUnpaidOrders();
    await shareReceiptAsImage(res.data);
  } catch (e) {
    console.error(e);
    apiError(e, "Gagal menyimpan transaksi ke server.");
  } finally {
    isSubmitting.value = false;
  }
};

// ── Struk ────────────────────────────────────────────────────────────
const canvasToBlob = (canvas) => new Promise((resolve) => canvas.toBlob(resolve, "image/png"));

const downloadBlob = (blob, filename) => {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
};

const toWaNumber = (raw) => {
  const digits = (raw || "").replace(/\D/g, "");
  return digits.startsWith("0") ? `62${digits.slice(1)}` : digits;
};

const shareReceiptAsImage = async (orderData) => {
  await nextTick();                                   // tunggu struk ter-render dengan lastOrder
  await new Promise((r) => setTimeout(r, 150));

  try {
    const { default: html2canvas } = await import("html2canvas"); // lazy-load, bundle awal lebih ringan
    const canvas = await html2canvas(receiptRef.value, { backgroundColor: "#ffffff", scale: 2, useCORS: true });
    const blob = await canvasToBlob(canvas);
    if (!blob) throw new Error("Blob struk kosong");

    const filename = `struk-${orderData.order_number}.png`;
    const file = new File([blob], filename, { type: "image/png" });

    if (navigator.canShare?.({ files: [file] })) {
      try {
        await navigator.share({ files: [file], text: "Bukti Pembelian di Masashimura 🙏" });
        return;
      } catch (err) {
        if (err?.name === "AbortError") return;       // kasir menutup dialog share
        // gagal share (mis. izin gesture kedaluwarsa) → lanjut ke unduh manual
      }
    }

    downloadBlob(blob, filename);
    const caption = encodeURIComponent("Bukti Pembelian di Masashimura 🙏");
    const phone = toWaNumber(orderData.customer_phone); // dari data order, bukan form (form sudah di-reset)
    setTimeout(
      () => window.open(phone ? `https://wa.me/${phone}?text=${caption}` : `https://wa.me/?text=${caption}`, "_blank"),
      500
    );
    toast.info("Gambar diunduh. Lampirkan ke WhatsApp secara manual.");
  } catch (err) {
    console.error(err);
    toast.error("Gagal membuat screenshot struk");
  }
};

// ── Drawer tagihan: bayar ────────────────────────────────────────────
const openPaymentModal = (order) => {
  selectedUnpaidOrder.value = order;
  selectedPaymentMethod.value = "cash";
  amountPaidModal.value = 0;
  showPaymentModal.value = true;
};

const confirmPayment = async () => {
  if (!selectedUnpaidOrder.value || modalUnderpaid.value) return;
  isPaying.value = true;
  try {
    await apiClient.patch(`/orders/${selectedUnpaidOrder.value.id}/pay/`, {
      payment_method: selectedPaymentMethod.value,
      amount_paid: selectedPaymentMethod.value === "cash" ? amountPaidModal.value || 0 : 0,
      kasir_name: kasirName.value,
    });
    toast.success("Pembayaran berhasil");
    showPaymentModal.value = false;
    selectedUnpaidOrder.value = null;
    amountPaidModal.value = 0;
    cardMode.value = { id: null, mode: null };
    fetchUnpaidOrders();
  } catch (e) {
    apiError(e, "Pembayaran gagal");
    fetchUnpaidOrders();   // mungkin order sudah dibayar/dibatalkan di tempat lain
  } finally {
    isPaying.value = false;
  }
};

// ── Drawer tagihan: ubah item & pisah bayar ──────────────────────────
const isMode = (order, mode) =>
  cardMode.value.id === order.id && cardMode.value.mode === mode;

const toggleCardMode = (order, mode) => {
  cardMode.value = isMode(order, mode) ? { id: null, mode: null } : { id: order.id, mode };
  splitQty.value = {};
  splitName.value = "";
  addMenuId.value = "";
};

const canSplit = (order) =>
  order.items.length > 1 || (order.items[0] && order.items[0].quantity > 1);

const replaceUnpaid = (updated) => {
  const i = unpaidOrders.value.findIndex((o) => o.id === updated.id);
  if (i !== -1) unpaidOrders.value[i] = updated;
};

const changeQty = async (order, item, delta) => {
  const newQty = item.quantity + delta;

  if (newQty <= 0) {
    if (order.items.length <= 1) return toast.error("Ini item terakhir di nota, tidak bisa dihapus.");
    if (!confirm(`Hapus ${item.menu_name} dari nota?`)) return;
  }

  isBusy.value = true;
  try {
    const { data } = newQty <= 0
      ? await apiClient.delete(`/orders/${order.id}/items/${item.id}/`)
      : await apiClient.patch(`/orders/${order.id}/items/${item.id}/`, { quantity: newQty });
    replaceUnpaid(data);
  } catch (e) {
    apiError(e, "Gagal mengubah item");
  } finally {
    isBusy.value = false;
  }
};

const addItemToOrder = async (order) => {
  if (!addMenuId.value) return;
  isBusy.value = true;
  try {
    const { data } = await apiClient.post(`/orders/${order.id}/items/`, {
      menu_id: addMenuId.value,
      quantity: 1,
    });
    replaceUnpaid(data);
  } catch (e) {
    apiError(e, "Gagal menambah item");
  } finally {
    isBusy.value = false;
    addMenuId.value = "";
  }
};

const stepSplit = (item, delta) => {
  const cur = splitQty.value[item.id] || 0;
  splitQty.value = {
    ...splitQty.value,
    [item.id]: Math.min(Math.max(cur + delta, 0), item.quantity),
  };
};

const splitSelectedTotal = (order) =>
  order.items.reduce((sum, i) => sum + (splitQty.value[i.id] || 0) * Number(i.price), 0);

const submitSplit = async (order) => {
  const items = Object.entries(splitQty.value)
    .filter(([, q]) => q > 0)
    .map(([id, q]) => ({ item_id: Number(id), quantity: q }));
  if (!items.length) return toast.error("Pilih dulu item yang mau dipisah");

  isBusy.value = true;
  try {
    await apiClient.post(`/orders/${order.id}/split/`, {
      items,
      customer_name: splitName.value.trim(),
      kasir_name: kasirName.value,
    });
    toast.success("Nota dipisah — sekarang bisa dibayar sendiri-sendiri");
    cardMode.value = { id: null, mode: null };
    splitQty.value = {};
    splitName.value = "";
    await fetchUnpaidOrders();
  } catch (e) {
    apiError(e, "Gagal memisah nota");
  } finally {
    isBusy.value = false;
  }
};

// ── Lifecycle ────────────────────────────────────────────────────────
// Refresh tiap drawer dibuka, supaya order web yang baru masuk ikut muncul.
watch(showUnpaidDrawer, (open) => { if (open) fetchUnpaidOrders(); });

onMounted(() => { fetchMenus(); fetchUnpaidOrders(); });
onBeforeUnmount(() => clearTimeout(debounceTimeout));
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
@media (max-width: 1024px) { .pos-root { flex-direction: column; padding: 1rem; padding-bottom: 6.5rem; } }

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
.unpaid-badge {
  display: inline-flex; align-items: center; justify-content: center;
  width: 18px; height: 18px; border-radius: 50%;
  background: #dc2626; color: #fff; font-size: 0.6rem; font-weight: 700;
}

/* ── Search bar ──────────────────────────────────────────────────── */
.search-bar { position: relative; display: flex; align-items: center; }
.search-icon { position: absolute; left: 0.9rem; color: rgba(255,255,255,0.25); pointer-events: none; }
.search-input {
  width: 100%; background: #0f0f0f; border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px; padding: 0.65rem 2.2rem 0.65rem 2.3rem;
  color: #fff; font-size: 0.82rem; font-family: 'Inter', sans-serif;
  outline: none; transition: border-color 0.15s;
}
.search-input::placeholder { color: rgba(255,255,255,0.2); }
.search-input:focus { border-color: rgba(220,38,38,0.45); }
.search-clear-btn {
  position: absolute; right: 0.75rem; width: 20px; height: 20px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(255,255,255,0.06); border: none; border-radius: 50%;
  color: rgba(255,255,255,0.4); cursor: pointer; transition: all 0.15s;
}
.search-clear-btn:hover { background: rgba(255,255,255,0.12); color: #fff; }

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

.order-panel-head {
  padding: 1.25rem 1.4rem 1rem;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  display: flex; align-items: flex-start; justify-content: space-between; gap: 0.75rem;
}
.order-panel-title {
  font-family: 'Oswald', sans-serif; font-size: 1rem; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.08em; margin: 0;
}
.order-panel-close { display: none; }

.order-section {
  padding: 1rem 1.4rem;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  display: flex; flex-direction: column; gap: 0.6rem;
}

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

/* ── Mobile cart backdrop + FAB (desktop: disembunyikan) ─────────── */
.mobile-cart-backdrop { display: none; }
.mobile-cart-fab { display: none; }

/* ── Drawer tagihan ──────────────────────────────────────────────── */
.drawer-overlay {
  position: fixed; inset: 0; z-index: 50;
  background: rgba(0,0,0,0.7); backdrop-filter: blur(3px);
}
.drawer-enter-active { transition: opacity 0.25s ease; }
.drawer-enter-from   { opacity: 0; }
.drawer-leave-active { transition: opacity 0.2s ease; }
.drawer-leave-to     { opacity: 0; }

.drawer-box {
  position: absolute; right: 0; top: 0;
  height: 100vh; height: 100dvh;            /* ikut tinggi layar yang BENAR-BENAR kelihatan */
  width: 420px; max-width: 100%;
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

.drawer-summary {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.55rem 1.25rem; font-size: 0.7rem; letter-spacing: 0.06em;
  text-transform: uppercase; color: rgba(255,255,255,0.45);
  background: rgba(220,38,38,0.06); border-bottom: 1px solid rgba(255,255,255,0.05);
}
.drawer-summary strong { font-family: monospace; font-size: 0.8rem; color: #fff; letter-spacing: 0; }

.drawer-empty {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 0.4rem; padding: 3rem;
  color: rgba(255,255,255,0.2); font-size: 0.8rem;
}

/* Area scroll: min-height:0 + flex-shrink:0 di kartu = kunci supaya bisa scroll & kartu tidak gepeng */
.drawer-list {
  flex: 1 1 0; min-height: 0;
  overflow-y: auto; overscroll-behavior: contain;
  padding: 1rem 1.25rem calc(2rem + env(safe-area-inset-bottom, 0px));
  display: flex; flex-direction: column; gap: 0.75rem;
  scrollbar-width: thin; scrollbar-color: rgba(255,255,255,0.18) transparent;
}
.drawer-list::-webkit-scrollbar { width: 6px; }
.drawer-list::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.18); border-radius: 999px; }

.drawer-order-card {
  flex-shrink: 0;
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px; padding: 1rem; display: flex; flex-direction: column; gap: 0.6rem;
}
.drawer-order-top { display: flex; justify-content: space-between; gap: 0.5rem; }
.drawer-order-num { font-family: monospace; font-weight: 700; font-size: 0.82rem; color: #fff; margin: 0 0 0.2rem; }
.drawer-order-name { font-size: 0.76rem; color: rgba(255,255,255,0.55); margin: 0 0 0.15rem; }
.drawer-order-phone { font-family: monospace; font-size: 0.68rem; color: rgba(255,255,255,0.3); margin: 0; }
.drawer-order-right { text-align: right; flex-shrink: 0; }
.drawer-order-total { font-family: monospace; font-weight: 700; color: #dc2626; font-size: 0.9rem; margin: 0 0 0.2rem; }
.drawer-order-items { font-size: 0.65rem; color: rgba(255,255,255,0.3); margin: 0; }

.drawer-items {
  list-style: none; margin: 0.25rem 0 0; padding: 0.6rem 0 0.1rem;
  border-top: 1px dashed rgba(255,255,255,0.1);
  display: flex; flex-direction: column; gap: 0.5rem;
}
.drawer-item { display: flex; align-items: center; gap: 0.6rem; font-size: 0.78rem; }
.drawer-item-info { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.drawer-item-name { color: rgba(255,255,255,0.85); }
.drawer-item-note { font-size: 0.65rem; color: rgba(255,255,255,0.35); }
.drawer-item-qty { color: rgba(255,255,255,0.45); font-family: monospace; }
.drawer-item-price { font-family: monospace; color: rgba(255,255,255,0.7); min-width: 4.5rem; text-align: right; }

.qty-stepper { display: flex; align-items: center; gap: 0.4rem; font-family: monospace; font-size: 0.75rem; }
.qty-stepper button {
  width: 1.9rem; height: 1.9rem; font-size: 0.95rem;   /* target sentuh lebih besar */
  border-radius: 0.4rem; border: 1px solid rgba(255,255,255,0.15);
  background: rgba(255,255,255,0.05); color: #fff; cursor: pointer;
}
.qty-stepper button:disabled { opacity: 0.4; cursor: not-allowed; }

.drawer-add-row { margin: 0.25rem 0; }
.drawer-split-box {
  margin: 0.25rem 0; padding: 0.75rem;
  border: 1px dashed rgba(255,255,255,0.15); border-radius: 0.6rem;
  display: flex; flex-direction: column; gap: 0.5rem;
}
.drawer-hint { font-size: 0.68rem; color: rgba(255,255,255,0.4); margin: 0; }
.drawer-split-total { display: flex; justify-content: space-between; font-size: 0.8rem; font-family: monospace; }

/* Baris aksi: [Ubah] [Pisah] [Bayar ........] */
.drawer-actions { display: flex; gap: 0.5rem; align-items: stretch; }
.drawer-ghost-btn {
  flex: 0 0 auto; padding: 0 0.85rem; min-height: 2.4rem;
  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
  border-radius: 9px; border: 1px solid rgba(255,255,255,0.15);
  background: transparent; color: rgba(255,255,255,0.7); cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.drawer-ghost-btn:hover { color: #fff; border-color: rgba(255,255,255,0.3); }
.drawer-ghost-btn.active { background: rgba(255,255,255,0.1); color: #fff; border-color: rgba(255,255,255,0.35); }

.drawer-pay-btn {
  display: flex; align-items: center; justify-content: center; gap: 0.4rem;
  width: 100%; padding: 0.6rem; border-radius: 9px; border: none;
  background: #dc2626; color: #fff;
  font-family: 'Oswald', sans-serif; font-size: 0.68rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: background 0.15s;
}
.drawer-pay-btn:hover:not(:disabled) { background: #b91c1c; }
.drawer-pay-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.drawer-actions .drawer-pay-btn { flex: 1; width: auto; min-height: 2.4rem; padding: 0 0.75rem; }

/* ── Modal pembayaran ────────────────────────────────────────────── */
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
  max-height: 90vh; max-height: 90dvh; overflow-y: auto;
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

.modal-customer { padding: 0.85rem 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.04); }
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

/* Sembunyikan spinner input number */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
input[type="number"] { -moz-appearance: textfield; }

/* ── MOBILE OVERRIDES ────────────────────────────────────────────── */
@media (max-width: 1024px) {
  .order-panel {
    position: fixed;
    left: 0; right: 0; bottom: 0; top: auto;
    width: 100%;
    max-height: 88vh;
    border-radius: 20px 20px 0 0;
    transform: translateY(105%);
    transition: transform 0.3s cubic-bezier(0.32, 0.72, 0, 1);
    z-index: 60;
    box-shadow: 0 -12px 40px rgba(0,0,0,0.55);
  }
  .order-panel.mobile-cart-open { transform: translateY(0); }

  .order-panel-close {
    display: flex; align-items: center; justify-content: center;
    width: 28px; height: 28px; border-radius: 8px; flex-shrink: 0;
    background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1);
    color: rgba(255,255,255,0.5); cursor: pointer;
  }

  .mobile-cart-backdrop {
    display: block; position: fixed; inset: 0;
    background: rgba(0,0,0,0.6); backdrop-filter: blur(2px); z-index: 55;
  }

  .mobile-cart-fab {
    display: flex; align-items: center; gap: 0.65rem;
    position: fixed; left: 1rem; right: 1rem; bottom: 1rem;
    z-index: 55; padding: 0.85rem 1.1rem;
    background: #dc2626; border: none; border-radius: 14px;
    box-shadow: 0 8px 28px rgba(220,38,38,0.4);
    cursor: pointer; color: #fff;
  }
  .mcf-count {
    width: 22px; height: 22px; border-radius: 50%; flex-shrink: 0;
    background: rgba(255,255,255,0.2); display: flex; align-items: center;
    justify-content: center; font-size: 0.7rem; font-weight: 800;
  }
  .mcf-label {
    flex: 1; text-align: left; font-family: 'Oswald', sans-serif;
    font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase;
  }
  .mcf-total { font-family: monospace; font-weight: 800; font-size: 0.85rem; }
}

@media (max-width: 480px) {
  .drawer-box { width: 100%; border-left: none; }
}
</style>