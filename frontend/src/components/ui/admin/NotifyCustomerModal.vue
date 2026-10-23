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
        <label class="nc-label" for="nc-text">
          {{ isReceipt ? 'Pesan pembuka' : 'Isi pesan' }}
          <span class="nc-faint">(boleh diedit sebelum dikirim)</span>
        </label>
        <textarea id="nc-text" v-model="text" class="adm-input nc-text" :rows="isReceipt ? 5 : 12" />
      </div>

      <p v-if="!phoneOk" class="nc-warn">Pesanan ini tidak punya nomor WhatsApp yang valid, jadi tidak bisa dikirim. Pesan masih bisa disalin.</p>
    </div>

    <template #footer>
      <button type="button" class="adm-btn adm-btn--ghost" @click="copy">Salin pesan</button>
      <button type="button" class="adm-btn adm-btn--primary" :disabled="!phoneOk || !text.trim()" @click="send">
        <component :is="isReceipt ? ImageIcon : MessageCircle" :size="14" />
        {{ isReceipt ? 'Kirim struk (gambar)' : 'Buka WhatsApp' }}
      </button>
    </template>
  </AdminModal>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { MessageCircle, Image as ImageIcon } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import AdminModal from '@/components/ui/admin/Adminmodal.vue'
import { waLink } from '@/utils/orderMessages'
import {
  msgReceipt, msgLate, msgUnavailable, msgRefundReminder, msgPaymentReminder,
} from '@/utils/friendlyMessages'

const props = defineProps({
  order: { type: Object, default: null },
  // jenis yang dipilih saat modal dibuka; kosong = tebak dari kondisi nota
  initialType: { type: String, default: '' },
})
// 'send-receipt' → induk membuat gambar struk lalu membagikannya bersama teks di kolom pesan.
const emit = defineEmits(['close', 'send-receipt'])

const type = ref('ready')
const text = ref('')

const options = computed(() => {
  const o = props.order
  if (!o) return []
  const unpaid = ['unpaid', 'pending'].includes(o.payment_status) && o.status !== 'cancelled'
  return [
    {
      key: 'ready',
      label: o.is_ready ? 'Siap diambil (kirim struk gambar)' : 'Kirim struk (gambar)',
      enabled: true,
      build: msgReceipt,
      hint: 'Struk dikirim sebagai gambar, pesan di bawah ikut sebagai tulisan pembukanya.',
    },
    { key: 'late', label: 'Telat', enabled: true, build: msgLate },
    { key: 'unavailable', label: 'Menu habis', enabled: !!o.unavailable_items?.length, why: 'belum ada menu yang ditandai habis',
      build: msgUnavailable, hint: 'Berisi menu yang habis, total baru, dan refund / yang harus dibayar.' },
    { key: 'refund', label: 'Pengingat refund', enabled: !!o.refund_pending, why: 'tidak ada refund tertunda', build: msgRefundReminder },
    { key: 'unpaid', label: 'Pengingat bayar', enabled: unpaid, why: 'sudah lunas / dibatalkan', build: msgPaymentReminder },
  ]
})
const current = computed(() => options.value.find((t) => t.key === type.value))
const isReceipt = computed(() => type.value === 'ready')

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

// Buka untuk nota lain → pilih jenis awal & susun pesan. Ganti jenis → pesan dibuat ulang.
// Kunci watch sengaja STRING: kalau array, polling (objek order diganti tiap 5 detik) akan
// menimpa pesan yang sedang diedit kasir.
watch(() => `${props.order?.id ?? ''}:${props.initialType}`, () => { type.value = guessType(); rebuild() }, { immediate: true })
watch(type, rebuild)

const phoneOk = computed(() => !!waLink(props.order?.customer_phone, 'x'))

const send = () => {
  if (isReceipt.value) {
    emit('send-receipt', { order: props.order, caption: text.value })
    return
  }
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
.nc-text { font-family: var(--font-mono, monospace); font-size: 0.82rem; line-height: 1.5; min-height: 6rem; }
.nc-warn { margin: 0; font-size: 0.82rem; color: var(--red-soft); }
</style>