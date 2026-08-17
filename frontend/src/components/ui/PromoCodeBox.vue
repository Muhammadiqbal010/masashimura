<template>
  <div class="promo-box">
    <!-- Belum ada promo terpakai -->
    <div v-if="!appliedPromo" class="promo-input-row">
      <div class="promo-input-wrap">
        <Tag :size="14" class="promo-icon" />
        <input
          v-model="codeInput"
          type="text"
          placeholder="Punya kode promo?"
          class="promo-input"
          :disabled="isChecking"
          @keyup.enter="applyPromo"
          @input="codeInput = codeInput.toUpperCase()"
        />
      </div>
      <button
        class="promo-apply-btn"
        :disabled="!codeInput.trim() || isChecking"
        @click="applyPromo"
      >
        {{ isChecking ? '...' : 'Pakai' }}
      </button>
    </div>

    <!-- Promo berhasil diterapkan -->
    <div v-else class="promo-applied-strip">
      <div class="promo-applied-info">
        <Check :size="14" class="promo-applied-icon" />
        <span class="promo-applied-code">{{ appliedPromo.code }}</span>
        <span class="promo-applied-amount">-{{ formatPrice(appliedPromo.discount_amount) }}</span>
      </div>
      <button class="promo-remove-btn" @click="removePromo">
        <X :size="13" />
      </button>
    </div>

    <p v-if="errorMessage" class="promo-error">{{ errorMessage }}</p>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { Tag, Check, X } from "lucide-vue-next";
import { apiClient } from "@/api";
import { toast } from "vue-sonner";

const props = defineProps({
  subtotal: {
    type: [Number, String],
    required: true,
  },
});

const emit = defineEmits(["applied", "removed"]);

const codeInput     = ref("");
const isChecking    = ref(false);
const errorMessage  = ref("");
const appliedPromo  = ref(null); // { promo_id, code, discount_amount }

const formatPrice = (p) =>
  new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", minimumFractionDigits: 0 }).format(p || 0);

const applyPromo = async () => {
  const code = codeInput.value.trim();
  if (!code) return;

  errorMessage.value = "";
  isChecking.value = true;

  try {
    const { data } = await apiClient.post("/promotions/validate/", {
      code,
      subtotal: props.subtotal,
    });

    appliedPromo.value = {
      promo_id: data.promo_id,
      code: data.code,
      discount_amount: data.discount_amount,
    };
    emit("applied", appliedPromo.value);
    toast.success(data.message || `Promo ${data.code} berhasil dipakai`);
  } catch (err) {
    const msg = err.response?.data?.message || "Kode promo tidak valid";
    errorMessage.value = msg;
  } finally {
    isChecking.value = false;
  }
};

const removePromo = () => {
  appliedPromo.value = null;
  codeInput.value = "";
  errorMessage.value = "";
  emit("removed");
};

// Diekspos biar parent (Checkout/NewOrder) bisa reset dari luar,
// misal setelah order berhasil dibuat
defineExpose({ removePromo });
</script>

<style scoped>
.promo-box { display: flex; flex-direction: column; gap: 0.4rem; }

.promo-input-row { display: flex; gap: 0.5rem; }

.promo-input-wrap {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
}
.promo-icon {
  position: absolute;
  left: 0.75rem;
  color: rgba(255,255,255,0.25);
  pointer-events: none;
}
.promo-input {
  width: 100%;
  background: #0f0f0f;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px;
  padding: 0.65rem 0.85rem 0.65rem 2.25rem;
  color: #fff;
  font-family: monospace;
  font-size: 0.82rem;
  letter-spacing: 0.05em;
  outline: none;
  transition: border-color 0.15s;
}
.promo-input::placeholder { color: rgba(255,255,255,0.2); font-family: 'Inter', sans-serif; letter-spacing: normal; }
.promo-input:focus { border-color: rgba(220,38,38,0.5); }
.promo-input:disabled { opacity: 0.5; }

.promo-apply-btn {
  padding: 0 1.1rem;
  background: #dc2626;
  border: none;
  border-radius: 10px;
  color: #fff;
  font-family: 'Oswald', sans-serif;
  font-size: 0.7rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
  transition: background 0.15s;
  white-space: nowrap;
}
.promo-apply-btn:hover:not(:disabled) { background: #b91c1c; }
.promo-apply-btn:disabled { opacity: 0.35; cursor: not-allowed; }

.promo-applied-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.65rem 0.85rem;
  background: rgba(34,197,94,0.08);
  border: 1px solid rgba(34,197,94,0.25);
  border-radius: 10px;
}
.promo-applied-info { display: flex; align-items: center; gap: 0.5rem; }
.promo-applied-icon { color: #4ade80; }
.promo-applied-code {
  font-family: monospace;
  font-weight: 700;
  font-size: 0.8rem;
  color: #fff;
  letter-spacing: 0.05em;
}
.promo-applied-amount {
  font-family: monospace;
  font-size: 0.8rem;
  color: #4ade80;
  font-weight: 700;
}
.promo-remove-btn {
  width: 24px; height: 24px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(255,255,255,0.06);
  border: none; border-radius: 6px;
  color: rgba(255,255,255,0.5);
  cursor: pointer;
  transition: all 0.15s;
}
.promo-remove-btn:hover { background: rgba(239,68,68,0.15); color: #f87171; }

.promo-error {
  font-size: 0.72rem;
  color: #f87171;
  margin: 0;
  padding-left: 0.25rem;
}
</style>