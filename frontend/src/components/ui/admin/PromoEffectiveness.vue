<!--
  PromoEffectiveness.vue — detail efektivitas promo (#15), dipasang di Kelola Promo.
  Satu endpoint agregasi: total diskon keluar, nilai keranjang dengan vs tanpa promo, dan per promo.
-->
<template>
  <section class="rt pe" aria-labelledby="pe-title">
    <div class="pe-head">
      <h2 id="pe-title" class="rt-title pe-h">Efektivitas Promo</h2>
      <div class="pe-periods" role="group" aria-label="Periode">
        <button v-for="p in periods" :key="p.key" type="button" class="pe-period"
                :aria-pressed="period === p.key" @click="period = p.key">{{ p.label }}</button>
      </div>
    </div>

    <div v-if="loading && !data" class="rt-skel" aria-busy="true"></div>
    <div v-else-if="error && !data" class="rt-empty">
      <p class="rt-empty-title">Gagal memuat efektivitas promo</p>
      <button type="button" class="rt-btn" @click="load">Muat ulang</button>
    </div>

    <template v-else-if="data">
      <div class="rt-kpis">
        <div class="rt-card">
          <p class="rt-kpi-value">{{ rp(data.totals.discount_total) }}</p>
          <p class="rt-kpi-label">Diskon yang keluar</p>
          <p class="rt-kpi-sub">dari {{ data.totals.orders_with_promo }} order berpromo</p>
        </div>
        <div class="rt-card">
          <p class="rt-kpi-value">{{ rp(data.comparison.avg_basket_with) }}</p>
          <p class="rt-kpi-label">Rata-rata keranjang, dengan promo</p>
          <p class="rt-kpi-sub">sebelum diskon</p>
        </div>
        <div class="rt-card">
          <p class="rt-kpi-value">{{ rp(data.comparison.avg_basket_without) }}</p>
          <p class="rt-kpi-label">Rata-rata keranjang, tanpa promo</p>
          <p class="rt-kpi-sub">{{ data.totals.orders_without_promo }} order</p>
        </div>
      </div>

      <p v-if="!data.enough_data" class="rt-banner" role="status">
        <strong>Data belum cukup.</strong> Perbandingan butuh minimal {{ data.min_orders_per_group }} order
        dengan promo dan {{ data.min_orders_per_group }} tanpa promo di periode ini.
      </p>
      <p v-else-if="data.comparison.basket_diff_pct !== null" class="rt-lead">
        Keranjang order berpromo rata-rata
        <strong>{{ Math.abs(data.comparison.basket_diff_pct) }}% {{ data.comparison.basket_diff_pct >= 0 ? 'lebih besar' : 'lebih kecil' }}</strong>
        dibanding tanpa promo. {{ data.note }}
      </p>

      <div class="rt-card">
        <h3 class="rt-title">Per promo</h3>
        <div v-if="!data.promos.length" class="rt-empty"><p class="rt-empty-sub">Belum ada promo.</p></div>
        <div v-else class="rt-scroll" tabindex="0" role="region" aria-label="Tabel efektivitas per promo, geser untuk melihat semua kolom">
          <table class="rt-table">
            <thead>
              <tr><th>Kode</th><th class="num">Order</th><th class="num">Diskon</th><th class="num">Keranjang rata-rata</th><th>Kuota</th><th>Status</th></tr>
            </thead>
            <tbody>
              <tr v-for="p in data.promos" :key="p.id">
                <td class="name">{{ p.code }}</td>
                <td class="num">{{ p.orders }}</td>
                <td class="num">{{ rp(p.discount_total) }}</td>
                <td class="num">{{ p.orders ? rp(p.avg_basket) : '—' }}</td>
                <td>{{ p.used_count }}<template v-if="p.max_usage !== null"> / {{ p.max_usage }}</template><template v-else> / ∞</template></td>
                <td>
                  <span class="rt-badge" :class="p.expired ? '' : p.is_active ? 'is-green' : 'is-amber'">
                    {{ p.expired ? 'Kedaluwarsa' : p.is_active ? 'Aktif' : 'Nonaktif' }}
                  </span>
                  <span v-if="p.is_active && !p.expired && p.orders === 0" class="rt-badge is-amber">Belum dipakai</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
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

const { data, loading, error, load } = useReportLoad(analyticsAPI.getPromoEffectiveness, () => params.value)
defineExpose({ reload: load })

const rp = (v) => "Rp" + Math.round(v || 0).toLocaleString("id-ID")
</script>

<style src="@/assets/report-tabs.css"></style>
<style scoped>
.pe { margin-top: 1.25rem; }
.pe-head { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: .75rem; }
.pe-h { margin: 0; }
.pe-periods { display: inline-flex; gap: 4px; padding: 3px; border-radius: var(--r-md); background: rgb(var(--ink) / 0.06); }
.pe-period { min-height: 36px; padding: 0 .9rem; border: 0; border-radius: var(--r-sm); background: transparent; color: var(--text-dim); font: inherit; font-size: .75rem; cursor: pointer; }
.pe-period[aria-pressed="true"] { background: var(--surface); color: var(--text); font-weight: 600; }
.pe-period:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
</style>
