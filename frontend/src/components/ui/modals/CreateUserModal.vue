<template>
  <div
    v-if="open"
    class="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
  >
    <div
      class="bg-[#0a0a0a] border border-white/10 rounded-3xl w-full max-w-md overflow-hidden shadow-2xl"
    >
      <div class="px-8 py-6 border-b border-white/10">
        <h2 class="font-oswald text-2xl uppercase tracking-tight text-white">
          Buat Akun Baru
        </h2>
        <p class="text-white/50 text-sm">
          Hanya Owner yang dapat mendaftarkan staff
        </p>
      </div>

      <form
        @submit.prevent="handleSubmit"
        class="p-8 space-y-6"
        autocomplete="off"
      >
        <div>
          <label class="block text-sm text-white/70 mb-2">Username</label>
          <input
            v-model="form.username"
            type="text"
            required
            class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-red-500 outline-none transition-colors"
            placeholder="username_staff"
          />
        </div>

        <div>
          <label class="block text-sm text-white/70 mb-2">Email</label>
          <input
            v-model="form.email"
            type="email"
            required
            class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-red-500 outline-none transition-colors"
            placeholder="staff@masashimura.id"
          />
        </div>

        <div>
          <label class="block text-sm text-white/70 mb-2">Password</label>
          <input
            v-model="form.password"
            type="password"
            required
            class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-red-500 outline-none transition-colors"
          />
        </div>

        <div>
          <label class="block text-sm text-white/70 mb-2"
            >Hak Akses (Role)</label
          >
          <select
            v-model="form.role"
            class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-red-500 outline-none transition-colors"
          >
            <option value="kasir">Kasir</option>
            <option value="admin">Admin</option>
            <option value="owner">Owner</option>
          </select>
        </div>

        <div class="flex gap-4 pt-4">
          <button
            type="button"
            @click="closeModal"
            class="flex-1 py-4 border border-white/20 rounded-2xl text-white/70 hover:bg-white/5 transition"
          >
            Batal
          </button>
          <button
            type="submit"
            :disabled="loading"
            class="flex-1 py-4 bg-red-600 hover:bg-red-500 text-white rounded-2xl font-bold uppercase transition disabled:opacity-50"
          >
            {{ loading ? "Memproses..." : "Buat Akun" }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { toast } from "vue-sonner";
import { authAPI } from "@/api";

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
