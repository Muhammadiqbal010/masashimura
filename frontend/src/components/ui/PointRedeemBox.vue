<template>
  <div v-if="points > 0 || affordable.length || locked.length" class="point-box">
    <div class="point-header">
      <span class="point-icon-tile"><Gift :size="15" /></span>
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
        :aria-pressed="isSelected(reward.id)"
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
        <Lock :size="12" class="point-item-lock" />
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
/* Palet: Surface #141414 · Washi #FAFAFA · Champagne #FFF500 (poin & reward) */

.point-box {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  background:
    radial-gradient(80% 100% at 100% 0%, rgba(255,245,0, 0.08), transparent 70%),
    #0D0D0D;
  border: 1px solid rgba(255,245,0, 0.18);
  border-radius: 1rem;
  padding: 1rem;
}

.point-header {
  display: flex;
  align-items: center;
  gap: 0.625rem;
}
.point-icon-tile {
  display: flex;
  height: 2rem;
  width: 2rem;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 0.625rem;
  border: 1px solid rgba(255,245,0, 0.25);
  background: rgba(255,245,0, 0.1);
  color: #FFF500;
}
.point-label {
  flex: 1;
  font-size: 0.875rem;
  font-weight: 500;
  color: #A3A3A3;
}
.point-balance {
  font-family: "Sora", ui-sans-serif, system-ui, sans-serif;
  font-weight: 600;
  font-size: 1.125rem;
  font-variant-numeric: tabular-nums;
  color: #FFF500;
}

.point-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.point-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  min-height: 2.75rem;
  text-align: left;
  border-radius: 0.75rem;
  padding: 0.625rem 0.875rem;
  font-family: "Inter", sans-serif;
  cursor: default;
}

.point-item--affordable {
  background: rgba(255,245,0, 0.05);
  border: 1px solid rgba(255,245,0, 0.2);
  cursor: pointer;
  transition: all 0.15s;
}
.point-item--affordable:hover { border-color: rgba(255,245,0, 0.45); }
.point-item--selected {
  background: rgba(255,245,0, 0.14);
  border-color: rgba(255,245,0, 0.7);
}

.point-item-check {
  width: 20px; height: 20px;
  border-radius: 6px;
  border: 1px solid rgba(255,245,0, 0.5);
  display: flex; align-items: center; justify-content: center;
  color: #1A1700;
  flex-shrink: 0;
  transition: all 0.15s;
}
.point-item--selected .point-item-check {
  background: #FFF500;
  border-color: #FFF500;
}

.point-item-name {
  flex: 1;
  min-width: 0;
  font-size: 0.875rem;
  color: #FAFAFA;
  font-weight: 600;
}
.point-item-cost {
  font-size: 0.8125rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: #FFF500;
  white-space: nowrap;
}

.point-item--locked {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  opacity: 0.65;
}
.point-item-lock { color: #737373; flex-shrink: 0; }
.point-item--locked .point-item-name { color: #A3A3A3; font-weight: 500; }
.point-item-missing {
  font-size: 0.8125rem;
  font-variant-numeric: tabular-nums;
  color: #737373;
  white-space: nowrap;
}

.point-summary {
  font-size: 0.8125rem;
  font-weight: 500;
  color: #FFF500;
  margin: 0;
  padding-left: 0.125rem;
}

.point-item--affordable:focus-visible {
  outline: 2px solid #FFF500;
  outline-offset: 2px;
}
</style>