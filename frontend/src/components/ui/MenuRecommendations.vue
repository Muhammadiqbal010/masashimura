<template>
  <section v-if="items.length" class="space-y-2.5" :aria-label="title">
    <div class="flex items-baseline justify-between gap-3">
      <span class="block text-xs font-medium text-[#737373]">{{ title }}</span>
    </div>

    <ul class="-mx-1 flex snap-x gap-3 overflow-x-auto px-1 pb-1">
      <li
        v-for="rec in items"
        :key="rec.menu.id"
        class="rec-card snap-start"
      >
        <button
          type="button"
          class="block w-full text-left"
          :aria-label="'Lihat ' + rec.menu.name"
          @click="$emit('select', rec.menu)"
        >
          <div class="aspect-[4/3] w-full overflow-hidden rounded-xl bg-[#1A1A1A]">
            <img
              v-if="rec.menu.image_url"
              :src="getMediaUrl(rec.menu.image_url, 320)"
              :alt="rec.menu.name"
              class="h-full w-full object-cover"
              loading="lazy"
            />
            <div v-else class="flex h-full w-full items-center justify-center">
              <span class="text-xl opacity-25">🍜</span>
            </div>
          </div>
          <p class="mt-2 line-clamp-2 text-[13px] font-semibold leading-snug text-[#FAFAFA]">
            {{ rec.menu.name }}
          </p>
          <p v-if="showReason && rec.reason?.length" class="mt-0.5 truncate text-[11px] text-[#737373]">
            Mirip: {{ rec.reason.join(", ") }}
          </p>
        </button>

        <div class="mt-2 flex items-center justify-between gap-2">
          <span class="text-[13px] font-semibold tabular-nums text-[#C8C8C8]">
            {{ formatPrice(rec.menu.price_web) }}
          </span>
          <button
            type="button"
            :aria-label="'Tambah ' + rec.menu.name"
            :disabled="!canAdd"
            class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] text-[#F4C542] transition-colors hover:bg-white/10 disabled:cursor-not-allowed disabled:text-[#737373]"
            @click="$emit('add', rec.menu)"
          >
            <Plus :size="14" />
          </button>
        </div>
      </li>
    </ul>
  </section>
</template>

<script setup>
import { Plus } from "lucide-vue-next"
import { getMediaUrl } from "@/api"

defineProps({
  // [{ menu, score, reason }] dari utils/recommender.js
  items: { type: Array, default: () => [] },
  title: { type: String, required: true },
  formatPrice: { type: Function, required: true },
  showReason: { type: Boolean, default: false },
  canAdd: { type: Boolean, default: true },
})

defineEmits(["select", "add"])
</script>

<style scoped>
.rec-card {
  width: 9.25rem;
  flex-shrink: 0;
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.07);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.01)), #141414;
  padding: 0.5rem;
}

button:focus-visible {
  outline: 2px solid #F4C542;
  outline-offset: 3px;
}

ul::-webkit-scrollbar { height: 3px; }
ul::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 99px; }
</style>
