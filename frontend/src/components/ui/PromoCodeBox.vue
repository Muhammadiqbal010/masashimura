<template>
  <div class="promo-box">
    <!-- Belum ada promo terpakai -->
    <div v-if="!appliedPromo" class="promo-input-row">
      <div class="promo-input-wrap">
        <Tag :size="16" class="promo-icon" />
        <input
          v-model="codeInput"
          type="text"
          placeholder="Punya kode promo?"
          aria-label="Kode promo"
          autocomplete="off"
          autocapitalize="characters"
          class="promo-input"
          :disabled="isChecking"
          @keyup.enter="applyPromo"
          @input="codeInput = codeInput.toUpperCase()"
        />
      </div>
      <button
        type="button"
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
        <span class="promo-applied-icon"><Check :size="13" /></span>
        <span class="promo-applied-code">{{ appliedPromo.code }}</span>
        <span class="promo-applied-amount">-{{ formatPrice(appliedPromo.discount_amount) }}</span>
      </div>
      <button type="button" class="promo-remove-btn" aria-label="Hapus kode promo" @click="removePromo">
        <X :size="15" />
      </button>
    </div>

    <p v-if="errorMessage" class="promo-error" role="alert">{{ errorMessage }}</p>
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
/* Palet: Surface #111111 · Washi #FAFAFA · Crimson #D71920 · Champagne #FFD400 */

.promo-box { display: flex; flex-direction: column; gap: 0.5rem; }

.promo-input-row { display: flex; gap: 0.5rem; }

.promo-input-wrap {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
}
.promo-icon {
  position: absolute;
  left: 0.875rem;
  color: #737373;
  pointer-events: none;
}

/* 16px di HP supaya iOS tidak zoom otomatis */
.promo-input {
  width: 100%;
  height: 3rem;
  background: #111111;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.75rem;
  padding: 0 1rem 0 2.5rem;
  color: #FAFAFA;
  font-family: "Inter", sans-serif;
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
@media (min-width: 640px) {
  .promo-input { font-size: 0.875rem; }
}
.promo-input::placeholder {
  color: #737373;
  font-weight: 400;
  letter-spacing: normal;
}
.promo-input:hover:not(:disabled) { border-color: rgba(255, 255, 255, 0.2); }
.promo-input:focus {
  border-color: rgba(255,212,0, 0.6);
  box-shadow: 0 0 0 3px rgba(255,212,0, 0.12);
}
.promo-input:disabled { opacity: 0.5; }

.promo-apply-btn {
  min-width: 5rem;
  padding: 0 1.25rem;
  background: #D71920;
  border: none;
  border-radius: 0.75rem;
  color: #fff;
  font-family: "Sora", ui-sans-serif, system-ui, sans-serif;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, transform 0.15s;
  white-space: nowrap;
}
.promo-apply-btn:hover:not(:disabled) { background: #B5121B; }
.promo-apply-btn:active:not(:disabled) { transform: scale(0.97); }
.promo-apply-btn:disabled { opacity: 0.35; cursor: not-allowed; }

.promo-applied-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem 0.625rem 1rem;
  background: rgba(52, 211, 153, 0.08);
  border: 1px solid rgba(52, 211, 153, 0.25);
  border-radius: 0.75rem;
}
.promo-applied-info {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  min-width: 0;
}
.promo-applied-icon {
  display: flex;
  height: 1.375rem;
  width: 1.375rem;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  background: rgba(52, 211, 153, 0.2);
  color: #6EE7B7;
}
.promo-applied-code {
  font-weight: 700;
  font-size: 0.875rem;
  color: #FAFAFA;
  letter-spacing: 0.06em;
}
.promo-applied-amount {
  font-size: 0.875rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: #6EE7B7;
  white-space: nowrap;
}
.promo-remove-btn {
  width: 2rem; height: 2rem;
  flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: rgba(255, 255, 255, 0.06);
  border: none; border-radius: 9999px;
  color: #A3A3A3;
  cursor: pointer;
  transition: all 0.15s;
}
.promo-remove-btn:hover { background: rgba(215,25,32, 0.15); color: #FF6A70; }

.promo-error {
  font-size: 0.8125rem;
  color: #FF6A70;
  margin: 0;
  padding-left: 0.25rem;
}

.promo-apply-btn:focus-visible,
.promo-remove-btn:focus-visible {
  outline: 2px solid #FFD400;
  outline-offset: 2px;
}
</style>