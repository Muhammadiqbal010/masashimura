<template>
  <AdminModal
    :model-value="state.open"
    :title="state.title"
    size="sm"
    @update:model-value="(v) => !v && emit('cancel')"
  >
    <p class="adm-modal-text">{{ state.message }}</p>
    <template #footer>
      <button type="button" class="adm-btn adm-btn--ghost" @click="emit('cancel')">
        {{ state.cancelText }}
      </button>
      <button
        type="button"
        class="adm-btn"
        :class="state.danger ? 'adm-btn--danger' : 'adm-btn--primary'"
        data-autofocus
        @click="emit('confirm')"
      >
        {{ state.confirmText }}
      </button>
    </template>
  </AdminModal>
</template>

<script setup>
import AdminModal from '@/components/ui/admin/Adminmodal.vue'

defineProps({ state: { type: Object, required: true } })
const emit = defineEmits(['confirm', 'cancel'])
</script>