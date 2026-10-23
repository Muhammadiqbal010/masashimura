<template>
  <AdminModal v-model="isOpen" title="Buat Akun Baru" size="sm" :persistent="loading">
    <form id="create-user-form" class="cu-form" autocomplete="off" @submit.prevent="handleSubmit">
      <p class="adm-modal-text">Hanya Owner yang dapat mendaftarkan staff.</p>

      <div class="adm-field">
        <label class="adm-label" for="cu-username">Username</label>
        <input id="cu-username" v-model="form.username" data-autofocus type="text" required class="adm-input" placeholder="username_staff" />
      </div>

      <div class="adm-field">
        <label class="adm-label" for="cu-email">Email</label>
        <input id="cu-email" v-model="form.email" type="email" required class="adm-input" placeholder="staff@masashimura.id" />
      </div>

      <div class="adm-field">
        <label class="adm-label" for="cu-password">Password</label>
        <input id="cu-password" v-model="form.password" type="password" required class="adm-input" />
      </div>

      <div class="adm-field">
        <label class="adm-label" for="cu-role">Hak Akses (Role)</label>
        <select id="cu-role" v-model="form.role" class="adm-input">
          <option value="kasir">Kasir</option>
          <option value="admin">Admin</option>
          <option value="owner">Owner</option>
        </select>
      </div>
    </form>

    <template #footer>
      <button type="button" class="adm-btn adm-btn--ghost" :disabled="loading" @click="closeModal">Batal</button>
      <button type="submit" form="create-user-form" class="adm-btn adm-btn--primary" :disabled="loading">
        <span v-if="loading" class="adm-spinner"></span>
        {{ loading ? "Memproses..." : "Buat Akun" }}
      </button>
    </template>
  </AdminModal>
</template>

<script setup>
import { ref, computed } from "vue";
import { toast } from "vue-sonner";
import { authAPI } from "@/api";
import AdminModal from "@/components/ui/admin/Adminmodal.vue";

const props = defineProps({
  open: { type: Boolean, required: true },
});

const emit = defineEmits(["update:open", "created"]);

const form = ref({
  username: "",
  email: "",
  password: "",
  role: "kasir",
});

const loading = ref(false);

// AdminModal memakai v-model; antarmuka publik komponen ini tetap `open` + `update:open`.
const isOpen = computed({
  get: () => props.open,
  set: (v) => { if (!v) closeModal(); },
});

const handleSubmit = async () => {
  loading.value = true;
  try {
    await authAPI.createUser(form.value);
    toast.success(`Akun ${form.value.username} sukses dibuat!`);
    emit("created");
    closeModal();
  } catch (err) {
    toast.error(err.response?.data?.detail || "Gagal mendaftarkan akun baru");
  } finally {
    loading.value = false;
  }
};

const closeModal = () => {
  emit("update:open", false);
  // Reset form setelah tutup
  form.value = { username: "", email: "", password: "", role: "kasir" };
};
</script>

<style scoped>
.cu-form { display: flex; flex-direction: column; gap: 1rem; }
</style>
