<!--
  BundleSuggestions.vue — "Saran Paket" di tab Paket (Kelola Menu, admin saja).
  Menggabungkan menu terlaris (makanan dan minuman), data dipesan-bareng, dan kemiripan teks,
  lalu menyarankan pasangan beserta harga paketnya. "Buat paket ini" membuka form Paket yang
  sudah terisi; owner tetap bisa mengubah nama, isi, dan harga sebelum menyimpan.
  Margin tidak dihitung karena biaya bahan (HPP) tidak tercatat.
-->
<template>
  <section class="bs adm-card" aria-labelledby="bs-title">
    <div class="bs-head">
      <div class="bs-head-text">
        <h3 id="bs-title" class="bs-title"><Sparkles :size="15" aria-hidden="true" /> Saran paket</h3>
        <p class="bs-lead">Pasangan makanan + minuman dari menu terlaris, dengan harga paket yang disarankan.</p>
      </div>
      <label class="bs-period">
        <span class="bs-sr">Periode data penjualan</span>
        <select v-model="periodKey" class="bs-select">
          <option v-for="p in PERIODS" :key="p.key" :value="p.key">{{ p.label }}</option>
        </select>
      </label>
    </div>

    <div v-if="loading && !perf" class="bs-skel" aria-busy="true"></div>

    <div v-else-if="error && !perf" class="bs-note">
      <p>Data penjualan gagal dimuat, jadi saran belum bisa dibuat.</p>
      <button type="button" class="adm-btn adm-btn--ghost" @click="load">Coba lagi</button>
    </div>

    <template v-else>
      <p v-if="perf && !perf.enough_data" class="bs-banner" role="status">
        <strong>Data penjualan masih sedikit</strong> ({{ perf.total_qty }} porsi terjual di periode ini).
        Saran lebih mudah meleset, anggap sebagai titik awal saja.
      </p>

      <p v-if="result.status === 'no_sales'" class="bs-none">Belum ada penjualan di periode ini, jadi belum ada yang bisa disarankan.</p>
      <p v-else-if="result.status === 'no_group'" class="bs-none">
        Belum ada pasangan makanan dan minuman yang laku di periode ini. Coba pilih periode yang lebih panjang.
      </p>
      <p v-else-if="result.status === 'none'" class="bs-none">Semua pasangan terlaris sudah ada di daftar paket.</p>

      <ul v-else class="bs-list">
        <li v-for="(s, i) in result.suggestions" :key="s.food.id + '-' + s.drink.id" class="bs-item">
          <div class="bs-item-top">
            <div class="bs-names">
              <span class="bs-rank" aria-hidden="true">{{ i + 1 }}</span>
              <div>
                <p class="bs-pair">{{ s.food.name }} <span class="bs-plus" aria-hidden="true">+</span><span class="bs-sr"> dan </span> {{ s.drink.name }}</p>
                <span class="bs-badge" :class="'is-' + s.evidence">{{ EVIDENCE_LABEL[s.evidence] }}</span>
              </div>
            </div>
            <button type="button" class="adm-btn adm-btn--primary bs-use" @click="$emit('use', s.draft)">
              Buat paket ini
            </button>
          </div>

          <p class="bs-price">
            <strong>{{ rp(s.price.price) }}</strong>
            <span class="bs-normal">normal {{ rp(s.price.normal) }}</span>
            <span class="bs-save">hemat {{ rp(s.price.normal - s.price.price) }} ({{ s.price.rate }}%)</span>
          </p>
          <p class="bs-range">Rentang wajar {{ rp(s.price.min) }} sampai {{ rp(s.price.max) }}</p>

          <ul class="bs-reasons">
            <li v-for="r in s.reasons" :key="r">{{ r }}</li>
          </ul>
        </li>
      </ul>

      <p class="bs-note-text">
        Diskon disesuaikan bukti: pasangan yang sudah sering dipesan bareng diberi diskon tipis, yang belum pernah
        diberi lebih besar sebagai pemicu. Biaya bahan tidak tercatat, jadi pastikan harga akhir masih untung
        sebelum menyimpan.
      </p>
    </template>
  </section>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { Sparkles } from 'lucide-vue-next'
import { analyticsAPI } from '@/api/analytics'
import { buildIndex } from '@/utils/recommender'
import { suggestBundles } from '@/utils/bundleSuggester'

const props = defineProps({
  menus: { type: Array, default: () => [] },
  bundles: { type: Array, default: () => [] },
})
defineEmits(['use'])

const PERIODS = [
  { key: 'lifetime', label: 'Semua waktu', params: { period: 'lifetime' } },
  { key: '30', label: '30 hari terakhir', params: { period: 'week', days: 30 } },
  { key: '14', label: '14 hari terakhir', params: { period: 'week', days: 14 } },
]
const EVIDENCE_LABEL = {
  kuat: 'Sering dipesan bareng',
  sedang: 'Pernah dipesan bareng',
  dasar: 'Dari popularitas saja',
}

const periodKey = ref('lifetime')
const perf = ref(null)
const pairs = ref([])
const loading = ref(false)
const error = ref(false)
let latest = 0

const load = async () => {
  const mine = ++latest
  loading.value = true
  error.value = false
  const params = PERIODS.find((p) => p.key === periodKey.value).params
  try {
    const [perfRes, pairRes] = await Promise.all([
      analyticsAPI.getMenuPerformance(params),
      // Data pasangan opsional: kalau gagal, saran tetap jalan dari popularitas.
      analyticsAPI.getMenuPairs({ ...params, min_count: 2 }).catch(() => null),
    ])
    if (mine !== latest) return
    perf.value = perfRes.data
    pairs.value = pairRes?.data?.pairs || []
  } catch {
    if (mine !== latest) return
    error.value = true
  } finally {
    if (mine === latest) loading.value = false
  }
}

onMounted(load)
watch(periodKey, load)

const index = computed(() => buildIndex(props.menus))
const result = computed(() =>
  suggestBundles({
    menus: props.menus,
    performance: perf.value?.menus || [],
    pairs: pairs.value,
    bundles: props.bundles,
    index: index.value,
    limit: 5,
  })
)

const rp = (v) => 'Rp' + Math.round(Number(v) || 0).toLocaleString('id-ID')
</script>

<style scoped>
.bs { padding: 1.1rem; display: flex; flex-direction: column; gap: 0.9rem; }
.bs-head { display: flex; flex-wrap: wrap; align-items: flex-start; justify-content: space-between; gap: 0.75rem; }
.bs-title { display: flex; align-items: center; gap: 0.4rem; margin: 0; font-size: 0.95rem; font-weight: 700; color: var(--text); }
.bs-lead { margin: 0.25rem 0 0; font-size: 0.78rem; color: var(--text-faint); }
.bs-select {
  min-height: 40px; padding: 0 0.75rem; border-radius: 10px;
  border: 1px solid rgb(var(--ink) / 0.1); background: rgb(var(--ink) / 0.04);
  color: var(--text); font-family: inherit; font-size: 0.8rem; cursor: pointer;
}
.bs-select:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.bs-sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }

.bs-skel { height: 96px; border-radius: 12px; background: rgb(var(--ink) / 0.05); animation: bs-pulse 1.4s ease-in-out infinite; }
@keyframes bs-pulse { 50% { opacity: 0.5; } }
@media (prefers-reduced-motion: reduce) { .bs-skel { animation: none; } }

.bs-note { display: flex; flex-direction: column; align-items: flex-start; gap: 0.6rem; font-size: 0.82rem; color: var(--text-dim); }
.bs-note p { margin: 0; }
.bs-banner {
  margin: 0; padding: 0.65rem 0.8rem; border-radius: 10px; font-size: 0.78rem; line-height: 1.45;
  color: var(--text-dim); background: rgb(var(--ink) / 0.04); border: 1px solid rgb(var(--ink) / 0.08);
}
.bs-none { margin: 0; font-size: 0.82rem; color: var(--text-faint); }

.bs-list { display: flex; flex-direction: column; margin: 0; padding: 0; list-style: none; }
.bs-item { display: flex; flex-direction: column; gap: 0.5rem; padding: 0.9rem 0; }
.bs-item:first-child { padding-top: 0; }
.bs-item + .bs-item { border-top: 1px solid rgb(var(--ink) / 0.06); }
.bs-item-top { display: flex; flex-wrap: wrap; align-items: flex-start; justify-content: space-between; gap: 0.6rem; }
.bs-names { display: flex; gap: 0.65rem; min-width: 0; flex: 1 1 14rem; }
.bs-rank {
  flex-shrink: 0; width: 1.5rem; height: 1.5rem; border-radius: 999px; display: grid; place-items: center;
  font-size: 0.75rem; font-weight: 700; color: var(--text-dim); background: rgb(var(--ink) / 0.06);
}
.bs-pair { margin: 0 0 0.3rem; font-size: 0.88rem; font-weight: 600; color: var(--text); }
.bs-plus { margin: 0 0.2rem; color: var(--text-faint); }
.bs-badge { display: inline-block; padding: 0.1rem 0.5rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; background: rgb(var(--ink) / 0.06); color: var(--text-dim); }
.bs-badge.is-kuat { background: rgb(34 197 94 / 0.14); color: rgb(22 163 74); }
.bs-badge.is-sedang { background: rgb(245 158 11 / 0.14); color: rgb(180 83 9); }
.bs-use { min-height: 40px; }
@media (max-width: 480px) { .bs-use { width: 100%; } }

.bs-price { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.2rem 0.6rem; margin: 0; padding-left: 2.15rem; font-size: 0.9rem; color: var(--text); }
.bs-normal { font-size: 0.75rem; color: var(--text-faint); text-decoration: line-through; }
.bs-save { font-size: 0.75rem; font-weight: 600; color: rgb(22 163 74); }
.bs-range { margin: 0; padding-left: 2.15rem; font-size: 0.75rem; color: var(--text-faint); }
.bs-reasons { margin: 0; padding: 0 0 0 2.15rem; list-style: none; display: flex; flex-direction: column; gap: 0.15rem; }
.bs-reasons li { font-size: 0.75rem; color: var(--text-dim); }
.bs-reasons li::before { content: '· '; color: var(--text-faint); }
.bs-note-text { margin: 0; font-size: 0.75rem; line-height: 1.5; color: var(--text-faint); }
</style>
