<!--
  SimulationPanel.vue — tab kecil "Simulasi" di bagian Prediksi (Dashboard, #19).
  Hanya skenario yang punya dasar data historis:
    1. Target: titik awal prediksi model yang sama dengan Briefing (cadangan: rata-rata per hari buka).
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
          Data belum cukup. Simulasi butuh prediksi model atau minimal {{ t.min_open_days }} hari buka yang sudah lewat bulan ini
          (baru {{ t.open_days_elapsed }}).
        </p>

        <template v-else>
          <label class="sim-label" for="sim-growth">
            Kalau omzet hari-hari tersisa
            <strong v-if="growth === 0">tetap seperti sekarang</strong>
            <strong v-else>{{ growth > 0 ? 'naik' : 'turun' }} {{ Math.abs(growth) }}%</strong>
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
          <p v-else-if="t.needed_per_open_day !== null && t.needed_per_open_day !== undefined" class="sim-hint">
            Untuk mencapai target, sisa {{ t.remaining_open_days }} hari buka perlu rata-rata
            <strong>{{ rp(t.needed_per_open_day) }} per hari</strong>
            (prediksi {{ rp(t.forecast_per_open_day ?? t.avg_open_day) }}<template v-if="t.needed_multiplier"> · sekitar {{ t.needed_multiplier }}× lipat</template>).
          </p>
          <p v-if="unrealisticTarget" class="sim-warn" role="status">
            Targetnya kemungkinan terlalu tinggi untuk bulan ini.
            <RouterLink v-if="auth.isOwner" :to="{ name: 'AdminSettings' }" class="sim-link">Tinjau target di Pengaturan</RouterLink>
          </p>
          <p v-else-if="!t.target" class="sim-hint">Isi target bulanan di Pengaturan Sistem untuk melihat selisihnya.</p>

          <dl class="sim-facts">
            <div><dt>Omzet berjalan</dt><dd>{{ rp(t.realized) }}</dd></div>
            <div><dt>{{ t.basis === 'model' ? 'Prediksi per hari buka' : 'Rata-rata per hari buka' }}</dt><dd>{{ rp(t.forecast_per_open_day ?? t.avg_open_day) }}</dd></div>
            <div><dt>Sisa hari buka</dt><dd>{{ t.remaining_open_days }} hari</dd></div>
          </dl>
        </template>
        <p class="sim-foot">{{ data.notes.target }}</p>
      </section>

      <!-- ── 2. Simulasi promo ────────────────────────────────────── -->
      <section class="sim-card" aria-labelledby="sim-promo-title">
        <h4 id="sim-promo-title" class="sim-title">Simulasi promo <span class="sim-badge">Estimasi</span></h4>

        <div v-if="!p.enough_data" class="sim-progress" role="status">
          <p class="sim-note">
            Data belum cukup. Simulasi butuh minimal {{ p.min_days_per_group }} hari ber-promo dan
            {{ p.min_days_per_group }} hari tanpa promo dalam {{ p.lookback_days }} hari terakhir.
          </p>
          <div v-for="g in promoGroups" :key="g.label" class="sim-prog-row">
            <span class="sim-prog-label">{{ g.label }}</span>
            <span class="sim-prog-track" aria-hidden="true"><span class="sim-prog-fill" :class="{ done: g.done }" :style="{ width: g.pct + '%' }"></span></span>
            <span class="sim-prog-val">{{ g.have }}/{{ g.need }}</span>
          </div>
        </div>

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
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const data = ref(null)
const loading = ref(true)
const error = ref(false)
const growth = ref(0)
const promoDays = ref(0)

const rp = (v) => 'Rp' + Math.round(Number(v) || 0).toLocaleString('id-ID')

const t = computed(() => data.value?.target || {})
const p = computed(() => data.value?.promo || {})

// bagian pasti (omzet berjalan + hari ini) + prediksi hari tersisa x (1 + X%), sama dasarnya dengan Briefing
const projected = computed(() =>
  (t.value.fixed_part || 0) + (t.value.forecast_remaining || 0) * (1 + growth.value / 100)
)
// Target dianggap tidak realistis kalau butuh lebih dari 3x lipat rata-rata harian sekarang.
const unrealisticTarget = computed(() => (t.value.needed_multiplier || 0) > 3)

const promoGroups = computed(() => {
  const need = p.value.min_days_per_group || 0
  const mk = (label, have) => ({ label, have: have || 0, need, done: (have || 0) >= need, pct: need ? Math.min(100, Math.round(((have || 0) / need) * 100)) : 0 })
  return [mk('Hari ber-promo', p.value.promo_days), mk('Hari tanpa promo', p.value.non_promo_days)]
})
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
.sim-grid { align-items: start; display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(min(100%, 320px), 1fr)); }
.sim-card { background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--r-md); padding: 1.1rem 1.2rem; min-width: 0; display: flex; flex-direction: column; gap: .7rem; }
.sim-title { margin: 0; font-size: .85rem; font-weight: 600; color: var(--text); display: flex; gap: .5rem; align-items: center; flex-wrap: wrap; }
.sim-badge { padding: .1rem .5rem; border-radius: 999px; font-size: 0.75rem; letter-spacing: .08em; text-transform: uppercase; background: color-mix(in srgb, var(--amber-soft) 18%, transparent); color: var(--amber-soft); }
.sim-label { font-size: .8rem; color: var(--text-2); }
.sim-range { width: 100%; min-height: 32px; accent-color: var(--red-soft); }
.sim-range:focus-visible { outline: 2px solid var(--red-soft); outline-offset: 2px; }
.sim-scale { display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-faint); margin-top: -.4rem; }
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
.sim-warn { margin: 0; padding: .5rem .7rem; font-size: .76rem; line-height: 1.45; color: var(--amber-soft); background: color-mix(in srgb, var(--amber-soft) 9%, transparent); border: 1px solid color-mix(in srgb, var(--amber-soft) 28%, transparent); border-radius: 10px; }
.sim-link { color: inherit; font-weight: 600; text-decoration: underline; text-underline-offset: 2px; }
.sim-progress { display: flex; flex-direction: column; gap: .55rem; }
.sim-prog-row { display: grid; grid-template-columns: 8.5rem 1fr 2.6rem; gap: .6rem; align-items: center; font-size: .75rem; color: var(--text-2); }
@media (max-width: 480px) { .sim-prog-row { grid-template-columns: 1fr 2.6rem; } .sim-prog-row .sim-prog-track { grid-column: 1 / -1; grid-row: 2; } }
.sim-prog-track { height: 6px; border-radius: 99px; background: var(--border); overflow: hidden; }
.sim-prog-fill { display: block; height: 100%; border-radius: 99px; background: var(--amber-soft); }
.sim-prog-fill.done { background: var(--green-soft); }
.sim-prog-val { text-align: right; font-variant-numeric: tabular-nums; color: var(--text-dim); }
.sim-foot { margin: auto 0 0; padding-top: .5rem; font-size: 0.75rem; line-height: 1.5; color: var(--text-faint); border-top: 1px solid rgb(var(--ink) / 0.06); }
.sim-skel { height: 220px; border-radius: var(--r-md); background: rgb(var(--ink) / 0.05); }
.sim-empty { padding: 2rem 1rem; text-align: center; color: var(--text-dim); font-size: .85rem; }
.sim-btn { min-height: 40px; padding: 0 1rem; border-radius: var(--r-sm); border: 1px solid var(--border-strong); background: transparent; color: var(--text); cursor: pointer; }
</style>
