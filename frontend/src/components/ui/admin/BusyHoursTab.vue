<!--
  BusyHoursTab.vue — Peta Jam Sibuk (admin), tab di halaman Order Reports.

  Menampilkan rata-rata jumlah pesanan per jam untuk tiap hari dalam seminggu,
  jam tersibuk dan paling sepi, serta ambang yang dipakai badge keramaian otomatis.
  Data dimuat saat tab dibuka (tidak ikut memberatkan tab Ringkasan).
-->
<template>
  <div class="bh">
    <!-- Pilih rentang riwayat -->
    <div class="bh-toolbar">
      <p class="bh-lead">
        Rata-rata pesanan per jam, dihitung dari riwayat
        <strong>{{ weeks }} minggu</strong> terakhir (tanpa hari ini).
      </p>
      <div class="bh-weeks" role="group" aria-label="Rentang riwayat">
        <button
          v-for="w in WEEK_OPTIONS"
          :key="w"
          type="button"
          class="bh-week"
          :class="{ 'is-on': weeks === w }"
          :aria-pressed="weeks === w"
          @click="setWeeks(w)"
        >{{ w }} minggu</button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading && !data" class="bh-skel" aria-busy="true">
      <div class="bh-skel-row"></div><div class="bh-skel-row"></div><div class="bh-skel-grid"></div>
    </div>

    <!-- Error -->
    <div v-else-if="error && !data" class="bh-empty">
      <p class="bh-empty-title">Gagal memuat Peta Jam Sibuk</p>
      <p class="bh-empty-sub">Periksa koneksi atau coba lagi beberapa saat.</p>
      <button type="button" class="bh-retry" @click="load">Muat ulang</button>
    </div>

    <template v-else-if="data">
      <!-- Data belum cukup -->
      <div v-if="!data.enough_data" class="bh-banner" role="status">
        <strong>Data belum cukup.</strong>
        Baru {{ data.total_orders }} pesanan di rentang ini (butuh minimal {{ data.min_orders_required }}).
        Pola di bawah masih kasar, dan badge keramaian otomatis memakai ambang tetap.
      </div>

      <!-- Ringkasan -->
      <div class="bh-kpis">
        <div class="bh-kpi">
          <p class="bh-kpi-value">{{ data.total_orders.toLocaleString('id-ID') }}</p>
          <p class="bh-kpi-label">Pesanan dianalisis</p>
          <p class="bh-kpi-sub">{{ rangeText }}</p>
        </div>
        <div class="bh-kpi">
          <p class="bh-kpi-value">{{ busiestDay?.name || '–' }}</p>
          <p class="bh-kpi-label">Hari tersibuk</p>
          <p v-if="busiestDay" class="bh-kpi-sub">≈ {{ fmt(busiestDay.avg) }} pesanan / hari</p>
        </div>
        <div class="bh-kpi">
          <p class="bh-kpi-value">{{ data.thresholds.santai_max }} · {{ data.thresholds.sedang_max }}</p>
          <p class="bh-kpi-label">Batas Santai · Sedang</p>
          <p class="bh-kpi-sub">
            Ramai bila &gt; {{ data.thresholds.sedang_max }} pesanan / 60 mnt
            ({{ data.thresholds.source === 'history' ? 'dari riwayat' : 'ambang tetap' }})
          </p>
        </div>
      </div>

      <!-- Peta panas -->
      <section class="bh-card" aria-labelledby="bh-heat-title">
        <div class="bh-card-head">
          <h3 id="bh-heat-title" class="bh-card-title">Peta jam sibuk</h3>
          <div class="bh-legend" aria-hidden="true">
            <span>Sepi</span><span class="bh-legend-bar"></span><span>Ramai</span>
          </div>
        </div>

        <div class="bh-scroll" tabindex="0" role="region" aria-label="Peta jam sibuk, geser untuk melihat semua jam">
          <table class="bh-grid">
            <caption class="bh-sr">Rata-rata pesanan per jam menurut hari dan jam (WIB)</caption>
            <thead>
              <tr>
                <th scope="col" class="bh-corner"></th>
                <th v-for="h in hours" :key="h" scope="col" class="bh-hour">{{ pad(h) }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(name, d) in data.day_names" :key="d">
                <th scope="row" class="bh-day">{{ name.slice(0, 3) }}</th>
                <td
                  v-for="h in hours"
                  :key="h"
                  class="bh-cell"
                  :class="{ 'is-closed': !isOpen(d, h) }"
                  :style="cellStyle(d, h)"
                  :title="cellTitle(d, h)"
                >
                  <span v-if="isOpen(d, h)" class="bh-num">{{ cellText(d, h) }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="bh-foot">Angka = rata-rata pesanan dalam satu jam. Kotak abu = di luar jam buka.</p>
      </section>

      <!-- Tersibuk & paling sepi -->
      <div class="bh-two">
        <section class="bh-card">
          <h3 class="bh-card-title">Jam tersibuk</h3>
          <ol v-if="data.busiest.length" class="bh-list">
            <li v-for="s in data.busiest" :key="s.label">
              <span>{{ s.label }}</span><strong>{{ fmt(s.avg) }}</strong>
            </li>
          </ol>
          <p v-else class="bh-none">Belum ada pesanan di rentang ini.</p>
        </section>

        <section class="bh-card">
          <h3 class="bh-card-title">Jam paling sepi</h3>
          <ol v-if="data.quietest.length" class="bh-list">
            <li v-for="s in data.quietest" :key="s.label">
              <span>{{ s.label }}</span><strong>{{ fmt(s.avg) }}</strong>
            </li>
          </ol>
          <p v-else class="bh-none">Belum cukup data.</p>
          <p v-if="data.quietest.length" class="bh-hint">
            Waktu yang cocok untuk mencoba promo jam sepi.
          </p>
        </section>
      </div>

      <!-- Per hari -->
      <section class="bh-card">
        <h3 class="bh-card-title">Rata-rata pesanan per hari</h3>
        <ul class="bh-days">
          <li v-for="(name, d) in data.day_names" :key="d">
            <span class="bh-days-name">{{ name }}</span>
            <span class="bh-days-track" aria-hidden="true">
              <span class="bh-days-fill" :style="{ width: dayPct(d) + '%' }"></span>
            </span>
            <span class="bh-days-val">
              <template v-if="data.open_hours[d] || !hasSchedule">{{ fmt(data.by_weekday[d]) }}</template>
              <template v-else>Libur</template>
            </span>
          </li>
        </ul>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { crowdAPI } from "@/api/crowd"

const WEEK_OPTIONS = [4, 8, 12]

const weeks   = ref(8)
const data    = ref(null)
const loading = ref(false)
const error   = ref(false)

let requestId = 0
const load = async () => {
  const mine = ++requestId
  loading.value = true
  error.value = false
  try {
    const res = await crowdAPI.getBusyHours(weeks.value)
    if (mine !== requestId) return   // jawaban lama, sudah ada permintaan yang lebih baru
    data.value = res.data
  } catch {
    if (mine !== requestId) return
    error.value = true
  } finally {
    if (mine === requestId) loading.value = false
  }
}

const setWeeks = (w) => { if (w !== weeks.value) { weeks.value = w; load() } }

onMounted(load)
defineExpose({ reload: load, loading })

// ── Turunan ──────────────────────────────────────────────────────────────
const pad = (n) => String(n).padStart(2, "0")
const fmt = (n) => (Number(n) || 0).toLocaleString("id-ID", { maximumFractionDigits: 1 })

const hasSchedule = computed(() => (data.value?.open_hours || []).some(Boolean))

const hours = computed(() => {
  const [a, b] = data.value?.hour_range || [8, 22]
  return Array.from({ length: Math.max(0, b - a) }, (_, i) => a + i)
})

const isOpen = (d, h) => {
  if (!hasSchedule.value) return true
  const o = data.value.open_hours[d]
  return !!o && h >= o[0] && h < o[1]
}

const maxCell = computed(() => {
  let m = 0
  data.value?.grid.forEach((row, d) => row.forEach((v, h) => { if (isOpen(d, h) && v > m) m = v }))
  return m
})

const cellStyle = (d, h) => {
  if (!isOpen(d, h)) return {}
  const v = data.value.grid[d][h]
  if (!v || !maxCell.value) return {}
  const pct = Math.round(10 + (v / maxCell.value) * 80)
  return { background: `color-mix(in srgb, var(--accent) ${pct}%, transparent)` }
}

const cellText = (d, h) => {
  const v = data.value.grid[d][h]
  return v ? fmt(v) : ""
}

const cellTitle = (d, h) => {
  const name = data.value.day_names[d]
  if (!isOpen(d, h)) return `${name} ${pad(h)}.00: di luar jam buka`
  return `${name} ${pad(h)}.00–${pad((h + 1) % 24)}.00: rata-rata ${fmt(data.value.grid[d][h])} pesanan`
}

const busiestDay = computed(() => {
  const by = data.value?.by_weekday || []
  if (!by.some((v) => v > 0)) return null
  const d = by.indexOf(Math.max(...by))
  return { name: data.value.day_names[d], avg: by[d] }
})

const dayPct = (d) => {
  const by = data.value.by_weekday
  const max = Math.max(...by, 0)
  return max ? Math.round((by[d] / max) * 100) : 0
}

const rangeText = computed(() => {
  const r = data.value?.range
  if (!r?.start) return "Belum ada data"
  const f = (iso) => new Date(iso + "T00:00:00+07:00").toLocaleDateString("id-ID", {
    day: "numeric", month: "short", year: "numeric", timeZone: "Asia/Jakarta",
  })
  return `${f(r.start)} – ${f(r.end)}`
})
</script>

<style scoped>
.bh { display: flex; flex-direction: column; gap: 1rem; }

.bh-toolbar { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0.75rem; }
.bh-lead { margin: 0; font-size: 0.8rem; color: var(--text-faint); }
.bh-lead strong { color: var(--text-dim); font-weight: 600; }
.bh-weeks { display: flex; gap: 0.25rem; padding: 0.25rem; background: var(--surface); border: 1px solid var(--border); border-radius: var(--r-md); }
.bh-week {
  min-height: 40px; padding: 0.4rem 0.9rem; border-radius: var(--r-sm); border: 0; cursor: pointer; background: transparent;
  font-family: var(--font-body); font-size: 0.75rem; letter-spacing: -0.01em; color: var(--text-faint);
}
.bh-week:hover { color: var(--text-dim); }
.bh-week.is-on { background: rgb(var(--ink) / 0.1); color: var(--text); }
.bh-week:focus-visible, .bh-retry:focus-visible, .bh-scroll:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

.bh-banner {
  padding: 0.8rem 1rem; border-radius: var(--r-md); font-size: 0.8rem; line-height: 1.5;
  background: color-mix(in srgb, var(--amber) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--amber) 35%, transparent); color: var(--amber-soft);
}

.bh-kpis { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; }
.bh-kpi, .bh-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--r-lg); padding: 1rem 1.1rem;
}
.bh-kpi-value { margin: 0; font-family: var(--font-body); font-size: 1.25rem; font-weight: 700; color: var(--text); }
.bh-kpi-label { margin: 0.25rem 0 0; font-size: 0.75rem; letter-spacing: 0.16em; text-transform: uppercase; color: var(--text-faint); }
.bh-kpi-sub { margin: 0.4rem 0 0; font-size: 0.7rem; color: var(--text-faint); }

.bh-card-head { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; margin-bottom: 0.9rem; }
.bh-card-title { margin: 0 0 0.9rem; font-family: var(--font-body); font-size: 0.75rem; letter-spacing: -0.01em; color: var(--text-faint); font-weight: 600; }
.bh-card-head .bh-card-title { margin: 0; }

.bh-legend { display: flex; align-items: center; gap: 0.5rem; font-size: 0.75rem; color: var(--text-faint); }
.bh-legend-bar { width: 72px; height: 8px; border-radius: 4px; background: linear-gradient(90deg, color-mix(in srgb, var(--accent) 10%, transparent), color-mix(in srgb, var(--accent) 90%, transparent)); }

.bh-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
.bh-grid { border-collapse: separate; border-spacing: 3px; min-width: 100%; }
.bh-corner { width: 36px; }
.bh-hour { min-width: 34px; padding-bottom: 4px; font-size: 0.75rem; font-weight: 400; color: var(--text-faint); text-align: center; }
.bh-day { padding-right: 8px; font-size: 0.7rem; font-weight: 500; color: var(--text-dim); text-align: left; white-space: nowrap; }
.bh-cell { height: 34px; min-width: 34px; border-radius: 6px; text-align: center; background: rgb(var(--ink) / 0.03); }
.bh-cell.is-closed {
  background: repeating-linear-gradient(135deg, transparent 0 4px, rgb(var(--ink) / 0.05) 4px 5px);
  opacity: 0.7;
}
.bh-num { font-size: 0.75rem; color: var(--text); font-variant-numeric: tabular-nums; }
.bh-foot { margin: 0.75rem 0 0; font-size: 0.75rem; color: var(--text-faint); }
.bh-sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }

.bh-two { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.bh-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; }
.bh-list li { display: flex; justify-content: space-between; gap: 0.75rem; padding: 0.6rem 0; border-top: 1px solid rgb(var(--ink) / 0.05); font-size: 0.85rem; color: var(--text-dim); }
.bh-list li:first-child { border-top: 0; padding-top: 0; }
.bh-list strong { color: var(--text); font-variant-numeric: tabular-nums; }
.bh-none, .bh-hint { margin: 0; font-size: 0.75rem; color: var(--text-faint); }
.bh-hint { margin-top: 0.75rem; }

.bh-days { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 0.5rem; }
.bh-days li { display: grid; grid-template-columns: 64px 1fr 56px; align-items: center; gap: 0.75rem; font-size: 0.8rem; }
.bh-days-name { color: var(--text-dim); }
.bh-days-track { height: 8px; border-radius: 4px; background: rgb(var(--ink) / 0.05); overflow: hidden; }
.bh-days-fill { display: block; height: 100%; border-radius: 4px; background: var(--accent); }
.bh-days-val { text-align: right; color: var(--text); font-variant-numeric: tabular-nums; }

.bh-empty { padding: 4rem 1rem; text-align: center; }
.bh-empty-title { margin: 0 0 0.25rem; font-family: var(--font-body); font-size: 0.85rem; letter-spacing: -0.01em; color: var(--text); }
.bh-empty-sub { margin: 0 0 1rem; font-size: 0.75rem; color: var(--text-faint); }
.bh-retry { min-height: 44px; padding: 0.6rem 1.2rem; border: 0; border-radius: var(--r-md); cursor: pointer; background: var(--accent); color: var(--on-accent); font-size: 0.75rem; letter-spacing: 0.1em; text-transform: uppercase; }

.bh-skel-row, .bh-skel-grid { background: var(--surface); border-radius: var(--r-lg); animation: bh-pulse 1.4s ease-in-out infinite; }
.bh-skel-row { height: 88px; margin-bottom: 0.75rem; }
.bh-skel-grid { height: 280px; }
@keyframes bh-pulse { 50% { opacity: 0.55; } }
@media (prefers-reduced-motion: reduce) { .bh-skel-row, .bh-skel-grid { animation: none; } }

@media (max-width: 640px) {
  .bh-kpis, .bh-two { grid-template-columns: 1fr; }
  .bh-days li { grid-template-columns: 56px 1fr 48px; }
}
</style>
