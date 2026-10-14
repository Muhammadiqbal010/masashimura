<!--
  PointEffectiveness.vue — detail efektivitas poin (#15), dipasang di Kelola Reward Poin.
  Poin terbit vs tertukar vs hangus, dan reward yang paling sering ditukar.
-->
<template>
  <section class="rt pe" aria-labelledby="pt-title">
    <div class="pe-head">
      <h2 id="pt-title" class="rt-title pe-h">Efektivitas Poin</h2>
      <div class="pe-periods" role="group" aria-label="Periode">
        <button v-for="p in periods" :key="p.key" type="button" class="pe-period"
                :aria-pressed="period === p.key" @click="period = p.key">{{ p.label }}</button>
      </div>
    </div>

    <div v-if="loading && !data" class="rt-skel" aria-busy="true"></div>
    <div v-else-if="error && !data" class="rt-empty">
      <p class="rt-empty-title">Gagal memuat efektivitas poin</p>
      <button type="button" class="rt-btn" @click="load">Muat ulang</button>
    </div>

    <template v-else-if="data">
      <div class="rt-kpis">
        <div class="rt-card">
          <p class="rt-kpi-value">{{ n(data.points.issued) }}</p>
          <p class="rt-kpi-label">Poin terbit</p>
          <p class="rt-kpi-sub">dari order lunas</p>
        </div>
        <div class="rt-card">
          <p class="rt-kpi-value">{{ n(data.points.redeemed) }}</p>
          <p class="rt-kpi-label">Poin tertukar</p>
          <p class="rt-kpi-sub">
            <template v-if="data.points.redeem_rate_pct !== null">{{ data.points.redeem_rate_pct }}% dari yang terbit</template>
            <template v-else>belum ada poin terbit</template>
          </p>
        </div>
        <div class="rt-card">
          <p class="rt-kpi-value">{{ n(data.points.expired) }}</p>
          <p class="rt-kpi-label">Poin hangus</p>
          <p class="rt-kpi-sub">tidak order sejak lama</p>
        </div>
        <div class="rt-card">
          <p class="rt-kpi-value">{{ n(data.members.outstanding_points) }}</p>
          <p class="rt-kpi-label">Poin beredar saat ini</p>
          <p class="rt-kpi-sub">{{ data.members.with_points }} dari {{ data.members.total }} member punya poin</p>
        </div>
      </div>

      <div class="rt-card">
        <h3 class="rt-title">Reward paling sering ditukar</h3>
        <div v-if="!data.top_rewards.length" class="rt-empty"><p class="rt-empty-sub">Belum ada penukaran poin di periode ini.</p></div>
        <div v-else class="rt-scroll" tabindex="0" role="region" aria-label="Tabel reward paling sering ditukar, geser untuk melihat semua kolom">
          <table class="rt-table">
            <thead><tr><th>Menu</th><th class="num">Ditukar</th><th class="num">Biaya poin</th><th class="num">Total poin (estimasi)</th></tr></thead>
            <tbody>
              <tr v-for="r in data.top_rewards" :key="r.menu_id">
                <td class="name">{{ r.name }}</td>
                <td class="num">{{ r.times }}x</td>
                <td class="num">{{ r.point_cost ?? '—' }}</td>
                <td class="num">{{ r.points_estimate !== null ? '≈ ' + n(r.points_estimate) : '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="rt-lead pt-note">{{ data.note }}</p>
      </div>
    </template>
  </section>
</template>

<script setup>
import { ref, computed } from "vue"
import { analyticsAPI } from "@/api/analytics"
import { useReportLoad } from "@/composables/useReportLoad"

const periods = [
  { key: "30d", label: "30 hari", params: { period: "week", days: 30 } },
  { key: "month", label: "Bulan ini", params: { period: "month" } },
  { key: "all", label: "Semua", params: { period: "lifetime" } },
]
const period = ref("30d")
const params = computed(() => periods.find((p) => p.key === period.value).params)

const { data, loading, error, load } = useReportLoad(analyticsAPI.getPointEffectiveness, () => params.value)
defineExpose({ reload: load })

const n = (v) => Math.round(v || 0).toLocaleString("id-ID")
</script>

<style src="@/assets/report-tabs.css"></style>
<style scoped>
.pe { margin-top: 1.25rem; }
.pe-head { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: .75rem; }
.pe-h { margin: 0; }
.pe-periods { display: inline-flex; gap: 4px; padding: 3px; border-radius: 12px; background: rgb(var(--ink) / 0.06); }
.pe-period { min-height: 36px; padding: 0 .9rem; border: 0; border-radius: 9px; background: transparent; color: var(--text-dim); font: inherit; font-size: .75rem; cursor: pointer; }
.pe-period[aria-pressed="true"] { background: var(--surface); color: var(--text); font-weight: 600; }
.pe-period:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.pt-note { margin-top: .8rem; }
</style>
