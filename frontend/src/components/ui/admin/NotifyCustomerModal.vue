<template>
  <AdminModal :model-value="!!order" title="Kabari pelanggan" size="lg" @update:model-value="(v) => !v && $emit('close')">
    <div v-if="order" class="nc">
      <p class="nc-to">
        Ke <b>{{ order.customer_name || 'Pelanggan' }}</b>
        <span v-if="order.customer_phone"> · {{ order.customer_phone }}</span>
        <span class="nc-faint"> · nota {{ order.order_number || '#' + order.id }}</span>
      </p>

      <div class="nc-field">
        <label class="nc-label" for="nc-type">Jenis pesan</label>
        <select id="nc-type" v-model="type" class="adm-input">
          <option v-for="t in options" :key="t.key" :value="t.key" :disabled="!t.enabled">
            {{ t.label }}{{ t.enabled ? '' : ` (${t.why})` }}
          </option>
        </select>
        <p v-if="current?.hint" class="nc-hint">{{ current.hint }}</p>
      </div>

      <div class="nc-field">
        <label class="nc-label" for="nc-text">Isi pesan <span class="nc-faint">(boleh diedit sebelum dikirim)</span></label>
        <textarea id="nc-text" v-model="text" class="adm-input nc-text" rows="12" />
      </div>

      <p v-if="!phoneOk" class="nc-warn">Pesanan ini tidak punya nomor WhatsApp yang valid, jadi tidak bisa dikirim. Pesan masih bisa disalin.</p>
    </div>

    <template #footer>
      <button type="button" class="adm-btn adm-btn--ghost" @click="copy">Salin pesan</button>
      <button type="button" class="adm-btn adm-btn--primary" :disabled="!phoneOk || !text.trim()" @click="send">
        <MessageCircle :size="14" /> Buka WhatsApp
      </button>
    </template>
  </AdminModal>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { MessageCircle } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import AdminModal from '@/components/ui/admin/Adminmodal.vue'
import {
  waLink, msgReady, msgLate, msgUnavailable, msgRefundReminder, msgPaymentReminder,
} from '@/utils/orderMessages'

const props = defineProps({
  order: { type: Object, default: null },
  // jenis yang dipilih saat modal dibuka; kosong = tebak dari kondisi nota
  initialType: { type: String, default: '' },
})
const emit = defineEmits(['close'])

const type = ref('ready')
const text = ref('')

const options = computed(() => {
  const o = props.order
  if (!o) return []
  const unpaid = ['unpaid', 'pending'].includes(o.payment_status) && o.status !== 'cancelled'
  return [
    { key: 'ready', label: 'Siap diambil (kirim nota)', enabled: true, build: msgReady,
      hint: 'Nota lengkap ikut terkirim, tulisan "siap diambil" ada di bawahnya.' },
    { key: 'late', label: 'Telat', enabled: true, build: msgLate },
    { key: 'unavailable', label: 'Menu habis', enabled: !!o.unavailable_items?.length, why: 'belum ada menu yang ditandai habis',
      build: msgUnavailable, hint: 'Berisi menu yang habis, total baru, dan refund / yang harus dibayar.' },
    { key: 'refund', label: 'Pengingat refund', enabled: !!o.refund_pending, why: 'tidak ada refund tertunda', build: msgRefundReminder },
    { key: 'unpaid', label: 'Pengingat bayar', enabled: unpaid, why: 'sudah lunas / dibatalkan', build: msgPaymentReminder },
  ]
})
const current = computed(() => options.value.find((t) => t.key === type.value))

const guessType = () => {
  const o = props.order
  if (!o) return 'ready'
  if (props.initialType && options.value.find((t) => t.key === props.initialType && t.enabled)) return props.initialType
  if (o.refund_pending) return 'refund'
  if (o.is_ready) return 'ready'
  if (o.is_late) return 'late'
  if (o.unavailable_items?.length) return 'unavailable'
  if (options.value.find((t) => t.key === 'unpaid')?.enabled) return 'unpaid'
  return 'ready'
}

const rebuild = () => {
  const t = current.value
  text.value = t && props.order ? t.build(props.order) : ''
}

// Buka untuk nota lain → pilih jenis awal. Ganti jenis atau data nota berubah → pesan dibuat ulang.
watch(() => [props.order?.id, props.initialType], () => { type.value = guessType(); rebuild() }, { immediate: true })
watch(type, rebuild)

const phoneOk = computed(() => !!waLink(props.order?.customer_phone, 'x'))

const send = () => {
  const url = waLink(props.order.customer_phone, text.value)
  if (url) window.open(url, '_blank', 'noopener')
}
const copy = async () => {
  try { await navigator.clipboard.writeText(text.value); toast.success('Pesan disalin') }
  catch { toast.error('Gagal menyalin pesan') }
}
</script>

<style scoped>
.nc { display: flex; flex-direction: column; gap: 0.9rem; }
.nc-to { margin: 0; font-size: 0.9rem; color: var(--text); }
.nc-faint { color: var(--text-faint); font-size: 0.8rem; font-weight: 400; }
.nc-field { display: flex; flex-direction: column; gap: 0.35rem; }
.nc-label { font-size: 0.78rem; font-weight: 700; color: var(--text-2); }
.nc-hint { margin: 0; font-size: 0.78rem; color: var(--text-2); }
.nc-text { font-family: var(--font-mono, monospace); font-size: 0.82rem; line-height: 1.5; min-height: 14rem; }
.nc-warn { margin: 0; font-size: 0.82rem; color: var(--red-soft); }
</style>
