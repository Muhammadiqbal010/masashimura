<template>
  <div class="max-w-4xl mx-auto p-4 sm:p-6 text-white space-y-6">

    <div>
      <div class="flex items-center gap-2 mb-2">
        <span class="w-1 h-1 rounded-full bg-red-600"></span>
        <p class="text-white/30 text-[10px] font-oswald uppercase tracking-[0.25em]">Masashimura · Admin</p>
      </div>
      <h1 class="font-oswald text-3xl sm:text-4xl uppercase tracking-tighter text-white">Kelola Staff</h1>
      <p class="text-white/40 text-xs sm:text-sm mt-1">Reset PIN keamanan staff yang lupa PIN-nya</p>
    </div>

    <div v-if="loading" class="text-white/40 text-sm">Memuat data staff...</div>

    <div v-else-if="staffList.length === 0" class="text-white/30 text-sm bg-[#0a0a0a] border border-white/5 rounded-2xl p-8 text-center">
      Belum ada staff terdaftar.
    </div>

    <div v-else class="bg-[#0a0a0a] border border-white/5 rounded-2xl overflow-hidden">
      <div v-for="staff in staffList" :key="staff.id"
        class="flex items-center justify-between gap-4 p-4 sm:p-5 border-b border-white/5 last:border-0">
        <div class="min-w-0">
          <p class="font-medium text-sm truncate">{{ staff.full_name || staff.username }}</p>
          <p class="text-white/40 text-xs font-mono truncate">{{ staff.username }} · {{ staff.email }}</p>
          <div class="flex items-center gap-2 mt-1">
            <span class="text-[10px] uppercase px-2 py-0.5 rounded-full bg-white/5 text-white/50">{{ staff.role }}</span>
            <span v-if="!staff.has_pin" class="text-[10px] uppercase px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400">
              Belum ada PIN
            </span>
            <span v-if="!staff.is_active" class="text-[10px] uppercase px-2 py-0.5 rounded-full bg-red-500/10 text-red-400">
              Nonaktif
            </span>
          </div>
        </div>
        <button
          @click="openPinModal(staff)"
          class="shrink-0 text-xs font-oswald uppercase tracking-wide px-4 py-2 rounded-lg bg-red-600/10 border border-red-600/30 text-red-400 hover:bg-red-600/20 transition"
        >
          Reset PIN
        </button>
      </div>
    </div>

    <!-- Modal Reset PIN -->
    <div v-if="pinModalStaff" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
      @click.self="pinModalStaff = null">
      <div class="bg-[#0f0f0f] border border-white/10 rounded-2xl w-full max-w-sm p-6 space-y-4">
        <h3 class="font-oswald text-lg uppercase">Reset PIN — {{ pinModalStaff.username }}</h3>
        <p class="text-white/40 text-xs">Masukkan PIN baru, lalu beritahu langsung ke staff ini secara lisan (bukan lewat chat).</p>
        <input
          v-model="newPin" type="text" inputmode="numeric" maxlength="6"
          placeholder="6 digit PIN baru..."
          class="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 text-sm font-mono tracking-widest text-white outline-none focus:border-red-600"
          @input="newPin = newPin.replace(/\D/g, '').slice(0, 6)"
        />
        <div class="grid grid-cols-2 gap-2">
          <button @click="submitNewPin" :disabled="!/^\d{6}$/.test(newPin) || submitting"
            class="py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-xs font-oswald uppercase disabled:opacity-40">
            {{ submitting ? 'Menyimpan...' : 'Simpan PIN' }}
          </button>
          <button @click="pinModalStaff = null" class="py-2.5 rounded-xl bg-white/5 border border-white/10 text-xs font-oswald uppercase">
            Batal
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { toast } from "vue-sonner";
import apiClient from "@/api/client";

const staffList = ref([]);
const loading = ref(true);
const pinModalStaff = ref(null);
const newPin = ref("");
const submitting = ref(false);

const fetchStaff = async () => {
  loading.value = true;
  try {
    const res = await apiClient.get("/auth/staff/list/");
    staffList.value = res.data;
  } catch (error) {
    console.error("Fetch Staff Error:", error);
    toast.error("Gagal memuat daftar staff.");
  } finally {
    loading.value = false;
  }
};

const openPinModal = (staff) => {
  pinModalStaff.value = staff;
  newPin.value = "";
};

const submitNewPin = async () => {
  submitting.value = true;
  try {
    await apiClient.post("/auth/staff/set-pin/", {
      user_id: pinModalStaff.value.id,
      new_pin: newPin.value,
    });
    toast.success(`PIN ${pinModalStaff.value.username} berhasil di-reset!`);
    pinModalStaff.value.has_pin = true;
    pinModalStaff.value = null;
  } catch (error) {
    console.error("Set PIN Error:", error);
    toast.error(error.response?.data?.detail || error.response?.data?.new_pin?.[0] || "Gagal reset PIN.");
  } finally {
    submitting.value = false;
  }
};

onMounted(fetchStaff);
</script>