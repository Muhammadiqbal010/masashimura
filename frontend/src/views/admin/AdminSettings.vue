<template>
  <div class="adm-page adm-page--form">

    <!-- ── Header ─────────────────────────────────────────────────────────── -->
    <header class="adm-header">
      <div>
        <p class="adm-eyebrow">Masashimura · Admin</p>
        <h1 class="adm-title">System Settings</h1>
        <p class="adm-sub">Konfigurasi sistem Masashimura: kontak, status toko, dan jam operasional.</p>
      </div>
    </header>

    <!-- ── Banner cache (tampil hanya jika data BUKAN dari server) ───────── -->
    <div v-if="isOffline" class="set-banner set-banner--amber" role="alert">
      <WifiOff :size="16" class="set-banner-icon" />
      <p>
        Tidak dapat terhubung ke server — menampilkan <strong>data cache lokal</strong> (mungkin tidak terbaru).
        Perubahan tidak akan tersimpan sampai koneksi ke server pulih.
      </p>
    </div>

    <!-- ── Status toko (live) ─────────────────────────────────────────────── -->
    <div class="set-banner" :class="isStoreOpen ? 'set-banner--green' : 'set-banner--red'" role="status">
      <span class="set-pulse" :class="{ 'is-open': isStoreOpen }" aria-hidden="true"></span>
      <p>
        Toko sekarang: <strong>{{ isStoreOpen ? 'BUKA' : 'TUTUP' }}</strong>
        <span v-if="form.is_open_override !== null" class="set-banner-note set-banner-note--amber">· override manual aktif</span>
        <span v-else class="set-banner-note">· mengikuti jadwal</span>
      </p>
    </div>

    <!-- ── CARD 1 — WhatsApp ──────────────────────────────────────────────── -->
    <section class="adm-card">
      <div class="adm-card-head">
        <div class="adm-card-icon tone-green"><MessageCircle :size="18" /></div>
        <div class="adm-card-head-main">
          <h2 class="adm-card-title">Nomor WhatsApp Admin</h2>
          <p class="adm-card-desc">Nomor tujuan pengiriman bukti pembayaran dari customer.</p>
        </div>
      </div>

      <div class="adm-card-body">
        <div class="adm-field">
          <div class="adm-label-row">
            <label class="adm-label" for="admin-whatsapp">Nomor WhatsApp</label>
            <span v-if="isWhatsappSaved" class="adm-badge adm-badge--green"><Check :size="11" /> Aktif</span>
          </div>
          <div class="adm-affix">
            <span class="adm-affix-pre" aria-hidden="true">+</span>
            <input
              id="admin-whatsapp"
              v-model="form.admin_whatsapp"
              type="tel"
              inputmode="numeric"
              autocomplete="off"
              class="adm-input adm-input--mono has-pre"
              placeholder="628xxxxxxxxxx"
              :aria-invalid="!!errors.whatsapp"
              aria-describedby="whatsapp-help"
              @input="onWhatsappInput"
              @blur="validateWhatsapp"
            />
          </div>
          <p v-if="errors.whatsapp" id="whatsapp-help" class="adm-error">{{ errors.whatsapp }}</p>
          <p v-else id="whatsapp-help" class="adm-hint">
            Format internasional tanpa "+", diawali kode negara 62. Contoh: <code class="set-code">6281234567890</code>
          </p>
        </div>

        <div v-if="form.admin_whatsapp" class="set-preview">
          <span class="set-preview-label">Preview link</span>
          <span class="set-preview-link adm-mono">https://wa.me/<strong>{{ form.admin_whatsapp }}</strong></span>
        </div>

        <div class="set-note">
          <Info :size="15" class="set-note-icon" />
          <p>Nomor ini digunakan saat customer checkout. Customer akan diarahkan ke WhatsApp ini untuk mengirimkan bukti pembayaran.</p>
        </div>
      </div>
    </section>

    <!-- ── CARD 2 — Override manual ───────────────────────────────────────── -->
    <section class="adm-card">
      <div class="adm-card-head">
        <div class="adm-card-icon tone-amber"><Power :size="18" /></div>
        <div class="adm-card-head-main">
          <h2 class="adm-card-title">Kontrol Manual Toko</h2>
          <p class="adm-card-desc">Override jadwal — berguna saat ada situasi mendadak.</p>
        </div>
      </div>

      <div class="adm-card-body">
        <div class="adm-field">
          <span id="override-label" class="adm-label">Status toko</span>
          <div class="set-override" role="radiogroup" aria-labelledby="override-label">
            <button
              v-for="opt in overrideOptions"
              :key="String(opt.value)"
              type="button"
              role="radio"
              class="set-override-btn"
              :class="[`is-${opt.tone}`, { 'is-active': form.is_open_override === opt.value }]"
              :aria-checked="form.is_open_override === opt.value"
              @click="requestOverride(opt.value)"
            >
              <component :is="opt.icon" :size="16" />
              <span>{{ opt.label }}</span>
            </button>
          </div>
        </div>

        <div class="adm-field">
          <label class="adm-label" for="closed-message">Pesan saat toko tutup</label>
          <textarea
            id="closed-message"
            v-model="form.closed_message"
            class="adm-input"
            rows="3"
            maxlength="240"
            placeholder="Maaf, kami sedang tidak beroperasi…"
          ></textarea>
          <p class="adm-hint">Tampil di halaman menu & checkout saat toko tutup. ({{ form.closed_message.length }}/240)</p>
        </div>

        <div v-if="form.is_open_override !== null" class="set-note set-note--amber" role="status">
          <AlertTriangle :size="15" class="set-note-icon" />
          <p>
            Override manual aktif — toko dipaksa <strong>{{ form.is_open_override ? 'BUKA' : 'TUTUP' }}</strong>.
            Pilih "Ikut Jadwal" untuk menonaktifkan. Perubahan baru berlaku setelah klik "Simpan Perubahan".
          </p>
        </div>
      </div>
    </section>

    <!-- ── CARD 3 — Jam operasional ───────────────────────────────────────── -->
    <section class="adm-card">
      <div class="adm-card-head">
        <div class="adm-card-icon tone-purple"><Clock :size="18" /></div>
        <div class="adm-card-head-main">
          <h2 class="adm-card-title">Jam Operasional</h2>
          <p class="adm-card-desc">Atur hari dan jam buka. Hari yang tidak diaktifkan dianggap libur.</p>
        </div>
        <div class="adm-card-head-actions">
          <button type="button" class="adm-btn adm-btn--ghost adm-btn--sm" :disabled="!firstOpenDay" @click="copyToAll">
            <Copy :size="13" /> Samakan semua
          </button>
        </div>
      </div>

      <ul class="hours-list">
        <li v-for="(day, idx) in DAY_OPTIONS" :key="idx" class="hours-item">
          <div class="hours-row">
            <span class="hours-day" :title="day.label">{{ day.short }}</span>

            <div class="hours-toggle">
              <button
                type="button"
                class="adm-switch"
                role="switch"
                :aria-checked="!!form.operating_hours[idx]"
                :aria-label="`${day.label} buka`"
                @click="toggleDay(idx)"
              ></button>
              <span class="hours-state" :class="{ 'is-on': form.operating_hours[idx] }">
                {{ form.operating_hours[idx] ? 'Buka' : 'Libur' }}
              </span>
            </div>

            <div v-if="form.operating_hours[idx]" class="time-fields">
              <div v-for="field in TIME_FIELDS" :key="field.key" class="time-group">
                <span class="time-label">{{ field.label }}</span>
                <div class="time-inputs">
                  <select
                    class="adm-input time-select"
                    :value="getHour(form.operating_hours[idx][field.key])"
                    :aria-label="`${day.label} jam ${field.label.toLowerCase()} (jam)`"
                    @change="setPart(idx, field.key, 'h', $event.target.value)"
                  >
                    <option v-for="h in HOURS" :key="h" :value="h">{{ h }}</option>
                  </select>
                  <span class="time-sep" aria-hidden="true">:</span>
                  <select
                    class="adm-input time-select"
                    :value="getMinute(form.operating_hours[idx][field.key])"
                    :aria-label="`${day.label} jam ${field.label.toLowerCase()} (menit)`"
                    @change="setPart(idx, field.key, 'm', $event.target.value)"
                  >
                    <option v-for="m in minuteOptions(idx, field.key)" :key="m" :value="m">{{ m }}</option>
                  </select>
                </div>
              </div>
            </div>
            <span v-else class="hours-off">Hari libur</span>
          </div>
          <p v-if="hoursErrors[idx]" class="adm-error hours-error">{{ hoursErrors[idx] }}</p>
        </li>
      </ul>
    </section>

    <!-- ── Bar simpan melayang ────────────────────────────────────────────── -->
    <div class="adm-savebar" :class="{ 'is-clean': !hasChanges }">
      <p class="adm-savebar-text" aria-live="polite">
        <span class="adm-dot"></span>
        {{ hasChanges ? 'Ada perubahan yang belum disimpan' : 'Semua perubahan sudah tersimpan' }}
      </p>
      <div class="adm-savebar-actions">
        <button v-if="hasChanges && !loading" type="button" class="adm-btn adm-btn--ghost" @click="resetForm">Batalkan</button>
        <button type="button" class="adm-btn adm-btn--primary" :disabled="loading || !hasChanges" @click="saveAll">
          <span v-if="loading" class="adm-spinner"></span>
          <Save v-else :size="15" />
          {{ loading ? 'Menyimpan…' : 'Simpan Perubahan' }}
        </button>
      </div>
    </div>

    <AdminConfirm :state="confirmState" @confirm="acceptConfirm" @cancel="cancelConfirm" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { toast } from 'vue-sonner'
import {
  MessageCircle, Power, Clock, Info, AlertTriangle, WifiOff, Check, Copy, Save,
  CalendarClock, Store, Lock,
} from 'lucide-vue-next'
import apiClient from '@/api/client'
import { useStoreSettings } from '@/composables/useStoreSettings'
import { useAdminConfirm } from '@/composables/useAdminConfirm'
import AdminConfirm from '@/components/admin/AdminConfirm.vue'

const { isStoreOpen, refetchSettings } = useStoreSettings()
const { state: confirmState, ask, accept: acceptConfirm, cancel: cancelConfirm } = useAdminConfirm()

const DAY_OPTIONS = [
  { label: 'Senin',  short: 'Sen' },
  { label: 'Selasa', short: 'Sel' },
  { label: 'Rabu',   short: 'Rab' },
  { label: 'Kamis',  short: 'Kam' },
  { label: 'Jumat',  short: 'Jum' },
  { label: 'Sabtu',  short: 'Sab' },
  { label: 'Minggu', short: 'Min' },
]
const TIME_FIELDS = [
  { key: 'open',  label: 'Buka' },
  { key: 'close', label: 'Tutup' },
]
const overrideOptions = [
  { value: null,  label: 'Ikut Jadwal', icon: CalendarClock, tone: 'blue' },
  { value: true,  label: 'Paksa Buka',  icon: Store,         tone: 'green' },
  { value: false, label: 'Paksa Tutup', icon: Lock,          tone: 'red' },
]

const HOURS   = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'))
const MINUTES = ['00', '15', '30', '45']
const WHATSAPP_REGEX = /^62[0-9]{8,13}$/ // kode negara 62 + 8-13 digit

const loading     = ref(false)
const isOffline   = ref(false) // true hanya jika data yang tampil BUKAN dari server
const errors      = ref({ whatsapp: '' })
const hoursErrors = ref({})

const defaultForm = () => ({
  admin_whatsapp:   '',
  is_open_override: null,
  closed_message:   'Maaf, kami sedang tidak beroperasi. Silakan kembali sesuai jam operasional kami.',
  operating_hours:  {},
})

const form      = ref(defaultForm())
const savedForm = ref(defaultForm())
const clone     = (v) => JSON.parse(JSON.stringify(v))

const hasChanges = computed(() => JSON.stringify(form.value) !== JSON.stringify(savedForm.value))
const isWhatsappSaved = computed(
  () => !!savedForm.value.admin_whatsapp && !errors.value.whatsapp && form.value.admin_whatsapp === savedForm.value.admin_whatsapp
)
const firstOpenDay = computed(() => {
  const idx = DAY_OPTIONS.findIndex((_, i) => form.value.operating_hours[i])
  return idx === -1 ? null : idx
})

// ── Jam ────────────────────────────────────────────────────────────
const getHour   = (t) => t?.split(':')?.[0] ?? '08'
const getMinute = (t) => t?.split(':')?.[1] ?? '00'

// Menit non-standar dari server (mis. "08:10") tetap ditampilkan, bukan dikosongkan.
const minuteOptions = (idx, field) => {
  const current = getMinute(form.value.operating_hours[idx]?.[field])
  return MINUTES.includes(current) ? MINUTES : [...MINUTES, current].sort()
}

const setPart = (idx, field, part, val) => {
  const range = form.value.operating_hours[idx]
  if (!range) return
  const h = part === 'h' ? val : getHour(range[field])
  const m = part === 'm' ? val : getMinute(range[field])
  form.value.operating_hours = {
    ...form.value.operating_hours,
    [idx]: { ...range, [field]: `${h}:${m}` },
  }
  delete hoursErrors.value[idx]
}

const toggleDay = (idx) => {
  const updated = { ...form.value.operating_hours }
  if (updated[idx]) delete updated[idx]
  else updated[idx] = { open: '08:00', close: '22:00' }
  form.value.operating_hours = updated
  delete hoursErrors.value[idx]
}

// Salin jam dari hari buka pertama ke semua hari yang sedang buka
const copyToAll = () => {
  const src = form.value.operating_hours[firstOpenDay.value]
  if (!src) return
  const updated = {}
  for (const idx of Object.keys(form.value.operating_hours)) updated[idx] = { ...src }
  form.value.operating_hours = updated
  hoursErrors.value = {}
  toast.success(`Jam ${DAY_OPTIONS[firstOpenDay.value].label} disalin ke semua hari buka`)
}

// ── Override toko ──────────────────────────────────────────────────
// Konfirmasi untuk "Paksa Buka"/"Paksa Tutup" karena langsung berdampak ke customer.
const requestOverride = async (val) => {
  if (val === form.value.is_open_override) return
  if (val !== null) {
    const ok = await ask(
      val === false
        ? {
            title: 'Paksa toko tutup?',
            message: 'Customer tidak akan bisa checkout sampai Anda mengembalikan status ini.',
            confirmText: 'Ya, tutup toko',
            danger: true,
          }
        : {
            title: 'Paksa toko buka?',
            message: 'Toko akan dibuka di luar jadwal normal. Pastikan dapur/kasir memang siap menerima pesanan.',
            confirmText: 'Ya, buka toko',
          }
    )
    if (!ok) return
  }
  form.value.is_open_override = val
}

// ── Validasi ───────────────────────────────────────────────────────
const validateWhatsapp = () => {
  const v = form.value.admin_whatsapp
  errors.value.whatsapp = v && !WHATSAPP_REGEX.test(v) ? 'Format tidak valid. Gunakan: 628xxxxxxxxxx' : ''
  return !errors.value.whatsapp
}
const onWhatsappInput = () => {
  form.value.admin_whatsapp = form.value.admin_whatsapp.replace(/\D/g, '') // hanya angka
  errors.value.whatsapp = ''
}

const validateHours = () => {
  const next = {}
  for (const [idx, range] of Object.entries(form.value.operating_hours)) {
    if (range?.open && range?.close && range.open >= range.close) {
      next[idx] = 'Jam tutup harus lebih besar dari jam buka'
    }
  }
  hoursErrors.value = next
  return Object.keys(next).length === 0
}

const validate = () => {
  const okWa = validateWhatsapp()
  const okHours = validateHours()
  return okWa && okHours
}

// ── Data ───────────────────────────────────────────────────────────
const applyFetchedData = (data, offline) => {
  const f = {
    admin_whatsapp:   data.admin_whatsapp   || '',
    is_open_override: data.is_open_override ?? null,
    closed_message:   data.closed_message   || defaultForm().closed_message,
    operating_hours:  data.operating_hours  || {},
  }
  form.value      = clone(f)
  savedForm.value = clone(f)
  isOffline.value = offline
}

const fetchData = async () => {
  try {
    const res = await apiClient.get('/orders/settings/')
    applyFetchedData(res.data, false)
  } catch (err) {
    console.error(err)
    // Cache lokal hanya untuk BACA cepat saat server tidak terjangkau, dan admin
    // diberi tahu eksplisit bahwa ini bukan data live.
    const cached = localStorage.getItem('store_settings')
    if (cached) {
      try { applyFetchedData(JSON.parse(cached), true) } catch { /* cache korup, abaikan */ }
    }
    toast.error('Gagal memuat konfigurasi dari server' + (cached ? ' — menampilkan cache lokal' : ''))
  }
}

const saveAll = async () => {
  if (!validate()) {
    toast.error('Periksa kembali isian yang bertanda merah.')
    return
  }
  loading.value = true
  try {
    const payload = {
      admin_whatsapp:   form.value.admin_whatsapp,
      is_open_override: form.value.is_open_override,
      closed_message:   form.value.closed_message,
      operating_hours:  form.value.operating_hours,
    }
    await apiClient.put('/orders/settings/', payload)

    // Cache disimpan HANYA setelah server mengonfirmasi sukses.
    localStorage.setItem('store_settings', JSON.stringify(payload))

    savedForm.value = clone(form.value)
    isOffline.value = false
    await refetchSettings()
    toast.success('Pengaturan berhasil disimpan!')
  } catch (err) {
    console.error(err)
    toast.error('Gagal menyimpan ke server. Perubahan Anda BELUM tersimpan — coba lagi.')
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.value        = clone(savedForm.value)
  errors.value      = { whatsapp: '' }
  hoursErrors.value = {}
}

// Peringatan bila tab ditutup saat masih ada perubahan
const onBeforeUnload = (e) => {
  if (!hasChanges.value) return
  e.preventDefault()
  e.returnValue = ''
}
onMounted(() => {
  fetchData()
  window.addEventListener('beforeunload', onBeforeUnload)
})
onBeforeUnmount(() => window.removeEventListener('beforeunload', onBeforeUnload))
</script>

<style scoped>
/* ── Banner status ─────────────────────────────────────────────── */
.set-banner {
  display: flex; align-items: center; gap: 0.7rem;
  padding: 0.75rem 1.1rem;
  border: 1px solid var(--border); border-radius: var(--r-md);
  background: var(--surface);
}
.set-banner p { margin: 0; font-size: 0.8125rem; line-height: 1.5; color: var(--text-dim); }
.set-banner strong { color: var(--text); }
.set-banner--green { background: var(--tint-green); border-color: var(--line-green); }
.set-banner--red   { background: var(--tint-accent); border-color: var(--line-accent); }
.set-banner--amber { background: var(--tint-amber); border-color: var(--line-amber); align-items: flex-start; }
.set-banner-icon { flex-shrink: 0; margin-top: 2px; color: var(--amber-soft); }
.set-banner-note { margin-left: 0.25rem; color: var(--text-faint); }
.set-banner-note--amber { color: var(--amber-soft); font-weight: 600; }

.set-pulse { flex-shrink: 0; width: 9px; height: 9px; border-radius: 50%; background: var(--red-soft); }
.set-pulse.is-open { background: var(--green); animation: set-pulse 2s infinite; }
@keyframes set-pulse {
  0%, 100% { box-shadow: 0 0 0 3px color-mix(in srgb, var(--green) 25%, transparent); }
  50%      { box-shadow: 0 0 0 6px color-mix(in srgb, var(--green) 8%, transparent); }
}

/* ── WhatsApp ──────────────────────────────────────────────────── */
.set-code {
  padding: 1px 6px; border-radius: 4px;
  background: rgb(var(--ink) / 0.07); color: var(--text-2);
  font-family: var(--font-mono); font-size: 0.72rem;
}
.set-preview {
  display: flex; align-items: center; gap: 0.75rem;
  padding: 0.65rem 0.9rem; min-width: 0;
  border: 1px solid var(--border); border-radius: var(--r-md);
  background: rgb(var(--ink) / 0.03);
}
.set-preview-label { flex-shrink: 0; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-faint); }
.set-preview-link { min-width: 0; font-size: 0.78rem; color: var(--text-dim); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.set-preview-link strong { color: var(--green-soft); font-weight: 600; }

.set-note {
  display: flex; align-items: flex-start; gap: 0.65rem;
  padding: 0.75rem 0.9rem;
  border: 1px solid var(--line-blue); border-radius: var(--r-md);
  background: var(--tint-blue);
}
.set-note p { margin: 0; font-size: 0.78rem; line-height: 1.6; color: var(--text-dim); }
.set-note strong { color: var(--text); }
.set-note-icon { flex-shrink: 0; margin-top: 2px; color: var(--blue-soft); }
.set-note--amber { background: var(--tint-amber); border-color: var(--line-amber); }
.set-note--amber .set-note-icon { color: var(--amber-soft); }

/* ── Override ──────────────────────────────────────────────────── */
.set-override { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; }
.set-override-btn {
  display: flex; align-items: center; justify-content: center; gap: 0.5rem;
  min-height: 46px; padding: 0.6rem 0.75rem;
  border: 1px solid var(--border-strong); border-radius: var(--r-md);
  background: var(--surface-2); color: var(--text-dim);
  font-family: inherit; font-size: 0.8125rem; font-weight: 600;
  cursor: pointer; transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.set-override-btn:hover { color: var(--text); background: var(--surface-hover); }
.set-override-btn.is-active.is-blue  { background: var(--tint-blue);   border-color: var(--line-blue);   color: var(--blue-soft); }
.set-override-btn.is-active.is-green { background: var(--tint-green);  border-color: var(--line-green);  color: var(--green-soft); }
.set-override-btn.is-active.is-red   { background: var(--tint-accent); border-color: var(--line-accent); color: var(--red-soft); }

/* ── Jam operasional ───────────────────────────────────────────── */
.hours-list { margin: 0; padding: 0.25rem 1.25rem 0.5rem; list-style: none; }
.hours-item { border-bottom: 1px solid var(--border); }
.hours-item:last-child { border-bottom: none; }
.hours-row {
  display: grid;
  grid-template-columns: 2.75rem 6.5rem minmax(0, 1fr);
  align-items: center;
  gap: 0.5rem 0.85rem;
  padding: 0.75rem 0;
}
.hours-day { font-size: 0.875rem; font-weight: 700; color: var(--text); }
.hours-toggle { display: flex; align-items: center; gap: 0.6rem; }
.hours-state { font-size: 0.72rem; font-weight: 600; color: var(--text-faint); }
.hours-state.is-on { color: var(--green-soft); }
.hours-off { font-size: 0.78rem; font-style: italic; color: var(--text-faint); }
.hours-error { padding: 0 0 0.6rem 3.6rem; }

.time-fields { display: flex; align-items: flex-end; flex-wrap: wrap; gap: 0.5rem 1.25rem; }
.time-group { display: flex; flex-direction: column; gap: 0.2rem; }
.time-label { font-size: 0.62rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-faint); }
.time-inputs { display: flex; align-items: center; gap: 0.25rem; }
.time-sep { font-weight: 700; color: var(--text-faint); }
.time-select {
  width: 4.1rem; min-height: 40px; padding: 0.4rem 0.2rem;
  font-family: var(--font-mono); font-size: 0.875rem; text-align: center; text-align-last: center;
  background-image: none; padding-right: 0.2rem;
}

/* ── Responsif ─────────────────────────────────────────────────── */
@media (max-width: 560px) {
  .set-override { grid-template-columns: 1fr; }
  .set-override-btn { justify-content: flex-start; }
  .hours-row { grid-template-columns: 2.5rem minmax(0, 1fr); }
  .hours-row .time-fields, .hours-row .hours-off { grid-column: 1 / -1; }
  .hours-error { padding-left: 0; }
  .adm-card-head { flex-wrap: wrap; }
  .adm-card-head-actions { margin-left: 3.2rem; }
}
</style>