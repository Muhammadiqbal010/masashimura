<!--
  SimulationPanel.vue — tab kecil "Simulasi" di bagian Prediksi (Dashboard, #19).
  Hanya skenario yang punya dasar data historis:
    1. Target: aritmatika dari rata-rata omzet per hari buka bulan ini (bukan model prediksi).
    2. Promo : estimasi kasar dari selisih hari ber-promo vs tanpa promo (wajib berlabel estimasi).
  Angka dasar dari server; slider dan input hanya menghitung ulang di layar.
-->
<template>
  <div class="sim">
    <div v-if="loading && !data" class="sim-skel" aria-busy="true"></div>

    <div v-else-if="error && !data" class="sim-empty">
      <p>Simulasi gagal dimuat.</p>
      <button type="button" class="sim-btn" @click="load">Muat ulang</button>
    </div>

    <div v-else-if="data" class="sim-grid">
      <!-- ── 1. Simulasi target ───────────────────────────────────── -->
      <section class="sim-card" aria-labelledby="sim-target-title">
        <h4 id="sim-target-title" class="sim-title">Simulasi target · {{ t.month_label }}</h4>

        <p v-if="!t.enough_data" class="sim-note" role="status">
          Data belum cukup. Simulasi butuh minimal {{ t.min_open_days }} hari buka yang sudah lewat bulan ini
          (baru {{ t.open_days_elapsed }}).
        </p>

        <template v-else>
          <label class="sim-label" for="sim-growth">
            Kalau rata-rata omzet harian
            <strong>{{ growth >= 0 ? 'naik' : 'turun' }} {{ Math.abs(growth) }}%</strong>
          </label>
          <input id="sim-growth" v-model.number="growth" class="sim-range" type="range" min="-50" max="100" step="5" />
          <div class="sim-scale" aria-hidden="true"><span>-50%</span><span>0%</span><span>+100%</span></div>

          <p class="sim-result">
            <span class="sim-result-label">Omzet bulan ini mencapai</span>
            <span class="sim-result-value">{{ rp(projected) }}</span>
          </p>

          <p v-if="t.target" class="sim-vs" :class="projected >= t.target ? 'is-ok' : 'is-low'">
            <template v-if="projected >= t.target">Mencapai target {{ rp(t.target) }} (lebih {{ rp(projected - t.target) }}).</template>
            <template v-else>Masih kurang {{ rp(t.target - projected) }} dari target {{ rp(t.target) }}.</template>
          </p>
          <p v-if="t.target_reached" class="sim-vs is-ok">Target bulan ini sudah tercapai.</p>
          <p v-else-if="t.needed_growth_pct !== null" class="sim-hint">
            Untuk mencapai target, rata-rata harian perlu
            <strong>{{ t.needed_growth_pct > 0 ? 'naik ' + t.needed_growth_pct : 'turun maksimal ' + Math.abs(t.needed_growth_pct) }}%</strong>
            dari sekarang.
          </p>
          <p v-else-if="!t.target" class="sim-hint">Isi target bulanan di Pengaturan Sistem untuk melihat selisihnya.</p>

          <dl class="sim-facts">
            <div><dt>Omzet berjalan</dt><dd>{{ rp(t.realized) }}</dd></div>
            <div><dt>Rata-rata per hari buka</dt><dd>{{ rp(t.avg_open_day) }}</dd></div>
            <div><dt>Sisa hari buka</dt><dd>{{ t.remaining_open_days }} hari</dd></div>
          </dl>
        </template>
        <p class="sim-foot">{{ data.notes.target }}</p>
      </section>

      <!-- ── 2. Simulasi promo ────────────────────────────────────── -->
      <section class="sim-card" aria-labelledby="sim-promo-title">
        <h4 id="sim-promo-title" class="sim-title">Simulasi promo <span class="sim-badge">Estimasi</span></h4>

        <p v-if="!p.enough_data" class="sim-note" role="status">
          Data belum cukup. Butuh minimal {{ p.min_days_per_group }} hari ber-promo dan {{ p.min_days_per_group }} hari tanpa promo
          dalam {{ p.lookback_days }} hari terakhir (sekarang {{ p.promo_days }} dan {{ p.non_promo_days }}).
        </p>

        <template v-else>
          <p class="sim-compare">
            Rata-rata omzet hari ber-promo <strong>{{ rp(p.avg_promo_day) }}</strong>,
            hari tanpa promo <strong>{{ rp(p.avg_non_promo_day) }}</strong>
            ({{ p.diff >= 0 ? '+' : '' }}{{ p.diff_pct }}%).
          </p>

          <label class="sim-label" for="sim-promo-days">
            Kalau menjalankan promo di <strong>{{ promoDays }} hari buka</strong> lagi bulan ini
          </label>
          <input id="sim-promo-days" v-model.number="promoDays" class="sim-range" type="range" min="0" :max="Math.max(t.remaining_open_days, 0)" step="1" :disabled="t.remaining_open_days <= 0" />

          <p class="sim-result">
            <span class="sim-result-label">Estimasi tambahan omzet</span>
            <span class="sim-result-value">≈ {{ p.diff >= 0 ? '' : '-' }}{{ rp(Math.abs(promoExtra)) }}</span>
          </p>
          <p v-if="p.diff <= 0" class="sim-hint">Hari ber-promo tidak lebih ramai dari hari biasa di data ini, jadi promo tidak terlihat menambah omzet.</p>
        </template>
        <p class="sim-foot">{{ data.notes.promo }}</p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { analyticsAPI } from '@/api'

const data = ref(null)
const loading = ref(true)
const error = ref(false)
const growth = ref(0)
const promoDays = ref(0)

const rp = (v) => 'Rp' + Math.round(Number(v) || 0).toLocaleString('id-ID')

const t = computed(() => data.value?.target || {})
const p = computed(() => data.value?.promo || {})

// realisasi + rata-rata harian x (1 + X%) x sisa hari buka
const projected = computed(() =>
  (t.value.realized || 0) + (t.value.avg_open_day || 0) * (1 + growth.value / 100) * (t.value.remaining_open_days || 0)
)
const promoExtra = computed(() => promoDays.value * (p.value.diff || 0))

const load = async () => {
  loading.value = true
  error.value = false
  try {
    const res = await analyticsAPI.getSimulation()
    data.value = res.data
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.sim-grid { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(min(100%, 320px), 1fr)); }
.sim-card { background: var(--surface-2); border: 1px solid rgb(var(--ink) / 0.05); border-radius: 12px; padding: 1.1rem 1.2rem; min-width: 0; display: flex; flex-direction: column; gap: .7rem; }
.sim-title { margin: 0; font-size: .85rem; font-weight: 600; color: var(--text); display: flex; gap: .5rem; align-items: center; flex-wrap: wrap; }
.sim-badge { padding: .1rem .5rem; border-radius: 999px; font-size: 0.72rem; letter-spacing: .08em; text-transform: uppercase; background: color-mix(in srgb, var(--amber-soft) 18%, transparent); color: var(--amber-soft); }
.sim-label { font-size: .8rem; color: var(--text-2); }
.sim-range { width: 100%; min-height: 32px; accent-color: var(--red-soft); }
.sim-range:focus-visible { outline: 2px solid var(--red-soft); outline-offset: 2px; }
.sim-scale { display: flex; justify-content: space-between; font-size: 0.72rem; color: var(--text-faint); margin-top: -.4rem; }
.sim-result { margin: .2rem 0 0; display: flex; flex-direction: column; gap: .15rem; }
.sim-result-label { font-size: .72rem; color: var(--text-faint); }
.sim-result-value { font-size: 1.5rem; font-weight: 600; color: var(--text); font-variant-numeric: tabular-nums; }
.sim-vs { margin: 0; font-size: .8rem; }
.sim-vs.is-ok { color: var(--green-soft); }
.sim-vs.is-low { color: var(--amber-soft); }
.sim-hint, .sim-note, .sim-compare { margin: 0; font-size: .78rem; line-height: 1.55; color: var(--text-dim); }
.sim-facts { margin: 0; display: grid; gap: .35rem; }
.sim-facts div { display: flex; justify-content: space-between; gap: 1rem; font-size: .75rem; }
.sim-facts dt { color: var(--text-faint); }
.sim-facts dd { margin: 0; color: var(--text-2); font-variant-numeric: tabular-nums; }
.sim-foot { margin: auto 0 0; padding-top: .5rem; font-size: 0.72rem; line-height: 1.5; color: var(--text-faint); border-top: 1px solid rgb(var(--ink) / 0.06); }
.sim-skel { height: 220px; border-radius: 12px; background: rgb(var(--ink) / 0.05); }
.sim-empty { padding: 2rem 1rem; text-align: center; color: var(--text-dim); font-size: .85rem; }
.sim-btn { min-height: 40px; padding: 0 1rem; border-radius: 8px; border: 1px solid rgb(var(--ink) / 0.15); background: transparent; color: var(--text); cursor: pointer; }
</style>
