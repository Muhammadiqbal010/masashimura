<template>
  <div class="ao-root">

    <!-- ── PAGE HEADER ─────────────────────────────────────────────── -->
    <div class="ao-header">
      <div class="ao-header-left">
        <p class="ao-eyebrow">Masashimura · Operasional</p>
        <h1 class="ao-title">Active Orders</h1>
        <p class="ao-date-label">{{ formattedCurrentDate }}</p>
      </div>

      <div class="ao-live">
        <span class="live-dot"></span>
        <span class="live-label">Live · update tiap 5 detik</span>
      </div>
    </div>

    <!-- ── CONTROL BAR ─────────────────────────────────────────────── -->
    <div class="control-bar">
      <div class="date-nav">
        <button class="date-nav-btn" @click="changeDate(-1)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 18l-6-6 6-6"/></svg>
          Kemarin
        </button>
        <span class="date-nav-current">{{ targetDateString }}</span>
        <button class="date-nav-btn" @click="changeDate(1)">
          Besok
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 18l6-6-6-6"/></svg>
        </button>
      </div>

      <div class="search-wrap">
        <svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Cari no. HP..."
          class="search-input"
        />
      </div>
    </div>

    <!-- ── ORDERS TABLE ────────────────────────────────────────────── -->
    <div class="ao-table-card">
      <!-- Summary chips -->
      <div class="ao-summary">
        <div class="summary-chip">
          <span class="summary-chip-value">{{ filteredOrders.length }}</span>
          <span class="summary-chip-label">Total Pesanan</span>
        </div>
        <div class="summary-chip chip-pending">
          <span class="summary-chip-value">{{ filteredOrders.filter(o => o.payment_status !== 'paid' && o.payment_status !== 'void').length }}</span>
          <span class="summary-chip-label">Belum Lunas</span>
        </div>
        <div class="summary-chip chip-paid">
          <span class="summary-chip-value">{{ filteredOrders.filter(o => o.payment_status === 'paid').length }}</span>
          <span class="summary-chip-label">Lunas</span>
        </div>
      </div>

      <div class="table-scroll">
        <table class="ao-table">
          <thead>
            <tr>
              <th>Order</th>
              <th>Customer</th>
              <th class="th-right">Tagihan</th>
              <th class="th-center">Status</th>
              <th>Metode</th>
              <th class="th-center">Waktu</th>
              <th class="th-center">Aksi</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="order in filteredOrders"
              :key="order.id"
              class="ao-row"
              @click="openOrderModal(order)"
            >
              <td class="td-id">#{{ order.id }}</td>

              <td class="td-customer">
                <span class="customer-phone">{{ order.customer_phone || '—' }}</span>
                <span v-if="!order.customer_phone" class="guest-badge">Guest</span>
              </td>

              <td class="td-right td-price">{{ formatPrice(order.total_price) }}</td>

              <td class="td-center">
                <div class="status-stack">
                  <span
                    class="status-pill"
                    :class="order.status === 'completed' ? 'pill-green' : (order.status === 'cancelled' ? 'pill-red' : 'pill-amber')"
                  >
                    {{ order.status === 'completed' ? 'Selesai' : (order.status === 'cancelled' ? 'Dibatalkan' : 'Proses') }}
                  </span>
                  <span
                    class="status-pill pill-sub"
                    :class="order.payment_status === 'paid' ? 'pill-green' : (order.payment_status === 'void' ? 'pill-gray' : 'pill-yellow')"
                  >
                    {{ order.payment_status === 'paid' ? 'Lunas' : (order.payment_status === 'void' ? 'Batal' : 'Pending') }}
                  </span>
                </div>
              </td>

              <td class="td-method">
                <span class="method-icon">{{ order.payment_method === 'qris_manual' ? '📱' : (order.payment_method === 'mixed' ? '🔀' : '💵') }}</span>
                {{ order.payment_method === 'qris_manual' ? 'QRIS' : (order.payment_method === 'mixed' ? 'Split' : (order.payment_method || 'Cash')) }}
              </td>

              <td class="td-center td-time">{{ formatTime(order.created_at) }}</td>

              <td class="td-center td-actions" @click.stop>
                <button
                  v-if="order.payment_status !== 'paid' && order.status !== 'cancelled'"
                  class="lunasi-btn"
                  @click="openPayModal(order)"
                >
                  Lunasi
                </button>
                <span v-else-if="order.status !== 'cancelled'" class="td-dash">✓</span>
                <button
                  v-if="order.status !== 'completed' && order.status !== 'cancelled'"
                  class="batalkan-btn"
                  @click="openCancelModal(order)"
                >
                  Batalkan
                </button>
                <button
                  v-if="isOwner"
                  class="hapus-btn"
                  @click="openDeleteModal(order)"
                  title="Hapus permanen (khusus owner)"
                >
                  Hapus
                </button>
              </td>
            </tr>

            <tr v-if="filteredOrders.length === 0">
              <td colspan="7" class="ao-empty">
                <div class="empty-icon">🍱</div>
                <p class="empty-text">Tidak ada pesanan untuk {{ targetDateString }}</p>
                <p class="empty-hint">Pesanan baru akan muncul otomatis setiap 5 detik</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── MODAL STRUK ─────────────────────────────────────────────── -->
    <div v-if="isModalOpen" class="modal-overlay" @click.self="isModalOpen = false">
      <div class="modal-box">
        <!-- Modal header -->
        <div class="modal-header">
          <div>
            <p class="modal-eyebrow">Struk Pesanan</p>
            <h2 class="modal-title">{{ selectedOrder?.order_number }}</h2>
          </div>
          <button class="modal-close" @click="isModalOpen = false">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>

        <!-- Receipt body — HANYA konten yang boleh ikut kalau struk ini
             suatu saat dijadikan struk online / di-share / di-print.
             Bukti pembayaran SENGAJA tidak ditaruh di sini, lihat blok
             "internal-proof-section" di bawah modal-footer. -->
        <div class="receipt-body">
          <div class="receipt-logo-area">
            <img src="/src/assets/masashimura-logo.png" alt="Logo" class="receipt-logo" />
            <p class="receipt-address">Jl. Pintu air no 48 Depan Pengadilan bekasi, Bekasi, Jawa Barat</p>
          </div>

          <div class="receipt-divider">· · · · · · · · · · · · · · · · · · · ·</div>

          <div class="receipt-meta">
            <div class="meta-row"><span>No. Nota</span><span class="meta-val">{{ selectedOrder?.order_number }}</span></div>
            <div class="meta-row"><span>Kasir</span><span class="meta-val">{{ selectedOrder?.kasir_name || kasirName }}</span></div>
            <div class="meta-row"><span>Waktu</span><span class="meta-val">{{ formatFullDateTime(selectedOrder?.created_at) }}</span></div>
            <div class="meta-row"><span>Pelanggan</span><span class="meta-val">{{ selectedOrder?.customer_name || selectedOrder?.customer_phone || 'Guest' }}</span></div>
          </div>

          <!-- Info pembatalan, cuma muncul kalau order berstatus cancelled -->
          <div v-if="selectedOrder?.status === 'cancelled'" class="cancel-info-box">
            <p class="cancel-info-title">⚠ Order Dibatalkan</p>
            <div class="meta-row"><span>Alasan</span><span class="meta-val">{{ selectedOrder?.cancel_reason_display || '—' }}</span></div>
            <div v-if="selectedOrder?.cancel_note" class="meta-row"><span>Catatan</span><span class="meta-val">{{ selectedOrder?.cancel_note }}</span></div>
            <div class="meta-row"><span>Oleh</span><span class="meta-val">{{ selectedOrder?.cancelled_by || '—' }}</span></div>
            <div class="meta-row"><span>Waktu</span><span class="meta-val">{{ formatFullDateTime(selectedOrder?.cancelled_at) }}</span></div>
          </div>

          <div class="receipt-divider">· · · · · · · · · · · · · · · · · · · ·</div>

          <div class="receipt-items">
            <p class="items-heading">Detail Pesanan</p>
            <div v-for="(item, idx) in selectedOrder?.items" :key="idx" class="item-row">
              <div class="item-main">
                <span class="item-qty">{{ item.quantity }}×</span>
                <span class="item-name">{{ item.menu_name }}</span>
                <span class="item-subtotal">{{ formatPrice(item.price * item.quantity) }}</span>
              </div>
              <div v-if="item.notes" class="item-note">{{ item.notes }}</div>
            </div>
          </div>

          <div class="receipt-divider">· · · · · · · · · · · · · · · · · · · ·</div>

          <div class="receipt-totals">
            <div class="total-row"><span>Subtotal</span><span>{{ formatPrice(computedSubtotal) }}</span></div>
            <div v-if="parseFloat(selectedOrder?.promo_discount_amount) > 0" class="total-row total-discount">
              <span>Diskon Promo</span><span>-{{ formatPrice(selectedOrder?.promo_discount_amount) }}</span>
            </div>
            <div class="total-row total-final">
              <span>Total</span><span>{{ formatPrice(selectedOrder?.total_price) }}</span>
            </div>
            <div v-if="parseFloat(selectedOrder?.amount_paid) > 0" class="total-row total-paid">
              <span>Dibayar</span><span>{{ formatPrice(selectedOrder?.amount_paid) }}</span>
            </div>
            <div v-if="parseFloat(selectedOrder?.change_amount) > 0" class="total-row total-change">
              <span>Kembalian</span><span>{{ formatPrice(selectedOrder?.change_amount) }}</span>
            </div>
          </div>

          <div class="receipt-info-card">
            <div class="info-row"><span>Metode</span><span class="info-val">{{ selectedOrder?.payment_method === 'qris_manual' ? 'QRIS' : (selectedOrder?.payment_method === 'mixed' ? 'Split Bayar' : (selectedOrder?.payment_method || 'Cash')) }}</span></div>
            <template v-if="selectedOrder?.payment_method === 'mixed' && selectedOrder?.payments?.length">
              <div v-for="p in selectedOrder.payments" :key="p.id" class="info-row" style="padding-left:0.75rem;">
                <span>— {{ p.method_display }}</span>
                <span class="info-val">{{ formatPrice(p.amount) }}</span>
              </div>
            </template>
            <div class="info-row"><span>Kasir</span><span class="info-val">{{ selectedOrder?.kasir_name || kasirName }}</span></div>
            <div class="info-row">
              <span>Status</span>
              <span :class="selectedOrder?.payment_status === 'paid' ? 'info-paid' : (selectedOrder?.payment_status === 'void' ? 'info-void' : 'info-pending')">
                {{ selectedOrder?.payment_status === 'paid' ? 'LUNAS' : (selectedOrder?.payment_status === 'void' ? 'BATAL' : 'PENDING') }}
              </span>
            </div>
          </div>
        </div>

        <!-- ── INFO INTERNAL — Bukti Pembayaran QRIS ───────────────────
             SENGAJA dipisah dari .receipt-body (struk) di atas. Blok ini
             gak pernah ikut ke:
               - shareReceiptAsImage() → capture cuma dari #receiptRef
               - printReceipt()        → cetak cuma dari #printRef
             Jadi kalau struk ini nanti dipakai jadi "struk online" yang
             dikirim/di-share ke customer, foto bukti transfer gak akan
             ikut kebawa. Ini murni buat verifikasi internal kasir. -->
        <div v-if="selectedOrder?.proof_image_url" class="internal-proof-section">
          <button type="button" class="internal-proof-toggle" @click="showProofImage = !showProofImage">
            <span class="internal-proof-toggle-left">
              <span class="internal-proof-badge">🔒 Internal</span>
              <span class="internal-proof-title">Bukti Pembayaran QRIS</span>
            </span>
            <span class="internal-proof-chevron" :class="{ open: showProofImage }">▾</span>
          </button>
          <p class="internal-proof-note">Tidak termasuk struk — hanya untuk verifikasi kasir/owner</p>

          <div v-if="showProofImage" class="internal-proof-body">
            <a
              :href="selectedOrder.proof_image_url"
              target="_blank"
              rel="noopener noreferrer"
              class="internal-proof-thumb-link"
            >
              <img :src="selectedOrder.proof_image_url" alt="Bukti Pembayaran" class="internal-proof-thumb" />
            </a>
            <a
              :href="selectedOrder.proof_image_url"
              target="_blank"
              rel="noopener noreferrer"
              class="internal-proof-view-link"
            >
              Buka ukuran penuh ↗
            </a>
          </div>
        </div>

        <!-- Modal footer actions -->
        <div class="modal-footer">
          <button class="btn-share" :disabled="isCapturing" @click="shareReceiptAsImage">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>
            {{ isCapturing ? 'Memproses...' : 'Kirim via WA' }}
          </button>
          <button class="btn-print" @click="printReceipt(80)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 9V2h12v7M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2M6 14h12v8H6z"/></svg>
            Cetak
          </button>
          <button class="btn-close-modal" @click="isModalOpen = false">Tutup</button>
        </div>
        <div class="print-size-row">
          <span class="print-size-label">Ukuran kertas:</span>
          <button
            class="print-size-btn"
            :class="{ active: printPaperWidth === 58 }"
            @click="printReceipt(58)"
          >58mm</button>
          <button
            class="print-size-btn"
            :class="{ active: printPaperWidth === 80 }"
            @click="printReceipt(80)"
          >80mm</button>
        </div>
      </div>
    </div>

    <!-- ── STRUK TERSEMBUNYI (untuk screenshot / WA) ────────────────── -->
    <div
      ref="receiptRef"
      style="
        position: fixed; left: -9999px; top: 0;
        width: 400px; background-color: #0f0f0f;
        color: #d4d4d8; padding: 24px;
        font-family: 'Courier New', monospace;
        font-size: 12px; line-height: 1.6;
      "
    >
      <div style="text-align:center; margin-bottom:16px;">
        <img src="/src/assets/masashimura-logo.png" alt="Logo" style="height:60px; margin:0 auto 8px; object-fit:contain; display:block;" />
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
        <div v-if="parseFloat(selectedOrder?.promo_discount_amount) > 0" style="display:flex; justify-content:space-between; color:#f87171; margin-bottom:4px;"><span>Diskon Promo</span><span>-{{ formatPrice(selectedOrder?.promo_discount_amount) }}</span></div>
        <div style="color:#3f3f46; margin:6px 0;">----------------------------------------</div>
        <div style="display:flex; justify-content:space-between; font-size:14px; font-weight:900; color:#ffffff; margin-bottom:6px;"><span>TOTAL AKHIR</span><span style="color:#ef4444;">{{ formatPrice(selectedOrder?.total_price) }}</span></div>
        <div v-if="parseFloat(selectedOrder?.amount_paid) > 0" style="display:flex; justify-content:space-between; margin-bottom:2px; color:#a1a1aa;"><span>Bayar</span><span style="color:#ffffff; font-weight:600;">{{ formatPrice(selectedOrder.amount_paid) }}</span></div>
        <div v-if="parseFloat(selectedOrder?.change_amount) > 0" style="display:flex; justify-content:space-between;"><span>Kembalian</span><span style="color:#34d399; font-weight:700;">{{ formatPrice(selectedOrder.change_amount) }}</span></div>
      </div>
      <div style="color:#3f3f46; margin-bottom:12px;">========================================</div>
      <div style="background-color:#1a1a1a; padding:12px; border-radius:12px; border:1px solid #2a2a2a; font-size:10px; line-height:2; margin-bottom:12px;">
        <div>• Metode Bayar : <span style="color:#ffffff; font-weight:700; text-transform:uppercase;">{{ selectedOrder?.payment_method || 'Cash' }}</span></div>
        <div>• Kasir : <span style="color:#ffffff; font-weight:700;">{{ selectedOrder?.kasir_name || kasirName }}</span></div>
        <div>• Status : <span :style="selectedOrder?.payment_status === 'paid' ? 'color:#34d399; font-weight:700;' : (selectedOrder?.payment_status === 'void' ? 'color:#a1a1aa; font-weight:700;' : 'color:#fbbf24; font-weight:700;')">{{ selectedOrder?.payment_status === 'paid' ? 'LUNAS' : (selectedOrder?.payment_status === 'void' ? 'BATAL' : 'PENDING') }}</span></div>
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
      <div v-for="(item, idx) in selectedOrder?.items" :key="'pr'+idx" class="pr-item">
        <div class="pr-item-row">
          <span>{{ item.quantity }}x {{ item.menu_name }}</span>
          <span>{{ formatPrice(item.price * item.quantity) }}</span>
        </div>
        <div v-if="item.notes" class="pr-note">"{{ item.notes }}"</div>
      </div>
      <div class="pr-divider"></div>
      <div class="pr-row"><span>Subtotal</span><span>{{ formatPrice(computedSubtotal) }}</span></div>
      <div v-if="parseFloat(selectedOrder?.promo_discount_amount) > 0" class="pr-row">
        <span>Diskon Promo</span><span>-{{ formatPrice(selectedOrder?.promo_discount_amount) }}</span>
      </div>
      <div class="pr-row pr-total"><span>TOTAL</span><span>{{ formatPrice(selectedOrder?.total_price) }}</span></div>
      <div v-if="parseFloat(selectedOrder?.amount_paid) > 0" class="pr-row pr-sub">
        <span>Bayar</span><span>{{ formatPrice(selectedOrder?.amount_paid) }}</span>
      </div>
      <div v-if="parseFloat(selectedOrder?.change_amount) > 0" class="pr-row pr-sub">
        <span>Kembalian</span><span>{{ formatPrice(selectedOrder?.change_amount) }}</span>
      </div>
      <div class="pr-divider pr-divider-strong"></div>
      <div class="pr-row"><span>Metode</span><span class="pr-upper">{{ selectedOrder?.payment_method === 'qris_manual' ? 'QRIS' : (selectedOrder?.payment_method === 'mixed' ? 'Split Bayar' : (selectedOrder?.payment_method || 'Cash')) }}</span></div>
      <div class="pr-row"><span>Status</span><span class="pr-upper">{{ selectedOrder?.payment_status === 'paid' ? 'LUNAS' : (selectedOrder?.payment_status === 'void' ? 'BATAL' : 'PENDING') }}</span></div>
      <div class="pr-divider pr-divider-strong"></div>
      <div class="pr-footer">Terima kasih sudah makan di Masashimura!</div>
    </div>

    <!-- ── MODAL LUNASI ────────────────────────────────────────────── -->
    <div v-if="isPayModalOpen && selectedPayOrder" class="modal-overlay" @click.self="isPayModalOpen = false">
      <div class="pay-modal-box">
        <div class="modal-header">
          <div>
            <p class="modal-eyebrow">Konfirmasi Pembayaran</p>
            <h2 class="modal-title">{{ selectedPayOrder.order_number }}</h2>
          </div>
          <button class="modal-close" @click="isPayModalOpen = false">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>

        <div class="pay-body">
          <!-- Customer info -->
          <div class="pay-customer">
            <p class="pay-name">{{ selectedPayOrder.customer_name || 'Walk In' }}</p>
            <p class="pay-phone">{{ selectedPayOrder.customer_phone || 'Tanpa nomor' }}</p>
          </div>

          <!-- Bukti bayar QRIS di modal lunasi juga, biar kasir bisa cek
               sebelum mengonfirmasi lunas. Ini juga terpisah dari struk. -->
          <a
            v-if="selectedPayOrder.proof_image_url"
            :href="selectedPayOrder.proof_image_url"
            target="_blank"
            rel="noopener noreferrer"
            class="pay-proof-banner"
          >
            📎 Lihat bukti pembayaran QRIS ↗
          </a>

          <!-- Total -->
          <div class="pay-total-strip">
            <span class="pay-total-label">Total Tagihan</span>
            <span class="pay-total-val">{{ formatPrice(selectedPayOrder.total_price) }}</span>
          </div>

          <!-- Split bayar: banyak baris pembayaran -->
          <div class="pay-section">
            <div class="pay-split-header">
              <p class="pay-section-label" style="margin:0;">Pembayaran</p>
              <button type="button" class="pay-add-row-btn" @click="addPayRow">+ Tambah Baris</button>
            </div>

            <div v-for="(row, idx) in payRows" :key="idx" class="pay-split-row">
              <div class="pay-method-grid pay-method-grid-compact">
                <button
                  type="button"
                  @click="row.method = 'cash'"
                  class="pay-method-btn pay-method-btn-sm"
                  :class="{ active: row.method === 'cash' }"
                >💵 Cash</button>
                <button
                  type="button"
                  @click="row.method = 'qris_manual'"
                  class="pay-method-btn pay-method-btn-sm"
                  :class="{ active: row.method === 'qris_manual' }"
                >📱 QRIS</button>
              </div>
              <input
                v-model.number="row.amount"
                type="number"
                placeholder="0"
                class="pay-amount-input pay-split-input"
              />
              <button
                v-if="payRows.length > 1"
                type="button"
                class="pay-remove-row-btn"
                @click="removePayRow(idx)"
                aria-label="Hapus baris"
              >✕</button>
            </div>

            <button type="button" class="pay-split-fill-btn" @click="fillRemainingToLastRow" v-if="paySplitRemaining !== 0">
              Isi otomatis sisa {{ formatPrice(Math.abs(paySplitRemaining)) }} ke baris terakhir
            </button>
          </div>

          <!-- Ringkasan total vs tagihan -->
          <div
            class="change-box"
            :class="paySplitRemaining > 0 ? 'change-err' : 'change-ok'"
          >
            <span>{{ paySplitRemaining > 0 ? 'Kurang' : (paySplitRemaining < 0 ? 'Kembalian' : 'Pas') }}</span>
            <span>{{ formatPrice(Math.abs(paySplitRemaining)) }}</span>
          </div>

          <button
            @click="confirmPay"
            :disabled="isPaying || paySplitRemaining > 0 || payRows.some(r => !r.amount || r.amount <= 0)"
            class="pay-confirm-btn"
          >
            {{ isPaying ? 'Memproses...' : 'Konfirmasi Lunas' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── MODAL BATALKAN ORDER ────────────────────────────────────── -->
    <div v-if="isCancelModalOpen && selectedCancelOrder" class="modal-overlay" @click.self="isCancelModalOpen = false">
      <div class="pay-modal-box">
        <div class="modal-header">
          <div>
            <p class="modal-eyebrow">Batalkan Order</p>
            <h2 class="modal-title">{{ selectedCancelOrder.order_number }}</h2>
          </div>
          <button class="modal-close" @click="isCancelModalOpen = false">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>

        <div class="pay-body">
          <div class="pay-customer">
            <p class="pay-name">{{ selectedCancelOrder.customer_name || 'Walk In' }}</p>
            <p class="pay-phone">{{ selectedCancelOrder.customer_phone || 'Tanpa nomor' }}</p>
          </div>

          <div class="pay-total-strip">
            <span class="pay-total-label">Total Tagihan</span>
            <span class="pay-total-val">{{ formatPrice(selectedCancelOrder.total_price) }}</span>
          </div>

          <!-- Alasan pembatalan (wajib) -->
          <div class="pay-section">
            <p class="pay-section-label">Alasan Pembatalan <span style="color:#dc2626;">*</span></p>
            <div class="pay-method-grid" style="grid-template-columns: repeat(2, 1fr);">
              <button
                v-for="reason in cancelReasonOptions"
                :key="reason.value"
                @click="cancelReason = reason.value"
                class="pay-method-btn"
                :class="{ active: cancelReason === reason.value }"
              >
                {{ reason.label }}
              </button>
            </div>
          </div>

          <!-- Catatan opsional -->
          <div class="pay-section">
            <p class="pay-section-label">Catatan Tambahan (opsional)</p>
            <textarea
              v-model="cancelNote"
              rows="2"
              placeholder="Cth: kelebihan input qty, salah pencet menu, dll."
              class="pay-amount-input"
              style="font-family: inherit; font-size: 0.85rem; resize: vertical;"
            ></textarea>
          </div>

          <button
            @click="confirmCancel"
            :disabled="isCancelling || !cancelReason"
            class="pay-confirm-btn cancel-confirm-btn"
          >
            {{ isCancelling ? 'Memproses...' : 'Batalkan Order Ini' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── MODAL HAPUS PERMANEN (khusus owner) ─────────────────────── -->
    <div v-if="isDeleteModalOpen && selectedDeleteOrder" class="modal-overlay" @click.self="closeDeleteModal">
      <div class="pay-modal-box">
        <div class="modal-header">
          <div>
            <p class="modal-eyebrow delete-eyebrow">⚠ Hapus Permanen</p>
            <h2 class="modal-title">{{ selectedDeleteOrder.order_number }}</h2>
          </div>
          <button class="modal-close" @click="closeDeleteModal">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>

        <div class="pay-body">
          <div class="pay-customer">
            <p class="pay-name">{{ selectedDeleteOrder.customer_name || 'Walk In' }}</p>
            <p class="pay-phone">{{ selectedDeleteOrder.customer_phone || 'Tanpa nomor' }}</p>
          </div>

          <div class="pay-total-strip">
            <span class="pay-total-label">Total Tagihan</span>
            <span class="pay-total-val">{{ formatPrice(selectedDeleteOrder.total_price) }}</span>
          </div>

          <div class="delete-warning-box">
            <p>
              Order ini akan <strong>dihapus permanen</strong> dari database{{ selectedDeleteOrder.payment_status === 'paid' ? ', termasuk data transaksi yang sudah LUNAS' : '' }}.
              Ini akan mempengaruhi laporan penjualan, data prediksi, dan riwayat poin pelanggan. Tindakan ini <strong>tidak bisa dibatalkan</strong>.
            </p>
          </div>

          <div class="pay-section">
            <p class="pay-section-label">
              Ketik <span class="delete-order-code">{{ selectedDeleteOrder.order_number }}</span> untuk konfirmasi
            </p>
            <input
              v-model="deleteConfirmText"
              type="text"
              class="pay-amount-input delete-confirm-input"
              placeholder="Ketik nomor order di sini..."
              autocomplete="off"
            />
          </div>

          <button
            @click="confirmDelete"
            :disabled="isDeleting || deleteConfirmText !== selectedDeleteOrder.order_number"
            class="pay-confirm-btn delete-confirm-btn"
          >
            {{ isDeleting ? 'Menghapus...' : 'Hapus Permanen' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { orderAPI, apiClient } from "@/api";
import { toast } from "vue-sonner";
import { useAuthStore } from '@/stores/auth';
import html2canvas from 'html2canvas';

const authStore = useAuthStore();
const kasirName = computed(() => authStore.user?.name || authStore.user?.username || 'Staff');

// Role owner — cuma role ini yang boleh hapus order permanen.
// NOTE: ini cuma nyembunyiin tombol di UI. Endpoint DELETE di backend
// WAJIB juga dikasih permission check role owner, kalau belum ada,
// karena request langsung ke API bisa bypass tombol ini.
const isOwner = computed(() => (authStore.user?.role || '').toLowerCase() === 'owner');

const currentDate   = ref(new Date());
const orders        = ref([]);
const searchQuery   = ref("");
const isModalOpen   = ref(false);
const selectedOrder = ref(null);
const isCapturing   = ref(false);
const showProofImage = ref(false); // toggle bukti bayar — collapsed by default biar modal gak kepanjangan
const receiptRef    = ref(null);
const printRef       = ref(null);
const printPaperWidth = ref(80); // 58 atau 80 (mm)
let pollingTimer    = null;

const isPayModalOpen   = ref(false);
const selectedPayOrder = ref(null);
const isPaying         = ref(false);
const payRows          = ref([{ method: "cash", amount: 0 }]);

const paySplitTotalEntered = computed(() =>
  payRows.value.reduce((sum, r) => sum + (Number(r.amount) || 0), 0)
);
const paySplitRemaining = computed(() => {
  if (!selectedPayOrder.value) return 0;
  return parseFloat(selectedPayOrder.value.total_price) - paySplitTotalEntered.value;
});

const isCancelModalOpen   = ref(false);
const selectedCancelOrder = ref(null);
const cancelReason        = ref("");
const cancelNote          = ref("");
const isCancelling        = ref(false);

const cancelReasonOptions = [
  { value: "wrong_input",     label: "Salah Input" },
  { value: "customer_cancel", label: "Pelanggan Batal" },
  { value: "out_of_stock",    label: "Stok Habis" },
  { value: "other",           label: "Lainnya" },
];

// ── Hapus permanen (khusus owner) ───────────────────────────────────
const isDeleteModalOpen   = ref(false);
const selectedDeleteOrder = ref(null);
const deleteConfirmText   = ref("");
const isDeleting          = ref(false);

const openDeleteModal = (order) => {
  selectedDeleteOrder.value = order;
  deleteConfirmText.value   = "";
  isDeleteModalOpen.value   = true;
};

const closeDeleteModal = () => {
  isDeleteModalOpen.value   = false;
  selectedDeleteOrder.value = null;
  deleteConfirmText.value   = "";
};

const confirmDelete = async () => {
  if (!selectedDeleteOrder.value) return;
  if (deleteConfirmText.value !== selectedDeleteOrder.value.order_number) return;
  isDeleting.value = true;
  try {
    await apiClient.delete(`/orders/${selectedDeleteOrder.value.id}/`);
    toast.success(`Order ${selectedDeleteOrder.value.order_number} dihapus permanen`);
    closeDeleteModal();
    fetchActiveOrders();
  } catch (err) {
    toast.error(err?.response?.data?.detail || "Gagal menghapus order. Cek apakah endpoint DELETE sudah tersedia di backend.");
  } finally {
    isDeleting.value = false;
  }
};

const formattedCurrentDate = computed(() =>
  currentDate.value.toLocaleDateString('id-ID', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
);
const targetDateString = computed(() => {
  const yyyy = currentDate.value.getFullYear();
  const mm   = String(currentDate.value.getMonth() + 1).padStart(2, '0');
  const dd   = String(currentDate.value.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
});

const changeDate = (days) => {
  const d = new Date(currentDate.value);
  d.setDate(d.getDate() + days);
  currentDate.value = d;
  fetchActiveOrders();
};

const fetchActiveOrders = async () => {
  try {
    const res = await orderAPI.getActiveOrders(targetDateString.value);
    orders.value = res.data;
  } catch (err) { console.error("Gagal tarik data:", err); }
};

const filteredOrders = computed(() =>
  orders.value.filter(o => (o.customer_phone || "").includes(searchQuery.value))
);

const openOrderModal = (order) => { selectedOrder.value = order; showProofImage.value = false; isModalOpen.value = true; };
const openPayModal = (order) => {
  selectedPayOrder.value = order;
  payRows.value          = [{ method: "cash", amount: 0 }];
  isPayModalOpen.value   = true;
};

const addPayRow = () => {
  payRows.value.push({ method: "cash", amount: 0 });
};

const removePayRow = (idx) => {
  payRows.value.splice(idx, 1);
};

const fillRemainingToLastRow = () => {
  if (!payRows.value.length) return;
  const last = payRows.value[payRows.value.length - 1];
  const currentOthers = paySplitTotalEntered.value - (Number(last.amount) || 0);
  const target = parseFloat(selectedPayOrder.value.total_price) - currentOthers;
  last.amount = Math.max(target, 0);
};

const confirmPay = async () => {
  if (!selectedPayOrder.value) return;
  isPaying.value = true;
  try {
    await apiClient.patch(`/orders/${selectedPayOrder.value.id}/pay/`, {
      payments: payRows.value.map(r => ({ method: r.method, amount: Number(r.amount) || 0 })),
      kasir_name: kasirName.value,
    });
    toast.success(`Order ${selectedPayOrder.value.order_number} berhasil dilunasi`);
    isPayModalOpen.value = false;
    selectedPayOrder.value = null;
    payRows.value = [{ method: "cash", amount: 0 }];
    fetchActiveOrders();
  } catch (err) {
    toast.error(err?.response?.data?.detail || "Gagal melunasi pembayaran");
  } finally {
    isPaying.value = false;
  }
};

const openCancelModal = (order) => {
  selectedCancelOrder.value = order;
  cancelReason.value        = "";
  cancelNote.value          = "";
  isCancelModalOpen.value   = true;
};

const confirmCancel = async () => {
  if (!selectedCancelOrder.value || !cancelReason.value) return;
  isCancelling.value = true;
  try {
    await apiClient.patch(`/orders/${selectedCancelOrder.value.id}/cancel/`, {
      cancel_reason: cancelReason.value,
      cancel_note:   cancelNote.value,
      kasir_name:    kasirName.value,
    });
    toast.success(`Order ${selectedCancelOrder.value.order_number} dibatalkan`);
    isCancelModalOpen.value = false;
    selectedCancelOrder.value = null;
    cancelReason.value = "";
    cancelNote.value = "";
    fetchActiveOrders();
  } catch (err) {
    toast.error(err?.response?.data?.detail || "Gagal membatalkan order");
  } finally {
    isCancelling.value = false;
  }
};

// Capture struk cuma dari #receiptRef — proof pembayaran memang tidak
// pernah dirender di dalam node itu, jadi otomatis tidak ikut ke gambar
// yang di-share ke customer via WA.
const shareReceiptAsImage = async () => {
  if (!receiptRef.value || !selectedOrder.value) return;
  isCapturing.value = true;
  await new Promise(r => setTimeout(r, 200));
  try {
    const canvas = await html2canvas(receiptRef.value, { backgroundColor: '#0f0f0f', scale: 2, useCORS: true });
    canvas.toBlob(async (blob) => {
      if (!blob) { toast.error("Gagal membuat gambar struk"); isCapturing.value = false; return; }
      const file = new File([blob], `struk-${selectedOrder.value.order_number}.png`, { type: 'image/png' });
      if (navigator.share && navigator.canShare?.({ files: [file] })) {
        await navigator.share({ files: [file], text: 'Bukti Pembelian di Masashimura 🙏' });
      } else {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url; a.download = file.name; a.click();
        URL.revokeObjectURL(url);
        const phone = (selectedOrder.value.customer_phone || '').startsWith('0')
          ? '62' + selectedOrder.value.customer_phone.slice(1) : selectedOrder.value.customer_phone || '';
        const caption = encodeURIComponent('Bukti Pembelian di Masashimura 🙏');
        setTimeout(() => window.open(phone ? `https://wa.me/${phone}?text=${caption}` : `https://wa.me/?text=${caption}`, '_blank'), 500);
        toast.info("Gambar diunduh. Lampirkan ke WhatsApp secara manual jika perlu.");
      }
      isCapturing.value = false;
    }, 'image/png');
  } catch (err) { console.error(err); toast.error("Gagal screenshot struk"); isCapturing.value = false; }
};

// ── Cetak struk thermal (58mm / 80mm) — cetak cuma dari #printRef,
// yang juga tidak pernah memuat bukti pembayaran ──────────────────
const printReceipt = (widthMm = 80) => {
  if (!selectedOrder.value) return;
  printPaperWidth.value = widthMm;

  // Set ukuran halaman cetak secara dinamis (@page tidak bisa pakai CSS variable)
  let pageStyleTag = document.getElementById('thermal-page-style');
  if (!pageStyleTag) {
    pageStyleTag = document.createElement('style');
    pageStyleTag.id = 'thermal-page-style';
    document.head.appendChild(pageStyleTag);
  }
  pageStyleTag.innerHTML = `@page { size: ${widthMm}mm auto; margin: 0; }`;

  // Kasih jeda dikit biar width & isi struk sempat re-render sebelum dialog print muncul
  setTimeout(() => window.print(), 80);
};

const computedSubtotal = computed(() => {
  const items = selectedOrder.value?.items || [];
  if (items.length) return items.reduce((sum, item) => sum + (parseFloat(item.price) * parseInt(item.quantity || 1)), 0);
  return parseFloat(selectedOrder.value?.subtotal || selectedOrder.value?.total_price || 0);
});

const formatPrice = (p) => new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", minimumFractionDigits: 0 }).format(p || 0);
const formatTime = (s) => new Date(s).toLocaleTimeString('id-ID', { hour: "2-digit", minute: "2-digit", hour12: false });
const formatFullDateTime = (s) => new Date(s).toLocaleString('id-ID', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) + ' WIB';

onMounted(() => { fetchActiveOrders(); pollingTimer = setInterval(fetchActiveOrders, 5000); });
onUnmounted(() => { if (pollingTimer) clearInterval(pollingTimer); });
</script>

<style scoped>
/* ── Root ─────────────────────────────────────────────────────────── */
.ao-root {
  min-height: 100vh;
  background: #080808;
  color: #fff;
  padding: 2.5rem 1.5rem;
  max-width: 1400px;
  margin: 0 auto;
  font-family: 'Inter', sans-serif;
}

/* ── Page Header ─────────────────────────────────────────────────── */
.ao-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  flex-wrap: wrap;
}
.ao-eyebrow {
  font-family: 'Oswald', sans-serif;
  font-size: 0.6rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #dc2626;
  margin: 0 0 0.3rem;
}
.ao-title {
  font-family: 'Oswald', sans-serif;
  font-size: 1.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin: 0 0 0.3rem;
}
.ao-date-label {
  font-size: 0.72rem;
  color: rgba(255,255,255,0.3);
  margin: 0;
}

/* Live indicator — jujur nunjukin tabel ini auto-refresh, bukan statis */
.ao-live {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.8rem;
  background: rgba(34,197,94,0.08);
  border: 1px solid rgba(34,197,94,0.2);
  border-radius: 100px;
  flex-shrink: 0;
}
.live-dot {
  width: 6px; height: 6px;
  background: #22c55e;
  border-radius: 50%;
  animation: pulse 2s infinite;
}
.live-label {
  font-size: 0.65rem;
  font-family: 'Oswald', sans-serif;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #22c55e;
  white-space: nowrap;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ── Control Bar ───────────────────────────────────────────────────
   Navigasi tanggal + pencarian dipisah dari header jadi satu "toolbar"
   sendiri — pola yang sama dipakai di dashboard, biar konsisten
   sebagai satu sistem desain di seluruh app. */
.control-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem 1.25rem;
  background: #0f0f0f;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px;
}

/* Date navigator */
.date-nav {
  display: flex;
  align-items: center;
  gap: 0;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px;
  overflow: hidden;
}
.date-nav-btn {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.55rem 0.85rem;
  background: transparent;
  border: none;
  color: rgba(255,255,255,0.45);
  font-family: 'Oswald', sans-serif;
  font-size: 0.65rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.15s;
}
.date-nav-btn:hover { background: rgba(255,255,255,0.04); color: #fff; }
.date-nav-current {
  padding: 0.55rem 1rem;
  font-family: monospace;
  font-size: 0.8rem;
  color: #fff;
  border-left: 1px solid rgba(255,255,255,0.06);
  border-right: 1px solid rgba(255,255,255,0.06);
}

/* Search */
.search-wrap {
  position: relative;
  display: flex;
  align-items: center;
  margin-left: auto;
}
.search-icon {
  position: absolute;
  left: 0.75rem;
  color: rgba(255,255,255,0.25);
  pointer-events: none;
}
.search-input {
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px;
  padding: 0.55rem 0.85rem 0.55rem 2.25rem;
  color: #fff;
  font-size: 0.82rem;
  font-family: 'Inter', sans-serif;
  outline: none;
  width: 220px;
  transition: border-color 0.15s;
}
.search-input::placeholder { color: rgba(255,255,255,0.2); }
.search-input:focus { border-color: rgba(220,38,38,0.5); }

/* ── Table Card ───────────────────────────────────────────────────── */
.ao-table-card {
  background: #0f0f0f;
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 16px;
  overflow: hidden;
}

/* Summary chips — angka jadi fokus utama, bukan titik kecil */
.ao-summary {
  display: flex;
  align-items: stretch;
  gap: 0;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.summary-chip {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  padding: 1rem 1.5rem;
  border-right: 1px solid rgba(255,255,255,0.05);
  min-width: 140px;
}
.summary-chip-value {
  font-family: 'Inter', monospace;
  font-size: 1.3rem;
  font-weight: 700;
  color: #fff;
  line-height: 1.1;
}
.summary-chip-label {
  font-family: 'Oswald', sans-serif;
  font-size: 0.6rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.3);
}
.chip-pending .summary-chip-value { color: #fbbf24; }
.chip-paid .summary-chip-value    { color: #4ade80; }

/* Table */
.table-scroll { overflow-x: auto; }
.ao-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 720px;
}
.ao-table thead th {
  position: sticky;
  top: 0;
  z-index: 1;
  padding: 0.75rem 1.5rem;
  font-family: 'Oswald', sans-serif;
  font-size: 0.6rem;
  font-weight: 400;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.25);
  text-align: left;
  background: #101010;
  white-space: nowrap;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.th-center { text-align: center; }
.th-right  { text-align: right; }

.ao-row {
  border-top: 1px solid rgba(255,255,255,0.04);
  cursor: pointer;
  transition: background 0.12s;
}
.ao-row:hover { background: rgba(255,255,255,0.025); }
.ao-table td {
  padding: 1rem 1.5rem;
  font-size: 0.85rem;
  vertical-align: middle;
}

.td-id { font-family: monospace; font-weight: 700; color: #dc2626; font-size: 0.82rem; }

.td-customer { display: flex; align-items: center; gap: 0.5rem; }
.customer-phone { font-family: monospace; font-size: 0.82rem; color: rgba(255,255,255,0.8); }
.guest-badge {
  font-size: 0.55rem; padding: 0.1rem 0.4rem;
  border-radius: 4px; border: 1px solid rgba(255,255,255,0.1);
  color: rgba(255,255,255,0.25);
  font-family: 'Oswald', sans-serif; letter-spacing: 0.08em; text-transform: uppercase;
}

.td-right { text-align: right; }
.td-price { font-family: monospace; font-weight: 700; color: #fbbf24; }

.td-center { text-align: center; }

/* Status order + pembayaran digabung jadi satu kolom (tumpuk), biar
   tabel gak kepanjangan dan dua info yang saling terkait kebaca
   bareng, bukan dipisah jauh di kolom berbeda. */
.status-stack {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 0.3rem;
}
.status-pill {
  display: inline-block;
  padding: 0.22rem 0.65rem;
  border-radius: 100px;
  font-size: 0.62rem;
  font-family: 'Oswald', sans-serif;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-weight: 500;
}
.status-pill.pill-sub { opacity: 0.75; font-size: 0.58rem; padding: 0.18rem 0.55rem; }
.pill-green  { background: rgba(34,197,94,0.1);  color: #4ade80; border: 1px solid rgba(34,197,94,0.2); }
.pill-amber  { background: rgba(245,158,11,0.1); color: #fbbf24; border: 1px solid rgba(245,158,11,0.2); }
.pill-yellow { background: rgba(234,179,8,0.08); color: #facc15; border: 1px solid rgba(234,179,8,0.18); }
.pill-red    { background: rgba(220,38,38,0.1);  color: #f87171; border: 1px solid rgba(220,38,38,0.2); }
.pill-gray   { background: rgba(255,255,255,0.05); color: #a1a1aa; border: 1px solid rgba(255,255,255,0.1); }

.td-method { font-size: 0.8rem; color: rgba(255,255,255,0.55); text-transform: capitalize; }
.method-icon { margin-right: 0.2rem; }

.td-time { font-family: monospace; font-size: 0.78rem; color: rgba(255,255,255,0.3); }
.td-dash { color: rgba(255,255,255,0.15); font-size: 0.8rem; }

.lunasi-btn {
  padding: 0.4rem 1rem;
  background: #dc2626;
  border: none;
  border-radius: 8px;
  color: #fff;
  font-family: 'Oswald', sans-serif;
  font-size: 0.65rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
  transition: background 0.15s;
}
.lunasi-btn:hover { background: #b91c1c; }

.td-actions { display: flex; align-items: center; justify-content: center; gap: 0.5rem; flex-wrap: wrap; }

.batalkan-btn {
  padding: 0.4rem 0.85rem;
  background: transparent;
  border: 1px solid rgba(220,38,38,0.35);
  border-radius: 8px;
  color: #f87171;
  font-family: 'Oswald', sans-serif;
  font-size: 0.65rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.batalkan-btn:hover { background: rgba(220,38,38,0.1); border-color: rgba(220,38,38,0.6); }

/* Tombol hapus permanen — dibedain visualnya dari "Batalkan" biar
   kasir/owner sadar ini aksi yang levelnya beda (destruktif, bukan
   sekadar ubah status). */
.hapus-btn {
  padding: 0.4rem 0.85rem;
  background: rgba(0,0,0,0.4);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 8px;
  color: rgba(255,255,255,0.5);
  font-family: 'Oswald', sans-serif;
  font-size: 0.65rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.15s;
}
.hapus-btn:hover { background: #dc2626; border-color: #dc2626; color: #fff; }

.cancel-confirm-btn { background: #dc2626; }
.cancel-confirm-btn:hover:not(:disabled) { background: #b91c1c; }

/* Empty state */
.ao-empty {
  padding: 4rem 2rem !important;
  text-align: center;
}
.empty-icon { font-size: 2rem; margin-bottom: 0.75rem; }
.empty-text { color: rgba(255,255,255,0.3); font-size: 0.875rem; margin: 0 0 0.3rem; }
.empty-hint { color: rgba(255,255,255,0.15); font-size: 0.7rem; margin: 0; }

/* ── Modal overlay ───────────────────────────────────────────────── */
.modal-overlay {
  position: fixed; inset: 0; z-index: 50;
  background: rgba(0,0,0,0.75);
  backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  padding: 1rem;
}

/* ── Receipt Modal ───────────────────────────────────────────────── */
.modal-box {
  background: #0f0f0f;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 20px;
  width: 100%; max-width: 420px;
  max-height: 90vh;
  display: flex; flex-direction: column;
  overflow: hidden;
}
.modal-header {
  display: flex; align-items: flex-start;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.modal-eyebrow {
  font-family: 'Oswald', sans-serif;
  font-size: 0.58rem; letter-spacing: 0.18em;
  text-transform: uppercase; color: #dc2626; margin: 0 0 0.25rem;
}
.delete-eyebrow { color: #f87171; }
.modal-title { font-family: monospace; font-size: 1rem; font-weight: 700; margin: 0; }
.modal-close {
  width: 30px; height: 30px; border-radius: 8px;
  background: rgba(255,255,255,0.05); border: none;
  color: rgba(255,255,255,0.4); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s; flex-shrink: 0;
}
.modal-close:hover { background: rgba(255,255,255,0.1); color: #fff; }

.receipt-body {
  padding: 1.25rem 1.5rem;
  overflow-y: auto; flex: 1;
  font-family: 'Courier New', monospace; font-size: 0.78rem;
  color: rgba(255,255,255,0.7);
}
.receipt-logo-area { text-align: center; margin-bottom: 1rem; }
.receipt-logo { height: 50px; margin: 0 auto 0.5rem; display: block; object-fit: contain; }
.receipt-address { font-size: 0.65rem; color: rgba(255,255,255,0.25); }
.receipt-divider { text-align: center; color: rgba(255,255,255,0.1); margin: 0.75rem 0; font-size: 0.7rem; letter-spacing: 0.1em; }

.receipt-meta { display: flex; flex-direction: column; gap: 0.25rem; }
.meta-row { display: flex; justify-content: space-between; font-size: 0.72rem; }
.cancel-info-box {
  margin-top: 0.75rem;
  padding: 0.7rem 0.85rem;
  background: rgba(220,38,38,0.08);
  border: 1px solid rgba(220,38,38,0.2);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.cancel-info-title { margin: 0 0 0.25rem; font-size: 0.72rem; font-weight: 700; color: #f87171; }
.meta-val { color: #fff; font-weight: 600; }

.receipt-items { margin-bottom: 0.5rem; }
.items-heading { font-size: 0.65rem; font-weight: 700; color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 0.12em; margin: 0 0 0.6rem; }
.item-row { margin-bottom: 0.5rem; }
.item-main { display: flex; gap: 0.4rem; }
.item-qty { color: rgba(255,255,255,0.35); min-width: 1.8rem; }
.item-name { flex: 1; color: #fff; }
.item-subtotal { color: rgba(255,255,255,0.7); font-weight: 600; }
.item-note { font-size: 0.65rem; color: #fbbf24; padding-left: 2.2rem; font-style: italic; margin-top: 0.15rem; }

.receipt-totals { display: flex; flex-direction: column; gap: 0.3rem; }
.total-row { display: flex; justify-content: space-between; font-size: 0.75rem; }
.total-discount { color: #f87171; }
.total-final { font-size: 0.9rem; font-weight: 900; color: #fff; padding-top: 0.4rem; border-top: 1px dashed rgba(255,255,255,0.1); margin-top: 0.25rem; }
.total-final span:last-child { color: #ef4444; }
.total-paid { color: rgba(255,255,255,0.5); }
.total-change span:last-child { color: #34d399; font-weight: 700; }

.receipt-info-card {
  margin-top: 1rem;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  padding: 0.75rem 1rem;
  display: flex; flex-direction: column; gap: 0.25rem;
}
.info-row { display: flex; justify-content: space-between; font-size: 0.7rem; }
.info-val { color: #fff; font-weight: 700; text-transform: uppercase; }
.info-paid   { color: #34d399; font-weight: 700; }
.info-pending{ color: #fbbf24; font-weight: 700; }
.info-void   { color: #a1a1aa; font-weight: 700; }

/* ── Info Internal: Bukti Pembayaran ───────────────────────────────
   Ditaruh di luar .receipt-body dan pakai gaya visual yang beda
   sengaja (bukan gaya struk monospace) supaya jelas kelihatan "ini
   bukan bagian dari struk" — baik secara kode maupun secara visual. */
.internal-proof-section {
  margin: 0 1.5rem;
  padding: 0.65rem 0.85rem;
  background: rgba(37,99,235,0.06);
  border: 1px dashed rgba(37,99,235,0.35);
  border-radius: 12px;
  font-family: 'Inter', sans-serif;
}
/* Header dobel sebagai tombol toggle — collapsed by default, jadi
   gak makan tempat di modal struk kecuali admin memang mau ngecek. */
.internal-proof-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  font-family: inherit;
}
.internal-proof-toggle-left { display: flex; align-items: center; gap: 0.5rem; }
.internal-proof-badge {
  font-size: 0.58rem;
  font-family: 'Oswald', sans-serif;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #93c5fd;
  background: rgba(37,99,235,0.15);
  border: 1px solid rgba(37,99,235,0.3);
  padding: 0.12rem 0.45rem;
  border-radius: 100px;
  flex-shrink: 0;
}
.internal-proof-title { font-size: 0.75rem; font-weight: 700; color: #fff; }
.internal-proof-chevron {
  color: rgba(255,255,255,0.35);
  font-size: 0.7rem;
  transition: transform 0.15s;
  flex-shrink: 0;
}
.internal-proof-chevron.open { transform: rotate(180deg); color: #93c5fd; }
.internal-proof-note {
  margin: 0.2rem 0 0;
  font-size: 0.6rem;
  color: rgba(255,255,255,0.3);
}
.internal-proof-body {
  margin-top: 0.65rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
}
.internal-proof-thumb-link { display: block; width: 100%; }
.internal-proof-thumb {
  width: 100%;
  max-height: 140px;
  object-fit: contain;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.08);
  cursor: zoom-in;
  background: #000;
}
.internal-proof-view-link {
  font-family: monospace;
  font-size: 0.68rem;
  color: #60a5fa;
  text-decoration: underline;
}
.internal-proof-view-link:hover { color: #93c5fd; }

/* Banner bukti bayar di modal Lunasi — biar kasir cek dulu sebelum konfirmasi */
.pay-proof-banner {
  display: block;
  text-align: center;
  padding: 0.6rem 0.85rem;
  background: rgba(37,99,235,0.1);
  border: 1px solid rgba(37,99,235,0.3);
  border-radius: 10px;
  color: #93c5fd;
  font-family: monospace;
  font-size: 0.72rem;
  font-weight: 700;
  text-decoration: none;
  transition: background 0.15s;
}
.pay-proof-banner:hover { background: rgba(37,99,235,0.18); }

.modal-footer {
  padding: 1rem 1.25rem;
  border-top: 1px solid rgba(255,255,255,0.06);
  display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.6rem;
}
.btn-share {
  display: flex; align-items: center; justify-content: center; gap: 0.4rem;
  padding: 0.7rem; background: #16a34a; border: none;
  border-radius: 10px; color: #fff;
  font-family: 'Oswald', sans-serif; font-size: 0.7rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: background 0.15s;
}
.btn-share:hover:not(:disabled) { background: #15803d; }
.btn-share:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-print {
  display: flex; align-items: center; justify-content: center; gap: 0.4rem;
  padding: 0.7rem; background: #2563eb; border: none;
  border-radius: 10px; color: #fff;
  font-family: 'Oswald', sans-serif; font-size: 0.7rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: background 0.15s;
}
.btn-print:hover { background: #1d4ed8; }
.btn-close-modal {
  padding: 0.7rem; background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08); border-radius: 10px;
  color: rgba(255,255,255,0.5);
  font-family: 'Oswald', sans-serif; font-size: 0.7rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: all 0.15s;
}
.btn-close-modal:hover { background: rgba(255,255,255,0.08); color: #fff; }

.print-size-row {
  display: flex; align-items: center; justify-content: center; gap: 0.5rem;
  padding: 0 1.25rem 1rem;
}
.print-size-label {
  font-size: 0.62rem; color: rgba(255,255,255,0.3);
  font-family: 'Oswald', sans-serif; letter-spacing: 0.1em; text-transform: uppercase;
}
.print-size-btn {
  padding: 0.3rem 0.7rem; border-radius: 100px;
  border: 1px solid rgba(255,255,255,0.1); background: transparent;
  color: rgba(255,255,255,0.4); font-family: monospace; font-size: 0.68rem;
  cursor: pointer; transition: all 0.15s;
}
.print-size-btn:hover { border-color: rgba(255,255,255,0.3); color: #fff; }
.print-size-btn.active { background: rgba(37,99,235,0.15); border-color: #2563eb; color: #93c5fd; }

/* ── Pay Modal ───────────────────────────────────────────────────── */
.pay-modal-box {
  background: #0f0f0f;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 20px;
  width: 100%; max-width: 400px;
  overflow: hidden;
}
.pay-body { padding: 1.25rem 1.5rem; display: flex; flex-direction: column; gap: 1.1rem; }

.pay-customer {
  padding: 0.85rem 1rem;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 10px;
}
.pay-name { font-weight: 600; font-size: 0.9rem; margin: 0 0 0.2rem; }
.pay-phone { font-family: monospace; font-size: 0.75rem; color: rgba(255,255,255,0.35); margin: 0; }

.pay-total-strip {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.85rem 1rem;
  background: rgba(220,38,38,0.06);
  border: 1px solid rgba(220,38,38,0.15);
  border-radius: 10px;
}
.pay-total-label { font-size: 0.72rem; color: rgba(255,255,255,0.4); font-family: 'Oswald', sans-serif; letter-spacing: 0.1em; text-transform: uppercase; }
.pay-total-val { font-family: monospace; font-size: 1.15rem; font-weight: 800; color: #ef4444; }

.pay-section { display: flex; flex-direction: column; gap: 0.5rem; }
.pay-section-label { font-size: 0.6rem; font-family: 'Oswald', sans-serif; letter-spacing: 0.15em; text-transform: uppercase; color: rgba(255,255,255,0.3); }

.pay-method-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
.pay-method-btn {
  display: flex; align-items: center; justify-content: center; gap: 0.4rem;
  padding: 0.7rem; border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.02);
  color: rgba(255,255,255,0.4);
  font-family: 'Oswald', sans-serif; font-size: 0.75rem;
  letter-spacing: 0.08em; text-transform: uppercase;
  cursor: pointer; transition: all 0.15s;
}
.pay-method-btn:hover { border-color: rgba(255,255,255,0.2); color: rgba(255,255,255,0.7); }
.pay-method-btn.active { background: rgba(220,38,38,0.12); border-color: #dc2626; color: #fff; }
.method-btn-icon { font-size: 1rem; }

.pay-amount-input {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px;
  padding: 0.75rem 1rem;
  color: #fff;
  font-family: monospace; font-size: 1rem;
  outline: none; width: 100%;
  transition: border-color 0.15s;
}
.pay-amount-input::placeholder { color: rgba(255,255,255,0.15); }
.pay-amount-input:focus { border-color: rgba(220,38,38,0.4); }

.pay-split-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.3rem; }
.pay-add-row-btn {
  background: transparent; border: 1px dashed rgba(255,255,255,0.2); border-radius: 8px;
  color: rgba(255,255,255,0.5); font-family: 'Oswald', sans-serif; font-size: 0.62rem;
  letter-spacing: 0.08em; text-transform: uppercase; padding: 0.3rem 0.6rem; cursor: pointer;
  transition: all 0.15s;
}
.pay-add-row-btn:hover { border-color: rgba(220,38,38,0.5); color: #fff; }

.pay-split-row { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; }
.pay-method-grid-compact { grid-template-columns: 1fr 1fr; flex-shrink: 0; width: 140px; }
.pay-method-btn-sm { padding: 0.55rem 0.4rem; font-size: 0.62rem; }
.pay-split-input { flex: 1; padding: 0.55rem 0.75rem; font-size: 0.85rem; }
.pay-remove-row-btn {
  background: transparent; border: none; color: rgba(255,255,255,0.3);
  cursor: pointer; font-size: 0.9rem; flex-shrink: 0; padding: 0.2rem 0.4rem;
  transition: color 0.15s;
}
.pay-remove-row-btn:hover { color: #f87171; }

.pay-split-fill-btn {
  background: transparent; border: none; color: rgba(220,38,38,0.7);
  font-family: 'Oswald', sans-serif; font-size: 0.62rem; letter-spacing: 0.06em;
  text-decoration: underline; cursor: pointer; padding: 0.2rem 0; text-align: left;
}
.pay-split-fill-btn:hover { color: #dc2626; }

.change-box {
  display: flex; justify-content: space-between;
  padding: 0.6rem 0.85rem;
  border-radius: 8px; font-family: monospace; font-size: 0.8rem; font-weight: 700;
}
.change-ok  { background: rgba(34,197,94,0.08); border: 1px solid rgba(34,197,94,0.2); color: #4ade80; }
.change-err { background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.2); color: #f87171; }

.pay-confirm-btn {
  width: 100%; padding: 0.85rem;
  background: #dc2626; border: none; border-radius: 12px;
  color: #fff; font-family: 'Oswald', sans-serif;
  font-size: 0.8rem; letter-spacing: 0.12em; text-transform: uppercase;
  cursor: pointer; transition: background 0.15s; font-weight: 500;
}
.pay-confirm-btn:hover:not(:disabled) { background: #b91c1c; }
.pay-confirm-btn:disabled { opacity: 0.35; cursor: not-allowed; }

/* Modal hapus permanen — visual peringatan lebih tegas */
.delete-warning-box {
  padding: 0.85rem 1rem;
  background: rgba(220,38,38,0.08);
  border: 1px solid rgba(220,38,38,0.25);
  border-radius: 10px;
  font-size: 0.75rem;
  line-height: 1.55;
  color: rgba(255,255,255,0.75);
}
.delete-warning-box strong { color: #f87171; }
.delete-order-code {
  font-family: monospace;
  font-weight: 700;
  color: #fff;
  background: rgba(255,255,255,0.08);
  padding: 0.05rem 0.4rem;
  border-radius: 4px;
}
.delete-confirm-input { font-family: monospace; }
.delete-confirm-btn { background: #991b1b; }
.delete-confirm-btn:hover:not(:disabled) { background: #7f1d1d; }

/* ── Struk print (thermal) — disembunyikan di layar biasa ─────────── */
.print-receipt { display: none; }

/* ── Responsive ─────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .ao-root { padding: 1.5rem 1rem; }
  .ao-title { font-size: 1.4rem; }
  .ao-header { flex-direction: column; align-items: flex-start; gap: 0.75rem; }
  .control-bar { flex-direction: column; align-items: stretch; }
  .search-wrap { margin-left: 0; }
  .search-input { width: 100%; }
  .date-nav { width: 100%; justify-content: space-between; }
  .ao-summary { flex-wrap: wrap; }
  .summary-chip { flex: 1; min-width: 110px; border-bottom: 1px solid rgba(255,255,255,0.05); }
  .internal-proof-section { margin: 0 1rem; }
}
@media (max-width: 480px) {
  .ao-live { display: none; }
}

/* Hide number spinners */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
input[type="number"] { -moz-appearance: textfield; }
</style>

<!-- ── STYLE PRINT (global, tidak di-scope) ─────────────────────────
     Harus di luar <style scoped> karena selector "body *" butuh akses
     ke seluruh halaman, bukan cuma elemen di dalam komponen ini. -->
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
  /* Jaga-jaga: kalau suatu saat print CSS di atas berubah, blok
     internal proof tetap dipastikan tidak pernah ikut tercetak. */
  .internal-proof-section { display: none !important; }
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