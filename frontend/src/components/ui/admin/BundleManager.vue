<!--
  BundleManager.vue — tab "Paket" di Kelola Menu.
  Admin hanya mengisi harga paket; harga normal dan potongan dihitung dari harga menu.
  Isi paket dibatasi ke menu tanpa pilihan wajib (mis. level pedas) dan bukan secret menu.
-->
<template>
  <div class="bm">
    <div class="bm-bar">
      <p class="adm-sub bm-lead">Gabungkan beberapa menu jadi satu harga. Saat dipesan, paket dipecah jadi menu biasa, jadi laporan per menu tetap benar.</p>
      <button type="button" class="adm-btn adm-btn--primary" @click="openCreate"><Plus :size="15" /> Buat Paket</button>
    </div>

    <div v-if="loading" class="adm-card adm-card--flush" aria-busy="true"><div class="bm-pad adm-skel" style="height:64px"></div></div>

    <div v-else-if="loadError" class="adm-card bm-empty">
      <p>Paket gagal dimuat.</p>
      <button type="button" class="adm-btn adm-btn--ghost" @click="load">Coba lagi</button>
    </div>

    <div v-else-if="!bundles.length" class="adm-card bm-empty">
      <p><strong>Belum ada paket.</strong></p>
      <p class="adm-sub">Mulai dari menu yang sering dipesan bersamaan (lihat tab Pasangan Menu di Laporan Menu).</p>
    </div>

    <div v-else class="bm-list">
      <article v-for="b in bundles" :key="b.id" class="adm-card bm-card" :class="{ 'is-off': !b.is_available }">
        <div class="bm-main">
          <div class="bm-title-row">
            <h3 class="bm-name">{{ b.name }}</h3>
            <span v-if="!b.is_available" class="bm-tag bm-tag--off">Habis (manual)</span>
            <span v-else-if="b.unavailable_reason" class="bm-tag bm-tag--warn">{{ b.unavailable_reason }}</span>
            <span v-else class="bm-tag bm-tag--ok">Tersedia</span>
          </div>
          <p class="bm-contents">{{ b.contents.map((c) => c.quantity + '× ' + c.name).join(' · ') }}</p>
          <p class="bm-price">
            <strong>{{ rp(b.pos.price) }}</strong>
            <span class="bm-normal">normal {{ rp(b.pos.normal_price) }}</span>
            <span v-if="b.pos.savings > 0" class="bm-save">hemat {{ rp(b.pos.savings) }}</span>
          </p>
          <p v-if="b.pos.not_cheaper" class="bm-warn" role="alert">
            <AlertTriangle :size="13" /> Harga paket sama atau lebih mahal dari harga normal. Label hemat disembunyikan dari pelanggan.
          </p>
          <p class="bm-web">Harga di web: {{ rp(b.web.price) }}<template v-if="!b.web.not_cheaper"> (normal {{ rp(b.web.normal_price) }}, hemat {{ rp(b.web.savings) }})</template></p>
        </div>
        <div class="bm-actions">
          <button type="button" class="adm-btn adm-btn--ghost" @click="toggle(b)">{{ b.is_available ? 'Tandai habis' : 'Tandai tersedia' }}</button>
          <button type="button" class="adm-btn adm-btn--ghost" :aria-label="'Edit ' + b.name" @click="openEdit(b)"><Pencil :size="14" /> Edit</button>
          <button type="button" class="adm-btn adm-btn--ghost bm-del" :aria-label="'Hapus ' + b.name" @click="deleteTarget = b"><Trash2 :size="14" /> Hapus</button>
        </div>
      </article>
    </div>

    <!-- Modal buat / edit -->
    <AdminModal v-model="showForm" :title="editingId ? 'Edit Paket' : 'Buat Paket'" :persistent="saving">
      <form id="bundle-form" class="bm-form" @submit.prevent="save">
        <div class="adm-field">
          <label class="adm-label" for="bm-name">Nama paket <span class="adm-req">*</span></label>
          <input id="bm-name" v-model="form.name" data-autofocus class="adm-input" type="text" maxlength="100" placeholder="Contoh: Paket Katsu + Es Teh" />
        </div>

        <div class="adm-field">
          <span class="adm-label">Isi paket <span class="adm-req">*</span></span>
          <div v-for="(row, i) in form.items" :key="i" class="bm-row">
            <select v-model.number="row.menu" class="adm-input" :aria-label="'Menu ' + (i + 1)">
              <option :value="null" disabled>Pilih menu…</option>
              <option v-for="m in pickable" :key="m.id" :value="m.id" :disabled="usedElsewhere(m.id, i)">
                {{ m.name }} · {{ rp(m.price) }}{{ m.is_available ? '' : ' (habis)' }}
              </option>
            </select>
            <input v-model.number="row.quantity" class="adm-input bm-qty" type="number" min="1" max="20" :aria-label="'Jumlah menu ' + (i + 1)" />
            <button type="button" class="adm-icon-btn" :aria-label="'Hapus baris ' + (i + 1)" :disabled="form.items.length <= 1" @click="form.items.splice(i, 1)"><X :size="15" /></button>
          </div>
          <button type="button" class="adm-btn adm-btn--ghost bm-add" @click="form.items.push({ menu: null, quantity: 1 })"><Plus :size="14" /> Tambah menu</button>
          <p class="adm-hint">Menu dengan pilihan wajib (mis. level pedas) dan secret menu belum bisa masuk paket.</p>
        </div>

        <div class="adm-field">
          <label class="adm-label" for="bm-price">Harga paket (Rp) <span class="adm-req">*</span></label>
          <input id="bm-price" v-model.number="form.price" class="adm-input" type="number" min="1" inputmode="numeric" />
          <p class="bm-preview" :class="{ 'is-bad': preview.normal > 0 && form.price >= preview.normal }">
            Harga normal {{ rp(preview.normal) }}.
            <template v-if="preview.normal > 0 && form.price > 0">
              <template v-if="form.price < preview.normal">Potongan <strong>{{ rp(preview.normal - form.price) }}</strong>.</template>
              <template v-else>Paket tidak lebih murah, label hemat tidak akan tampil.</template>
            </template>
          </p>
        </div>

        <div class="adm-field">
          <label class="adm-label" for="bm-desc">Deskripsi (opsional)</label>
          <textarea id="bm-desc" v-model="form.description" class="adm-input" rows="2" maxlength="300"></textarea>
        </div>
        <p v-if="formError" class="adm-error" role="alert">{{ formError }}</p>
      </form>
      <template #footer>
        <button type="button" class="adm-btn adm-btn--ghost" :disabled="saving" @click="showForm = false">Batal</button>
        <button type="submit" form="bundle-form" class="adm-btn adm-btn--primary" :disabled="saving">
          <span v-if="saving" class="adm-spinner"></span>{{ saving ? 'Menyimpan…' : editingId ? 'Simpan Perubahan' : 'Buat Paket' }}
        </button>
      </template>
    </AdminModal>

    <!-- Konfirmasi hapus -->
    <AdminModal :model-value="!!deleteTarget" title="Hapus paket?" size="sm" :persistent="saving" @update:model-value="(v) => !v && (deleteTarget = null)">
      <p class="adm-modal-text">Paket <strong>{{ deleteTarget?.name }}</strong> akan dihapus. Riwayat order yang sudah memakai paket ini tidak berubah.</p>
      <template #footer>
        <button type="button" class="adm-btn adm-btn--ghost" :disabled="saving" @click="deleteTarget = null">Batal</button>
        <button type="button" class="adm-btn adm-btn--danger" data-autofocus :disabled="saving" @click="confirmDelete"><Trash2 :size="15" /> Hapus</button>
      </template>
    </AdminModal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Plus, X, Pencil, Trash2, AlertTriangle } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { bundleAPI } from '@/api'
import AdminModal from '@/components/ui/admin/Adminmodal.vue'

const props = defineProps({ menus: { type: Array, default: () => [] } })
const emit = defineEmits(['changed'])

const bundles = ref([])
const loading = ref(true)
const loadError = ref(false)
const saving = ref(false)
const showForm = ref(false)
const editingId = ref(null)
const deleteTarget = ref(null)
const formError = ref('')
const form = reactive({ name: '', description: '', price: null, items: [] })

const rp = (v) => 'Rp' + Math.round(Number(v) || 0).toLocaleString('id-ID')
const hasRequiredOption = (m) => (m.options || []).some((g) => g && g.required)

// Menu yang boleh masuk paket (aktif, bukan secret, tanpa pilihan wajib).
const pickable = computed(() =>
  props.menus.filter((m) => m.is_active !== false && !m.is_secret && !hasRequiredOption(m))
)
const priceOf = (id) => Number(props.menus.find((m) => m.id === id)?.price) || 0
const usedElsewhere = (id, idx) => form.items.some((r, i) => i !== idx && r.menu === id)
const preview = computed(() => ({
  normal: form.items.reduce((s, r) => s + (r.menu ? priceOf(r.menu) * (Number(r.quantity) || 0) : 0), 0),
}))

const load = async () => {
  loading.value = true
  loadError.value = false
  try {
    const { data } = await bundleAPI.getAll()
    bundles.value = Array.isArray(data) ? data : data?.results || []
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editingId.value = null
  Object.assign(form, { name: '', description: '', price: null, items: [{ menu: null, quantity: 1 }, { menu: null, quantity: 1 }] })
  formError.value = ''
  showForm.value = true
}
const openEdit = (b) => {
  editingId.value = b.id
  Object.assign(form, {
    name: b.name, description: b.description || '', price: Number(b.price),
    items: b.contents.map((c) => ({ menu: c.menu, quantity: c.quantity })),
  })
  formError.value = ''
  showForm.value = true
}

const firstError = (err) => {
  const d = err?.response?.data
  if (!d) return 'Gagal menyimpan paket. Periksa koneksi.'
  if (typeof d === 'string') return d
  const v = d.detail || Object.values(d)[0]
  return Array.isArray(v) ? String(v[0]) : typeof v === 'object' ? JSON.stringify(v) : String(v)
}

const save = async () => {
  formError.value = ''
  if (!form.name.trim()) return (formError.value = 'Nama paket wajib diisi.')
  if (form.items.some((r) => !r.menu)) return (formError.value = 'Pilih menu untuk setiap baris, atau hapus baris kosong.')
  if (!(form.price > 0)) return (formError.value = 'Harga paket harus lebih dari 0.')
  saving.value = true
  try {
    const body = {
      name: form.name.trim(), description: form.description.trim(), price: form.price,
      items: form.items.map((r) => ({ menu: r.menu, quantity: Number(r.quantity) || 1 })),
    }
    if (editingId.value) await bundleAPI.update(editingId.value, body)
    else await bundleAPI.create(body)
    toast.success(editingId.value ? 'Paket diperbarui' : 'Paket dibuat')
    showForm.value = false
    await load()
    emit('changed')
  } catch (err) {
    formError.value = firstError(err)
  } finally {
    saving.value = false
  }
}

const toggle = async (b) => {
  try {
    await bundleAPI.update(b.id, { is_available: !b.is_available })
    await load()
  } catch (err) {
    toast.error(firstError(err))
  }
}

const confirmDelete = async () => {
  const t = deleteTarget.value
  if (!t) return
  saving.value = true
  try {
    await bundleAPI.remove(t.id)
    toast.success('Paket dihapus')
    deleteTarget.value = null
    await load()
    emit('changed')
  } catch (err) {
    toast.error(firstError(err))
  } finally {
    saving.value = false
  }
}

onMounted(load)
defineExpose({ reload: load })
</script>

<style scoped>
.bm { display: flex; flex-direction: column; gap: 1rem; }
.bm-bar { display: flex; flex-wrap: wrap; gap: .75rem; align-items: center; justify-content: space-between; }
.bm-lead { margin: 0; max-width: 46ch; }
.bm-list { display: grid; gap: .75rem; }
.bm-card { display: flex; flex-wrap: wrap; gap: 1rem; justify-content: space-between; align-items: flex-start; padding: 1rem 1.1rem; }
.bm-card.is-off { opacity: .75; }
.bm-main { min-width: 0; flex: 1 1 280px; display: flex; flex-direction: column; gap: .35rem; }
.bm-title-row { display: flex; flex-wrap: wrap; gap: .5rem; align-items: center; }
.bm-name { margin: 0; font-size: 1rem; font-weight: 600; }
.bm-tag { padding: .1rem .55rem; border-radius: 999px; font-size: 0.72rem; background: rgb(var(--ink) / .07); }
.bm-tag--ok { background: color-mix(in srgb, var(--green) 14%, transparent); }
.bm-tag--warn { background: color-mix(in srgb, var(--amber) 16%, transparent); }
.bm-tag--off { background: color-mix(in srgb, var(--accent) 14%, transparent); }
.bm-contents, .bm-web { margin: 0; font-size: .8rem; opacity: .75; }
.bm-price { margin: 0; display: flex; flex-wrap: wrap; gap: .6rem; align-items: baseline; }
.bm-normal { font-size: .78rem; opacity: .6; text-decoration: line-through; }
.bm-save { font-size: .78rem; font-weight: 600; color: var(--amber-soft, #e0d100); }
.bm-warn { margin: 0; display: flex; gap: .4rem; align-items: flex-start; font-size: .78rem; color: var(--amber-soft, #e0d100); }
.bm-actions { display: flex; flex-wrap: wrap; gap: .5rem; }
.bm-del { color: #d92b22; }
.bm-empty { padding: 2rem 1rem; text-align: center; }
.bm-form { display: flex; flex-direction: column; gap: 1rem; }
.bm-row { display: grid; grid-template-columns: 1fr 76px 40px; gap: .5rem; margin-bottom: .5rem; align-items: center; }
.bm-add { align-self: flex-start; }
.bm-preview { margin: .4rem 0 0; font-size: .8rem; opacity: .8; }
.bm-preview.is-bad { color: var(--amber-soft, #e0d100); opacity: 1; }
</style>