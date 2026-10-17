<template>
  <section v-if="items.length" class="reco" :class="`reco--${variant}`" :aria-label="title">
    <header class="reco-head">
      <h3 class="reco-title">{{ title }}</h3>
      <p v-if="subtitle" class="reco-sub">{{ subtitle }}</p>
    </header>

    <!-- ── Variant "cards": detail menu. HP = geser horizontal, layar lebar = 3 kolom rata ── -->
    <ul v-if="variant === 'cards'" class="reco-cards">
      <li v-for="rec in items" :key="rec.menu.id" class="reco-card">
        <button
          type="button"
          class="reco-card-main"
          :aria-label="'Lihat ' + rec.menu.name"
          @click="$emit('select', rec.menu)"
        >
          <span class="reco-thumb reco-thumb--wide">
            <img
              v-if="rec.menu.image_url"
              :src="getMediaUrl(rec.menu.image_url, 320)"
              :alt="rec.menu.name"
              loading="lazy"
            />
            <span v-else class="reco-thumb-fallback" aria-hidden="true">🍜</span>
          </span>
          <span class="reco-name">{{ rec.menu.name }}</span>
          <span v-if="showReason && rec.reason?.length" class="reco-reason">Mirip: {{ rec.reason.join(", ") }}</span>
        </button>

        <div class="reco-foot">
          <span class="reco-price">{{ formatPrice(rec.menu.price_web) }}</span>
          <button
            type="button"
            class="reco-add"
            :aria-label="'Tambah ' + rec.menu.name"
            :title="canAdd ? undefined : 'Toko sedang tutup'"
            :disabled="!canAdd"
            @click="$emit('add', rec.menu)"
          >
            <Plus :size="16" />
          </button>
        </div>
      </li>
    </ul>

    <!-- ── Variant "list": drawer keranjang. Baris ringkas, target sentuh >= 44px ── -->
    <ul v-else class="reco-list">
      <li v-for="rec in items" :key="rec.menu.id" class="reco-row">
        <button
          type="button"
          class="reco-row-main"
          :aria-label="'Lihat ' + rec.menu.name"
          @click="$emit('select', rec.menu)"
        >
          <span class="reco-thumb reco-thumb--square">
            <img
              v-if="rec.menu.image_url"
              :src="getMediaUrl(rec.menu.image_url, 160)"
              :alt="rec.menu.name"
              loading="lazy"
            />
            <span v-else class="reco-thumb-fallback" aria-hidden="true">🍜</span>
          </span>
          <span class="reco-row-text">
            <span class="reco-name reco-name--row">{{ rec.menu.name }}</span>
            <span class="reco-price">{{ formatPrice(rec.menu.price_web) }}</span>
          </span>
        </button>
        <button
          type="button"
          class="reco-add reco-add--row"
          :aria-label="'Tambah ' + rec.menu.name"
          :title="canAdd ? undefined : 'Toko sedang tutup'"
          :disabled="!canAdd"
          @click="$emit('add', rec.menu)"
        >
          <Plus :size="18" />
        </button>
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
  subtitle: { type: String, default: "" },
  formatPrice: { type: Function, required: true },
  showReason: { type: Boolean, default: false },
  canAdd: { type: Boolean, default: true },
  // "cards" = kartu bergambar (detail menu) · "list" = baris ringkas (keranjang)
  variant: { type: String, default: "cards", validator: (v) => ["cards", "list"].includes(v) },
})

defineEmits(["select", "add"])
</script>

<style scoped>
/* Palet: Surface #141414 · Washi #FAFAFA · Crimson #D92B22 · Champagne #F4C542 */

.reco { display: flex; flex-direction: column; gap: 0.75rem; }
.reco-head { display: flex; flex-direction: column; gap: 0.15rem; }
.reco-title { margin: 0; font-size: 0.8125rem; font-weight: 600; color: #FAFAFA; letter-spacing: -0.01em; }
.reco-sub { margin: 0; font-size: 0.75rem; color: #737373; }

/* ── Thumbnail ── */
.reco-thumb { display: block; overflow: hidden; background: #1A1A1A; flex-shrink: 0; }
.reco-thumb img { display: block; width: 100%; height: 100%; object-fit: cover; }
.reco-thumb--wide { aspect-ratio: 4 / 3; width: 100%; border-radius: 0.75rem; }
.reco-thumb--square { width: 3.5rem; height: 3.5rem; border-radius: 0.75rem; }
.reco-thumb-fallback { display: flex; width: 100%; height: 100%; align-items: center; justify-content: center; font-size: 1.25rem; opacity: 0.25; }

.reco-name {
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  font-size: 0.8125rem; font-weight: 600; line-height: 1.3; color: #FAFAFA;
}
.reco-price { font-size: 0.8125rem; font-weight: 600; color: #C8C8C8; font-variant-numeric: tabular-nums; }
.reco-reason { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 0.6875rem; color: #737373; }

/* ── Tombol tambah: 40px di HP (mudah ditekan jempol), 36px di layar lebar ── */
.reco-add {
  display: flex; flex-shrink: 0; align-items: center; justify-content: center;
  width: 2.5rem; height: 2.5rem; border-radius: 9999px;
  border: 1px solid rgba(244, 197, 66, 0.3); background: rgba(244, 197, 66, 0.08); color: #F4C542;
  cursor: pointer; transition: background-color 0.15s ease, border-color 0.15s ease, transform 0.1s ease;
}
.reco-add:hover:not(:disabled) { background: rgba(244, 197, 66, 0.16); border-color: rgba(244, 197, 66, 0.5); }
.reco-add:active:not(:disabled) { transform: scale(0.94); }
.reco-add:disabled { cursor: not-allowed; border-color: rgba(255, 255, 255, 0.08); background: rgba(255, 255, 255, 0.03); color: #737373; }
@media (min-width: 640px) { .reco-add { width: 2.25rem; height: 2.25rem; } }

/* ── Cards ── */
.reco-cards {
  display: flex; gap: 0.75rem; margin: 0; padding: 0 var(--rec-bleed, 0px) 0.25rem; list-style: none;
  margin-inline: calc(var(--rec-bleed, 0px) * -1);
  overflow-x: auto; scroll-snap-type: x proximity; scroll-padding-inline: var(--rec-bleed, 0px);
  scrollbar-width: none;
}
.reco-cards::-webkit-scrollbar { display: none; }
.reco-card {
  display: flex; flex-direction: column; justify-content: space-between; gap: 0.5rem;
  flex: 0 0 8.75rem; scroll-snap-align: start; padding: 0.5rem;
  border-radius: 1rem; border: 1px solid rgba(255, 255, 255, 0.07);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.01)), #141414;
}
.reco-card-main { display: flex; flex-direction: column; gap: 0.4rem; width: 100%; padding: 0; border: 0; background: none; text-align: left; cursor: pointer; }
.reco-card-main .reco-name { min-height: 2.1rem; }
.reco-foot { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; }

/* Layar lebar: tiga kartu rata memenuhi lebar, tanpa geser */
@media (min-width: 640px) {
  .reco-cards { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); margin-inline: 0; padding: 0; overflow: visible; }
  .reco-card { flex: none; }
}

/* ── List ── */
.reco--list {
  padding: 0.875rem 0.875rem 0.25rem; gap: 0.25rem;
  border-radius: 1.25rem; border: 1px solid rgba(255, 255, 255, 0.07);
  background: rgba(255, 255, 255, 0.02);
}
.reco--list .reco-head { padding: 0 0.125rem 0.375rem; }
.reco-list { display: flex; flex-direction: column; margin: 0; padding: 0; list-style: none; }
.reco-row { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0; }
.reco-row + .reco-row { border-top: 1px solid rgba(255, 255, 255, 0.06); }
.reco-row-main { display: flex; flex: 1; min-width: 0; align-items: center; gap: 0.75rem; padding: 0; border: 0; background: none; text-align: left; cursor: pointer; }
.reco-row-text { display: flex; flex-direction: column; gap: 0.1rem; min-width: 0; }
.reco-name--row { -webkit-line-clamp: 2; }
.reco-add--row { width: 2.75rem; height: 2.75rem; }
@media (min-width: 640px) { .reco-add--row { width: 2.5rem; height: 2.5rem; } }

button:focus-visible { outline: 2px solid #F4C542; outline-offset: 2px; }

@media (prefers-reduced-motion: reduce) {
  .reco-add { transition: none; }
  .reco-add:active:not(:disabled) { transform: none; }
}
</style>