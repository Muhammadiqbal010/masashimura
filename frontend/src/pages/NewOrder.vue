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
        <div class="header-actions">

          <!-- Waktu order: default "Sekarang"; "Atur Manual" buat input susulan hari/jam lain. -->
          <div class="time-chip-wrap">
            <button
              type="button"
              class="time-chip"
              :class="{ 'is-manual': useCustomTime, 'is-warn': useCustomTime && !!customTimeError }"
              :aria-expanded="showTimePop"
              title="Waktu order"
              @click="showTimePop = !showTimePop"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              <span>{{ timeChipText }}</span>
            </button>

            <div v-if="showTimePop" class="time-pop-backdrop" @click="showTimePop = false"></div>
            <div v-if="showTimePop" class="time-pop" role="dialog" aria-label="Waktu order">
              <p class="time-pop-title">Waktu Order</p>
              <div class="toggle-grid">
                <button
                  type="button"
                  @click="setNowMode"
                  class="toggle-btn"
                  :class="!useCustomTime ? 'toggle-active-white' : 'toggle-inactive'"
                >
                  Sekarang
                </button>
                <button
                  type="button"
                  @click="enableCustomTime"
                  class="toggle-btn"
                  :class="useCustomTime ? 'toggle-active-amber' : 'toggle-inactive'"
                >
                  Atur Manual
                </button>
              </div>

              <div v-if="useCustomTime" class="time-box">
                <div class="time-fields">
                  <input v-model="orderDate" type="date" :max="wibToday()" class="pos-input" aria-label="Tanggal order" />
                  <input v-model="orderTime" type="time" class="pos-input" aria-label="Jam order" />
                </div>
                <p v-if="customTimeError" class="time-error">{{ customTimeError }}</p>
                <p v-else class="time-note">
                  Order dicatat pada <strong>{{ customTimeLabel }}</strong> dan masuk ke laporan hari itu.
                  Mode ini <strong>tetap aktif</strong> (juga setelah pindah halaman/refresh) sampai kamu pilih “Sekarang”.
                </p>
              </div>
              <p v-else class="time-note">Order dicatat saat itu juga.</p>

              <button type="button" class="time-pop-done" @click="showTimePop = false">Selesai</button>
            </div>
          </div>

          <button @click="showUnpaidDrawer = true" class="unpaid-trigger">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            <span>Tagihan</span>
            <span v-if="unpaidOrders.length" class="unpaid-badge">{{ unpaidOrders.length }}</span>
          </button>
        </div>
      </div>

      <!-- Banner mode tambah ke tagihan -->
      <div v-if="addTarget" class="add-banner">
        <div class="add-banner-info">
          <p class="add-banner-eyebrow">Menambah ke tagihan</p>
          <p class="add-banner-title">
            {{ addTarget.order_number }}
            <span>· {{ addTarget.customer_name || 'Walk In' }}</span>
          </p>
        </div>
        <div class="add-banner-right">
          <p class="add-banner-total">{{ formatPrice(addTarget.total_price) }}</p>
          <button class="add-banner-done" @click="finishAddToOrder">Selesai</button>
        </div>
      </div>

      <!-- Search bar -->
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
          @click="onMenuClick(menu)"
        >
          <div v-if="!menu.is_available" class="menu-habis-overlay">
            <span class="habis-badge">Habis</span>
          </div>

          <!-- Badge jumlah: hijau = baru ditambah ke tagihan, merah = ada di keranjang -->
          <span v-if="addTarget && addedCounts[menu.id]" class="menu-count-badge menu-count-added">+{{ addedCounts[menu.id] }}</span>
          <span v-else-if="!addTarget && cartCounts[menu.id]" class="menu-count-badge">×{{ cartCounts[menu.id] }}</span>

          <div class="menu-card-body">
            <div v-if="menu.is_secret || menu.options?.length" class="menu-tags">
              <span v-if="menu.is_secret" class="menu-tag menu-tag-secret" title="Secret menu: tidak tampil di web">SECRET</span>
              <span v-if="menu.options?.length" class="menu-tag menu-tag-opt" title="Punya opsi pilihan">OPSI</span>
            </div>
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
          <h2 class="order-panel-title">
            Ringkasan Pesanan
            <span v-if="cartItemCount" class="order-panel-count">{{ cartItemCount }}</span>
          </h2>
        </div>
        <button class="order-panel-close" @click="showMobileCart = false" aria-label="Tutup keranjang">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </button>
      </div>

      <!-- Area scroll: semua isi form. Total + tombol submit ada di footer yang selalu kelihatan. -->
      <div class="order-panel-body">

        <!-- Cart -->
        <div class="order-section">
          <div v-if="orderItems.length === 0" class="cart-empty">
            <div class="cart-empty-icon">🛒</div>
            <p>Keranjang masih kosong</p>
            <p class="cart-empty-hint">Tap menu di kiri untuk menambah item</p>
          </div>

          <template v-else>
            <div class="cart-head">
              <span class="field-label">Item Pesanan</span>
              <button type="button" class="cart-clear" @click="clearCart">Kosongkan</button>
            </div>
            <div class="cart-list">
              <div v-for="(item, index) in orderItems" :key="index" class="cart-item">
                <div class="cart-item-top">
                  <div class="cart-item-info">
                    <p class="cart-item-name">{{ item.name }}</p>
                    <p class="cart-item-price">{{ formatPrice(item.price) }} <span class="cart-item-sub">· {{ formatPrice(Number(item.price) * item.quantity) }}</span></p>
                    <p v-if="item.optionDetails?.length" class="cart-item-opts">
                      {{ item.optionDetails.map((o) => o.label).join(' · ') }}
                    </p>
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
                  placeholder="Catatan koki: Tanpa Bawang..."
                  class="cart-notes-input"
                />
              </div>
            </div>
          </template>
        </div>

        <!-- Customer info -->
        <div class="order-section">
          <div class="field">
            <label class="field-label">Nomor HP Pelanggan <span class="field-optional">(Opsional)</span></label>
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
          <p v-if="paymentMethod === 'qris_manual'" class="field-hint">QRIS Manual hanya untuk bayar sekarang.</p>
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
          <div v-if="quickCash.length" class="quick-cash">
            <button
              v-for="v in quickCash"
              :key="v"
              type="button"
              class="quick-cash-btn"
              :class="{ 'is-active': amountPaid === v }"
              @click="amountPaid = v"
            >{{ v === totalPrice ? 'Uang Pas' : formatPrice(v) }}</button>
          </div>
          <div v-if="amountPaid > 0 && amountPaid >= totalPrice" class="change-box change-ok">
            <span>Kembalian</span>
            <span>{{ formatPrice(changeDue) }}</span>
          </div>
          <div v-else-if="amountPaid > 0 && amountPaid < totalPrice" class="change-box change-err">
            <span>Kurang</span>
            <span>{{ formatPrice(totalPrice - amountPaid) }}</span>
          </div>
        </div>

        <!-- Promo + poin -->
        <div class="order-section">
          <div class="price-row">
            <span>Subtotal</span>
            <span>{{ formatPrice(subtotal) }}</span>
          </div>

          <!-- Tema kotak promo dipaksa lewat :deep() di bawah -->
          <div class="promo-slot">
            <PromoCodeBox
              ref="promoBoxRef"
              :subtotal="subtotal"
              @applied="onPromoApplied"
              @removed="onPromoRemoved"
            />
          </div>

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
        </div>

        <!-- Kasir -->
        <div class="kasir-strip">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          Kasir: <span class="kasir-name">{{ kasirName }}</span>
        </div>
      </div>

      <!-- Footer tetap: total + submit selalu kelihatan tanpa scroll -->
      <div class="order-panel-foot">
        <div class="price-total">
          <span>Total Akhir</span>
          <span class="total-val">{{ formatPrice(totalPrice) }}</span>
        </div>
        <button
          @click="submitOrder"
          :disabled="isSubmitting || orderItems.length === 0 || cashShort"
          class="submit-btn"
        >
          <span v-if="isSubmitting" class="btn-spinner"></span>
          <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
          {{ submitLabel }}
        </button>
      </div>
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

            <!-- Tambah menu (mode ubah) → lompat ke katalog POS -->
            <div v-if="isMode(order, 'edit')" class="drawer-add-row">
              <button class="drawer-add-btn" @click="startAddToOrder(order)">
                + Tambah menu dari katalog
              </button>
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

  <!-- ── MODAL PILIH OPSI MENU ─────────────────────────────────────── -->
  <transition
    enter-active-class="modal-enter-active" enter-from-class="modal-enter-from"
    leave-active-class="modal-leave-active" leave-to-class="modal-leave-to"
  >
    <div v-if="pickerMenu" class="modal-overlay" @click.self="closePicker">
      <div class="modal-box" role="dialog" aria-modal="true" :aria-label="`Pilih opsi ${pickerMenu.name}`">
        <div class="modal-head">
          <div>
            <p class="pos-eyebrow">Pilih Opsi</p>
            <h2 class="modal-title">{{ pickerMenu.name }}</h2>
            <p class="modal-ordnum">{{ formatPrice(pickerMenu.price) }}</p>
          </div>
          <button class="modal-close-btn" @click="closePicker" aria-label="Tutup">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>

        <div class="modal-section opt-groups">
          <div v-for="group in pickerMenu.options" :key="group.name" class="opt-group">
            <label class="field-label">
              {{ group.name }}
              <span class="opt-group-hint">
                {{ group.required ? 'wajib' : 'opsional' }} · {{ group.multiple ? 'boleh banyak' : 'pilih satu' }}
              </span>
            </label>
            <div class="opt-choices">
              <button
                v-for="choice in group.choices"
                :key="choice.label"
                type="button"
                class="toggle-btn opt-choice"
                :class="isPicked(group, choice) ? 'toggle-active-red' : 'toggle-inactive'"
                :role="group.multiple ? 'checkbox' : 'radio'"
                :aria-checked="isPicked(group, choice)"
                @click="togglePick(group, choice)"
              >
                <span>{{ choice.label }}</span>
                <span v-if="Number(choice.price) > 0" class="opt-choice-price">+{{ formatPrice(choice.price) }}</span>
              </button>
            </div>
          </div>
        </div>

        <div class="modal-section opt-footer">
          <p v-if="pickerMissing" class="opt-missing">Pilih "{{ pickerMissing }}" dulu.</p>
          <div class="opt-footer-row">
            <div class="qty-control">
              <button class="qty-btn" :disabled="pickerQty <= 1" @click="pickerQty--" aria-label="Kurangi">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="5" y1="12" x2="19" y2="12"/></svg>
              </button>
              <span class="qty-val">{{ pickerQty }}</span>
              <button class="qty-btn" :disabled="pickerQty >= 99" @click="pickerQty++" aria-label="Tambah">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              </button>
            </div>
            <button class="toggle-btn toggle-active-red opt-confirm" :disabled="!!pickerMissing || isBusy" @click="confirmPicker">
              {{ addTarget ? 'Tambah ke Tagihan' : 'Tambah' }} · {{ formatPrice(pickerTotal) }}
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
          <div v-if="quickCashModal.length" class="quick-cash">
            <button
              v-for="v in quickCashModal"
              :key="v"
              type="button"
              class="quick-cash-btn"
              :class="{ 'is-active': amountPaidModal === v }"
              @click="amountPaidModal = v"
            >{{ v === modalTotal ? 'Uang Pas' : formatPrice(v) }}</button>
          </div>
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
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue";
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

// ── State: picker opsi menu (pedas, add-on, dll) ─────────────────────
const pickerMenu      = ref(null);
const pickerSelection = ref({});   // { "Level Pedas": ["Pedas"], "Tambahan": ["Extra keju"] }
const pickerQty       = ref(1);

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

// ── State: waktu order manual (input susulan) ────────────────────────
// Dihitung dalam WIB (UTC+7) tanpa bergantung zona waktu perangkat; nilai
// dikirim ke server lengkap dengan offset +07:00.
const WIB_OFFSET_MS = 7 * 60 * 60 * 1000;
const wibParts = (ms = Date.now()) => {
  const iso = new Date(ms + WIB_OFFSET_MS).toISOString();
  return { date: iso.slice(0, 10), time: iso.slice(11, 16) };
};
const wibToday = () => wibParts().date;

// Pilihan "Atur Manual" + tanggalnya DISIMPAN di browser ini, jadi tetap aktif
// waktu pindah halaman / refresh — sampai admin sendiri memilih "Sekarang".
// Jam sengaja TIDAK disimpan: tiap order susulan jamnya harus diisi lagi.
const CUSTOM_TIME_KEY   = "masashimura.pos.customTime";
const BACKDATE_MAX_DAYS = 366;   // samakan dengan batas di backend
const loadSavedTimeMode = () => {
  try {
    const saved = JSON.parse(localStorage.getItem(CUSTOM_TIME_KEY) || "null");
    if (!saved?.on || !/^\d{4}-\d{2}-\d{2}$/.test(saved.date || "")) return null;
    const oldest = wibParts(Date.now() - BACKDATE_MAX_DAYS * 86400000).date;
    if (saved.date > wibToday() || saved.date < oldest) return null;   // tidak masuk akal -> abaikan
    return saved.date;
  } catch { return null; }
};
const savedDate     = loadSavedTimeMode();
const useCustomTime = ref(!!savedDate);
const orderDate     = ref(savedDate || "");   // YYYY-MM-DD
const orderTime     = ref("");                // HH:mm
const showTimePop   = ref(false);

watch([useCustomTime, orderDate], () => {
  try {
    if (useCustomTime.value && orderDate.value) {
      localStorage.setItem(CUSTOM_TIME_KEY, JSON.stringify({ on: true, date: orderDate.value }));
    } else {
      localStorage.removeItem(CUSTOM_TIME_KEY);
    }
  } catch { /* localStorage tidak tersedia (mis. mode privat) — fitur tetap jalan tanpa penyimpanan */ }
});

const timeChipText = computed(() => {
  if (!useCustomTime.value) return "Sekarang";
  const day = orderDate.value
    ? new Date(`${orderDate.value}T12:00:00+07:00`).toLocaleDateString("id-ID", {
        day: "numeric", month: "short", year: "numeric", timeZone: "Asia/Jakarta",
      })
    : "—";
  return `${day} · ${orderTime.value || "isi jam"}`;
});

const customCreatedAtValue = () => `${orderDate.value}T${orderTime.value}:00+07:00`;

const getCustomTimeError = () => {
  if (!useCustomTime.value) return "";
  if (!orderDate.value || !orderTime.value) {
    return "Isi tanggal dan jam order dulu, atau pilih “Sekarang”.";
  }
  const picked = new Date(customCreatedAtValue());
  if (Number.isNaN(picked.getTime())) return "Tanggal/jam order tidak valid.";
  if (picked.getTime() > Date.now() + 60_000) return "Waktu order tidak boleh di masa depan.";
  return "";
};
const customTimeError = computed(() => getCustomTimeError());

const customTimeLabel = computed(() => {
  const picked = new Date(customCreatedAtValue());
  if (Number.isNaN(picked.getTime())) return "—";
  const day = picked.toLocaleDateString("id-ID", {
    weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "Asia/Jakarta",
  });
  return `${day} · ${orderTime.value} WIB`;
});

const enableCustomTime = () => {
  const now = wibParts();
  if (!orderDate.value) orderDate.value = now.date;
  if (!orderTime.value) orderTime.value = now.time;
  useCustomTime.value = true;
};
const setNowMode = () => { useCustomTime.value = false; };

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
const splitQty  = ref({});   // { [itemId]: jumlah yang dipindah ke nota baru }
const splitName = ref("");

// ── State: mode "tambah menu ke tagihan" (pakai katalog POS) ─────────
const addTarget   = ref(null);   // order tujuan (objek order terbaru dari server)
const addedCounts = ref({});     // { [menuId]: jumlah yang ditambah di sesi ini }

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

// Jumlah per menu di keranjang (untuk badge di kartu menu)
const cartCounts = computed(() => {
  const out = {};
  for (const i of orderItems.value) out[i.id] = (out[i.id] || 0) + i.quantity;
  return out;
});

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
const cashShort = computed(() =>
  isCashNow.value && amountPaid.value > 0 && amountPaid.value < totalPrice.value
);

// Tombol nominal cepat: uang pas + pembulatan ke atas (5rb, 10rb, 20rb, 50rb, 100rb)
const buildQuickCash = (total) => {
  if (!total || total <= 0) return [];
  const opts = new Set([total]);
  for (const step of [5000, 10000, 20000, 50000, 100000]) opts.add(Math.ceil(total / step) * step);
  return [...opts].filter((v) => v >= total).sort((a, b) => a - b).slice(0, 4);
};
const quickCash = computed(() => buildQuickCash(totalPrice.value));

const submitLabel = computed(() => {
  if (isSubmitting.value) return "Memproses...";
  if (useCustomTime.value) return "Simpan Pesanan Susulan";
  if (orderType.value === "dine_in_later") return "Simpan ke Tagihan";
  return "Eksekusi Pesanan";
});

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

const modalTotal = computed(() => Number(selectedUnpaidOrder.value?.total_price || 0));
const quickCashModal = computed(() => buildQuickCash(modalTotal.value));
const modalUnderpaid = computed(() =>
  selectedPaymentMethod.value === "cash" && amountPaidModal.value > 0 && amountPaidModal.value < modalTotal.value
);

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
// Pilihan opsi: buang grup kosong + urutkan, supaya pilihan yang sama = tanda yang sama.
// Perhitungan harga di sini hanya tampilan; server memvalidasi ulang & menghitung sendiri.
const normalizeSelection = (selection) => {
  const out = {};
  for (const key of Object.keys(selection || {}).sort()) {
    const picks = (Array.isArray(selection[key]) ? selection[key] : []).filter(Boolean);
    if (picks.length) out[key] = [...picks].sort();
  }
  return out;
};

const describeSelection = (menu, selection) => {
  const details = [];
  for (const group of menu.options || []) {
    for (const label of selection[group.name] || []) {
      const choice = (group.choices || []).find((c) => c.label === label);
      if (choice) details.push({ group: group.name, label: choice.label, price: Number(choice.price) || 0 });
    }
  }
  return details;
};

const addToOrder = (menu, selection = {}, quantity = 1) => {
  if (!menu.is_available) { toast.error("Menu ini sedang habis!"); return; }
  const chosen    = normalizeSelection(selection);
  const signature = JSON.stringify(chosen);

  // Menu sama + pilihan sama + catatan masih kosong → jumlahnya ditambah
  const existing = orderItems.value.find(
    (i) => i.id === menu.id && (i.optionSignature ?? "{}") === signature && i.notes === ""
  );
  if (existing) { existing.quantity += quantity; return; }

  const optionDetails = describeSelection(menu, chosen);
  const extra = optionDetails.reduce((sum, d) => sum + d.price, 0);
  orderItems.value.push({
    ...menu,
    quantity,
    notes: "",
    options: chosen,
    optionSignature: signature,
    optionDetails,
    price: Number(menu.price) + extra,   // harga satuan termasuk add-on
  });
};

const clearCart = () => {
  if (!orderItems.value.length) return;
  if (!confirm("Kosongkan semua item di keranjang?")) return;
  orderItems.value = [];
  selectedRewardIds.value = [];
  amountPaid.value = 0;
  promoBoxRef.value?.removePromo?.();
};

// ── Picker opsi ──────────────────────────────────────────────────────
const openPicker = (menu) => {
  pickerMenu.value = menu;
  pickerSelection.value = {};
  pickerQty.value = 1;
};
const closePicker = () => { pickerMenu.value = null; };

const isPicked = (group, choice) => (pickerSelection.value[group.name] || []).includes(choice.label);

const togglePick = (group, choice) => {
  const current = pickerSelection.value[group.name] || [];
  let next;
  if (group.multiple) {
    next = current.includes(choice.label) ? current.filter((l) => l !== choice.label) : [...current, choice.label];
  } else if (current[0] === choice.label) {
    next = group.required ? current : [];   // opsi wajib tetap terpilih
  } else {
    next = [choice.label];
  }
  pickerSelection.value = { ...pickerSelection.value, [group.name]: next };
};

const pickerMissing = computed(
  () => (pickerMenu.value?.options || []).find((g) => g.required && !(pickerSelection.value[g.name] || []).length)?.name || null
);

const pickerTotal = computed(() => {
  const menu = pickerMenu.value;
  if (!menu) return 0;
  const extra = describeSelection(menu, pickerSelection.value).reduce((sum, d) => sum + d.price, 0);
  return (Number(menu.price) + extra) * pickerQty.value;
});

const confirmPicker = async () => {
  const menu = pickerMenu.value;
  if (!menu || pickerMissing.value) return;
  const selection = normalizeSelection(pickerSelection.value);

  if (addTarget.value) {
    // Mode "tambah ke tagihan": kirim langsung ke order yang sedang dibuka
    if (await addMenuToTargetOrder(menu, selection, pickerQty.value)) closePicker();
    return;
  }
  addToOrder(menu, selection, pickerQty.value);
  closePicker();
};

// Dipanggil saat input catatan selesai diedit (@change), bukan tiap ketikan,
// supaya item tidak ke-merge di tengah mengetik.
const handleNotesChange = (index) => {
  const cur = orderItems.value[index];
  if (!cur) return;
  const norm = (s) => (s || "").trim().toLowerCase();
  const dup = orderItems.value.findIndex(
    (item, idx) =>
      idx !== index &&
      item.id === cur.id &&
      (item.optionSignature ?? "{}") === (cur.optionSignature ?? "{}") &&
      norm(item.notes) === norm(cur.notes)
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
  promoBoxRef.value?.removePromo?.();
  showMobileCart.value = false;
};

const submitOrder = async () => {
  if (orderItems.value.length === 0) return toast.error("Keranjang kosong!");
  if (isCashNow.value && amountPaid.value > 0 && amountPaid.value < totalPrice.value) {
    return toast.error("Uang diterima kurang dari total tagihan");
  }

  if (useCustomTime.value) {
    const timeErr = getCustomTimeError();
    if (timeErr) { showTimePop.value = true; return toast.error(timeErr); }
  }

  isSubmitting.value = true;

  // Harga, diskon promo, dan status dihitung ulang di server — client hanya kirim niat.
  const payload = {
    source: "pos",
    ...(useCustomTime.value ? { created_at: customCreatedAtValue() } : {}),
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
      options: item.options || {},   // server memvalidasi & menghitung harga add-on sendiri
    })),
  };

  try {
    const res = await apiClient.post("/orders/", payload);
    const no = res.data?.order_number;
    toast.success(
      useCustomTime.value
        ? `Pesanan${no ? ` ${no}` : ""} dicatat untuk ${customTimeLabel.value}`
        : `Pesanan${no ? ` ${no}` : ""} berhasil masuk ke sistem!`
    );
    // Input susulan sering beruntun di hari yang sama: tanggal dipertahankan,
    // tapi jam dikosongkan supaya order berikutnya tidak ikut jam lama tanpa sengaja.
    if (useCustomTime.value) orderTime.value = "";
    resetForm();
    fetchUnpaidOrders();
    // Struk dibagikan dari halaman Active Orders (tidak ada unduhan otomatis di sini).
  } catch (e) {
    console.error(e);
    apiError(e, "Gagal menyimpan transaksi ke server.");
  } finally {
    isSubmitting.value = false;
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

// ── Mode "tambah menu ke tagihan" (pakai katalog POS) ────────────────
const startAddToOrder = (order) => {
  addTarget.value = order;
  addedCounts.value = {};
  cardMode.value = { id: null, mode: null };
  showUnpaidDrawer.value = false;
};

// Drawer dibuka lagi → watcher showUnpaidDrawer otomatis fetch ulang dari server
const finishAddToOrder = () => {
  addTarget.value = null;
  addedCounts.value = {};
  showUnpaidDrawer.value = true;
};

const onMenuClick = async (menu) => {
  // Menu beropsi: kasir pilih opsi dulu (berlaku untuk keranjang baru maupun tambah ke tagihan)
  if (menu.options?.length) return openPicker(menu);

  // Bukan mode tambah ke tagihan → perilaku lama (masuk keranjang)
  if (!addTarget.value) return addToOrder(menu);

  await addMenuToTargetOrder(menu, {}, 1);
};

// Tambah menu ke tagihan yang sedang dibuka. Return true kalau berhasil.
const addMenuToTargetOrder = async (menu, selection, quantity) => {
  // Guard: abaikan tap selagi request sebelumnya masih jalan (cegah double-add & angka banner loncat)
  if (isBusy.value) return false;
  isBusy.value = true;

  try {
    const { data } = await apiClient.post(`/orders/${addTarget.value.id}/items/`, {
      menu_id: menu.id,
      quantity,
      options: selection,
    });
    addTarget.value = data;
    replaceUnpaid(data);
    addedCounts.value = {
      ...addedCounts.value,
      [menu.id]: (addedCounts.value[menu.id] || 0) + quantity,
    };
    return true;
  } catch (e) {
    apiError(e, "Gagal menambah item");
    // Tagihan sudah keburu lunas/dibatalkan → keluar dari mode ini (drawer fetch ulang sendiri).
    // Kesalahan pilihan opsi tidak ikut: kasir tetap di mode ini dan bisa memperbaiki pilihannya.
    const msg = e.response?.data?.detail || e.response?.data?.error || "";
    if (e.response?.status === 400 && !/opsi|pilih|dobel/i.test(msg)) {
      closePicker();
      finishAddToOrder();
    }
    return false;
  } finally {
    isBusy.value = false;
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

// Metode/alur berubah → nominal uang diterima lama tidak relevan lagi
watch(isCashNow, (v) => { if (!v) amountPaid.value = 0; });

onMounted(() => { fetchMenus(); fetchUnpaidOrders(); });
onBeforeUnmount(() => clearTimeout(debounceTimeout));
</script>

<style scoped>
/* ── Root layout ─────────────────────────────────────────────────── */
.pos-root {
  display: flex;
  gap: 1.25rem;
  min-height: 100vh; min-height: 100dvh;
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', sans-serif;
  padding: 1.5rem;
  align-items: flex-start;
}
@media (max-width: 1024px) { .pos-root { flex-direction: column; padding: 1rem; padding-bottom: 6.5rem; } }

button:focus-visible, input:focus-visible { outline: 2px solid color-mix(in srgb, var(--accent) 60%, transparent); outline-offset: 2px; }

/* ── Shared tokens ───────────────────────────────────────────────── */
.pos-eyebrow {
  font-family: 'Oswald', sans-serif; font-size: 0.58rem;
  letter-spacing: 0.2em; text-transform: uppercase; color: var(--accent-text);
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
  border-bottom: 1px solid rgb(var(--ink) / 0.06);
}
.pos-title {
  font-family: 'Oswald', sans-serif; font-size: 1.6rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.04em; margin: 0 0 0.2rem;
  color: var(--text);
}
.pos-date { font-size: 0.68rem; color: var(--text-faint); margin: 0; }

.unpaid-trigger {
  display: flex; align-items: center; gap: 0.45rem;
  padding: 0.55rem 1rem;
  background: var(--surface); border: 1px solid rgb(var(--ink) / 0.08);
  border-radius: 10px; color: var(--text-dim);
  font-family: 'Oswald', sans-serif; font-size: 0.68rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: all 0.15s; position: relative;
  white-space: nowrap;
}
.unpaid-trigger:hover { border-color: rgb(var(--ink) / 0.18); color: var(--text); }

/* ── Waktu order (chip di samping Tagihan + popover) ──────────────── */
.header-actions { display: flex; align-items: flex-start; gap: 0.6rem; flex-wrap: wrap; }
.time-chip-wrap { position: relative; }
.time-chip {
  display: flex; align-items: center; gap: 0.45rem;
  padding: 0.55rem 1rem;
  background: var(--surface); border: 1px solid rgb(var(--ink) / 0.08);
  border-radius: 10px; color: var(--text-dim);
  font-family: 'Oswald', sans-serif; font-size: 0.68rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: all 0.15s; white-space: nowrap;
}
.time-chip:hover { border-color: rgb(var(--ink) / 0.18); color: var(--text); }
.time-chip.is-manual { color: var(--amber-soft); border-color: color-mix(in srgb, var(--amber) 45%, transparent); background: color-mix(in srgb, var(--amber) 7%, transparent); }
.time-chip.is-warn   { color: var(--red-soft); border-color: color-mix(in srgb, var(--accent) 60%, transparent); background: color-mix(in srgb, var(--accent) 7%, transparent); }
.time-pop-backdrop { position: fixed; inset: 0; z-index: 40; }
.time-pop {
  position: absolute; top: calc(100% + 8px); right: 0; z-index: 41;
  width: min(330px, calc(100vw - 2rem)); padding: 0.9rem;
  display: flex; flex-direction: column; gap: 0.65rem;
  background: var(--surface); border: 1px solid rgb(var(--ink) / 0.1); border-radius: 12px;
  box-shadow: var(--shadow-lg);
}
.time-pop-title {
  margin: 0; font-size: 0.62rem; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--text-faint);
}
.time-pop .time-box { margin-top: 0; }
.time-pop-done {
  padding: 0.45rem; border-radius: 8px; cursor: pointer;
  background: rgb(var(--ink) / 0.05); border: 1px solid rgb(var(--ink) / 0.08);
  color: var(--text-2); font-size: 0.7rem; transition: all 0.15s;
}
.time-pop-done:hover { color: var(--text); background: rgb(var(--ink) / 0.09); }
@media (max-width: 640px) {
  .time-pop { left: 0; right: auto; }
}
.unpaid-badge {
  display: inline-flex; align-items: center; justify-content: center;
  width: 18px; height: 18px; border-radius: 50%;
  background: #dc2626; color: #fff; font-size: 0.6rem; font-weight: 700;
}

/* ── Banner mode tambah ke tagihan ───────────────────────────────── */
.add-banner {
  position: sticky; top: 0; z-index: 5;
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
  padding: 0.75rem 1rem;
  background: color-mix(in srgb, var(--green) 12%, var(--bg)); border: 1px solid color-mix(in srgb, var(--green) 40%, transparent);
  border-radius: 12px; backdrop-filter: blur(6px);
}
.add-banner-eyebrow { margin: 0 0 0.15rem; font-size: 0.6rem; letter-spacing: 0.14em; text-transform: uppercase; color: var(--green-soft); }
.add-banner-title { margin: 0; font-family: monospace; font-weight: 700; font-size: 0.85rem; color: var(--text); }
.add-banner-title span { font-family: inherit; font-weight: 400; color: var(--text-dim); }
.add-banner-right { display: flex; align-items: center; gap: 0.75rem; flex-shrink: 0; }
.add-banner-total { margin: 0; font-family: monospace; font-weight: 700; font-size: 0.95rem; color: var(--text); }
.add-banner-done {
  padding: 0.5rem 0.9rem; border: none; border-radius: 9px; cursor: pointer;
  background: #16a34a; color: #fff; font-size: 0.7rem; font-weight: 700;
  letter-spacing: 0.08em; text-transform: uppercase;
}
.add-banner-done:hover { background: #15803d; }

/* ── Search bar ──────────────────────────────────────────────────── */
.search-bar { position: relative; display: flex; align-items: center; }
.search-icon { position: absolute; left: 0.9rem; color: var(--text-faint); pointer-events: none; }
.search-input {
  width: 100%; background: var(--surface); border: 1px solid rgb(var(--ink) / 0.08);
  border-radius: 10px; padding: 0.65rem 2.2rem 0.65rem 2.3rem;
  color: var(--text); font-size: 0.82rem; font-family: 'Inter', sans-serif;
  outline: none; transition: border-color 0.15s;
}
.search-input::placeholder { color: var(--text-faint); }
.search-input:focus { border-color: color-mix(in srgb, var(--accent) 45%, transparent); }
.search-clear-btn {
  position: absolute; right: 0.75rem; width: 20px; height: 20px;
  display: flex; align-items: center; justify-content: center;
  background: rgb(var(--ink) / 0.06); border: none; border-radius: 50%;
  color: var(--text-dim); cursor: pointer; transition: all 0.15s;
}
.search-clear-btn:hover { background: rgb(var(--ink) / 0.12); color: var(--text); }

/* ── Menu grid ───────────────────────────────────────────────────── */
.menu-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.75rem;
}
@media (max-width: 640px) { .menu-grid { grid-template-columns: repeat(2, 1fr); } }

.menu-skeleton {
  background: var(--surface); border: 1px solid rgb(var(--ink) / 0.04);
  border-radius: 12px; min-height: 110px;
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.5; } }

.menu-error, .menu-empty {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 0.6rem; padding: 3rem 2rem;
  background: var(--surface); border: 1px solid rgb(var(--ink) / 0.05);
  border-radius: 14px; text-align: center;
  color: var(--text-faint); font-size: 0.8rem;
}
.empty-icon { font-size: 1.75rem; margin-bottom: 0.25rem; }
.empty-text { color: var(--text-faint); margin: 0; font-size: 0.85rem; }
.empty-hint { color: var(--text-faint); margin: 0; font-size: 0.7rem; }
.retry-btn {
  padding: 0.5rem 1.25rem; border-radius: 8px;
  background: #dc2626; border: none; color: #fff;
  font-family: 'Oswald', sans-serif; font-size: 0.68rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: background 0.15s;
}
.retry-btn:hover { background: #b91c1c; }

.menu-card {
  position: relative; background: var(--surface);
  border: 1px solid rgb(var(--ink) / 0.05);
  border-radius: 12px; padding: 0.9rem 1rem;
  display: flex; flex-direction: column; justify-content: space-between;
  min-height: 118px; cursor: pointer; text-align: left;
  transition: border-color 0.15s, background 0.15s, transform 0.08s;
  overflow: hidden;
}
.menu-card-avail:hover { border-color: color-mix(in srgb, var(--accent) 50%, transparent); background: color-mix(in srgb, var(--accent) 4%, var(--surface)); }
.menu-card-avail:hover .menu-add-indicator { opacity: 1; }
.menu-card-avail:active { transform: scale(0.98); }
.menu-card-unavail { opacity: 0.45; cursor: not-allowed; filter: grayscale(0.7); }

/* Badge jumlah di kartu menu */
.menu-count-badge {
  position: absolute; top: 0.5rem; right: 0.5rem; z-index: 2;
  min-width: 1.6rem; padding: 0.1rem 0.4rem; text-align: center;
  background: #dc2626; color: #fff; border-radius: 999px;
  font-family: monospace; font-size: 0.72rem; font-weight: 700;
}
.menu-count-added { background: #16a34a; }

.menu-habis-overlay {
  position: absolute; inset: 0; z-index: 10;
  background: rgba(0,0,0,0.65); border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
}
.habis-badge {
  font-family: 'Oswald', sans-serif; font-size: 0.62rem; font-weight: 600;
  letter-spacing: 0.15em; text-transform: uppercase;
  color: var(--red-soft); border: 1px solid color-mix(in srgb, var(--accent) 40%, transparent);
  padding: 0.2rem 0.65rem; border-radius: 100px;
}
/* Tag sekarang di dalam alur kartu (bukan absolute) supaya tidak menimpa nama menu */
.menu-tags { display: flex; gap: 0.25rem; margin-bottom: 0.4rem; }
.menu-tag {
  font-family: monospace; font-size: 0.56rem; font-weight: 700; letter-spacing: 0.1em;
  padding: 0.1rem 0.35rem; border-radius: 4px; line-height: 1.3;
}
.menu-tag-secret { background: #7c3aed; color: #fff; }
.menu-tag-opt { background: rgb(var(--ink) / 0.1); color: var(--text-2); }
.menu-card-body { flex: 1; }
.menu-name { font-weight: 600; font-size: 0.82rem; color: var(--text-2); margin: 0 0 0.35rem; line-height: 1.3; }
.menu-price { font-family: monospace; font-size: 0.78rem; font-weight: 700; color: var(--accent-text); margin: 0; }
.menu-add-indicator {
  display: flex; align-items: center; justify-content: center;
  width: 22px; height: 22px; border-radius: 6px;
  background: color-mix(in srgb, var(--accent) 10%, transparent); border: 1px solid color-mix(in srgb, var(--accent) 20%, transparent);
  color: var(--red-soft); margin-top: 0.5rem; align-self: flex-end;
  opacity: 0; transition: opacity 0.15s;
}
@media (hover: none) { .menu-card-avail .menu-add-indicator { opacity: 0.8; } }

/* ── Order panel ─────────────────────────────────────────────────── */
.order-panel {
  width: 360px; flex-shrink: 0;
  background: var(--surface); border: 1px solid rgb(var(--ink) / 0.06);
  border-radius: 16px; overflow: hidden;
  position: sticky; top: 1.5rem;
  display: flex; flex-direction: column;
  max-height: calc(100vh - 3rem); max-height: calc(100dvh - 3rem);
}

.order-panel-head {
  flex-shrink: 0;
  padding: 1.1rem 1.4rem 0.9rem;
  border-bottom: 1px solid rgb(var(--ink) / 0.05);
  display: flex; align-items: flex-start; justify-content: space-between; gap: 0.75rem;
}
.order-panel-title {
  display: flex; align-items: center; gap: 0.5rem;
  font-family: 'Oswald', sans-serif; font-size: 1rem; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.08em; margin: 0;
  color: var(--text);
}
.order-panel-count {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 20px; height: 20px; padding: 0 0.35rem; border-radius: 999px;
  background: #dc2626; color: #fff; font-family: monospace; font-size: 0.65rem; font-weight: 700;
  letter-spacing: 0;
}
.order-panel-close { display: none; }

/* Isi form yang bisa di-scroll; footer di bawahnya tetap */
.order-panel-body {
  flex: 1 1 auto; min-height: 0;
  overflow-y: auto; overscroll-behavior: contain;
  scrollbar-width: thin; scrollbar-color: rgb(var(--ink) / 0.15) transparent;
}
.order-panel-body::-webkit-scrollbar { width: 5px; }
.order-panel-body::-webkit-scrollbar-thumb { background: rgb(var(--ink) / 0.15); border-radius: 999px; }

.order-panel-foot {
  flex-shrink: 0;
  padding: 0.85rem 1.4rem calc(1rem + env(safe-area-inset-bottom, 0px));
  border-top: 1px solid rgb(var(--ink) / 0.08);
  background: var(--surface);
  display: flex; flex-direction: column; gap: 0.7rem;
  box-shadow: 0 -8px 20px -12px rgb(var(--ink) / 0.18);
}

.order-section {
  padding: 1rem 1.4rem;
  border-bottom: 1px solid rgb(var(--ink) / 0.04);
  display: flex; flex-direction: column; gap: 0.6rem;
}

.field { display: flex; flex-direction: column; gap: 0.35rem; }
.field-label {
  font-family: 'Oswald', sans-serif; font-size: 0.56rem;
  letter-spacing: 0.15em; text-transform: uppercase; color: var(--text-faint);
}
.field-optional { font-size: 0.5rem; color: var(--text-faint); }
.field-hint { margin: 0; font-size: 0.65rem; color: var(--text-faint); }

.phone-input-row { display: flex; align-items: center; gap: 0.6rem; }
.phone-avatar {
  width: 34px; height: 34px; border-radius: 50%; flex-shrink: 0;
  background: color-mix(in srgb, var(--accent) 10%, transparent); border: 1px solid color-mix(in srgb, var(--accent) 20%, transparent);
  display: flex; align-items: center; justify-content: center;
  font-family: monospace; font-size: 0.75rem; font-weight: 700; color: var(--accent-text);
}

.pos-input {
  background: rgb(var(--ink) / 0.04); border: 1px solid rgb(var(--ink) / 0.08);
  border-radius: 10px; padding: 0.65rem 0.85rem;
  color: var(--text); font-size: 0.82rem; font-family: 'Inter', sans-serif;
  outline: none; transition: border-color 0.15s; width: 100%;
}
.pos-input::placeholder { color: var(--text-faint); }
.pos-input:focus { border-color: color-mix(in srgb, var(--accent) 45%, transparent); }

/* Loyalty status */
.loyalty-status {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.6rem 0.85rem; border-radius: 10px; border: 1px solid;
  font-size: 0.72rem; line-height: 1.4;
}
.ls-loading { background: rgb(var(--ink) / 0.02); border-color: rgb(var(--ink) / 0.06); color: var(--text-dim); }
.ls-loyal   { background: color-mix(in srgb, var(--green) 7%, transparent);  border-color: color-mix(in srgb, var(--green) 18%, transparent); color: var(--green-soft); }
.ls-regular { background: rgb(var(--ink) / 0.02); border-color: rgb(var(--ink) / 0.06); color: var(--text-faint); }
.ls-spinner {
  width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0;
  border: 2px solid rgb(var(--ink) / 0.2); border-top-color: rgb(var(--ink) / 0.6);
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Cart */
.cart-empty {
  padding: 1.5rem 0; text-align: center;
  color: var(--text-faint); font-size: 0.78rem;
  display: flex; flex-direction: column; align-items: center; gap: 0.3rem;
}
.cart-empty p { margin: 0; }
.cart-empty-icon { font-size: 1.75rem; margin-bottom: 0.25rem; }
.cart-empty-hint { font-size: 0.65rem; color: var(--text-faint); }

.cart-head { display: flex; align-items: center; justify-content: space-between; }
.cart-clear {
  background: none; border: none; padding: 0.2rem 0.1rem; cursor: pointer;
  font-size: 0.65rem; color: var(--text-faint); text-decoration: underline; text-underline-offset: 2px;
}
.cart-clear:hover { color: var(--red-soft); }

.cart-list { display: flex; flex-direction: column; gap: 0.6rem; }

.cart-item {
  background: rgb(var(--ink) / 0.03); border: 1px solid rgb(var(--ink) / 0.06);
  border-radius: 10px; padding: 0.75rem; display: flex; flex-direction: column; gap: 0.5rem;
}
.cart-item-top { display: flex; align-items: flex-start; gap: 0.5rem; }
.cart-item-info { flex: 1; min-width: 0; }
.cart-item-name { font-size: 0.8rem; font-weight: 600; color: var(--text-2); margin: 0 0 0.15rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cart-item-price { font-family: monospace; font-size: 0.7rem; color: var(--text-faint); margin: 0; }
.cart-item-sub { color: var(--text-dim); font-weight: 700; }

.qty-control {
  display: flex; align-items: center; gap: 0.4rem;
  background: rgb(var(--ink) / 0.06); border: 1px solid rgb(var(--ink) / 0.08);
  border-radius: 8px; padding: 3px; flex-shrink: 0; color: var(--text);
}
.qty-btn {
  width: 26px; height: 26px; border-radius: 5px; border: none;
  background: transparent; color: var(--text-dim);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all 0.12s;
}
.qty-btn:hover:not(:disabled) { background: rgb(var(--ink) / 0.1); color: var(--text); }
.qty-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.qty-val { font-family: monospace; font-size: 0.78rem; font-weight: 700; min-width: 18px; text-align: center; }

.cart-item-opts { font-size: 0.68rem; color: var(--amber-soft); margin: 0.15rem 0 0; }

/* ── Picker opsi menu ───────────────────────────────────────────── */
.opt-groups { display: flex; flex-direction: column; gap: 1.1rem; }
.opt-group-hint { margin-left: 0.4rem; font-weight: 400; text-transform: none; letter-spacing: 0; color: var(--text-faint); }
.opt-choices { display: flex; flex-direction: column; gap: 0.4rem; }
.opt-choice { display: flex; justify-content: space-between; align-items: center; gap: 0.75rem; text-align: left; width: 100%; }
.opt-choice-price { font-family: monospace; font-size: 0.72rem; color: var(--amber-soft); }
.opt-missing { font-size: 0.72rem; color: var(--text-faint); margin: 0 0 0.5rem; }
.opt-footer-row { display: flex; align-items: center; gap: 0.75rem; }
.opt-confirm { flex: 1; justify-content: center; }
.opt-confirm:disabled { opacity: 0.45; cursor: not-allowed; }

.cart-notes-input {
  background: rgb(var(--ink) / 0.06); border: 1px solid rgb(var(--ink) / 0.05);
  border-radius: 7px; padding: 0.45rem 0.65rem;
  font-size: 0.68rem; color: var(--amber-soft); font-family: 'Inter', sans-serif;
  outline: none; transition: border-color 0.15s; width: 100%;
}
.cart-notes-input::placeholder { color: var(--text-faint); font-style: italic; }
.cart-notes-input:focus { border-color: color-mix(in srgb, var(--amber) 30%, transparent); }

/* Toggle buttons */
.toggle-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
.toggle-btn {
  display: flex; align-items: center; justify-content: center; gap: 0.35rem;
  padding: 0.65rem 0.6rem; border-radius: 9px; border: 1px solid;
  font-family: 'Oswald', sans-serif; font-size: 0.65rem;
  letter-spacing: 0.08em; text-transform: uppercase;
  cursor: pointer; transition: all 0.15s;
}
.toggle-inactive { background: transparent; border-color: rgb(var(--ink) / 0.08); color: var(--text-faint); }
.toggle-inactive:hover { border-color: rgb(var(--ink) / 0.2); color: var(--text-2); }
.toggle-active-red   { background: color-mix(in srgb, var(--accent) 12%, transparent); border-color: #dc2626; color: var(--text); }
.toggle-active-amber { background: color-mix(in srgb, var(--amber) 12%, transparent); border-color: #d97706; color: var(--amber-soft); }
.toggle-active-white { background: rgb(var(--ink) / 0.08); border-color: rgb(var(--ink) / 0.2); color: var(--text); }
.toggle-disabled { background: transparent; border-color: rgb(var(--ink) / 0.04); color: var(--text-faint); cursor: not-allowed; opacity: 0.6; }

/* Nominal cepat */
.quick-cash { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.quick-cash-btn {
  padding: 0.4rem 0.7rem; border-radius: 8px; cursor: pointer;
  background: rgb(var(--ink) / 0.04); border: 1px solid rgb(var(--ink) / 0.1);
  color: var(--text-2); font-family: monospace; font-size: 0.7rem; font-weight: 700;
  transition: all 0.12s;
}
.quick-cash-btn:hover { border-color: rgb(var(--ink) / 0.25); color: var(--text); }
.quick-cash-btn.is-active {
  background: color-mix(in srgb, var(--accent) 12%, transparent);
  border-color: #dc2626; color: var(--text);
}

/* Change box */
.change-box {
  display: flex; justify-content: space-between;
  padding: 0.55rem 0.85rem; border-radius: 9px;
  font-family: monospace; font-size: 0.78rem; font-weight: 700; border: 1px solid;
}
.change-ok  { background: color-mix(in srgb, var(--green) 7%, transparent);  border-color: color-mix(in srgb, var(--green) 20%, transparent);  color: var(--green-soft); }
.change-err { background: color-mix(in srgb, var(--accent) 7%, transparent);  border-color: color-mix(in srgb, var(--accent) 20%, transparent);  color: var(--red-soft); }

/* ── Waktu order manual (input susulan) ───────────────────────────── */
.time-box {
  margin-top: 0.6rem; padding: 0.7rem; border-radius: 10px;
  display: flex; flex-direction: column; gap: 0.5rem;
  background: color-mix(in srgb, var(--amber) 6%, transparent); border: 1px solid color-mix(in srgb, var(--amber) 25%, transparent);
}
.time-fields { display: grid; grid-template-columns: 1.4fr 1fr; gap: 0.5rem; }
.time-fields .pos-input { min-width: 0; }  /* color-scheme ikut tema dari <html> */
.time-note { margin: 0; font-size: 0.68rem; line-height: 1.5; color: var(--text-dim); }
.time-note strong { color: var(--amber-soft); font-weight: 600; }
.time-error { margin: 0; font-size: 0.68rem; line-height: 1.5; color: var(--red-soft); }

.kasir-strip {
  padding: 0.7rem 1.4rem;
  display: flex; align-items: center; gap: 0.4rem;
  font-size: 0.7rem; color: var(--text-faint);
}
.kasir-name { color: var(--text-dim); font-weight: 600; }

/* ── Promo box: PAKSA ikut tema ──────────────────────────────────────
   PromoCodeBox.vue punya style scoped sendiri dengan warna gelap hardcode.
   :deep() + !important menimpanya dari sini. Kalau nanti PromoCodeBox.vue
   sudah dirapikan, blok ini boleh dihapus. */
.promo-slot { width: 100%; }
.promo-slot :deep(input) {
  background: rgb(var(--ink) / 0.04) !important;
  border: 1px solid rgb(var(--ink) / 0.08) !important;
  color: var(--text) !important;
  border-radius: 10px !important;
  padding: 0.65rem 0.85rem !important;
  font-size: 0.82rem !important;
  font-family: 'Inter', sans-serif !important;
  outline: none;
  box-shadow: none !important;
}
.promo-slot :deep(input::placeholder) { color: var(--text-faint) !important; opacity: 1; }
.promo-slot :deep(input:focus) { border-color: color-mix(in srgb, var(--accent) 45%, transparent) !important; }
.promo-slot :deep(button) {
  background: #dc2626 !important;
  color: #fff !important;
  border: none !important;
  border-radius: 10px !important;
  font-family: 'Oswald', sans-serif !important;
  font-size: 0.68rem !important;
  letter-spacing: 0.1em !important;
  text-transform: uppercase !important;
  cursor: pointer;
  opacity: 1 !important;
}
.promo-slot :deep(button:hover:not(:disabled)) { background: #b91c1c !important; }
.promo-slot :deep(button:disabled) {
  background: rgb(var(--ink) / 0.06) !important;
  color: var(--text-faint) !important;
  cursor: not-allowed;
}

/* Price rows */
.price-row {
  display: flex; justify-content: space-between;
  font-size: 0.78rem; font-family: monospace; color: var(--text-dim);
}
.price-discount { color: var(--green-soft); }
.price-total {
  display: flex; justify-content: space-between; align-items: baseline;
  font-family: 'Oswald', sans-serif; font-size: 0.8rem;
  letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--text-2); font-weight: 500;
}
.total-val { font-family: monospace; font-size: 1.3rem; font-weight: 800; color: var(--accent-text); letter-spacing: 0; }

/* Submit */
.submit-btn {
  display: flex; align-items: center; justify-content: center; gap: 0.45rem;
  padding: 0.85rem; border-radius: 12px; border: none;
  background: #dc2626; color: #fff;
  font-family: 'Oswald', sans-serif; font-size: 0.8rem;
  letter-spacing: 0.12em; text-transform: uppercase;
  cursor: pointer; transition: background 0.15s;
  box-shadow: 0 4px 20px color-mix(in srgb, var(--accent) 20%, transparent);
}
.submit-btn:hover:not(:disabled) { background: #b91c1c; }
.submit-btn:disabled { background: rgb(var(--ink) / 0.06); color: var(--text-faint); cursor: not-allowed; box-shadow: none; }
.btn-spinner {
  width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0;
  border: 2px solid rgb(var(--ink) / 0.3); border-top-color: #fff;
  animation: spin 0.75s linear infinite;
}

/* ── Mobile cart backdrop + FAB (desktop: disembunyikan) ─────────── */
.mobile-cart-backdrop { display: none; }
.mobile-cart-fab { display: none; }

/* ── Drawer tagihan ──────────────────────────────────────────────── */
.drawer-overlay {
  position: fixed; inset: 0; z-index: 50;
  background: var(--overlay); backdrop-filter: blur(3px);
}
.drawer-enter-active { transition: opacity 0.25s ease; }
.drawer-enter-from   { opacity: 0; }
.drawer-leave-active { transition: opacity 0.2s ease; }
.drawer-leave-to     { opacity: 0; }

.drawer-box {
  position: absolute; right: 0; top: 0;
  height: 100vh; height: 100dvh;            /* ikut tinggi layar yang BENAR-BENAR kelihatan */
  width: 420px; max-width: 100%;
  background: var(--surface); border-left: 1px solid rgb(var(--ink) / 0.07);
  display: flex; flex-direction: column; overflow: hidden;
}
.drawer-head {
  display: flex; align-items: flex-start; justify-content: space-between;
  padding: 1.5rem 1.5rem 1.1rem;
  border-bottom: 1px solid rgb(var(--ink) / 0.06);
}
.drawer-title {
  font-family: 'Oswald', sans-serif; font-size: 1.05rem; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.06em; margin: 0;
  color: var(--text);
}
.drawer-close {
  width: 30px; height: 30px; border-radius: 8px;
  background: rgb(var(--ink) / 0.05); border: 1px solid rgb(var(--ink) / 0.08);
  color: var(--text-dim); cursor: pointer;
  display: flex; align-items: center; justify-content: center; transition: all 0.15s;
}
.drawer-close:hover { background: rgb(var(--ink) / 0.1); color: var(--text); }

.drawer-search-wrap { position: relative; padding: 0.85rem 1.25rem; border-bottom: 1px solid rgb(var(--ink) / 0.05); }
.drawer-search-icon { position: absolute; left: 2rem; top: 50%; transform: translateY(-50%); color: var(--text-faint); pointer-events: none; }
.drawer-search {
  width: 100%; background: rgb(var(--ink) / 0.04);
  border: 1px solid rgb(var(--ink) / 0.08); border-radius: 9px;
  padding: 0.6rem 0.85rem 0.6rem 2.2rem;
  color: var(--text); font-size: 0.8rem; outline: none; transition: border-color 0.15s;
}
.drawer-search::placeholder { color: var(--text-faint); }
.drawer-search:focus { border-color: color-mix(in srgb, var(--accent) 40%, transparent); }

.drawer-summary {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.55rem 1.25rem; font-size: 0.7rem; letter-spacing: 0.06em;
  text-transform: uppercase; color: var(--text-dim);
  background: color-mix(in srgb, var(--accent) 6%, transparent); border-bottom: 1px solid rgb(var(--ink) / 0.05);
}
.drawer-summary strong { font-family: monospace; font-size: 0.8rem; color: var(--text); letter-spacing: 0; }

.drawer-empty {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 0.4rem; padding: 3rem;
  color: var(--text-faint); font-size: 0.8rem;
}

/* Area scroll: min-height:0 + flex-shrink:0 di kartu = kunci supaya bisa scroll & kartu tidak gepeng */
.drawer-list {
  flex: 1 1 0; min-height: 0;
  overflow-y: auto; overscroll-behavior: contain;
  padding: 1rem 1.25rem calc(2rem + env(safe-area-inset-bottom, 0px));
  display: flex; flex-direction: column; gap: 0.75rem;
  scrollbar-width: thin; scrollbar-color: rgb(var(--ink) / 0.18) transparent;
}
.drawer-list::-webkit-scrollbar { width: 6px; }
.drawer-list::-webkit-scrollbar-thumb { background: rgb(var(--ink) / 0.18); border-radius: 999px; }

.drawer-order-card {
  flex-shrink: 0;
  background: rgb(var(--ink) / 0.03); border: 1px solid rgb(var(--ink) / 0.06);
  border-radius: 12px; padding: 1rem; display: flex; flex-direction: column; gap: 0.6rem;
}
.drawer-order-top { display: flex; justify-content: space-between; gap: 0.5rem; }
.drawer-order-num { font-family: monospace; font-weight: 700; font-size: 0.82rem; color: var(--text); margin: 0 0 0.2rem; }
.drawer-order-name { font-size: 0.76rem; color: var(--text-dim); margin: 0 0 0.15rem; }
.drawer-order-phone { font-family: monospace; font-size: 0.68rem; color: var(--text-faint); margin: 0; }
.drawer-order-right { text-align: right; flex-shrink: 0; }
.drawer-order-total { font-family: monospace; font-weight: 700; color: var(--accent-text); font-size: 0.9rem; margin: 0 0 0.2rem; }
.drawer-order-items { font-size: 0.65rem; color: var(--text-faint); margin: 0; }

.drawer-items {
  list-style: none; margin: 0.25rem 0 0; padding: 0.6rem 0 0.1rem;
  border-top: 1px dashed rgb(var(--ink) / 0.1);
  display: flex; flex-direction: column; gap: 0.5rem;
}
.drawer-item { display: flex; align-items: center; gap: 0.6rem; font-size: 0.78rem; }
.drawer-item-info { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.drawer-item-name { color: var(--text-2); }
.drawer-item-note { font-size: 0.65rem; color: var(--text-faint); }
.drawer-item-qty { color: var(--text-dim); font-family: monospace; }
.drawer-item-price { font-family: monospace; color: var(--text-2); min-width: 4.5rem; text-align: right; }

.qty-stepper { display: flex; align-items: center; gap: 0.4rem; font-family: monospace; font-size: 0.75rem; color: var(--text); }
.qty-stepper button {
  width: 1.9rem; height: 1.9rem; font-size: 0.95rem;   /* target sentuh lebih besar */
  border-radius: 0.4rem; border: 1px solid rgb(var(--ink) / 0.15);
  background: rgb(var(--ink) / 0.05); color: var(--text); cursor: pointer;
}
.qty-stepper button:disabled { opacity: 0.4; cursor: not-allowed; }

.drawer-add-row { margin: 0.25rem 0; }
.drawer-add-btn {
  width: 100%; min-height: 2.5rem; border-radius: 9px; cursor: pointer;
  border: 1px dashed color-mix(in srgb, var(--green) 50%, transparent); background: color-mix(in srgb, var(--green) 8%, transparent);
  color: var(--green-soft); font-size: 0.72rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
}
.drawer-add-btn:hover { background: color-mix(in srgb, var(--green) 15%, transparent); }

.drawer-split-box {
  margin: 0.25rem 0; padding: 0.75rem;
  border: 1px dashed rgb(var(--ink) / 0.15); border-radius: 0.6rem;
  display: flex; flex-direction: column; gap: 0.5rem;
}
.drawer-hint { font-size: 0.68rem; color: var(--text-dim); margin: 0; }
.drawer-split-total { display: flex; justify-content: space-between; font-size: 0.8rem; font-family: monospace; color: var(--text); }

/* Baris aksi: [Ubah] [Pisah] [Bayar ........] */
.drawer-actions { display: flex; gap: 0.5rem; align-items: stretch; }
.drawer-ghost-btn {
  flex: 0 0 auto; padding: 0 0.85rem; min-height: 2.4rem;
  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
  border-radius: 9px; border: 1px solid rgb(var(--ink) / 0.15);
  background: transparent; color: var(--text-2); cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.drawer-ghost-btn:hover { color: var(--text); border-color: rgb(var(--ink) / 0.3); }
.drawer-ghost-btn.active { background: rgb(var(--ink) / 0.1); color: var(--text); border-color: rgb(var(--ink) / 0.35); }

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
  background: var(--overlay); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; padding: 1rem;
}
.modal-enter-active { transition: all 0.2s ease; }
.modal-enter-from   { opacity: 0; transform: scale(0.95); }
.modal-leave-active { transition: all 0.15s ease; }
.modal-leave-to     { opacity: 0; transform: scale(0.95); }

.modal-box {
  background: var(--surface); border: 1px solid rgb(var(--ink) / 0.08);
  border-radius: 18px; width: 100%; max-width: 460px;
  max-height: 90vh; max-height: 90dvh; overflow-y: auto;
  display: flex; flex-direction: column; gap: 0;
  color: var(--text);
}
.modal-head {
  display: flex; align-items: flex-start; justify-content: space-between;
  padding: 1.5rem 1.5rem 1rem; border-bottom: 1px solid rgb(var(--ink) / 0.05);
}
.modal-title {
  font-family: 'Oswald', sans-serif; font-size: 1.05rem; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.06em; margin: 0 0 0.2rem;
  color: var(--text);
}
.modal-ordnum { font-family: monospace; font-size: 0.78rem; color: var(--text-faint); margin: 0; }
.modal-close-btn {
  width: 30px; height: 30px; border-radius: 8px;
  background: rgb(var(--ink) / 0.05); border: 1px solid rgb(var(--ink) / 0.08);
  color: var(--text-dim); cursor: pointer;
  display: flex; align-items: center; justify-content: center; transition: all 0.15s;
}
.modal-close-btn:hover { background: rgb(var(--ink) / 0.1); color: var(--text); }

.modal-customer { padding: 0.85rem 1.5rem; border-bottom: 1px solid rgb(var(--ink) / 0.04); }
.modal-cust-name { font-weight: 600; font-size: 0.88rem; margin: 0 0 0.15rem; }
.modal-cust-phone { font-family: monospace; font-size: 0.72rem; color: var(--text-faint); margin: 0; }

.modal-items {
  padding: 0.85rem 1.5rem; border-bottom: 1px solid rgb(var(--ink) / 0.04);
  display: flex; flex-direction: column; gap: 0.5rem; max-height: 200px; overflow-y: auto;
}
.modal-item { display: flex; justify-content: space-between; gap: 0.5rem; align-items: flex-start; }
.modal-item-left { flex: 1; min-width: 0; }
.modal-item-name { font-size: 0.82rem; font-weight: 600; color: var(--text-2); margin: 0 0 0.15rem; }
.modal-item-qty { color: var(--text-dim); font-weight: 400; font-size: 0.75rem; }
.modal-item-note { font-size: 0.67rem; color: var(--amber-soft); font-style: italic; margin: 0; }
.modal-item-price { font-family: monospace; font-size: 0.8rem; color: var(--text-2); flex-shrink: 0; }

.modal-totals {
  padding: 0.85rem 1.5rem; border-bottom: 1px solid rgb(var(--ink) / 0.04);
  display: flex; flex-direction: column; gap: 0.35rem;
}
.modal-total-row { display: flex; justify-content: space-between; font-size: 0.78rem; font-family: monospace; color: var(--text-dim); }
.modal-discount { color: var(--green-soft); }
.modal-total-final {
  display: flex; justify-content: space-between;
  padding-top: 0.5rem; border-top: 1px solid rgb(var(--ink) / 0.07);
  font-family: 'Oswald', sans-serif; font-size: 0.82rem; letter-spacing: 0.06em;
  text-transform: uppercase; color: var(--text-2); font-weight: 500;
}
.modal-total-final span:last-child { font-family: monospace; font-size: 1.05rem; font-weight: 800; color: var(--accent-text); }

.modal-section { padding: 0.85rem 1.5rem; border-bottom: 1px solid rgb(var(--ink) / 0.04); display: flex; flex-direction: column; gap: 0.55rem; }
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
    max-height: 88vh; max-height: 88dvh;
    border-radius: 20px 20px 0 0;
    transform: translateY(105%);
    transition: transform 0.3s cubic-bezier(0.32, 0.72, 0, 1);
    z-index: 60;
    box-shadow: var(--shadow-lg);
  }
  .order-panel.mobile-cart-open { transform: translateY(0); }

  .order-panel-close {
    display: flex; align-items: center; justify-content: center;
    width: 28px; height: 28px; border-radius: 8px; flex-shrink: 0;
    background: rgb(var(--ink) / 0.06); border: 1px solid rgb(var(--ink) / 0.1);
    color: var(--text-dim); cursor: pointer;
  }

  .mobile-cart-backdrop {
    display: block; position: fixed; inset: 0;
    background: var(--overlay); backdrop-filter: blur(2px); z-index: 55;
  }

  .mobile-cart-fab {
    display: flex; align-items: center; gap: 0.65rem;
    position: fixed; left: 1rem; right: 1rem; bottom: 1rem;
    z-index: 55; padding: 0.85rem 1.1rem;
    background: #dc2626; border: none; border-radius: 14px;
    box-shadow: 0 8px 28px color-mix(in srgb, var(--accent) 40%, transparent);
    cursor: pointer; color: #fff;
  }
  .mcf-count {
    width: 22px; height: 22px; border-radius: 50%; flex-shrink: 0;
    background: rgba(255,255,255,0.22); display: flex; align-items: center;
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