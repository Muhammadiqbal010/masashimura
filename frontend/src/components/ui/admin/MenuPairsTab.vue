<!--
  MenuPairsTab.vue — Pasangan Menu (admin saja, tab di Order Reports).
  Menu yang sering dipesan dalam satu order, sebagai dasar memilih paket yang layak dibuat.
-->
<template>
  <div class="rt">
    <div v-if="loading && !data" class="rt-skel tall" aria-busy="true"></div>

    <div v-else-if="error && !data" class="rt-empty">
      <p class="rt-empty-title">Gagal memuat Pasangan Menu</p>
      <p class="rt-empty-sub">Periksa koneksi atau coba lagi beberapa saat.</p>
      <button type="button" class="rt-btn" @click="load">Muat ulang</button>
    </div>

    <template v-else-if="data">
      <div v-if="!data.enough_data" class="rt-banner" role="status">
        <strong>Data belum cukup.</strong>
        Baru {{ data.multi_item_orders }} order berisi lebih dari satu menu di periode ini.
        Pasangan di bawah bisa kebetulan, jadi jangan dijadikan dasar paket dulu.
      </div>

      <div class="rt-kpis">
        <div class="rt-card">
          <p class="rt-kpi-value">{{ data.total_orders.toLocaleString('id-ID') }}</p>
          <p class="rt-kpi-label">Order dianalisis</p>
        </div>
        <div class="rt-card">
          <p class="rt-kpi-value">{{ data.multi_item_orders.toLocaleString('id-ID') }}</p>
          <p class="rt-kpi-label">Order lebih dari 1 menu</p>
          <p class="rt-kpi-sub">{{ multiPct }}% dari seluruh order</p>
        </div>
        <div class="rt-card">
          <p class="rt-kpi-value">{{ data.pairs_total }}</p>
          <p class="rt-kpi-label">Pasangan ditemukan</p>
          <p class="rt-kpi-sub">muncul bersama minimal {{ data.min_count }}×</p>
        </div>
      </div>

      <section class="rt-card">
        <h3 class="rt-title">Pasangan paling sering</h3>

        <div v-if="!data.pairs.length" class="rt-empty">
          <p class="rt-empty-sub">Belum ada pasangan yang muncul bersama minimal {{ data.min_count }} kali di periode ini.</p>
        </div>
        <div v-else class="rt-scroll" tabindex="0" role="region" aria-label="Tabel pasangan menu, geser untuk melihat semua kolom">
          <table class="rt-table">
            <thead>
              <tr>
                <th>Pasangan</th><th class="num">Bersama</th><th class="num">% order</th>
                <th class="num">Lift</th><th>Kandidat paket</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in data.pairs" :key="`${p.a.id}-${p.b.id}`">
                <td class="name">
                  {{ p.a.name }} <span class="mp-plus" aria-hidden="true">+</span><span class="sr-only"> dan </span> {{ p.b.name }}
                  <span class="mp-conf">
                    {{ p.confidence_a_to_b }}% pemesan {{ p.a.name }} juga pesan {{ p.b.name }};
                    {{ p.confidence_b_to_a }}% sebaliknya
                  </span>
                </td>
                <td class="num">{{ p.count }}×</td>
                <td class="num">{{ p.support }}%</td>
                <td class="num">{{ p.lift }}</td>
                <td><span v-if="p.bundle_candidate" class="rt-badge is-green">Layak dicoba</span><span v-else class="mp-dash">–</span></td>
              </tr>
            </tbody>
          </table>
        </div>

        <p class="rt-lead mp-note">
          Lift di atas 1 berarti pasangan itu dipesan bersama lebih sering daripada kebetulan.
          "Layak dicoba" = muncul bersama minimal 3 kali dan lift di atas 1. Jumlah porsi per menu tidak
          menggandakan hitungan. Item tukar poin tidak dihitung.
        </p>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed } from "vue"
import { analyticsAPI } from "@/api/analytics"
import { useReportLoad } from "@/composables/useReportLoad"

const props = defineProps({ params: { type: Object, required: true } })

const { data, loading, error, load } = useReportLoad(analyticsAPI.getMenuPairs, () => props.params)
defineExpose({ reload: load, loading })

const multiPct = computed(() => {
  const d = data.value
  return d?.total_orders ? Math.round((d.multi_item_orders / d.total_orders) * 100) : 0
})
</script>

<style src="@/assets/report-tabs.css"></style>
<style scoped>
.mp-plus { margin: 0 0.25rem; color: var(--text-faint); }
.mp-conf { display: block; margin-top: 0.2rem; font-size: 0.68rem; font-weight: 400; line-height: 1.4; color: var(--text-faint); }
.mp-dash { color: var(--text-faint); }
.mp-note { margin-top: 0.9rem; font-size: 0.72rem; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
</style>
