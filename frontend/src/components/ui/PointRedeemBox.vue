<template>
  <div v-if="points > 0 || affordable.length || locked.length" class="point-box">
    <div class="point-header">
      <Gift :size="14" class="point-icon" />
      <span class="point-label">Poin kamu</span>
      <span class="point-balance">{{ points.toLocaleString("id-ID") }}</span>
    </div>

    <!-- Reward yang bisa ditukar sekarang -->
    <div v-if="affordable.length" class="point-list">
      <button
        v-for="reward in affordable"
        :key="reward.id"
        type="button"
        class="point-item point-item--affordable"
        :class="{ 'point-item--selected': isSelected(reward.id) }"
        @click="toggle(reward.id)"
      >
        <span class="point-item-check">
          <Check v-if="isSelected(reward.id)" :size="12" />
        </span>
        <span class="point-item-name">{{ reward.menu_name }}</span>
        <span class="point-item-cost">{{ reward.point_cost.toLocaleString("id-ID") }} poin</span>
      </button>
    </div>

    <!-- Reward yang belum cukup poin (gamifikasi: "kurang X poin lagi") -->
    <div v-if="locked.length" class="point-list point-list--locked">
      <div
        v-for="reward in locked"
        :key="reward.id"
        class="point-item point-item--locked"
      >
        <Lock :size="11" class="point-item-lock" />
        <span class="point-item-name">{{ reward.menu_name }}</span>
        <span class="point-item-missing">kurang {{ reward.missing_points.toLocaleString("id-ID") }} poin</span>
      </div>
    </div>

    <p v-if="selectedIds.length" class="point-summary">
      {{ selectedIds.length }} reward dipilih · −{{ totalPointsUsed.toLocaleString("id-ID") }} poin
    </p>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { Gift, Check, Lock } from "lucide-vue-next";

const props = defineProps({
  points: { type: Number, default: 0 },
  affordable: { type: Array, default: () => [] },
  locked: { type: Array, default: () => [] },
  selectedIds: { type: Array, default: () => [] },
});

const emit = defineEmits(["update:selectedIds"]);

const isSelected = (id) => props.selectedIds.includes(id);

const toggle = (id) => {
  const next = isSelected(id)
    ? props.selectedIds.filter((x) => x !== id)
    : [...props.selectedIds, id];
  emit("update:selectedIds", next);
};

const totalPointsUsed = computed(() =>
  props.affordable
    .filter((r) => props.selectedIds.includes(r.id))
    .reduce((sum, r) => sum + r.point_cost, 0)
);
</script>

<style scoped>
.point-box {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  background: #0f0f0f;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 0.75rem 0.85rem;
}

.point-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.point-icon { color: #fbbf24; }
.point-label {
  font-family: monospace;
  font-size: 0.68rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.4);
  flex: 1;
}
.point-balance {
  font-family: monospace;
  font-weight: 700;
  font-size: 0.85rem;
  color: #fbbf24;
}

.point-list {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.point-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  text-align: left;
  border-radius: 9px;
  padding: 0.5rem 0.65rem;
  font-family: "Inter", sans-serif;
  cursor: default;
}

.point-item--affordable {
  background: rgba(34, 197, 94, 0.06);
  border: 1px solid rgba(34, 197, 94, 0.2);
  cursor: pointer;
  transition: all 0.15s;
}
.point-item--affordable:hover { border-color: rgba(34, 197, 94, 0.4); }
.point-item--selected {
  background: rgba(34, 197, 94, 0.15);
  border-color: rgba(34, 197, 94, 0.6);
}

.point-item-check {
  width: 16px; height: 16px;
  border-radius: 5px;
  border: 1px solid rgba(74, 222, 128, 0.5);
  display: flex; align-items: center; justify-content: center;
  color: #4ade80;
  flex-shrink: 0;
}

.point-item-name {
  flex: 1;
  font-size: 0.78rem;
  color: #fff;
  font-weight: 600;
}
.point-item-cost {
  font-family: monospace;
  font-size: 0.7rem;
  color: #4ade80;
  white-space: nowrap;
}

.point-item--locked {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  opacity: 0.55;
}
.point-item-lock { color: rgba(255, 255, 255, 0.3); flex-shrink: 0; }
.point-item--locked .point-item-name { color: rgba(255, 255, 255, 0.5); font-weight: 500; }
.point-item-missing {
  font-family: monospace;
  font-size: 0.68rem;
  color: rgba(255, 255, 255, 0.35);
  white-space: nowrap;
}

.point-summary {
  font-family: monospace;
  font-size: 0.7rem;
  color: #fbbf24;
  margin: 0;
  padding-left: 0.15rem;
}
</style>
