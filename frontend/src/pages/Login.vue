<template>
  <div class="login-root">

    <!-- ── PANEL KIRI (hero) ──────────────────────────────────────── -->
    <div class="hero-panel">
      <div
        class="hero-bg"
        :style="{ backgroundImage: `url(${heroImage})` }"
      />
      <div class="hero-overlay-bottom" />
      <div class="hero-overlay-side" />

      <div class="hero-content">
        <!-- Top label -->
        <div class="hero-top">
          <span class="hero-badge">
            <span class="hero-badge-dot"></span>
            Premium Quality
          </span>
        </div>

        <!-- Bottom branding -->
        <div class="hero-bottom">
          <img
            src="@/assets/masashimura-logo.png"
            alt="Masashimura"
            class="hero-logo"
            onerror="this.style.display='none'"
          />
          <h2 class="hero-tagline">Admin ERP System</h2>
          <p class="hero-desc">
            Infrastruktur manajemen internal, rekap finansial, kontrol stok, dan kasir POS terintegrasi Masashimura Bekasi.
          </p>
          <div class="hero-stats">
            <div class="hero-stat">
              <span class="stat-num">POS</span>
              <span class="stat-lbl">Kasir</span>
            </div>
            <div class="hero-stat-div"></div>
            <div class="hero-stat">
              <span class="stat-num">ERP</span>
              <span class="stat-lbl">Finansial</span>
            </div>
            <div class="hero-stat-div"></div>
            <div class="hero-stat">
              <span class="stat-num">CRM</span>
              <span class="stat-lbl">Loyalitas</span>
            </div>
          </div>
        </div>

        <p class="hero-copy">© 2026 Masashimura Corporation. All Rights Reserved.</p>
      </div>
    </div>

    <!-- ── PANEL KANAN (form) ─────────────────────────────────────── -->
    <div class="form-panel">
      <div class="form-inner">

        <!-- Header -->
        <div class="form-header">
          <p class="form-eyebrow">Masashimura · Admin ERP</p>
          <h1 class="form-title">Masuk ke Sistem</h1>
          <p class="form-subtitle">Masukkan kredensial otorisasi untuk mengakses ruang kendali.</p>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleSubmit" class="login-form">

          <div class="field">
            <label class="field-label">Username / Email Karyawan</label>
            <div class="input-wrap">
              <svg class="input-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              <input
                v-model="formData.username"
                type="text"
                required
                autocomplete="username"
                :disabled="loading"
                placeholder="username anda..."
                class="text-input"
              />
            </div>
          </div>

          <div class="field">
            <label class="field-label">Kata Sandi</label>
            <div class="input-wrap">
              <svg class="input-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
              <input
                v-model="formData.password"
                :type="showPassword ? 'text' : 'password'"
                required
                autocomplete="current-password"
                :disabled="loading"
                placeholder="••••••••"
                class="text-input pr-input"
              />
              <button type="button" class="eye-btn" @click="showPassword = !showPassword">
                <component :is="showPassword ? EyeOff : Eye" :size="15" />
              </button>
            </div>
          </div>

          <button type="submit" :disabled="loading" class="submit-btn">
            <span v-if="loading" class="btn-spinner"></span>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4M10 17l5-5-5-5M15 12H3"/></svg>
            {{ loading ? 'Memverifikasi...' : 'Masuk ke Sistem' }}
          </button>

        </form>

        <!-- Forgot password -->
        <div class="forgot-wrap">
          <button @click="openForgotModal" class="forgot-btn">
            Lupa password akun?
          </button>
        </div>

        <!-- Footer -->
        <p class="form-footer">Akses terbatas untuk staff & operator Masashimura</p>

      </div>
    </div>

    <!-- ── MODAL RESET PASSWORD ───────────────────────────────────── -->
    <div v-if="isForgotModalOpen" class="modal-overlay" @click.self="isForgotModalOpen = false">
      <div class="modal-box">

        <div class="modal-header">
          <div>
            <p class="modal-eyebrow">Keamanan Akun</p>
            <h3 class="modal-title">Reset Password</h3>
          </div>
          <button class="modal-close" @click="isForgotModalOpen = false">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>

        <p class="modal-desc">Masukkan email staff yang terdaftar, lalu tentukan password baru langsung di bawah ini.</p>

        <form @submit.prevent="handleSelfResetPassword" class="modal-form">

          <div class="field">
            <label class="field-label">Email Akun Staff</label>
            <div class="input-wrap">
              <svg class="input-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
              <input
                v-model="resetForm.email"
                type="email"
                required
                placeholder="kasir@masashimura.id"
                class="text-input"
              />
            </div>
          </div>

          <div class="field">
            <label class="field-label">Password Baru</label>
            <div class="input-wrap">
              <svg class="input-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
              <input
                v-model="resetForm.newPassword"
                :type="showResetPassword ? 'text' : 'password'"
                required
                placeholder="Minimal 6 karakter..."
                class="text-input pr-input"
              />
              <button type="button" class="eye-btn" @click="showResetPassword = !showResetPassword">
                <component :is="showResetPassword ? EyeOff : Eye" :size="15" />
              </button>
            </div>
          </div>

          <div class="modal-actions">
            <button type="submit" :disabled="isResetting" class="submit-btn">
              <span v-if="isResetting" class="btn-spinner"></span>
              {{ isResetting ? 'Memproses...' : 'Ganti Password' }}
            </button>
            <button type="button" @click="isForgotModalOpen = false" class="cancel-btn">
              Batalkan
            </button>
          </div>

        </form>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { toast } from "vue-sonner";
import { Eye, EyeOff } from "lucide-vue-next";
import axios from "axios";

const router = useRouter();
const auth   = useAuthStore();

const showPassword      = ref(false);
const showResetPassword = ref(false);
const loading           = ref(false);
const isResetting       = ref(false);
const isForgotModalOpen = ref(false);

const formData  = ref({ username: "", password: "" });
const resetForm = ref({ email: "", newPassword: "" });

const heroImage = "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?q=80&w=2080";

const openForgotModal = () => {
  resetForm.value = { email: "", newPassword: "" };
  showResetPassword.value = false;
  isForgotModalOpen.value = true;
};

const handleSubmit = async () => {
  loading.value = true;
  try {
    await auth.login({ username: formData.value.username.trim(), password: formData.value.password });
    toast.success(`Akses diberikan. Selamat datang, ${auth.user?.name || "Admin"}!`);
    if (auth.isOwner || auth.isAdmin) router.push("/admin");
    else if (auth.isKasir) router.push("/admin/orders");
    else router.push("/");
  } catch (error) {
    toast.error(error.response?.data?.detail || "Username atau password salah.");
  } finally {
    loading.value = false;
  }
};

const handleSelfResetPassword = async () => {
  if (resetForm.value.newPassword.length < 6) return toast.error("Password minimal 6 karakter!");
  isResetting.value = true;
  try {
    await axios.post("http://127.0.0.1:8000/api/auth/reset-password-instan/", {
      email: resetForm.value.email.trim(),
      new_password: resetForm.value.newPassword,
    });
    toast.success("Password berhasil diubah. Silakan login.");
    isForgotModalOpen.value = false;
  } catch (error) {
    toast.error(error.response?.data?.message || "Email tidak terdaftar atau salah ketik.");
  } finally {
    isResetting.value = false;
  }
};
</script>

<style scoped>
/* ── Root ──────────────────────────────────────────────────────────── */
.login-root {
  min-height: 100vh;
  display: flex;
  background: #050505;
  font-family: 'Inter', sans-serif;
  color: #fff;
}

/* ── Hero Panel ────────────────────────────────────────────────────── */
.hero-panel {
  display: none;
  position: relative;
  overflow: hidden;
  border-right: 1px solid rgba(255,255,255,0.05);
}
@media (min-width: 1024px) {
  .hero-panel { display: flex; width: 50%; }
}

.hero-bg {
  position: absolute; inset: 0;
  background-size: cover; background-position: center;
  transition: transform 1.2s ease;
}
.hero-panel:hover .hero-bg { transform: scale(1.04); }

.hero-overlay-bottom {
  position: absolute; inset: 0;
  background: linear-gradient(to top, #000 0%, rgba(0,0,0,0.5) 45%, rgba(0,0,0,0.15) 100%);
}
.hero-overlay-side {
  position: absolute; inset: 0;
  background: linear-gradient(to right, rgba(120,0,0,0.3) 0%, transparent 60%);
}

.hero-content {
  position: relative; z-index: 10;
  display: flex; flex-direction: column;
  justify-content: space-between;
  padding: 3rem 3.5rem;
  width: 100%; height: 100%;
}

.hero-top { }
.hero-badge {
  display: inline-flex; align-items: center; gap: 0.5rem;
  padding: 0.35rem 0.85rem;
  background: rgba(220,38,38,0.12);
  border: 1px solid rgba(220,38,38,0.25);
  border-radius: 100px;
  font-family: 'Oswald', sans-serif;
  font-size: 0.6rem; letter-spacing: 0.2em; text-transform: uppercase;
  color: #fca5a5;
}
.hero-badge-dot {
  width: 5px; height: 5px; border-radius: 50%; background: #ef4444;
  animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.4; } }

.hero-bottom { display: flex; flex-direction: column; gap: 1rem; }
.hero-logo {
  width: 220px; object-fit: contain;
  filter: drop-shadow(0 10px 30px rgba(0,0,0,0.8));
  user-select: none;
}
.hero-tagline {
  font-family: 'Oswald', sans-serif;
  font-size: 1.1rem; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.2em;
  color: rgba(255,255,255,0.7); margin: 0;
}
.hero-desc {
  font-size: 0.78rem; color: rgba(255,255,255,0.4);
  line-height: 1.7; margin: 0; max-width: 340px;
}
.hero-stats {
  display: flex; align-items: center; gap: 1.5rem;
  margin-top: 0.5rem;
}
.hero-stat { display: flex; flex-direction: column; gap: 0.15rem; }
.stat-num {
  font-family: 'Oswald', sans-serif; font-size: 1rem;
  font-weight: 600; letter-spacing: 0.08em; color: #fff;
}
.stat-lbl { font-size: 0.6rem; color: rgba(255,255,255,0.3); letter-spacing: 0.1em; text-transform: uppercase; }
.hero-stat-div { width: 1px; height: 28px; background: rgba(255,255,255,0.1); }

.hero-copy { font-size: 0.62rem; color: rgba(255,255,255,0.2); font-family: monospace; }

/* ── Form Panel ────────────────────────────────────────────────────── */
.form-panel {
  flex: 1;
  display: flex; align-items: center; justify-content: center;
  padding: 3rem 1.5rem;
  background: linear-gradient(160deg, #0d0d0d 0%, #050505 100%);
}
.form-inner {
  width: 100%; max-width: 380px;
  display: flex; flex-direction: column; gap: 1.75rem;
}

.form-header { display: flex; flex-direction: column; gap: 0.5rem; }
.form-eyebrow {
  font-family: 'Oswald', sans-serif; font-size: 0.6rem;
  letter-spacing: 0.2em; text-transform: uppercase; color: #dc2626;
}
.form-title {
  font-family: 'Oswald', sans-serif; font-size: 2rem;
  font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em;
  margin: 0; color: #fff;
}
.form-subtitle { font-size: 0.75rem; color: rgba(255,255,255,0.35); line-height: 1.6; }

/* ── Form fields ───────────────────────────────────────────────────── */
.login-form { display: flex; flex-direction: column; gap: 1rem; }
.modal-form { display: flex; flex-direction: column; gap: 1rem; }

.field { display: flex; flex-direction: column; gap: 0.4rem; }
.field-label {
  font-family: 'Oswald', sans-serif; font-size: 0.58rem;
  letter-spacing: 0.15em; text-transform: uppercase;
  color: rgba(255,255,255,0.3);
}

.input-wrap { position: relative; display: flex; align-items: center; }
.input-icon {
  position: absolute; left: 0.9rem;
  color: rgba(255,255,255,0.2); pointer-events: none; flex-shrink: 0;
}
.text-input {
  width: 100%; background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px; padding: 0.8rem 1rem 0.8rem 2.5rem;
  color: #fff; font-size: 0.85rem;
  font-family: 'Inter', monospace; outline: none;
  transition: border-color 0.15s, background 0.15s;
  -webkit-appearance: none;
}
.text-input::placeholder { color: rgba(255,255,255,0.15); }
.text-input:focus { border-color: rgba(220,38,38,0.5); background: rgba(255,255,255,0.06); }
.text-input:disabled { opacity: 0.45; cursor: not-allowed; }
.pr-input { padding-right: 2.75rem; }

.eye-btn {
  position: absolute; right: 0.85rem;
  background: none; border: none; padding: 0;
  color: rgba(255,255,255,0.25); cursor: pointer;
  transition: color 0.15s; display: flex; align-items: center;
}
.eye-btn:hover { color: rgba(255,255,255,0.7); }

/* ── Submit btn ────────────────────────────────────────────────────── */
.submit-btn {
  width: 100%; display: flex; align-items: center; justify-content: center; gap: 0.5rem;
  padding: 0.9rem; border-radius: 12px; border: none;
  background: #dc2626; color: #fff;
  font-family: 'Oswald', sans-serif; font-size: 0.78rem;
  letter-spacing: 0.12em; text-transform: uppercase;
  cursor: pointer; transition: background 0.15s, opacity 0.15s;
  box-shadow: 0 4px 20px rgba(220,38,38,0.2);
  margin-top: 0.25rem;
}
.submit-btn:hover:not(:disabled) { background: #b91c1c; }
.submit-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-spinner {
  width: 15px; height: 15px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff; border-radius: 50%;
  animation: spin 0.75s linear infinite; flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Forgot ────────────────────────────────────────────────────────── */
.forgot-wrap { text-align: center; }
.forgot-btn {
  background: none; border: none;
  font-size: 0.72rem; color: rgba(255,255,255,0.25);
  cursor: pointer; transition: color 0.15s;
  text-decoration: underline; text-underline-offset: 3px;
  text-decoration-color: rgba(255,255,255,0.1);
}
.forgot-btn:hover { color: #fca5a5; text-decoration-color: rgba(220,38,38,0.4); }

.form-footer {
  text-align: center; font-size: 0.65rem;
  color: rgba(255,255,255,0.15); margin: 0;
  font-family: monospace; letter-spacing: 0.05em;
}

/* ── Modal ─────────────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed; inset: 0; z-index: 50;
  background: rgba(0,0,0,0.8); backdrop-filter: blur(6px);
  display: flex; align-items: center; justify-content: center;
  padding: 1rem;
  animation: fadeIn 0.18s ease;
}
@keyframes fadeIn { from { opacity:0; } to { opacity:1; } }

.modal-box {
  background: #0f0f0f;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 20px;
  width: 100%; max-width: 420px;
  padding: 1.75rem;
  display: flex; flex-direction: column; gap: 1.25rem;
  box-shadow: 0 20px 60px rgba(0,0,0,0.6);
  animation: slideUp 0.2s ease;
}
@keyframes slideUp { from { transform: translateY(12px); opacity:0; } to { transform: translateY(0); opacity:1; } }

.modal-header {
  display: flex; align-items: flex-start; justify-content: space-between;
}
.modal-eyebrow {
  font-family: 'Oswald', sans-serif; font-size: 0.58rem;
  letter-spacing: 0.18em; text-transform: uppercase;
  color: #dc2626; margin: 0 0 0.25rem;
}
.modal-title {
  font-family: 'Oswald', sans-serif; font-size: 1.15rem;
  font-weight: 500; text-transform: uppercase; letter-spacing: 0.06em; margin: 0;
}
.modal-close {
  width: 30px; height: 30px; border-radius: 8px;
  background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.4); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s; flex-shrink: 0;
}
.modal-close:hover { background: rgba(255,255,255,0.1); color: #fff; }

.modal-desc { font-size: 0.74rem; color: rgba(255,255,255,0.35); line-height: 1.65; margin: 0; }

.modal-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; margin-top: 0.25rem; }
.cancel-btn {
  padding: 0.85rem; border-radius: 12px;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.45);
  font-family: 'Oswald', sans-serif; font-size: 0.72rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  cursor: pointer; transition: all 0.15s;
}
.cancel-btn:hover { background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.8); }

/* ── Mobile: show minimal branding strip ──────────────────────────── */
@media (max-width: 1023px) {
  .form-panel {
    background:
      linear-gradient(160deg, #0d0d0d 0%, #050505 100%);
    min-height: 100vh;
  }
  .form-inner { max-width: 420px; }
}
</style>