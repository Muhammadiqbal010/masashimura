<!--
  OptionGroupFormModal.vue — modal buat / edit satu Grup Opsi (mis. "Level Pedas").
  Dipakai di dua tempat:
    1) tab "Opsi" di Kelola Menu (kelola library)
    2) tombol "+" di form menu (buat cepat, langsung terpilih untuk menu itu)
  Admin juga bisa langsung centang menu mana saja yang memakai grup ini.
-->
<template>
  <AdminModal
    :model-value="modelValue"
    :title="group ? 'Edit Grup Opsi' : 'Buat Grup Opsi'"
    size="lg"
    :persistent="saving"
    @update:model-value="(v) => !v && close()"
  >
    <form id="og-form" class="og-form" @submit.prevent="save">
      <div class="adm-field">
        <label class="adm-label" for="og-name">Nama grup <span class="adm-req">*</span></label>
        <input
          id="og-name" v-model="form.name" data-autofocus type="text" maxlength="50"
          class="adm-input" placeholder="Contoh: Level Pedas" :aria-invalid="!!errors.name"
        />
        <p v-if="errors.name" class="adm-error">{{ errors.name }}</p>
      </div>

      <div class="og-flags">
        <label class="adm-check"><input v-model="form.required" type="checkbox" /> Wajib dipilih</label>
        <label class="adm-check"><input v-model="form.multiple" type="checkbox" /> Boleh pilih banyak</label>
      </div>

      <div class="adm-field">
        <span class="adm-label">Pilihan <span class="adm-req">*</span></span>
        <p class="og-hint">Kosongkan harga kalau gratis. Isi kalau pilihan itu berbayar (mis. Extra Telur +Rp3.000).</p>

        <div v-for="(choice, ci) in form.choices" :key="ci" class="og-choice">
          <input
            v-model="choice.label" type="text" class="adm-input" maxlength="50"
            placeholder="Nama pilihan" :aria-label="`Pilihan ${ci + 1}`"
          />
          <div class="adm-affix og-price">
            <span class="adm-affix-pre" aria-hidden="true">+Rp</span>
            <input
              v-model="choice.price" type="number" inputmode="numeric" min="0" step="500"
              class="adm-input adm-input--mono has-pre" placeholder="0" aria-label="Harga tambahan"
            />
          </div>
          <button
            type="button" class="adm-icon-btn" :disabled="form.choices.length <= 1"
            :aria-label="`Hapus pilihan ${choice.label || ci + 1}`" @click="removeChoice(ci)"
          >
            <X :size="14" />
          </button>
        </div>

        <button
          type="button" class="adm-btn adm-btn--ghost og-add"
          :disabled="form.choices.length >= MAX_CHOICES" @click="addChoice"
        >
          <Plus :size="14" /> Tambah pilihan
        </button>
        <p v-if="errors.choices" class="adm-error">{{ errors.choices }}</p>
      </div>

      <div class="adm-field">
        <div class="og-menus-head">
          <span class="adm-label">Dipakai di menu <span class="adm-opt">({{ form.menu_ids.length }} dipilih)</span></span>
          <div class="og-menus-tools">
            <button type="button" class="adm-btn adm-btn--ghost adm-btn--sm" @click="selectShown">Pilih semua yang tampil</button>
            <button type="button" class="adm-btn adm-btn--ghost adm-btn--sm" :disabled="!form.menu_ids.length" @click="form.menu_ids = []">Kosongkan</button>
          </div>
        </div>

        <div class="adm-search og-search">
          <Search :size="15" class="adm-search-icon" />
          <input v-model="menuQuery" type="search" class="adm-input" placeholder="Cari menu…" aria-label="Cari menu" />
        </div>

        <div class="og-menus">
          <label v-for="m in shownMenus" :key="m.id" class="adm-check og-menu">
            <input v-model="form.menu_ids" type="checkbox" :value="m.id" />
            <span class="og-menu-name">{{ m.name }}</span>
            <span class="og-menu-cat">{{ m.category_name || 'Tanpa Kategori' }}</span>
          </label>
          <p v-if="!shownMenus.length" class="og-hint og-none">Tidak ada menu yang cocok.</p>
        </div>
        <p v-if="errors.menus" class="adm-error">{{ errors.menus }}</p>
      </div>
    </form>

    <template #footer>
      <button type="button" class="adm-btn adm-btn--ghost" :disabled="saving" @click="close">Batal</button>
      <button type="submit" form="og-form" class="adm-btn adm-btn--primary" :disabled="saving">
        <span v-if="saving" class="adm-spinner"></span>
        {{ saving ? 'Menyimpan…' : group ? 'Simpan Perubahan' : 'Buat Grup' }}
      </button>
    </template>
  </AdminModal>
</template>

<script setup>
import { reactive, ref, computed, watch } from 'vue'
import { toast } from 'vue-sonner'
import { Plus, X, Search } from 'lucide-vue-next'
import AdminModal from '@/components/ui/admin/Adminmodal.vue'
import { optionGroupAPI } from '@/api/optionGroups'

const props = defineProps({
  modelValue: Boolean,
  group: { type: Object, default: null },      // null = buat baru
  menus: { type: Array, default: () => [] },
  preset: { type: Object, default: null },     // isi awal untuk grup baru (mis. Level Pedas)
  preselectMenuId: { type: [Number, String], default: null }, // menu yang sedang diedit di form menu
})
const emit = defineEmits(['update:modelValue', 'saved'])

// Batas ini sama dengan menu/options.py (server tetap validasi ulang)
const MAX_CHOICES = 15

const blank = () => ({ name: '', required: false, multiple: false, choices: [{ label: '', price: '' }], menu_ids: [] })
const form = reactive(blank())
const errors = reactive({ name: '', choices: '', menus: '' })
const saving = ref(false)
const menuQuery = ref('')

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    errors.name = errors.choices = errors.menus = ''
    menuQuery.value = ''
    const g = props.group
    if (g) {
      Object.assign(form, {
        name: g.name,
        required: !!g.required,
        multiple: !!g.multiple,
        choices: (g.choices || []).map((c) => ({ label: c.label, price: c.price || '' })),
        menu_ids: [...(g.menu_ids || [])],
      })
    } else {
      const p = props.preset
      Object.assign(form, blank(), p ? {
        name: p.name, required: !!p.required, multiple: !!p.multiple,
        choices: p.choices.map((c) => ({ label: c.label, price: c.price || '' })),
      } : {})
      if (props.preselectMenuId) form.menu_ids = [props.preselectMenuId]
    }
  },
  { immediate: true }
)

const shownMenus = computed(() => {
  const q = menuQuery.value.trim().toLowerCase()
  return props.menus.filter((m) => m.is_active !== false && m.name.toLowerCase().includes(q))
})
const selectShown = () => {
  form.menu_ids = [...new Set([...form.menu_ids, ...shownMenus.value.map((m) => m.id)])]
}

const addChoice = () => { if (form.choices.length < MAX_CHOICES) form.choices.push({ label: '', price: '' }) }
const removeChoice = (ci) => { if (form.choices.length > 1) form.choices.splice(ci, 1) }

const build = () => {
  errors.name = errors.choices = ''
  const name = form.name.trim()
  if (!name) { errors.name = 'Nama grup wajib diisi.'; return null }

  const seen = new Set()
  const choices = []
  for (const c of form.choices) {
    const label = (c.label || '').trim()
    if (!label) { errors.choices = 'Ada pilihan yang masih kosong (isi atau hapus).'; return null }
    if (seen.has(label.toLowerCase())) { errors.choices = `Pilihan "${label}" dobel.`; return null }
    seen.add(label.toLowerCase())
    const price = c.price === '' || c.price == null ? 0 : Number(c.price)
    if (!Number.isInteger(price) || price < 0) { errors.choices = `Harga "${label}" harus bilangan bulat, tidak negatif.`; return null }
    choices.push({ label, price })
  }
  return { name, required: !!form.required, multiple: !!form.multiple, choices, menu_ids: form.menu_ids }
}

const save = async () => {
  const payload = build()
  if (!payload) return
  saving.value = true
  try {
    const res = props.group
      ? await optionGroupAPI.update(props.group.id, payload)
      : await optionGroupAPI.create(payload)
    toast.success(props.group ? 'Grup opsi diperbarui' : 'Grup opsi dibuat')
    emit('saved', res.data)
    emit('update:modelValue', false)
  } catch (err) {
    const d = err.response?.data
    const pick = (v) => (Array.isArray(v) ? v[0] : v)
    if (d?.name) errors.name = String(pick(d.name))
    if (d?.choices) errors.choices = String(pick(d.choices))
    if (d?.menu_ids) errors.menus = String(pick(d.menu_ids))
    toast.error('Grup opsi belum valid / gagal disimpan')
  } finally {
    saving.value = false
  }
}

const close = () => { if (!saving.value) emit('update:modelValue', false) }
</script>

<style scoped>
.og-form { display: flex; flex-direction: column; gap: 1rem; }
.og-flags { display: flex; flex-wrap: wrap; gap: 0.2rem 1.4rem; }
.og-hint { margin: 0 0 0.6rem; font-size: 0.75rem; color: var(--text-faint); }
.og-choice { display: grid; grid-template-columns: minmax(0, 1fr) 8.5rem auto; gap: 0.5rem; align-items: center; margin-bottom: 0.5rem; }
.og-price { min-width: 0; }
.og-add { align-self: flex-start; }
.og-menus-head { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0.5rem; margin-bottom: 0.5rem; }
.og-menus-tools { display: flex; gap: 0.4rem; flex-wrap: wrap; }
.og-search { margin-bottom: 0.5rem; }
.og-menus {
  max-height: 14rem; overflow-y: auto; padding: 0.25rem 0.75rem;
  border: 1px solid var(--border); border-radius: var(--r-md); background: var(--surface-2);
}
.og-menu { gap: 0.6rem; }
.og-menu-name { flex: 1; min-width: 0; color: var(--text); }
.og-menu-cat { font-size: 0.7rem; color: var(--text-faint); }
.og-none { padding: 0.75rem 0; text-align: center; }
@media (max-width: 640px) {
  .og-choice { grid-template-columns: minmax(0, 1fr) 7rem auto; }
}
</style>
