<template>
  <div class="adm-page adm-page--narrow">
    <header class="adm-header">
      <div>
        <p class="adm-eyebrow">Masashimura · Admin</p>
        <h1 class="adm-title">Kelola Staff</h1>
        <p class="adm-sub">Reset PIN keamanan staff yang lupa PIN-nya.</p>
      </div>
      <div class="adm-header-actions">
        <button type="button" class="adm-btn adm-btn--ghost" :disabled="loading" @click="fetchStaff">
          <RefreshCw :size="14" :class="{ 'staff-spin': loading }" /> Muat Ulang
        </button>
      </div>
    </header>

    <!-- Cari: hanya muncul kalau staff sudah banyak -->
    <div v-if="!loading && !loadError && staffList.length > 5" class="adm-toolbar">
      <div class="adm-search">
        <Search :size="15" class="adm-search-icon" />
        <input v-model="query" type="search" class="adm-input" placeholder="Cari nama, username, atau email…" aria-label="Cari staff" />
      </div>
    </div>

    <section class="adm-card adm-card--flush" aria-live="polite">
      <!-- Loading -->
      <div v-if="loading" class="staff-list" aria-busy="true">
        <div v-for="n in 4" :key="n" class="staff-row">
          <span class="adm-skel staff-avatar-skel"></span>
          <div class="staff-info"><span class="adm-skel" style="height: 14px; width: 55%"></span><span class="adm-skel" style="height: 11px; width: 80%; margin-top: 8px"></span></div>
        </div>
      </div>

      <!-- Error -->
      <div v-else-if="loadError" class="adm-empty">
        <div class="adm-empty-icon"><AlertTriangle :size="22" /></div>
        <p class="adm-empty-title">Gagal memuat daftar staff</p>
        <p class="adm-empty-text">Periksa koneksi lalu coba lagi.</p>
        <button type="button" class="adm-btn adm-btn--primary" @click="fetchStaff">Coba Lagi</button>
      </div>

      <!-- Kosong -->
      <div v-else-if="staffList.length === 0" class="adm-empty">
        <div class="adm-empty-icon"><Users :size="22" /></div>
        <p class="adm-empty-title">Belum ada staff terdaftar</p>
        <p class="adm-empty-text">Staff baru bisa ditambahkan lewat menu "Register Staff Baru".</p>
      </div>

      <!-- Tidak ada hasil cari -->
      <div v-else-if="filtered.length === 0" class="adm-empty">
        <div class="adm-empty-icon"><Search :size="22" /></div>
        <p class="adm-empty-title">Tidak ada staff yang cocok</p>
        <button type="button" class="adm-btn adm-btn--ghost" @click="query = ''">Hapus Pencarian</button>
      </div>

      <ul v-else class="staff-list">
        <li v-for="staff in filtered" :key="staff.id" class="staff-row">
          <div class="staff-avatar" :class="`role-${roleKey(staff.role)}`" aria-hidden="true">
            {{ initials(staff) }}
          </div>

          <div class="staff-info">
            <p class="staff-name adm-truncate">{{ staff.full_name || staff.username }}</p>
            <p class="staff-meta adm-mono adm-truncate">{{ staff.username }}<template v-if="staff.email"> · {{ staff.email }}</template></p>
            <div class="staff-badges">
              <span class="adm-badge" :class="roleBadge(staff.role)">{{ staff.role }}</span>
              <span v-if="!staff.has_pin" class="adm-badge adm-badge--amber">Belum ada PIN</span>
              <span v-if="!staff.is_active" class="adm-badge adm-badge--red">Nonaktif</span>
            </div>
          </div>

          <button type="button" class="adm-btn adm-btn--soft adm-btn--sm staff-action" @click="openPinModal(staff)">
            <KeyRound :size="14" /> Reset PIN
          </button>
        </li>
      </ul>
    </section>

    <!-- Modal Reset PIN -->
    <AdminModal v-model="pinOpen" :title="`Reset PIN — ${pinTarget?.username ?? ''}`" size="sm" :persistent="submitting">
      <form id="pin-form" class="adm-field" @submit.prevent="submitNewPin">
        <p class="adm-modal-text">
          Masukkan PIN baru, lalu beritahu langsung ke staff ini secara lisan (jangan lewat chat).
        </p>
        <label class="adm-label" for="new-pin">PIN baru</label>
        <input
          id="new-pin"
          v-model="newPin"
          data-autofocus
          type="text"
          inputmode="numeric"
          autocomplete="off"
          maxlength="6"
          placeholder="••••••"
          class="adm-input adm-input--mono staff-pin"
          :aria-describedby="'pin-hint'"
          @input="newPin = newPin.replace(/\D/g, '').slice(0, 6)"
        />
        <p id="pin-hint" class="adm-hint">{{ newPin.length }}/6 digit — harus tepat 6 angka.</p>
      </form>

      <template #footer>
        <button type="button" class="adm-btn adm-btn--ghost" :disabled="submitting" @click="pinOpen = false">Batal</button>
        <button type="submit" form="pin-form" class="adm-btn adm-btn--primary" :disabled="!pinValid || submitting">
          <span v-if="submitting" class="adm-spinner"></span>
          {{ submitting ? 'Menyimpan…' : 'Simpan PIN' }}
        </button>
      </template>
    </AdminModal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { toast } from 'vue-sonner'
import { RefreshCw, Search, Users, KeyRound, AlertTriangle } from 'lucide-vue-next'
import apiClient from '@/api/client'
import AdminModal from '@/components/ui/admin/Adminmodal.vue'

const staffList = ref([])
const loading = ref(true)
const loadError = ref(false)
const query = ref('')

const pinOpen = ref(false)
const pinTarget = ref(null)
const newPin = ref('')
const submitting = ref(false)

const pinValid = computed(() => /^\d{6}$/.test(newPin.value))

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return staffList.value
  return staffList.value.filter((s) =>
    [s.full_name, s.username, s.email].some((v) => (v || '').toLowerCase().includes(q))
  )
})

const roleKey = (role) => (role || '').toLowerCase()
const roleBadge = (role) =>
  ({ owner: 'adm-badge--amber', admin: 'adm-badge--blue' }[roleKey(role)] || 'adm-badge--green')
const initials = (s) =>
  (s.full_name || s.username || '?').split(/\s+/).slice(0, 2).map((w) => w[0]).join('').toUpperCase()

const fetchStaff = async () => {
  loading.value = true
  loadError.value = false
  try {
    const res = await apiClient.get('/auth/staff/list/')
    staffList.value = res.data
  } catch (error) {
    console.error('Fetch Staff Error:', error)
    loadError.value = true
    toast.error('Gagal memuat daftar staff.')
  } finally {
    loading.value = false
  }
}

const openPinModal = (staff) => {
  pinTarget.value = staff
  newPin.value = ''
  pinOpen.value = true
}

const submitNewPin = async () => {
  if (!pinValid.value || submitting.value) return
  submitting.value = true
  try {
    await apiClient.post('/auth/staff/set-pin/', {
      user_id: pinTarget.value.id,
      new_pin: newPin.value,
    })
    toast.success(`PIN ${pinTarget.value.username} berhasil di-reset!`)
    pinTarget.value.has_pin = true
    pinOpen.value = false
  } catch (error) {
    console.error('Set PIN Error:', error)
    toast.error(error.response?.data?.detail || error.response?.data?.new_pin?.[0] || 'Gagal reset PIN.')
  } finally {
    submitting.value = false
  }
}

onMounted(fetchStaff)
</script>

<style scoped>
.staff-list { margin: 0; padding: 0; list-style: none; }
.staff-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.85rem;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border);
}
.staff-row:last-child { border-bottom: none; }

.staff-avatar, .staff-avatar-skel {
  display: flex; align-items: center; justify-content: center;
  width: 40px; height: 40px; border-radius: 50%;
}
.staff-avatar {
  font-family: var(--font-display); font-size: 0.8rem; letter-spacing: 0.04em;
  background: var(--tint-green); border: 1px solid var(--line-green); color: var(--green-soft);
}
.staff-avatar.role-owner { background: var(--tint-amber); border-color: var(--line-amber); color: var(--amber-soft); }
.staff-avatar.role-admin { background: var(--tint-blue);  border-color: var(--line-blue);  color: var(--blue-soft); }

.staff-info { min-width: 0; }
.staff-name { margin: 0; font-size: 0.875rem; font-weight: 600; color: var(--text); }
.staff-meta { margin: 0.15rem 0 0; font-size: 0.72rem; color: var(--text-dim); }
.staff-badges { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.5rem; }
.staff-badges .adm-badge { text-transform: uppercase; letter-spacing: 0.06em; font-size: 0.62rem; }

.staff-pin { font-size: 1.25rem; letter-spacing: 0.5em; text-align: center; }
.staff-spin { animation: adm-spin 0.8s linear infinite; }

@media (max-width: 520px) {
  .staff-row { grid-template-columns: auto minmax(0, 1fr); padding: 1rem; }
  .staff-action { grid-column: 1 / -1; width: 100%; }
}
</style>