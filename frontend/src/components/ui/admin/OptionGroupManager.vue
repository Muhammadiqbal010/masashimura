<!--
  OptionGroupManager.vue — tab "Opsi" di Kelola Menu.
  Admin membuat grup opsi SEKALI (Level Pedas, Suhu, Topping…), lalu memasangnya
  ke menu mana saja. Mengubah grup di sini otomatis berlaku di semua menu yang memakainya.
-->
<template>
  <div class="ogm">
    <div class="ogm-bar">
      <p class="adm-sub ogm-lead">
        Buat opsi sekali, lalu pasang ke menu mana saja. Kalau opsinya diubah di sini, semua menu yang memakainya ikut berubah.
      </p>
      <div class="ogm-actions">
        <button type="button" class="adm-btn adm-btn--ghost" @click="openCreate(SPICY_PRESET)">Preset Level Pedas</button>
        <button type="button" class="adm-btn adm-btn--primary" @click="openCreate(null)"><Plus :size="15" /> Buat Grup Opsi</button>
      </div>
    </div>

    <div v-if="loading" class="adm-card adm-card--flush" aria-busy="true"><div class="adm-skel" style="height:64px"></div></div>

    <div v-else-if="!groups.length" class="adm-card ogm-empty">
      <p><strong>Belum ada grup opsi.</strong></p>
      <p class="adm-sub">Mulai dari yang paling sering dipakai, mis. Level Pedas atau Suhu (Panas / Dingin).</p>
    </div>

    <div v-else class="ogm-list">
      <article v-for="g in groups" :key="g.id" class="adm-card ogm-card">
        <div class="ogm-main">
          <div class="ogm-title-row">
            <h3 class="ogm-name">{{ g.name }}</h3>
            <span class="adm-badge" :class="g.required ? 'adm-badge--red' : ''">{{ g.required ? 'Wajib' : 'Opsional' }}</span>
            <span class="adm-badge">{{ g.multiple ? 'Pilih banyak' : 'Pilih satu' }}</span>
          </div>
          <p class="ogm-choices">
            <template v-for="(c, i) in g.choices" :key="i">
              <span v-if="i" aria-hidden="true"> · </span>{{ c.label }}<em v-if="c.price" class="ogm-plus"> +{{ rp(c.price) }}</em>
            </template>
          </p>
          <p class="ogm-used">
            <ListChecks :size="13" />
            <template v-if="g.menu_count">Dipakai di {{ g.menu_count }} menu: {{ usedNames(g) }}</template>
            <template v-else>Belum dipasang ke menu mana pun</template>
          </p>
        </div>
        <div class="ogm-btns">
          <button type="button" class="adm-btn adm-btn--ghost" :aria-label="'Edit ' + g.name" @click="openEdit(g)"><Pencil :size="14" /> Edit</button>
          <button type="button" class="adm-btn adm-btn--ghost ogm-del" :aria-label="'Hapus ' + g.name" @click="deleteTarget = g"><Trash2 :size="14" /> Hapus</button>
        </div>
      </article>
    </div>

    <OptionGroupFormModal
      v-model="showForm" :group="editing" :menus="menus" :preset="preset"
      @saved="$emit('changed')"
    />

    <AdminModal
      :model-value="!!deleteTarget" title="Hapus grup opsi?" size="sm" :persistent="deleting"
      @update:model-value="(v) => !v && (deleteTarget = null)"
    >
      <p class="adm-modal-text">
        Grup <strong>{{ deleteTarget?.name }}</strong> akan dihapus
        <template v-if="deleteTarget?.menu_count"> dan dicabut dari <strong>{{ deleteTarget.menu_count }} menu</strong></template>.
      </p>
      <p class="adm-modal-text ogm-note">Riwayat pesanan yang sudah ada tidak berubah.</p>
      <template #footer>
        <button type="button" class="adm-btn adm-btn--ghost" :disabled="deleting" @click="deleteTarget = null">Batal</button>
        <button type="button" class="adm-btn adm-btn--danger" data-autofocus :disabled="deleting" @click="confirmDelete">
          <span v-if="deleting" class="adm-spinner"></span><Trash2 v-else :size="15" />
          {{ deleting ? 'Menghapus…' : 'Ya, hapus' }}
        </button>
      </template>
    </AdminModal>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { toast } from 'vue-sonner'
import { Plus, Pencil, Trash2, ListChecks } from 'lucide-vue-next'
import AdminModal from '@/components/ui/admin/Adminmodal.vue'
import OptionGroupFormModal from '@/components/ui/admin/OptionGroupFormModal.vue'
import { optionGroupAPI } from '@/api/optionGroups'

const props = defineProps({
  groups: { type: Array, default: () => [] },
  menus: { type: Array, default: () => [] },
  loading: Boolean,
})
const emit = defineEmits(['changed'])

const SPICY_PRESET = {
  name: 'Level Pedas', required: true, multiple: false,
  choices: [{ label: 'Nggak pedas' }, { label: 'Sedeng' }, { label: 'Pedas' }],
}

const showForm = ref(false)
const editing = ref(null)
const preset = ref(null)
const deleteTarget = ref(null)
const deleting = ref(false)

const rp = (n) => 'Rp' + new Intl.NumberFormat('id-ID').format(n)

const menuById = computed(() => new Map(props.menus.map((m) => [m.id, m.name])))
const usedNames = (g) => {
  const names = (g.menu_ids || []).map((id) => menuById.value.get(id)).filter(Boolean)
  return names.length > 4 ? `${names.slice(0, 4).join(', ')} +${names.length - 4} lagi` : names.join(', ')
}

const openCreate = (p) => { editing.value = null; preset.value = p; showForm.value = true }
const openEdit = (g) => { editing.value = g; preset.value = null; showForm.value = true }

const confirmDelete = async () => {
  const target = deleteTarget.value
  if (!target) return
  deleting.value = true
  try {
    await optionGroupAPI.delete(target.id)
    toast.success('Grup opsi dihapus')
    deleteTarget.value = null
    emit('changed')
  } catch {
    toast.error('Gagal menghapus grup opsi')
  } finally {
    deleting.value = false
  }
}
</script>

<style scoped>
.ogm { display: flex; flex-direction: column; gap: 1rem; }
.ogm-bar { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0.75rem; }
.ogm-lead { margin: 0; flex: 1 1 18rem; }
.ogm-actions { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.ogm-empty { padding: 1.5rem; text-align: center; }
.ogm-list { display: flex; flex-direction: column; gap: 0.75rem; }
.ogm-card { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0.75rem; padding: 1rem; }
.ogm-main { flex: 1 1 18rem; min-width: 0; display: flex; flex-direction: column; gap: 0.35rem; }
.ogm-title-row { display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem; }
.ogm-name { margin: 0; font-size: 0.95rem; font-weight: 700; color: var(--text); }
.ogm-choices { margin: 0; font-size: 0.8125rem; color: var(--text-2); }
.ogm-plus { font-style: normal; color: var(--accent-text); }
.ogm-used { display: flex; align-items: flex-start; gap: 0.4rem; margin: 0; font-size: 0.75rem; color: var(--text-faint); }
.ogm-used svg { flex-shrink: 0; margin-top: 0.15rem; }
.ogm-btns { display: flex; gap: 0.5rem; }
.ogm-del { color: var(--red-soft); }
.ogm-note { margin-top: 0.6rem; font-size: 0.8rem; color: var(--text-faint); }
</style>
