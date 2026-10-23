<template>
  <div class="adm-page adm-page--form">

    <header class="adm-header">
      <div>
        <p class="adm-eyebrow">Masashimura · Akun</p>
        <h1 class="adm-title">My Profile</h1>
        <p class="adm-sub">Kelola kredensial login dan keamanan akun operasional kamu.</p>
      </div>
    </header>

    <div class="up-grid">

      <!-- Ringkasan akun -->
      <aside class="adm-card up-summary">
        <div class="up-avatar" aria-hidden="true">{{ userInitial }}</div>
        <div class="up-who">
          <h2 class="adm-card-title adm-truncate">{{ auth.user?.name || 'Staff Masashimura' }}</h2>
          <p class="adm-hint adm-mono adm-truncate">{{ auth.user?.email }}</p>
        </div>

        <span class="adm-badge up-role" :class="roleStyle.badge">
          <component :is="roleStyle.icon" :size="12" />
          {{ userRole }}
        </span>

        <dl class="up-facts">
          <div class="up-fact">
            <dt>Username</dt>
            <dd class="adm-mono adm-truncate">{{ auth.user?.username || '—' }}</dd>
          </div>
          <div class="up-fact">
            <dt>Status</dt>
            <dd class="up-active"><span class="adm-dot"></span> Aktif</dd>
          </div>
        </dl>
      </aside>

      <!-- Form kredensial -->
      <form class="adm-card up-form" @submit.prevent="handleUpdateProfile">

        <section class="up-section">
          <div class="up-section-head">
            <IdCard :size="15" class="up-section-icon" />
            <h2 class="adm-card-title">Informasi Akun</h2>
          </div>

          <div class="adm-field">
            <label class="adm-label" for="profile-email">Alamat Email</label>
            <div class="up-affix">
              <input id="profile-email" :value="auth.user?.email" type="email" disabled readonly class="adm-input adm-input--mono up-pr" />
              <Lock :size="14" class="up-icon up-icon--end" />
            </div>
            <p class="adm-hint">Email terkunci dan tidak dapat diubah. Hubungi owner jika perlu mengganti email akun kamu.</p>
          </div>

          <div class="adm-field">
            <label class="adm-label" for="profile-username">Username</label>
            <div class="up-affix">
              <UserRound :size="14" class="up-icon" />
              <input
                id="profile-username"
                v-model="profileForm.username"
                type="text"
                required
                :disabled="isSaving"
                placeholder="Masukkan username baru kamu..."
                class="adm-input adm-input--mono up-pl"
              />
            </div>
          </div>
        </section>

        <section class="up-section">
          <div class="up-section-head">
            <ShieldCheck :size="15" class="up-section-icon" />
            <h2 class="adm-card-title">Keamanan Password</h2>
            <span class="adm-opt up-optional">Opsional</span>
          </div>

          <p class="adm-hint">Isi kolom di bawah hanya jika kamu ingin mengganti password akun operasional.</p>

          <!-- Toggle metode verifikasi -->
          <div v-if="profileForm.newPassword" class="adm-seg adm-seg--fill" role="group" aria-label="Metode verifikasi">
            <button type="button" class="adm-seg-btn" :aria-pressed="verifyMethod === 'password'" @click="verifyMethod = 'password'">
              Password Lama
            </button>
            <button type="button" class="adm-seg-btn" :aria-pressed="verifyMethod === 'pin'" @click="verifyMethod = 'pin'">
              PIN Keamanan
            </button>
          </div>

          <!-- Password Saat Ini -->
          <div v-if="verifyMethod === 'password'" class="adm-field">
            <label class="adm-label" for="profile-current-password">Password Saat Ini</label>
            <div class="up-affix">
              <Lock :size="14" class="up-icon" />
              <input
                id="profile-current-password"
                v-model="profileForm.currentPassword"
                :type="showCurrentPassword ? 'text' : 'password'"
                :disabled="isSaving"
                placeholder="Wajib diisi kalau mau ganti password..."
                class="adm-input adm-input--mono up-pl up-pr"
              />
              <button type="button" tabindex="-1" class="adm-icon-btn up-eye" :aria-label="showCurrentPassword ? 'Sembunyikan password' : 'Tampilkan password'" @click="showCurrentPassword = !showCurrentPassword">
                <component :is="showCurrentPassword ? EyeOff : Eye" :size="16" />
              </button>
            </div>
          </div>

          <!-- PIN Keamanan -->
          <div v-else class="adm-field">
            <label class="adm-label" for="profile-pin">PIN Keamanan</label>
            <div class="up-affix">
              <Lock :size="14" class="up-icon" />
              <input
                id="profile-pin"
                v-model="profileForm.securityPin"
                type="text" inputmode="numeric" maxlength="6"
                :disabled="isSaving"
                placeholder="6 digit PIN kamu..."
                class="adm-input adm-input--mono up-pl up-pin"
                @input="profileForm.securityPin = profileForm.securityPin.replace(/\D/g, '').slice(0, 6)"
              />
            </div>
          </div>

          <!-- Password Baru -->
          <div class="adm-field">
            <label class="adm-label" for="profile-new-password">Password Baru</label>
            <div class="up-affix">
              <Lock :size="14" class="up-icon" />
              <input
                id="profile-new-password"
                v-model="profileForm.newPassword"
                :type="showNewPassword ? 'text' : 'password'"
                :disabled="isSaving"
                placeholder="Masukkan password baru jika ingin diganti..."
                class="adm-input adm-input--mono up-pl up-pr"
              />
              <button type="button" tabindex="-1" class="adm-icon-btn up-eye" :aria-label="showNewPassword ? 'Sembunyikan password' : 'Tampilkan password'" @click="showNewPassword = !showNewPassword">
                <component :is="showNewPassword ? EyeOff : Eye" :size="16" />
              </button>
            </div>

            <div v-if="profileForm.newPassword" class="up-strength" :class="passwordStrength.tone">
              <div class="up-strength-bars">
                <span v-for="i in 4" :key="i" :class="{ on: i <= passwordStrength.score }"></span>
              </div>
              <span class="up-strength-label">{{ passwordStrength.label }}</span>
            </div>
          </div>

          <!-- Konfirmasi Password -->
          <div class="adm-field">
            <label class="adm-label" for="profile-confirm-password">Konfirmasi Password Baru</label>
            <div class="up-affix">
              <Lock :size="14" class="up-icon" />
              <input
                id="profile-confirm-password"
                v-model="profileForm.confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                :disabled="isSaving || !profileForm.newPassword"
                placeholder="Ulangi password baru kamu..."
                class="adm-input adm-input--mono up-pl up-pr"
                :class="{ 'is-invalid': confirmMismatch }"
              />
              <button type="button" tabindex="-1" class="adm-icon-btn up-eye" :aria-label="showConfirmPassword ? 'Sembunyikan password' : 'Tampilkan password'" @click="showConfirmPassword = !showConfirmPassword">
                <component :is="showConfirmPassword ? EyeOff : Eye" :size="16" />
              </button>
            </div>
            <p v-if="confirmMismatch" class="adm-error">Konfirmasi password tidak cocok</p>
            <p v-else-if="profileForm.newPassword && profileForm.confirmPassword" class="up-match">
              <CheckCircle2 :size="13" /> Password cocok
            </p>
          </div>
        </section>

        <div class="up-actions">
          <button type="submit" class="adm-btn adm-btn--primary" :disabled="isSaving || !canSubmit">
            <span v-if="isSaving" class="adm-spinner"></span>
            <Save v-else :size="14" />
            {{ isSaving ? 'Menyimpan...' : 'Simpan Kredensial Baru' }}
          </button>
        </div>

      </form>
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

const showCurrentPassword = ref(false);
const showNewPassword = ref(false);
const showConfirmPassword = ref(false);
const verifyMethod = ref("password"); // "password" | "pin"

const profileForm = ref({
  username: "",
  currentPassword: "",
  securityPin: "",
  newPassword: "",
  confirmPassword: "",
});

const userInitial = computed(() =>
  auth.user?.name ? auth.user.name.trim().charAt(0).toUpperCase() : "?"
);

const userRole = computed(() => auth.user?.role?.toLowerCase() || "kasir");

const roleStyle = computed(() => {
  const map = {
    owner: { badge: "adm-badge--amber", icon: Crown },
    admin: { badge: "adm-badge--blue", icon: UserCog },
    kasir: { badge: "adm-badge--green", icon: ChefHat },
  };
  return map[userRole.value] || map.kasir;
});

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
    { label: "Lemah", tone: "is-weak" },
    { label: "Lemah", tone: "is-weak" },
    { label: "Cukup", tone: "is-mid" },
    { label: "Kuat", tone: "is-strong" },
    { label: "Sangat Kuat", tone: "is-strong" },
  ];
  return { score, ...levels[score] };
});

// Verifikasi ganti password sekarang OR: password lama ATAU PIN — bukan
// dua-duanya wajib. Salah satu cukup, karena dua-duanya sama-sama cuma
// diketahui pemilik akun.
const canSubmit = computed(() => {
  if (!profileForm.value.username.trim()) return false;
  if (profileForm.value.newPassword) {
    const hasVerification = verifyMethod.value === "password"
      ? !!profileForm.value.currentPassword
      : /^\d{6}$/.test(profileForm.value.securityPin);
    if (!hasVerification) return false;
    if (profileForm.value.newPassword.length < 6) return false;
    if (profileForm.value.newPassword !== profileForm.value.confirmPassword) return false;
  }
  return true;
});

onMounted(() => {
  if (auth.user?.username) {
    profileForm.value.username = auth.user.username;
  }
});

const handleUpdateProfile = async () => {
  if (profileForm.value.newPassword) {
    const hasVerification = verifyMethod.value === "password"
      ? !!profileForm.value.currentPassword
      : /^\d{6}$/.test(profileForm.value.securityPin);
    if (!hasVerification) {
      return toast.error(
        verifyMethod.value === "password"
          ? "Masukkan password saat ini buat konfirmasi ganti password!"
          : "PIN harus 6 digit angka!"
      );
    }
    if (profileForm.value.newPassword.length < 6) {
      return toast.error("Password baru minimal harus 6 karakter!");
    }
    if (profileForm.value.newPassword !== profileForm.value.confirmPassword) {
      return toast.error("Konfirmasi password baru tidak cocok!");
    }
  }

  isSaving.value = true;
  try {
    const response = await apiClient.put("/auth/profile/update/", {
      username: profileForm.value.username,
    });

    if (profileForm.value.newPassword) {
      const payload = { new_password: profileForm.value.newPassword };
      if (verifyMethod.value === "password") payload.old_password = profileForm.value.currentPassword;
      else payload.security_pin = profileForm.value.securityPin;

      await apiClient.post("/auth/profile/change-password/", payload);
    }

    toast.success("Kredensial profil kamu berhasil diperbarui!");

    if (response.data?.user) {
      const updatedUser = {
        ...auth.user,
        username: response.data.user.username,
        name: response.data.user.name,
        email: response.data.user.email,
      };
      auth.user = updatedUser;
      localStorage.setItem("user", JSON.stringify(updatedUser));
    }

    profileForm.value.currentPassword = "";
    profileForm.value.securityPin = "";
    profileForm.value.newPassword = "";
    profileForm.value.confirmPassword = "";
  } catch (error) {
    console.error("Update Profile Error:", error);
    toast.error(
      error.response?.data?.non_field_errors?.[0] ||
      error.response?.data?.username?.[0] ||
      "Gagal memperbarui profil ke database."
    );
  } finally {
    isSaving.value = false;
  }
};
</script>

<style scoped>
.up-grid { display: grid; grid-template-columns: minmax(0, 1fr); gap: 1.25rem; align-items: start; }
@media (min-width: 768px) { .up-grid { grid-template-columns: minmax(0, 17rem) minmax(0, 1fr); } .up-summary { position: sticky; top: 1.5rem; } }

.up-summary { display: flex; flex-direction: column; align-items: center; gap: 1rem; padding: 1.5rem 1.25rem; text-align: center; }
.up-avatar {
  display: flex; align-items: center; justify-content: center; width: 80px; height: 80px; border-radius: 50%;
  background: var(--tint-accent); border: 2px solid var(--line-accent); color: var(--accent-text);
  font-family: var(--font-display); font-size: 1.875rem; user-select: none;
}
.up-who { width: 100%; min-width: 0; }
.up-who .adm-hint { margin-top: 0.2rem; }
.up-role { text-transform: uppercase; letter-spacing: 0.06em; }

.up-facts { width: 100%; margin: 0; padding-top: 1rem; border-top: 1px solid var(--border); display: flex; flex-direction: column; gap: 0.6rem; text-align: left; }
.up-fact { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; }
.up-fact dt { font-size: 0.8125rem; color: var(--text-faint); }
.up-fact dd { margin: 0; max-width: 8rem; font-size: 0.8125rem; color: var(--text-2); }
.up-active { display: inline-flex; align-items: center; gap: 0.4rem; color: var(--green-soft) !important; }

.up-form { display: flex; flex-direction: column; gap: 1.5rem; padding: 1.25rem; }
@media (min-width: 640px) { .up-form { padding: 1.75rem; } }
.up-section { display: flex; flex-direction: column; gap: 1rem; }
.up-section-head { display: flex; align-items: center; gap: 0.5rem; padding-bottom: 0.75rem; border-bottom: 1px solid var(--border); }
.up-section-icon { color: var(--accent-text); }
.up-optional { margin-left: auto; font-size: 0.8125rem; }

.up-affix { position: relative; display: flex; align-items: center; }
.up-icon { position: absolute; left: 0.85rem; color: var(--text-faint); pointer-events: none; }
.up-icon--end { left: auto; right: 0.85rem; }
.up-pl { padding-left: 2.5rem; }
.up-pr { padding-right: 2.75rem; }
.up-eye { position: absolute; right: 0.3rem; }
.up-pin { letter-spacing: 0.3em; }

.up-strength { display: flex; align-items: center; gap: 0.6rem; padding-top: 0.25rem; --lvl: var(--red-soft); }
.up-strength.is-mid { --lvl: var(--amber-soft); }
.up-strength.is-strong { --lvl: var(--green-soft); }
.up-strength-bars { display: flex; flex: 1; gap: 4px; }
.up-strength-bars span { flex: 1; height: 4px; border-radius: 99px; background: rgb(var(--ink) / 0.1); transition: background 0.15s; }
.up-strength-bars span.on { background: var(--lvl); }
.up-strength-label { flex-shrink: 0; font-size: 0.75rem; font-weight: 600; color: var(--lvl); }
.up-match { display: flex; align-items: center; gap: 0.35rem; margin: 0; font-size: 0.8125rem; color: var(--green-soft); }

.up-actions { display: flex; justify-content: flex-end; padding-top: 1rem; border-top: 1px solid var(--border); }
@media (max-width: 640px) { .up-actions .adm-btn { width: 100%; } }
</style>
