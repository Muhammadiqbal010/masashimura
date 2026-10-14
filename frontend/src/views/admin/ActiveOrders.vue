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
          :class="{ 'is-on': paused }"
          :title="paused ? 'Pembaruan otomatis dijeda (klik untuk lanjutkan)' : 'Jeda pembaruan otomatis'"
          :aria-label="paused ? 'Lanjutkan pembaruan otomatis' : 'Jeda pembaruan otomatis'"
          :aria-pressed="paused"
          @click="togglePause"
        >
          <component :is="paused ? Play : Pause" :size="14" />
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

        <span class="adm-badge" :class="liveBadge.cls" role="status">
          <span class="adm-dot" :class="{ 'ao-pulse': liveBadge.pulse }"></span>
          {{ liveBadge.label }}
        </span>
      </div>
    </header>

    <!-- ── RINGKASAN HARI INI ──────────────────────────────────────── -->
    <section v-if="orders.length" class="ao-stats" aria-label="Ringkasan pesanan">
      <div class="ao-stat">
        <span class="ao-stat-label">Order aktif</span>
        <strong class="ao-stat-value">{{ summary.active }}</strong>
        <span class="ao-stat-hint">{{ summary.cancelled }} dibatalkan</span>
      </div>
      <div class="ao-stat" :class="{ 'is-alert': summary.unpaidCount > 0 }">
        <span class="ao-stat-label">Belum dibayar</span>
        <strong class="ao-stat-value">{{ formatPrice(summary.pending) }}</strong>
        <span class="ao-stat-hint">{{ summary.unpaidCount }} order</span>
      </div>
      <template v-if="isOwner">
        <div class="ao-stat ao-stat--cash">
          <span class="ao-stat-label">Cash</span>
          <strong class="ao-stat-value">{{ formatPrice(summary.cash) }}</strong>
        </div>
        <div class="ao-stat ao-stat--qris">
          <span class="ao-stat-label">QRIS</span>
          <strong class="ao-stat-value">{{ formatPrice(summary.qris) }}</strong>
        </div>
        <div class="ao-stat ao-stat--total">
          <span class="ao-stat-label">Terkumpul</span>
          <strong class="ao-stat-value">{{ formatPrice(summary.paid) }}</strong>
          <span class="ao-stat-hint">{{ summary.paidCount }} order lunas</span>
        </div>
      </template>
    </section>

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

      <div class="adm-search ao-search">
        <Search :size="14" class="adm-search-icon" aria-hidden="true" />
        <input
          ref="searchInput"
          v-model="searchQuery"
          type="search"
          class="adm-input"
          placeholder="Cari no. HP, nama, menu, atau no. order…"
          aria-label="Cari pesanan"
          aria-keyshortcuts="/"
          title="Tekan / untuk langsung mencari, Esc untuk menghapus"
          @keydown.esc="searchQuery = ''"
        />
        <button v-if="searchQuery" type="button" class="adm-search-clear" aria-label="Hapus pencarian" @click="searchQuery = ''">
          <X :size="14" />
        </button>
      </div>
    </div>

    <!-- ── FILTER STATUS + METODE + URUTAN ─────────────────────────── -->
    <div class="ao-filterbar">
      <div class="ao-scroll">
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
      </div>

      <div class="ao-filterbar-right">
        <div class="ao-scroll">
          <div class="adm-seg" role="group" aria-label="Filter metode bayar">
            <button
              v-for="m in methodTabs"
              :key="m.value"
              type="button"
              class="adm-seg-btn"
              :aria-pressed="methodFilter === m.value"
              @click="methodFilter = m.value"
            >{{ m.label }}</button>
          </div>
        </div>

        <div class="ao-scroll">
          <div class="adm-seg ao-sort" role="group" aria-label="Urutan daftar">
            <button type="button" class="adm-seg-btn" :aria-pressed="sortMode === 'newest'" @click="setSort('newest')">Terbaru</button>
            <button type="button" class="adm-seg-btn" :aria-pressed="sortMode === 'unpaid'" @click="setSort('unpaid')">Belum lunas dulu</button>
          </div>
        </div>

        <button
          v-if="isOwner"
          type="button"
          class="adm-btn adm-btn--ghost adm-btn--sm"
          :disabled="!filteredOrders.length"
          title="Unduh daftar yang sedang tampil sebagai CSV"
          @click="exportCsv"
        >
          <Download :size="13" /> Ekspor CSV
        </button>
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
          <p class="adm-empty-text">Ini bukan berarti tidak ada pesanan. Lihat keterangan di atas.</p>
        </template>
        <template v-else-if="orders.length">
          <div class="adm-empty-icon"><Search :size="22" /></div>
          <p class="adm-empty-title">Tidak ada pesanan yang cocok</p>
          <p class="adm-empty-text">Ubah kata kunci atau filter, lalu coba lagi.</p>
          <button type="button" class="adm-btn adm-btn--ghost adm-btn--sm" @click="resetFilters">Reset filter</button>
        </template>
        <template v-else>
          <div class="adm-empty-icon"><Receipt :size="22" /></div>
          <p class="adm-empty-title">Belum ada pesanan untuk {{ targetDateString }}</p>
          <p class="adm-empty-text">Pesanan baru muncul otomatis, tidak perlu refresh.</p>
        </template>
      </div>

      <!-- Daftar: tabel di desktop, kartu di layar kecil (satu markup, layout diatur CSS grid) -->
      <div v-else class="ao-list" role="table" aria-label="Daftar pesanan">
        <div class="ao-head" role="row">
          <span role="columnheader" class="ao-a-id">Order</span>
          <span role="columnheader" class="ao-a-cust">Customer</span>
          <span role="columnheader" class="ao-a-menu">Menu</span>
          <span role="columnheader" class="ao-a-bill">Tagihan</span>
          <span role="columnheader" class="ao-a-status">Status</span>
          <span role="columnheader" class="ao-a-time">Waktu</span>
          <span role="columnheader" class="ao-a-act">Aksi</span>
        </div>

        <div
          v-for="order in shownOrders"
          :key="order.id"
          class="ao-row"
          :class="{
            'ao-row--unpaid': isUnpaid(order),
            'ao-row--stale': isUnpaid(order) && isToday && isStale(order),
            'ao-row--cancelled': order.status === 'cancelled',
            'ao-row--new': newIds.has(order.id),
          }"
          role="row"
          tabindex="0"
          :aria-label="`Buka struk order ${order.order_number || order.id}`"
          @click="openOrderModal(order)"
          @keydown.enter.self="openOrderModal(order)"
        >
          <div class="ao-a-id ao-id" role="cell">
            #{{ order.id }}
            <span v-if="newIds.has(order.id)" class="ao-new-tag">Baru</span>
          </div>

          <div class="ao-a-cust" role="cell">
            <template v-if="order.customer_name || order.customer_phone">
              <span class="ao-cust-name">{{ order.customer_name || order.customer_phone }}</span>
              <span v-if="order.customer_name && order.customer_phone" class="ao-cust-phone">{{ order.customer_phone }}</span>
            </template>
            <span v-else class="adm-badge ao-guest">Guest</span>
          </div>

          <div class="ao-a-menu ao-menu-cell" role="cell" :title="itemsTitle(order)">
            <ul v-if="order.items?.length" class="ao-items">
              <li v-for="(item, i) in itemsPreview(order)" :key="i">
                <span class="ao-items-qty">{{ item.quantity }}×</span>
                <span class="ao-items-name">{{ item.menu_name }}</span>
              </li>
            </ul>
            <span v-else class="ao-items-empty">Tidak ada item</span>
            <span v-if="itemsMore(order)" class="ao-items-more">+{{ itemsMore(order) }} menu lainnya</span>
          </div>

          <div class="ao-a-bill ao-bill" role="cell">
            <span class="ao-price">{{ formatPrice(order.total_price) }}</span>
            <span class="ao-method" :class="`ao-method--${methodTone(order.payment_method)}`">
              <component :is="methodIcon(order.payment_method)" :size="13" aria-hidden="true" />
              {{ methodLabel(order.payment_method) }}
            </span>
          </div>

          <div class="ao-a-status" role="cell">
            <div class="ao-status">
              <span class="adm-badge" :class="orderBadge(order).cls">{{ orderBadge(order).label }}</span>
              <span v-if="order.status !== 'cancelled'" class="adm-badge" :class="payBadge(order).cls">{{ payBadge(order).label }}</span>
            </div>
          </div>

          <div class="ao-a-time ao-time" role="cell">
            <span>{{ formatTime(order.created_at) }}</span>
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
          </div>

          <div class="ao-a-act ao-actions" role="cell" @click.stop>
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
              v-if="canRemind(order)"
              type="button"
              class="adm-icon-btn adm-icon-btn--bordered"
              title="Ingatkan pembayaran via WhatsApp"
              aria-label="Ingatkan pembayaran via WhatsApp"
              @click="remindViaWA(order)"
            >
              <MessageCircle :size="14" />
            </button>

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
        </div>

        <div v-if="hiddenCount > 0" class="ao-more">
          <span>Menampilkan {{ shownOrders.length }} dari {{ visibleOrders.length }} order</span>
          <button type="button" class="adm-btn adm-btn--ghost adm-btn--sm" @click="pageLimit += PAGE_SIZE">
            <ChevronDown :size="14" /> Tampilkan {{ Math.min(PAGE_SIZE, hiddenCount) }} lagi
          </button>
        </div>
      </div>
    </section>

    <!-- ── MODAL STRUK ─────────────────────────────────────────────── -->
    <AdminModal v-model="isModalOpen" :title="`Struk ${selectedOrder?.order_number || ''}`" size="sm" back-close>
      <div v-if="selectedOrder" class="rcpt">
        <div class="rcpt-head">
          <img :src="logoUrl" alt="Masashimura" class="rcpt-logo" />
          <p class="rcpt-address">{{ STORE_ADDRESS }}</p>
        </div>

        <hr class="rcpt-div" />

        <div class="rcpt-rows">
          <div class="rcpt-row">
            <span>No. Nota</span>
            <b class="rcpt-copy" role="button" tabindex="0" title="Klik untuk menyalin" @click="copyText(selectedOrder.order_number, 'No. nota')" @keydown.enter="copyText(selectedOrder.order_number, 'No. nota')">{{ selectedOrder.order_number }}</b>
          </div>
          <div class="rcpt-row"><span>Kasir</span><b>{{ selectedOrder.kasir_name || kasirName }}</b></div>
          <div class="rcpt-row"><span>Waktu</span><b>{{ formatFullDateTime(selectedOrder.created_at) }}</b></div>
          <div v-if="customerLabel" class="rcpt-row"><span>Pelanggan</span><b>{{ customerLabel }}</b></div>
        </div>

        <div v-if="selectedOrder.status === 'cancelled'" class="rcpt-cancel">
          <p class="rcpt-cancel-title"><AlertTriangle :size="13" /> Order dibatalkan</p>
          <div class="rcpt-row"><span>Alasan</span><b>{{ selectedOrder.cancel_reason_display || '—' }}</b></div>
          <div v-if="selectedOrder.cancel_note" class="rcpt-row"><span>Catatan</span><b>{{ selectedOrder.cancel_note }}</b></div>
          <div class="rcpt-row"><span>Oleh</span><b>{{ selectedOrder.cancelled_by || '—' }}</b></div>
          <div class="rcpt-row"><span>Waktu</span><b>{{ formatFullDateTime(selectedOrder.cancelled_at) }}</b></div>
        </div>

        <hr class="rcpt-div" />

        <p class="rcpt-heading">Detail pesanan</p>
        <div v-for="(line, idx) in receiptLines" :key="idx" class="rcpt-item">
          <template v-if="line.type === 'bundle'">
            <div class="rcpt-item-main">
              <span class="rcpt-name"><b>Paket {{ line.name }}</b></span>
              <span class="rcpt-sub">{{ formatPrice(line.total) }}</span>
            </div>
            <div v-for="(c, ci) in line.contents" :key="ci" class="rcpt-note" style="font-style:normal">{{ c.quantity }}× {{ c.menu_name }}</div>
          </template>
          <template v-else>
            <div class="rcpt-item-main">
              <span class="rcpt-qty">{{ line.item.quantity }}×</span>
              <span class="rcpt-name">{{ line.item.menu_name }}</span>
              <span class="rcpt-sub">{{ formatPrice(line.item.price * line.item.quantity) }}</span>
            </div>
            <div v-if="line.item.notes" class="rcpt-note">{{ line.item.notes }}</div>
          </template>
        </div>

        <hr class="rcpt-div" />

        <div class="rcpt-rows">
          <div class="rcpt-row"><span>Subtotal</span><span>{{ formatPrice(computedSubtotal) }}</span></div>
          <div v-if="num(selectedOrder.promo_discount_amount) > 0" class="rcpt-row rcpt-discount">
            <span>Diskon promo</span><span>-{{ formatPrice(selectedOrder.promo_discount_amount) }}</span>
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
          <div class="rcpt-row">
            <span>Metode</span>
            <b class="rcpt-method" :class="`rcpt-method--${methodTone(selectedOrder.payment_method)}`">{{ methodLabel(selectedOrder.payment_method, true) }}</b>
          </div>
          <template v-if="selectedOrder.payment_method === 'mixed' && selectedOrder.payments?.length">
            <div v-for="p in selectedOrder.payments" :key="p.id" class="rcpt-row rcpt-split">
              <span>— {{ p.method_display }}</span><b>{{ formatPrice(p.amount) }}</b>
            </div>
          </template>
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
         Sengaja putih & fixed: gambar yang dikirim ke customer harus sama
         apa pun tema admin yang dipakai kasir. -->
    <div
      ref="receiptRef"
      aria-hidden="true"
      style="
        position: fixed; left: -9999px; top: 0;
        width: 400px; background-color: #ffffff;
        color: #000000; padding: 24px;
        font-family: 'Courier New', monospace;
        font-size: 13px; font-weight: 700; line-height: 1.6;
      "
    >
      <div style="text-align:center; margin-bottom:16px;">
        <img :src="logoUrl" alt="Logo" style="height:60px; margin:0 auto 8px; object-fit:contain; display:block;" />
        <div style="font-size:12px; color:#27272a; font-weight:700;">{{ STORE_ADDRESS }}</div>
        <div style="border-top:2px dashed #000; margin-top:12px;"></div>
      </div>

      <div style="font-size:13px; margin-bottom:12px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:2px;"><span>No. Nota :</span><span style="font-weight:900;">{{ selectedOrder?.order_number }}</span></div>
        <div style="display:flex; justify-content:space-between; margin-bottom:2px;"><span>Kasir :</span><span>{{ selectedOrder?.kasir_name || kasirName }}</span></div>
        <div style="display:flex; justify-content:space-between; margin-bottom:2px;"><span>Waktu :</span><span>{{ formatFullDateTime(selectedOrder?.created_at) }}</span></div>
        <div v-if="customerLabel" style="display:flex; justify-content:space-between;"><span>Pelanggan :</span><span>{{ customerLabel }}</span></div>
      </div>

      <div style="border-top:1px dashed #000; margin-bottom:12px;"></div>

      <div style="margin-bottom:12px;">
        <div style="font-weight:900; font-size:13px; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Detail Pesanan:</div>
        <div v-for="(line, idx) in receiptLines" :key="idx" style="margin-bottom:8px;">
          <template v-if="line.type === 'bundle'">
            <div style="display:flex; justify-content:space-between; gap:12px; font-weight:700;"><span>Paket {{ line.name }}</span><span style="white-space:nowrap;">{{ formatPrice(line.total) }}</span></div>
            <div v-for="(c, ci) in line.contents" :key="ci" style="font-size:12px; padding-left:12px;">{{ c.quantity }}x {{ c.menu_name }}</div>
          </template>
          <template v-else>
            <div style="display:flex; justify-content:space-between; gap:12px;"><span>{{ line.item.quantity }}x {{ line.item.menu_name }}</span><span style="white-space:nowrap;">{{ formatPrice(line.item.price * line.item.quantity) }}</span></div>
            <div v-if="line.item.notes" style="font-size:12px; padding-left:12px; font-style:italic; color:#000;">📋 "{{ line.item.notes }}"</div>
          </template>
        </div>
      </div>

      <div style="border-top:1px dashed #000; margin-bottom:12px;"></div>

      <div style="font-size:13px; margin-bottom:12px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:4px;"><span>Subtotal</span><span>{{ formatPrice(computedSubtotal) }}</span></div>
        <div v-if="num(selectedOrder?.promo_discount_amount) > 0" style="display:flex; justify-content:space-between; color:#c20000; margin-bottom:4px;"><span>Diskon Promo</span><span>-{{ formatPrice(selectedOrder?.promo_discount_amount) }}</span></div>
        <div style="border-top:1px dashed #000; margin:8px 0;"></div>
        <div style="display:flex; justify-content:space-between; font-size:16px; font-weight:900; margin-bottom:6px;"><span>TOTAL AKHIR</span><span style="color:#c20000;">{{ formatPrice(selectedOrder?.total_price) }}</span></div>
        <div v-if="num(selectedOrder?.amount_paid) > 0" style="display:flex; justify-content:space-between; margin-bottom:2px;"><span>Bayar</span><span>{{ formatPrice(selectedOrder?.amount_paid) }}</span></div>
        <div v-if="num(selectedOrder?.change_amount) > 0" style="display:flex; justify-content:space-between;"><span>Kembalian</span><span style="color:#047857; font-weight:900;">{{ formatPrice(selectedOrder?.change_amount) }}</span></div>
      </div>

      <div style="border-top:2px dashed #000; margin-bottom:12px;"></div>

      <div style="background-color:#f4f4f5; padding:12px 14px; border-radius:12px; border:1.5px solid #52525b; font-size:12px; line-height:2; margin-bottom:12px;">
        <div>• Metode Bayar : <span style="font-weight:900; text-transform:uppercase;">{{ methodLabel(selectedOrder?.payment_method, true) }}</span></div>
        <div>• Kasir : <span style="font-weight:900;">{{ selectedOrder?.kasir_name || kasirName }}</span></div>
        <div>• Status : <span :style="selectedOrder?.payment_status === 'paid' ? 'color:#047857; font-weight:900;' : (selectedOrder?.payment_status === 'void' ? 'color:#52525b; font-weight:900;' : 'color:#b45309; font-weight:900;')">{{ payStatusText(selectedOrder) }}</span></div>
      </div>

      <div style="text-align:center; font-size:12px; padding-top:4px; font-weight:900;">Terima kasih sudah makan di Masashimura! 🙏</div>
    </div>

    <!-- ── STRUK PRINT (thermal 58mm/80mm), hanya tampil saat print ── -->
    <div ref="printRef" class="print-receipt" :style="{ width: printPaperWidth + 'mm' }">
      <div class="pr-center">
        <img :src="receiptLogo" alt="Masashimura" class="pr-logo" />
        <div class="pr-addr">{{ STORE_ADDRESS }}</div>
      </div>
      <div class="pr-divider pr-divider-strong"></div>
      <div class="pr-row"><span>No. Nota</span><span>{{ selectedOrder?.order_number }}</span></div>
      <div class="pr-row"><span>Kasir</span><span>{{ selectedOrder?.kasir_name || kasirName }}</span></div>
      <div class="pr-row"><span>Waktu</span><span>{{ formatFullDateTime(selectedOrder?.created_at) }}</span></div>
      <div v-if="customerLabel" class="pr-row"><span>Pelanggan</span><span>{{ customerLabel }}</span></div>
      <div class="pr-divider"></div>
      <div class="pr-heading">Detail Pesanan</div>
      <div v-for="(line, idx) in receiptLines" :key="'pr' + idx" class="pr-item">
        <template v-if="line.type === 'bundle'">
          <div class="pr-item-row" style="font-weight:700">
            <span>Paket {{ line.name }}</span>
            <span>{{ formatPrice(line.total) }}</span>
          </div>
          <div v-for="(c, ci) in line.contents" :key="ci" class="pr-note" style="font-style:normal">{{ c.quantity }}x {{ c.menu_name }}</div>
        </template>
        <template v-else>
          <div class="pr-item-row">
            <span>{{ line.item.quantity }}x {{ line.item.menu_name }}</span>
            <span>{{ formatPrice(line.item.price * line.item.quantity) }}</span>
          </div>
          <div v-if="line.item.notes" class="pr-note">"{{ line.item.notes }}"</div>
        </template>
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
    <AdminModal v-model="isPayModalOpen" :title="`Lunasi ${selectedPayOrder?.order_number || ''}`" size="md" :persistent="isPaying" back-close>
      <template v-if="selectedPayOrder">
        <div class="ao-person">
          <p class="ao-person-name">{{ selectedPayOrder.customer_name || 'Walk In' }}</p>
          <p class="ao-person-phone">{{ selectedPayOrder.customer_phone || 'Tanpa nomor' }}</p>
        </div>

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
              <button type="button" class="adm-seg-btn ao-pm-cash" :aria-pressed="row.method === 'cash'" @click="row.method = 'cash'">
                <Banknote :size="13" /> Cash
              </button>
              <button type="button" class="adm-seg-btn ao-pm-qris" :aria-pressed="row.method === 'qris_manual'" @click="row.method = 'qris_manual'">
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
    <AdminModal v-model="isCancelModalOpen" :title="`Batalkan ${selectedCancelOrder?.order_number || ''}`" size="sm" :persistent="isCancelling" back-close>
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
            placeholder="Cth: kelebihan input qty, salah pencet menu"
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
    <AdminModal v-model="isDeleteModalOpen" title="Hapus permanen" size="sm" :persistent="isDeleting" back-close @close="closeDeleteModal">
      <template v-if="selectedDeleteOrder">
        <div class="ao-person">
          <p class="ao-person-name">{{ selectedDeleteOrder.order_number }} · {{ selectedDeleteOrder.customer_name || 'Walk In' }}</p>
          <p class="ao-person-phone">{{ selectedDeleteOrder.customer_phone || 'Tanpa nomor' }} · {{ formatPrice(selectedDeleteOrder.total_price) }}</p>
        </div>

        <p class="adm-alert" role="alert">
          <AlertTriangle :size="16" class="ao-error-icon" aria-hidden="true" />
          <span>
            Order ini akan <strong>dihapus permanen</strong> dari database{{ selectedDeleteOrder.payment_status === 'paid' ? ', termasuk data transaksi yang sudah LUNAS' : '' }}.
            Tindakan ini <strong>tidak bisa dibatalkan</strong>.
          </span>
        </p>
        <ul class="ao-del-effects">
          <li>Semua menu, jumlah, dan total di nota ini dihapus (laporan penjualan ikut berubah).</li>
          <li>Pembayaran ikut dihapus: metode, nominal, dan pembagian bayar.</li>
          <li v-if="selectedDeleteOrder.items?.some((i) => i.is_point_redemption)">Poin yang dipakai untuk tukar reward <strong>dikembalikan</strong> ke pelanggan.</li>
          <li v-if="selectedDeleteOrder.customer_phone">Poin yang didapat dari order ini ditarik kembali, begitu juga total belanja dan jumlah order pelanggan.</li>
          <li v-if="selectedDeleteOrder.promo_discount_amount > 0">Kuota promo yang terpakai dikembalikan.</li>
        </ul>

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
  Search, X, ChevronLeft, ChevronRight, ChevronDown, Printer, Send, Plus, Trash2,
  Banknote, QrCode, Shuffle, RefreshCw, AlertTriangle, Receipt, Bell, BellOff,
  Pause, Play, Download, MessageCircle,
} from 'lucide-vue-next'
import { orderAPI, apiClient } from '@/api'
import { toast } from 'vue-sonner'
import { useAuthStore } from '@/stores/auth'
import html2canvas from 'html2canvas'
import AdminModal from '@/components/ui/admin/Adminmodal.vue'
import { groupReceiptLines } from '@/utils/receiptLines'
// Di-import (bukan "/src/assets/…") supaya path-nya ikut di-hash & tetap jalan di build production.
import logoUrl from '@/assets/masashimura-logo.png'

const STORE_ADDRESS = 'Jl. Pintu Air No. 48, depan Pengadilan Bekasi, Bekasi, Jawa Barat'

const authStore = useAuthStore()
const kasirName = computed(() => authStore.user?.name || authStore.user?.username || 'Staff')

// Role owner: cuma role ini yang boleh hapus order permanen, lihat nominal uang masuk, dan ekspor CSV.
// NOTE: ini cuma menyembunyikan tombol di UI. Endpoint DELETE di backend
// WAJIB juga dicek role owner-nya: request langsung ke API bisa melewati tombol ini.
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
const PAGE_SIZE = 30
const currentDate = ref(new Date())
const isLoading = ref(true)       // true sampai jawaban pertama (sukses/gagal) untuk tanggal yang dipilih
const isRefreshing = ref(false)
const loadError = ref('')         // pesan kegagalan memuat; kosong = baik-baik saja
const lastUpdated = ref('')
const orders = ref([])
const searchQuery = ref('')
const statusFilter = ref('all')
const methodFilter = ref('all')
const searchInput = ref(null)
const now = ref(Date.now())
const paused = ref(false)
const pageLimit = ref(PAGE_SIZE)
const followToday = ref(true)   // true = ikut berganti hari otomatis saat lewat tengah malam

const num = (v) => parseFloat(v) || 0

// ── Tanggal ─────────────────────────────────────────────────────────
const toDateString = (d) => {
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}
const targetDateString = computed(() => toDateString(currentDate.value))
const isToday = computed(() => targetDateString.value === toDateString(new Date(now.value)))
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
  followToday.value = toDateString(d) === toDateString(new Date())
  resetForNewDate()
  fetchActiveOrders({ force: true })
}
const jumpToDate = (value) => {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value || '')) return
  const [y, m, d] = value.split('-').map(Number)
  currentDate.value = new Date(y, m - 1, d)
  followToday.value = toDateString(currentDate.value) === toDateString(new Date())
  resetForNewDate()
  fetchActiveOrders({ force: true })
}
const goToday = () => {
  currentDate.value = new Date()
  followToday.value = true
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
  } catch { /* browser menolak audio: sorotan visual tetap jalan */ }
}
const toggleSound = () => {
  soundOn.value = !soundOn.value
  writePref(SOUND_KEY, soundOn.value ? '1' : '0')
  if (soundOn.value) playBeep()   // sekaligus contoh bunyinya, dan "membuka" audio browser
}

// Jawaban pertama untuk suatu tanggal hanya jadi patokan (baseline), bukan "order baru".
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
  if (!status) return 'Tidak bisa terhubung ke server. Cek internet, atau server backend sedang mati / restart.'
  if (status === 401 || status === 403) return `Sesi login habis atau akun tidak punya akses (${status}). Coba login ulang.`
  if (status >= 500) return `Server error (${status}). Data pesanan tidak hilang, masalahnya di backend. Cek log server; kalau baru deploy, pastikan migrasi database sudah dijalankan.`
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
const togglePause = () => {
  paused.value = !paused.value
  if (!paused.value) fetchActiveOrders({ force: true })
}

const liveBadge = computed(() => {
  if (loadError.value) return { cls: 'adm-badge--red', label: 'Gagal memuat · mencoba lagi', pulse: false }
  if (paused.value) return { cls: 'adm-badge--amber', label: 'Dijeda', pulse: false }
  return { cls: 'adm-badge--green', label: 'Live · tiap 5 detik', pulse: true }
})

// Pintasan: "/" untuk langsung mengetik di kolom cari (seperti GitHub / Gmail).
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
let clockTimer = null
const onVisibility = () => { if (!document.hidden && !paused.value) fetchActiveOrders() }
onMounted(() => {
  applyPageSize()
  buildBlackLogo()
  fetchActiveOrders()
  // Tab yang tidak dilihat atau sedang dijeda tidak perlu menembak server tiap 5 detik.
  pollingTimer = setInterval(() => { if (!document.hidden && !paused.value) fetchActiveOrders() }, POLL_MS)
  // Label "x mnt lalu" tetap berjalan walau polling dijeda.
  clockTimer = setInterval(() => {
    now.value = Date.now()
    // Lewat tengah malam: pindah ke hari baru, jangan terus menampilkan kemarin.
    if (followToday.value && toDateString(new Date()) !== targetDateString.value) goToday()
  }, 30000)
  document.addEventListener('visibilitychange', onVisibility)
  window.addEventListener('keydown', onKeydown)
})
onUnmounted(() => {
  if (pollingTimer) clearInterval(pollingTimer)
  if (clockTimer) clearInterval(clockTimer)
  clearTimeout(flashTimer)
  document.removeEventListener('visibilitychange', onVisibility)
  window.removeEventListener('keydown', onKeydown)
  document.title = baseTitle
  try { audioCtx?.close() } catch { /* abaikan */ }
})

// ── Metode bayar ────────────────────────────────────────────────────
const isQrisMethod = (m) => ['gateway', 'qris_manual', 'qris'].includes(m)
const methodIcon = (m) => (isQrisMethod(m) ? QrCode : (m === 'mixed' ? Shuffle : Banknote))
const methodLabel = (m, full = false) => {
  if (isQrisMethod(m)) return 'QRIS'
  if (m === 'mixed') return full ? 'Split Bayar' : 'Split'
  return m || 'Cash'
}
// Warna pembeda: cash = kuning, QRIS = biru, split = netral
const methodTone = (m) => (isQrisMethod(m) ? 'qris' : (m === 'mixed' ? 'mixed' : 'cash'))

// ── Pencarian + filter + urutan ─────────────────────────────────────
const isUnpaid = (o) => o.status !== 'cancelled' && o.payment_status !== 'paid' && o.payment_status !== 'void'

const searchedOrders = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  const byMethod = methodFilter.value === 'all'
    ? orders.value
    : orders.value.filter((o) => methodTone(o.payment_method) === methodFilter.value)
  if (!q) return byMethod
  return byMethod.filter((o) =>
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
const methodTabs = [
  { value: 'all', label: 'Semua metode' },
  { value: 'cash', label: 'Cash' },
  { value: 'qris', label: 'QRIS' },
  { value: 'mixed', label: 'Split' },
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
// Hari ramai bisa ratusan order: render bertahap supaya halaman tetap ringan.
const shownOrders = computed(() => visibleOrders.value.slice(0, pageLimit.value))
const hiddenCount = computed(() => Math.max(visibleOrders.value.length - pageLimit.value, 0))
watch([searchQuery, statusFilter, methodFilter, sortMode, targetDateString], () => { pageLimit.value = PAGE_SIZE })

const resetFilters = () => { searchQuery.value = ''; statusFilter.value = 'all'; methodFilter.value = 'all' }

// ── Ringkasan nominal ───────────────────────────────────────────────
// Pecah satu order lunas jadi bagian QRIS & Cash. Untuk split bayar, QRIS dijumlah dari
// baris pembayarannya, sisanya dianggap cash (supaya uang kembalian tidak dihitung dua kali).
const splitPaid = (o) => {
  const total = num(o.total_price)
  if (o.payment_method === 'mixed' && o.payments?.length) {
    const qris = o.payments.reduce((sum, p) => {
      const m = p.method || p.payment_method || ''
      return sum + (isQrisMethod(m) || /qris/i.test(p.method_display || '') ? num(p.amount) : 0)
    }, 0)
    const q = Math.min(qris, total)
    return { qris: q, cash: total - q }
  }
  return isQrisMethod(o.payment_method) ? { qris: total, cash: 0 } : { qris: 0, cash: total }
}
const summary = computed(() => {
  const s = { paid: 0, pending: 0, cash: 0, qris: 0, active: 0, cancelled: 0, paidCount: 0, unpaidCount: 0 }
  for (const o of orders.value) {
    if (o.status === 'cancelled') { s.cancelled++; continue }
    s.active++
    if (o.payment_status === 'paid') {
      s.paid += num(o.total_price)
      s.paidCount++
      const part = splitPaid(o)
      s.cash += part.cash
      s.qris += part.qris
    } else if (o.payment_status !== 'void') {
      s.pending += num(o.total_price)
      s.unpaidCount++
    }
  }
  return s
})

// Jumlah order belum lunas di judul tab browser: kelihatan walau admin sedang buka tab lain.
let baseTitle = typeof document !== 'undefined' ? document.title : ''
const unpaidTotal = computed(() => orders.value.filter(isUnpaid).length)
watch([unpaidTotal, isToday], ([n, today]) => {
  document.title = n > 0 && today ? `(${n}) ${baseTitle}` : baseTitle
})

// ── Ringkasan menu di daftar ────────────────────────────────────────
const ITEMS_PREVIEW = 2
// Baris hasil pecahan paket (menu & paket sama, beda harga satuan) digabung jadi satu baris.
const mergedItems = (o) => {
  const out = []
  const seen = {}
  for (const it of o.items || []) {
    if (!it.bundle_name) { out.push(it); continue }
    const key = `${it.bundle_name}|${it.menu_name}`
    if (seen[key] !== undefined) out[seen[key]] = { ...out[seen[key]], quantity: out[seen[key]].quantity + it.quantity }
    else seen[key] = out.push({ ...it }) - 1
  }
  return out
}
const itemsPreview = (o) => mergedItems(o).slice(0, ITEMS_PREVIEW)
const itemsMore = (o) => Math.max(mergedItems(o).length - ITEMS_PREVIEW, 0)
const itemsTitle = (o) => mergedItems(o).map((i) => `${i.quantity}× ${i.menu_name}`).join('\n')

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
  : { cls: 'adm-badge--amber', label: 'Belum bayar' }
const payStatusText = (o) =>
  o?.payment_status === 'paid' ? 'LUNAS' : (o?.payment_status === 'void' ? 'BATAL' : 'BELUM BAYAR')

const canPay = (o) => o.payment_status !== 'paid' && o.status !== 'cancelled' && o.payment_method !== 'gateway'

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

// ── WhatsApp: ingatkan pembayaran ───────────────────────────────────
const normalizePhone = (raw) => {
  const digits = String(raw || '').replace(/\D/g, '')
  if (!digits) return ''
  if (digits.startsWith('0')) return '62' + digits.slice(1)
  if (digits.startsWith('8')) return '62' + digits
  return digits
}
const canRemind = (o) => isUnpaid(o) && !!normalizePhone(o.customer_phone)
const remindViaWA = (o) => {
  const phone = normalizePhone(o.customer_phone)
  if (!phone) return
  const who = o.customer_name ? ` ${o.customer_name}` : ''
  const text = `Halo${who}, pesanan ${o.order_number || '#' + o.id} di Masashimura sebesar ${formatPrice(o.total_price)} belum dibayar. Mohon konfirmasinya ya, terima kasih 🙏`
  window.open(`https://wa.me/${phone}?text=${encodeURIComponent(text)}`, '_blank', 'noopener')
}

// ── Salin teks ──────────────────────────────────────────────────────
const copyText = async (text, label = 'Teks') => {
  if (!text) return
  try {
    await navigator.clipboard.writeText(String(text))
    toast.success(`${label} disalin`)
  } catch {
    toast.error('Tidak bisa menyalin. Izinkan akses clipboard di browser.')
  }
}

// ── Ekspor CSV (daftar yang sedang tampil) ──────────────────────────
// Sel yang diawali = + - @ diberi tanda ' supaya tidak dieksekusi sebagai rumus di Excel.
const csvCell = (v) => {
  let s = String(v ?? '')
  if (/^[=+\-@]/.test(s)) s = `'${s}`
  return `"${s.replace(/"/g, '""')}"`
}
const exportCsv = () => {
  const rows = [['No. Nota', 'Waktu', 'Customer', 'No. HP', 'Menu', 'Total', 'Metode', 'Status order', 'Status bayar']]
  for (const o of visibleOrders.value) {
    rows.push([
      o.order_number || o.id,
      formatFullDateTime(o.created_at),
      o.customer_name || '',
      o.customer_phone || '',
      (o.items || []).map((i) => `${i.quantity}x ${i.menu_name}`).join('; '),
      num(o.total_price),
      methodLabel(o.payment_method, true),
      orderBadge(o).label,
      o.status === 'cancelled' ? '-' : payBadge(o).label,
    ])
  }
  const csv = '\uFEFF' + rows.map((r) => r.map(csvCell).join(',')).join('\r\n')
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  const a = document.createElement('a')
  a.href = url
  a.download = `order-masashimura-${targetDateString.value}.csv`
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
  toast.success(`${visibleOrders.value.length} order diekspor`)
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

const receiptLines = computed(() => groupReceiptLines(selectedOrder.value?.items))

const computedSubtotal = computed(() => {
  const items = selectedOrder.value?.items || []
  if (items.length) return items.reduce((sum, item) => sum + parseFloat(item.price) * parseInt(item.quantity || 1), 0)
  return num(selectedOrder.value?.subtotal || selectedOrder.value?.total_price)
})

// Nama pelanggan di struk: nama → no. HP → kosong (baris disembunyikan, tanpa tulisan "Guest" / "-")
const customerLabel = computed(() =>
  selectedOrder.value?.customer_name || selectedOrder.value?.customer_phone || ''
)

// ── Logo struk print ────────────────────────────────────────────────
// Struk WA pakai logo asli (merah-kuning). Struk print pakai versi HITAM
// karena kertas thermal cuma bisa hitam-putih. Dibuat otomatis dari logo asli.
const receiptLogo = ref(logoUrl)
const buildBlackLogo = () => {
  const img = new Image()
  img.onload = () => {
    try {
      const c = document.createElement('canvas')
      c.width = img.naturalWidth
      c.height = img.naturalHeight
      const ctx = c.getContext('2d')
      ctx.drawImage(img, 0, 0)
      const d = ctx.getImageData(0, 0, c.width, c.height)
      const px = d.data

      // Logo PNG transparan atau punya background solid? Cek piksel pojok kiri atas.
      const hasAlpha = px[3] < 250

      for (let i = 0; i < px.length; i += 4) {
        if (hasAlpha) {
          px[i] = px[i + 1] = px[i + 2] = 0
        } else {
          const lum = 0.299 * px[i] + 0.587 * px[i + 1] + 0.114 * px[i + 2]
          const v = lum > 200 ? 255 : 0
          px[i] = px[i + 1] = px[i + 2] = v
          px[i + 3] = 255
        }
      }
      ctx.putImageData(d, 0, 0)
      receiptLogo.value = c.toDataURL('image/png')
    } catch { /* gagal convert: tetap pakai logo asli */ }
  }
  img.src = logoUrl
}

// ── Cetak thermal ───────────────────────────────────────────────────
const printRef = ref(null)
const PAPER_KEY = 'masashimura-print-width'
const readPaper = () => (Number(readPref(PAPER_KEY, 80)) === 58 ? 58 : 80)
const printPaperWidth = ref(readPaper())

// @page tidak bisa pakai CSS variable → set ukuran halaman cetak secara dinamis
const applyPageSize = () => {
  let tag = document.getElementById('thermal-page-style')
  if (!tag) {
    tag = document.createElement('style')
    tag.id = 'thermal-page-style'
    document.head.appendChild(tag)
  }
  tag.textContent = `@page { size: ${printPaperWidth.value}mm auto; margin: 0; }`
}

// Memilih ukuran kertas TIDAK langsung mencetak; ukuran diingat untuk cetak berikutnya.
const setPaper = (w) => {
  printPaperWidth.value = w
  writePref(PAPER_KEY, w)
  applyPageSize()
}
const printReceipt = () => {
  if (!selectedOrder.value) return
  applyPageSize()
  // Jeda singkat biar lebar & isi struk sempat re-render sebelum dialog print muncul
  setTimeout(() => window.print(), 300)
}

// ── Kirim struk via WA ──────────────────────────────────────────────
// Capture cuma dari #receiptRef: bukti pembayaran memang tidak pernah
// dirender di node itu, jadi otomatis tidak ikut ke gambar untuk customer.
const receiptRef = ref(null)
const isCapturing = ref(false)
const canvasToBlob = (canvas) => new Promise((resolve) => canvas.toBlob(resolve, 'image/png'))

const shareReceiptAsImage = async () => {
  if (!receiptRef.value || !selectedOrder.value) return
  isCapturing.value = true
  try {
    await new Promise((r) => setTimeout(r, 200))
    const canvas = await html2canvas(receiptRef.value, { backgroundColor: '#ffffff', scale: 2, useCORS: true })
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
      setTimeout(() => URL.revokeObjectURL(url), 1000)   // jangan dicabut seketika: unduhan bisa gagal
      const phone = normalizePhone(order.customer_phone)
      const caption = encodeURIComponent('Bukti Pembelian di Masashimura 🙏')
      setTimeout(() => window.open(phone ? `https://wa.me/${phone}?text=${caption}` : `https://wa.me/?text=${caption}`, '_blank', 'noopener'), 500)
      toast.info('Gambar diunduh. Lampirkan ke WhatsApp secara manual jika perlu.')
    }
  } catch (err) {
    console.error(err)
    toast.error('Gagal membuat gambar struk')
  } finally {
    isCapturing.value = false
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
  { value: 'wrong_input', label: 'Salah input' },
  { value: 'customer_cancel', label: 'Pelanggan batal' },
  { value: 'out_of_stock', label: 'Stok habis' },
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
    const { data } = await apiClient.delete(`/orders/${selectedDeleteOrder.value.id}/`)
    // Server mengembalikan ringkasan (poin dikembalikan, promo, dll) di `detail`.
    toast.success(data?.detail || `Order ${selectedDeleteOrder.value.order_number} dihapus permanen`, { duration: 8000 })
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
.ao-page { max-width: 87.5rem; }

/* ── Header ──────────────────────────────────────────────────────── */
.ao-head-actions { display: flex; align-items: center; flex-wrap: wrap; gap: 0.5rem; }
.ao-head-actions .adm-icon-btn.is-on { color: var(--accent-text); border-color: var(--line-accent); background: var(--tint-accent); }
.ao-pulse { animation: ao-pulse 2s ease-in-out infinite; }
@keyframes ao-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
.ao-spin { animation: ao-spin 0.8s linear infinite; }
@keyframes ao-spin { to { transform: rotate(360deg); } }

/* ── Kartu ringkasan ─────────────────────────────────────────────── */
.ao-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(9.5rem, 1fr)); gap: 0.6rem; }
.ao-stat {
  display: flex; flex-direction: column; gap: 0.15rem; min-width: 0;
  padding: 0.75rem 0.9rem;
  border: 1px solid var(--border); border-radius: var(--r-md);
  background: var(--surface-2);
}
.ao-stat-label { font-size: 0.7rem; font-weight: 600; color: var(--text-dim); }
.ao-stat-value { font-family: var(--font-mono); font-size: 1.05rem; font-weight: 800; color: var(--text); overflow-wrap: anywhere; }
.ao-stat-hint { font-size: 0.72rem; color: var(--text-faint); }
.ao-stat.is-alert { border-color: var(--line-accent); background: var(--tint-accent); }
.ao-stat.is-alert .ao-stat-value { color: var(--red-soft); }
.ao-stat--cash { box-shadow: inset 3px 0 0 #eab308; }
.ao-stat--qris { box-shadow: inset 3px 0 0 #3b82f6; }
.ao-stat--total { box-shadow: inset 3px 0 0 var(--green); }
@media (max-width: 480px) { .ao-stats { grid-template-columns: 1fr 1fr; } }

/* ── Toolbar ─────────────────────────────────────────────────────── */
.ao-toolbar { justify-content: space-between; }
.ao-date { display: flex; align-items: center; flex-wrap: wrap; gap: 0.4rem; }
.ao-date-input { width: auto; min-width: 9.5rem; cursor: pointer; }
/* flex-basis 16rem hanya berlaku saat toolbar berbaris (desktop). */
.ao-toolbar .ao-search { flex: 1 1 16rem; max-width: 26rem; }
@media (max-width: 720px) {
  .ao-toolbar { flex-direction: column; align-items: stretch; }
  .ao-date { justify-content: space-between; flex-wrap: nowrap; }
  .ao-date-input { flex: 1; min-width: 0; }
  /* PENYEBAB BUG MOBILE: di kolom, flex-basis berubah jadi TINGGI (16rem). Kunci ke auto. */
  .ao-toolbar .ao-search { flex: 0 0 auto; width: 100%; max-width: none; }
}
@media (max-width: 480px) { .ao-hide-xs { display: none; } }

/* ── Filter ──────────────────────────────────────────────────────── */
.ao-filterbar { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.6rem 1rem; }
.ao-filterbar-right { display: flex; align-items: center; flex-wrap: wrap; gap: 0.6rem; }
/* Grup tombol yang kepanjangan di HP digeser ke samping, bukan dipatahkan. */
.ao-scroll { max-width: 100%; overflow-x: auto; scrollbar-width: none; }
.ao-scroll::-webkit-scrollbar { display: none; }
.ao-scroll .adm-seg { width: max-content; }
@media (max-width: 720px) {
  .ao-filterbar, .ao-filterbar-right { flex-direction: column; align-items: stretch; width: 100%; }
}

.ao-count {
  min-width: 1.25rem; padding: 0 0.35rem; border-radius: 99px;
  background: rgb(var(--ink) / 0.1);
  font-family: var(--font-mono); font-size: 0.72rem; line-height: 1.35rem; text-align: center;
}
.adm-seg-btn[aria-pressed='true'] .ao-count { background: rgb(255 255 255 / 0.22); }
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

/* ── Daftar: satu markup, dua layout ─────────────────────────────── */
.ao-list { display: flex; flex-direction: column; }

.ao-head,
.ao-row {
  display: grid;
  grid-template-columns: 5.5rem minmax(9rem, 1.1fr) minmax(11rem, 1.6fr) 9rem 7.5rem 6.5rem auto;
  grid-template-areas: 'id cust menu bill status time act';
  align-items: center;
  column-gap: 1rem;
  padding: 0.85rem 1.1rem;
}
.ao-a-id { grid-area: id; }
.ao-a-cust { grid-area: cust; min-width: 0; }
.ao-a-menu { grid-area: menu; min-width: 0; }
.ao-a-bill { grid-area: bill; }
.ao-a-status { grid-area: status; }
.ao-a-time { grid-area: time; }
.ao-a-act { grid-area: act; }

.ao-head {
  padding-block: 0.65rem;
  border-bottom: 1px solid var(--border);
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
  color: var(--text-faint);
}
.ao-head .ao-a-bill { text-align: right; }
.ao-head .ao-a-status, .ao-head .ao-a-time { text-align: center; }
.ao-head .ao-a-act { text-align: right; }

.ao-row { border-bottom: 1px solid var(--border); cursor: pointer; transition: background 0.15s; }
.ao-row:last-of-type { border-bottom: 0; }
.ao-row:hover { background: var(--surface-hover); }
.ao-row:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; background: var(--surface-hover); }

.ao-id { font-family: var(--font-mono); font-weight: 700; color: var(--accent-text); white-space: nowrap; }
.ao-new-tag { display: inline-block; margin-left: 0.4rem; padding: 0.05rem 0.4rem; border-radius: 99px; background: var(--green); color: #fff; font-family: var(--font-body); font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em; vertical-align: middle; }

/* Belum lunas: disorot; makin lama makin tegas */
.ao-row--unpaid { background: var(--tint-accent); box-shadow: inset 3px 0 0 var(--accent); }
.ao-row--unpaid:hover { background: var(--surface-hover); }
.ao-row--stale { box-shadow: inset 5px 0 0 var(--accent); }

/* Dibatalkan: diredupkan, tombol aksi tetap jelas */
.ao-row--cancelled > :not(.ao-a-act) { opacity: 0.55; }
.ao-row--cancelled .ao-price { text-decoration: line-through; }

/* Order baru masuk: berkedip sekali dari hijau ke warna asli */
.ao-row--new { animation: ao-flash 2.4s ease-out 1; }
@keyframes ao-flash { 0% { background-color: var(--tint-green); } }

/* Customer */
.ao-cust-name { display: block; font-weight: 600; color: var(--text); overflow-wrap: anywhere; }
.ao-cust-phone { display: block; font-family: var(--font-mono); font-size: 0.7rem; color: var(--text-faint); }
.ao-guest { padding-block: 0.1rem; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; }

/* Menu */
.ao-items { display: flex; flex-direction: column; gap: 0.15rem; margin: 0; padding: 0; list-style: none; }
.ao-items li { display: flex; gap: 0.4rem; font-size: 0.8rem; line-height: 1.35; min-width: 0; }
.ao-items-qty { flex-shrink: 0; font-family: var(--font-mono); font-weight: 700; color: var(--accent-text); }
.ao-items-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text); }
.ao-items-more { display: inline-block; margin-top: 0.25rem; padding: 0.05rem 0.5rem; border-radius: 99px; background: rgb(var(--ink) / 0.08); font-size: 0.72rem; font-weight: 600; color: var(--text-dim); }
.ao-items-empty { color: var(--text-faint); font-size: 0.78rem; }

/* Tagihan */
.ao-bill { display: flex; flex-direction: column; align-items: flex-end; gap: 0.3rem; }
.ao-price { font-family: var(--font-mono); font-weight: 700; color: var(--amber-soft); white-space: nowrap; }
.ao-method {
  display: inline-flex; align-items: center; gap: 0.3rem;
  padding: 0.12rem 0.55rem;
  border: 1px solid transparent; border-radius: 99px;
  font-size: 0.7rem; font-weight: 700; text-transform: capitalize;
  color: var(--text-dim);
}
.ao-method--cash  { color: #facc15; background: rgb(234 179 8 / 0.14);  border-color: rgb(234 179 8 / 0.45); }
.ao-method--qris  { color: #60a5fa; background: rgb(59 130 246 / 0.14); border-color: rgb(59 130 246 / 0.45); }
.ao-method--mixed { color: var(--text-dim); background: rgb(var(--ink) / 0.08); border-color: var(--border-strong); }
:global(html[data-admin-theme='light']) .ao-method--cash { color: #a16207; background: rgb(234 179 8 / 0.18); }
:global(html[data-admin-theme='light']) .ao-method--qris { color: #1d4ed8; background: rgb(59 130 246 / 0.12); }

/* Status */
.ao-status { display: inline-flex; flex-direction: column; align-items: center; gap: 0.3rem; }
.ao-a-status { display: flex; justify-content: center; }

/* Waktu */
.ao-time { display: flex; flex-direction: column; align-items: center; font-family: var(--font-mono); color: var(--text-dim); white-space: nowrap; }
.ao-age { margin-top: 2px; font-family: var(--font-body); font-size: 0.72rem; color: var(--text-dim); }
.ao-age.is-old { font-weight: 700; color: var(--red-soft); }
.ao-late { margin-top: 2px; font-family: var(--font-body); font-size: 0.72rem; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; color: var(--amber-soft); }

/* Aksi */
.ao-actions { display: flex; align-items: center; justify-content: flex-end; gap: 0.4rem; white-space: nowrap; }

/* Tombol "tampilkan lagi" */
.ao-more { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; padding: 0.8rem 1.1rem; border-top: 1px solid var(--border); font-size: 0.75rem; color: var(--text-dim); }

/* ── Layout kartu (tablet & HP) ──────────────────────────────────── */
@media (max-width: 1100px) {
  .ao-head { display: none; }
  .ao-list { gap: 0.6rem; padding: 0.6rem; }
  .ao-row {
    grid-template-columns: minmax(0, 1fr) auto;
    grid-template-areas:
      'id    time'
      'cust  cust'
      'menu  menu'
      'bill  status'
      'act   act';
    row-gap: 0.55rem;
    padding: 0.85rem 0.95rem;
    border: 1px solid var(--border); border-radius: var(--r-md);
    background: var(--surface-2);
  }
  .ao-row:last-of-type { border-bottom: 1px solid var(--border); }
  .ao-row--unpaid { border-color: var(--line-accent); }
  .ao-a-time { flex-direction: row; align-items: baseline; gap: 0.5rem; justify-self: end; }
  .ao-age, .ao-late { margin-top: 0; }
  .ao-bill { flex-direction: row; align-items: center; flex-wrap: wrap; gap: 0.5rem; }
  .ao-status { flex-direction: row; justify-self: end; }
  .ao-a-status { justify-content: flex-end; }
  .ao-items-name { white-space: normal; }
  .ao-actions { flex-wrap: wrap; justify-content: stretch; padding-top: 0.6rem; border-top: 1px dashed var(--border); }
  .ao-actions .adm-btn { flex: 1; min-height: 44px; }
  .ao-actions .adm-icon-btn { min-width: 44px; min-height: 44px; }
  .ao-more { border-top: 0; padding-inline: 0.4rem; }
}

/* ── Footer modal struk ──────────────────────────────────────────── */
.ao-foot { display: flex; align-items: center; flex-wrap: wrap; gap: 0.6rem; width: 100%; }
.ao-paper { display: flex; align-items: center; gap: 0.5rem; }
.ao-paper-label { font-size: 0.72rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-faint); }
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
.rcpt-address { margin: 0; font-size: 0.72rem; color: var(--text-faint); }
.rcpt-div { margin: 0.85rem 0; border: 0; border-top: 1px dashed var(--border-strong); }
.rcpt-rows { display: flex; flex-direction: column; gap: 0.25rem; }
.rcpt-row { display: flex; justify-content: space-between; gap: 1rem; }
.rcpt-row > :last-child { text-align: right; }
.rcpt-row b { color: var(--text); font-weight: 600; }
.rcpt-copy { cursor: copy; text-decoration: underline dotted; text-underline-offset: 3px; }
.rcpt-heading { margin: 0 0 0.6rem; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-dim); }
.rcpt-item { margin-bottom: 0.5rem; }
.rcpt-item-main { display: flex; gap: 0.4rem; }
.rcpt-qty { min-width: 1.8rem; color: var(--text-faint); }
.rcpt-name { flex: 1; color: var(--text); }
.rcpt-sub { font-weight: 600; }
.rcpt-note { padding-left: 2.2rem; font-size: 0.72rem; font-style: italic; color: var(--amber-soft); }
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
.rcpt-row b.rcpt-method--cash { color: #facc15; }
.rcpt-row b.rcpt-method--qris { color: #60a5fa; }
:global(html[data-admin-theme='light']) .rcpt-row b.rcpt-method--cash { color: #a16207; }
:global(html[data-admin-theme='light']) .rcpt-row b.rcpt-method--qris { color: #1d4ed8; }
.rcpt-cancel { display: flex; flex-direction: column; gap: 0.25rem; margin-top: 0.75rem; padding: 0.7rem 0.85rem; border: 1px solid var(--line-accent); border-radius: var(--r-md); background: var(--tint-accent); }
.rcpt-cancel-title { display: flex; align-items: center; gap: 0.35rem; margin: 0 0 0.25rem; font-weight: 700; color: var(--red-soft); }

/* ── Modal lunasi / batalkan / hapus ─────────────────────────────── */
.ao-person { padding: 0.8rem 1rem; border: 1px solid var(--border); border-radius: var(--r-md); background: var(--surface-2); }
.ao-person-name { margin: 0 0 0.15rem; font-size: 0.9rem; font-weight: 600; color: var(--text); overflow-wrap: anywhere; }
.ao-person-phone { margin: 0; font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-dim); }

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

.adm-seg-btn.ao-pm-cash[aria-pressed='true'] { background: #eab308; color: #1c1917; }
.adm-seg-btn.ao-pm-qris[aria-pressed='true'] { background: #2563eb; color: #fff; }

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

/* ── Struk print (thermal): disembunyikan di layar biasa ──────────── */
.print-receipt { display: none; }

/* Hormati pengaturan "kurangi gerakan" di perangkat */
@media (prefers-reduced-motion: reduce) {
  .ao-pulse, .ao-spin, .ao-row--new { animation: none; }
}
</style>

<!-- ── STYLE PRINT (global, tidak di-scope) ─────────────────────────
     Harus di luar <style scoped> karena selector "body *" butuh akses
     ke seluruh halaman. Struk cetak selalu putih-hitam (kertas), tidak ikut tema. -->
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
    font-size: 12.5px;
    font-weight: 700;
    line-height: 1.55;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
}

.pr-center { text-align: center; margin-bottom: 4px; }
.pr-logo { display: block; height: 52px; max-width: 100%; margin: 0 auto 4px; object-fit: contain; }
.pr-addr { font-size: 11px; margin-top: 3px; line-height: 1.4; color: #000; font-weight: 700; }

.pr-divider { border-top: 1px dashed #000; margin: 8px 0; height: 0; }
.pr-divider-strong { border-top: 2px solid #000; margin: 8px 0; height: 0; }

.pr-row { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 3px; font-size: 12.5px; }
.pr-sub { color: #000; }
.pr-upper { text-transform: uppercase; font-weight: 900; }

.pr-total {
  font-weight: 900;
  font-size: 15px;
  padding: 5px 0;
  margin-top: 2px;
  border-top: 1px dashed #000;
  border-bottom: 1px dashed #000;
}

.pr-heading {
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 6px;
  font-size: 12px;
  color: #000;
}
.pr-item { margin-bottom: 5px; }
.pr-item-row { display: flex; justify-content: space-between; gap: 10px; font-size: 12.5px; }
.pr-note { font-size: 11px; font-style: italic; padding-left: 12px; color: #000; margin-top: 1px; }

.pr-footer {
  text-align: center;
  font-size: 12px;
  font-weight: 900;
  margin-top: 4px;
  letter-spacing: 0.02em;
}

.ao-del-effects { margin: 0.75rem 0 1rem; padding-left: 1.1rem; font-size: 0.78rem; line-height: 1.5; color: var(--text-dim, inherit); list-style: disc; }
.ao-del-effects li + li { margin-top: 0.2rem; }
</style>