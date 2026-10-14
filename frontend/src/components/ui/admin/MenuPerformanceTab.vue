<!--
  MenuPerformanceTab.vue — Performa Menu (tab di Order Reports).
  Volume, kontribusi omzet, dan pengelompokan: Bintang / Andalan / Potensial / Perlu evaluasi.
-->
<template>
  <div class="rt">
    <div v-if="loading && !data" class="rt-skel tall" aria-busy="true"></div>

    <div v-else-if="error && !data" class="rt-empty">
      <p class="rt-empty-title">Gagal memuat Performa Menu</p>
      <p class="rt-empty-sub">Periksa koneksi atau coba lagi beberapa saat.</p>
      <button type="button" class="rt-btn" @click="load">Muat ulang</button>
    </div>

    <template v-else-if="data">
      <div v-if="!data.enough_data" class="rt-banner" role="status">
        <strong>Data belum cukup.</strong>
        Baru {{ data.total_qty }} porsi terjual di periode ini (butuh minimal {{ data.min_items_required }}),
        jadi pengelompokan di bawah masih kasar.
      </div>

      <!-- Kelompok: klik untuk menyaring tabel -->
      <div class="mp-classes" role="group" aria-label="Saring menurut kelompok">
        <button
          v-for="(label, key) in data.class_labels"
          :key="key"
          type="button"
          class="rt-card rt-chip mp-class"
          :class="[`is-${key}`, { 'is-on': filter === key }]"
          :aria-pressed="filter === key"
          @click="filter = filter === key ? null : key"
        >
          <span class="mp-class-n">{{ data.summary[key] }}</span>
          <span class="mp-class-label">{{ label }}</span>
          <span class="mp-class-hint">{{ data.class_hints[key] }}</span>
        </button>
      </div>

      <section class="rt-card">
        <h3 class="rt-title">Semua menu aktif <template v-if="filter">· {{ data.class_labels[filter] }}</template></h3>

        <div v-if="!rows.length" class="rt-empty"><p class="rt-empty-sub">Tidak ada menu di kelompok ini.</p></div>
        <div v-else class="rt-scroll" tabindex="0" role="region" aria-label="Tabel performa menu, geser untuk melihat semua kolom">
          <table class="rt-table">
            <thead>
              <tr>
                <th>Menu</th><th class="num">Terjual</th><th class="num">Omzet</th>
                <th>Kontribusi</th><th>Kelompok</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in rows" :key="m.id">
                <td class="name">
                  {{ m.name }}
                  <span v-if="m.category" class="mp-cat">{{ m.category }}</span>
                </td>
                <td class="num">{{ m.qty.toLocaleString('id-ID') }}</td>
                <td class="num">{{ rp(m.revenue) }}</td>
                <td class="mp-share">
                  <span class="rt-bar" aria-hidden="true"><span :style="{ width: Math.min(100, m.revenue_share * 2) + '%' }"></span></span>
                  <span class="mp-share-n">{{ m.revenue_share }}%</span>
                </td>
                <td><span class="rt-badge" :class="badgeTone[m.class]">{{ m.class_label }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>

        <p class="rt-lead mp-note">
          Populer = terjual minimal {{ data.thresholds.popular_min_qty }} porsi (70% dari rata-rata
          {{ data.thresholds.avg_qty_per_menu }} porsi per menu). Harga tinggi = harga rata-rata per porsi
          di atas {{ rp(data.thresholds.avg_unit_price) }}. Biaya bahan belum tercatat, jadi harga dipakai
          sebagai pendekatan margin.
        </p>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from "vue"
import { analyticsAPI } from "@/api/analytics"
import { useReportLoad } from "@/composables/useReportLoad"

const props = defineProps({ params: { type: Object, required: true } })

const { data, loading, error, load } = useReportLoad(analyticsAPI.getMenuPerformance, () => props.params)
defineExpose({ reload: load, loading })

const filter = ref(null)
const rows = computed(() => (data.value?.menus || []).filter((m) => !filter.value || m.class === filter.value))
const rp = (v) => "Rp " + Math.round(v || 0).toLocaleString("id-ID")
const badgeTone = { bintang: "is-green", andalan: "is-blue", potensial: "is-amber", evaluasi: "is-red" }
</script>

<style src="@/assets/report-tabs.css"></style>
<style scoped>
.mp-classes { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 0.75rem; }
.mp-class { display: flex; flex-direction: column; gap: 0.3rem; border-color: rgb(var(--ink) / 0.05); }
.mp-class:hover { border-color: rgb(var(--ink) / 0.15); }
.mp-class.is-on { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 6%, var(--surface)); }
.mp-class-n { font-family: 'Manrope', system-ui, sans-serif; font-size: 1.6rem; font-weight: 700; color: var(--text); line-height: 1; }
.mp-class-label { font-size: 0.7rem; letter-spacing: 0.14em; text-transform: uppercase; color: var(--text-dim); }
.mp-class-hint { font-size: 0.72rem; line-height: 1.45; color: var(--text-faint); }
.mp-cat { margin-left: 0.5rem; font-size: 0.72rem; font-weight: 400; color: var(--text-faint); }
.mp-share { display: flex; align-items: center; gap: 0.6rem; min-width: 130px; }
.mp-share .rt-bar { flex: 1; }
.mp-share-n { font-size: 0.72rem; font-variant-numeric: tabular-nums; color: var(--text-faint); min-width: 36px; text-align: right; }
.mp-note { margin-top: 0.9rem; font-size: 0.72rem; }
</style>
