<template>
  <div class="p-4 sm:p-8 text-[color:var(--text)] max-w-2xl mx-auto w-full box-border">

    <!-- ═══ HEADER ════════════════════════════════════════════════════ -->
    <div class="mb-6 sm:mb-8">
      <div class="flex items-center gap-2 mb-2">
        <span class="w-1 h-1 rounded-full bg-red-600"></span>
        <p class="text-[color:var(--text-faint)] text-[10px] font-oswald uppercase tracking-[0.25em]">Masashimura · Admin</p>
      </div>
      <h1 class="font-oswald text-2xl sm:text-4xl uppercase tracking-tighter text-[color:var(--text)] leading-tight">
        Register Staff Internal
      </h1>
      <p class="text-[color:var(--text-faint)] text-xs sm:text-sm mt-1.5">
        Daftarkan akun karyawan baru (Admin/Kasir) untuk operasional Masashimura
      </p>
    </div>

    <div class="bg-[color:var(--surface)] border border-[color:rgb(var(--ink)/0.05)] rounded-2xl sm:rounded-3xl p-5 sm:p-8 shadow-2xl shadow-black/40">
      <form @submit.prevent="handleInternalRegister" class="space-y-5 sm:space-y-6" novalidate>

        <!-- Nama -->
        <div class="space-y-2">
          <label for="staff-name" class="block text-[10px] uppercase tracking-widest font-bold text-[color:var(--text-2)]">
            Nama Lengkap Karyawan
          </label>
          <div class="relative">
            <User :size="16" class="absolute left-4 top-1/2 -translate-y-1/2 text-[color:var(--text-faint)]" />
            <input
              id="staff-name"
              v-model="formData.name"
              type="text"
              required
              :disabled="loading"
              class="w-full bg-[color:rgb(var(--ink)/0.05)] border border-[color:rgb(var(--ink)/0.1)] text-[color:var(--text)] rounded-xl h-12 pl-11 pr-4 outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600/30 transition-all placeholder-[color:var(--text-faint)] disabled:opacity-50 text-sm"
              placeholder="Masukkan nama lengkap staff..."
            />
          </div>
        </div>

        <!-- Email -->
        <div class="space-y-2">
          <label for="staff-email" class="block text-[10px] uppercase tracking-widest font-bold text-[color:var(--text-2)]">
            Alamat Email Login
          </label>
          <div class="relative">
            <Mail :size="16" class="absolute left-4 top-1/2 -translate-y-1/2 text-[color:var(--text-faint)]" />
            <input
              id="staff-email"
              v-model="formData.email"
              type="email"
              required
              :disabled="loading"
              :class="[
                'w-full bg-[color:rgb(var(--ink)/0.05)] border text-[color:var(--text)] rounded-xl h-12 pl-11 pr-10 outline-none transition-all placeholder-[color:var(--text-faint)] disabled:opacity-50 text-sm font-mono',
                emailTouched && formData.email && !emailValid
                  ? 'border-red-500/60 focus:border-red-500 focus:ring-1 focus:ring-red-500/30'
                  : 'border-[color:rgb(var(--ink)/0.1)] focus:border-red-600 focus:ring-1 focus:ring-red-600/30'
              ]"
              placeholder="contoh: kasir.masashimura@id"
              @blur="emailTouched = true"
            />
            <CheckCircle2
              v-if="emailTouched && emailValid"
              :size="16"
              class="absolute right-4 top-1/2 -translate-y-1/2 text-[color:var(--green-soft)]"
            />
          </div>
          <p v-if="emailTouched && formData.email && !emailValid" class="text-[color:color-mix(in_srgb,var(--red-soft)_80%,transparent)] text-[11px] pl-1">
            Format email belum valid
          </p>
        </div>

        <!-- Role -->
        <div class="space-y-2">
          <label class="block text-[10px] uppercase tracking-widest font-bold text-[color:var(--text-2)]">
            Role / Hak Akses Sistem
          </label>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            <button
              v-for="r in roleOptions"
              :key="r.value"
              type="button"
              :disabled="loading"
              @click="formData.role = r.value"
              :class="[
                'text-left rounded-xl border p-3.5 transition-all disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-600/60',
                formData.role === r.value
                  ? 'border-red-600/60 bg-red-600/10'
                  : 'border-[color:rgb(var(--ink)/0.1)] bg-[color:rgb(var(--ink)/0.02)] hover:bg-[color:rgb(var(--ink)/0.05)] hover:border-[color:rgb(var(--ink)/0.2)]'
              ]"
            >
              <div class="flex items-center gap-2.5 mb-1">
                <div
                  :class="[
                    'w-8 h-8 rounded-lg flex items-center justify-center shrink-0 transition-colors',
                    formData.role === r.value ? 'bg-red-600/20' : 'bg-[color:rgb(var(--ink)/0.05)]'
                  ]"
                >
                  <component :is="r.icon" :size="15" :class="formData.role === r.value ? 'text-[color:var(--red-soft)]' : 'text-[color:var(--text-faint)]'" />
                </div>
                <span class="font-oswald uppercase text-xs tracking-wide text-[color:var(--text)]">{{ r.label }}</span>
                <CheckCircle2 v-if="formData.role === r.value" :size="14" class="text-[color:var(--accent-text)] ml-auto" />
              </div>
              <p class="text-[color:var(--text-faint)] text-[11px] leading-snug pl-[42px] -mt-0.5">{{ r.desc }}</p>
            </button>
          </div>
        </div>

        <!-- Password -->
        <div class="space-y-2">
          <label for="staff-password" class="block text-[10px] uppercase tracking-widest font-bold text-[color:var(--text-2)]">
            Password Akun
          </label>
          <div class="relative">
            <Lock :size="16" class="absolute left-4 top-1/2 -translate-y-1/2 text-[color:var(--text-faint)]" />
            <input
              id="staff-password"
              v-model="formData.password"
              :type="showPassword ? 'text' : 'password'"
              required
              minlength="8"
              :disabled="loading"
              class="w-full bg-[color:rgb(var(--ink)/0.05)] border border-[color:rgb(var(--ink)/0.1)] text-[color:var(--text)] rounded-xl h-12 pl-11 pr-12 outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600/30 transition-all placeholder-[color:var(--text-faint)] disabled:opacity-50 text-sm font-mono"
              placeholder="••••••••"
            />
            <button
              type="button"
              tabindex="-1"
              @click="showPassword = !showPassword"
              class="absolute right-4 top-1/2 -translate-y-1/2 text-[color:var(--text-faint)] hover:text-[color:var(--text)] transition-colors"
            >
              <component :is="showPassword ? EyeOff : Eye" :size="18" />
            </button>
          </div>

          <!-- Strength meter -->
          <div v-if="formData.password" class="flex items-center gap-2 pt-1">
            <div class="flex gap-1 flex-1">
              <span
                v-for="i in 4"
                :key="i"
                class="h-1 flex-1 rounded-full transition-colors"
                :class="i <= passwordStrength.score ? passwordStrength.color : 'bg-[color:rgb(var(--ink)/0.08)]'"
              ></span>
            </div>
            <span class="text-[10px] uppercase tracking-wider shrink-0" :class="passwordStrength.textColor">
              {{ passwordStrength.label }}
            </span>
          </div>
        </div>

        <!-- PIN Keamanan -->
<div class="space-y-2">
  <label for="staff-pin" class="block text-[10px] uppercase tracking-widest font-bold text-[color:var(--text-2)]">
    PIN Keamanan (6 digit)
  </label>
  <div class="relative">
    <KeyRound :size="16" class="absolute left-4 top-1/2 -translate-y-1/2 text-[color:var(--text-faint)]" />
    <input
      id="staff-pin"
      v-model="formData.securityPin"
      type="text"
      inputmode="numeric"
      maxlength="6"
      required
      :disabled="loading"
      class="w-full bg-[color:rgb(var(--ink)/0.05)] border border-[color:rgb(var(--ink)/0.1)] text-[color:var(--text)] rounded-xl h-12 pl-11 pr-4 outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600/30 transition-all placeholder-[color:var(--text-faint)] disabled:opacity-50 text-sm font-mono tracking-widest"
      placeholder="6 digit angka..."
      @input="formData.securityPin = formData.securityPin.replace(/\D/g, '').slice(0, 6)"
    />
  </div>
  <p class="text-[color:var(--text-faint)] text-[11px] pl-1">
    Beritahu PIN ini ke staff secara langsung (lisan/tatap muka), bukan lewat chat. PIN ini dipakai staff buat reset password sendiri kalau lupa.
  </p>
</div>

        <!-- Submit -->
        <button
          type="submit"
          :disabled="loading || !canSubmit"
          class="w-full bg-red-600 hover:bg-red-500 text-white font-oswald uppercase tracking-widest h-14 rounded-xl font-bold transition-all flex justify-center items-center gap-2 cursor-pointer disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-red-600 shadow-[0_4px_20px_rgba(220,38,38,0.15)] text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400"
        >
          <span
            v-if="loading"
            class="animate-spin inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full"
          />
          <component v-else :is="UserPlus" :size="16" />
          {{ loading ? "MENDAFTARKAN STAFF..." : "BUAT AKUN KARYAWAN" }}
        </button>

        <p class="text-center text-[color:var(--text-faint)] text-[11px]">
          Akun baru akan langsung aktif dan bisa login sesuai role yang dipilih.
        </p>
      </form>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { toast } from "vue-sonner";
import {
  Eye, EyeOff, User, Mail, Lock, CheckCircle2, KeyRound,
  ChefHat, ShieldCheck, UserPlus,
} from "lucide-vue-next";
import apiClient from "@/api/client";

const loading = ref(false);
const showPassword = ref(false);
const emailTouched = ref(false);

const formData = ref({
  name: "",
  email: "",
  password: "",
  securityPin: "",
  role: "kasir",
});

const roleOptions = [
  { value: "kasir", label: "Kasir", desc: "Staff outlet lapangan", icon: ChefHat },
  { value: "admin", label: "Admin", desc: "Manajer operasional", icon: ShieldCheck },
];

const emailValid = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.value.email));
const pinValid = computed(() => /^\d{6}$/.test(formData.value.securityPin));

const passwordStrength = computed(() => {
  const p = formData.value.password;
  let score = 0;
  if (p.length >= 8) score++;
  if (/[A-Z]/.test(p) && /[a-z]/.test(p)) score++;
  if (/\d/.test(p)) score++;
  if (/[^A-Za-z0-9]/.test(p) && p.length >= 10) score++;

  const levels = [
    { label: "Lemah", color: "bg-red-500", textColor: "text-[color:var(--red-soft)]" },
    { label: "Lemah", color: "bg-red-500", textColor: "text-[color:var(--red-soft)]" },
    { label: "Cukup", color: "bg-amber-500", textColor: "text-[color:var(--amber-soft)]" },
    { label: "Kuat", color: "bg-emerald-500", textColor: "text-[color:var(--green-soft)]" },
    { label: "Sangat Kuat", color: "bg-emerald-500", textColor: "text-[color:var(--green-soft)]" },
  ];
  return { score, ...levels[score] };
});

const canSubmit = computed(() =>
  formData.value.name.trim().length > 0 &&
  emailValid.value &&
  formData.value.password.length >= 8 &&
  pinValid.value
);

// Username dibuat dari bagian depan email — bukan nama lengkap, biar gak ada spasi
const generateUsername = (email) => email.split("@")[0].toLowerCase();

const handleInternalRegister = async () => {
  emailTouched.value = true;
  if (!canSubmit.value) {
    toast.error("Periksa kembali data yang diisi (email valid, password min. 8 karakter, PIN 6 digit).");
    return;
  }

  loading.value = true;
  try {
    const payload = {
      username: generateUsername(formData.value.email),
      email: formData.value.email,
      password: formData.value.password,
      full_name: formData.value.name,
      role: formData.value.role,
      security_pin: formData.value.securityPin,
    };

    await apiClient.post("/auth/register-internal/", payload);

    toast.success(`Akun ${formData.value.role.toUpperCase()} baru berhasil didaftarkan! Username: ${payload.username}`);

    formData.value = { name: "", email: "", password: "", securityPin: "", role: "kasir" };
    emailTouched.value = false;
  } catch (error) {
    console.error("Internal Register Error:", error);
    const data = error.response?.data;
    const firstError = data && typeof data === "object"
      ? Object.values(data)[0]?.[0] || data.message
      : null;
    toast.error(firstError || "Gagal mendaftarkan staff. Periksa koneksi backend.");
  } finally {
    loading.value = false;
  }
};
</script>