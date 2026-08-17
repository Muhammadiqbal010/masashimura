<template>
  <div
    v-if="open"
    class="fixed inset-0 z-[70] flex items-center justify-center bg-black/90 backdrop-blur-md"
  >
    <div
      class="bg-[#0a0a0a] w-full max-w-md rounded-3xl p-8 border border-white/5"
    >
      <h2 class="text-2xl font-oswald text-center mb-8 uppercase tracking-wide">
        Konfirmasi Pesanan
      </h2>

      <div class="mb-8">
        <p class="text-white/60 text-sm mb-3 font-medium">Tipe Pesanan</p>
        <div class="grid grid-cols-2 gap-3">
          <button
            v-for="type in ['dine-in', 'takeaway']"
            :key="type"
            @click="orderType = type"
            :class="
              orderType === type ? 'bg-red-600' : 'bg-white/5 hover:bg-white/10'
            "
            class="border-2 border-transparent py-6 rounded-2xl text-lg font-medium transition-all capitalize"
          >
            {{ type === "dine-in" ? "🍽️ Dine In" : "📦 Takeaway" }}
          </button>
        </div>
      </div>

      <div class="mb-8">
        <p class="text-white/60 text-sm mb-3 font-medium">Metode Pembayaran</p>
        <div class="flex gap-3">
          <button
            v-for="method in ['cash', 'transfer']"
            :key="method"
            @click="paymentMethod = method"
            :class="
              paymentMethod === method ? 'bg-white text-black' : 'bg-white/5'
            "
            class="flex-1 py-5 rounded-2xl font-medium transition-all capitalize"
          >
            {{ method === "cash" ? "💵 Cash" : "📱 Transfer / QRIS" }}
          </button>
        </div>
      </div>

      <div class="mb-8">
        <label class="block text-white/60 text-sm mb-2"
          >Nomor WhatsApp Kamu</label
        >
        <input
          v-model="customerPhone"
          type="tel"
          placeholder="628xxxxxxxxxx"
          class="w-full bg-white/5 border border-white/10 rounded-2xl px-5 py-4 text-white focus:border-red-600 outline-none"
        />
      </div>

      <div class="flex gap-3">
        <button
          @click="$emit('cancel')"
          class="flex-1 py-4 border border-white/20 rounded-2xl text-white/70 hover:text-white transition"
        >
          Batal
        </button>
        <button
          @click="confirm"
          :disabled="!isFormValid"
          class="flex-1 py-4 bg-red-600 text-white rounded-2xl font-bold disabled:opacity-50 transition hover:bg-red-500"
        >
          Kirim Pesanan
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";

const props = defineProps({ open: Boolean });
const emit = defineEmits(["cancel", "confirm"]);

const orderType = ref("dine-in");
const paymentMethod = ref("cash");
const customerPhone = ref("");

// Computed untuk validasi tombol
const isFormValid = computed(
  () =>
    orderType.value && paymentMethod.value && customerPhone.value.length > 8,
);

const confirm = () => {
  emit("confirm", {
    orderType: orderType.value,
    paymentMethod: paymentMethod.value,
    customerPhone: customerPhone.value,
  });
};
</script>
