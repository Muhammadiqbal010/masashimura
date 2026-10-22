<!--
  MemberPinBox.vue — kotak PIN member di Checkout (selalu terlihat oleh semua pelanggan).
  Sebelum PIN benar tidak ada angka poin yang tampil. Pesan gagal dibuat sama untuk semua
  kemungkinan (bukan member, belum punya PIN, PIN salah, terkunci) supaya nomor orang lain
  tidak bisa ditebak statusnya.
-->
<template>
  <div class="pin-box">
    <!-- Sudah terverifikasi -->
    <template v-if="info">
      <div class="pin-head">
        <span class="pin-tile"><Gift :size="15" /></span>
        <div class="pin-head-text">
          <p class="pin-title">Poin kamu</p>
          <p class="pin-balance">{{ info.points.toLocaleString('id-ID') }}</p>
        </div>
        <button type="button" class="pin-link" @click="$emit('reset')">Tutup</button>
      </div>

      <div v-if="info.progress" class="pin-progress">
        <div class="pin-bar" role="progressbar" :aria-valuenow="Math.min(info.points, info.progress.target_cost)" aria-valuemin="0" :aria-valuemax="info.progress.target_cost" :aria-label="'Progres menuju ' + info.progress.target_name">
          <span class="pin-bar-fill" :style="{ width: pct + '%' }"></span>
        </div>
        <p class="pin-progress-text">
          <template v-if="info.points >= info.progress.target_cost">
            Cukup untuk menukar <strong>{{ info.progress.target_name }}</strong> ({{ info.progress.target_cost }} poin).
          </template>
          <template v-else>
            {{ info.points }} dari {{ info.progress.target_cost }} poin untuk <strong>{{ info.progress.target_name }}</strong>. Kurang {{ info.progress.target_cost - info.points }} poin lagi.
          </template>
        </p>
      </div>

      <p v-if="expiryText" class="pin-expiry" :class="{ 'is-soon': soon }">{{ expiryText }}</p>
    </template>

    <!-- Belum terverifikasi -->
    <template v-else>
      <label for="co-pin" class="pin-label">PIN member <span class="pin-opt">(opsional, untuk lihat dan tukar poin)</span></label>
      <div class="pin-row">
        <input
          id="co-pin"
          :value="pin"
          type="password"
          inputmode="numeric"
          autocomplete="new-password"
          name="member-pin"
          maxlength="4"
          pattern="[0-9]*"
          class="field pin-input tabular-nums"
          placeholder="••••"
          aria-describedby="co-pin-help"
          @input="onPinInput"
          @keyup.enter="submit"
        />
        <button type="button" class="pin-btn" :disabled="!canSubmit" @click="submit">
          <span v-if="loading" class="pin-spin" aria-hidden="true"></span>
          {{ loading ? 'Mengecek…' : 'Lihat poin saya' }}
        </button>
      </div>
      <p v-if="error" class="pin-error" role="alert">{{ error }}</p>
      <p v-else-if="hint" class="pin-hint">{{ hint }}</p>
      <p id="co-pin-help" class="pin-help">
        Setelah 5 kali salah, PIN dikunci 15 menit.
        <a v-if="waLink" :href="waLink" target="_blank" rel="noopener" class="pin-wa">Lupa PIN atau ingin menggantinya? Hubungi admin</a>
      </p>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Gift } from 'lucide-vue-next'
import { orderAPI } from '@/api'
import { isValidPhone } from '@/utils/phone'

const props = defineProps({
  phone: { type: String, default: '' },
  info: { type: Object, default: null },        // hasil verifikasi dari server
  adminWhatsapp: { type: String, default: '' },
})
const emit = defineEmits(['verified', 'reset'])

const pin = ref('')
const loading = ref(false)
const error = ref('')

const NEUTRAL = 'Nomor atau PIN salah, atau minta PIN ke kasir.'

const phoneOk = computed(() => isValidPhone(props.phone))
const pinOk   = computed(() => /^\d{4}$/.test(pin.value))
const canSubmit = computed(() => !loading.value && phoneOk.value && pinOk.value)

// Alasan tombol belum aktif, supaya pelanggan tidak bingung. Kosong saat form masih bersih.
const hint = computed(() => {
  if (loading.value || (!props.phone && !pin.value)) return ''
  if (!phoneOk.value) return 'Isi nomor WhatsApp yang valid dulu.'
  if (!pinOk.value) return 'Masukkan 4 digit PIN.'
  return ''
})

// PIN hanya angka (inputmode numeric tidak menahan ketikan di keyboard desktop).
const onPinInput = (e) => {
  const clean = e.target.value.replace(/\D/g, '').slice(0, 4)
  pin.value = clean
  e.target.value = clean
}

// Ganti nomor = PIN yang sudah diketik dan pesan error lama dibuang.
// Pembuangan hasil verifikasi (info) dilakukan oleh Checkout lewat watch nomor-nya sendiri.
watch(() => props.phone, () => {
  pin.value = ''
  error.value = ''
})

const submit = async () => {
  if (!canSubmit.value) return
  const phoneAtSubmit = props.phone
  const pinAtSubmit   = pin.value

  loading.value = true
  error.value = ''
  try {
    const { data } = await orderAPI.verifyMember(phoneAtSubmit, pinAtSubmit)
    // Nomor diganti saat request berjalan: hasilnya milik nomor lama, buang.
    if (props.phone !== phoneAtSubmit) return
    emit('verified', { info: data, pin: pinAtSubmit })
    pin.value = ''
  } catch {
    if (props.phone !== phoneAtSubmit) return
    // Semua kegagalan (termasuk jaringan) memakai pesan yang sama.
    error.value = NEUTRAL
  } finally {
    loading.value = false
  }
}

const pct = computed(() => {
  const p = props.info?.progress
  if (!p || !p.target_cost) return 0
  return Math.min(100, Math.round((p.points / p.target_cost) * 100))
})

const soon = computed(() => {
  const d = props.info?.days_until_expiry
  return d !== null && d !== undefined && d <= 14
})

const fmtDate = (iso) => new Date(iso).toLocaleDateString('id-ID', { day: 'numeric', month: 'long', year: 'numeric' })

const expiryText = computed(() => {
  const i = props.info
  if (!i) return ''
  if (i.points_expiring_note && !i.expiry_date) return i.points_expiring_note   // mis. poin baru saja hangus
  if (!i.expiry_months || !i.expiry_date || i.points <= 0) return ''
  const sisa = i.days_until_expiry
  const kapan = sisa !== null && sisa >= 0 ? `${fmtDate(i.expiry_date)} (${sisa} hari lagi)` : fmtDate(i.expiry_date)
  return `Poin hangus ${kapan} kalau kamu tidak belanja selama ${i.expiry_months} bulan. Setiap belanja memulai hitungan dari awal.`
})

const waLink = computed(() => {
  const number = (props.adminWhatsapp || '').replace(/\D/g, '')
  if (!number) return ''
  const text = `Halo admin, saya lupa PIN member untuk nomor ${props.phone || ''}`.trim()
  return `https://wa.me/${number}?text=${encodeURIComponent(text)}`
})
</script>

<style scoped>
.pin-box { display: flex; flex-direction: column; gap: .6rem; }
.pin-label { font-size: .875rem; font-weight: 500; color: #C8C8C8; }
.pin-opt { font-weight: 400; color: #9A9AA3; font-size: .75rem; }
.pin-row { display: flex; gap: .6rem; }
.pin-input { max-width: 7.5rem; text-align: center; letter-spacing: .4em; }
.pin-btn {
  min-height: 48px; flex: 1; padding: 0 1rem; border-radius: .875rem; cursor: pointer;
  border: 1px solid rgba(244,197,66,.35); background: rgba(244,197,66,.1); color: #F4C542;
  font-size: .875rem; font-weight: 600; display: inline-flex; align-items: center; justify-content: center; gap: .5rem;
}
.pin-btn:disabled { opacity: .45; cursor: not-allowed; }
.pin-btn:focus-visible, .pin-link:focus-visible, .pin-wa:focus-visible { outline: 2px solid #F4C542; outline-offset: 2px; }
.pin-spin { width: 14px; height: 14px; border-radius: 50%; border: 2px solid currentColor; border-top-color: transparent; animation: pin-rot .7s linear infinite; }
@keyframes pin-rot { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .pin-spin { animation: none; } }
.pin-error { margin: 0; font-size: .8125rem; color: #F0605A; }
.pin-hint { margin: 0; font-size: .8125rem; color: #F4C542; }
.pin-help { margin: 0; font-size: .75rem; line-height: 1.5; color: #B8B8C0; }
.pin-wa { display: block; margin-top: .25rem; color: #F4C542; text-decoration: underline; text-underline-offset: 2px; }

.pin-head { display: flex; align-items: center; gap: .625rem; }
.pin-tile { display: flex; height: 2rem; width: 2rem; align-items: center; justify-content: center; border-radius: .625rem; border: 1px solid rgba(244,197,66,.25); background: rgba(244,197,66,.1); color: #F4C542; flex-shrink: 0; }
.pin-head-text { flex: 1; min-width: 0; }
.pin-title { margin: 0; font-size: .75rem; color: #B8B8C0; }
.pin-balance { margin: 0; font-family: "Manrope", ui-sans-serif, system-ui, sans-serif; font-size: 1.375rem; font-weight: 600; color: #F4C542; font-variant-numeric: tabular-nums; }
.pin-link { min-height: 40px; padding: 0 .5rem; background: none; border: 0; color: #B8B8C0; font-size: .8125rem; cursor: pointer; text-decoration: underline; }
.pin-progress { display: flex; flex-direction: column; gap: .4rem; }
.pin-bar { height: 8px; border-radius: 999px; background: rgba(255,255,255,.08); overflow: hidden; }
.pin-bar-fill { display: block; height: 100%; border-radius: 999px; background: #F4C542; transition: width .4s ease; }
@media (prefers-reduced-motion: reduce) { .pin-bar-fill { transition: none; } }
.pin-progress-text { margin: 0; font-size: .8125rem; line-height: 1.5; color: #C8C8C8; }
.pin-expiry { margin: 0; font-size: .8125rem; line-height: 1.5; color: #B8B8C0; }
.pin-expiry.is-soon { color: #F4C542; font-weight: 500; }
</style>