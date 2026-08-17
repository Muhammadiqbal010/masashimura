<template>
  <div
    v-if="open"
    class="fixed inset-0 z-[110] flex items-center justify-center bg-black/90 backdrop-blur-md p-4"
  >
    <div
      class="bg-[#0a0a0a] w-full max-w-2xl rounded-2xl overflow-hidden border border-white/10 shadow-2xl flex flex-col max-h-[90vh]"
    >
      <div
        class="px-8 py-6 border-b border-white/5 flex items-center justify-between bg-white/[0.02]"
      >
        <h2
          class="text-2xl font-oswald uppercase tracking-wider text-white italic"
        >
          {{ editingMenu ? "Edit Menu" : "Tambah Menu Baru" }}
        </h2>
        <button
          @click="$emit('update:open', false)"
          class="text-white/40 hover:text-red-400 text-3xl"
        >
          ✕
        </button>
      </div>

      <MenuForm
        :editing-menu="editingMenu"
        @created="
          $emit('created');
          $emit('update:open', false);
        "
        @cancel="$emit('update:open', false)"
      />
    </div>
  </div>
</template>

<script setup>
import MenuForm from "../forms/MenuForm.vue";

defineProps({
  open: Boolean,
  editingMenu: Object,
});

defineEmits(["update:open", "created"]);
</script>
