<!--
  BriefingStrip.vue — Strip Briefing di atas Dashboard.

  Selalu "hari ini", tidak ikut filter tanggal dashboard, dan dimuat sendiri
  (satu endpoint: /orders/briefing/) supaya error di sini tidak mematikan bagian lain.
  Bagian yang gagal dihitung server tampil sebagai "Gagal dimuat", bagian lain tetap jalan.

  Isi: prediksi hari ini, keramaian, target bulan ini + proyeksi, tagihan belum lunas,
  dan 2 sampai 3 saran berbasis aturan (tiap saran menyebut dasar hitungannya).

  Dashboard bisa memanggil reload() lewat ref ("Muat ulang"). Strip juga menyegarkan diri
  tiap 5 menit selama tab terlihat, supaya keramaian tidak basi di dashboard yang dibiarkan terbuka.
-->
<template>
  <section class="bf" aria-labelledby="bf-title" :aria-busy="loading">
    <header class="bf-head">
      <div>
        <p class="bf-eyebrow">Briefing hari ini</p>
        <h2 id="bf-title" class="bf-title">{{ headline }}</h2>
      </div>
      <span v-if="loading && data" class="bf-status" role="status">Memuat ulang…</span>
      <span v-else-if="refreshFailed && data" class="bf-status bf-status--warn" role="status">
        Gagal memperbarui, menampilkan data sebelumnya
      </span>
      <span v-else-if="updatedAt" class="bf-status">Diperbarui {{ updatedAt }}</span>
    </header>

    <div v-if="loading && !data" class="bf-skel" aria-hidden="true">
      <span v-for="n in 4" :key="n" class="bf-skel-tile"></span>
    </div>

    <div v-else-if="refreshFailed && !data" class="bf-error" role="alert">
      <p>Briefing gagal dimuat. Bagian lain dashboard tidak terpengaruh.</p>
      <button type="button" class="bf-btn" @click="load">Coba lagi</button>
    </div>

    <template v-else-if="data">
      <div class="bf-grid">
        <!-- Prediksi hari ini -->
        <div class="bf-tile">
          <span class="bf-label">Prediksi hari ini</span>
          <template v-if="pred">
            <div v-if="pred.is_closed_day" class="bf-value">Libur rutin</div>
            <div v-else-if="pred.predicted !== null" class="bf-value">{{ formatPrice(pred.predicted) }}</div>
            <div v-else class="bf-value bf-value--muted">Belum ada data</div>
            <p class="bf-sub">Omzet sejauh ini {{ formatPrice(pred.actual_so_far) }}</p>
            <p
              v-if="pred.predicted !== null && !pred.is_closed_day && pred.upper > pred.lower"
              class="bf-sub"
            >
              Kisaran {{ formatPrice(pred.lower) }} – {{ formatPrice(pred.upper) }}
            </p>
            <span v-if="pred.confidence && !pred.is_closed_day" class="bf-chip" :class="`is-conf-${pred.confidence}`">
              Keyakinan {{ pred.confidence }}
            </span>
          </template>
          <div v-else class="bf-value bf-value--muted">Gagal dimuat</div>
        </div>

        <!-- Keramaian -->
        <div class="bf-tile">
          <span class="bf-label">Keramaian</span>
          <template v-if="crowd">
            <div v-if="!crowd.store_open" class="bf-value bf-value--muted">Toko tutup</div>
            <div v-else class="bf-value bf-crowd" :class="`is-${crowd.level}`">
              <span class="bf-dot" aria-hidden="true"></span>{{ crowd.label }}
            </div>
            <p v-if="crowd.live_orders !== null && crowd.live_orders !== undefined" class="bf-sub">
              {{ crowd.live_orders }} pesanan dalam 60 menit terakhir
            </p>
            <span v-if="crowd.mode === 'manual'" class="bf-chip is-manual">
              Manual<template v-if="crowd.until"> sampai {{ formatClock(crowd.until) }}</template>
            </span>
            <p v-if="!crowd.enabled" class="bf-sub bf-sub--warn">Badge disembunyikan dari pelanggan</p>
          </template>
          <div v-else class="bf-value bf-value--muted">Gagal dimuat</div>
        </div>

        <!-- Target bulan ini -->
        <div class="bf-tile">
          <span class="bf-label">Target {{ target ? target.month_label : 'bulan ini' }}</span>
          <template v-if="target">
            <div class="bf-value">{{ formatPrice(target.realized) }}</div>
            <template v-if="target.target">
              <div class="bf-bar" role="img" :aria-label="barLabel">
                <span class="bf-bar-proj" :style="{ width: clampPct(target.projected_pct) + '%' }"></span>
                <span class="bf-bar-real" :style="{ width: clampPct(target.realized_pct) + '%' }"></span>
              </div>
              <p class="bf-sub">dari target {{ formatPrice(target.target) }} ({{ target.realized_pct }}%)</p>
            </template>
            <p v-if="target.projected !== null" class="bf-sub">
              Proyeksi akhir bulan {{ formatPrice(target.projected) }}<template v-if="target.projected_pct !== null"> ({{ target.projected_pct }}%)</template>
            </p>
            <span v-if="targetChip" class="bf-chip" :class="`is-${targetChip.tone}`">{{ targetChip.text }}</span>
            <p v-if="!target.target" class="bf-sub">
              Belum ada target.
              <RouterLink v-if="auth.isOwner" :to="{ name: 'AdminSettings' }" class="bf-link">Isi di Pengaturan</RouterLink>
              <template v-else>Minta owner mengisinya di Pengaturan.</template>
            </p>
          </template>
          <div v-else class="bf-value bf-value--muted">Gagal dimuat</div>
        </div>

        <!-- Tagihan belum lunas -->
        <div class="bf-tile">
          <span class="bf-label">Tagihan belum lunas</span>
          <template v-if="unpaid">
            <div v-if="unpaid.count === 0" class="bf-value">Tidak ada</div>
            <div v-else class="bf-value">{{ formatPrice(unpaid.total) }}</div>
            <p v-if="unpaid.count > 0" class="bf-sub">{{ unpaid.count }} order</p>
            <p v-if="unpaid.older_count > 0" class="bf-sub bf-sub--warn">
              {{ unpaid.older_count }} dari hari sebelumnya ({{ formatPrice(unpaid.older_total) }})
            </p>
            <RouterLink v-if="unpaid.count > 0" :to="{ name: 'ActiveOrders' }" class="bf-link">Lihat tagihan</RouterLink>
          </template>
          <div v-else class="bf-value bf-value--muted">Gagal dimuat</div>
        </div>
      </div>

      <!-- Saran -->
      <div class="bf-recs-wrap">
        <p class="bf-label">Saran <span class="bf-label-note">berbasis aturan dari data penjualan</span></p>
        <ul v-if="data.recommendations.length" class="bf-recs">
          <li v-for="rec in data.recommendations" :key="rec.id" class="bf-rec" :class="`tone-${rec.tone}`">
            <span class="bf-bullet" aria-hidden="true"></span>
            <div>
              <p class="bf-rec-text">{{ rec.text }}</p>
              <p class="bf-rec-reason">Dasar: {{ rec.reason }}</p>
            </div>
          </li>
        </ul>
        <p v-else-if="!data.errors.includes('recommendations')" class="bf-muted">
          Belum ada saran untuk hari ini.
        </p>
        <p v-else class="bf-muted">Saran gagal dihitung.</p>
      </div>

      <p v-if="data.data_note" class="bf-note">{{ data.data_note }}</p>
    </template>
  </section>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { analyticsAPI } from '@/api/analytics'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const AUTO_REFRESH_MS = 5 * 60 * 1000

const data = ref(null)
const loading = ref(true)
const refreshFailed = ref(false)
const updatedAt = ref('')
let latest = 0
let timer = null

const pred = computed(() => data.value?.prediction_today ?? null)
const crowd = computed(() => data.value?.crowd ?? null)
const target = computed(() => data.value?.target ?? null)
const unpaid = computed(() => data.value?.unpaid ?? null)

const headline = computed(() => {
  if (!data.value) return 'Ringkasan hari ini'
  const d = new Date(data.value.date + 'T00:00:00')
  const date = d.toLocaleDateString('id-ID', { day: 'numeric', month: 'long' })
  return `${data.value.day_name}, ${date}`
})

const targetChip = computed(() => {
  const t = target.value
  if (!t) return null
  switch (t.status) {
    case 'tercapai': return { tone: 'good', text: 'Tercapai' }
    case 'di_jalur': return { tone: 'good', text: 'Di jalur' }
    case 'di_bawah': return { tone: 'warn', text: `Kurang ±${formatPrice(t.gap)}` }
    case 'proyeksi_tidak_tersedia': return { tone: 'muted', text: 'Proyeksi belum tersedia' }
    default: return null
  }
})

const barLabel = computed(() => {
  const t = target.value
  if (!t || !t.target) return ''
  return `Realisasi ${t.realized_pct}% dari target` + (t.projected_pct !== null ? `, proyeksi ${t.projected_pct}%` : '')
})

const clampPct = (v) => Math.max(0, Math.min(100, Number(v) || 0))

const formatPrice = (value) =>
  new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(value || 0)

const formatClock = (iso) =>
  new Date(iso).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'Asia/Jakarta' })
    .replace(':', '.')

// Jawaban lama yang datang terlambat diabaikan; data lama tetap tampil selama memuat ulang.
const load = async () => {
  const mine = ++latest
  loading.value = true
  try {
    const res = await analyticsAPI.getBriefing()
    if (mine !== latest) return
    data.value = res.data
    refreshFailed.value = false
    updatedAt.value = new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', hour12: false })
  } catch (err) {
    if (mine !== latest) return
    console.error('Gagal memuat briefing:', err)
    refreshFailed.value = true
  } finally {
    if (mine === latest) loading.value = false
  }
}

onMounted(() => {
  load()
  timer = setInterval(() => {
    if (!document.hidden) load()
  }, AUTO_REFRESH_MS)
})
onBeforeUnmount(() => clearInterval(timer))

defineExpose({ reload: load })
</script>

<style scoped>
/* Token mengikuti tema admin (admin-theme.css), jadi gelap/terang otomatis. */
.bf {
  margin-bottom: 1.75rem;
  padding: clamp(1rem, 2.5vw, 1.4rem);
  background: var(--surface);
  border: 1px solid rgb(var(--ink) / 0.07);
  border-radius: 16px;
}
.bf-head {
  display: flex; align-items: flex-end; justify-content: space-between;
  gap: 0.75rem; flex-wrap: wrap; margin-bottom: 1rem;
}
.bf-eyebrow {
  margin: 0 0 0.2rem; font-family: 'Oswald', sans-serif; font-size: 0.68rem;
  letter-spacing: 0.2em; text-transform: uppercase; color: var(--accent-text);
}
.bf-title { margin: 0; font-size: 1.15rem; font-weight: 600; color: var(--text); }
.bf-status { font-size: 0.72rem; color: var(--text-faint); }
.bf-status--warn { color: var(--amber-soft); }

.bf-grid {
  display: grid; gap: 0.75rem;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
}
.bf-tile {
  display: flex; flex-direction: column; align-items: flex-start; gap: 0.3rem;
  min-width: 0; padding: 0.9rem 1rem;
  background: var(--surface-2);
  border: 1px solid rgb(var(--ink) / 0.06);
  border-radius: 12px;
}
.bf-label {
  font-family: 'Oswald', sans-serif; font-size: 0.68rem; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--text-dim);
}
.bf-label-note { margin-left: 0.4rem; letter-spacing: 0.02em; text-transform: none; font-family: 'Inter', sans-serif; color: var(--text-faint); }
.bf-value {
  font-size: 1.25rem; font-weight: 700; letter-spacing: -0.01em; color: var(--text);
  line-height: 1.2; overflow-wrap: anywhere;
}
.bf-value--muted { font-size: 0.95rem; font-weight: 500; color: var(--text-faint); }
.bf-sub { margin: 0; font-size: 0.76rem; color: var(--text-dim); line-height: 1.35; }
.bf-sub--warn { color: var(--amber-soft); }
.bf-muted { margin: 0; font-size: 0.82rem; color: var(--text-faint); }

.bf-chip {
  margin-top: 0.15rem; padding: 0.12rem 0.55rem; border-radius: 999px;
  font-size: 0.68rem; font-weight: 600; letter-spacing: 0.02em;
  border: 1px solid rgb(var(--ink) / 0.14); color: var(--text-dim);
}
.bf-chip.is-good { color: var(--green-soft); border-color: color-mix(in srgb, var(--green-soft) 45%, transparent); }
.bf-chip.is-warn { color: var(--amber-soft); border-color: color-mix(in srgb, var(--amber-soft) 45%, transparent); }
.bf-chip.is-muted, .bf-chip.is-manual { color: var(--text-dim); }
.bf-chip.is-manual { border-color: color-mix(in srgb, var(--blue-soft) 45%, transparent); color: var(--blue-soft); }
.bf-chip.is-conf-rendah { color: var(--amber-soft); border-color: color-mix(in srgb, var(--amber-soft) 45%, transparent); }
.bf-chip.is-conf-sedang { color: var(--text-2); }
.bf-chip.is-conf-tinggi { color: var(--green-soft); border-color: color-mix(in srgb, var(--green-soft) 45%, transparent); }

/* Keramaian: teks selalu ada, warna hanya penegas. */
.bf-crowd { display: inline-flex; align-items: center; gap: 0.5rem; --tone: var(--green-soft); }
.bf-crowd.is-sedang { --tone: var(--amber-soft); }
.bf-crowd.is-ramai { --tone: var(--red-soft); }
.bf-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--tone); flex-shrink: 0; }

/* Progres target: proyeksi (pucat) di belakang, realisasi (penuh) di depan. */
.bf-bar {
  position: relative; width: 100%; height: 8px; margin: 0.2rem 0 0.1rem;
  border-radius: 999px; background: rgb(var(--ink) / 0.08); overflow: hidden;
}
.bf-bar-proj, .bf-bar-real { position: absolute; inset: 0 auto 0 0; border-radius: 999px; }
.bf-bar-proj { background: color-mix(in srgb, var(--accent-text) 35%, transparent); }
.bf-bar-real { background: var(--accent-text); }

.bf-link {
  font-size: 0.76rem; font-weight: 600; color: var(--accent-text);
  text-decoration: underline; text-underline-offset: 2px;
}

.bf-recs-wrap { margin-top: 1.1rem; padding-top: 1rem; border-top: 1px solid rgb(var(--ink) / 0.06); }
.bf-recs { list-style: none; margin: 0.6rem 0 0; padding: 0; display: grid; gap: 0.65rem; }
.bf-rec { display: flex; gap: 0.7rem; align-items: flex-start; }
.bf-bullet { width: 8px; height: 8px; margin-top: 0.4rem; border-radius: 50%; flex-shrink: 0; background: var(--blue-soft); }
.bf-rec.tone-warn .bf-bullet { background: var(--amber-soft); }
.bf-rec.tone-good .bf-bullet { background: var(--green-soft); }
.bf-rec-text { margin: 0; font-size: 0.88rem; color: var(--text); line-height: 1.45; }
.bf-rec-reason { margin: 0.15rem 0 0; font-size: 0.72rem; color: var(--text-faint); line-height: 1.4; }

.bf-note {
  margin: 1rem 0 0; padding: 0.55rem 0.8rem; font-size: 0.76rem; color: var(--amber-soft);
  background: color-mix(in srgb, var(--amber-soft) 9%, transparent);
  border: 1px solid color-mix(in srgb, var(--amber-soft) 28%, transparent);
  border-radius: 10px;
}

.bf-skel { display: grid; gap: 0.75rem; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); }
.bf-skel-tile { height: 104px; border-radius: 12px; background: rgb(var(--ink) / 0.05); animation: bf-pulse 1.4s ease-in-out infinite; }
@keyframes bf-pulse { 50% { opacity: 0.55; } }

.bf-error {
  display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap;
  padding: 0.8rem 1rem; border-radius: 12px; font-size: 0.85rem; color: var(--text-2);
  background: color-mix(in srgb, var(--red-soft) 8%, transparent);
  border: 1px solid color-mix(in srgb, var(--red-soft) 30%, transparent);
}
.bf-error p { margin: 0; }
.bf-btn {
  padding: 0.4rem 0.9rem; border-radius: 8px; cursor: pointer;
  border: 1px solid rgb(var(--ink) / 0.18); background: transparent; color: var(--text);
  font-family: 'Oswald', sans-serif; font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase;
}
.bf-btn:hover { border-color: rgb(var(--ink) / 0.35); }

@media (prefers-reduced-motion: reduce) {
  .bf-skel-tile { animation: none; }
}
</style>
