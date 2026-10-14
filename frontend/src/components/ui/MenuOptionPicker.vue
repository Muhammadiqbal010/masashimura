<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-[70] flex items-end justify-center bg-black/75 backdrop-blur-md sm:items-center sm:p-6"
      role="dialog"
      aria-modal="true"
      :aria-label="`Pilih opsi ${menu.name}`"
      @click.self="$emit('close')"
      @keydown.esc="$emit('close')"
    >
      <div class="picker-sheet flex max-h-[92vh] w-full flex-col overflow-hidden rounded-t-[2rem] border border-white/[0.08] sm:max-w-lg sm:rounded-[2rem]">

        <!-- Header -->
        <div class="flex items-start justify-between gap-3 border-b border-white/[0.07] px-6 pb-4 pt-6 sm:px-7">
          <div class="min-w-0">
            <p class="text-xs font-medium text-[#FFD400]">Pilih opsi</p>
            <h3 class="mt-1 font-sora text-xl font-semibold leading-tight tracking-tight text-[#FAFAFA]">
              {{ menu.name }}
            </h3>
          </div>
          <button
            type="button"
            aria-label="Tutup"
            class="-mr-2 -mt-1 flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full text-[#A3A3A3] transition-colors hover:bg-white/5 hover:text-[#FAFAFA]"
            @click="$emit('close')"
          >
            <X :size="18" />
          </button>
        </div>

        <!-- Grup opsi -->
        <div class="flex-1 space-y-7 overflow-y-auto px-6 py-6 sm:px-7">
          <fieldset v-for="group in menu.options" :key="group.name" class="space-y-3">
            <legend class="flex w-full flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
              <span class="font-sora text-base font-semibold text-[#FAFAFA]">{{ group.name }}</span>
              <span class="text-xs font-medium" :class="group.required ? 'text-[#FF6A70]' : 'text-[#737373]'">
                {{ group.required ? "Wajib" : "Opsional" }} · {{ group.multiple ? "boleh lebih dari satu" : "pilih satu" }}
              </span>
            </legend>

            <div class="space-y-2" :role="group.multiple ? 'group' : 'radiogroup'" :aria-label="group.name">
              <button
                v-for="choice in group.choices"
                :key="choice.label"
                type="button"
                :role="group.multiple ? 'checkbox' : 'radio'"
                :aria-checked="isPicked(group, choice)"
                :class="[
                  'flex min-h-[52px] w-full items-center justify-between gap-3 rounded-2xl border px-4 py-3 text-left transition-all duration-150',
                  isPicked(group, choice)
                    ? 'border-[#D71920] bg-[#D71920]/10'
                    : 'border-white/10 bg-white/[0.03] hover:border-white/25'
                ]"
                @click="toggle(group, choice)"
              >
                <span class="flex min-w-0 items-center gap-3">
                  <span
                    :class="[
                      'flex h-5 w-5 flex-shrink-0 items-center justify-center border transition-colors',
                      group.multiple ? 'rounded-md' : 'rounded-full',
                      isPicked(group, choice) ? 'border-[#D71920] bg-[#D71920]' : 'border-white/25'
                    ]"
                  >
                    <Check v-if="isPicked(group, choice)" :size="12" class="text-white" />
                  </span>
                  <span class="truncate text-[15px] text-[#FAFAFA]">{{ choice.label }}</span>
                </span>
                <span v-if="Number(choice.price) > 0" class="flex-shrink-0 text-sm font-semibold tabular-nums text-[#FFD400]">
                  +{{ formatPrice(choice.price) }}
                </span>
              </button>
            </div>
          </fieldset>
        </div>

        <!-- Footer: jumlah + konfirmasi -->
        <div class="footer-safe space-y-3 border-t border-white/[0.07] bg-black/25 px-6 pt-4 sm:px-7">
          <p v-if="missingGroup" class="text-sm text-[#FFD400]">
            Pilih "{{ missingGroup }}" dulu.
          </p>
          <div class="flex items-center gap-3">
            <div class="flex flex-shrink-0 items-center rounded-full border border-white/10 bg-white/[0.03] p-1">
              <button
                type="button"
                aria-label="Kurangi jumlah"
                :disabled="quantity <= 1"
                class="flex h-11 w-11 items-center justify-center rounded-full text-[#FAFAFA] transition-colors hover:bg-white/10 disabled:opacity-30 disabled:hover:bg-transparent"
                @click="quantity--"
              >
                <Minus :size="16" />
              </button>
              <span class="min-w-[2rem] text-center text-base font-semibold tabular-nums text-[#FAFAFA]">{{ quantity }}</span>
              <button
                type="button"
                aria-label="Tambah jumlah"
                :disabled="quantity >= 99"
                class="flex h-11 w-11 items-center justify-center rounded-full text-[#FAFAFA] transition-colors hover:bg-white/10 disabled:opacity-30 disabled:hover:bg-transparent"
                @click="quantity++"
              >
                <Plus :size="16" />
              </button>
            </div>

            <button
              type="button"
              :disabled="!!missingGroup"
              :class="[
                'flex h-[52px] flex-1 items-center justify-center gap-2 rounded-full px-4 text-sm font-semibold transition-all duration-200',
                missingGroup
                  ? 'cursor-not-allowed border border-white/5 bg-[#1B1B1B] text-[#737373]'
                  : 'bg-[#D71920] text-white hover:bg-[#B5121B] hover:shadow-lg shadow-black/20 active:scale-[0.98]'
              ]"
              @click="confirm"
            >
              <span>Tambah</span>
              <span class="tabular-nums">· {{ formatPrice(total) }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { reactive, ref, computed, onMounted, onUnmounted } from "vue"
import { X, Check, Plus, Minus } from "lucide-vue-next"

const props = defineProps({
  menu: { type: Object, required: true },
  formatPrice: { type: Function, required: true },
})
const emit = defineEmits(["close", "confirm"])

// { "Level Pedas": ["Pedas"], "Tambahan": ["Extra keju"] }
const selection = reactive({})
const quantity = ref(1)

const isPicked = (group, choice) => (selection[group.name] || []).includes(choice.label)

const toggle = (group, choice) => {
  const current = selection[group.name] || []
  if (group.multiple) {
    selection[group.name] = current.includes(choice.label)
      ? current.filter((label) => label !== choice.label)
      : [...current, choice.label]
  } else if (current[0] === choice.label) {
    // Klik pilihan yang sama: opsi wajib tetap terpilih, opsi opsional boleh dikosongkan
    if (!group.required) selection[group.name] = []
  } else {
    selection[group.name] = [choice.label]
  }
}

const missingGroup = computed(
  () => (props.menu.options || []).find((g) => g.required && !(selection[g.name] || []).length)?.name || null
)

// Hanya untuk tampilan; server menghitung ulang harga add-on dari data menu.
const extraPrice = computed(() =>
  (props.menu.options || []).reduce((sum, group) => {
    const picks = selection[group.name] || []
    return sum + group.choices
      .filter((c) => picks.includes(c.label))
      .reduce((s, c) => s + (Number(c.price) || 0), 0)
  }, 0)
)

const total = computed(
  () => ((Number(props.menu.price_web ?? props.menu.price) || 0) + extraPrice.value) * quantity.value
)

const confirm = () => {
  if (missingGroup.value) return
  emit("confirm", { selection: { ...selection }, quantity: quantity.value })
}

const onKey = (e) => { if (e.key === "Escape") emit("close") }
onMounted(() => document.addEventListener("keydown", onKey))
onUnmounted(() => document.removeEventListener("keydown", onKey))
</script>

<style scoped>
/* Palet: Surface #1B1B1B · Washi #FAFAFA · Crimson #D71920 · Champagne #FFD400 */

.picker-sheet {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.01)), #1B1B1B;
  box-shadow: 0 40px 80px -20px rgba(0, 0, 0, 0.7);
}

/* Footer aman dari home-indicator di HP */
.footer-safe { padding-bottom: calc(1.25rem + env(safe-area-inset-bottom, 0px)); }

button:focus-visible {
  outline: 2px solid #FFD400;
  outline-offset: 3px;
}
</style>