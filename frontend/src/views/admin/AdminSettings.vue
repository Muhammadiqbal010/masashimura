<template>
  <div class="settings-page">

    <!-- ── Header ─────────────────────────────────────────────────────────── -->
    <div class="page-header">
      <div class="header-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 20h9M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/>
        </svg>
      </div>
      <div>
        <h1 class="page-title">System Settings</h1>
        <p class="page-subtitle">Konfigurasi sistem Masashimura</p>
      </div>
    </div>

    <!-- ── Offline / cache banner (tampil hanya jika data BUKAN dari server) ── -->
    <div v-if="isOffline" class="status-bar status-bar--offline">
      <div class="status-dot status-dot--closed"></div>
      <span class="status-text">
        Tidak dapat terhubung ke server — menampilkan <strong>data cache lokal</strong> (mungkin tidak terbaru).
        Perubahan tidak akan tersimpan sampai koneksi ke server pulih.
      </span>
    </div>

    <!-- ── STATUS TOKO (live indicator) ───────────────────────────────────── -->
    <div class="status-bar" :class="isStoreOpen ? 'status-bar--open' : 'status-bar--closed'">
      <div class="status-dot" :class="isStoreOpen ? 'status-dot--open' : 'status-dot--closed'"></div>
      <span class="status-text">
        Toko sekarang:
        <strong>{{ isStoreOpen ? "BUKA" : "TUTUP" }}</strong>
        <span v-if="form.is_open_override !== null" class="status-override">
          (override manual aktif)
        </span>
        <span v-else class="status-auto">· mengikuti jadwal</span>
      </span>
    </div>

    <!-- CARD 1 — WhatsApp -->
    <div class="card">
      <div class="card-header">
        <div class="card-icon whatsapp-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/>
            <path d="M12 0C5.373 0 0 5.373 0 12c0 2.125.558 4.126 1.535 5.862L.057 23.215a.75.75 0 00.916.938l5.532-1.453A11.943 11.943 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.75a9.702 9.702 0 01-4.964-1.362l-.356-.212-3.684.968.984-3.595-.232-.369A9.711 9.711 0 012.25 12C2.25 6.615 6.615 2.25 12 2.25S21.75 6.615 21.75 12 17.385 21.75 12 21.75z"/>
          </svg>
        </div>
        <div>
          <h2 class="card-title">Nomor WhatsApp Admin</h2>
          <p class="card-desc">Nomor tujuan pengiriman bukti pembayaran dari customer</p>
        </div>
      </div>
      <div class="divider"></div>
      <div class="field-group">
        <div class="field">
          <label class="label" for="admin-whatsapp">Nomor WhatsApp</label>
          <div class="input-wrapper">
            <span class="input-prefix">+</span>
            <input
              id="admin-whatsapp"
              v-model="form.admin_whatsapp"
              type="tel"
              inputmode="numeric"
              class="input"
              placeholder="628xxxxxxxxxx"
              :class="{ 'input--error': errors.whatsapp }"
              :aria-invalid="!!errors.whatsapp"
              @input="errors.whatsapp = ''"
            />
            <span v-if="savedForm.admin_whatsapp && !errors.whatsapp && form.admin_whatsapp === savedForm.admin_whatsapp" class="input-badge">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
              Aktif
            </span>
          </div>
          <p v-if="errors.whatsapp" class="field-error">{{ errors.whatsapp }}</p>
          <p v-else class="field-hint">
            Format internasional tanpa "+", diawali kode negara 62, contoh: <span class="hint-code">6281234567890</span>
          </p>
        </div>
        <div v-if="form.admin_whatsapp" class="preview-box">
          <span class="preview-label">Preview link</span>
          <span class="preview-link">https://wa.me/<strong>{{ form.admin_whatsapp }}</strong></span>
        </div>
      </div>
      <div class="info-box">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="info-icon">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <p>Nomor ini digunakan saat customer checkout. Customer akan diarahkan ke WhatsApp ini untuk mengirimkan bukti pembayaran.</p>
      </div>
    </div>

    <!-- CARD 2 — Override Manual -->
    <div class="card">
      <div class="card-header">
        <div class="card-icon override-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18.36 6.64a9 9 0 11-12.73 0M12 2v10"/>
          </svg>
        </div>
        <div>
          <h2 class="card-title">Kontrol Manual Toko</h2>
          <p class="card-desc">Override jadwal — berguna saat ada situasi mendadak</p>
        </div>
      </div>
      <div class="divider"></div>
      <div class="field-group">
        <div class="override-grid">
          <button @click="requestOverride(null)" :class="['override-btn', form.is_open_override === null ? 'override-btn--active-auto' : '']">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
            Ikut Jadwal
          </button>
          <button @click="requestOverride(true)" :class="['override-btn', form.is_open_override === true ? 'override-btn--active-open' : '']">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/></svg>
            Paksa Buka
          </button>
          <button @click="requestOverride(false)" :class="['override-btn', form.is_open_override === false ? 'override-btn--active-closed' : '']">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
            Paksa Tutup
          </button>
        </div>

        <div class="field">
          <label class="label" for="closed-message">Pesan saat toko tutup</label>
          <textarea id="closed-message" v-model="form.closed_message" class="textarea" rows="2" placeholder="Maaf, kami sedang tidak beroperasi..."></textarea>
          <p class="field-hint">Tampil di halaman menu & checkout saat toko tutup</p>
        </div>
      </div>

      <div v-if="form.is_open_override !== null" class="info-box info-box--warning">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="info-icon">
          <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
          <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        <p>Override manual aktif — toko dipaksa <strong>{{ form.is_open_override ? "BUKA" : "TUTUP" }}</strong>. Klik "Ikut Jadwal" untuk menonaktifkan. Perubahan baru berlaku setelah klik "Simpan Semua".</p>
      </div>
    </div>

    <!-- CARD 3 — Jam Operasional -->
    <div class="card">
      <div class="card-header">
        <div class="card-icon hours-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
          </svg>
        </div>
        <div>
          <h2 class="card-title">Jam Operasional</h2>
          <p class="card-desc">Atur hari dan jam buka. Hari yang tidak diaktifkan = hari libur.</p>
        </div>
      </div>
      <div class="divider"></div>
      <div class="hours-list">
        <div v-for="(day, idx) in DAY_OPTIONS" :key="idx" class="hours-row-wrap">
          <div class="hours-row">
            <div class="hours-day">
              <span class="day-label">{{ day.short }}</span>
            </div>

            <button
              class="day-toggle"
              :class="form.operating_hours[idx] ? 'day-toggle--on' : 'day-toggle--off'"
              @click="toggleDay(idx)"
            >
              {{ form.operating_hours[idx] ? "Buka" : "Libur" }}
            </button>

            <transition name="fade-slide">
              <div v-if="form.operating_hours[idx]" class="time-fields">
                <div class="time-group">
                  <span class="time-label">Buka</span>
                  <div class="time-inputs">
                    <select :value="getHour(form.operating_hours[idx]?.open)" @change="setHour(idx, 'open', $event.target.value)" class="time-select">
                      <option v-for="h in HOURS" :key="h" :value="h">{{ h }}</option>
                    </select>
                    <span class="time-sep">:</span>
                    <select :value="getMinute(form.operating_hours[idx]?.open)" @change="setMinute(idx, 'open', $event.target.value)" class="time-select">
                      <option v-for="m in MINUTES" :key="m" :value="m">{{ m }}</option>
                    </select>
                  </div>
                </div>
                <span class="time-arrow">→</span>
                <div class="time-group">
                  <span class="time-label">Tutup</span>
                  <div class="time-inputs">
                    <select :value="getHour(form.operating_hours[idx]?.close)" @change="setHour(idx, 'close', $event.target.value)" class="time-select">
                      <option v-for="h in HOURS" :key="h" :value="h">{{ h }}</option>
                    </select>
                    <span class="time-sep">:</span>
                    <select :value="getMinute(form.operating_hours[idx]?.close)" @change="setMinute(idx, 'close', $event.target.value)" class="time-select">
                      <option v-for="m in MINUTES" :key="m" :value="m">{{ m }}</option>
                    </select>
                  </div>
                </div>
              </div>
            </transition>

            <div v-if="!form.operating_hours[idx]" class="day-off-label">Hari libur</div>
          </div>
          <p v-if="hoursErrors[idx]" class="field-error hours-row-error">{{ hoursErrors[idx] }}</p>
        </div>
      </div>
    </div>

    <!-- Actions -->
    <div class="actions">
      <button @click="saveAll" :disabled="loading || !hasChanges" class="btn-save">
        <span v-if="loading" class="btn-spinner"></span>
        <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/>
          <polyline points="17 21 17 13 7 13 7 21"/>
          <polyline points="7 3 7 8 15 8"/>
        </svg>
        {{ loading ? "Menyimpan..." : "Simpan Semua" }}
      </button>
      <button v-if="hasChanges && !loading" @click="resetForm" class="btn-cancel">Batalkan</button>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { toast } from "vue-sonner"
import apiClient from "@/api/client"
import { useStoreSettings } from "@/composables/useStoreSettings"

const { isStoreOpen, refetchSettings } = useStoreSettings()

const DAY_OPTIONS = [
  { label: "Senin",  short: "Sen" },
  { label: "Selasa", short: "Sel" },
  { label: "Rabu",   short: "Rab" },
  { label: "Kamis",  short: "Kam" },
  { label: "Jumat",  short: "Jum" },
  { label: "Sabtu",  short: "Sab" },
  { label: "Minggu", short: "Min" },
]

const HOURS   = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, "0"))
const MINUTES = ["00", "15", "30", "45"]
const WHATSAPP_REGEX = /^62[0-9]{8,13}$/ // kode negara 62 + 8-13 digit

const loading    = ref(false)
const isOffline  = ref(false) // true hanya jika data yang tampil BUKAN dari server
const errors     = ref({ whatsapp: "" })
const hoursErrors = ref({})

const defaultForm = () => ({
  admin_whatsapp:   "",
  is_open_override: null,
  closed_message:   "Maaf, kami sedang tidak beroperasi. Silakan kembali sesuai jam operasional kami.",
  operating_hours:  {},
})

const form      = ref(defaultForm())
const savedForm = ref(defaultForm())

const hasChanges = computed(() => JSON.stringify(form.value) !== JSON.stringify(savedForm.value))

const getHour   = (t) => t?.split(":")?.[0] ?? "08"
const getMinute = (t) => t?.split(":")?.[1] ?? "00"

const setHour = (idx, field, val) => {
  if (!form.value.operating_hours[idx]) return
  const min = getMinute(form.value.operating_hours[idx][field])
  form.value.operating_hours = {
    ...form.value.operating_hours,
    [idx]: { ...form.value.operating_hours[idx], [field]: `${val}:${min}` }
  }
}
const setMinute = (idx, field, val) => {
  if (!form.value.operating_hours[idx]) return
  const hr = getHour(form.value.operating_hours[idx][field])
  form.value.operating_hours = {
    ...form.value.operating_hours,
    [idx]: { ...form.value.operating_hours[idx], [field]: `${hr}:${val}` }
  }
}

const toggleDay = (idx) => {
  const updated = { ...form.value.operating_hours }
  if (updated[idx]) {
    delete updated[idx]
  } else {
    updated[idx] = { open: "08:00", close: "22:00" }
  }
  form.value.operating_hours = updated
  delete hoursErrors.value[idx]
}

// Override toko: minta konfirmasi untuk "Paksa Buka"/"Paksa Tutup" karena
// langsung berdampak pada customer yang sedang mengakses situs.
const requestOverride = (val) => {
  if (val === form.value.is_open_override) return
  if (val === false) {
    const ok = window.confirm(
      "Yakin ingin memaksa toko TUTUP? Customer tidak akan bisa checkout sampai Anda mengembalikan status ini."
    )
    if (!ok) return
  } else if (val === true) {
    const ok = window.confirm(
      "Yakin ingin memaksa toko BUKA di luar jadwal normal? Pastikan dapur/kasir memang siap menerima pesanan."
    )
    if (!ok) return
  }
  form.value.is_open_override = val
}

const validateHours = () => {
  const newErrors = {}
  let ok = true
  for (const [idx, range] of Object.entries(form.value.operating_hours)) {
    if (range?.open && range?.close && range.open >= range.close) {
      newErrors[idx] = "Jam tutup harus lebih besar dari jam buka"
      ok = false
    }
  }
  hoursErrors.value = newErrors
  return ok
}

const validate = () => {
  let ok = true
  if (form.value.admin_whatsapp && !WHATSAPP_REGEX.test(form.value.admin_whatsapp)) {
    errors.value.whatsapp = "Format tidak valid. Gunakan: 628xxxxxxxxxx"
    ok = false
  }
  if (!validateHours()) ok = false
  return ok
}

const applyFetchedData = (data, offline) => {
  const f = {
    admin_whatsapp:   data.admin_whatsapp   || "",
    is_open_override: data.is_open_override ?? null,
    closed_message:   data.closed_message   || defaultForm().closed_message,
    operating_hours:  data.operating_hours  || {},
  }
  form.value      = JSON.parse(JSON.stringify(f))
  savedForm.value = JSON.parse(JSON.stringify(f))
  isOffline.value = offline
}

const fetchData = async () => {
  try {
    const res = await apiClient.get("/orders/settings/")
    applyFetchedData(res.data, false)
  } catch (err) {
    console.error(err)
    // Cache lokal hanya dipakai untuk BACA cepat saat server tidak terjangkau.
    // Kita tetap beri tahu admin secara eksplisit bahwa ini bukan data live,
    // supaya tidak ada kesan pengaturan "aman" padahal belum tentu sinkron.
    const cached = localStorage.getItem("store_settings")
    if (cached) {
      try {
        applyFetchedData(JSON.parse(cached), true)
      } catch {
        // cache korup, abaikan dan pakai default kosong
      }
    }
    toast.error("Gagal memuat konfigurasi dari server" + (cached ? " — menampilkan cache lokal" : ""))
  }
}

const saveAll = async () => {
  if (!validate()) return
  loading.value = true
  try {
    const payload = {
      admin_whatsapp:   form.value.admin_whatsapp,
      is_open_override: form.value.is_open_override,
      closed_message:   form.value.closed_message,
      operating_hours:  form.value.operating_hours,
    }
    await apiClient.put("/orders/settings/", payload)

    // Simpan cache lokal HANYA setelah server mengonfirmasi sukses —
    // jadi cache selalu merepresentasikan state server yang valid, bukan
    // tebakan optimistis saat request sebenarnya gagal.
    localStorage.setItem("store_settings", JSON.stringify(payload))

    savedForm.value = JSON.parse(JSON.stringify(form.value))
    isOffline.value = false
    await refetchSettings()
    toast.success("Pengaturan berhasil disimpan!")
  } catch (err) {
    console.error(err)
    toast.error("Gagal menyimpan ke server. Perubahan Anda BELUM tersimpan — coba lagi.")
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.value    = JSON.parse(JSON.stringify(savedForm.value))
  errors.value  = { whatsapp: "" }
  hoursErrors.value = {}
}

onMounted(fetchData)
</script>

<style scoped>
.settings-page {
  max-width: 720px; margin: 0 auto;
  padding: 32px 24px 80px; color: white;
  display: flex; flex-direction: column; gap: 24px;
}
.page-header { display: flex; align-items: center; gap: 14px; }
.header-icon {
  width: 42px; height: 42px; border-radius: 12px;
  background: rgba(220,38,38,0.12); border: 1px solid rgba(220,38,38,0.2);
  display: flex; align-items: center; justify-content: center;
  color: #ef4444; flex-shrink: 0;
}
.page-title { font-size: 22px; font-weight: 700; letter-spacing: -0.02em; line-height: 1.2; font-family: 'Oswald', sans-serif; text-transform: uppercase; }
.page-subtitle { font-size: 13px; color: rgba(255,255,255,0.35); margin-top: 2px; }

.status-bar { display: flex; align-items: center; gap: 10px; padding: 12px 18px; border-radius: 12px; border: 1px solid; }
.status-bar--open    { background: rgba(34,197,94,0.06);  border-color: rgba(34,197,94,0.15); }
.status-bar--closed  { background: rgba(239,68,68,0.06);  border-color: rgba(239,68,68,0.15); }
.status-bar--offline { background: rgba(245,158,11,0.06); border-color: rgba(245,158,11,0.2); }
.status-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.status-dot--open   { background: #22c55e; box-shadow: 0 0 0 3px rgba(34,197,94,0.2); animation: pulse 2s infinite; }
.status-dot--closed { background: #ef4444; }
@keyframes pulse { 0%,100% { box-shadow: 0 0 0 3px rgba(34,197,94,0.2); } 50% { box-shadow: 0 0 0 6px rgba(34,197,94,0.08); } }
.status-text { font-size: 12.5px; color: rgba(255,255,255,0.5); }
.status-text strong { font-weight: 700; color: white; }
.status-override { color: #f59e0b; margin-left: 4px; }
.status-auto     { color: rgba(255,255,255,0.2); margin-left: 4px; }

.card { background: #0d0d0d; border: 1px solid rgba(255,255,255,0.07); border-radius: 18px; overflow: hidden; }
.card-header { display: flex; align-items: flex-start; gap: 14px; padding: 22px 26px; }
.card-icon { width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.whatsapp-icon { background: rgba(37,211,102,0.1); color: #25d366; }
.override-icon { background: rgba(245,158,11,0.1); color: #f59e0b; }
.hours-icon    { background: rgba(99,102,241,0.1); color: #818cf8; }
.card-title { font-size: 15px; font-weight: 600; letter-spacing: -0.01em; }
.card-desc  { font-size: 12.5px; color: rgba(255,255,255,0.35); margin-top: 3px; line-height: 1.5; }
.divider    { height: 1px; background: rgba(255,255,255,0.05); }
.field-group { padding: 22px 26px; display: flex; flex-direction: column; gap: 16px; }

.field { display: flex; flex-direction: column; gap: 8px; }
.label { font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: rgba(255,255,255,0.35); }

.input-wrapper { position: relative; display: flex; align-items: center; }
.input-prefix  { position: absolute; left: 14px; font-size: 15px; color: rgba(255,255,255,0.3); pointer-events: none; }
.input {
  width: 100%; background: #111; border: 1px solid rgba(255,255,255,0.08);
  padding: 12px 110px 12px 28px; border-radius: 12px; color: white;
  font-size: 14px; transition: border-color 0.2s, box-shadow 0.2s;
  font-family: 'SF Mono','Fira Code',monospace;
}
.input::placeholder { color: rgba(255,255,255,0.18); font-family: inherit; }
.input:focus { outline: none; border-color: rgba(220,38,38,0.5); box-shadow: 0 0 0 3px rgba(220,38,38,0.08); }
.input--error { border-color: rgba(239,68,68,0.6) !important; }
.input-badge {
  position: absolute; right: 12px; display: flex; align-items: center; gap: 5px;
  font-size: 11px; font-weight: 600; color: #22c55e;
  background: rgba(34,197,94,0.1); border: 1px solid rgba(34,197,94,0.2);
  padding: 4px 9px; border-radius: 20px;
}
.field-error { font-size: 12px; color: #f87171; }
.field-hint  { font-size: 12px; color: rgba(255,255,255,0.22); line-height: 1.5; }
.hint-code   { font-family: 'SF Mono','Fira Code',monospace; font-size: 11.5px; color: rgba(255,255,255,0.45); background: rgba(255,255,255,0.05); padding: 1px 5px; border-radius: 4px; }

.textarea {
  width: 100%; background: #111; border: 1px solid rgba(255,255,255,0.08);
  padding: 12px 14px; border-radius: 12px; color: white; font-size: 13px;
  resize: none; line-height: 1.6; font-family: inherit; transition: border-color 0.2s;
}
.textarea::placeholder { color: rgba(255,255,255,0.18); }
.textarea:focus { outline: none; border-color: rgba(220,38,38,0.4); }

.preview-box { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 11px 15px; display: flex; align-items: center; gap: 10px; }
.preview-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: rgba(255,255,255,0.18); white-space: nowrap; }
.preview-link  { font-size: 12.5px; color: rgba(255,255,255,0.3); font-family: 'SF Mono','Fira Code',monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.preview-link strong { color: #25d366; font-weight: 600; }

.info-box { margin: 0 26px 22px; background: rgba(59,130,246,0.04); border: 1px solid rgba(59,130,246,0.1); border-radius: 10px; padding: 12px 14px; display: flex; align-items: flex-start; gap: 10px; }
.info-box--warning { background: rgba(245,158,11,0.05); border-color: rgba(245,158,11,0.15); }
.info-box--warning .info-icon { color: rgba(251,191,36,0.6); }
.info-icon { color: rgba(147,197,253,0.5); flex-shrink: 0; margin-top: 1px; }
.info-box p { font-size: 12.5px; color: rgba(255,255,255,0.3); line-height: 1.6; }
.info-box strong { color: rgba(255,255,255,0.6); }

.override-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 8px; }
.override-btn {
  display: flex; align-items: center; justify-content: center; gap: 7px;
  padding: 11px 10px; border-radius: 12px; font-size: 11.5px; font-weight: 600;
  border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.03);
  color: rgba(255,255,255,0.4); cursor: pointer; transition: all 0.15s;
}
.override-btn:hover { border-color: rgba(255,255,255,0.15); color: rgba(255,255,255,0.7); }
.override-btn--active-auto   { background: rgba(99,102,241,0.12); border-color: rgba(99,102,241,0.3); color: #a5b4fc; }
.override-btn--active-open   { background: rgba(34,197,94,0.1);  border-color: rgba(34,197,94,0.3);  color: #4ade80; }
.override-btn--active-closed { background: rgba(239,68,68,0.1);  border-color: rgba(239,68,68,0.3);  color: #f87171; }

.hours-list { padding: 8px 26px 22px; display: flex; flex-direction: column; gap: 0; }
.hours-row-wrap { border-bottom: 1px solid rgba(255,255,255,0.04); }
.hours-row-wrap:last-child { border-bottom: none; }
.hours-row { display: flex; align-items: center; gap: 12px; padding: 11px 0; }
.hours-row-error { padding: 0 0 8px 52px; }
.hours-day { width: 40px; flex-shrink: 0; }
.day-label { font-size: 13px; font-weight: 700; color: white; display: block; }

.day-toggle {
  flex-shrink: 0; padding: 5px 0; border-radius: 8px;
  font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;
  cursor: pointer; border: 1px solid; transition: all 0.15s; width: 58px; text-align: center;
}
.day-toggle--on  { background: rgba(34,197,94,0.1); border-color: rgba(34,197,94,0.25); color: #4ade80; }
.day-toggle--off { background: rgba(255,255,255,0.03); border-color: rgba(255,255,255,0.08); color: rgba(255,255,255,0.25); }

.time-fields { display: flex; align-items: center; gap: 10px; flex: 1; }
.time-group  { display: flex; flex-direction: column; gap: 3px; }
.time-label  { font-size: 9px; text-transform: uppercase; letter-spacing: 0.1em; color: rgba(255,255,255,0.2); }
.time-inputs { display: flex; align-items: center; gap: 3px; }
.time-select {
  background: #111; border: 1px solid rgba(255,255,255,0.09);
  color: white; font-size: 13px; font-family: 'SF Mono','Fira Code',monospace;
  padding: 6px 2px; border-radius: 8px; text-align: center;
  cursor: pointer; appearance: none; -webkit-appearance: none;
  width: 42px; transition: border-color 0.15s;
}
.time-select:focus { outline: none; border-color: rgba(220,38,38,0.4); }
.time-sep   { color: rgba(255,255,255,0.3); font-size: 14px; font-weight: 700; }
.time-arrow { color: rgba(255,255,255,0.15); font-size: 12px; flex-shrink: 0; margin: 0 2px; }
.day-off-label { flex: 1; font-size: 11.5px; color: rgba(255,255,255,0.12); font-style: italic; }

.fade-slide-enter-active { transition: all 0.2s ease-out; }
.fade-slide-leave-active { transition: all 0.15s ease-in; }
.fade-slide-enter-from, .fade-slide-leave-to { opacity: 0; transform: translateX(-6px); }

.actions { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.btn-save {
  display: flex; align-items: center; gap: 8px; background: #dc2626; color: white;
  border: none; padding: 13px 28px; border-radius: 12px; font-size: 13.5px;
  font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;
  cursor: pointer; transition: background 0.2s, transform 0.15s, opacity 0.2s;
}
.btn-save:hover:not(:disabled) { background: #ef4444; transform: translateY(-1px); }
.btn-save:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-spinner { width: 15px; height: 15px; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 0.7s linear infinite; flex-shrink: 0; }
@keyframes spin { to { transform: rotate(360deg); } }
.btn-cancel { background: transparent; border: 1px solid rgba(255,255,255,0.1); color: rgba(255,255,255,0.4); padding: 13px 20px; border-radius: 12px; font-size: 13.5px; font-weight: 600; cursor: pointer; transition: border-color 0.2s, color 0.2s; }
.btn-cancel:hover { border-color: rgba(255,255,255,0.2); color: rgba(255,255,255,0.7); }

@media (max-width: 540px) {
  .settings-page { padding: 20px 14px 60px; gap: 18px; }
  .card-header { padding: 18px; }
  .field-group { padding: 18px; }
  .hours-list  { padding: 8px 18px 18px; }
  .info-box    { margin: 0 18px 18px; }
  .override-grid { grid-template-columns: 1fr; gap: 6px; }
  .override-btn  { justify-content: flex-start; padding: 10px 14px; }
  .page-title    { font-size: 18px; }
  .actions       { flex-direction: column; align-items: stretch; }
  .btn-save, .btn-cancel { justify-content: center; width: 100%; }
  .time-fields { flex-wrap: wrap; gap: 6px; }
}

.time-select::-webkit-scrollbar { display: none; }
.time-select { -ms-overflow-style: none; scrollbar-width: none; }
</style>