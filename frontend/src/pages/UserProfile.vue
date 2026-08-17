<template>
  <div class="max-w-4xl mx-auto p-4 sm:p-6 text-white box-border space-y-6 sm:space-y-8">

    <!-- 👤 HEADER PROFIL -->
    <div>
      <div class="flex items-center gap-2 mb-2">
        <span class="w-1 h-1 rounded-full bg-red-600"></span>
        <p class="text-white/30 text-[10px] font-oswald uppercase tracking-[0.25em]">Masashimura · Akun</p>
      </div>
      <h1 class="font-oswald text-3xl sm:text-4xl uppercase tracking-tighter text-white">
        My Profile
      </h1>
      <p class="text-white/40 text-xs sm:text-sm font-light mt-1">
        Kelola kredensial login dan keamanan akun operasional kamu
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-5 sm:gap-6 items-start">

      <!-- CARD INFORMASI AKUN -->
      <div class="md:col-span-1 bg-[#0a0a0a] border border-white/5 rounded-2xl p-6 text-center space-y-4 shadow-xl md:sticky md:top-6">
        <div class="w-20 h-20 rounded-full bg-red-600/10 border-2 border-red-600/20 flex items-center justify-center text-3xl font-bold text-red-500 mx-auto font-oswald select-none">
          {{ userInitial }}
        </div>
        <div>
          <h3 class="font-bold text-lg text-white/90 truncate">{{ auth.user?.name || 'Staff Masashimura' }}</h3>
          <p class="text-xs text-white/40 font-mono mt-0.5 truncate">{{ auth.user?.email }}</p>
        </div>
        <div class="pt-3 border-t border-white/5 flex justify-center">
          <span
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider font-mono"
            :class="roleStyle.badge"
          >
            <component :is="roleStyle.icon" :size="11" />
            {{ userRole }}
          </span>
        </div>

        <!-- Quick meta -->
        <div class="pt-3 border-t border-white/5 text-left space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-[10px] text-white/30 uppercase tracking-wider">Username</span>
            <span class="text-xs text-white/60 font-mono truncate max-w-[110px]">{{ auth.user?.username || '—' }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-[10px] text-white/30 uppercase tracking-wider">Status</span>
            <span class="inline-flex items-center gap-1 text-xs text-emerald-400">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Aktif
            </span>
          </div>
        </div>
      </div>

      <!-- FORM UPDATE DATA KREDENSIAL -->
      <div class="md:col-span-2 bg-[#0a0a0a] border border-white/5 rounded-2xl p-5 sm:p-8 shadow-2xl shadow-black/30">

        <form @submit.prevent="handleUpdateProfile" class="space-y-7">

          <!-- ── Section: Informasi Akun ───────────────────────────────── -->
          <section class="space-y-5">
            <div class="flex items-center gap-2 pb-3 border-b border-white/5">
              <IdCard :size="14" class="text-red-500" />
              <h2 class="font-oswald text-sm uppercase tracking-wider text-white/80">Informasi Akun</h2>
            </div>

            <!-- Email (Read-Only) -->
            <div class="space-y-1.5">
              <label class="text-[10px] uppercase font-bold tracking-wider text-white/40">Alamat Email</label>
              <div class="relative">
                <input
                  :value="auth.user?.email"
                  type="email"
                  disabled
                  readonly
                  class="w-full bg-white/[0.02] border border-white/5 rounded-xl py-3.5 pl-4 pr-12 text-sm font-mono text-white/40 cursor-not-allowed"
                />
                <Lock :size="14" class="absolute right-4 top-1/2 -translate-y-1/2 text-white/20" />
              </div>
              <p class="text-[11px] text-white/25 italic pt-0.5">
                Email terkunci dan tidak dapat diubah. Hubungi owner jika perlu mengganti email akun kamu.
              </p>
            </div>

            <!-- Username -->
            <div class="space-y-1.5">
              <label for="profile-username" class="text-[10px] uppercase font-bold tracking-wider text-white/40">
                Username
              </label>
              <div class="relative">
                <UserRound :size="14" class="absolute left-4 top-1/2 -translate-y-1/2 text-white/25" />
                <input
                  id="profile-username"
                  v-model="profileForm.username"
                  type="text"
                  required
                  :disabled="isSaving"
                  placeholder="Masukkan username baru kamu..."
                  class="w-full bg-white/5 border border-white/10 rounded-xl py-3.5 pl-11 pr-4 text-sm focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600/30 font-mono transition text-white disabled:opacity-50"
                />
              </div>
            </div>
          </section>

          <!-- ── Section: Keamanan Password ────────────────────────────── -->
          <section class="space-y-5">
            <div class="flex items-center gap-2 pb-3 border-b border-white/5">
              <ShieldCheck :size="14" class="text-red-500" />
              <h2 class="font-oswald text-sm uppercase tracking-wider text-white/80">Keamanan Password</h2>
              <span class="text-[10px] text-white/25 italic ml-auto">Opsional</span>
            </div>

            <p class="text-[11px] text-white/30 -mt-1">
              Isi kolom di bawah hanya jika kamu ingin mengganti password akun operasional.
            </p>

            <!-- Password Baru -->
            <div class="space-y-1.5">
              <label for="profile-new-password" class="text-[10px] uppercase font-bold tracking-wider text-white/40">
                Password Baru
              </label>
              <div class="relative">
                <Lock :size="14" class="absolute left-4 top-1/2 -translate-y-1/2 text-white/25" />
                <input
                  id="profile-new-password"
                  v-model="profileForm.newPassword"
                  :type="showNewPassword ? 'text' : 'password'"
                  :disabled="isSaving"
                  placeholder="Masukkan password baru jika ingin diganti..."
                  class="w-full bg-white/5 border border-white/10 rounded-xl py-3.5 pl-11 pr-12 text-sm focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600/30 font-mono transition text-white disabled:opacity-50"
                />
                <button
                  type="button"
                  tabindex="-1"
                  @click="showNewPassword = !showNewPassword"
                  class="absolute right-4 top-1/2 -translate-y-1/2 text-white/40 hover:text-white transition-colors"
                >
                  <component :is="showNewPassword ? EyeOff : Eye" :size="16" />
                </button>
              </div>

              <!-- Strength meter -->
              <div v-if="profileForm.newPassword" class="flex items-center gap-2 pt-1">
                <div class="flex gap-1 flex-1">
                  <span
                    v-for="i in 4"
                    :key="i"
                    class="h-1 flex-1 rounded-full transition-colors"
                    :class="i <= passwordStrength.score ? passwordStrength.color : 'bg-white/8'"
                  ></span>
                </div>
                <span class="text-[10px] uppercase tracking-wider shrink-0" :class="passwordStrength.textColor">
                  {{ passwordStrength.label }}
                </span>
              </div>
            </div>

            <!-- Konfirmasi Password -->
            <div class="space-y-1.5">
              <label for="profile-confirm-password" class="text-[10px] uppercase font-bold tracking-wider text-white/40">
                Konfirmasi Password Baru
              </label>
              <div class="relative">
                <Lock :size="14" class="absolute left-4 top-1/2 -translate-y-1/2 text-white/25" />
                <input
                  id="profile-confirm-password"
                  v-model="profileForm.confirmPassword"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  :disabled="isSaving || !profileForm.newPassword"
                  placeholder="Ulangi password baru kamu..."
                  :class="[
                    'w-full bg-white/5 border rounded-xl py-3.5 pl-11 pr-12 text-sm focus:outline-none font-mono transition text-white disabled:opacity-50',
                    confirmMismatch
                      ? 'border-red-500/60 focus:border-red-500 focus:ring-1 focus:ring-red-500/30'
                      : 'border-white/10 focus:border-red-600 focus:ring-1 focus:ring-red-600/30'
                  ]"
                />
                <button
                  type="button"
                  tabindex="-1"
                  @click="showConfirmPassword = !showConfirmPassword"
                  class="absolute right-4 top-1/2 -translate-y-1/2 text-white/40 hover:text-white transition-colors"
                >
                  <component :is="showConfirmPassword ? EyeOff : Eye" :size="16" />
                </button>
              </div>
              <p v-if="confirmMismatch" class="text-red-400/80 text-[11px] pl-1">
                Konfirmasi password tidak cocok
              </p>
              <p v-else-if="profileForm.newPassword && profileForm.confirmPassword" class="flex items-center gap-1 text-emerald-400/80 text-[11px] pl-1">
                <CheckCircle2 :size="12" /> Password cocok
              </p>
            </div>
          </section>

          <!-- Tombol Submit -->
          <div class="flex justify-end pt-2 border-t border-white/5">
            <button
              type="submit"
              :disabled="isSaving || !canSubmit"
              class="w-full sm:w-fit flex items-center justify-center gap-2 bg-red-600 hover:bg-red-500 text-white font-oswald uppercase px-8 py-3.5 rounded-xl text-xs font-bold tracking-widest transition disabled:opacity-40 disabled:hover:bg-red-600 cursor-pointer disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400"
            >
              <span
                v-if="isSaving"
                class="animate-spin inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full"
              />
              <Save v-else :size="14" />
              {{ isSaving ? 'Menyimpan...' : 'Simpan Kredensial Baru' }}
            </button>
          </div>

        </form>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useAuthStore } from "@/stores/auth";
import {
  Eye, EyeOff, Lock, UserRound, IdCard, ShieldCheck,
  Save, CheckCircle2, Crown, UserCog, ChefHat,
} from "lucide-vue-next";
import { toast } from "vue-sonner";
import apiClient from "@/api/client";

const auth = useAuthStore();
const isSaving = ref(false);

const showNewPassword = ref(false);
const showConfirmPassword = ref(false);

const profileForm = ref({
  username: "",
  newPassword: "",
  confirmPassword: "",
});

const userInitial = computed(() =>
  auth.user?.name ? auth.user.name.trim().charAt(0).toUpperCase() : "?"
);

const userRole = computed(() => auth.user?.role?.toLowerCase() || "kasir");

const roleStyle = computed(() => {
  const map = {
    owner: { badge: "bg-amber-500/10 text-amber-400 border border-amber-500/20", icon: Crown },
    admin: { badge: "bg-blue-500/10 text-blue-400 border border-blue-500/20", icon: UserCog },
    kasir: { badge: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20", icon: ChefHat },
  };
  return map[userRole.value] || map.kasir;
});

// ── Validation ────────────────────────────────────────────────────────────
const confirmMismatch = computed(() =>
  profileForm.value.newPassword &&
  profileForm.value.confirmPassword &&
  profileForm.value.newPassword !== profileForm.value.confirmPassword
);

const passwordStrength = computed(() => {
  const p = profileForm.value.newPassword;
  let score = 0;
  if (p.length >= 6) score++;
  if (/[A-Z]/.test(p) && /[a-z]/.test(p)) score++;
  if (/\d/.test(p)) score++;
  if (/[^A-Za-z0-9]/.test(p) && p.length >= 10) score++;

  const levels = [
    { label: "Lemah", color: "bg-red-500", textColor: "text-red-400" },
    { label: "Lemah", color: "bg-red-500", textColor: "text-red-400" },
    { label: "Cukup", color: "bg-amber-500", textColor: "text-amber-400" },
    { label: "Kuat", color: "bg-emerald-500", textColor: "text-emerald-400" },
    { label: "Sangat Kuat", color: "bg-emerald-500", textColor: "text-emerald-400" },
  ];
  return { score, ...levels[score] };
});

const canSubmit = computed(() => {
  if (!profileForm.value.username.trim()) return false;
  if (profileForm.value.newPassword) {
    if (profileForm.value.newPassword.length < 6) return false;
    if (profileForm.value.newPassword !== profileForm.value.confirmPassword) return false;
  }
  return true;
});

// Load data awal username user aktif dari store/state auth bawaan
onMounted(() => {
  if (auth.user?.username) {
    profileForm.value.username = auth.user.username;
  }
});

// Aksi Update Kredensial Pengguna Ke Django DB Lokal
const handleUpdateProfile = async () => {
  if (profileForm.value.newPassword) {
    if (profileForm.value.newPassword.length < 6) {
      return toast.error("Password baru minimal harus 6 karakter!");
    }
    if (profileForm.value.newPassword !== profileForm.value.confirmPassword) {
      return toast.error("Konfirmasi password baru tidak cocok!");
    }
  }

  isSaving.value = true;
  try {
    const payload = {
      username: profileForm.value.username,
    };

    if (profileForm.value.newPassword) {
      payload.password = profileForm.value.newPassword;
    }

    // apiClient sudah membawa token & base URL yang benar (lihat @/api/client)
    const response = await apiClient.put("/auth/profile/update/", payload);

    toast.success("Kredensial profil kamu berhasil diperbarui!");

    // 🔥 Sinkronisasi State: Update data di Pinia Store & localStorage biar live-sync
    if (response.data?.user) {
      const updatedUser = {
        ...auth.user, // pertahankan token dan role lama yang sudah di-map
        username: response.data.user.username,
        name: response.data.user.name,
        email: response.data.user.email,
      };

      auth.user = updatedUser;
      localStorage.setItem("user", JSON.stringify(updatedUser));
    }

    // Bersihkan form password setelah mutasi data di DB sukses
    profileForm.value.newPassword = "";
    profileForm.value.confirmPassword = "";
  } catch (error) {
    console.error("Update Profile Error:", error);
    toast.error(
      error.response?.data?.username?.[0] ||
      error.response?.data?.non_field_errors?.[0] ||
      "Gagal memperbarui profil ke database."
    );
  } finally {
    isSaving.value = false;
  }
};
</script>