<template>
  <AdminModal v-model="isOpen" :title="`Edit Pesanan #${localOrder?.id || '...'}`" size="lg">
    <p class="adm-hint">Pelanggan: {{ localOrder?.customer?.phone || "Guest" }}</p>

    <div class="adm-field">
      <label class="adm-label" for="oe-status">Ubah Status</label>
      <select id="oe-status" v-model="localOrder.status" class="adm-input">
        <option value="pending">PENDING</option>
        <option value="diproses">DIPROSES</option>
        <option value="selesai">SELESAI / LUNAS</option>
      </select>
    </div>

    <div v-if="localOrder.payment_method === 'qris' && localOrder.qris_url" class="oe-qris">
      <p class="adm-label">Scan QRIS</p>
      <img :src="localOrder.qris_url" alt="QRIS" class="oe-qris-img" />
    </div>

    <div class="adm-field">
      <div class="adm-label-row">
        <span class="adm-label">Item Menu</span>
        <button type="button" class="adm-btn adm-btn--soft adm-btn--sm" @click="addItemPlaceholder">
          <Plus :size="14" /> Tambah Item
        </button>
      </div>

      <div class="oe-items">
        <div v-for="(item, index) in localOrder.items" :key="index" class="oe-item">
          <div class="oe-item-main">
            <p class="oe-item-name adm-truncate">{{ item.menu?.name || "Item Menu" }}</p>
            <p class="adm-hint">Rp {{ (item.price || 0).toLocaleString() }}</p>
          </div>

          <div class="oe-qty">
            <button type="button" class="adm-icon-btn" aria-label="Kurangi" @click="updateQty(index, -1)"><Minus :size="14" /></button>
            <span class="oe-qty-val">{{ item.quantity }}</span>
            <button type="button" class="adm-icon-btn" aria-label="Tambah" @click="updateQty(index, 1)"><Plus :size="14" /></button>
          </div>

          <div class="oe-item-total">Rp {{ ((item.price || 0) * item.quantity).toLocaleString() }}</div>

          <button type="button" class="adm-icon-btn adm-icon-btn--danger" aria-label="Hapus item" @click="removeItemRow(index)">
            <Trash2 :size="15" />
          </button>
        </div>
      </div>
    </div>

    <div class="oe-total">
      <span class="adm-label">Total Baru</span>
      <span class="oe-total-val">Rp {{ calculatedFinalPrice.toLocaleString() }}</span>
    </div>

    <template #footer>
      <button type="button" class="adm-btn adm-btn--danger oe-delete" @click="$emit('delete', localOrder.id)">
        <Trash2 :size="14" /> Hapus Order
      </button>
      <button type="button" class="adm-btn adm-btn--ghost" @click="$emit('close')">Batal</button>
      <button type="button" class="adm-btn adm-btn--primary" @click="submitSave">Simpan Perubahan</button>
    </template>
  </AdminModal>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { Plus, Minus, Trash2 } from "lucide-vue-next";
import AdminModal from "@/components/ui/admin/Adminmodal.vue";

const props = defineProps({
  open: { type: Boolean, default: false },
  order: { type: Object, default: null },
});

const emit = defineEmits(["close", "save", "delete"]);
const localOrder = ref({ items: [] });

// AdminModal memakai v-model; antarmuka publik komponen ini tetap `open` + emit("close").
const isOpen = computed({
  get: () => props.open,
  set: (v) => { if (!v) emit("close"); },
});

// Watcher untuk melakukan deep copy order ke local state agar tidak mutasi props langsung
watch(
  () => props.order,
  (newVal) => {
    if (newVal) {
      localOrder.value = JSON.parse(JSON.stringify(newVal));
    }
  },
  { immediate: true, deep: true },
);

const calculatedFinalPrice = computed(() => {
  return (
    localOrder.value.items?.reduce(
      (sum, item) => sum + item.price * item.quantity,
      0,
    ) || 0
  );
});

const updateQty = (index, change) => {
  if (localOrder.value.items[index]) {
    localOrder.value.items[index].quantity = Math.max(
      0,
      localOrder.value.items[index].quantity + change,
    );
    if (localOrder.value.items[index].quantity === 0) removeItemRow(index);
  }
};

const removeItemRow = (index) => {
  localOrder.value.items.splice(index, 1);
};

const addItemPlaceholder = () => {
  const name = prompt("Masukkan nama menu:");
  const price = parseInt(prompt("Masukkan harga satuan (Rp):") || "0");
  if (name && price > 0) {
    localOrder.value.items.push({
      menu: { name },
      quantity: 1,
      price: price,
    });
  }
};

const submitSave = () => {
  const payload = {
    ...localOrder.value,
    final_price: calculatedFinalPrice.value,
  };
  emit("save", payload);
};
</script>

<style scoped>
.oe-qris { display: flex; flex-direction: column; align-items: center; gap: 0.6rem; padding: 1rem; border: 1px solid var(--border); border-radius: var(--r-md); background: var(--surface-2); }
.oe-qris-img { width: 10rem; height: 10rem; padding: 0.5rem; border-radius: var(--r-sm); background: #fff; } /* QR wajib latar putih agar terbaca scanner */

.oe-items { display: flex; flex-direction: column; gap: 0.6rem; }
.oe-item {
  display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem 0.9rem;
  border: 1px solid var(--border); border-radius: var(--r-md); background: var(--surface-2);
}
.oe-item-main { flex: 1; min-width: 0; }
.oe-item-name { margin: 0; font-size: 0.875rem; font-weight: 600; color: var(--text); }
.oe-qty { display: flex; align-items: center; gap: 0.25rem; padding: 2px; border: 1px solid var(--border-strong); border-radius: var(--r-sm); background: var(--surface); }
.oe-qty-val { min-width: 1.75rem; text-align: center; font-size: 0.875rem; font-weight: 600; font-variant-numeric: tabular-nums; }
.oe-item-total { min-width: 6rem; text-align: right; font-size: 0.875rem; font-weight: 700; color: var(--amber-soft); font-variant-numeric: tabular-nums; }

.oe-total { display: flex; align-items: center; justify-content: space-between; padding-top: 1rem; border-top: 1px solid var(--border); }
.oe-total-val { font-family: var(--font-display); font-size: 1.25rem; color: var(--green-soft); font-variant-numeric: tabular-nums; }
.oe-delete { margin-right: auto; }

@media (max-width: 560px) {
  .oe-item { flex-wrap: wrap; }
  .oe-item-total { margin-left: auto; }
  .oe-delete { margin-right: 0; flex-basis: 100%; }
}
</style>
