<template>
  <div class="adm-page ao-page">

    <!-- ── HEADER ──────────────────────────────────────────────────── -->
    <header class="adm-header">
      <div>
        <p class="adm-eyebrow">Masashimura · Operasional</p>
        <h1 class="adm-title">Active Orders</h1>
        <p class="adm-sub">
          {{ formattedCurrentDate }}
          <template v-if="lastUpdated"> · diperbarui {{ lastUpdated }}</template>
        </p>
      </div>

      <div class="adm-header-actions ao-head-actions">
        <button
          type="button"
          class="adm-icon-btn adm-icon-btn--bordered"
          :class="{ 'is-on': soundOn }"
          :title="soundOn ? 'Bunyi order baru: nyala (klik untuk matikan)' : 'Bunyi order baru: mati (klik untuk nyalakan)'"
          :aria-label="soundOn ? 'Matikan bunyi order baru' : 'Nyalakan bunyi order baru'"
          :aria-pressed="soundOn"
          @click="toggleSound"
        >
          <component :is="soundOn ? Bell : BellOff" :size="15" />
        </button>

        <button
          type="button"
          class="adm-icon-btn adm-icon-btn--bordered"
          title="Muat ulang sekarang"
          aria-label="Muat ulang sekarang"
          :disabled="isRefreshing"
          @click="manualRefresh"
        >
          <RefreshCw :size="14" :class="{ 'ao-spin': isRefreshing }" />
        </button>

        <span class="adm-badge" :class="loadError ? 'adm-badge--red' : 'adm-badge--green'" role="status">
          <span class="adm-dot" :class="{ 'ao-pulse': !loadError }"></span>
          {{ loadError ? 'Gagal memuat · mencoba lagi' : 'Live · tiap 5 detik' }}
        </span>
      </div>
    </header>

    <!-- ── TOOLBAR: tanggal + pencarian ────────────────────────────── -->
    <div class="adm-toolbar ao-toolbar">
      <div class="ao-date" role="group" aria-label="Navigasi tanggal">
        <button type="button" class="adm-btn adm-btn--ghost adm-btn--sm" aria-label="Hari sebelumnya" @click="changeDate(-1)">
          <ChevronLeft :size="14" /><span class="ao-hide-xs">Sebelumnya</span>
        </button>
        <input
          type="date"
          class="adm-input adm-input--mono ao-date-input"
          :value="targetDateString"
          aria-label="Pilih tanggal"
          @change="jumpToDate($event.target.value)"
        />
        <button type="button" class="adm-btn adm-btn--ghost adm-btn--sm" aria-label="Hari berikutnya" @click="changeDate(1)">
          <span class="ao-hide-xs">Berikutnya</span><ChevronRight :size="14" />
        </button>
        <button v-if="!isToday" type="button" class="adm-btn adm-btn--soft adm-btn--sm" @click="goToday">Hari ini</button>
      </div>

      <div class="adm-search">
        <Search :size="14" class="adm-search-icon" aria-hidden="true" />
        <input
          ref="searchInput"
          v-model="searchQuery"
          type="search"
          class="adm-input"
          placeholder="Cari no. HP, nama, menu, atau no. order…"
          aria-label="Cari pesanan"
          aria-keyshortcuts="/"
          title="Tekan / untuk langsung mencari"
        />
        <button v-if="searchQuery" type="button" class="adm-search-clear" aria-label="Hapus pencarian" @click="searchQuery = ''">
          <X :size="14" />
        </button>
      </div>
    </div>

    <!-- ── FILTER STATUS + RINGKASAN + URUTAN ──────────────────────── -->
    <div class="ao-filterbar">
      <div class="adm-seg" role="group" aria-label="Filter status pesanan">
        <button
          v-for="tab in statusTabs"
          :key="tab.value"
          type="button"
          class="adm-seg-btn"
          :aria-pressed="statusFilter === tab.value"
          @click="statusFilter = tab.value"
        >
          {{ tab.label }}
          <span class="ao-count" :class="{ 'is-alert': tab.value === 'unpaid' && counts.unpaid > 0 }">{{ counts[tab.value] }}</span>
        </button>
      </div>

      <div class="ao-filterbar-right">
        <div v-if="orders.length" class="ao-summary">
          <span v-if="summary.pending > 0" class="ao-summary-item is-pending">
            Belum dibayar <b>{{ formatPrice(summary.pending) }}</b>
          </span>
          <span v-if="isOwner" class="ao-summary-item">
            Terkumpul <b>{{ formatPrice(summary.paid) }}</b>
          </span>
        </div>

        <div class="adm-seg ao-sort" role="group" aria-label="Urutan daftar">
          <button type="button" class="adm-seg-btn" :aria-pressed="sortMode === 'newest'" @click="setSort('newest')">Terbaru</button>
          <button type="button" class="adm-seg-btn" :aria-pressed="sortMode === 'unpaid'" @click="setSort('unpaid')">Belum lunas dulu</button>
        </div>
      </div>
    </div>

    <!-- ── ERROR MEMUAT DATA ───────────────────────────────────────── -->
    <div v-if="loadError" class="adm-alert ao-error" role="alert">
      <AlertTriangle :size="16" class="ao-error-icon" aria-hidden="true" />
      <div class="ao-error-text">
        <strong>Pesanan {{ targetDateString }} gagal dimuat</strong>
        <span>{{ loadError }}</span>
      </div>
      <button type="button" class="adm-btn adm-btn--ghost adm-btn--sm" @click="retryFetch">
        <RefreshCw :size="13" /> Coba lagi
      </button>
    </div>

    <!-- ── DAFTAR PESANAN ──────────────────────────────────────────── -->
    <section class="adm-card adm-card--flush" aria-label="Daftar pesanan">

      <!-- Loading awal -->
      <div v-if="isLoading && !orders.length && !loadError" class="ao-skeleton" aria-busy="true" aria-label="Memuat pesanan">
        <span v-for="i in 5" :key="i" class="adm-skel ao-skel-row"></span>
      </div>

      <!-- Kosong -->
      <div v-else-if="!filteredOrders.length" class="adm-empty">
        <template v-if="loadError">
          <div class="adm-empty-icon"><AlertTriangle :size="22" /></div>
          <p class="adm-empty-title">Data tidak bisa dimuat</p>
          <p class="adm-empty-text">Ini bukan berarti tidak ada pesanan — lihat keterangan di atas.</p>
        </template>
        <template v-else-if="orders.length">
          <div class="adm-empty-icon"><Search :size="22" /></div>
          <p class="adm-empty-title">Tidak ada pesanan yang cocok</p>
          <p class="adm-empty-text">Coba ubah kata kunci atau filter status.</p>
          <button type="button" class="adm-btn adm-btn--ghost adm-btn--sm" @click="resetFilters">Reset filter</button>
        </template>
        <template v-else>
          <div class="adm-empty-icon"><Receipt :size="22" /></div>
          <p class="adm-empty-title">Belum ada pesanan untuk {{ targetDateString }}</p>
          <p class="adm-empty-text">Pesanan baru akan muncul otomatis, tidak perlu refresh.</p>
        </template>
      </div>

      <!-- Tabel (jadi kartu bertumpuk di HP) -->
      <div v-else class="adm-table-wrap">
        <table class="adm-table adm-table--stack">
          <thead>
            <tr>
              <th>Order</th>
              <th>Customer</th>
              <th>Menu</th>
              <th class="adm-th-r">Tagihan</th>
              <th class="adm-th-c">Status</th>
              <th class="adm-th-c">Waktu</th>
              <th class="adm-th-r">Aksi</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="order in visibleOrders"
              :key="order.id"
              class="ao-row"
              :class="{
                'ao-row--unpaid': isUnpaid(order),
                'ao-row--cancelled': order.status === 'cancelled',
                'ao-row--new': newIds.has(order.id),
              }"
              tabindex="0"
              :aria-label="`Buka struk order ${order.order_number || order.id}`"
              @click="openOrderModal(order)"
              @keydown.enter.self="openOrderModal(order)"
            >
              <td class="adm-td-first ao-id">
                #{{ order.id }}
                <span v-if="newIds.has(order.id)" class="ao-new-tag">Baru</span>
              </td>

              <td data-label="Customer">
                <template v-if="order.customer_name || order.customer_phone">
                  <span class="ao-cust-name">{{ order.customer_name || order.customer_phone }}</span>
                  <span v-if="order.customer_name && order.customer_phone" class="ao-cust-phone">{{ order.customer_phone }}</span>
                </template>
                <span v-else class="adm-badge ao-guest">Guest</span>
              </td>

              <td class="ao-menu-cell" data-label="Menu" :title="itemsTitle(order)">
                <ul v-if="order.items?.length" class="ao-items">
                  <li v-for="(item, i) in itemsPreview(order)" :key="i">
                    <span class="ao-items-qty">{{ item.quantity }}×</span>
                    <span class="ao-items-name">{{ item.menu_name }}</span>
                  </li>
                </ul>
                <span v-else class="ao-items-empty">—</span>
                <span v-if="itemsMore(order)" class="ao-items-more">+{{ itemsMore(order) }} menu lainnya</span>
              </td>

              <td class="adm-td-r" data-label="Tagihan">
                <span class="ao-price">{{ formatPrice(order.total_price) }}</span>
                <span class="ao-method">
                  <component :is="methodIcon(order.payment_method)" :size="13" aria-hidden="true" />
                  {{ methodLabel(order.payment_method) }}
                </span>
              </td>

              <td class="adm-td-c" data-label="Status">
                <div class="ao-status">
                  <span class="adm-badge" :class="orderBadge(order).cls">{{ orderBadge(order).label }}</span>
                  <span v-if="order.status !== 'cancelled'" class="adm-badge" :class="payBadge(order).cls">{{ payBadge(order).label }}</span>
                </div>
              </td>

              <td class="adm-td-c ao-time" data-label="Waktu">
                {{ formatTime(order.created_at) }}
                <span
                  v-if="isUnpaid(order) && isToday && ageLabel(order)"
                  class="ao-age"
                  :class="{ 'is-old': isStale(order) }"
                >{{ ageLabel(order) }}</span>
                <span
                  v-if="order.entered_at"
                  class="ao-late"
                  :title="`Diinput ${formatFullDateTime(order.entered_at)}`"
                >Input susulan</span>
              </td>

              <!-- td tetap table-cell; flex-nya ada di div di dalamnya -->
              <td class="adm-td-r ao-actions-cell" data-label="" @click.stop>
                <div class="ao-actions">
                  <button
                    v-if="canPay(order)"
                    type="button"
                    class="adm-btn adm-btn--primary adm-btn--sm"
                    @click="openPayModal(order)"
                  >Lunasi</button>

                  <button
                    v-if="order.status !== 'completed' && order.status !== 'cancelled'"
                    type="button"
                    class="adm-btn adm-btn--soft adm-btn--sm"
                    @click="openCancelModal(order)"
                  >Batalkan</button>

                  <button
                    type="button"
                    class="adm-icon-btn adm-icon-btn--bordered"
                    title="Lihat struk"
                    aria-label="Lihat struk"
                    @click="openOrderModal(order)"
                  >
                    <Receipt :size="14" />
                  </button>

                  <button
                    v-if="isOwner"
                    type="button"
                    class="adm-icon-btn adm-icon-btn--danger adm-icon-btn--bordered"
                    title="Hapus permanen (khusus owner)"
                    aria-label="Hapus permanen"
                    @click="openDeleteModal(order)"
                  >
                    <Trash2 :size="14" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- ── MODAL STRUK ─────────────────────────────────────────────── -->
    <AdminModal v-model="isModalOpen" :title="`Struk ${selectedOrder?.order_number || ''}`" size="sm">
      <div v-if="selectedOrder" class="rcpt">
        <div class="rcpt-head">
          <img :src="logoUrl" alt="Masashimura" class="rcpt-logo" />
          <p class="rcpt-address">Jl. Pintu air no 48 Depan Pengadilan bekasi, Bekasi, Jawa Barat</p>
        </div>

        <hr class="rcpt-div" />

        <div class="rcpt-rows">
          <div class="rcpt-row"><span>No. Nota</span><b>{{ selectedOrder.order_number }}</b></div>
          <div class="rcpt-row"><span>Kasir</span><b>{{ selectedOrder.kasir_name || kasirName }}</b></div>
          <div class="rcpt-row"><span>Waktu</span><b>{{ formatFullDateTime(selectedOrder.created_at) }}</b></div>
          <div class="rcpt-row"><span>Pelanggan</span><b>{{ selectedOrder.customer_name || selectedOrder.customer_phone || 'Guest' }}</b></div>
        </div>

        <div v-if="selectedOrder.status === 'cancelled'" class="rcpt-cancel">
          <p class="rcpt-cancel-title"><AlertTriangle :size="13" /> Order Dibatalkan</p>
          <div class="rcpt-row"><span>Alasan</span><b>{{ selectedOrder.cancel_reason_display || '—' }}</b></div>
          <div v-if="selectedOrder.cancel_note" class="rcpt-row"><span>Catatan</span><b>{{ selectedOrder.cancel_note }}</b></div>
          <div class="rcpt-row"><span>Oleh</span><b>{{ selectedOrder.cancelled_by || '—' }}</b></div>
          <div class="rcpt-row"><span>Waktu</span><b>{{ formatFullDateTime(selectedOrder.cancelled_at) }}</b></div>
        </div>

        <hr class="rcpt-div" />

        <p class="rcpt-heading">Detail Pesanan</p>
        <div v-for="(item, idx) in selectedOrder.items" :key="idx" class="rcpt-item">
          <div class="rcpt-item-main">
            <span class="rcpt-qty">{{ item.quantity }}×</span>
            <span class="rcpt-name">{{ item.menu_name }}</span>
            <span class="rcpt-sub">{{ formatPrice(item.price * item.quantity) }}</span>
          </div>
          <div v-if="item.notes" class="rcpt-note">{{ item.notes }}</div>
        </div>

        <hr class="rcpt-div" />

        <div class="rcpt-rows">
          <div class="rcpt-row"><span>Subtotal</span><span>{{ formatPrice(computedSubtotal) }}</span></div>
          <div v-if="num(selectedOrder.promo_discount_amount) > 0" class="rcpt-row rcpt-discount">
            <span>Diskon Promo</span><span>-{{ formatPrice(selectedOrder.promo_discount_amount) }}</span>
          </div>
          <div class="rcpt-row rcpt-final"><span>Total</span><span>{{ formatPrice(selectedOrder.total_price) }}</span></div>
          <div v-if="num(selectedOrder.amount_paid) > 0" class="rcpt-row rcpt-muted">
            <span>Dibayar</span><span>{{ formatPrice(selectedOrder.amount_paid) }}</span>
          </div>
          <div v-if="num(selectedOrder.change_amount) > 0" class="rcpt-row rcpt-change">
            <span>Kembalian</span><span>{{ formatPrice(selectedOrder.change_amount) }}</span>
          </div>
        </div>

        <div class="rcpt-card">
          <div class="rcpt-row"><span>Metode</span><b>{{ methodLabel(selectedOrder.payment_method, true) }}</b></div>
          <template v-if="selectedOrder.payment_method === 'mixed' && selectedOrder.payments?.length">
            <div v-for="p in selectedOrder.payments" :key="p.id" class="rcpt-row rcpt-split">
              <span>— {{ p.method_display }}</span><b>{{ formatPrice(p.amount) }}</b>
            </div>
          </template>
          <div class="rcpt-row"><span>Kasir</span><b>{{ selectedOrder.kasir_name || kasirName }}</b></div>
          <div class="rcpt-row">
            <span>Status</span>
            <b :class="['rcpt-status', `is-${selectedOrder.payment_status || 'pending'}`]">{{ payStatusText(selectedOrder) }}</b>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="ao-foot">
          <div class="ao-paper" role="group" aria-label="Ukuran kertas cetak">
            <span class="ao-paper-label">Kertas</span>
            <div class="adm-seg">
              <button type="button" class="adm-seg-btn" :aria-pressed="printPaperWidth === 58" @click="setPaper(58)">58 mm</button>
              <button type="button" class="adm-seg-btn" :aria-pressed="printPaperWidth === 80" @click="setPaper(80)">80 mm</button>
            </div>
          </div>
          <div class="ao-foot-actions">
            <button type="button" class="adm-btn ao-btn-wa" :disabled="isCapturing" @click="shareReceiptAsImage">
              <span v-if="isCapturing" class="adm-spinner"></span><Send v-else :size="14" />
              {{ isCapturing ? 'Memproses…' : 'Kirim via WA' }}
            </button>
            <button type="button" class="adm-btn adm-btn--primary" @click="printReceipt">
              <Printer :size="14" /> Cetak
            </button>
          </div>
        </div>
      </template>
    </AdminModal>

    <!-- ── STRUK TERSEMBUNYI (untuk screenshot / WA) ────────────────────
         Sengaja gelap & fixed — gambar yang dikirim ke customer harus sama
         apa pun tema admin yang sedang dipakai kasir. -->
    <div
      ref="receiptRef"
      aria-hidden="true"
      style="
        position: fixed; left: -9999px; top: 0;
        width: 400px; background-color: #0f0f0f;
        color: #d4d4d8; padding: 24px;
        font-family: 'Courier New', monospace;
        font-size: 12px; line-height: 1.6;
      "
    >
      <div style="text-align:center; margin-bottom:16px;">
        <img :src="logoUrl" alt="Logo" style="height:60px; margin:0 auto 8px; object-fit:contain; display:block;" />
        <div style="font-size:10px; color:#71717a;">Jl. Pintu air no 48 Depan Pengadilan bekasi, Bekasi, Jawa Barat</div>
        <div style="color:#3f3f46; margin-top:8px;">========================================</div>
      </div>
      <div style="font-size:11px; margin-bottom:12px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:2px;"><span>No. Nota :</span><span style="color:#ffffff; font-weight:700;">{{ selectedOrder?.order_number }}</span></div>
        <div style="display:flex; justify-content:space-between; margin-bottom:2px;"><span>Kasir :</span><span style="color:#ffffff;">{{ selectedOrder?.kasir_name || kasirName }}</span></div>
        <div style="display:flex; justify-content:space-between; margin-bottom:2px;"><span>Waktu :</span><span>{{ formatFullDateTime(selectedOrder?.created_at) }}</span></div>
        <div style="display:flex; justify-content:space-between;"><span>Pelanggan :</span><span style="color:#ffffff;">{{ selectedOrder?.customer_name || selectedOrder?.customer_phone || 'Guest' }}</span></div>
      </div>
      <div style="color:#3f3f46; margin-bottom:12px;">----------------------------------------</div>
      <div style="margin-bottom:12px;">
        <div style="font-weight:700; color:#ffffff; font-size:11px; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Detail Pesanan:</div>
        <div v-for="(item, idx) in selectedOrder?.items" :key="idx" style="margin-bottom:6px;">
          <div style="display:flex; justify-content:space-between; color:#ffffff;"><span>{{ item.quantity }}x {{ item.menu_name }}</span><span>{{ formatPrice(item.price * item.quantity) }}</span></div>
          <div v-if="item.notes" style="color:#f59e0b; font-size:10px; padding-left:12px; font-style:italic;">📋 "{{ item.notes }}"</div>
        </div>
      </div>
      <div style="color:#3f3f46; margin-bottom:12px;">----------------------------------------</div>
      <div style="font-size:11px; margin-bottom:12px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:4px;"><span>Subtotal</span><span>{{ formatPrice(computedSubtotal) }}</span></div>
        <div v-if="num(selectedOrder?.promo_discount_amount) > 0" style="display:flex; justify-content:space-between; color:#f87171; margin-bottom:4px;"><span>Diskon Promo</span><span>-{{ formatPrice(selectedOrder?.promo_discount_amount) }}</span></div>
        <div style="color:#3f3f46; margin:6px 0;">----------------------------------------</div>
        <div style="display:flex; justify-content:space-between; font-size:14px; font-weight:900; color:#ffffff; margin-bottom:6px;"><span>TOTAL AKHIR</span><span style="color:#ef4444;">{{ formatPrice(selectedOrder?.total_price) }}</span></div>
        <div v-if="num(selectedOrder?.amount_paid) > 0" style="display:flex; justify-content:space-between; margin-bottom:2px; color:#a1a1aa;"><span>Bayar</span><span style="color:#ffffff; font-weight:600;">{{ formatPrice(selectedOrder?.amount_paid) }}</span></div>
        <div v-if="num(selectedOrder?.change_amount) > 0" style="display:flex; justify-content:space-between;"><span>Kembalian</span><span style="color:#34d399; font-weight:700;">{{ formatPrice(selectedOrder?.change_amount) }}</span></div>
      </div>
      <div style="color:#3f3f46; margin-bottom:12px;">========================================</div>
      <div style="background-color:#1a1a1a; padding:12px; border-radius:12px; border:1px solid #2a2a2a; font-size:10px; line-height:2; margin-bottom:12px;">
        <div>• Metode Bayar : <span style="color:#ffffff; font-weight:700; text-transform:uppercase;">{{ methodLabel(selectedOrder?.payment_method, true) }}</span></div>
        <div>• Kasir : <span style="color:#ffffff; font-weight:700;">{{ selectedOrder?.kasir_name || kasirName }}</span></div>
        <div>• Status : <span :style="selectedOrder?.payment_status === 'paid' ? 'color:#34d399; font-weight:700;' : (selectedOrder?.payment_status === 'void' ? 'color:#a1a1aa; font-weight:700;' : 'color:#fbbf24; font-weight:700;')">{{ payStatusText(selectedOrder) }}</span></div>
      </div>
      <div style="text-align:center; font-size:10px; color:#a1a1aa; padding-top:4px; font-weight:700;">Terima kasih sudah makan di Masashimura! 🙏</div>
    </div>

    <!-- ── STRUK PRINT (thermal 58mm/80mm) — hanya tampil saat print ── -->
    <div ref="printRef" class="print-receipt" :style="{ width: printPaperWidth + 'mm' }">
      <div class="pr-center">
        <div class="pr-brand">MASASHIMURA</div>
        <div class="pr-addr">Jl. Pintu air no 48 Depan Pengadilan Bekasi, Bekasi, Jawa Barat</div>
      </div>
      <div class="pr-divider pr-divider-strong"></div>
      <div class="pr-row"><span>No. Nota</span><span>{{ selectedOrder?.order_number }}</span></div>
      <div class="pr-row"><span>Kasir</span><span>{{ selectedOrder?.kasir_name || kasirName }}</span></div>
      <div class="pr-row"><span>Waktu</span><span>{{ formatFullDateTime(selectedOrder?.created_at) }}</span></div>
      <div class="pr-row"><span>Pelanggan</span><span>{{ selectedOrder?.customer_name || selectedOrder?.customer_phone || 'Guest' }}</span></div>
      <div class="pr-divider"></div>
      <div class="pr-heading">Detail Pesanan</div>
      <div v-for="(item, idx) in selectedOrder?.items" :key="'pr' + idx" class="pr-item">
        <div class="pr-item-row">
          <span>{{ item.quantity }}x {{ item.menu_name }}</span>
          <span>{{ formatPrice(item.price * item.quantity) }}</span>
        </div>
        <div v-if="item.notes" class="pr-note">"{{ item.notes }}"</div>
      </div>
      <div class="pr-divider"></div>
      <div class="pr-row"><span>Subtotal</span><span>{{ formatPrice(computedSubtotal) }}</span></div>
      <div v-if="num(selectedOrder?.promo_discount_amount) > 0" class="pr-row">
        <span>Diskon Promo</span><span>-{{ formatPrice(selectedOrder?.promo_discount_amount) }}</span>
      </div>
      <div class="pr-row pr-total"><span>TOTAL</span><span>{{ formatPrice(selectedOrder?.total_price) }}</span></div>
      <div v-if="num(selectedOrder?.amount_paid) > 0" class="pr-row pr-sub">
        <span>Bayar</span><span>{{ formatPrice(selectedOrder?.amount_paid) }}</span>
      </div>
      <div v-if="num(selectedOrder?.change_amount) > 0" class="pr-row pr-sub">
        <span>Kembalian</span><span>{{ formatPrice(selectedOrder?.change_amount) }}</span>
      </div>
      <div class="pr-divider pr-divider-strong"></div>
      <div class="pr-row"><span>Metode</span><span class="pr-upper">{{ methodLabel(selectedOrder?.payment_method, true) }}</span></div>
      <div class="pr-row"><span>Status</span><span class="pr-upper">{{ payStatusText(selectedOrder) }}</span></div>
      <div class="pr-divider pr-divider-strong"></div>
      <div class="pr-footer">Terima kasih sudah makan di Masashimura!</div>
    </div>

    <!-- ── MODAL LUNASI ────────────────────────────────────────────── -->
    <AdminModal v-model="isPayModalOpen" :title="`Lunasi ${selectedPayOrder?.order_number || ''}`" size="md" :persistent="isPaying">
      <template v-if="selectedPayOrder">
        <div class="ao-person">
          <p class="ao-person-name">{{ selectedPayOrder.customer_name || 'Walk In' }}</p>
          <p class="ao-person-phone">{{ selectedPayOrder.customer_phone || 'Tanpa nomor' }}</p>
        </div>

        <!-- Menu yang dipesan: kasir bisa cek ulang sebelum menerima uang -->
        <ul v-if="selectedPayOrder.items?.length" class="ao-order-items" aria-label="Menu yang dipesan">
          <li v-for="(item, i) in selectedPayOrder.items" :key="i">
            <span class="ao-items-qty">{{ item.quantity }}×</span>
            <span class="ao-oi-name">{{ item.menu_name }}</span>
            <span class="ao-oi-price">{{ formatPrice(item.price * item.quantity) }}</span>
          </li>
        </ul>

        <div class="ao-total">
          <span>Total tagihan</span>
          <strong>{{ formatPrice(selectedPayOrder.total_price) }}</strong>
        </div>

        <div class="adm-field">
          <div class="adm-label-row">
            <span class="adm-label">Pembayaran</span>
            <button type="button" class="adm-btn adm-btn--ghost adm-btn--sm" @click="addPayRow">
              <Plus :size="13" /> Tambah baris
            </button>
          </div>

          <div v-for="(row, idx) in payRows" :key="idx" class="ao-payrow">
            <div class="adm-seg" role="group" :aria-label="`Metode baris ${idx + 1}`">
              <button type="button" class="adm-seg-btn" :aria-pressed="row.method === 'cash'" @click="row.method = 'cash'">
                <Banknote :size="13" /> Cash
              </button>
              <button type="button" class="adm-seg-btn" :aria-pressed="row.method === 'qris_manual'" @click="row.method = 'qris_manual'">
                <QrCode :size="13" /> QRIS
              </button>
            </div>
            <input
              v-model.number="row.amount"
              type="number"
              inputmode="numeric"
              min="0"
              placeholder="0"
              class="adm-input adm-input--mono ao-payrow-input"
              :aria-label="`Nominal baris ${idx + 1}`"
              :data-autofocus="idx === 0 ? '' : null"
              @keydown.enter="canConfirmPay && confirmPay()"
            />
            <button
              v-if="payRows.length > 1"
              type="button"
              class="adm-icon-btn adm-icon-btn--danger"
              :aria-label="`Hapus baris ${idx + 1}`"
              @click="removePayRow(idx)"
            ><X :size="14" /></button>
          </div>

          <!-- Nominal cepat: berlaku untuk baris terakhir -->
          <div v-if="quickAmounts.length" class="ao-quick" role="group" aria-label="Nominal cepat">
            <button
              v-for="q in quickAmounts"
              :key="q.value"
              type="button"
              class="ao-chip"
              @click="applyQuick(q.value)"
            >{{ q.label }}</button>
          </div>

          <button v-if="payRows.length > 1 && paySplitRemaining > 0" type="button" class="ao-link" @click="fillRemainingToLastRow">
            Isi sisa {{ formatPrice(paySplitRemaining) }} ke baris terakhir
          </button>
        </div>

        <div class="ao-diff" :class="paySplitRemaining > 0 ? 'is-short' : 'is-ok'" role="status">
          <span>{{ paySplitRemaining > 0 ? 'Kurang' : (paySplitRemaining < 0 ? 'Kembalian' : 'Pas') }}</span>
          <span>{{ formatPrice(Math.abs(paySplitRemaining)) }}</span>
        </div>
      </template>

      <template #footer>
        <button type="button" class="adm-btn adm-btn--ghost" :disabled="isPaying" @click="isPayModalOpen = false">Batal</button>
        <button type="button" class="adm-btn adm-btn--primary" :disabled="!canConfirmPay" @click="confirmPay">
          <span v-if="isPaying" class="adm-spinner"></span>
          {{ isPaying ? 'Memproses…' : 'Konfirmasi lunas' }}
        </button>
      </template>
    </AdminModal>

    <!-- ── MODAL BATALKAN ORDER ────────────────────────────────────── -->
    <AdminModal v-model="isCancelModalOpen" :title="`Batalkan ${selectedCancelOrder?.order_number || ''}`" size="sm" :persistent="isCancelling">
      <template v-if="selectedCancelOrder">
        <div class="ao-person">
          <p class="ao-person-name">{{ selectedCancelOrder.customer_name || 'Walk In' }}</p>
          <p class="ao-person-phone">{{ selectedCancelOrder.customer_phone || 'Tanpa nomor' }}</p>
        </div>

        <ul v-if="selectedCancelOrder.items?.length" class="ao-order-items" aria-label="Menu yang dipesan">
          <li v-for="(item, i) in selectedCancelOrder.items" :key="i">
            <span class="ao-items-qty">{{ item.quantity }}×</span>
            <span class="ao-oi-name">{{ item.menu_name }}</span>
            <span class="ao-oi-price">{{ formatPrice(item.price * item.quantity) }}</span>
          </li>
        </ul>

        <div class="ao-total">
          <span>Total tagihan</span>
          <strong>{{ formatPrice(selectedCancelOrder.total_price) }}</strong>
        </div>

        <div class="adm-field">
          <span class="adm-label">Alasan pembatalan <span class="adm-req">*</span></span>
          <div class="ao-reasons" role="group" aria-label="Alasan pembatalan">
            <button
              v-for="reason in cancelReasonOptions"
              :key="reason.value"
              type="button"
              class="ao-choice"
              :aria-pressed="cancelReason === reason.value"
              @click="cancelReason = reason.value"
            >{{ reason.label }}</button>
          </div>
        </div>

        <div class="adm-field">
          <label class="adm-label" for="ao-cancel-note">Catatan tambahan <span class="adm-opt">(opsional)</span></label>
          <textarea
            id="ao-cancel-note"
            v-model="cancelNote"
            rows="2"
            class="adm-input"
            placeholder="Cth: kelebihan input qty, salah pencet menu, dll."
          ></textarea>
        </div>
      </template>

      <template #footer>
        <button type="button" class="adm-btn adm-btn--ghost" :disabled="isCancelling" @click="isCancelModalOpen = false">Kembali</button>
        <button type="button" class="adm-btn adm-btn--danger" :disabled="isCancelling || !cancelReason" @click="confirmCancel">
          <span v-if="isCancelling" class="adm-spinner"></span>
          {{ isCancelling ? 'Memproses…' : 'Batalkan order' }}
        </button>
      </template>
    </AdminModal>

    <!-- ── MODAL HAPUS PERMANEN (khusus owner) ─────────────────────── -->
    <AdminModal v-model="isDeleteModalOpen" title="Hapus permanen" size="sm" :persistent="isDeleting" @close="closeDeleteModal">
      <template v-if="selectedDeleteOrder">
        <div class="ao-person">
          <p class="ao-person-name">{{ selectedDeleteOrder.order_number }} · {{ selectedDeleteOrder.customer_name || 'Walk In' }}</p>
          <p class="ao-person-phone">{{ selectedDeleteOrder.customer_phone || 'Tanpa nomor' }} · {{ formatPrice(selectedDeleteOrder.total_price) }}</p>
        </div>

        <p class="adm-alert" role="alert">
          <AlertTriangle :size="16" class="ao-error-icon" aria-hidden="true" />
          <span>
            Order ini akan <strong>dihapus permanen</strong> dari database{{ selectedDeleteOrder.payment_status === 'paid' ? ', termasuk data transaksi yang sudah LUNAS' : '' }}.
            Laporan penjualan, data prediksi, dan riwayat poin pelanggan ikut terpengaruh. Tindakan ini <strong>tidak bisa dibatalkan</strong>.
          </span>
        </p>

        <div class="adm-field">
          <label class="adm-label" for="ao-delete-confirm">
            Ketik <code class="ao-code">{{ selectedDeleteOrder.order_number }}</code> untuk konfirmasi
          </label>
          <input
            id="ao-delete-confirm"
            v-model="deleteConfirmText"
            type="text"
            class="adm-input adm-input--mono"
            placeholder="Ketik nomor order di sini…"
            autocomplete="off"
            data-autofocus
            @keydown.enter="canConfirmDelete && confirmDelete()"
          />
        </div>
      </template>

      <template #footer>
        <button type="button" class="adm-btn adm-btn--ghost" :disabled="isDeleting" @click="closeDeleteModal">Batal</button>
        <button type="button" class="adm-btn adm-btn--danger" :disabled="!canConfirmDelete" @click="confirmDelete">
          <span v-if="isDeleting" class="adm-spinner"></span>
          {{ isDeleting ? 'Menghapus…' : 'Hapus permanen' }}
        </button>
      </template>
    </AdminModal>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import {
  Search, X, ChevronLeft, ChevronRight, Printer, Send, Plus, Trash2,
  Banknote, QrCode, Shuffle, RefreshCw, AlertTriangle, Receipt, Bell, BellOff,
} from 'lucide-vue-next'
import { orderAPI, apiClient } from '@/api'
import { toast } from 'vue-sonner'
import { useAuthStore } from '@/stores/auth'
import html2canvas from 'html2canvas'
import AdminModal from '@/components/ui/admin/Adminmodal.vue'
// Di-import (bukan "/src/assets/…") supaya path-nya ikut di-hash & tetap jalan di build production.
import logoUrl from '@/assets/masashimura-logo.png'

const authStore = useAuthStore()
const kasirName = computed(() => authStore.user?.name || authStore.user?.username || 'Staff')

// Role owner — cuma role ini yang boleh hapus order permanen & lihat nominal "Terkumpul".
// NOTE: ini cuma nyembunyiin tombol di UI. Endpoint DELETE di backend
// WAJIB juga dikasih permission check role owner: request langsung ke API
// bisa bypass tombol ini.
const isOwner = computed(() => (authStore.user?.role || '').toLowerCase() === 'owner')

// ── Preferensi kecil yang diingat di browser ────────────────────────
const readPref = (key, fallback) => {
  try {
    const v = localStorage.getItem(key)
    return v === null ? fallback : v
  } catch { return fallback }
}
const writePref = (key, value) => {
  try { localStorage.setItem(key, String(value)) } catch { /* abaikan */ }
}

// ── State utama ─────────────────────────────────────────────────────
const POLL_MS = 5000
const currentDate = ref(new Date())
const isLoading = ref(true)       // true sampai jawaban pertama (sukses/gagal) untuk tanggal yang dipilih
const isRefreshing = ref(false)
const loadError = ref('')         // pesan kegagalan memuat; kosong = baik-baik saja
const lastUpdated = ref('')
const orders = ref([])
const searchQuery = ref('')
const statusFilter = ref('all')
const searchInput = ref(null)
const now = ref(Date.now())

const num = (v) => parseFloat(v) || 0

// ── Tanggal ─────────────────────────────────────────────────────────
const toDateString = (d) => {
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}
const targetDateString = computed(() => toDateString(currentDate.value))
const isToday = computed(() => targetDateString.value === toDateString(new Date()))
const formattedCurrentDate = computed(() =>
  currentDate.value.toLocaleDateString('id-ID', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
)

// Ganti hari: kosongkan daftar lama dulu. Tanpa ini, kalau request hari baru
// gagal, layar masih menampilkan pesanan hari SEBELUMNYA di bawah tanggal baru.
const resetForNewDate = () => {
  orders.value = []
  loadError.value = ''
  isLoading.value = true
  // Hari baru = mulai dari nol: jangan bunyikan alarm "order baru" untuk isi hari itu.
  knownIds = new Set()
  hasBaseline = false
  newIds.value = new Set()
}
const changeDate = (days) => {
  const d = new Date(currentDate.value)
  d.setDate(d.getDate() + days)
  currentDate.value = d
  resetForNewDate()
  fetchActiveOrders({ force: true })
}
const jumpToDate = (value) => {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value || '')) return
  const [y, m, d] = value.split('-').map(Number)
  currentDate.value = new Date(y, m - 1, d)
  resetForNewDate()
  fetchActiveOrders({ force: true })
}
const goToday = () => {
  currentDate.value = new Date()
  resetForNewDate()
  fetchActiveOrders({ force: true })
}

// ── Notifikasi order baru (bunyi + sorotan) ─────────────────────────
const SOUND_KEY = 'masashimura-ao-sound'
const soundOn = ref(readPref(SOUND_KEY, '1') === '1')
const newIds = ref(new Set())
let knownIds = new Set()
let hasBaseline = false
let flashTimer = null
let audioCtx = null

const playBeep = () => {
  if (!soundOn.value) return
  try {
    audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)()
    if (audioCtx.state === 'suspended') audioCtx.resume()
    const t0 = audioCtx.currentTime
    ;[880, 1175].forEach((freq, i) => {
      const t = t0 + i * 0.16
      const osc = audioCtx.createOscillator()
      const gain = audioCtx.createGain()
      osc.type = 'sine'
      osc.frequency.value = freq
      gain.gain.setValueAtTime(0.0001, t)
      gain.gain.exponentialRampToValueAtTime(0.25, t + 0.02)
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.15)
      osc.connect(gain)
      gain.connect(audioCtx.destination)
      osc.start(t)
      osc.stop(t + 0.16)
    })
  } catch { /* browser menolak audio — abaikan, sorotan visual tetap jalan */ }
}
const toggleSound = () => {
  soundOn.value = !soundOn.value
  writePref(SOUND_KEY, soundOn.value ? '1' : '0')
  if (soundOn.value) playBeep()   // sekaligus contoh bunyinya, dan "membuka" audio browser
}

// Bandingkan daftar baru dengan yang sudah dikenal. Jawaban pertama untuk
// suatu tanggal hanya jadi patokan (baseline), bukan "order baru".
const detectNewOrders = (list) => {
  const fresh = hasBaseline && isToday.value ? list.filter((o) => !knownIds.has(o.id)) : []
  knownIds = new Set(list.map((o) => o.id))
  hasBaseline = true
  if (!fresh.length) return
  newIds.value = new Set([...newIds.value, ...fresh.map((o) => o.id)])
  clearTimeout(flashTimer)
  flashTimer = setTimeout(() => { newIds.value = new Set() }, 8000)
  playBeep()
  toast.info(fresh.length === 1 ? `Order baru #${fresh[0].id} masuk` : `${fresh.length} order baru masuk`)
}

// ── Fetch + polling ─────────────────────────────────────────────────
// Kegagalan memuat TIDAK boleh tampil sebagai "tidak ada pesanan".
const describeFetchError = (err) => {
  const status = err?.response?.status
  const detail = err?.response?.data?.error || err?.response?.data?.detail
  if (!status) return 'Tidak bisa terhubung ke server. Cek internet, atau server backend sedang mati / sedang restart.'
  if (status === 401 || status === 403) return `Sesi login habis atau akun tidak punya akses (${status}). Coba login ulang.`
  if (status >= 500) return `Server error (${status}). Data pesanan tidak hilang — masalahnya di backend (cek log server; kalau baru deploy, pastikan migrasi database sudah dijalankan).`
  return `Server menolak permintaan (${status})${detail ? `: ${detail}` : '.'}`
}

let reqSeq = 0
let inflight = false
const fetchActiveOrders = async ({ force = false } = {}) => {
  if (inflight && !force) return           // jangan numpuk request kalau server lambat
  const seq = ++reqSeq
  inflight = true
  try {
    const res = await orderAPI.getActiveOrders(targetDateString.value)
    if (seq !== reqSeq) return             // jawaban usang (user keburu ganti hari) dibuang
    const list = Array.isArray(res.data) ? res.data : []
    detectNewOrders(list)
    orders.value = list
    loadError.value = ''
    now.value = Date.now()
    lastUpdated.value = new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
  } catch (err) {
    if (seq !== reqSeq) return
    console.error('Gagal tarik data:', err)
    loadError.value = describeFetchError(err) // data lama (tanggal sama) dibiarkan tampil
  } finally {
    if (seq === reqSeq) { inflight = false; isLoading.value = false }
  }
}
const retryFetch = () => { isLoading.value = true; fetchActiveOrders({ force: true }) }
const manualRefresh = async () => {
  isRefreshing.value = true
  try { await fetchActiveOrders({ force: true }) } finally { isRefreshing.value = false }
}

// Pintasan: tekan "/" untuk langsung mengetik di kolom cari (seperti di GitHub / Gmail).
const onKeydown = (e) => {
  if (e.key !== '/' || e.ctrlKey || e.metaKey || e.altKey) return
  const t = e.target
  const tag = t?.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || t?.isContentEditable) return
  if (isModalOpen.value || isPayModalOpen.value || isCancelModalOpen.value || isDeleteModalOpen.value) return
  e.preventDefault()
  searchInput.value?.focus()
}

let pollingTimer = null
const onVisibility = () => { if (!document.hidden) fetchActiveOrders() }
onMounted(() => {
  fetchActiveOrders()
  // Tab yang lagi tidak dilihat tidak perlu menembak server tiap 5 detik.
  pollingTimer = setInterval(() => { if (!document.hidden) fetchActiveOrders() }, POLL_MS)
  document.addEventListener('visibilitychange', onVisibility)
  window.addEventListener('keydown', onKeydown)
})
onUnmounted(() => {
  if (pollingTimer) clearInterval(pollingTimer)
  clearTimeout(flashTimer)
  document.removeEventListener('visibilitychange', onVisibility)
  window.removeEventListener('keydown', onKeydown)
  document.title = baseTitle
  try { audioCtx?.close() } catch { /* abaikan */ }
})

// ── Pencarian + filter status + urutan ──────────────────────────────
const isUnpaid = (o) => o.status !== 'cancelled' && o.payment_status !== 'paid' && o.payment_status !== 'void'
const searchedOrders = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return orders.value
  return orders.value.filter((o) =>
    [o.customer_phone, o.customer_name, o.order_number, o.id, ...(o.items || []).map((i) => i.menu_name)]
      .some((v) => String(v ?? '').toLowerCase().includes(q))
  )
})
const counts = computed(() => {
  const list = searchedOrders.value
  return {
    all: list.length,
    unpaid: list.filter(isUnpaid).length,
    paid: list.filter((o) => o.payment_status === 'paid').length,
    cancelled: list.filter((o) => o.status === 'cancelled').length,
  }
})
const statusTabs = [
  { value: 'all', label: 'Semua' },
  { value: 'unpaid', label: 'Belum lunas' },
  { value: 'paid', label: 'Lunas' },
  { value: 'cancelled', label: 'Dibatalkan' },
]
const filteredOrders = computed(() => {
  const list = searchedOrders.value
  switch (statusFilter.value) {
    case 'unpaid': return list.filter(isUnpaid)
    case 'paid': return list.filter((o) => o.payment_status === 'paid')
    case 'cancelled': return list.filter((o) => o.status === 'cancelled')
    default: return list
  }
})

const SORT_KEY = 'masashimura-ao-sort'
const sortMode = ref(readPref(SORT_KEY, 'newest') === 'unpaid' ? 'unpaid' : 'newest')
const setSort = (mode) => { sortMode.value = mode; writePref(SORT_KEY, mode) }
// "Terbaru" = urutan dari server apa adanya. "Belum lunas dulu" memindahkan yang
// belum dibayar ke atas; sort bersifat stabil jadi urutan di dalam grup tetap.
const visibleOrders = computed(() => {
  if (sortMode.value !== 'unpaid') return filteredOrders.value
  return [...filteredOrders.value].sort((a, b) => Number(isUnpaid(b)) - Number(isUnpaid(a)))
})
const resetFilters = () => { searchQuery.value = ''; statusFilter.value = 'all' }

// ── Ringkasan nominal ───────────────────────────────────────────────
const summary = computed(() => {
  let paid = 0
  let pending = 0
  for (const o of orders.value) {
    if (o.status === 'cancelled') continue
    if (o.payment_status === 'paid') paid += num(o.total_price)
    else if (o.payment_status !== 'void') pending += num(o.total_price)
  }
  return { paid, pending }
})

// Jumlah order belum lunas di judul tab browser — kelihatan walau admin sedang buka tab lain.
let baseTitle = typeof document !== 'undefined' ? document.title : ''
const unpaidTotal = computed(() => orders.value.filter(isUnpaid).length)
watch([unpaidTotal, isToday], ([n, today]) => {
  document.title = n > 0 && today ? `(${n}) ${baseTitle}` : baseTitle
})

// ── Ringkasan menu di tabel ─────────────────────────────────────────
const ITEMS_PREVIEW = 2
const itemsPreview = (o) => (o.items || []).slice(0, ITEMS_PREVIEW)
const itemsMore = (o) => Math.max((o.items?.length || 0) - ITEMS_PREVIEW, 0)
const itemsTitle = (o) => (o.items || []).map((i) => `${i.quantity}× ${i.menu_name}`).join('\n')

// ── Umur order (untuk yang belum lunas) ─────────────────────────────
const ageMinutes = (o) => Math.floor((now.value - new Date(o.created_at).getTime()) / 60000)
const ageLabel = (o) => {
  const m = ageMinutes(o)
  if (isNaN(m) || m < 0) return ''
  if (m < 1) return 'baru saja'
  if (m < 60) return `${m} mnt lalu`
  const h = Math.floor(m / 60)
  return h < 24 ? `${h} jam lalu` : ''
}
const isStale = (o) => ageMinutes(o) >= 30

// ── Badge & label ───────────────────────────────────────────────────
const orderBadge = (o) =>
  o.status === 'completed' ? { cls: 'adm-badge--green', label: 'Selesai' }
  : o.status === 'cancelled' ? { cls: 'adm-badge--red', label: 'Dibatalkan' }
  : { cls: 'adm-badge--amber', label: 'Proses' }
const payBadge = (o) =>
  o.payment_status === 'paid' ? { cls: 'adm-badge--green', label: 'Lunas' }
  : o.payment_status === 'void' ? { cls: '', label: 'Batal' }
  : { cls: 'adm-badge--amber', label: 'Pending' }
const payStatusText = (o) =>
  o?.payment_status === 'paid' ? 'LUNAS' : (o?.payment_status === 'void' ? 'BATAL' : 'PENDING')

const canPay = (o) => o.payment_status !== 'paid' && o.status !== 'cancelled' && o.payment_method !== 'gateway'

const methodIcon = (m) => (['gateway', 'qris_manual', 'qris'].includes(m) ? QrCode : (m === 'mixed' ? Shuffle : Banknote))
const methodLabel = (m, full = false) => {
  if (['gateway', 'qris_manual', 'qris'].includes(m)) return 'QRIS'
  if (m === 'mixed') return full ? 'Split Bayar' : 'Split'
  return m || 'Cash'
}

const formatPrice = (p) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(p || 0)
const formatTime = (s) => {
  const d = new Date(s)
  return isNaN(d) ? '—' : d.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', hour12: false })
}
const formatFullDateTime = (s) => {
  const d = new Date(s)
  if (!s || isNaN(d)) return '—'
  return d.toLocaleString('id-ID', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) + ' WIB'
}

// ── Modal struk ─────────────────────────────────────────────────────
const isModalOpen = ref(false)
const selectedId = ref(null)
const selectedSnapshot = ref(null)
// Ambil dari daftar terbaru supaya struk yang sedang dibuka ikut ter-update oleh polling
// (mis. status berubah jadi Lunas), dengan snapshot sebagai cadangan.
const selectedOrder = computed(() => orders.value.find((o) => o.id === selectedId.value) ?? selectedSnapshot.value)
const openOrderModal = (order) => {
  selectedId.value = order.id
  selectedSnapshot.value = order
  isModalOpen.value = true
}

const computedSubtotal = computed(() => {
  const items = selectedOrder.value?.items || []
  if (items.length) return items.reduce((sum, item) => sum + parseFloat(item.price) * parseInt(item.quantity || 1), 0)
  return num(selectedOrder.value?.subtotal || selectedOrder.value?.total_price)
})

// ── Cetak thermal ───────────────────────────────────────────────────
const printRef = ref(null)
const PAPER_KEY = 'masashimura-print-width'
const readPaper = () => {
  try { return Number(localStorage.getItem(PAPER_KEY)) === 58 ? 58 : 80 } catch { return 80 }
}
const printPaperWidth = ref(readPaper())
// Memilih ukuran kertas TIDAK lagi langsung mencetak; ukuran diingat untuk cetak berikutnya.
const setPaper = (w) => {
  printPaperWidth.value = w
  writePref(PAPER_KEY, w)
}
const printReceipt = () => {
  if (!selectedOrder.value) return
  // @page tidak bisa pakai CSS variable → set ukuran halaman cetak secara dinamis
  let tag = document.getElementById('thermal-page-style')
  if (!tag) {
    tag = document.createElement('style')
    tag.id = 'thermal-page-style'
    document.head.appendChild(tag)
  }
  tag.textContent = `@page { size: ${printPaperWidth.value}mm auto; margin: 0; }`
  // Jeda singkat biar lebar & isi struk sempat re-render sebelum dialog print muncul
  setTimeout(() => window.print(), 80)
}

// ── Kirim struk via WA ──────────────────────────────────────────────
// Capture cuma dari #receiptRef — bukti pembayaran memang tidak pernah
// dirender di node itu, jadi otomatis tidak ikut ke gambar untuk customer.
const receiptRef = ref(null)
const isCapturing = ref(false)
const canvasToBlob = (canvas) => new Promise((resolve) => canvas.toBlob(resolve, 'image/png'))

const shareReceiptAsImage = async () => {
  if (!receiptRef.value || !selectedOrder.value) return
  isCapturing.value = true
  try {
    await new Promise((r) => setTimeout(r, 200))
    const canvas = await html2canvas(receiptRef.value, { backgroundColor: '#0f0f0f', scale: 2, useCORS: true })
    const blob = await canvasToBlob(canvas)
    if (!blob) throw new Error('Gagal membuat blob gambar')

    const order = selectedOrder.value
    const file = new File([blob], `struk-${order.order_number}.png`, { type: 'image/png' })

    if (navigator.share && navigator.canShare?.({ files: [file] })) {
      try {
        await navigator.share({ files: [file], text: 'Bukti Pembelian di Masashimura 🙏' })
      } catch (e) {
        if (e?.name !== 'AbortError') throw e   // user menutup menu share = bukan error
      }
    } else {
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = file.name
      a.click()
      URL.revokeObjectURL(url)
      const raw = order.customer_phone || ''
      const phone = raw.startsWith('0') ? '62' + raw.slice(1) : raw
      const caption = encodeURIComponent('Bukti Pembelian di Masashimura 🙏')
      setTimeout(() => window.open(phone ? `https://wa.me/${phone}?text=${caption}` : `https://wa.me/?text=${caption}`, '_blank'), 500)
      toast.info('Gambar diunduh. Lampirkan ke WhatsApp secara manual jika perlu.')
    }
  } catch (err) {
    console.error(err)
    toast.error('Gagal membuat gambar struk')
  } finally {
    isCapturing.value = false     // sebelumnya bisa nyangkut "Memproses…" kalau share dibatalkan
  }
}

// ── Lunasi ──────────────────────────────────────────────────────────
const isPayModalOpen = ref(false)
const selectedPayOrder = ref(null)
const isPaying = ref(false)
const payRows = ref([{ method: 'cash', amount: 0 }])

const paySplitTotalEntered = computed(() => payRows.value.reduce((sum, r) => sum + (Number(r.amount) || 0), 0))
const paySplitRemaining = computed(() =>
  selectedPayOrder.value ? num(selectedPayOrder.value.total_price) - paySplitTotalEntered.value : 0
)
const canConfirmPay = computed(() =>
  !isPaying.value && paySplitRemaining.value <= 0 && payRows.value.every((r) => Number(r.amount) > 0)
)

// Nominal cepat untuk baris terakhir: "Uang pas" + pembulatan ke atas (5rb, 10rb, 20rb, 50rb, 100rb).
// Kalau baris terakhir QRIS, cuma "Uang pas" yang masuk akal.
const quickAmounts = computed(() => {
  const total = num(selectedPayOrder.value?.total_price)
  if (!total) return []
  const out = [{ value: total, label: 'Uang pas' }]
  const last = payRows.value[payRows.value.length - 1]
  if (last?.method !== 'cash') return out
  const seen = new Set([total])
  for (const step of [5000, 10000, 20000, 50000, 100000]) {
    const v = Math.ceil(total / step) * step
    if (!seen.has(v)) {
      seen.add(v)
      out.push({ value: v, label: formatPrice(v) })
    }
    if (out.length >= 4) break
  }
  return out
})
// `value` = total uang yang diterima dari semua baris; baris terakhir menutup selisihnya.
const applyQuick = (value) => {
  const last = payRows.value[payRows.value.length - 1]
  if (!last) return
  const others = paySplitTotalEntered.value - (Number(last.amount) || 0)
  last.amount = Math.max(value - others, 0)
}

const openPayModal = (order) => {
  selectedPayOrder.value = order
  payRows.value = [{ method: 'cash', amount: 0 }]
  isPayModalOpen.value = true
}
const addPayRow = () => payRows.value.push({ method: 'cash', amount: 0 })
const removePayRow = (idx) => payRows.value.splice(idx, 1)
const fillRemainingToLastRow = () => {
  const last = payRows.value[payRows.value.length - 1]
  if (!last) return
  const others = paySplitTotalEntered.value - (Number(last.amount) || 0)
  last.amount = Math.max(num(selectedPayOrder.value.total_price) - others, 0)
}

const confirmPay = async () => {
  if (!selectedPayOrder.value || !canConfirmPay.value) return
  isPaying.value = true
  try {
    await apiClient.patch(`/orders/${selectedPayOrder.value.id}/pay/`, {
      payments: payRows.value.map((r) => ({ method: r.method, amount: Number(r.amount) || 0 })),
      kasir_name: kasirName.value,
    })
    toast.success(`Order ${selectedPayOrder.value.order_number} berhasil dilunasi`)
    isPayModalOpen.value = false
    selectedPayOrder.value = null
    payRows.value = [{ method: 'cash', amount: 0 }]
    fetchActiveOrders({ force: true })
  } catch (err) {
    toast.error(err?.response?.data?.detail || 'Gagal melunasi pembayaran')
  } finally {
    isPaying.value = false
  }
}

// ── Batalkan ────────────────────────────────────────────────────────
const isCancelModalOpen = ref(false)
const selectedCancelOrder = ref(null)
const cancelReason = ref('')
const cancelNote = ref('')
const isCancelling = ref(false)

const cancelReasonOptions = [
  { value: 'wrong_input', label: 'Salah Input' },
  { value: 'customer_cancel', label: 'Pelanggan Batal' },
  { value: 'out_of_stock', label: 'Stok Habis' },
  { value: 'other', label: 'Lainnya' },
]

const openCancelModal = (order) => {
  selectedCancelOrder.value = order
  cancelReason.value = ''
  cancelNote.value = ''
  isCancelModalOpen.value = true
}

const confirmCancel = async () => {
  if (!selectedCancelOrder.value || !cancelReason.value) return
  isCancelling.value = true
  try {
    await apiClient.patch(`/orders/${selectedCancelOrder.value.id}/cancel/`, {
      cancel_reason: cancelReason.value,
      cancel_note: cancelNote.value,
      kasir_name: kasirName.value,
    })
    toast.success(`Order ${selectedCancelOrder.value.order_number} dibatalkan`)
    isCancelModalOpen.value = false
    selectedCancelOrder.value = null
    cancelReason.value = ''
    cancelNote.value = ''
    fetchActiveOrders({ force: true })
  } catch (err) {
    toast.error(err?.response?.data?.detail || 'Gagal membatalkan order')
  } finally {
    isCancelling.value = false
  }
}

// ── Hapus permanen (khusus owner) ───────────────────────────────────
const isDeleteModalOpen = ref(false)
const selectedDeleteOrder = ref(null)
const deleteConfirmText = ref('')
const isDeleting = ref(false)

const canConfirmDelete = computed(() =>
  !isDeleting.value && !!selectedDeleteOrder.value && deleteConfirmText.value.trim() === selectedDeleteOrder.value.order_number
)

const openDeleteModal = (order) => {
  selectedDeleteOrder.value = order
  deleteConfirmText.value = ''
  isDeleteModalOpen.value = true
}
const closeDeleteModal = () => {
  isDeleteModalOpen.value = false
  selectedDeleteOrder.value = null
  deleteConfirmText.value = ''
}

const confirmDelete = async () => {
  if (!canConfirmDelete.value) return
  isDeleting.value = true
  try {
    await apiClient.delete(`/orders/${selectedDeleteOrder.value.id}/`)
    toast.success(`Order ${selectedDeleteOrder.value.order_number} dihapus permanen`)
    closeDeleteModal()
    fetchActiveOrders({ force: true })
  } catch (err) {
    toast.error(err?.response?.data?.detail || 'Gagal menghapus order. Cek apakah endpoint DELETE sudah tersedia di backend.')
  } finally {
    isDeleting.value = false
  }
}
</script>

<style scoped>
/* Halaman ini punya 7 kolom → butuh ruang lebih lebar dari default .adm-page */
.ao-page { max-width: 87.5rem; }

/* ── Header ──────────────────────────────────────────────────────── */
.ao-head-actions { display: flex; align-items: center; flex-wrap: wrap; gap: 0.5rem; }
.ao-head-actions .adm-icon-btn.is-on { color: var(--accent-text); border-color: var(--line-accent); background: var(--tint-accent); }
.ao-pulse { animation: ao-pulse 2s ease-in-out infinite; }
@keyframes ao-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
.ao-spin { animation: ao-spin 0.8s linear infinite; }
@keyframes ao-spin { to { transform: rotate(360deg); } }

/* ── Toolbar ─────────────────────────────────────────────────────── */
.ao-toolbar { justify-content: space-between; }
.ao-date { display: flex; align-items: center; flex-wrap: wrap; gap: 0.4rem; }
.ao-date-input { width: auto; min-width: 9.5rem; cursor: pointer; }
.adm-search { flex: 1 1 16rem; max-width: 26rem; }
@media (max-width: 720px) {
  .ao-toolbar { flex-direction: column; align-items: stretch; }
  .ao-date { justify-content: space-between; flex-wrap: nowrap; }
  .ao-date-input { flex: 1; min-width: 0; }
  .adm-search { max-width: none; }
}
@media (max-width: 480px) { .ao-hide-xs { display: none; } }

/* ── Filter + ringkasan + urutan ─────────────────────────────────── */
.ao-filterbar { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.75rem; }
.ao-filterbar-right { display: flex; align-items: center; flex-wrap: wrap; gap: 0.6rem 1rem; }
.ao-summary { display: flex; align-items: center; flex-wrap: wrap; gap: 0.25rem 1rem; font-size: 0.75rem; color: var(--text-dim); }
.ao-summary b { margin-left: 0.3rem; font-family: var(--font-mono); font-weight: 700; color: var(--text); }
.ao-summary-item.is-pending b { color: var(--red-soft); }

/* Hitungan di tab filter */
.ao-count {
  min-width: 1.25rem; padding: 0 0.35rem; border-radius: 99px;
  background: rgb(var(--ink) / 0.1);
  font-family: var(--font-mono); font-size: 0.68rem; line-height: 1.35rem; text-align: center;
}
.adm-seg-btn[aria-pressed='true'] .ao-count { background: rgb(255 255 255 / 0.22); }
/* Ada yang belum lunas → angkanya merah supaya tidak terlewat */
.ao-count.is-alert,
.adm-seg-btn[aria-pressed='true'] .ao-count.is-alert { background: var(--accent); color: #fff; }

/* ── Error ───────────────────────────────────────────────────────── */
.ao-error { align-items: center; flex-wrap: wrap; }
.ao-error-icon { flex-shrink: 0; margin-top: 2px; }
.ao-error-text { display: flex; flex-direction: column; gap: 0.15rem; flex: 1 1 16rem; min-width: 0; }
.ao-error-text span { color: var(--text-dim); font-size: 0.75rem; }

/* ── Skeleton ────────────────────────────────────────────────────── */
.ao-skeleton { display: flex; flex-direction: column; gap: 0.6rem; padding: 1rem; }
.ao-skel-row { height: 3.25rem; border-radius: var(--r-md); }

/* ── Tabel ───────────────────────────────────────────────────────── */
.ao-row { cursor: pointer; }
.ao-row:focus-visible { outline-offset: -2px; }
.ao-row:focus-visible td { background: var(--surface-hover); }
.adm-table td { padding-block: 0.9rem; vertical-align: middle; }

.ao-id { font-family: var(--font-mono); font-weight: 700; color: var(--accent-text); white-space: nowrap; }
.ao-new-tag { display: inline-block; margin-left: 0.4rem; padding: 0.05rem 0.4rem; border-radius: 99px; background: var(--green); color: #fff; font-family: var(--font-body); font-size: 0.6rem; font-weight: 700; letter-spacing: 0.04em; vertical-align: middle; }

/* Belum lunas: disorot supaya kasir tidak lupa menagih */
.ao-row--unpaid td { background: var(--tint-accent); }
.ao-row--unpaid td:first-child { box-shadow: inset 3px 0 0 var(--accent); }
.ao-row--unpaid:hover td { background: var(--surface-hover); }

/* Dibatalkan: diredupkan, tombol aksi tetap jelas */
.ao-row--cancelled td:not(.ao-actions-cell) { opacity: 0.6; }
.ao-row--cancelled .ao-price { text-decoration: line-through; }

/* Order baru masuk: berkedip sekali dari hijau ke warna asli */
.ao-row--new td { animation: ao-flash 2.4s ease-out 1; }
@keyframes ao-flash { 0% { background-color: var(--tint-green); } }

/* Customer */
.ao-cust-name { display: block; font-weight: 600; color: var(--text); overflow-wrap: anywhere; }
.ao-cust-phone { display: block; font-family: var(--font-mono); font-size: 0.7rem; color: var(--text-faint); }
.ao-guest { padding-block: 0.1rem; font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.06em; }

/* Menu */
.ao-menu-cell { min-width: 11rem; max-width: 18rem; }
.ao-items { display: flex; flex-direction: column; gap: 0.15rem; margin: 0; padding: 0; list-style: none; }
.ao-items li { display: flex; gap: 0.4rem; font-size: 0.8rem; line-height: 1.35; }
.ao-items-qty { flex-shrink: 0; font-family: var(--font-mono); font-weight: 700; color: var(--accent-text); }
.ao-items-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text); }
.ao-items-more { display: inline-block; margin-top: 0.25rem; padding: 0.05rem 0.5rem; border-radius: 99px; background: rgb(var(--ink) / 0.08); font-size: 0.66rem; font-weight: 600; color: var(--text-dim); }
.ao-items-empty { color: var(--text-faint); }

/* Tagihan + metode */
.ao-price { display: block; font-family: var(--font-mono); font-weight: 700; color: var(--amber-soft); white-space: nowrap; }
.ao-method { display: flex; align-items: center; justify-content: flex-end; gap: 0.3rem; margin-top: 0.15rem; font-size: 0.72rem; text-transform: capitalize; color: var(--text-dim); }

/* Status */
.ao-status { display: inline-flex; flex-direction: column; align-items: center; gap: 0.3rem; }

/* Waktu */
.ao-time { font-family: var(--font-mono); color: var(--text-dim); white-space: nowrap; }
.ao-age { display: block; margin-top: 2px; font-family: var(--font-body); font-size: 0.65rem; color: var(--text-dim); }
.ao-age.is-old { font-weight: 700; color: var(--red-soft); }
.ao-late { display: block; margin-top: 2px; font-family: var(--font-body); font-size: 0.62rem; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; color: var(--amber-soft); }

/* Aksi — flex ada di div, BUKAN di td (td ber-display:flex keluar dari grid tabel) */
.ao-actions-cell { white-space: nowrap; }
.ao-actions { display: flex; align-items: center; justify-content: flex-end; gap: 0.4rem; }

@media (max-width: 720px) {
  .ao-row { margin: 0.6rem; padding: 0.4rem 0 !important; border: 1px solid var(--border); border-radius: var(--r-md); background: var(--surface-2); }
  .adm-table--stack tbody tr.ao-row:last-child { border-bottom: 1px solid var(--border); }
  .ao-row--unpaid { border-color: var(--line-accent); }
  .ao-status { flex-direction: row; }
  .ao-menu-cell { max-width: none; }
  .ao-items-name { white-space: normal; }
  .ao-method { justify-content: flex-start; }
  .ao-actions-cell { padding-top: 0.6rem !important; }
  .ao-actions { justify-content: stretch; }
  .ao-actions .adm-btn { flex: 1; min-height: 44px; }
}

/* ── Footer modal struk ──────────────────────────────────────────── */
.ao-foot { display: flex; align-items: center; flex-wrap: wrap; gap: 0.6rem; width: 100%; }
.ao-paper { display: flex; align-items: center; gap: 0.5rem; }
.ao-paper-label { font-size: 0.68rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-faint); }
.ao-foot-actions { display: flex; gap: 0.5rem; margin-left: auto; }
@media (max-width: 560px) {
  .ao-paper { width: 100%; justify-content: space-between; }
  .ao-foot-actions { width: 100%; }
  .ao-foot-actions .adm-btn { flex: 1; }
}
.ao-btn-wa { background: var(--green); border-color: var(--green); color: #fff; }
.ao-btn-wa:hover:not(:disabled) { filter: brightness(0.92); }

/* ── Struk di dalam modal (ikut tema) ────────────────────────────── */
.rcpt { font-family: var(--font-mono); font-size: 0.78rem; line-height: 1.5; color: var(--text-2); }
.rcpt-head { text-align: center; }
.rcpt-logo { display: block; height: 50px; margin: 0 auto 0.5rem; object-fit: contain; }
:global(html[data-admin-theme='light']) .rcpt-logo { filter: drop-shadow(0 0 1px rgb(24 24 27 / 0.55)) drop-shadow(0 1px 1px rgb(24 24 27 / 0.2)); }
.rcpt-address { margin: 0; font-size: 0.66rem; color: var(--text-faint); }
.rcpt-div { margin: 0.85rem 0; border: 0; border-top: 1px dashed var(--border-strong); }
.rcpt-rows { display: flex; flex-direction: column; gap: 0.25rem; }
.rcpt-row { display: flex; justify-content: space-between; gap: 1rem; }
.rcpt-row > :last-child { text-align: right; }
.rcpt-row b { color: var(--text); font-weight: 600; }
.rcpt-heading { margin: 0 0 0.6rem; font-size: 0.66rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-dim); }
.rcpt-item { margin-bottom: 0.5rem; }
.rcpt-item-main { display: flex; gap: 0.4rem; }
.rcpt-qty { min-width: 1.8rem; color: var(--text-faint); }
.rcpt-name { flex: 1; color: var(--text); }
.rcpt-sub { font-weight: 600; }
.rcpt-note { padding-left: 2.2rem; font-size: 0.68rem; font-style: italic; color: var(--amber-soft); }
.rcpt-discount { color: var(--red-soft); }
.rcpt-final { margin-top: 0.25rem; padding-top: 0.45rem; border-top: 1px dashed var(--border-strong); font-size: 0.95rem; font-weight: 800; color: var(--text); }
.rcpt-final > :last-child { color: var(--accent-text); }
.rcpt-muted { color: var(--text-dim); }
.rcpt-change > :last-child { color: var(--green-soft); font-weight: 700; }
.rcpt-card { display: flex; flex-direction: column; gap: 0.25rem; margin-top: 1rem; padding: 0.75rem 1rem; border: 1px solid var(--border); border-radius: var(--r-md); background: var(--surface-2); }
.rcpt-card b { text-transform: uppercase; }
.rcpt-split { padding-left: 0.75rem; }
.rcpt-status.is-paid { color: var(--green-soft); }
.rcpt-status.is-void { color: var(--text-dim); }
.rcpt-status.is-pending { color: var(--amber-soft); }
.rcpt-cancel { display: flex; flex-direction: column; gap: 0.25rem; margin-top: 0.75rem; padding: 0.7rem 0.85rem; border: 1px solid var(--line-accent); border-radius: var(--r-md); background: var(--tint-accent); }
.rcpt-cancel-title { display: flex; align-items: center; gap: 0.35rem; margin: 0 0 0.25rem; font-weight: 700; color: var(--red-soft); }

/* ── Modal lunasi / batalkan / hapus ─────────────────────────────── */
.ao-person { padding: 0.8rem 1rem; border: 1px solid var(--border); border-radius: var(--r-md); background: var(--surface-2); }
.ao-person-name { margin: 0 0 0.15rem; font-size: 0.9rem; font-weight: 600; color: var(--text); overflow-wrap: anywhere; }
.ao-person-phone { margin: 0; font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-dim); }

/* Daftar menu di dalam modal (maks ±5 baris, sisanya di-scroll) */
.ao-order-items { display: flex; flex-direction: column; gap: 0.3rem; max-height: 9.5rem; margin: 0; padding: 0.7rem 1rem; overflow-y: auto; list-style: none; border: 1px solid var(--border); border-radius: var(--r-md); }
.ao-order-items li { display: flex; align-items: baseline; gap: 0.5rem; font-size: 0.8rem; }
.ao-oi-name { flex: 1; min-width: 0; overflow-wrap: anywhere; color: var(--text); }
.ao-oi-price { font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-dim); white-space: nowrap; }

.ao-total { display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: 0.8rem 1rem; border: 1px solid var(--line-accent); border-radius: var(--r-md); background: var(--tint-accent); }
.ao-total span { font-size: 0.72rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-dim); }
.ao-total strong { font-family: var(--font-mono); font-size: 1.2rem; font-weight: 800; color: var(--accent-text); }

.ao-payrow { display: flex; align-items: center; gap: 0.5rem; }
.ao-payrow .adm-seg { flex-shrink: 0; }
.ao-payrow-input { flex: 1; min-width: 0; }
@media (max-width: 480px) {
  .ao-payrow { flex-wrap: wrap; }
  .ao-payrow .adm-seg { width: 100%; }
  .ao-payrow .adm-seg-btn { flex: 1; }
}

/* Nominal cepat */
.ao-quick { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.ao-chip {
  min-height: 36px; padding: 0.3rem 0.8rem;
  border: 1px solid var(--border-strong); border-radius: 99px;
  background: transparent; color: var(--text-dim);
  font-family: var(--font-mono); font-size: 0.75rem; font-weight: 700;
  cursor: pointer; transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.ao-chip:hover { background: var(--surface-hover); color: var(--text); }
.ao-chip:first-child { border-color: var(--line-accent); color: var(--accent-text); font-family: var(--font-body); }

.ao-link { align-self: flex-start; padding: 0.25rem 0; border: 0; background: none; color: var(--accent-text); font-family: inherit; font-size: 0.75rem; font-weight: 600; text-decoration: underline; cursor: pointer; }
.ao-link:hover { color: var(--text); }

.ao-diff { display: flex; justify-content: space-between; padding: 0.65rem 0.9rem; border: 1px solid; border-radius: var(--r-md); font-family: var(--font-mono); font-size: 0.85rem; font-weight: 700; }
.ao-diff.is-ok { background: var(--tint-green); border-color: var(--line-green); color: var(--green-soft); }
.ao-diff.is-short { background: var(--tint-accent); border-color: var(--line-accent); color: var(--red-soft); }

.ao-reasons { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
.ao-choice {
  min-height: 44px; padding: 0.6rem 0.75rem;
  border: 1px solid var(--border-strong); border-radius: var(--r-md);
  background: transparent; color: var(--text-dim);
  font-family: var(--font-body); font-size: 0.8125rem; font-weight: 600;
  cursor: pointer; transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.ao-choice:hover { background: var(--surface-hover); color: var(--text); }
.ao-choice[aria-pressed='true'] { background: var(--tint-accent); border-color: var(--accent); color: var(--text); }

.ao-code { padding: 0.05rem 0.4rem; border-radius: 4px; background: rgb(var(--ink) / 0.08); color: var(--text); font-family: var(--font-mono); font-weight: 700; }

/* ── Struk print (thermal) — disembunyikan di layar biasa ─────────── */
.print-receipt { display: none; }

/* Hormati pengaturan "kurangi gerakan" di perangkat */
@media (prefers-reduced-motion: reduce) {
  .ao-pulse, .ao-spin, .ao-row--new td { animation: none; }
}
</style>

<!-- ── STYLE PRINT (global, tidak di-scope) ─────────────────────────
     Harus di luar <style scoped> karena selector "body *" butuh akses
     ke seluruh halaman, bukan cuma elemen di dalam komponen ini.
     Struk cetak selalu putih-hitam (kertas), tidak ikut tema. -->
<style>
@media print {
  body * { visibility: hidden; }
  .print-receipt, .print-receipt * { visibility: visible; }
  .print-receipt {
    display: block !important;
    position: absolute;
    left: 0;
    top: 0;
    background: #ffffff;
    color: #000000;
    padding: 4mm 4.5mm;
    font-family: 'Courier New', Courier, monospace;
    font-size: 11.5px;
    line-height: 1.55;
  }
}

.pr-center { text-align: center; margin-bottom: 4px; }
.pr-brand { font-size: 18px; font-weight: 900; letter-spacing: 0.08em; }
.pr-addr { font-size: 9.5px; margin-top: 3px; line-height: 1.4; color: #333; }

.pr-divider { border-top: 1px dashed #000; margin: 8px 0; height: 0; }
.pr-divider-strong { border-top: 2px solid #000; margin: 8px 0; height: 0; }

.pr-row { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 3px; font-size: 11.5px; }
.pr-sub { color: #444; }
.pr-upper { text-transform: uppercase; font-weight: 700; }

.pr-total {
  font-weight: 900;
  font-size: 14px;
  padding: 5px 0;
  margin-top: 2px;
  border-top: 1px dashed #000;
  border-bottom: 1px dashed #000;
}

.pr-heading {
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 6px;
  font-size: 10.5px;
  color: #333;
}
.pr-item { margin-bottom: 5px; }
.pr-item-row { display: flex; justify-content: space-between; gap: 10px; font-size: 11.5px; }
.pr-note { font-size: 9.5px; font-style: italic; padding-left: 12px; color: #444; margin-top: 1px; }

.pr-footer {
  text-align: center;
  font-size: 10.5px;
  font-weight: 700;
  margin-top: 4px;
  letter-spacing: 0.02em;
}
</style>