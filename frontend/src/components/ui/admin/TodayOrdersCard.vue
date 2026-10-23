<template>
  <section class="adm-card today" aria-labelledby="today-title">
    <header class="adm-card-head">
      <div class="adm-card-head-main">
        <h2 id="today-title" class="adm-card-title">Pesanan hari ini</h2>
        <p class="adm-card-desc">
          {{ summary.count }} pesanan aktif · tidak ikut filter tanggal
          <template v-if="lastUpdated"> · diperbarui {{ lastUpdated }}</template>
        </p>
      </div>
      <router-link to="/admin/orders" class="today-link">Lihat semua</router-link>
    </header>

    <div v-if="loading" class="today-state" role="status" aria-live="polite">Memuat pesanan…</div>

    <div v-else-if="error && !orders.length" class="today-state today-state--error" role="alert">
      <p>{{ error }}</p>
      <button type="button" class="today-retry" @click="load({ force: true })">Coba lagi</button>
    </div>

    <div v-else-if="!orders.length" class="today-state">Belum ada pesanan hari ini.</div>

    <div v-else class="today-body">
      <div class="today-table-wrap">
        <table class="today-table">
          <thead>
            <tr>
              <th scope="col">No. nota</th>
              <th scope="col">Pelanggan</th>
              <th scope="col" class="num">Total</th>
              <th scope="col">Status</th>
              <th scope="col" class="num">Jam</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="o in latest" :key="o.id ?? o.order_number">
              <td class="mono">{{ o.order_number || o.id }}</td>
              <td class="cust">{{ o.customer_name || o.customer_phone || 'Walk In' }}</td>
              <td class="num">{{ rupiah(o.total_price) }}</td>
              <td>
                <span class="adm-badge" :class="statusOf(o).cls">{{ statusOf(o).label }}</span>
              </td>
              <td class="num">{{ timeOf(o.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="today-methods" role="group" aria-label="Komposisi metode bayar hari ini">
        <div
          class="donut"
          role="img"
          :aria-label="donutLabel"
          :style="{ background: donutBackground }"
        >
          <div class="donut-hole">
            <strong>{{ summary.count }}</strong>
            <span>pesanan</span>
          </div>
        </div>
        <ul class="legend">
          <li v-for="m in methods" :key="m.key">
            <span class="dot" :style="{ background: m.color }" aria-hidden="true"></span>
            <span class="legend-name">{{ m.label }}</span>
            <span class="legend-val">{{ m.count }} <small>({{ m.pct }}%)</small></span>
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { orderAPI } from '@/api/order'
import { formatRupiah } from '@/utils/price'

const REFRESH_MS = 30000
const LATEST_LIMIT = 6

const orders = ref([])
const loading = ref(true)
const error = ref('')
const lastUpdated = ref('')

let timer = null
let inflight = false
let seq = 0

// Tanggal lokal (bukan UTC) supaya "hari ini" tidak bergeser sekitar tengah malam WIB.
const localDateString = () => {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

const isQris = (m) => ['gateway', 'qris_manual', 'qris'].includes(m)

const rupiah = (v) => formatRupiah(parseFloat(v) || 0)
const timeOf = (iso) => {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', hour12: false })
}

const statusOf = (o) => {
  if (o.status === 'cancelled' || o.payment_status === 'void') return { cls: '', label: 'Batal' }
  if (o.payment_status === 'paid') return { cls: 'adm-badge--green', label: 'Lunas' }
  return { cls: 'adm-badge--amber', label: 'Belum bayar' }
}

const live = computed(() => orders.value.filter((o) => o.status !== 'cancelled'))

// Urutan dari server dianggap terbaru-dulu (sama seperti Active Orders), tapi diurutkan
// ulang berdasarkan created_at kalau tersedia supaya tidak bergantung pada asumsi itu.
const latest = computed(() =>
  [...orders.value]
    .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
    .slice(0, LATEST_LIMIT)
)

const summary = computed(() => ({ count: live.value.length }))

const methods = computed(() => {
  const total = live.value.length
  const counts = { cash: 0, qris: 0, mixed: 0 }
  for (const o of live.value) {
    if (isQris(o.payment_method)) counts.qris++
    else if (o.payment_method === 'mixed') counts.mixed++
    else counts.cash++
  }
  const defs = [
    { key: 'cash', label: 'Cash', color: 'var(--amber-soft)' },
    { key: 'qris', label: 'QRIS', color: 'var(--blue-soft)' },
    { key: 'mixed', label: 'Split', color: 'var(--purple-soft)' },
  ]
  return defs.map((d) => ({
    ...d,
    count: counts[d.key],
    pct: total ? Math.round((counts[d.key] / total) * 100) : 0,
  }))
})

const donutBackground = computed(() => {
  const total = live.value.length
  if (!total) return 'var(--surface-2)'
  let acc = 0
  const stops = methods.value
    .filter((m) => m.count > 0)
    .map((m) => {
      const from = acc
      acc += (m.count / total) * 100
      return `${m.color} ${from}% ${acc}%`
    })
  return `conic-gradient(${stops.join(', ')})`
})

const donutLabel = computed(
  () =>
    'Metode bayar hari ini: ' +
    methods.value.map((m) => `${m.label} ${m.count} pesanan (${m.pct}%)`).join(', ')
)

const load = async ({ force = false } = {}) => {
  if (inflight && !force) return
  const mySeq = ++seq
  inflight = true
  try {
    const res = await orderAPI.getActiveOrders(localDateString())
    if (mySeq !== seq) return
    orders.value = Array.isArray(res.data) ? res.data : []
    error.value = ''
    lastUpdated.value = new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', hour12: false })
  } catch (err) {
    if (mySeq !== seq) return
    console.error('Gagal memuat pesanan hari ini:', err)
    // Data lama tetap tampil kalau ada; pesan galat hanya muncul bila belum ada data sama sekali.
    error.value = 'Pesanan hari ini gagal dimuat.'
  } finally {
    if (mySeq === seq) { inflight = false; loading.value = false }
  }
}

const onVisible = () => { if (!document.hidden) load() }

onMounted(() => {
  load()
  timer = setInterval(() => { if (!document.hidden) load() }, REFRESH_MS)
  document.addEventListener('visibilitychange', onVisible)
})
onUnmounted(() => {
  clearInterval(timer)
  document.removeEventListener('visibilitychange', onVisible)
})

// Dipanggil tombol "Muat ulang" di Dashboard lewat ref.
defineExpose({ reload: () => load({ force: true }) })
</script>

<style scoped>
.today { margin-bottom: 1.75rem; }
.today-link {
  font-size: 0.8125rem; font-weight: 600; color: var(--accent-text);
  text-decoration: none; padding: 0.5rem 0.25rem; min-height: 44px;
  display: inline-flex; align-items: center;
}
.today-link:hover { text-decoration: underline; }

.today-state { padding: 2rem 1.25rem; text-align: center; font-size: 0.875rem; color: var(--text-dim); }
.today-state p { margin: 0 0 0.75rem; }
.today-retry {
  min-height: 44px; padding: 0 1rem; border-radius: var(--r-md);
  border: 1px solid var(--border-strong); background: var(--surface-2); color: var(--text);
  font-weight: 600; cursor: pointer;
}

.today-body {
  display: grid; grid-template-columns: minmax(0, 1fr) 15rem; gap: var(--sp-6);
  padding: 0 1.25rem 1.25rem;
}
.today-table-wrap { overflow-x: auto; }
.today-table { width: 100%; border-collapse: collapse; font-size: 0.8125rem; }
.today-table th {
  text-align: left; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.02em;
  color: var(--text-dim); padding: 0.6rem 0.75rem; border-bottom: 1px solid var(--border-strong);
  white-space: nowrap;
}
.today-table td {
  padding: 0.7rem 0.75rem; border-bottom: 1px solid var(--border);
  color: var(--text-2); vertical-align: middle;
}
.today-table tbody tr:last-child td { border-bottom: 0; }
.today-table .num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.today-table .mono { font-family: var(--font-mono); font-size: 0.75rem; white-space: nowrap; }
.today-table .cust { max-width: 11rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.today-methods { display: flex; flex-direction: column; align-items: center; gap: var(--sp-4); padding-top: 0.5rem; }
.donut {
  width: 9.5rem; height: 9.5rem; border-radius: 50%;
  display: grid; place-items: center; flex-shrink: 0;
}
.donut-hole {
  width: 6.25rem; height: 6.25rem; border-radius: 50%; background: var(--surface);
  display: flex; flex-direction: column; align-items: center; justify-content: center; line-height: 1.2;
}
.donut-hole strong { font-size: 1.5rem; color: var(--text); font-variant-numeric: tabular-nums; }
.donut-hole span { font-size: 0.75rem; color: var(--text-dim); }

.legend { list-style: none; margin: 0; padding: 0; width: 100%; display: flex; flex-direction: column; gap: 0.5rem; }
.legend li { display: flex; align-items: center; gap: 0.5rem; font-size: 0.8125rem; color: var(--text-2); }
.dot { width: 0.625rem; height: 0.625rem; border-radius: 50%; flex-shrink: 0; }
.legend-name { flex: 1; }
.legend-val { font-weight: 700; color: var(--text); font-variant-numeric: tabular-nums; }
.legend-val small { font-weight: 500; color: var(--text-dim); }

@media (max-width: 1023px) {
  .today-body { grid-template-columns: minmax(0, 1fr); }
  .today-methods { flex-direction: row; flex-wrap: wrap; justify-content: center; }
  .legend { width: auto; min-width: 11rem; }
}

/* HP: tabel jadi daftar kartu (tanpa geser samping) */
@media (max-width: 640px) {
  .today-table { min-width: 0; width: 100%; }
  .today-table thead { display: none; }
  .today-table tbody, .today-table tr, .today-table td { display: block; }
  .today-table tr {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 0.2rem 0.75rem;
    padding: 0.85rem 1.25rem;
    border-top: 1px solid var(--border);
  }
  .today-table td { padding: 0; border: 0; }
  .today-table td:nth-child(2) { grid-column: 1; grid-row: 1; font-weight: 700; }
  .today-table td:nth-child(3) { grid-column: 2; grid-row: 1; text-align: right; font-weight: 700; }
  .today-table td:nth-child(1) { grid-column: 1; grid-row: 2; }
  .today-table td:nth-child(5) { grid-column: 2; grid-row: 2; text-align: right; }
  .today-table td:nth-child(4) { grid-column: 1 / -1; grid-row: 3; margin-top: 0.4rem; }
}
</style>
