<template>
  <div
    v-if="open"
    class="fixed inset-0 bg-black/80 flex items-center justify-center z-50 backdrop-blur-sm p-4"
  >
    <div
      class="bg-[#0a0a0a] border border-white/10 rounded-3xl w-full max-w-2xl overflow-hidden shadow-2xl"
    >
      <div
        class="px-8 py-5 border-b border-white/5 flex justify-between items-center bg-white/5"
      >
        <div>
          <h2 class="font-oswald text-2xl uppercase tracking-wide text-white">
            Edit Pesanan #{{ localOrder?.id || "..." }}
          </h2>
          <p class="text-xs text-white/40">
            Pelanggan: {{ localOrder?.customer?.phone || "Guest" }}
          </p>
        </div>
        <button
          @click="$emit('close')"
          class="text-white/50 hover:text-white text-xl transition"
        >
          &times;
        </button>
      </div>

      <div
        class="p-8 max-h-[60vh] overflow-y-auto space-y-6 text-white custom-scroll"
      >
        <div>
          <label
            class="block text-xs uppercase tracking-widest text-white/40 mb-2"
            >Ubah Status</label
          >
          <select
            v-model="localOrder.status"
            class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:border-red-600 transition"
          >
            <option value="pending">PENDING</option>
            <option value="diproses">DIPROSES</option>
            <option value="selesai">SELESAI / LUNAS</option>
          </select>
        </div>

        <div
          v-if="localOrder.payment_method === 'qris' && localOrder.qris_url"
          class="bg-white/5 p-4 rounded-xl flex flex-col items-center border border-white/5"
        >
          <p class="text-xs uppercase tracking-widest text-white/40 mb-3">
            Scan QRIS
          </p>
          <img
            :src="localOrder.qris_url"
            alt="QRIS"
            class="w-40 h-40 bg-white p-2 rounded-lg"
          />
        </div>

        <div>
          <div class="flex justify-between items-center mb-3">
            <label class="block text-xs uppercase tracking-widest text-white/40"
              >Item Menu</label
            >
            <button
              @click="addItemPlaceholder"
              class="text-xs bg-red-600/20 text-red-400 border border-red-500/30 px-3 py-1 rounded-lg hover:bg-red-600 hover:text-white transition"
            >
              + Tambah Item
            </button>
          </div>

          <div class="space-y-3">
            <div
              v-for="(item, index) in localOrder.items"
              :key="index"
              class="flex items-center gap-4 bg-white/5 border border-white/5 p-4 rounded-xl"
            >
              <div class="flex-1">
                <p class="text-sm font-semibold">
                  {{ item.menu?.name || "Item Menu" }}
                </p>
                <p class="text-xs text-white/40">
                  Rp {{ (item.price || 0).toLocaleString() }}
                </p>
              </div>

              <div
                class="flex items-center gap-2 bg-black border border-white/10 rounded-lg p-1"
              >
                <button
                  type="button"
                  @click="updateQty(index, -1)"
                  class="w-8 h-8 rounded bg-white/5 hover:bg-white/10"
                >
                  -
                </button>
                <span class="w-8 text-center text-sm font-semibold">{{
                  item.quantity
                }}</span>
                <button
                  type="button"
                  @click="updateQty(index, 1)"
                  class="w-8 h-8 rounded bg-white/5 hover:bg-white/10"
                >
                  +
                </button>
              </div>

              <div class="w-24 text-right font-oswald text-sm text-amber-500">
                Rp {{ ((item.price || 0) * item.quantity).toLocaleString() }}
              </div>

              <button
                @click="removeItemRow(index)"
                class="text-white/30 hover:text-red-500 transition"
              >
                🗑️
              </button>
            </div>
          </div>
        </div>

        <div
          class="pt-4 border-t border-white/5 flex justify-between items-center"
        >
          <span class="text-sm uppercase tracking-wider text-white/50"
            >Total Baru:</span
          >
          <span class="text-xl font-bold font-oswald text-emerald-400">
            Rp {{ calculatedFinalPrice.toLocaleString() }}
          </span>
        </div>
      </div>

      <div
        class="px-8 py-5 border-t border-white/5 bg-white/5 flex justify-between"
      >
        <button
          @click="$emit('delete', localOrder.id)"
          class="px-5 py-3 border border-red-500/30 text-red-500 rounded-xl hover:bg-red-600 hover:text-white transition text-xs uppercase"
        >
          Hapus Order
        </button>
        <div class="flex gap-3">
          <button
            @click="$emit('close')"
            class="px-5 py-3 border border-white/10 text-white/70 rounded-xl hover:bg-white/5 transition text-xs uppercase"
          >
            Batal
          </button>
          <button
            @click="submitSave"
            class="px-6 py-3 bg-red-600 hover:bg-red-500 text-white rounded-xl font-bold text-xs uppercase transition"
          >
            Simpan Perubahan
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps({
  open: { type: Boolean, default: false },
  order: { type: Object, default: null },
});

const emit = defineEmits(["close", "save", "delete"]);
const localOrder = ref({ items: [] });

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
