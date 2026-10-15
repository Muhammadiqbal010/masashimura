<template>
  <div class="fr-root">

    <!-- ── HEADER + TOOLBAR ───────────────────────────────────────── -->
    <header class="fr-header">
      <div class="fr-heading">
        <h1 class="fr-title">Laporan Keuangan</h1>
        <p class="fr-subtitle">{{ viewModeLabel }}</p>
      </div>

      <div class="fr-toolbar">
        <div class="mode-switch" role="group" aria-label="Periode laporan">
          <button
            v-for="m in viewModes"
            :key="m.key"
            type="button"
            class="mode-btn"
            :class="{ active: viewMode === m.key }"
            :aria-pressed="viewMode === m.key"
            @click="switchMode(m.key)"
          >{{ m.label }}</button>
        </div>

        <!-- HARIAN -->
        <template v-if="viewMode === 'daily'">
          <div class="date-nav">
            <button type="button" class="nav-btn" aria-label="Hari sebelumnya" @click="changeDate(-1)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M15 18l-6-6 6-6"/></svg>
            </button>
            <input
              type="date"
              class="nav-date"
              :value="targetDateString"
              :max="todayString"
              aria-label="Pilih tanggal"
              @change="jumpToDate($event.target.value)"
            />
            <button type="button" class="nav-btn" aria-label="Hari berikutnya" :disabled="isToday" @click="changeDate(1)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M9 18l6-6-6-6"/></svg>
            </button>
          </div>
          <button v-if="!isToday" type="button" class="today-btn" @click="goToday">Hari ini</button>
        </template>

        <!-- BULANAN -->
        <template v-if="viewMode === 'monthly'">
          <div class="date-nav">
            <button type="button" class="nav-btn" aria-label="Bulan sebelumnya" @click="changeMonth(-1)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M15 18l-6-6 6-6"/></svg>
            </button>
            <span class="nav-current">{{ monthNames[selectedMonth - 1] }} {{ selectedYear }}</span>
            <button type="button" class="nav-btn" aria-label="Bulan berikutnya" @click="changeMonth(1)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M9 18l6-6-6-6"/></svg>
            </button>
          </div>
          <select v-model.number="selectedYear" class="nav-select" aria-label="Pilih tahun" @change="onMonthlyYearChange">
            <option v-for="y in yearsAvailable" :key="y" :value="y">{{ y }}</option>
          </select>
        </template>

        <!-- TAHUNAN -->
        <template v-if="viewMode === 'yearly'">
          <div class="date-nav">
            <button type="button" class="nav-btn" aria-label="Tahun sebelumnya" @click="changeYear(-1)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M15 18l-6-6 6-6"/></svg>
            </button>
            <span class="nav-current">Tahun {{ selectedYear }}</span>
            <button type="button" class="nav-btn" aria-label="Tahun berikutnya" @click="changeYear(1)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M9 18l6-6-6-6"/></svg>
            </button>
          </div>
          <select v-model.number="selectedYear" class="nav-select" aria-label="Pilih tahun" @change="onYearlyYearChange">
            <option v-for="y in yearsAvailable" :key="y" :value="y">{{ y }}</option>
          </select>
        </template>
      </div>
    </header>

    <!-- ── KPI ────────────────────────────────────────────────────── -->
    <section class="summary-grid" aria-label="Ringkasan keuangan">
      <div class="s-card s-green">
        <div class="s-top">
          <span class="s-icon-wrap ic-green">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M23 6l-9.5 9.5-5-5L1 18"/><path d="M17 6h6v6"/></svg>
          </span>
          <span class="s-label">Total pendapatan</span>
        </div>
        <div class="s-value">{{ formatRp(summaryCards.revenue) }}</div>
        <div class="s-note">Order lunas terkonfirmasi</div>
      </div>

      <div class="s-card s-amber">
        <div class="s-top">
          <span class="s-icon-wrap ic-amber">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/></svg>
          </span>
          <span class="s-label">Total pengeluaran</span>
        </div>
        <div class="s-value">{{ formatRp(summaryCards.expenses) }}</div>
        <div class="s-note">Cash + QRIS</div>
      </div>

      <div class="s-card" :class="summaryCards.net_profit >= 0 ? 's-surplus' : 's-defisit'">
        <div class="s-top">
          <span class="s-icon-wrap" :class="summaryCards.net_profit >= 0 ? 'ic-green' : 'ic-red'">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M12 3v18M5 8l7-5 7 5M5 8v8a2 2 0 002 2h10a2 2 0 002-2V8"/></svg>
          </span>
          <span class="s-label">Laba bersih</span>
          <span class="s-badge" :class="summaryCards.net_profit >= 0 ? 'badge-up' : 'badge-down'">
            {{ summaryCards.net_profit >= 0 ? '▲ Surplus' : '▼ Defisit' }}
          </span>
        </div>
        <div class="s-value" :class="summaryCards.net_profit >= 0 ? 'val-green' : 'val-red'">
          {{ formatRp(summaryCards.net_profit) }}
        </div>
        <div class="s-note">Pendapatan dikurangi pengeluaran</div>
      </div>
    </section>

    <!-- ── BODY ───────────────────────────────────────────────────── -->
    <div class="fr-shell" :class="{ 'has-aside': hasAside }">

      <!-- ═══ KOLOM UTAMA ═══ -->
      <main class="fr-main">

        <!-- HARIAN -->
        <template v-if="viewMode === 'daily'">
          <section class="card table-card">
            <div class="card-head border-b">
              <div class="card-titles">
                <h3 class="card-title">Log pengeluaran</h3>
                <p class="card-sub">{{ dailyExpensesList.length }} entri pada tanggal ini</p>
              </div>
              <div class="card-head-actions">
                <button type="button" class="jump-btn" @click="scrollToForm">+ Catat</button>
              </div>
            </div>

            <div class="table-scroll">
              <table class="data-table daily-table">
                <colgroup>
                  <col />
                  <col class="col-method" />
                  <col class="col-amount" />
                  <col class="col-actions" />
                </colgroup>
                <thead>
                  <tr>
                    <th>Keterangan</th>
                    <th>Metode</th>
                    <th class="th-right">Nominal</th>
                    <th class="th-center">Aksi</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="isLoadingDaily && !dailyExpensesList.length">
                    <td colspan="4" class="empty-cell">
                      <div class="spinner-sm"></div>
                      <p>Memuat pengeluaran…</p>
                    </td>
                  </tr>
                  <tr
                    v-for="exp in dailyExpensesList"
                    :key="exp.id"
                    class="data-row"
                    :class="{ 'row-editing': editingId === exp.id }"
                  >
                    <td class="td-desc">{{ exp.description }}</td>
                    <td class="td-method">
                      <span class="method-badge" :class="exp.payment_method === 'qris' ? 'mb-qris' : 'mb-cash'">{{ methodLabel(exp.payment_method) }}</span>
                    </td>
                    <td class="td-right td-amount">−Rp {{ formatNumber(exp.amount) }}</td>
                    <td class="td-center">
                      <div class="row-actions">
                        <button type="button" class="edit-btn" @click="startEdit(exp)">Edit</button>
                        <button type="button" class="delete-btn" @click="askDelete(exp)">Hapus</button>
                      </div>
                    </td>
                  </tr>
                  <tr v-if="!isLoadingDaily && !dailyExpensesList.length">
                    <td colspan="4" class="empty-cell">
                      <div class="empty-icon" aria-hidden="true">📋</div>
                      <p class="empty-title">Belum ada pengeluaran di tanggal ini</p>
                      <p class="empty-hint">Catat lewat form “Input pengeluaran”.</p>
                    </td>
                  </tr>
                </tbody>
                <tfoot v-if="dailyExpensesList.length">
                  <tr class="total-row">
                    <td>Total pengeluaran</td>
                    <td></td>
                    <td class="td-right td-exp">Rp {{ formatNumber(summaryCards.expenses) }}</td>
                    <td></td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </section>

          <!-- Pengeluaran per metode -->
          <section class="card">
            <div class="card-head border-b">
              <div class="card-titles">
                <h3 class="card-title">Pengeluaran per metode</h3>
                <p class="card-sub">Perbandingan Cash dan QRIS</p>
              </div>
            </div>
            <div class="method-split">
              <div v-for="row in methodBreakdown" :key="row.key" class="split-item">
                <div class="split-top">
                  <span class="method-badge" :class="row.key === 'qris' ? 'mb-qris' : 'mb-cash'">{{ row.label }}</span>
                  <span class="split-amount">Rp {{ formatNumber(row.amount) }}</span>
                </div>
                <div class="split-track" role="presentation">
                  <div class="split-fill" :class="row.key === 'qris' ? 'sf-qris' : 'sf-cash'" :style="{ width: row.pct + '%' }"></div>
                </div>
                <span class="split-pct">{{ row.pct }}% dari total</span>
              </div>
            </div>
          </section>
        </template>

        <!-- BULANAN / TAHUNAN -->
        <template v-else>
          <section class="card chart-card">
            <div class="card-head border-b">
              <div class="card-titles">
                <h3 class="card-title">
                  {{ viewMode === 'monthly'
                    ? `Per hari — ${monthNames[selectedMonth - 1]} ${selectedYear}`
                    : `Per bulan — Tahun ${selectedYear}` }}
                </h3>
                <p class="card-sub">Arahkan kursor ke batang untuk melihat nominal</p>
              </div>
              <div class="chart-legend" aria-hidden="true">
                <span class="legend-item"><span class="legend-dot ld-green"></span>Pendapatan</span>
                <span class="legend-item"><span class="legend-dot ld-amber"></span>Pengeluaran</span>
              </div>
            </div>

            <div v-if="isLoadingChart" class="chart-loading">
              <div class="spinner-sm"></div>
              <span>Memuat grafik…</span>
            </div>

            <div v-else class="chart-area">
              <div class="chart-frame">
                <div class="y-axis" aria-hidden="true">
                  <span>{{ formatCompact(chartMax) }}</span>
                  <span>{{ formatCompact(chartMax / 2) }}</span>
                  <span>0</span>
                </div>
                <div
                  class="bar-chart"
                  :class="{ 'bar-chart-yearly': viewMode === 'yearly' }"
                  role="img"
                  aria-label="Grafik batang pendapatan dan pengeluaran. Arahkan kursor ke batang untuk melihat nominal."
                >
                  <div
                    v-for="d in (viewMode === 'monthly' ? monthlyData : yearlyData)"
                    :key="viewMode === 'monthly' ? d.date : d.month"
                    class="bar-col"
                    :title="`${viewMode === 'monthly' ? d.date : d.month_name}\nPendapatan: Rp ${formatNumber(d.revenue)}\nPengeluaran: Rp ${formatNumber(d.expenses)}`"
                  >
                    <div class="bar-pair">
                      <div class="bar bar-rev" :style="{ height: barPct(d.revenue, chartMax) + '%' }"></div>
                      <div class="bar bar-exp" :style="{ height: barPct(d.expenses, chartMax) + '%' }"></div>
                    </div>
                    <span class="bar-label">{{ viewMode === 'monthly' ? d.day : d.month_name.slice(0, 3) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section class="card table-card" :class="{ 'is-refreshing': isLoadingChart }">
            <div class="card-head border-b">
              <div class="card-titles">
                <h3 class="card-title">{{ viewMode === 'monthly' ? `Detail harian — ${monthNames[selectedMonth - 1]} ${selectedYear}` : `Rekap tahunan — ${selectedYear}` }}</h3>
                <p class="card-sub">{{ viewMode === 'monthly' ? `${monthlyDataFiltered.length} hari ada transaksi` : `${yearlyActiveCount} bulan ada transaksi` }}</p>
              </div>
            </div>
            <div class="table-scroll">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>{{ viewMode === 'monthly' ? 'Tanggal' : 'Bulan' }}</th>
                    <th class="th-right">Pendapatan</th>
                    <th class="th-right">Pengeluaran</th>
                    <th class="th-right">Laba bersih</th>
                  </tr>
                </thead>
                <tbody v-if="viewMode === 'monthly'">
                  <tr v-for="d in monthlyDataFiltered" :key="d.date" class="data-row">
                    <td class="td-mono">{{ d.date }}</td>
                    <td class="td-right td-rev">{{ d.revenue > 0 ? 'Rp ' + formatNumber(d.revenue) : '—' }}</td>
                    <td class="td-right td-exp">{{ d.expenses > 0 ? 'Rp ' + formatNumber(d.expenses) : '—' }}</td>
                    <td class="td-right" :class="d.net_profit >= 0 ? 'td-pos' : 'td-neg'">{{ formatRp(d.net_profit) }}</td>
                  </tr>
                  <tr v-if="!monthlyDataFiltered.length">
                    <td colspan="4" class="empty-cell">
                      <div class="empty-icon" aria-hidden="true">📭</div>
                      <p class="empty-title">Tidak ada data untuk bulan ini</p>
                    </td>
                  </tr>
                  <tr v-if="monthlyDataFiltered.length" class="total-row">
                    <td>Total bulan</td>
                    <td class="td-right td-rev">Rp {{ formatNumber(summaryCards.revenue) }}</td>
                    <td class="td-right td-exp">Rp {{ formatNumber(summaryCards.expenses) }}</td>
                    <td class="td-right" :class="summaryCards.net_profit >= 0 ? 'td-pos' : 'td-neg'">{{ formatRp(summaryCards.net_profit) }}</td>
                  </tr>
                </tbody>
                <tbody v-else>
                  <tr
                    v-for="d in yearlyData"
                    :key="d.month"
                    class="data-row"
                    :class="{ 'row-empty': d.revenue === 0 && d.expenses === 0 }"
                  >
                    <td class="td-month">{{ d.month_name }}</td>
                    <td class="td-right td-rev">{{ d.revenue > 0 ? 'Rp ' + formatNumber(d.revenue) : '—' }}</td>
                    <td class="td-right td-exp">{{ d.expenses > 0 ? 'Rp ' + formatNumber(d.expenses) : '—' }}</td>
                    <td class="td-right" :class="d.net_profit >= 0 ? 'td-pos' : 'td-neg'">
                      {{ (d.revenue > 0 || d.expenses > 0) ? formatRp(d.net_profit) : '—' }}
                    </td>
                  </tr>
                  <tr class="total-row">
                    <td>Total {{ selectedYear }}</td>
                    <td class="td-right td-rev">Rp {{ formatNumber(summaryCards.revenue) }}</td>
                    <td class="td-right td-exp">Rp {{ formatNumber(summaryCards.expenses) }}</td>
                    <td class="td-right" :class="summaryCards.net_profit >= 0 ? 'td-pos' : 'td-neg'">{{ formatRp(summaryCards.net_profit) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </template>
      </main>

      <!-- ═══ SAMPING (form / insight) ═══ -->
      <aside v-if="hasAside" class="fr-aside">

        <!-- Form pengeluaran (harian) -->
        <section v-if="viewMode === 'daily'" ref="formCard" class="card form-card" :class="{ 'is-editing': editingId }">
          <div class="card-head border-b">
            <div class="card-titles">
              <h3 class="card-title">{{ editingId ? 'Edit pengeluaran' : 'Input pengeluaran' }}</h3>
              <p class="card-sub">{{ editingId ? 'Ubah catatan yang dipilih' : `Untuk tanggal ${targetDateString}` }}</p>
            </div>
            <button v-if="editingId" type="button" class="link-btn" @click="cancelEdit">Batal</button>
          </div>

          <form class="expense-form" @submit.prevent="submitExpense">
            <div class="field">
              <label class="field-label" for="exp-desc">Keterangan</label>
              <input
                id="exp-desc"
                ref="descInput"
                v-model="expenseForm.description"
                type="text"
                autocomplete="off"
                maxlength="120"
                placeholder="Beli daging, gas 3 kg, dll."
                required
                class="field-input"
              />
              <div v-if="!editingId" class="chip-row" role="group" aria-label="Keterangan cepat">
                <button v-for="q in quickDescs" :key="q" type="button" class="chip" @click="pickQuick(q)">{{ q }}</button>
              </div>
            </div>

            <div class="field">
              <label class="field-label" for="exp-amount">Nominal (Rp)</label>
              <input
                id="exp-amount"
                v-model.number="expenseForm.amount"
                type="number"
                inputmode="numeric"
                placeholder="150000"
                required
                min="1"
                class="field-input font-mono"
              />
              <span class="field-hint" :class="{ 'is-on': amountPreview }">{{ amountPreview || 'Ketik angka tanpa titik' }}</span>
            </div>

            <div class="field">
              <span class="field-label" id="method-label">Dibayar via</span>
              <div class="method-switch" role="group" aria-labelledby="method-label">
                <button
                  v-for="m in paymentMethods"
                  :key="m.key"
                  type="button"
                  class="method-btn"
                  :class="{ active: expenseForm.payment_method === m.key }"
                  :aria-pressed="expenseForm.payment_method === m.key"
                  @click="expenseForm.payment_method = m.key"
                >{{ m.label }}</button>
              </div>
            </div>

            <button type="submit" :disabled="isSubmittingExpense || !canSubmit" class="submit-btn">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path v-if="editingId" d="M20 6L9 17l-5-5"/><path v-else d="M12 5v14M5 12h14"/></svg>
              {{ isSubmittingExpense ? 'Menyimpan…' : (editingId ? 'Simpan perubahan' : 'Catat pengeluaran') }}
            </button>
          </form>
        </section>

        <!-- Insight bulanan -->
        <section v-if="viewMode === 'monthly' && monthlyStats" class="card">
          <div class="card-head border-b">
            <div class="card-titles">
              <h3 class="card-title">Insight bulan ini</h3>
            </div>
          </div>
          <div class="insight-body">
            <div class="insight-row">
              <span class="insight-label">Hari berjualan</span>
              <span class="insight-value">{{ monthlyStats.activeDays }} hari</span>
            </div>
            <div class="insight-row">
              <span class="insight-label">Rata-rata pendapatan / hari</span>
              <span class="insight-value">Rp {{ formatNumber(monthlyStats.avgRevenue) }}</span>
            </div>
            <div class="insight-row">
              <span class="insight-label">Hari terbaik</span>
              <span class="insight-value">{{ monthlyStats.best.date }} · Rp {{ formatNumber(monthlyStats.best.revenue) }}</span>
            </div>
          </div>
        </section>

        <!-- Insight tahunan -->
        <section v-if="viewMode === 'yearly' && yearlyStats" class="card">
          <div class="card-head border-b">
            <div class="card-titles">
              <h3 class="card-title">Insight tahun ini</h3>
            </div>
          </div>
          <div class="insight-body">
            <div class="insight-row">
              <span class="insight-label">Bulan aktif</span>
              <span class="insight-value">{{ yearlyStats.activeMonths }} bulan</span>
            </div>
            <div class="insight-row">
              <span class="insight-label">Rata-rata pendapatan / bulan</span>
              <span class="insight-value">Rp {{ formatNumber(yearlyStats.avgRevenue) }}</span>
            </div>
            <div class="insight-row">
              <span class="insight-label">Bulan terbaik</span>
              <span class="insight-value">{{ yearlyStats.best.month_name }} · Rp {{ formatNumber(yearlyStats.best.revenue) }}</span>
            </div>
          </div>
        </section>
      </aside>

      <!-- ═══ EXPORT (selalu di bawah, lebar penuh) ═══ -->
      <section class="card export-card fr-export">
        <div class="card-head border-b">
          <div class="card-titles">
            <h3 class="card-title">Export dokumen</h3>
            <p class="card-sub">Unduh laporan dalam format Excel atau PDF</p>
          </div>
        </div>

        <div class="export-body">
          <div class="export-toggle" role="group" aria-label="Jenis laporan">
            <button type="button" class="toggle-btn" :class="{ active: exportMode === 'monthly' }" :aria-pressed="exportMode === 'monthly'" @click="exportMode = 'monthly'">Bulanan</button>
            <button type="button" class="toggle-btn" :class="{ active: exportMode === 'yearly' }" :aria-pressed="exportMode === 'yearly'" @click="exportMode = 'yearly'">Tahunan</button>
          </div>

          <div class="export-controls">
            <select v-if="exportMode === 'monthly'" v-model.number="exportMonth" class="nav-select nav-select-block" aria-label="Bulan yang diexport">
              <option v-for="(name, idx) in monthNames" :key="idx" :value="idx + 1">{{ name }}</option>
            </select>
            <select v-model.number="exportYear" class="nav-select nav-select-block" aria-label="Tahun yang diexport">
              <option v-for="y in yearsAvailable" :key="y" :value="y">{{ y }}</option>
            </select>
          </div>

          <p class="export-period-label">
            Periode: <span class="period-highlight">{{ exportMode === 'monthly' ? `${monthNames[exportMonth - 1]} ${exportYear}` : `Tahun ${exportYear}` }}</span>
          </p>

          <div class="export-btns">
            <button type="button" :disabled="isExporting" class="export-btn btn-excel" @click="exportDocument('excel')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
              {{ isExporting ? 'Mengunduh…' : 'Excel' }}
            </button>
            <button type="button" :disabled="isExporting" class="export-btn btn-pdf" @click="exportDocument('pdf')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
              {{ isExporting ? 'Mengunduh…' : 'PDF' }}
            </button>
          </div>
        </div>
      </section>
    </div>

    <!-- ── KONFIRMASI HAPUS ───────────────────────────────────────── -->
    <div v-if="deleteTarget" class="modal-backdrop" @click.self="closeDelete">
      <div class="modal" role="alertdialog" aria-modal="true" aria-labelledby="del-title" aria-describedby="del-desc">
        <div class="modal-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M3 6h18M8 6V4a1 1 0 011-1h6a1 1 0 011 1v2M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6M10 11v6M14 11v6"/></svg>
        </div>
        <h3 id="del-title" class="modal-title">Hapus pengeluaran ini?</h3>
        <p id="del-desc" class="modal-text">
          <strong>{{ deleteTarget.description }}</strong> senilai Rp {{ formatNumber(deleteTarget.amount) }}
          ({{ methodLabel(deleteTarget.payment_method) }}) akan dihapus dari buku kas dan tidak bisa dikembalikan.
        </p>
        <div class="modal-actions">
          <button ref="cancelDeleteBtn" type="button" class="modal-cancel" @click="closeDelete">Batal</button>
          <button type="button" class="modal-confirm" :disabled="isDeleting" @click="confirmDelete">
            {{ isDeleting ? 'Menghapus…' : 'Hapus pengeluaran' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from "vue";
import apiClient from "@/api/client";
import { toast } from "vue-sonner";

const monthNames = ["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"];
const viewModes  = [{ key: "daily", label: "Harian" }, { key: "monthly", label: "Bulanan" }, { key: "yearly", label: "Tahunan" }];

const viewMode       = ref("daily");
const currentDate    = ref(new Date());
const selectedMonth  = ref(new Date().getMonth() + 1);
const selectedYear   = ref(new Date().getFullYear());
const yearsAvailable = ref([new Date().getFullYear()]);

const financialSummary    = ref({ revenue: 0, expenses: 0, net_profit: 0 });
const dailyExpensesList   = ref([]);
const monthlyData         = ref([]);
const yearlyData          = ref([]);
const isLoadingDaily      = ref(false);
const isLoadingChart      = ref(false);
const isSubmittingExpense = ref(false);
const isExporting         = ref(false);
const expenseForm         = ref({ description: "", amount: null, payment_method: "cash" });
const editingId           = ref(null);
const formCard            = ref(null);
const descInput           = ref(null);

const exportMode  = ref("monthly");
const exportMonth = ref(new Date().getMonth() + 1);
const exportYear  = ref(new Date().getFullYear());

const paymentMethods = [{ key: "cash", label: "Cash" }, { key: "qris", label: "QRIS" }];
const methodLabel    = (m) => (m === "qris" ? "QRIS" : "Cash");
const quickDescs     = ["Bahan baku", "Gas", "Kemasan", "Listrik / air", "Gaji", "Lainnya"];

// ── Tanggal ─────────────────────────────────────────────────────────
const toDateString = (d) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const targetDateString = computed(() => toDateString(currentDate.value));
const todayString      = computed(() => toDateString(new Date()));
const isToday          = computed(() => targetDateString.value === todayString.value);

const viewModeLabel = computed(() => {
  if (viewMode.value === "daily")   return `Per tanggal — ${targetDateString.value}`;
  if (viewMode.value === "monthly") return `Per hari — ${monthNames[selectedMonth.value - 1]} ${selectedYear.value}`;
  return `Per bulan — Tahun ${selectedYear.value}`;
});

// ── Angka turunan ───────────────────────────────────────────────────
const summaryCards = computed(() => {
  if (viewMode.value === "daily") return financialSummary.value;
  const src = viewMode.value === "monthly" ? monthlyData.value : yearlyData.value;
  const rev = src.reduce((a, d) => a + (d.revenue  || 0), 0);
  const exp = src.reduce((a, d) => a + (d.expenses || 0), 0);
  return { revenue: rev, expenses: exp, net_profit: rev - exp };
});
const monthlyDataFiltered = computed(() => monthlyData.value.filter((d) => d.revenue > 0 || d.expenses > 0));
const maxMonthlyRevenue   = computed(() => Math.max(...monthlyData.value.map((d) => Math.max(d.revenue || 0, d.expenses || 0)), 1));
const maxYearlyRevenue    = computed(() => Math.max(...yearlyData.value.map((d) => Math.max(d.revenue || 0, d.expenses || 0)), 1));
const yearlyActiveCount   = computed(() => yearlyData.value.filter((d) => d.revenue > 0 || d.expenses > 0).length);

const monthlyStats = computed(() => {
  const active = monthlyDataFiltered.value;
  if (!active.length) return null;
  const avgRevenue = active.reduce((a, d) => a + d.revenue, 0) / active.length;
  const best = active.reduce((a, d) => (d.revenue > a.revenue ? d : a), active[0]);
  return { avgRevenue, best, activeDays: active.length };
});
const yearlyStats = computed(() => {
  const active = yearlyData.value.filter((d) => d.revenue > 0 || d.expenses > 0);
  if (!active.length) return null;
  const avgRevenue = active.reduce((a, d) => a + d.revenue, 0) / active.length;
  const best = active.reduce((a, d) => (d.revenue > a.revenue ? d : a), active[0]);
  return { avgRevenue, best, activeMonths: active.length };
});

// Kolom samping hanya dirender kalau ada isinya (supaya tidak ada ruang kosong)
const hasAside = computed(() =>
  viewMode.value === "daily" ||
  (viewMode.value === "monthly" && !!monthlyStats.value) ||
  (viewMode.value === "yearly" && !!yearlyStats.value)
);

// Rincian pengeluaran harian per metode
const methodBreakdown = computed(() => {
  const sum = (m) => dailyExpensesList.value
    .filter((e) => (e.payment_method || "cash") === m)
    .reduce((a, e) => a + Number(e.amount || 0), 0);
  const cash = sum("cash");
  const qris = sum("qris");
  const total = cash + qris;
  const pct = (v) => (total ? Math.round((v / total) * 100) : 0);
  return [
    { key: "cash", label: "Cash", amount: cash, pct: pct(cash) },
    { key: "qris", label: "QRIS", amount: qris, pct: pct(qris) },
  ];
});

// ── Format ──────────────────────────────────────────────────────────
const formatNumber = (v) => Math.round(Math.abs(v) || 0).toLocaleString("id-ID");
// Format rupiah dengan tanda minus yang rapi untuk nilai negatif
const formatRp = (v) => `${Number(v) < 0 ? "−" : ""}Rp ${formatNumber(v)}`;
const chartMax = computed(() => (viewMode.value === "monthly" ? maxMonthlyRevenue.value : maxYearlyRevenue.value));
// Nilai > 0 selalu punya batang minimal 2% supaya tetap terlihat.
const barPct = (value, max) => {
  const v = Number(value) || 0;
  if (!v || !max) return 0;
  return Math.max((v / max) * 100, 2);
};
const formatCompact = (v) => {
  const n = Number(v) || 0;
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)} M`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1).replace(/\.0$/, "")} jt`;
  if (n >= 1_000) return `${Math.round(n / 1_000)} rb`;
  return String(Math.round(n));
};
const amountPreview = computed(() => {
  const n = Number(expenseForm.value.amount);
  return n > 0 ? `= Rp ${formatNumber(n)}` : "";
});
const canSubmit = computed(() =>
  expenseForm.value.description.trim().length > 0 && Number(expenseForm.value.amount) > 0
);

const scrollToForm = () => formCard.value?.scrollIntoView({ behavior: "smooth", block: "start" });

// ── Navigasi periode ────────────────────────────────────────────────
const resetDaily = () => {
  financialSummary.value = { revenue: 0, expenses: 0, net_profit: 0 };
  dailyExpensesList.value = [];
};
const switchMode = (mode) => {
  viewMode.value = mode;
  cancelEdit();
  if (mode === "monthly") { exportMode.value = "monthly"; exportMonth.value = selectedMonth.value; exportYear.value = selectedYear.value; fetchMonthlyData(); }
  else if (mode === "yearly") { exportMode.value = "yearly"; exportYear.value = selectedYear.value; fetchYearlyData(); }
  else { fetchDailyData(); }
};
const changeDate = (days) => {
  cancelEdit();
  const d = new Date(currentDate.value);
  d.setDate(d.getDate() + days);
  if (d > new Date()) return;            // tidak ada pembukuan untuk hari yang belum terjadi
  currentDate.value = d;
  resetDaily();
  fetchDailyData();
};
const jumpToDate = (value) => {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value || "")) return;
  const [y, m, d] = value.split("-").map(Number);
  cancelEdit();
  currentDate.value = new Date(y, m - 1, d);
  resetDaily();
  fetchDailyData();
};
const goToday = () => {
  cancelEdit();
  currentDate.value = new Date();
  resetDaily();
  fetchDailyData();
};
const changeMonth = (delta) => {
  let m = selectedMonth.value + delta, y = selectedYear.value;
  if (m < 1) { m = 12; y--; }
  if (m > 12) { m = 1; y++; }
  selectedMonth.value = m; selectedYear.value = y;
  exportMonth.value = m; exportYear.value = y;
  fetchMonthlyData();
};
const changeYear = (delta) => { selectedYear.value += delta; exportYear.value = selectedYear.value; fetchYearlyData(); };
// Ganti tahun lewat dropdown: export ikut disinkronkan
const onMonthlyYearChange = () => { exportYear.value = selectedYear.value; fetchMonthlyData(); };
const onYearlyYearChange  = () => { exportYear.value = selectedYear.value; fetchYearlyData(); };

// ── Fetch ───────────────────────────────────────────────────────────
let dailySeq = 0;
const fetchDailyData = async () => {
  const seq = ++dailySeq;
  isLoadingDaily.value = true;
  try {
    const [summaryRes, expenseRes] = await Promise.all([
      apiClient.get("/orders/admin_dashboard_daily_stats/", { params: { target_date: targetDateString.value } }),
      apiClient.get("/expenses/", { params: { date: targetDateString.value } }),
    ]);
    if (seq !== dailySeq) return;        // jawaban usang (user keburu ganti tanggal) dibuang
    financialSummary.value  = summaryRes.data;
    dailyExpensesList.value = expenseRes.data;
  } catch (err) {
    if (seq !== dailySeq) return;
    console.error(err);
    toast.error("Gagal memuat data keuangan harian.");
  } finally {
    if (seq === dailySeq) isLoadingDaily.value = false;
  }
};
const fetchMonthlyData = async () => {
  isLoadingChart.value = true;
  try {
    const { data } = await apiClient.get("/orders/finance/daily/", { params: { year: selectedYear.value, month: selectedMonth.value } });
    monthlyData.value = data.data;
    if (data.years_available) yearsAvailable.value = data.years_available;
  } catch (err) { console.error(err); toast.error("Gagal memuat data bulanan."); }
  finally { isLoadingChart.value = false; }
};
const fetchYearlyData = async () => {
  isLoadingChart.value = true;
  try {
    const { data } = await apiClient.get("/orders/finance/monthly/", { params: { year: selectedYear.value } });
    yearlyData.value = data.data;
    if (data.years_available) yearsAvailable.value = data.years_available;
  } catch (err) { console.error(err); toast.error("Gagal memuat data tahunan."); }
  finally { isLoadingChart.value = false; }
};

// ── Form pengeluaran ────────────────────────────────────────────────
const resetExpenseForm = () => { expenseForm.value = { description: "", amount: null, payment_method: "cash" }; };
const cancelEdit = () => { editingId.value = null; resetExpenseForm(); };
const pickQuick = (text) => {
  expenseForm.value.description = text;
  nextTick(() => descInput.value?.focus());
};
const startEdit = (exp) => {
  editingId.value = exp.id;
  expenseForm.value = { description: exp.description, amount: Number(exp.amount), payment_method: exp.payment_method || "cash" };
  nextTick(() => {
    formCard.value?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    descInput.value?.focus();
  });
};
const submitExpense = async () => {
  if (!canSubmit.value || isSubmittingExpense.value) return;
  isSubmittingExpense.value = true;
  const isEdit  = editingId.value !== null;
  const payload = {
    description: expenseForm.value.description.trim(),
    amount: expenseForm.value.amount,
    payment_method: expenseForm.value.payment_method,
  };
  try {
    if (isEdit) await apiClient.patch(`/expenses/${editingId.value}/`, payload);
    else await apiClient.post("/expenses/", { ...payload, date: targetDateString.value });
    cancelEdit();
    await fetchDailyData();
    toast.success(isEdit ? "Pengeluaran diperbarui." : "Pengeluaran dicatat.");
    if (!isEdit) nextTick(() => descInput.value?.focus());   // siap input berikutnya
  } catch {
    toast.error(isEdit ? "Gagal memperbarui pengeluaran." : "Gagal mencatat pengeluaran.");
  } finally { isSubmittingExpense.value = false; }
};

// ── Hapus ───────────────────────────────────────────────────────────
const deleteTarget    = ref(null);
const isDeleting      = ref(false);
const cancelDeleteBtn = ref(null);
const askDelete   = (exp) => { deleteTarget.value = exp; nextTick(() => cancelDeleteBtn.value?.focus()); };
const closeDelete = () => { if (!isDeleting.value) deleteTarget.value = null; };
const confirmDelete = async () => {
  const exp = deleteTarget.value;
  if (!exp) return;
  isDeleting.value = true;
  try {
    await apiClient.delete(`/expenses/${exp.id}/`);
    if (editingId.value === exp.id) cancelEdit();
    toast.success("Pengeluaran dihapus.");
    deleteTarget.value = null;
    fetchDailyData();
  } catch { toast.error("Gagal menghapus pengeluaran."); }
  finally { isDeleting.value = false; }
};

// Esc menutup modal hapus (listener global, karena fokus belum tentu di dalam modal)
const onKeydown = (e) => { if (e.key === "Escape" && deleteTarget.value) closeDelete(); };

// ── Export ──────────────────────────────────────────────────────────
const exportDocument = async (type) => {
  isExporting.value = true;
  const endpoint = type === "excel" ? "/orders/export/finance-excel/" : "/orders/export/finance-pdf/";
  const params   = new URLSearchParams({ mode: exportMode.value, year: exportYear.value });
  if (exportMode.value === "monthly") params.append("month", exportMonth.value);
  const url         = `${apiClient.defaults.baseURL}${endpoint}?${params.toString()}`;
  const periodLabel = exportMode.value === "monthly" ? `${monthNames[exportMonth.value - 1]} ${exportYear.value}` : `Tahun ${exportYear.value}`;
  try { window.open(url, "_blank"); toast.success(`Mengunduh laporan ${type.toUpperCase()} — ${periodLabel}`); }
  catch { toast.error("Gagal membuka link unduhan."); }
  finally { setTimeout(() => { isExporting.value = false; }, 1500); }
};

onMounted(async () => {
  window.addEventListener("keydown", onKeydown);
  await fetchDailyData();
  try {
    const { data } = await apiClient.get("/orders/finance/monthly/", { params: { year: selectedYear.value } });
    if (data.years_available) yearsAvailable.value = data.years_available;
    yearlyData.value = data.data;
  } catch { /* tidak kritis: hanya untuk daftar tahun */ }
});
onBeforeUnmount(() => window.removeEventListener("keydown", onKeydown));
</script>

<style scoped>
/* ── Root ────────────────────────────────────────────────────────── */
.fr-root {
  --page-max: 1360px;
  min-height: 100%;
  background: var(--bg);
  color: var(--text);
  padding: clamp(1.1rem, 3vw, 2rem) max(clamp(1rem, 3vw, 1.75rem), calc((100% - var(--page-max)) / 2)) 3rem;
  font-family: 'Inter', sans-serif;
  -webkit-font-smoothing: antialiased;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
.font-mono { font-family: monospace; }

/* ── Header + toolbar ────────────────────────────────────────────── */
.fr-header {
  display: flex; align-items: flex-end; justify-content: space-between;
  gap: 1.25rem; padding-bottom: 1.4rem;
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}
.fr-heading { display: flex; flex-direction: column; gap: 0.35rem; }
.fr-title {
  font-family: 'Manrope', system-ui, sans-serif; font-size: clamp(1.45rem, 4vw, 1.9rem);
  font-weight: 700; letter-spacing: -0.02em; margin: 0; line-height: 1.1;
}
.fr-subtitle { font-size: 0.85rem; color: var(--text-dim); margin: 0; }

.fr-toolbar { display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; }

.mode-switch {
  display: flex; background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--r-md); padding: 4px; gap: 2px;
}
.mode-btn {
  padding: 0.5rem 1.1rem; border-radius: 9px; border: none; background: transparent;
  color: var(--text-faint); font-family: 'Manrope', system-ui, sans-serif; font-size: 0.82rem; font-weight: 600;
  cursor: pointer; transition: background 0.15s, color 0.15s;
}
.mode-btn:hover { color: var(--text-2); }
.mode-btn.active { background: var(--accent); color: var(--on-accent); }

.date-nav {
  display: flex; align-items: stretch; background: var(--surface);
  border: 1px solid var(--border); border-radius: var(--r-md); overflow: hidden;
}
.nav-btn {
  display: flex; align-items: center; justify-content: center; min-width: 42px;
  padding: 0.5rem 0.75rem; background: transparent; border: none;
  color: var(--text-dim); cursor: pointer; transition: background 0.15s, color 0.15s;
}
.nav-btn:hover:not(:disabled) { color: var(--text); background: rgb(var(--ink) / 0.05); }
.nav-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.nav-current {
  display: flex; align-items: center; padding: 0.5rem 1rem;
  font-size: 0.88rem; font-weight: 600; color: var(--text);
  border-left: 1px solid var(--border); border-right: 1px solid var(--border);
  white-space: nowrap; font-variant-numeric: tabular-nums;
}
.nav-date {
  min-width: 9.5rem; padding: 0.5rem 0.75rem; background: transparent; color: var(--text);
  border: 0; border-left: 1px solid var(--border); border-right: 1px solid var(--border);
  font-family: inherit; font-size: 0.88rem; font-weight: 600; outline: none; cursor: pointer; color-scheme: inherit;
}
.nav-date:focus-visible { background: var(--surface-hover); }
.today-btn {
  padding: 0.55rem 1rem; border-radius: var(--r-md); background: transparent;
  border: 1px solid var(--line-accent, var(--border-strong)); color: var(--accent-text);
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.82rem; font-weight: 600;
  cursor: pointer; transition: background 0.15s;
}
.today-btn:hover { background: var(--tint-accent, var(--surface-hover)); }
.nav-select {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--r-md);
  padding: 0.6rem 0.9rem; color: var(--text); font-family: inherit; font-size: 0.88rem; font-weight: 600;
  outline: none; cursor: pointer; transition: border-color 0.15s; color-scheme: inherit;
}
.nav-select:focus { border-color: var(--accent); }
.nav-select-block { width: 100%; }

/* ── KPI ─────────────────────────────────────────────────────────── */
.summary-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; }
.s-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--r-lg);
  padding: 1.4rem 1.5rem; position: relative; overflow: hidden; box-shadow: var(--shadow-sm);
}
.s-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; }
.s-green::before, .s-surplus::before { background: var(--green); }
.s-amber::before { background: var(--amber); }
.s-defisit::before { background: var(--red-soft); }

.s-top { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 1rem; }
.s-icon-wrap {
  display: flex; align-items: center; justify-content: center;
  width: 30px; height: 30px; border-radius: var(--r-sm); flex-shrink: 0;
}
.ic-green { background: rgba(34,197,94,0.1); color: var(--green-soft); }
.ic-amber { background: rgba(244,197,66,0.1); color: var(--amber-soft); }
.ic-red   { background: rgba(255,42,42,0.1); color: var(--red-soft); }
.s-label { font-family: 'Manrope', system-ui, sans-serif; font-size: 0.82rem; font-weight: 600; color: var(--text-dim); flex: 1; min-width: 0; }
.s-badge {
  font-size: 0.75rem; padding: 0.15rem 0.6rem; border-radius: 100px;
  font-family: 'Manrope', system-ui, sans-serif; font-weight: 600; white-space: nowrap;
}
.badge-up   { background: rgba(34,197,94,0.1); color: var(--green-soft); border: 1px solid rgba(34,197,94,0.2); }
.badge-down { background: rgba(255,42,42,0.1); color: var(--red-soft); border: 1px solid rgba(255,42,42,0.2); }
.s-value {
  font-family: 'Manrope', system-ui, sans-serif; font-size: clamp(1.25rem, 4.2vw, 1.7rem); overflow-wrap: anywhere;
  font-weight: 700; color: var(--text); letter-spacing: -0.02em; margin-bottom: 0.4rem;
  font-variant-numeric: tabular-nums;
}
.val-green { color: var(--green-soft); }
.val-red   { color: var(--red-soft); }
.s-note    { font-size: 0.78rem; color: var(--text-faint); }

/* ── Shell: main + aside (+ export lebar penuh) ──────────────────── */
.fr-shell { display: grid; grid-template-columns: minmax(0, 1fr); gap: 1.25rem; align-items: start; }
.fr-shell.has-aside { grid-template-columns: minmax(0, 1fr) 340px; }
.fr-main  { display: flex; flex-direction: column; gap: 1.25rem; min-width: 0; }
.fr-aside { display: flex; flex-direction: column; gap: 1.25rem; min-width: 0; }
.fr-aside > * { flex-shrink: 0; }
.fr-export { grid-column: 1 / -1; }

@media (max-width: 980px) {
  .fr-shell.has-aside { grid-template-columns: minmax(0, 1fr); }
}

/* ── Card ────────────────────────────────────────────────────────── */
.card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--r-lg); overflow: hidden; box-shadow: var(--shadow-sm);
}
.card.is-refreshing .table-scroll { opacity: 0.5; transition: opacity 0.15s; }
.card-head {
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
  padding: 1.1rem 1.4rem; flex-wrap: wrap;
}
.card-head.border-b { border-bottom: 1px solid var(--border); }
.card-titles { display: flex; flex-direction: column; gap: 0.2rem; min-width: 0; }
.card-title {
  font-family: 'Manrope', system-ui, sans-serif; font-size: 1rem; font-weight: 700; letter-spacing: -0.01em; margin: 0; color: var(--text);
  overflow-wrap: anywhere;
}
.card-sub { margin: 0; font-size: 0.78rem; color: var(--text-faint); }
.card-head-actions { display: flex; align-items: center; gap: 0.75rem; flex-shrink: 0; }

.jump-btn {
  display: none; min-height: 36px; padding: 0.3rem 0.9rem; border-radius: 8px;
  background: var(--accent); border: none; color: var(--on-accent);
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.8rem; font-weight: 600;
  cursor: pointer;
}
.jump-btn:hover { background: var(--accent-hover); }
.link-btn {
  padding: 0.25rem 0.1rem; border: 0; background: none; color: var(--accent-text);
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.82rem; font-weight: 600;
  text-decoration: underline; cursor: pointer; flex-shrink: 0;
}
.link-btn:hover { color: var(--text); }

/* ── Form ────────────────────────────────────────────────────────── */
.form-card.is-editing { border-color: var(--amber); box-shadow: 0 0 0 1px var(--amber), var(--shadow-sm); }
.expense-form { padding: 1.25rem 1.4rem 1.4rem; display: flex; flex-direction: column; gap: 1.15rem; }
.field { display: flex; flex-direction: column; gap: 0.45rem; }
.field-label { font-family: 'Manrope', system-ui, sans-serif; font-size: 0.8rem; font-weight: 600; color: var(--text-dim); }
.field-input {
  min-height: 44px; background: rgb(var(--ink) / 0.03); border: 1px solid var(--border-strong);
  border-radius: var(--r-sm); padding: 0.7rem 1rem; color: var(--text);
  font-size: 0.9rem; font-family: 'Inter', sans-serif; outline: none;
  transition: border-color 0.15s, background 0.15s; color-scheme: inherit;
}
.field-input::placeholder { color: var(--text-faint); }
.field-input:focus { border-color: var(--accent); background: transparent; }
.field-hint { min-height: 1.1rem; font-size: 0.78rem; color: var(--text-faint); }
.field-hint.is-on { font-family: monospace; font-weight: 600; color: var(--green-soft); }

.chip-row { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.chip {
  padding: 0.3rem 0.75rem; border-radius: 99px; background: transparent;
  border: 1px solid var(--border-strong); color: var(--text-dim);
  font-size: 0.78rem; cursor: pointer; transition: background 0.15s, color 0.15s;
}
.chip:hover { background: var(--surface-hover); color: var(--text); }

.method-switch {
  display: flex; background: rgb(var(--ink) / 0.03); border: 1px solid var(--border);
  border-radius: var(--r-sm); padding: 3px; gap: 2px;
}
.method-btn {
  flex: 1; padding: 0.55rem 0.7rem; border-radius: 6px; border: none; background: transparent;
  color: var(--text-faint); font-family: 'Manrope', system-ui, sans-serif; font-size: 0.82rem; font-weight: 600;
  cursor: pointer; transition: background 0.15s, color 0.15s;
}
.method-btn:hover { color: var(--text-2); }
.method-btn.active { background: var(--accent); color: var(--on-accent); }

.submit-btn {
  display: flex; align-items: center; justify-content: center; gap: 0.5rem;
  min-height: 46px; padding: 0.75rem; background: var(--accent);
  border: 1px solid var(--accent); border-radius: var(--r-sm); color: var(--on-accent);
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.85rem; font-weight: 600;
  cursor: pointer; transition: background 0.15s, border-color 0.15s;
}
.submit-btn:hover:not(:disabled) { background: var(--accent-hover); border-color: var(--accent-hover); }
.submit-btn:disabled { opacity: 0.35; cursor: not-allowed; }

/* focus keyboard */
.mode-btn:focus-visible, .nav-btn:focus-visible, .today-btn:focus-visible, .method-btn:focus-visible,
.toggle-btn:focus-visible, .chip:focus-visible, .edit-btn:focus-visible, .delete-btn:focus-visible,
.link-btn:focus-visible, .submit-btn:focus-visible, .export-btn:focus-visible, .jump-btn:focus-visible,
.modal-cancel:focus-visible, .modal-confirm:focus-visible, .nav-select:focus-visible, .field-input:focus-visible {
  outline: 2px solid var(--amber-soft); outline-offset: 2px;
}

/* ── Tabel ───────────────────────────────────────────────────────── */
.table-scroll { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; min-width: 420px; }
.data-table th {
  padding: 0.7rem 1.4rem; font-family: 'Manrope', system-ui, sans-serif; font-size: 0.78rem; font-weight: 600;
  color: var(--text-faint); text-align: left;
  background: rgb(var(--ink) / 0.02); border-bottom: 1px solid var(--border);
}
.th-right  { text-align: right !important; }
.th-center { text-align: center !important; }
.daily-table { table-layout: fixed; min-width: 560px; }
.daily-table .col-method  { width: 110px; }
.daily-table .col-amount  { width: 160px; }
.daily-table .col-actions { width: 160px; }

.data-row { border-bottom: 1px solid var(--border); transition: background 0.12s; }
.data-row:hover { background: var(--surface-hover); }
.data-row:last-child { border-bottom: none; }
.row-empty { opacity: 0.35; }
.row-editing, .row-editing:hover { background: rgba(244,197,66,0.08); }

.data-table td { padding: 0.9rem 1.4rem; font-size: 0.88rem; vertical-align: middle; }
.td-mono   { font-family: monospace; color: var(--text-2); }
.td-month  { font-weight: 600; color: var(--text); }
.td-desc   { color: var(--text); overflow-wrap: anywhere; }
.td-right  { text-align: right; font-variant-numeric: tabular-nums; }
.td-center { text-align: center; }
.td-rev    { font-family: monospace; font-weight: 700; color: var(--green-soft); }
.td-exp    { font-family: monospace; color: var(--amber-soft); }
.td-amount { font-family: monospace; font-weight: 700; color: var(--amber-soft); white-space: nowrap; }
.td-pos    { font-family: monospace; font-weight: 700; color: var(--text); }
.td-neg    { font-family: monospace; font-weight: 700; color: var(--red-soft); }

.total-row { background: rgb(var(--ink) / 0.03) !important; border-top: 1px solid var(--border-strong) !important; }
.total-row td {
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.82rem; font-weight: 700; color: var(--text-dim); padding: 0.85rem 1.4rem;
}
.total-row .td-rev, .total-row .td-exp, .total-row .td-pos, .total-row .td-neg { font-family: monospace; font-size: 0.88rem; }

.method-badge {
  display: inline-block; padding: 0.15rem 0.65rem; border-radius: 100px; border: 1px solid;
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.78rem; font-weight: 600;
}
.mb-cash { color: var(--text-dim); background: rgb(var(--ink) / 0.04); border-color: var(--border-strong); }
.mb-qris { color: var(--blue-soft); background: rgba(56,189,248,0.08); border-color: rgba(56,189,248,0.25); }

.row-actions { display: inline-flex; gap: 0.4rem; }
.edit-btn, .delete-btn {
  padding: 0.32rem 0.75rem; border-radius: 6px; border: 1px solid;
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.78rem; font-weight: 600;
  cursor: pointer; transition: background 0.15s, color 0.15s;
}
.edit-btn { background: rgb(var(--ink) / 0.04); border-color: var(--border-strong); color: var(--text-dim); }
.edit-btn:hover { color: var(--text); background: rgb(var(--ink) / 0.08); }
.delete-btn { background: rgba(255,42,42,0.07); border-color: rgba(255,42,42,0.18); color: var(--red-soft); }
.delete-btn:hover { background: rgba(255,42,42,0.15); }

.empty-cell { padding: 2.75rem 1.4rem !important; text-align: center; color: var(--text-faint); }
.empty-cell .spinner-sm { margin: 0 auto 0.6rem; }
.empty-icon { font-size: 1.6rem; margin-bottom: 0.5rem; }
.empty-cell p { margin: 0; font-size: 0.85rem; }
.empty-title { color: var(--text-dim); font-weight: 600; }
.empty-hint { margin-top: 0.25rem !important; font-size: 0.78rem !important; }

/* ── Pengeluaran per metode ──────────────────────────────────────── */
.method-split { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1.5rem; padding: 1.25rem 1.4rem 1.4rem; }
.split-item { display: flex; flex-direction: column; gap: 0.55rem; min-width: 0; }
.split-top { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; flex-wrap: wrap; }
.split-amount { font-family: monospace; font-size: 1rem; font-weight: 700; color: var(--text); font-variant-numeric: tabular-nums; }
.split-track { height: 8px; border-radius: 99px; background: rgb(var(--ink) / 0.07); overflow: hidden; }
.split-fill { height: 100%; border-radius: 99px; min-width: 0; transition: width 0.4s ease; }
.sf-cash { background: var(--amber); }
.sf-qris { background: var(--blue-soft); }
.split-pct { font-size: 0.78rem; color: var(--text-faint); }

/* ── Insight ─────────────────────────────────────────────────────── */
.insight-body { padding: 1.15rem 1.4rem 1.35rem; display: flex; flex-direction: column; gap: 1.1rem; }
.insight-row { display: flex; flex-direction: column; gap: 0.25rem; }
.insight-row + .insight-row { padding-top: 1.1rem; border-top: 1px solid var(--border); }
.insight-label { font-size: 0.78rem; color: var(--text-dim); }
.insight-value { font-family: monospace; font-size: 0.95rem; font-weight: 700; color: var(--text); font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }

/* ── Export (horizontal) ─────────────────────────────────────────── */
.export-body { padding: 1.15rem 1.4rem 1.35rem; display: flex; flex-wrap: wrap; align-items: center; gap: 0.75rem 1rem; }
.export-toggle {
  display: flex; background: rgb(var(--ink) / 0.03); border: 1px solid var(--border);
  border-radius: var(--r-sm); padding: 3px; gap: 2px;
}
.toggle-btn {
  padding: 0.45rem 1.05rem; border-radius: 6px; border: none; background: transparent; color: var(--text-faint);
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.82rem; font-weight: 600;
  cursor: pointer; transition: background 0.15s, color 0.15s;
}
.toggle-btn:hover { color: var(--text-2); }
.toggle-btn.active { background: var(--accent); color: var(--on-accent); }
.export-controls { display: flex; gap: 0.5rem; }
.export-controls .nav-select { width: auto; min-width: 7.5rem; }
.export-period-label {
  flex: 1 1 14rem; margin: 0; font-size: 0.85rem; color: var(--text-dim);
  background: rgb(var(--ink) / 0.03); border: 1px solid var(--border);
  border-radius: var(--r-sm); padding: 0.6rem 0.85rem;
}
.period-highlight { color: var(--accent-text); font-weight: 700; }
.export-btns { display: flex; gap: 0.5rem; margin-left: auto; }
.export-btn {
  display: flex; align-items: center; justify-content: center; gap: 0.45rem; min-width: 8rem;
  padding: 0.7rem 1rem; border-radius: var(--r-sm); border: 1px solid;
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.85rem; font-weight: 600;
  cursor: pointer; transition: background 0.15s;
}
.export-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-excel { background: rgba(34,197,94,0.07); border-color: rgba(34,197,94,0.25); color: var(--green-soft); }
.btn-excel:hover:not(:disabled) { background: rgba(34,197,94,0.14); }
.btn-pdf   { background: rgba(217,43,34,0.07); border-color: rgba(217,43,34,0.25); color: var(--red-soft); }
.btn-pdf:hover:not(:disabled)   { background: rgba(217,43,34,0.14); }

/* ── Grafik ──────────────────────────────────────────────────────── */
.chart-loading {
  display: flex; align-items: center; justify-content: center; gap: 0.6rem; padding: 3.5rem;
  color: var(--text-faint); font-size: 0.85rem; font-family: 'Manrope', system-ui, sans-serif;
}
.spinner-sm {
  width: 20px; height: 20px; border: 2px solid rgb(var(--ink) / 0.07);
  border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.chart-area { padding: 1.25rem 1.4rem 1.2rem; }
.chart-frame { display: flex; gap: 0.6rem; align-items: stretch; }
/* Sumbu Y: tinggi disamakan dengan area batang (label X ≈ 1.5rem di bawahnya) */
.y-axis {
  display: flex; flex-direction: column; justify-content: space-between; align-items: flex-end;
  flex-shrink: 0; min-width: 3.2rem; height: 200px; padding-bottom: calc(1.5rem + 0.25rem);
  font-family: monospace; font-size: 0.75rem; color: var(--text-faint);
  font-variant-numeric: tabular-nums; line-height: 1;
}
.bar-chart { flex: 1; min-width: 0; display: flex; align-items: stretch; gap: 4px; height: 200px; overflow-x: auto; overflow-y: hidden; padding-bottom: 0.25rem; }
.bar-chart-yearly { gap: 8px; overflow-x: visible; }
.bar-col { display: flex; flex-direction: column; align-items: stretch; gap: 0.35rem; flex: 1 0 22px; min-width: 22px; cursor: default; }
.bar-chart-yearly .bar-col { flex-basis: 0; min-width: 0; }
.bar-pair {
  display: flex; align-items: flex-end; justify-content: center; gap: 2px;
  flex: 1; min-height: 0; width: 100%; border-bottom: 1px solid var(--border-strong);
  background-image: repeating-linear-gradient(to top, transparent 0, transparent calc(50% - 1px), var(--border) calc(50% - 1px), var(--border) 50%);
}
.bar { flex: 1; max-width: 18px; min-width: 4px; border-radius: 3px 3px 0 0; transition: height 0.5s ease, filter 0.15s; }
.bar-col:hover .bar { filter: brightness(1.18); }
.bar-rev { background: var(--green); }
.bar-exp { background: var(--amber); opacity: 0.75; }
.bar-label { height: 1.15rem; font-size: 0.75rem; font-family: monospace; color: var(--text-faint); white-space: nowrap; text-align: center; }
.chart-legend { display: flex; gap: 1rem; flex-wrap: wrap; }
.legend-item { display: flex; align-items: center; gap: 0.45rem; font-size: 0.78rem; color: var(--text-dim); }
.legend-dot { width: 10px; height: 10px; border-radius: 3px; }
.ld-green { background: var(--green); }
.ld-amber { background: var(--amber); }

/* ── Modal hapus ─────────────────────────────────────────────────── */
.modal-backdrop {
  position: fixed; inset: 0; z-index: 100; display: flex; align-items: center; justify-content: center;
  padding: 1rem; background: var(--overlay); backdrop-filter: blur(4px);
}
.modal {
  width: 100%; max-width: 400px; background: var(--surface); border: 1px solid var(--border-strong);
  border-radius: var(--r-lg); padding: 1.6rem; box-shadow: var(--shadow-lg); animation: modal-in 0.15s ease-out;
}
@keyframes modal-in { from { opacity: 0; transform: translateY(6px) scale(0.98); } to { opacity: 1; transform: none; } }
.modal-icon {
  display: flex; align-items: center; justify-content: center; width: 40px; height: 40px;
  border-radius: var(--r-sm); margin-bottom: 1rem; background: rgba(255,42,42,0.1); color: var(--red-soft);
}
.modal-title { font-family: 'Manrope', system-ui, sans-serif; font-size: 1.1rem; font-weight: 700; letter-spacing: -0.01em; margin: 0 0 0.5rem; color: var(--text); }
.modal-text { font-size: 0.88rem; line-height: 1.6; color: var(--text-dim); margin: 0 0 1.4rem; }
.modal-text strong { color: var(--text); font-weight: 600; }
.modal-actions { display: flex; gap: 0.5rem; }
.modal-cancel, .modal-confirm {
  flex: 1; min-height: 44px; padding: 0.7rem; border-radius: var(--r-sm); border: 1px solid;
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.85rem; font-weight: 600;
  cursor: pointer; transition: background 0.15s;
}
.modal-cancel { background: rgb(var(--ink) / 0.04); border-color: var(--border-strong); color: var(--text); }
.modal-cancel:hover { background: rgb(var(--ink) / 0.08); }
.modal-confirm { background: var(--accent); border-color: var(--accent); color: var(--on-accent); }
.modal-confirm:hover:not(:disabled) { background: var(--accent-hover); }
.modal-confirm:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── Hilangkan spinner input number ──────────────────────────────── */
input::-webkit-outer-spin-button, input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
input[type=number] { -moz-appearance: textfield; }

/* ── Responsif ───────────────────────────────────────────────────── */
@media (max-width: 980px) {
  .jump-btn { display: inline-flex; align-items: center; }
}

@media (max-width: 768px) {
  .fr-root { gap: 1.1rem; }
  .fr-header { flex-direction: column; align-items: flex-start; gap: 1rem; padding-bottom: 1.1rem; }
  .fr-toolbar { width: 100%; flex-direction: column; align-items: stretch; }
  .mode-switch { width: 100%; }
  .mode-btn { flex: 1; min-height: 42px; }
  .date-nav { width: 100%; }
  .nav-current, .nav-date { flex: 1; text-align: center; justify-content: center; min-width: 0; }
  .nav-select { width: 100%; min-height: 44px; }
  .today-btn { min-height: 42px; }

  .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.75rem; }
  .summary-grid > :last-child { grid-column: 1 / -1; }
  .s-card { padding: 1.1rem; }

  .card-head { padding: 1rem 1.1rem; }
  .expense-form, .insight-body, .export-body, .method-split { padding-inline: 1.1rem; }
  .chart-area { padding: 1rem 1.1rem; }
  .bar-chart, .y-axis { height: 170px; }
  .y-axis { min-width: 2.6rem; }
  .method-split { gap: 1rem; }

  .export-controls { width: 100%; }
  .export-controls .nav-select { flex: 1; }
  .export-toggle { width: 100%; }
  .toggle-btn { flex: 1; }
  .export-btns { width: 100%; margin-left: 0; }
  .export-btn { flex: 1; min-height: 46px; }
}

@media (max-width: 640px) {
  /* log pengeluaran: tabel → kartu */
  .daily-table { min-width: 0; table-layout: auto; }
  .daily-table, .daily-table tbody, .daily-table tfoot { display: block; width: 100%; }
  .daily-table colgroup { display: none; }
  .daily-table thead { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
  .daily-table tbody tr.data-row {
    display: grid; grid-template-columns: 1fr auto;
    grid-template-areas: "desc amount" "method actions";
    gap: 0.6rem 0.75rem; align-items: center; padding: 0.9rem 1rem;
  }
  .daily-table td { display: block; padding: 0; }
  .daily-table .td-desc   { grid-area: desc; font-weight: 500; }
  .daily-table .td-amount { grid-area: amount; text-align: right; }
  .daily-table .td-method { grid-area: method; }
  .daily-table .td-center { grid-area: actions; text-align: right; }
  .daily-table tfoot tr.total-row { display: flex; justify-content: space-between; align-items: center; padding: 0.85rem 1rem; }
  .daily-table tfoot td { padding: 0; }
  .daily-table tfoot td:empty { display: none; }
  .daily-table .empty-cell { padding: 2rem 1rem !important; }
  .edit-btn, .delete-btn { min-height: 36px; padding-inline: 0.9rem; }

  /* tabel bulanan/tahunan: kolom pertama menempel saat scroll samping */
  .data-table:not(.daily-table) th,
  .data-table:not(.daily-table) td { padding: 0.7rem 0.8rem; }
  .data-table:not(.daily-table) th:first-child,
  .data-table:not(.daily-table) td:first-child { position: sticky; left: 0; z-index: 1; background: var(--surface); }
  .data-table:not(.daily-table) .total-row td:first-child { background: var(--surface-2); }
  .data-table:not(.daily-table) td { font-size: 0.82rem; }
}

@media (max-width: 420px) {
  .method-split { grid-template-columns: 1fr; }
}
@media (max-width: 380px) {
  .summary-grid { grid-template-columns: 1fr; }
}

@media (pointer: coarse) {
  .nav-btn, .mode-btn, .toggle-btn, .method-btn { min-height: 44px; }
  .field-input, .nav-select, .nav-date { font-size: 1rem; }
}

@media (prefers-reduced-motion: reduce) {
  .modal, .spinner-sm, .bar, .split-fill { animation: none; transition: none; }
}
</style>