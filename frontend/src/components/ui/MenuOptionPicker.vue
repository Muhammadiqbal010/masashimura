<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-[70] bg-black/70 backdrop-blur-sm flex items-end sm:items-center justify-center"
      role="dialog"
      aria-modal="true"
      :aria-label="`Pilih opsi ${menu.name}`"
      @click.self="$emit('close')"
      @keydown.esc="$emit('close')"
    >
      <div class="w-full sm:max-w-md bg-[#0d0d0d] border border-white/[0.08] rounded-t-3xl sm:rounded-2xl max-h-[90vh] flex flex-col overflow-hidden">

        <!-- Header -->
        <div class="flex items-start justify-between gap-3 px-6 pt-5 pb-4 border-b border-white/[0.06]">
          <div class="min-w-0">
            <p class="font-mono text-[9px] tracking-[0.25em] uppercase text-[#DC2626]">Pilih opsi</p>
            <h3 class="mt-1 font-sora text-base font-extrabold uppercase tracking-wide text-white leading-tight">
              {{ menu.name }}
            </h3>
          </div>
          <button
            type="button"
            aria-label="Tutup"
            class="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full text-zinc-500 hover:text-white hover:bg-white/5 transition-colors"
            @click="$emit('close')"
          >
            <X :size="16" />
          </button>
        </div>

        <!-- Grup opsi -->
        <div class="flex-1 overflow-y-auto px-6 py-5 space-y-6">
          <fieldset v-for="group in menu.options" :key="group.name" class="space-y-2.5">
            <legend class="w-full flex items-baseline justify-between gap-3">
              <span class="font-sora text-[11px] font-bold uppercase tracking-widest text-white">{{ group.name }}</span>
              <span class="font-mono text-[9px] tracking-[0.15em] uppercase" :class="group.required ? 'text-[#DC2626]' : 'text-zinc-600'">
                {{ group.required ? "Wajib" : "Opsional" }} · {{ group.multiple ? "boleh lebih dari satu" : "pilih satu" }}
              </span>
            </legend>

            <div class="space-y-1.5" :role="group.multiple ? 'group' : 'radiogroup'" :aria-label="group.name">
              <button
                v-for="choice in group.choices"
                :key="choice.label"
                type="button"
                :role="group.multiple ? 'checkbox' : 'radio'"
                :aria-checked="isPicked(group, choice)"
                :class="[
                  'w-full flex items-center justify-between gap-3 px-4 py-3 border text-left transition-colors duration-150',
                  isPicked(group, choice)
                    ? 'border-[#DC2626] bg-[#DC2626]/10'
                    : 'border-white/10 bg-[#111] hover:border-white/25'
                ]"
                @click="toggle(group, choice)"
              >
                <span class="flex items-center gap-3 min-w-0">
                  <span
                    :class="[
                      'flex-shrink-0 w-4 h-4 border flex items-center justify-center',
                      group.multiple ? 'rounded-sm' : 'rounded-full',
                      isPicked(group, choice) ? 'border-[#DC2626] bg-[#DC2626]' : 'border-white/25'
                    ]"
                  >
                    <Check v-if="isPicked(group, choice)" :size="11" class="text-white" />
                  </span>
                  <span class="text-[13px] text-white truncate">{{ choice.label }}</span>
                </span>
                <span v-if="Number(choice.price) > 0" class="flex-shrink-0 font-mono text-[11px] text-amber-400">
                  +{{ formatPrice(choice.price) }}
                </span>
              </button>
            </div>
          </fieldset>
        </div>

        <!-- Footer: jumlah + konfirmasi -->
        <div class="px-6 pt-4 pb-5 border-t border-white/[0.06] bg-[#080808] space-y-3">
          <p v-if="missingGroup" class="font-mono text-[10px] text-zinc-500">
            Pilih "{{ missingGroup }}" dulu.
          </p>
          <div class="flex items-center gap-3">
            <div class="flex items-center border border-white/10 flex-shrink-0">
              <button
                type="button"
                aria-label="Kurangi jumlah"
                :disabled="quantity <= 1"
                class="w-10 h-12 flex items-center justify-center text-zinc-300 hover:text-white disabled:opacity-30 transition-colors"
                @click="quantity--"
              >
                <Minus :size="14" />
              </button>
              <span class="min-w-[2rem] text-center font-mono text-[13px] font-bold text-white">{{ quantity }}</span>
              <button
                type="button"
                aria-label="Tambah jumlah"
                :disabled="quantity >= 99"
                class="w-10 h-12 flex items-center justify-center text-zinc-300 hover:text-white disabled:opacity-30 transition-colors"
                @click="quantity++"
              >
                <Plus :size="14" />
              </button>
            </div>

            <button
              type="button"
              :disabled="!!missingGroup"
              :class="[
                'flex-1 h-12 flex items-center justify-center gap-2 px-4 font-sora text-[11px] font-bold uppercase tracking-widest transition-all duration-200',
                missingGroup
                  ? 'bg-[#1a1a1a] text-zinc-600 cursor-not-allowed border border-white/5'
                  : 'bg-[#DC2626] hover:bg-red-700 text-white active:scale-[0.98]'
              ]"
              @click="confirm"
            >
              <span>Tambah</span>
              <span class="font-mono">· {{ formatPrice(total) }}</span>
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