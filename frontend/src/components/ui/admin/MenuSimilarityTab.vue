<!--
  MenuSimilarityTab.vue — Kemiripan Menu (admin saja, tab di Kelola Menu).
  Membantu owner menyusun paket atau promo dengan melihat menu mana yang mirip satu sama lain.
  Dihitung di browser dari daftar menu (TF-IDF + cosine similarity), BUKAN dari data penjualan.
-->
<template>
  <div class="rt">
    <p class="rt-lead">
      <strong>Kemiripan menu</strong> dihitung dari teks menu (nama, kategori, deskripsi, opsi) memakai
      TF-IDF dan cosine similarity. Ini bukan data penjualan: pakai sebagai bahan ide paket atau promo,
      bukan bukti bahwa dua menu saling bersaing.
    </p>

    <div v-if="noDescNotice" class="rt-banner" role="status">
      <strong>{{ noDescCount }} dari {{ listed.length }} menu belum punya deskripsi.</strong>
      Kemiripannya jadi hanya bergantung pada nama dan kategori. Mengisi deskripsi membuat hasilnya lebih akurat.
    </div>

    <div v-if="listed.length < 2" class="rt-card">
      <div class="rt-empty">
        <p class="rt-empty-title">Menu belum cukup</p>
        <p class="rt-empty-sub">Butuh minimal 2 menu aktif untuk membandingkan kemiripan.</p>
      </div>
    </div>

    <template v-else>
      <!-- ── Cari menu serupa ── -->
      <section class="rt-card">
        <h3 class="rt-title">Cari menu serupa</h3>

        <label class="ms-field">
          <span class="ms-label">Pilih menu</span>
          <select class="ms-select" :value="activeId" @change="onPick">
            <optgroup v-for="group in grouped" :key="group.name" :label="group.name">
              <option v-for="m in group.menus" :key="m.id" :value="m.id">{{ m.name }}</option>
            </optgroup>
          </select>
        </label>

        <p v-if="!neighbors.length" class="ms-none">
          Belum ada menu yang cukup mirip dengan {{ activeMenu?.name }}.
        </p>

        <ul v-else class="ms-list">
          <li v-for="n in neighbors" :key="n.menu.id" class="ms-item">
            <div class="ms-item-top">
              <span class="ms-name">{{ n.menu.name }}</span>
              <span class="ms-score">{{ pct(n.score) }}%</span>
            </div>
            <span class="rt-bar" role="img" :aria-label="`Kemiripan ${pct(n.score)} persen`"><span :style="{ width: pct(n.score) + '%' }"></span></span>
            <div class="ms-meta">
              <span class="rt-badge">{{ n.menu.category_name || 'Tanpa kategori' }}</span>
              <span v-if="n.menu.is_available === false" class="rt-badge is-amber">Habis</span>
              <span v-if="n.menu.is_secret" class="rt-badge is-blue">Secret</span>
              <span v-if="n.reason.length" class="ms-terms">Kata sama: {{ n.reason.join(', ') }}</span>
              <span class="ms-price">{{ formatRp(n.menu.price) }}</span>
            </div>
          </li>
        </ul>
      </section>

      <!-- ── Pasangan paling mirip ── -->
      <section class="rt-card">
        <h3 class="rt-title">Pasangan paling mirip</h3>

        <p v-if="!pairs.length" class="ms-none">Belum ada pasangan menu yang cukup mirip.</p>

        <template v-else>
          <!-- Layar lebar: tabel -->
          <div class="rt-scroll ms-table-wrap" tabindex="0" role="region" aria-label="Tabel pasangan menu mirip, geser untuk melihat semua kolom">
            <table class="rt-table">
              <thead>
                <tr><th>Pasangan</th><th>Kemiripan</th><th>Kata sama</th><th>Kategori</th></tr>
              </thead>
              <tbody>
                <tr v-for="p in pairs" :key="`${p.a.id}-${p.b.id}`">
                  <td class="name">{{ p.a.name }} <span class="ms-plus" aria-hidden="true">+</span><span class="ms-sr"> dan </span> {{ p.b.name }}</td>
                  <td>
                    <div class="ms-cell-score">
                      <span class="rt-bar"><span :style="{ width: pct(p.score) + '%' }"></span></span>
                      <span class="ms-score-sm">{{ pct(p.score) }}%</span>
                    </div>
                  </td>
                  <td>{{ p.reason.join(', ') || '–' }}</td>
                  <td><span class="rt-badge" :class="p.sameCategory ? '' : 'is-green'">{{ p.sameCategory ? 'Satu kategori' : 'Beda kategori' }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- HP: daftar bertumpuk (tabel 4 kolom terlalu sempit) -->
          <ul class="ms-list ms-pairs-mobile">
            <li v-for="p in pairs" :key="`m-${p.a.id}-${p.b.id}`" class="ms-item">
              <div class="ms-item-top">
                <span class="ms-name">{{ p.a.name }} <span class="ms-plus" aria-hidden="true">+</span><span class="ms-sr"> dan </span> {{ p.b.name }}</span>
                <span class="ms-score">{{ pct(p.score) }}%</span>
              </div>
              <span class="rt-bar" role="img" :aria-label="`Kemiripan ${pct(p.score)} persen`"><span :style="{ width: pct(p.score) + '%' }"></span></span>
              <div class="ms-meta">
                <span class="rt-badge" :class="p.sameCategory ? '' : 'is-green'">{{ p.sameCategory ? 'Satu kategori' : 'Beda kategori' }}</span>
                <span v-if="p.reason.length" class="ms-terms">Kata sama: {{ p.reason.join(', ') }}</span>
              </div>
            </li>
          </ul>
        </template>

        <p class="rt-lead ms-note">
          Pasangan <strong>beda kategori</strong> yang mirip bisa jadi ide paket. Pasangan
          <strong>satu kategori</strong> yang sangat mirip bisa saling menggantikan di mata pelanggan.
          Keduanya baru dugaan dari teks, cocokkan dengan tab Pasangan Menu di laporan penjualan sebelum memutuskan.
        </p>
        <button type="button" class="rt-btn ms-go" @click="$emit('go-paket')">Lihat saran paket</button>
      </section>

      <!-- ── Lembar penilaian relevansi ── -->
      <section class="rt-card">
        <h3 class="rt-title">Lembar penilaian relevansi</h3>
        <p class="rt-lead ms-note">
          Unduh daftar 3 rekomendasi teratas untuk setiap menu, lengkap dengan kolom kosong untuk penilai
          (1 = relevan, 0 = tidak). Pakai untuk mengukur Precision@3. Skor cosine ada di kolom paling kanan,
          sembunyikan kolom itu sebelum lembar dibagikan ke penilai.
        </p>
        <button type="button" class="rt-btn ms-go" @click="exportSheet">Unduh lembar (CSV)</button>
        <p v-if="exportInfo" class="ms-none ms-export-info" role="status">{{ exportInfo }}</p>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { buildIndex, similarTo, similarPairs } from '@/utils/recommender'
import { buildRelevanceSheet, downloadText } from '@/utils/relevanceSheet'

const props = defineProps({
  // Daftar menu dari Kelola Menu (admin melihat semuanya, termasuk habis dan secret)
  menus: { type: Array, default: () => [] },
})
defineEmits(['go-paket'])

const index = computed(() => buildIndex(props.menus))

const listed = computed(() => props.menus.filter((m) => m && m.id != null && m.is_active !== false))

const noDescCount = computed(() => listed.value.filter((m) => !String(m.description || '').trim()).length)
const noDescNotice = computed(() => listed.value.length > 0 && noDescCount.value / listed.value.length >= 0.3)

// Pilihan menu dikelompokkan per kategori
const grouped = computed(() => {
  const byCat = new Map()
  for (const m of listed.value) {
    const key = m.category_name || 'Tanpa kategori'
    if (!byCat.has(key)) byCat.set(key, [])
    byCat.get(key).push(m)
  }
  return [...byCat.entries()]
    .sort(([a], [b]) => a.localeCompare(b, 'id'))
    .map(([name, menus]) => ({ name, menus: [...menus].sort((x, y) => String(x.name).localeCompare(String(y.name), 'id')) }))
})

const selectedId = ref(null)
const activeMenu = computed(
  () => listed.value.find((m) => m.id === selectedId.value) ?? grouped.value[0]?.menus[0] ?? null,
)
const activeId = computed(() => activeMenu.value?.id ?? '')

const onPick = (e) => {
  const picked = listed.value.find((m) => String(m.id) === e.target.value)
  if (picked) selectedId.value = picked.id
}

const neighbors = computed(() =>
  activeMenu.value ? similarTo(index.value, activeMenu.value.id, { limit: 5, includeHidden: true }) : [],
)
const pairs = computed(() => similarPairs(index.value, { limit: 8 }))

// Lembar penilaian relevansi (untuk evaluasi Precision@3 di laporan)
const exportInfo = ref('')
const exportSheet = () => {
  const { csv, referenceCount, rowCount } = buildRelevanceSheet(index.value, { limit: 3, raters: 3 })
  const stamp = new Date().toISOString().slice(0, 10)
  downloadText(csv, `lembar-penilaian-relevansi-${stamp}.csv`)
  exportInfo.value = `${referenceCount} menu acuan, ${rowCount} baris terunduh.`
}

const pct = (score) => Math.round(Math.min(1, Math.max(0, score)) * 100)
const formatRp = (n) =>
  new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(Number(n) || 0)
</script>

<style src="@/assets/report-tabs.css"></style>
<style scoped>
.ms-field { display: flex; flex-direction: column; gap: 0.4rem; margin-bottom: 1rem; }
.ms-label { font-size: 0.72rem; color: var(--text-faint); }
/* 16px di HP supaya iOS tidak zoom otomatis saat select difokuskan */
.ms-select {
  width: 100%; min-height: 44px; padding: 0 0.85rem;
  border-radius: 12px; border: 1px solid rgb(var(--ink) / 0.1);
  background: rgb(var(--ink) / 0.04); color: var(--text);
  font-family: inherit; font-size: 1rem; cursor: pointer;
}
.ms-select:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
@media (min-width: 640px) { .ms-select { max-width: 24rem; font-size: 0.85rem; } }

.ms-none { margin: 0; font-size: 0.8rem; color: var(--text-faint); }

.ms-list { display: flex; flex-direction: column; margin: 0; padding: 0; list-style: none; }
.ms-item { display: flex; flex-direction: column; gap: 0.45rem; padding: 0.8rem 0; }
.ms-item + .ms-item { border-top: 1px solid rgb(var(--ink) / 0.05); }
.ms-item:first-child { padding-top: 0; }
.ms-item-top { display: flex; align-items: baseline; justify-content: space-between; gap: 0.75rem; }
.ms-name { font-size: 0.85rem; font-weight: 600; color: var(--text); min-width: 0; }
.ms-score { flex-shrink: 0; font-size: 0.95rem; font-weight: 700; color: var(--text); font-variant-numeric: tabular-nums; }
.ms-meta { display: flex; flex-wrap: wrap; align-items: center; gap: 0.4rem 0.6rem; }
.ms-terms { font-size: 0.72rem; color: var(--text-faint); }
.ms-price { margin-left: auto; font-size: 0.78rem; color: var(--text-dim); font-variant-numeric: tabular-nums; }
.ms-plus { margin: 0 0.25rem; color: var(--text-faint); }
.ms-sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }

.ms-cell-score { display: flex; align-items: center; gap: 0.6rem; min-width: 8rem; }
.ms-cell-score .rt-bar { flex: 1; }
.ms-score-sm { font-size: 0.8rem; font-weight: 600; color: var(--text); font-variant-numeric: tabular-nums; }

/* Tabel di layar lebar, daftar bertumpuk di HP */
.ms-table-wrap { display: none; }
.ms-pairs-mobile { display: flex; }
@media (min-width: 640px) {
  .ms-table-wrap { display: block; }
  .ms-pairs-mobile { display: none; }
}

.ms-note { margin-top: 1rem; font-size: 0.75rem; }
.ms-export-info { margin-top: 0.6rem; }
.ms-go { margin-top: 0.9rem; width: 100%; }
@media (min-width: 640px) { .ms-go { width: auto; } }
</style>