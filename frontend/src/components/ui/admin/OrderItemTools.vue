<template>
  <AdminModal :model-value="!!mode" :title="title" size="lg" @update:model-value="(v) => !v && close()">
    <div v-if="order" class="oit">
      <!-- ───────── TAMBAH MENU ───────── -->
      <template v-if="mode === 'add'">
        <p class="oit-hint">
          Menu ditambahkan ke nota <b>{{ order.order_number || '#' + order.id }}</b>. Item baru diberi tanda
          "Ditambah" supaya dapur tahu, dan status "Siap" dicabut kalau sebelumnya sudah ditandai.
        </p>

        <div v-if="pickerMenu" class="oit-picker">
          <p class="oit-picker-title">{{ pickerMenu.name }} · {{ money(unitPrice(pickerMenu)) }}</p>
          <div v-for="group in pickerMenu.options" :key="group.name" class="oit-group">
            <p class="oit-group-name">
              {{ group.name }}
              <span v-if="group.required" class="oit-req">wajib</span>
              <span v-if="group.multiple" class="oit-opt">boleh lebih dari satu</span>
            </p>
            <div class="oit-chips">
              <button
                v-for="c in group.choices"
                :key="c.label"
                type="button"
                class="oit-chip"
                :class="{ 'is-on': isPicked(group, c) }"
                @click="togglePick(group, c)"
              >
                {{ c.label }}<span v-if="Number(c.price) > 0"> +{{ money(c.price) }}</span>
              </button>
            </div>
          </div>
          <div class="oit-field">
            <label class="oit-label" for="oit-note">Catatan (opsional)</label>
            <input id="oit-note" v-model="pickNote" class="adm-input" maxlength="120" placeholder="mis. tanpa sayur" />
          </div>
          <div class="oit-row">
            <div class="oit-stepper">
              <button type="button" class="adm-icon-btn adm-icon-btn--bordered" aria-label="Kurangi" @click="pickQty = Math.max(1, pickQty - 1)"><Minus :size="14" /></button>
              <span class="oit-qty">{{ pickQty }}</span>
              <button type="button" class="adm-icon-btn adm-icon-btn--bordered" aria-label="Tambah" @click="pickQty += 1"><Plus :size="14" /></button>
            </div>
            <div class="oit-actions">
              <button type="button" class="adm-btn adm-btn--ghost adm-btn--sm" @click="pickerMenu = null">Batal</button>
              <button type="button" class="adm-btn adm-btn--primary adm-btn--sm" :disabled="busy || !!missingGroup" @click="submitPicked">
                Tambahkan
              </button>
            </div>
          </div>
          <p v-if="missingGroup" class="oit-warn">Pilih dulu: {{ missingGroup.name }}</p>
        </div>

        <template v-else>
          <div class="oit-search">
            <Search :size="14" aria-hidden="true" />
            <input v-model="menuQuery" class="adm-input" placeholder="Cari menu…" aria-label="Cari menu" />
          </div>
          <p v-if="menuLoading" class="oit-hint">Memuat menu…</p>
          <p v-else-if="menuError" class="oit-warn">{{ menuError }}</p>
          <ul v-else class="oit-list">
            <li v-for="m in filteredMenus" :key="m.id" class="oit-item">
              <div class="oit-item-main">
                <span class="oit-item-name">{{ m.name }}</span>
                <span class="oit-item-sub">{{ m.category_name }} · {{ money(unitPrice(m)) }}</span>
              </div>
              <button type="button" class="adm-btn adm-btn--soft adm-btn--sm" :disabled="busy" @click="startAdd(m)">
                <Plus :size="14" /> Tambah
              </button>
            </li>
            <li v-if="!filteredMenus.length" class="oit-hint">Tidak ada menu yang cocok.</li>
          </ul>
        </template>

        <div v-if="addedLog.length" class="oit-added">
          <p class="oit-ok"><Check :size="14" /> Sudah ditambahkan ke nota ini</p>
          <ul class="oit-added-list">
            <li v-for="(a, i) in addedLog" :key="i">
              <span class="oit-added-qty">{{ a.qty }}×</span>
              <span class="oit-added-name">{{ a.name }}<small v-if="a.detail"> · {{ a.detail }}</small></span>
            </li>
          </ul>
          <p class="oit-added-total">Total nota sekarang <b>{{ money(addedTotal) }}</b></p>
        </div>
      </template>

      <!-- ───────── PISAH NOTA ───────── -->
      <template v-else-if="mode === 'split'">
        <p class="oit-hint">
          Pilih item yang dipindah ke <b>nota baru</b> supaya bisa dibayar terpisah. Sisakan minimal satu
          item di nota asal. Poin member tetap di nota asal.
        </p>
        <ul class="oit-list">
          <li v-for="i in order.items" :key="i.id" class="oit-item" :class="{ 'is-off': i.is_point_redemption }">
            <div class="oit-item-main">
              <span class="oit-item-name">{{ i.menu_name }}</span>
              <span class="oit-item-sub">
                {{ i.quantity }}× · {{ money(i.price) }}
                <template v-if="i.notes"> · {{ i.notes }}</template>
                <template v-if="i.is_point_redemption"> · tukar poin (tidak bisa dipisah)</template>
              </span>
            </div>
            <div v-if="!i.is_point_redemption" class="oit-stepper">
              <button type="button" class="adm-icon-btn adm-icon-btn--bordered" aria-label="Kurangi" @click="step(i, -1)"><Minus :size="14" /></button>
              <span class="oit-qty">{{ pick[i.id] || 0 }}</span>
              <button type="button" class="adm-icon-btn adm-icon-btn--bordered" aria-label="Tambah" @click="step(i, 1)"><Plus :size="14" /></button>
            </div>
          </li>
        </ul>
        <div class="oit-field">
          <label class="oit-label" for="oit-name">Nama untuk nota baru (opsional)</label>
          <input id="oit-name" v-model="splitName" class="adm-input" maxlength="100" placeholder="mis. Budi" />
        </div>
        <p class="oit-sum">Dipindah: <b>{{ pickedUnits }}</b> porsi · {{ money(pickedValue) }}</p>
        <p v-if="splitBlocked" class="oit-warn">{{ splitBlocked }}</p>
      </template>

      <!-- ───────── MENU HABIS ───────── -->
      <template v-else-if="mode === 'unavailable'">
        <template v-if="!result">
          <p class="oit-hint">
            Pilih menu yang habis. Item dikeluarkan dari nota dan total dihitung ulang.
            <b v-if="isPaid">Nota ini sudah lunas, jadi selisihnya dicatat sebagai refund yang diserahkan saat pesanan diambil.</b>
            <b v-else>Nota ini belum dibayar, jadi pelanggan cukup bayar total yang baru.</b>
          </p>
          <ul class="oit-list">
            <li v-for="i in order.items" :key="i.id" class="oit-item" :class="{ 'is-off': i.is_point_redemption }">
              <div class="oit-item-main">
                <span class="oit-item-name">{{ i.menu_name }}</span>
                <span class="oit-item-sub">
                  {{ i.quantity }}× · {{ money(i.price) }}
                  <template v-if="i.is_point_redemption"> · tukar poin (void order kalau habis)</template>
                </span>
              </div>
              <div v-if="!i.is_point_redemption" class="oit-stepper">
                <button type="button" class="adm-icon-btn adm-icon-btn--bordered" aria-label="Kurangi" @click="step(i, -1)"><Minus :size="14" /></button>
                <span class="oit-qty">{{ pick[i.id] || 0 }}</span>
                <button type="button" class="adm-icon-btn adm-icon-btn--bordered" aria-label="Tambah" @click="step(i, 1)"><Plus :size="14" /></button>
              </div>
            </li>
          </ul>
          <div class="oit-field">
            <label class="oit-label" for="oit-reason">Catatan (opsional)</label>
            <input id="oit-reason" v-model="unavailNote" class="adm-input" maxlength="200" placeholder="mis. bahan habis" />
          </div>
          <label class="oit-check">
            <input v-model="soldOutCatalog" type="checkbox" />
            <span>
              <b>Ikut tandai habis di Kelola Menu</b>
              <span class="oit-faint">Menu tidak bisa dipesan lagi di POS maupun web sampai diaktifkan kembali.</span>
            </span>
          </label>
          <p class="oit-sum">
            Menu habis: <b>{{ pickedUnits }}</b> porsi · sekitar {{ money(pickedValue) }}
            <span class="oit-faint">(angka pasti dihitung server, termasuk promo)</span>
          </p>
        </template>

        <div v-else class="oit-result">
          <p class="oit-ok"><Check :size="14" /> Tersimpan.</p>
          <template v-if="result.summary.cancelled">
            <p>Semua menu habis, nota otomatis <b>dibatalkan</b> (alasan: stok habis).</p>
          </template>
          <template v-else>
            <p>Total nota: {{ money(result.summary.old_total) }} → <b>{{ money(result.summary.new_total) }}</b></p>
            <p v-if="result.summary.is_paid" class="oit-money">
              Kembalikan ke pelanggan: <b>{{ money(result.summary.refund_due) }}</b> saat pesanan diambil.
            </p>
            <p v-else class="oit-money">
              Pelanggan bayar: <b>{{ money(result.summary.amount_to_pay_now) }}</b>
            </p>
          </template>
          <p v-if="result.menus_marked?.length" class="oit-note">
            <b>{{ result.menus_marked.map((m) => m.name).join(', ') }}</b>
            sekarang berstatus <b>habis</b> di Kelola Menu, jadi tidak bisa dipesan di POS maupun web.
            Aktifkan lagi di Kelola Menu kalau stoknya sudah ada.
          </p>
          <p v-if="result.other_orders?.length" class="oit-note is-warn">
            <AlertTriangle :size="14" />
            <span>
              Ada {{ result.other_orders.length }} nota lain yang masih memuat menu ini:
              {{ result.other_orders.map((o) => o.customer_name || o.order_number).join(', ') }}.
              Cek dan kabari kalau perlu.
            </span>
          </p>
        </div>
      </template>
    </div>

    <template #footer>
      <template v-if="mode === 'add'">
        <button type="button" class="adm-btn adm-btn--primary" @click="close">Selesai</button>
      </template>
      <template v-else-if="mode === 'split'">
        <button type="button" class="adm-btn adm-btn--ghost" @click="close">Batal</button>
        <button type="button" class="adm-btn adm-btn--primary" :disabled="busy || !pickedUnits || !!splitBlocked" @click="submitSplit">
          Pisahkan nota
        </button>
      </template>
      <template v-else-if="mode === 'unavailable'">
        <template v-if="!result">
          <button type="button" class="adm-btn adm-btn--ghost" @click="close">Batal</button>
          <button type="button" class="adm-btn adm-btn--danger" :disabled="busy || !pickedUnits" @click="submitUnavailable">
            Tandai habis
          </button>
        </template>
        <template v-else>
          <button
            v-if="canWhatsApp && !result.summary.cancelled"
            type="button"
            class="adm-btn adm-btn--soft"
            @click="notifyCustomer"
          >
            <MessageCircle :size="14" /> Kabari pelanggan
          </button>
          <button type="button" class="adm-btn adm-btn--primary" @click="close">Selesai</button>
        </template>
      </template>
    </template>
  </AdminModal>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { Search, Plus, Minus, Check, MessageCircle, AlertTriangle } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import AdminModal from '@/components/ui/admin/Adminmodal.vue'
import { orderAPI, menuAPI } from '@/api'
import { waLink } from '@/utils/orderMessages'

const props = defineProps({
  // 'add' | 'split' | 'unavailable' | null (tertutup)
  mode: { type: String, default: null },
  order: { type: Object, default: null },
  kasirName: { type: String, default: '' },
})
const emit = defineEmits(['close', 'updated', 'notify'])

const money = (n) =>
  new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(Number(n) || 0)

const title = computed(() => {
  const no = props.order?.order_number || (props.order ? '#' + props.order.id : '')
  return { add: `Tambah menu · ${no}`, split: `Pisah nota · ${no}`, unavailable: `Menu habis · ${no}` }[props.mode] || ''
})

const busy = ref(false)
const apiError = (err, fallback) => err?.response?.data?.detail || err?.response?.data?.error || fallback

// ── state umum untuk split & unavailable ──
const pick = reactive({})          // { itemId: jumlah }
const splitName = ref('')
const unavailNote = ref('')
const soldOutCatalog = ref(true)   // menu yang ditandai habis di nota ikut habis di katalog
const result = ref(null)

const items = computed(() => props.order?.items || [])
const pickedUnits = computed(() => Object.values(pick).reduce((a, b) => a + (Number(b) || 0), 0))
const pickedValue = computed(() =>
  items.value.reduce((sum, i) => sum + (Number(pick[i.id]) || 0) * Number(i.price || 0), 0)
)
const step = (item, d) => {
  const next = (Number(pick[item.id]) || 0) + d
  pick[item.id] = Math.min(Math.max(next, 0), item.quantity)
}
const isPaid = computed(() => props.order?.payment_status === 'paid')

const splitBlocked = computed(() => {
  const total = items.value.reduce((a, i) => a + i.quantity, 0)
  if (pickedUnits.value > 0 && total - pickedUnits.value <= 0) return 'Sisakan minimal satu item di nota asal.'
  return ''
})

// ── tambah menu ──
const menus = ref([])
const menuLoading = ref(false)
const menuError = ref('')
const menuQuery = ref('')
const pickerMenu = ref(null)
const selection = reactive({})
const pickQty = ref(1)
const pickNote = ref('')
// Riwayat tambahan selama modal ini terbuka (menu yang sama digabung jumlahnya).
const addedLog = ref([])
const addedTotal = ref(0)

const unitPrice = (m) =>
  props.order?.source === 'web' ? Number(m.price_web ?? m.web_price ?? m.price) : Number(m.price)

const filteredMenus = computed(() => {
  const q = menuQuery.value.trim().toLowerCase()
  return menus.value.filter((m) => !q || String(m.name).toLowerCase().includes(q))
})

const loadMenus = async () => {
  menuLoading.value = true
  menuError.value = ''
  try {
    const res = await menuAPI.getAll()
    const list = Array.isArray(res.data) ? res.data : res.data?.results || []
    menus.value = list.filter((m) => m.is_available !== false && m.is_active !== false)
  } catch (err) {
    menuError.value = apiError(err, 'Gagal memuat daftar menu.')
  } finally {
    menuLoading.value = false
  }
}

const resetPicker = () => {
  pickerMenu.value = null
  Object.keys(selection).forEach((k) => delete selection[k])
  pickQty.value = 1
  pickNote.value = ''
}

const isPicked = (group, c) => (selection[group.name] || []).includes(c.label)
const togglePick = (group, c) => {
  const cur = selection[group.name] || []
  if (group.multiple) {
    selection[group.name] = cur.includes(c.label) ? cur.filter((l) => l !== c.label) : [...cur, c.label]
  } else {
    selection[group.name] = cur.includes(c.label) ? [] : [c.label]
  }
}
const missingGroup = computed(() =>
  (pickerMenu.value?.options || []).find((g) => g.required && !(selection[g.name] || []).length)
)

const postAdd = async (menu, quantity, options, notes) => {
  busy.value = true
  try {
    const res = await orderAPI.addItem(props.order.id, {
      menu_id: menu.id,
      quantity,
      options,
      notes,
    })
    const detail = [
      ...Object.values(options || {}).flat(),
      notes || '',
    ].filter(Boolean).join(', ')
    const hit = addedLog.value.find((a) => a.id === menu.id && a.detail === detail)
    if (hit) hit.qty += quantity
    else addedLog.value.push({ id: menu.id, name: menu.name, qty: quantity, detail })
    addedTotal.value = res.data.total_price
    emit('updated', { order: res.data })
    resetPicker()
  } catch (err) {
    toast.error(apiError(err, 'Gagal menambah menu.'))
  } finally {
    busy.value = false
  }
}

const startAdd = (menu) => {
  if (menu.options?.length) {
    resetPicker()
    pickerMenu.value = menu
    return
  }
  postAdd(menu, 1, {}, '')
}
const submitPicked = () => {
  if (!pickerMenu.value || missingGroup.value) return
  postAdd(pickerMenu.value, pickQty.value, { ...selection }, pickNote.value.trim())
}

// ── pisah nota ──
const submitSplit = async () => {
  busy.value = true
  try {
    const rows = items.value
      .filter((i) => (Number(pick[i.id]) || 0) > 0)
      .map((i) => ({ item_id: i.id, quantity: Number(pick[i.id]) }))
    const res = await orderAPI.splitOrder(props.order.id, {
      items: rows,
      customer_name: splitName.value.trim(),
      kasir_name: props.kasirName,
    })
    toast.success(`Nota baru ${res.data.new_order?.order_number || ''} dibuat`)
    emit('updated', { order: res.data.original, newOrder: res.data.new_order })
    close()
  } catch (err) {
    toast.error(apiError(err, 'Gagal memisah nota.'))
  } finally {
    busy.value = false
  }
}

// ── menu habis ──
const submitUnavailable = async () => {
  busy.value = true
  try {
    const rows = items.value
      .filter((i) => (Number(pick[i.id]) || 0) > 0)
      .map((i) => ({ item_id: i.id, quantity: Number(pick[i.id]) }))
    const res = await orderAPI.markUnavailable(props.order.id, {
      items: rows,
      kasir_name: props.kasirName,
      note: unavailNote.value.trim(),
      mark_menu_sold_out: soldOutCatalog.value,
    })
    result.value = res.data
    emit('updated', { order: res.data.order })
  } catch (err) {
    toast.error(apiError(err, 'Gagal menandai menu habis.'))
  } finally {
    busy.value = false
  }
}

const latestOrder = computed(() => result.value?.order || props.order)
const canWhatsApp = computed(() => !!waLink(latestOrder.value?.customer_phone, 'x'))
// Buka modul "Kabari pelanggan" (jenis: Menu habis) di halaman induk, supaya kasir bisa
// mengedit pesannya dulu dan memakai jenis pesan lain kalau perlu.
const notifyCustomer = () => emit('notify', latestOrder.value)

const close = () => emit('close')

// PENTING: kuncinya STRING, bukan array. Getter yang mengembalikan array baru dianggap
// "berubah" setiap kali props.order diganti objek baru (polling 5 detik menggantinya terus),
// akibatnya jumlah yang sudah dipilih & layar "Tersimpan" ter-reset sendiri.
watch(
  () => `${props.mode || ''}:${props.order?.id ?? ''}`,
  () => {
    Object.keys(pick).forEach((k) => delete pick[k])
    splitName.value = ''
    unavailNote.value = ''
    soldOutCatalog.value = true
    result.value = null
    addedLog.value = []
    addedTotal.value = 0
    menuQuery.value = ''
    resetPicker()
    if (props.mode === 'add') loadMenus()
  },
  { immediate: true }
)
</script>

<style scoped>
.oit { display: flex; flex-direction: column; gap: 0.9rem; }
.oit-hint { font-size: 0.85rem; color: var(--text-2); line-height: 1.55; margin: 0; }
.oit-warn { font-size: 0.82rem; color: var(--red-soft); margin: 0; }
.oit-added { display: flex; flex-direction: column; gap: 0.4rem; padding: 0.7rem 0.9rem; border: 1px solid var(--line-green); border-radius: var(--r-md); background: var(--tint-green); }
.oit-added-list { display: flex; flex-direction: column; gap: 0.2rem; margin: 0; padding: 0; list-style: none; max-height: 7rem; overflow-y: auto; }
.oit-added-list li { display: flex; gap: 0.5rem; font-size: 0.85rem; color: var(--text); }
.oit-added-qty { font-family: var(--font-mono); font-weight: 700; color: var(--green-soft); }
.oit-added-name small { color: var(--text-dim); }
.oit-added-total { margin: 0; font-size: 0.8rem; color: var(--text-dim); }
.oit-ok { display: inline-flex; align-items: center; gap: 0.4rem; font-size: 0.85rem; font-weight: 700; color: var(--green-soft); margin: 0; }
.oit-faint { color: var(--text-faint); font-size: 0.78rem; }
.oit-search { position: relative; display: flex; align-items: center; gap: 0.5rem; }
.oit-search svg { position: absolute; left: 0.75rem; color: var(--text-faint); pointer-events: none; }
.oit-search .adm-input { padding-left: 2.2rem; }
.oit-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 0.4rem; max-height: 46vh; overflow-y: auto; }
.oit-item { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; padding: 0.6rem 0.75rem; border: 1px solid var(--border-strong); border-radius: 0.75rem; }
.oit-item.is-off { opacity: 0.55; }
.oit-item-main { display: flex; flex-direction: column; min-width: 0; }
.oit-item-name { font-weight: 700; color: var(--text); }
.oit-item-sub { font-size: 0.78rem; color: var(--text-2); }
.oit-stepper { display: inline-flex; align-items: center; gap: 0.5rem; }
.oit-qty { min-width: 1.5rem; text-align: center; font-weight: 800; font-variant-numeric: tabular-nums; }
.oit-sum { margin: 0; font-size: 0.9rem; color: var(--text); }
.oit-field { display: flex; flex-direction: column; gap: 0.35rem; }
.oit-label { font-size: 0.78rem; font-weight: 700; color: var(--text-2); }
.oit-picker { display: flex; flex-direction: column; gap: 0.8rem; padding: 0.9rem; border: 1px solid var(--border-strong); border-radius: 0.9rem; }
.oit-picker-title { margin: 0; font-weight: 800; color: var(--text); }
.oit-group-name { margin: 0 0 0.35rem; font-size: 0.82rem; font-weight: 700; color: var(--text); display: flex; gap: 0.5rem; align-items: center; }
.oit-req { font-size: 0.7rem; color: var(--red-soft); text-transform: uppercase; letter-spacing: 0.06em; }
.oit-opt { font-size: 0.72rem; font-weight: 500; color: var(--text-faint); }
.oit-chips { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.oit-chip { padding: 0.35rem 0.75rem; border-radius: 9999px; border: 1px solid var(--border-strong); font-size: 0.82rem; font-weight: 600; color: var(--text-2); background: transparent; cursor: pointer; }
.oit-chip.is-on { background: var(--accent); border-color: var(--accent); color: var(--on-accent); }
.oit-row { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; flex-wrap: wrap; }
.oit-actions { display: flex; gap: 0.5rem; }
.oit-result { display: flex; flex-direction: column; gap: 0.5rem; font-size: 0.92rem; color: var(--text); }
.oit-result p { margin: 0; }
.oit-check { display: flex; gap: 0.6rem; align-items: flex-start; padding: 0.7rem 0.8rem; border: 1px solid var(--border-strong); border-radius: 0.75rem; cursor: pointer; font-size: 0.85rem; color: var(--text); line-height: 1.45; }
.oit-check input { margin-top: 0.2rem; accent-color: var(--accent); flex-shrink: 0; }
.oit-check span { display: flex; flex-direction: column; gap: 0.1rem; }
.oit-note { margin: 0; font-size: 0.82rem; color: var(--text-2); line-height: 1.5; }
.oit-note.is-warn { display: flex; gap: 0.45rem; align-items: flex-start; color: var(--amber-soft); }
.oit-note.is-warn svg { flex-shrink: 0; margin-top: 0.15rem; }
.oit-money { padding: 0.7rem 0.9rem; border-radius: 0.75rem; background: var(--tint-accent); border: 1px solid var(--line-accent); }
</style>
