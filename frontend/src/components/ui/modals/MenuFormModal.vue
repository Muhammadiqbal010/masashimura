<template>
  <MenuForm
    v-if="open"
    :editing-menu="editingMenu"
    @saved="onDone"
    @close="close"
  />
</template>

<script setup>
import MenuForm from "../forms/MenuForm.vue";

defineProps({
  open: Boolean,
  editingMenu: Object,
});

const emit = defineEmits(["update:open", "created"]);

const close = () => emit("update:open", false);
const onDone = () => {
  emit("created");
  close();
};
</script>
