<template>
  <div class="page relative min-h-screen bg-[#080808] pb-24 pt-28 font-inter text-[#FAFAFA] sm:pt-32">
    <div class="page-glow pointer-events-none absolute inset-x-0 top-0 h-[420px]" aria-hidden="true"></div>

    <div class="relative mx-auto max-w-6xl px-5 sm:px-8 lg:px-10">

      <!-- Header -->
      <header class="mb-8 sm:mb-10">
        <h1 class="font-sora text-4xl font-semibold leading-[1.05] tracking-tight sm:text-5xl">
          Pesanan Kamu
        </h1>
        <p class="mt-3 text-base text-[#A3A3A3]">Cek item, isi data, lalu pilih cara bayar.</p>
      </header>

      <!-- ══ PANEL STATUS PEMBAYARAN ONLINE (muncul setelah order gateway dibuat) ══ -->
      <div
        v-if="payment"
        class="card mx-auto max-w-md space-y-6 text-center"
        role="status"
      >
        <div
          class="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border"
          :class="phaseIconClass"
        >
          <div
            v-if="payment.phase === 'starting' || payment.phase === 'waiting'"
            class="h-7 w-7 animate-spin rounded-full border-2 border-white/20 border-t-[#FFF500]"
          ></div>
          <Check v-else-if="payment.phase === 'paid'" :size="26" class="text-emerald-400" />
          <X v-else-if="payment.phase === 'failed'" :size="26" class="text-[#FF5C5C]" />
          <Clock v-else :size="26" class="text-[#FFF500]" />
        </div>

        <div class="space-y-2">
          <h2 class="font-sora text-2xl font-semibold tracking-tight text-[#FAFAFA]">{{ phaseTitle }}</h2>
          <p class="text-sm leading-relaxed text-[#A3A3A3]">{{ phaseDescription }}</p>
        </div>

        <div class="summary-box space-y-2.5 text-left">
          <div class="flex items-center justify-between">
            <span class="text-sm text-[#A3A3A3]">No. order</span>
            <span class="text-sm font-semibold tabular-nums text-[#FAFAFA]">#{{ payment.orderNumber }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-[#A3A3A3]">Total</span>
            <span class="font-sora text-lg font-semibold text-[#FAFAFA]">{{ formatPrice(payment.total) }}</span>
          </div>

          <!-- Ringkasan pesanan (tetap tampil setelah refresh) -->
          <div
            v-if="payment.items?.length"
            class="mt-1 space-y-1.5 border-t border-white/[0.07] pt-3"
          >
            <div
              v-for="(it, i) in payment.items"
              :key="i"
              class="flex justify-between gap-3 text-sm"
            >
              <span class="truncate text-[#A3A3A3]">
                {{ it.quantity }}x {{ it.name }}<template v-if="it.optionText"> ({{ it.optionText }})</template>
              </span>
              <span class="flex-shrink-0 tabular-nums text-[#737373]">{{ formatPrice(it.price * it.quantity) }}</span>
            </div>
          </div>
        </div>

        <div class="space-y-2.5">
          <!-- Berhasil -->
          <template v-if="payment.phase === 'paid'">
            <button
              v-if="payment.waMessage"
              type="button"
              class="btn-wa"
              @click="openWhatsApp(payment.waMessage)"
            >
              Kabari admin via WhatsApp
            </button>
            <button type="button" class="btn-ghost" @click="finishPayment">
              Selesai
            </button>
          </template>

          <!-- Gagal / kedaluwarsa -->
          <template v-else-if="payment.phase === 'failed'">
            <button type="button" class="btn-primary" @click="backToMenu">
              Kembali ke menu
            </button>
          </template>

          <!-- Belum terkonfirmasi -->
          <template v-else-if="payment.phase === 'pending'">
            <button type="button" class="btn-primary" @click="openSnap">
              Lanjutkan bayar
            </button>
            <button type="button" class="btn-ghost" @click="onCheckStatusClick">
              Cek status
            </button>
            <p class="pt-1 text-xs text-[#737373]">
              Order otomatis dibatalkan kalau tidak dibayar dalam 30 menit.
            </p>
          </template>
        </div>
      </div>

      <!-- ══ PANEL PESANAN CASH BERHASIL ══
           WhatsApp TIDAK dibuka otomatis: browser HP (terutama iOS Safari) sering memblokir
           popup yang dibuka setelah proses async. Jadi customer menekan tombolnya sendiri. -->
      <div
        v-else-if="cashDone"
        class="card mx-auto max-w-md space-y-6 text-center"
      >
        <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-emerald-400/30 bg-emerald-400/10">
          <Check :size="26" class="text-emerald-400" />
        </div>

        <div class="space-y-2">
          <h2 class="font-sora text-2xl font-semibold tracking-tight text-[#FAFAFA]">Pesanan dibuat</h2>
          <p class="text-sm leading-relaxed text-[#A3A3A3]">
            Bayar langsung di toko, kasir yang mengonfirmasi pembayaranmu. Kabari admin lewat WhatsApp supaya pesananmu cepat diproses.
          </p>
        </div>

        <div class="summary-box space-y-2.5 text-left">
          <div class="flex items-center justify-between">
            <span class="text-sm text-[#A3A3A3]">No. order</span>
            <span class="text-sm font-semibold tabular-nums text-[#FAFAFA]">#{{ cashDone.orderNumber }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-[#A3A3A3]">Total</span>
            <span class="font-sora text-lg font-semibold text-[#FAFAFA]">{{ formatPrice(cashDone.total) }}</span>
          </div>

          <div
            v-if="cashDone.items?.length"
            class="mt-1 space-y-1.5 border-t border-white/[0.07] pt-3"
          >
            <div
              v-for="(it, i) in cashDone.items"
              :key="i"
              class="flex justify-between gap-3 text-sm"
            >
              <span class="truncate text-[#A3A3A3]">
                {{ it.quantity }}x {{ it.name }}<template v-if="it.optionText"> ({{ it.optionText }})</template>
              </span>
              <span class="flex-shrink-0 tabular-nums text-[#737373]">{{ formatPrice(it.price * it.quantity) }}</span>
            </div>
          </div>
        </div>

        <div class="space-y-2.5">
          <button type="button" class="btn-wa" @click="openWhatsApp(cashDone.waMessage)">
            Kabari admin via WhatsApp
          </button>
          <button type="button" class="btn-ghost" @click="finishCash">
            Selesai
          </button>
        </div>
      </div>

      <!-- ══ FORM CHECKOUT NORMAL ══ -->
      <div v-else>
        <!-- Toko tutup: jelaskan kenapa tombol pesan tidak bisa dipakai -->
        <StoreBanner />

        <div class="grid grid-cols-1 items-start gap-6 lg:grid-cols-[1fr_400px] lg:gap-8">

          <!-- ── KIRI: List Item ──────────────────────────────────── -->
          <section class="space-y-3" aria-label="Item pesanan">

            <!-- Empty -->
            <div
              v-if="cartStore.isEmpty"
              class="space-y-4 rounded-3xl border border-dashed border-white/10 px-6 py-20 text-center"
            >
              <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-[#141414]">
                <ShoppingCart :size="22" class="text-[#A3A3A3]" />
              </div>
              <p class="font-sora text-lg font-semibold text-[#FAFAFA]">Keranjang masih kosong</p>
              <p class="text-sm text-[#A3A3A3]">Pilih menu favoritmu dulu, lalu balik ke sini.</p>
              <router-link to="/menu" class="btn-primary !inline-flex !w-auto px-7">
                Lihat menu
              </router-link>
            </div>

            <!-- Paket -->
            <div
              v-for="line in cartStore.bundleLines"
              :key="line.cartKey"
              class="card-item flex flex-col gap-2"
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="text-[11px] font-semibold uppercase tracking-wider text-[#FFF500]">Paket</p>
                  <h4 class="font-sora text-base font-semibold leading-snug text-[#FAFAFA]">{{ line.name }}</h4>
                </div>
                <button
                  type="button"
                  :aria-label="'Hapus ' + line.name + ' dari keranjang'"
                  @click="cartStore.removeBundle(line.id)"
                  class="-mr-2 -mt-1.5 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full text-[#737373] transition-colors duration-150 hover:bg-[#EE0000]/10 hover:text-[#FF5C5C]"
                >
                  <X :size="16" />
                </button>
              </div>
              <p class="text-sm text-[#A3A3A3]">
                {{ line.quantity }} × {{ formatPrice(line.price) }}
                <span v-if="line.normal_price && line.savings > 0" class="ml-1 text-xs text-[#737373] line-through">{{ formatPrice(line.normal_price) }}</span>
              </p>
              <p v-if="line.savings > 0" class="text-xs font-semibold text-[#FFF500]">Kamu hemat {{ formatPrice(line.savings * line.quantity) }}</p>
              <p class="text-xs text-[#A3A3A3]">{{ line.contents.map((c) => c.quantity * line.quantity + '× ' + c.name).join(' · ') }}</p>
            </div>

            <!-- Items -->
            <div
              v-for="item in Object.values(cartStore.cart)"
              :key="item.cartKey"
              class="card-item flex gap-4"
            >
              <!-- Thumbnail -->
              <div class="h-[72px] w-[72px] flex-shrink-0 overflow-hidden rounded-2xl border border-white/[0.07] bg-[#1A1A1A] sm:h-20 sm:w-20">
                <img
                  v-if="item.image_url"
                  :src="getMediaUrl(item.image_url, 160)"
                  class="pointer-events-none h-full w-full object-cover"
                  :alt="item.name"
                />
                <div v-else class="flex h-full w-full items-center justify-center text-xl opacity-30">🍜</div>
              </div>

              <!-- Detail -->
              <div class="min-w-0 flex-1">
                <div class="flex items-start justify-between gap-3">
                  <h4 class="font-sora text-base font-semibold leading-snug text-[#FAFAFA]">
                    {{ item.name }}
                  </h4>
                  <button
                    type="button"
                    :aria-label="'Hapus ' + item.name + ' dari keranjang'"
                    @click="cartStore.removeFromCart(item.cartKey)"
                    class="-mr-2 -mt-1.5 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full text-[#737373] transition-colors duration-150 hover:bg-[#EE0000]/10 hover:text-[#FF5C5C]"
                  >
                    <X :size="16" />
                  </button>
                </div>

                <p class="mt-1 text-sm text-[#A3A3A3]">
                  {{ item.quantity }} × {{ formatPrice(item.price) }}
                </p>

                <div v-if="item.optionDetails?.length" class="mt-2 flex flex-wrap gap-1.5">
                  <span
                    v-for="opt in item.optionDetails"
                    :key="opt.group + opt.label"
                    class="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-0.5 text-xs font-medium text-[#C8C8C8]"
                  >
                    {{ opt.label }}<template v-if="opt.price"> +{{ formatPrice(opt.price) }}</template>
                  </span>
                </div>

                <p v-if="item.notes" class="mt-2 text-xs italic text-[#FFF500]">
                  "{{ item.notes }}"
                </p>

                <p class="mt-3 font-sora text-base font-semibold tracking-tight text-[#FAFAFA]">
                  {{ formatPrice(item.price * item.quantity) }}
                </p>
              </div>
            </div>
          </section>

          <!-- ── KANAN: Form & Payment ────────────────────────────── -->
          <aside class="card space-y-6 lg:sticky lg:top-24">

            <h2 class="font-sora text-xl font-semibold tracking-tight text-[#FAFAFA]">Data pemesan</h2>

            <!-- Nama -->
            <div class="space-y-2">
              <label for="co-name" class="block text-sm font-medium text-[#C8C8C8]">Nama</label>
              <input
                id="co-name"
                :value="name"
                type="text"
                autocomplete="name"
                :maxlength="NAME_MAX"
                :aria-invalid="nameErrorText ? 'true' : 'false'"
                aria-describedby="co-name-help"
                class="field"
                :class="{ 'field-invalid': nameErrorText }"
                placeholder="Nama kamu"
                @input="onNameInput"
                @blur="nameTouched = true"
              />
              <p
                id="co-name-help"
                class="text-xs leading-relaxed"
                :class="nameErrorText ? 'text-[#FF5C5C]' : 'text-[#737373]'"
                :role="nameErrorText ? 'alert' : undefined"
              >
                {{ nameErrorText || `Huruf saja, ${NAME_MIN}-${NAME_MAX} karakter, tanpa angka atau tanda.` }}
              </p>
            </div>

            <!-- Nomor WA -->
            <div class="space-y-2">
              <label for="co-phone" class="block text-sm font-medium text-[#C8C8C8]">Nomor WhatsApp</label>
              <!-- type="tel" + inputmode="numeric": keypad angka di HP, tapi nilainya tetap string.
                   type="number" sengaja tidak dipakai: Vue mengubahnya jadi Number sehingga angka 0 di depan
                   hilang ("0812..." jadi 812...), dan browser masih menerima huruf "e", "+", "-" serta ".". -->
              <input
                id="co-phone"
                :value="phone"
                type="tel"
                inputmode="numeric"
                autocomplete="tel-national"
                :maxlength="PHONE_MAX"
                :aria-invalid="phoneErrorText ? 'true' : 'false'"
                aria-describedby="co-phone-help"
                class="field tabular-nums"
                :class="{ 'field-invalid': phoneErrorText }"
                placeholder="081234567890"
                @input="onPhoneInput"
                @paste="onPhonePaste"
                @blur="phoneTouched = true"
              />
              <p
                id="co-phone-help"
                class="text-xs leading-relaxed"
                :class="phoneErrorText ? 'text-[#FF5C5C]' : 'text-[#737373]'"
                :role="phoneErrorText ? 'alert' : undefined"
              >
                {{ phoneErrorText || `Diawali 08, ${PHONE_MIN}-${PHONE_MAX} digit angka.` }}
              </p>

              <!-- PIN member: terlihat oleh semua pelanggan supaya status member nomor lain tidak bocor -->
              <div class="mt-3 rounded-2xl border border-white/[0.07] bg-[#0D0D0D] p-3.5">
                <MemberPinBox
                  :phone="phone"
                  :info="memberInfo"
                  :admin-whatsapp="adminWhatsapp"
                  @verified="onMemberVerified"
                  @reset="resetMember"
                />
              </div>
            </div>

            <!-- Metode Pembayaran -->
            <div class="space-y-2">
              <span class="block text-sm font-medium text-[#C8C8C8]">Pembayaran</span>
              <div class="grid grid-cols-2 gap-2.5">
                <button
                  type="button"
                  @click="selectPayment('cash')"
                  :aria-pressed="paymentMethod === 'cash'"
                  :class="[
                    'rounded-2xl border px-4 py-3 text-left transition-all duration-150',
                    paymentMethod === 'cash'
                      ? 'border-[#EE0000] bg-[#EE0000]/10'
                      : 'border-white/10 bg-white/[0.03] hover:border-white/25'
                  ]"
                >
                  <span class="block font-sora text-sm font-semibold text-[#FAFAFA]">Cash</span>
                  <span class="block text-xs text-[#A3A3A3]">Bayar di toko</span>
                </button>
                <button
                  type="button"
                  :disabled="gatewayUnavailable"
                  @click="selectPayment('gateway')"
                  :aria-pressed="paymentMethod === 'gateway'"
                  :class="[
                    'rounded-2xl border px-4 py-3 text-left transition-all duration-150 disabled:cursor-not-allowed disabled:opacity-35',
                    paymentMethod === 'gateway'
                      ? 'border-[#EE0000] bg-[#EE0000]/10'
                      : 'border-white/10 bg-white/[0.03] hover:border-white/25'
                  ]"
                >
                  <span class="block font-sora text-sm font-semibold text-[#FAFAFA]">QRIS</span>
                  <span class="block text-xs text-[#A3A3A3]">Bayar online</span>
                </button>
              </div>
              <p class="pt-0.5 text-xs leading-relaxed text-[#737373]">
                <template v-if="paymentMethod === 'cash'">
                  Bayar langsung di toko. Kasir yang mengonfirmasi pembayaranmu.
                </template>
                <template v-else>
                  Bayar lewat QRIS di popup. Pesanan diproses setelah pembayaran terkonfirmasi otomatis.
                </template>
              </p>
              <p v-if="gatewayUnavailable && !cartStore.isEmpty" class="text-xs text-[#FFF500]">
                Total Rp0 (semua item tukar poin), pembayaran online tidak diperlukan. Pakai Cash.
              </p>
            </div>

            <div class="border-t border-white/[0.07]"></div>

            <!-- Ringkasan Harga -->
            <div class="space-y-3">
              <div class="flex items-center justify-between text-sm">
                <span class="text-[#A3A3A3]">Subtotal</span>
                <span class="tabular-nums text-[#FAFAFA]">{{ formatPrice(cartStore.subtotal) }}</span>
              </div>

              <!-- Kode Promo -->
              <PromoCodeBox
                ref="promoBoxRef"
                :subtotal="cartStore.totalPrice"
                @applied="onPromoApplied"
                @removed="onPromoRemoved"
              />

              <div v-if="appliedPromo" class="flex items-center justify-between text-sm">
                <span class="text-emerald-300">Diskon promo ({{ appliedPromo.code }})</span>
                <span class="tabular-nums text-emerald-300">−{{ formatPrice(appliedPromo.discount_amount) }}</span>
              </div>

              <!-- Tukar Poin -->
              <PointRedeemBox
                :points="pointsBalance"
                :affordable="affordableRewards"
                :locked="lockedRewards"
                v-model:selected-ids="selectedRewardIds"
              />

              <div
                v-for="reward in selectedRewards"
                :key="`reward-${reward.id}`"
                class="flex items-center justify-between gap-3 text-sm"
              >
                <span class="text-[#FFF500]">🎁 {{ reward.menu_name }} (gratis)</span>
                <span class="flex-shrink-0 tabular-nums text-[#737373]">−{{ reward.point_cost.toLocaleString("id-ID") }} poin</span>
              </div>

              <div class="flex items-end justify-between border-t border-white/[0.07] pt-4">
                <span class="text-sm font-medium text-[#A3A3A3]">Total bayar</span>
                <span class="font-sora text-3xl font-semibold leading-none tracking-tight text-[#FAFAFA]">
                  {{ formatPrice(finalTotal) }}
                </span>
              </div>
            </div>

            <!-- CTA -->
            <button
              type="button"
              class="btn-primary !min-h-[56px] !text-base"
              @click="checkout"
              :disabled="isCheckoutDisabled"
            >
              <span>{{ ctaLabel }}</span>
              <ArrowRight v-if="!isProcessing" :size="18" />
            </button>
          </aside>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue"
import { useRouter } from "vue-router"
import { useCartStore } from "@/stores/cart"
import { orderAPI, paymentAPI, getMediaUrl } from "@/api"
import { toast } from "vue-sonner"
import { X, Check, Clock, ShoppingCart, ArrowRight } from "lucide-vue-next"
import { useStoreSettings } from "@/composables/useStoreSettings"
import PromoCodeBox from "@/components/ui/PromoCodeBox.vue"
import PointRedeemBox from "@/components/ui/PointRedeemBox.vue"
import MemberPinBox from "@/components/ui/MemberPinBox.vue"
import StoreBanner from "@/components/ui/StoreBanner.vue"
import { unlockPaymentAudio, playPaymentSuccess } from "@/utils/paymentSuccessSound.js"
import {
  PHONE_MIN, PHONE_MAX,
  sanitizePhone, normalizePastedPhone, isValidPhone, hasValidPhonePrefix, phoneError,
} from "@/utils/phone"
import { NAME_MIN, NAME_MAX, sanitizeName, cleanName, nameError, isValidName } from "@/utils/name"

const cartStore = useCartStore()
const router    = useRouter()
const { adminWhatsapp, isStoreOpen, fetchSettings } = useStoreSettings()

// ══════════════════════════════════════════════════════════════════════════════
// FORM
// ══════════════════════════════════════════════════════════════════════════════
const name            = ref("")
const phone           = ref("")
const paymentMethod   = ref("cash")   // "cash" | "gateway" (Midtrans)
const isProcessing    = ref(false)

// ── Nama pemesan ─────────────────────────────────────────────────────────────
// Hanya huruf dan spasi. Angka dan tanda baca langsung dibuang saat diketik.
const nameTouched = ref(false)
const isNameValid = computed(() => isValidName(name.value))
// Error baru tampil setelah kolom ditinggalkan, supaya tidak menegur saat masih mengetik.
const nameErrorText = computed(() => (nameTouched.value ? nameError(name.value) : ""))

const onNameInput = (e) => {
  const clean = sanitizeName(e.target.value)
  name.value = clean
  e.target.value = clean   // paksa tampilan ikut bersih walau nilai ref tidak berubah
}

// ── Nomor WhatsApp ───────────────────────────────────────────────────────────
// Hanya angka, diawali 08, 10-13 digit. Ketikan non-angka langsung dibuang.
const phoneTouched = ref(false)
const isPhoneValid = computed(() => isValidPhone(phone.value))

// Awalan salah ditegur langsung; aturan panjang baru muncul setelah kolom ditinggalkan,
// supaya pelanggan tidak ditegur saat masih mengetik.
const phoneErrorText = computed(() => {
  const message = phoneError(phone.value)
  if (!message) return ""
  const prefixWrong = phone.value.length > 0 && !hasValidPhonePrefix(phone.value)
  return phoneTouched.value || prefixWrong ? message : ""
})

const onPhoneInput = (e) => {
  const clean = sanitizePhone(e.target.value)
  phone.value = clean
  e.target.value = clean   // paksa tampilan ikut bersih walau nilai ref tidak berubah
}

const onPhonePaste = (e) => {
  e.preventDefault()
  phone.value = normalizePastedPhone(e.clipboardData?.getData("text"))
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

const formatPrice = (p) =>
  new Intl.NumberFormat("id-ID", {
    style: "currency", currency: "IDR", minimumFractionDigits: 0,
  }).format(p || 0)

// ── Promo code ───────────────────────────────────────────────────────────────
const promoBoxRef  = ref(null)
const appliedPromo = ref(null)

const onPromoApplied = (promo) => { appliedPromo.value = promo }
const onPromoRemoved = () => { appliedPromo.value = null }

// ── Tukar poin loyalty ───────────────────────────────────────────────────────
const pointsBalance     = ref(0)
const affordableRewards = ref([])
const lockedRewards     = ref([])
const selectedRewardIds = ref([])

const selectedRewards = computed(() =>
  affordableRewards.value.filter((r) => selectedRewardIds.value.includes(r.id))
)

// Hasil verifikasi PIN (kosong sampai PIN benar). PIN hanya disimpan di memori halaman ini,
// tidak pernah ke localStorage, dan dikirim ulang ke server saat membuat order yang menukar poin.
const memberInfo = ref(null)
const memberPin  = ref("")

const onMemberVerified = ({ info, pin }) => {
  memberInfo.value        = info
  memberPin.value         = pin
  pointsBalance.value     = info.points ?? 0
  affordableRewards.value = info.affordable ?? []
  lockedRewards.value     = info.locked ?? []
  selectedRewardIds.value = []
}

const resetMember = () => {
  memberInfo.value = null
  memberPin.value  = ""
  resetPointRewards()
}

const resetPointRewards = () => {
  pointsBalance.value     = 0
  affordableRewards.value = []
  lockedRewards.value     = []
  selectedRewardIds.value = []
}

// Total setelah dikurangi diskon promo (reward poin gratis Rp0, dihandle backend).
// Ini cuma estimasi tampilan; nominal sebenarnya selalu dihitung ulang di backend.
const finalTotal = computed(() => {
  const promoDiscount = appliedPromo.value?.discount_amount || 0
  return Math.max(cartStore.totalPrice - promoDiscount, 0)
})

// Ganti nomor HP = verifikasi PIN nomor sebelumnya dibuang (MemberPinBox ikut mereset dirinya).
watch(phone, () => {
  if (memberInfo.value) resetMember()
})

// ── Metode pembayaran ────────────────────────────────────────────────────────
// Order Rp0 (semua item tukar poin) ditolak endpoint pembayaran, jadi QRIS dimatikan.
const gatewayUnavailable = computed(() => finalTotal.value <= 0)

const selectPayment = (method) => {
  if (method === "gateway" && gatewayUnavailable.value) return
  paymentMethod.value = method
}

// ══════════════════════════════════════════════════════════════════════════════
// PEMBAYARAN ONLINE (MIDTRANS SNAP)
// ══════════════════════════════════════════════════════════════════════════════

// ── Status pembayaran ────────────────────────────────────────────────────────
// payment = null → form checkout biasa
// payment = { orderNumber, total, waMessage, items, createdAt, message, phase }
//   phase: "starting" | "waiting" | "paid" | "failed" | "pending"
const payment = ref(null)

// ── Pesanan Cash yang baru dibuat ────────────────────────────────────────────
// cashDone = null → form biasa
// cashDone = { orderNumber, total, waMessage, items }
// Tidak perlu disimpan ke localStorage: order sudah ada di backend, ini hanya layar konfirmasi.
const cashDone = ref(null)

// Watch ini ditaruh setelah `payment` dideklarasikan karena membacanya.
watch(gatewayUnavailable, (unavailable) => {
  if (unavailable && paymentMethod.value === "gateway") {
    paymentMethod.value = "cash"
    if (!cartStore.isEmpty && !payment.value) {
      toast.info("Total Rp0, pembayaran dialihkan ke Cash.")
    }
  }
})

// ── Simpan status pembayaran supaya selamat dari refresh ─────────────────────
// Keranjang sengaja dikosongkan begitu order dibuat (order sudah ada di backend).
// Yang harus bertahan saat halaman di-refresh adalah status pembayarannya.
const PENDING_PAYMENT_KEY    = "masashimura:pendingPayment"
const PENDING_PAYMENT_TTL_MS = 3 * 60 * 60 * 1000   // 3 jam (Midtrans kedaluwarsa 30 menit)

const persistPayment = (p) => {
  try {
    localStorage.setItem(PENDING_PAYMENT_KEY, JSON.stringify({
      orderNumber: p.orderNumber,
      total:       p.total,
      waMessage:   p.waMessage,
      items:       p.items,
      createdAt:   p.createdAt,
    }))
  } catch { /* storage penuh / mode private: abaikan, hanya kehilangan fitur restore */ }
}

const clearSavedPayment = () => {
  try { localStorage.removeItem(PENDING_PAYMENT_KEY) } catch { /* abaikan */ }
}

const loadSavedPayment = () => {
  try {
    const raw = localStorage.getItem(PENDING_PAYMENT_KEY)
    if (!raw) return null
    const saved = JSON.parse(raw)
    const fresh = saved?.orderNumber && Date.now() - Number(saved.createdAt) < PENDING_PAYMENT_TTL_MS
    if (!fresh) {
      clearSavedPayment()
      return null
    }
    return saved
  } catch {
    clearSavedPayment()
    return null
  }
}

// ── Polling status ───────────────────────────────────────────────────────────
const POLL_INTERVAL_MS  = 2000
const POLL_MAX_ATTEMPTS = 30   // ≈ 60 detik

let pollRun = 0
const stopPolling = () => { pollRun++ }

const dropPayment = () => {
  stopPolling()
  payment.value = null
  clearSavedPayment()
}

const DEFAULT_PENDING_MESSAGE =
  "Pembayaran belum terkonfirmasi. Kalau kamu sudah membayar, tunggu beberapa detik lalu klik Cek Status."

// Sumber kebenaran = status di backend (diubah webhook Midtrans), BUKAN callback Snap.
// Callback Snap di browser bisa terlewat (tab ditutup, internet putus).
//   attempts       : berapa kali cek sebelum menyerah (jadi "pending")
//   silent         : true = tanpa suara dan toast (dipakai saat restore setelah refresh)
//   pendingMessage : teks kalau sampai akhir belum lunas
const pollStatus = async ({
  attempts = POLL_MAX_ATTEMPTS,
  silent = false,
  pendingMessage = DEFAULT_PENDING_MESSAGE,
} = {}) => {
  const p = payment.value
  if (!p) return

  stopPolling()
  const run = pollRun
  p.phase   = "waiting"
  p.message = ""

  for (let i = 0; i < attempts; i++) {
    if (run !== pollRun) return
    try {
      const { data } = await paymentAPI.getStatus(p.orderNumber)
      if (run !== pollRun) return

      if (data.payment_status === "paid") {
        p.phase = "paid"
        // Suara hanya dibunyikan setelah backend mengonfirmasi lunas,
        // supaya customer tidak pernah dapat "sukses" palsu.
        if (!silent) {
          playPaymentSuccess({ total: p.total })
          toast.success("Pembayaran berhasil!")
        }
        return
      }
      if (data.payment_status === "void" || data.status === "cancelled") {
        p.phase = "failed"
        return
      }
    } catch (err) {
      // Order tidak ada lagi di backend (mis. data dibersihkan): buang status tersimpan.
      if (err.response?.status === 404) {
        dropPayment()
        return
      }
      // selain itu koneksi putus sebentar, lanjut coba lagi
    }
    if (i < attempts - 1) await sleep(POLL_INTERVAL_MS)
  }

  if (run === pollRun) {
    p.phase   = "pending"
    p.message = pendingMessage
  }
}

// Tombol "Cek Status" = tap user, jadi sekalian buka kunci audio.
const onCheckStatusClick = () => {
  unlockPaymentAudio()
  pollStatus({ attempts: 5 })
}

// ── Snap ─────────────────────────────────────────────────────────────────────
const MIDTRANS_CLIENT_KEY = import.meta.env.VITE_MIDTRANS_CLIENT_KEY || ""

// Format client key Midtrans bervariasi (ada "SB-Mid-client-...", ada yang langsung
// "Mid-client-..."), jadi mode ditentukan eksplisit lewat env, bukan dari awalan key.
// Default sandbox. Set VITE_MIDTRANS_IS_PRODUCTION=true hanya saat go-live.
const IS_PRODUCTION = import.meta.env.VITE_MIDTRANS_IS_PRODUCTION === "true"
const SNAP_URL = IS_PRODUCTION
  ? "https://app.midtrans.com/snap/snap.js"
  : "https://app.sandbox.midtrans.com/snap/snap.js"

let snapLoading = null
const loadSnap = () => {
  if (window.snap) return Promise.resolve()
  if (!MIDTRANS_CLIENT_KEY) {
    return Promise.reject(new Error("VITE_MIDTRANS_CLIENT_KEY belum diisi"))
  }
  if (snapLoading) return snapLoading

  snapLoading = new Promise((resolve, reject) => {
    const script = document.createElement("script")
    script.src = SNAP_URL
    script.setAttribute("data-client-key", MIDTRANS_CLIENT_KEY)
    script.onload  = () => resolve()
    script.onerror = () => {
      snapLoading = null
      script.remove()
      reject(new Error("Gagal memuat Midtrans Snap"))
    }
    document.head.appendChild(script)
  })
  return snapLoading
}

// Preload begitu customer milih QRIS, supaya popup cepat kebuka.
watch(paymentMethod, (method) => {
  if (method === "gateway") loadSnap().catch(() => {})
})

// Minta token (token yang sama dipakai ulang backend) lalu buka popup Snap.
// Fungsi ini tidak pernah throw; error ditampilkan lewat panel.
const openSnap = async () => {
  const p = payment.value
  if (!p) return

  // Aman dipanggil berulang. Penting kalau dipicu dari tombol "Lanjutkan Bayar".
  unlockPaymentAudio()

  stopPolling()
  p.phase   = "starting"
  p.message = ""

  try {
    await loadSnap()
    const { data } = await paymentAPI.createSnapToken(p.orderNumber)
    if (!data?.token) throw new Error("Token pembayaran kosong")

    let handled = false
    p.phase = "waiting"
    window.snap.pay(data.token, {
      onSuccess: () => { handled = true; pollStatus() },
      onPending: () => { handled = true; pollStatus() },
      onError:   () => { handled = true; pollStatus({ attempts: 3 }) },
      // Popup ditutup tanpa menyelesaikan: cek sebentar, bisa jadi sudah bayar lalu menutup.
      onClose:   () => { if (!handled) pollStatus({ attempts: 2 }) },
    })
  } catch (err) {
    p.phase = "pending"
    p.message =
      err.response?.data?.detail ||
      "Gagal membuka pembayaran. Cek koneksi lalu coba lagi."
  }
}

// ── Pulihkan status pembayaran setelah halaman di-refresh ────────────────────
const restorePendingPayment = () => {
  const saved = loadSavedPayment()
  if (!saved) return

  payment.value = { ...saved, message: "", phase: "waiting" }
  // Cek sekali ke backend: lunas / gagal / masih menunggu. Tanpa suara dan toast.
  pollStatus({
    attempts: 1,
    silent: true,
    pendingMessage:
      "Pembayaran belum selesai. Klik Lanjutkan Bayar, atau Cek Status kalau kamu sudah membayar.",
  })
}

// ── Tombol di panel ──────────────────────────────────────────────────────────
const finishPayment = () => {
  dropPayment()
  router.push("/")
}

const finishCash = () => {
  cashDone.value = null
  router.push("/")
}

const backToMenu = () => {
  dropPayment()
  router.push("/menu")
}

// ── Teks & warna panel ───────────────────────────────────────────────────────
const phaseTitle = computed(() => ({
  starting: "Menyiapkan Pembayaran",
  waiting:  "Menunggu Pembayaran",
  paid:     "Pembayaran Berhasil",
  failed:   "Pembayaran Gagal",
  pending:  "Belum Terkonfirmasi",
}[payment.value?.phase] || ""))

const phaseDescription = computed(() => {
  const p = payment.value
  if (!p) return ""
  switch (p.phase) {
    case "starting": return "Membuka halaman pembayaran QRIS..."
    case "waiting":  return "Selesaikan pembayaran di popup, lalu tunggu konfirmasi. Jangan tutup halaman ini."
    case "paid":     return "Pesananmu sudah masuk dan sedang diproses. Terima kasih!"
    case "failed":   return "Pembayaran gagal atau kedaluwarsa, jadi pesanan ini dibatalkan. Kamu bisa pesan ulang dari menu."
    default:         return p.message
  }
})

const phaseIconClass = computed(() => ({
  paid:    "bg-emerald-400/10 border-emerald-400/30",
  failed:  "bg-[#EE0000]/10 border-[#EE0000]/30",
  pending: "bg-[#FFF500]/10 border-[#FFF500]/30",
}[payment.value?.phase] || "bg-white/[0.04] border-white/[0.08]"))

// ══════════════════════════════════════════════════════════════════════════════
// CHECKOUT
// ══════════════════════════════════════════════════════════════════════════════
const isCheckoutDisabled = computed(() => {
  if (!isStoreOpen.value) return true
  if (cartStore.isEmpty || !isNameValid.value || !isPhoneValid.value || isProcessing.value) return true
  if (paymentMethod.value === "gateway" && gatewayUnavailable.value) return true
  return false
})

const ctaLabel = computed(() => {
  if (isProcessing.value) return "Memproses..."
  return paymentMethod.value === "gateway" ? "Bayar Sekarang" : "Buat Pesanan"
})

// ── WhatsApp ─────────────────────────────────────────────────────────────────
// Pesan dibangun SEBELUM keranjang dikosongkan, lalu dikirim lewat tombol di panel:
// setelah pembayaran terkonfirmasi (online) atau setelah pesanan Cash dibuat.
// "Pedas · Extra keju" dari pilihan opsi item keranjang ("" kalau tidak ada).
const optionTextOf = (item) => (item.optionDetails || []).map((d) => d.label).join(" · ")

const buildWaMessage = (orderNumber, paymentLabel) => {
  const bundleText = cartStore.bundleLines.map((line) => {
    const inside = line.contents.map((c) => `${c.quantity * line.quantity}× ${c.name}`).join(", ")
    return `   • Paket ${line.name} x${line.quantity} — Rp ${(Number(line.price) * line.quantity).toLocaleString("id-ID")}\n     🔸 ${inside}`
  })
  const itemsText = [...bundleText, ...Object.values(cartStore.cart)
    .map((item) => {
      const line = `   • ${item.name} x${item.quantity} — Rp ${(Number(item.price) * item.quantity).toLocaleString("id-ID")}`
      const optionText = optionTextOf(item)
      return line + (optionText ? `\n     🔸 ${optionText}` : "") + (item.notes ? `\n     📋 ${item.notes}` : "")
    })]
    .join("\n")

  const promoLine = appliedPromo.value
    ? `Diskon Promo (${appliedPromo.value.code}): -Rp ${appliedPromo.value.discount_amount.toLocaleString("id-ID")}\n`
    : ""

  const rewardLine = selectedRewards.value.length
    ? selectedRewards.value
        .map((r) => `   🎁 ${r.menu_name} (tukar ${r.point_cost.toLocaleString("id-ID")} poin)`)
        .join("\n") + "\n"
    : ""

  return (
    `*ORDER BARU - MASASHIMURA*\n` +
    `===========================\n` +
    `No. Order  : *#${orderNumber}*\n` +
    `Nama       : ${name.value}\n` +
    `WhatsApp   : ${phone.value}\n` +
    `Pembayaran : ${paymentLabel}\n` +
    `===========================\n` +
    `*Pesanan:*\n${itemsText}\n` +
    `===========================\n` +
    `${promoLine}` +
    `${rewardLine}` +
    `*TOTAL: Rp ${finalTotal.value.toLocaleString("id-ID")}*\n` +
    `===========================\n` +
    `Mohon segera diproses, terima kasih!`
  )
}

const openWhatsApp = (message) => {
  // Ambil nomor dinamis; fallback ke env var kalau belum ke-fetch
  const targetNumber = adminWhatsapp.value
    || import.meta.env.VITE_ADMIN_WHATSAPP
    || ""

  if (!targetNumber) {
    toast.error("Nomor WhatsApp admin belum dikonfigurasi")
    return false
  }

  window.open(`https://wa.me/${targetNumber}?text=${encodeURIComponent(message)}`, "_blank")
  return true
}

// Ringkasan item untuk panel pembayaran (diambil SEBELUM keranjang dikosongkan).
const snapshotItems = () => [
  ...cartStore.bundleLines.map((line) => ({
    name:       `Paket ${line.name}`,
    quantity:   line.quantity,
    price:      Number(line.price) || 0,   // harga satuan paket
    optionText: line.contents.map((c) => `${c.quantity}× ${c.name}`).join(" · "),
  })),
  ...Object.values(cartStore.cart).map((item) => ({
    name:       item.name,
    quantity:   item.quantity,
    price:      Number(item.price) || 0,   // harga satuan termasuk add-on
    optionText: optionTextOf(item),
  })),
]

// ── Reset form setelah order berhasil dibuat ─────────────────────────────────
const resetForm = () => {
  cartStore.clearCart()
  name.value  = ""
  phone.value = ""
  nameTouched.value  = false
  phoneTouched.value = false
  promoBoxRef.value?.removePromo()
  resetMember()
}

const checkout = async () => {
  // HARUS paling awal dan sebelum `await` apa pun: browser (terutama iOS Safari)
  // hanya mengizinkan audio dibuka di dalam gesture tap. Kalau ditaruh setelah
  // await, suara sukses nanti diblok browser.
  unlockPaymentAudio()

  // Dobel klik / ketuk cepat tidak boleh membuat dua order.
  if (isProcessing.value) return

  if (!isNameValid.value) {
    nameTouched.value = true
    return toast.error(nameError(name.value))
  }
  if (!isPhoneValid.value) {
    phoneTouched.value = true
    return toast.error(phoneError(phone.value))
  }

  const isGateway = paymentMethod.value === "gateway"
  if (isGateway && finalTotal.value <= 0) {
    return toast.error("Total Rp0, pakai metode Cash.")
  }

  // Dikunci SEBELUM await pertama (fetchSettings di bawah), bukan sesudahnya.
  isProcessing.value = true
  try {
    // Guard nomor admin hanya untuk Cash (tombol WhatsApp di panel butuh nomor ini).
    // Untuk online, WA cuma tombol opsional setelah bayar, jadi tidak memblokir.
    if (!isGateway && !adminWhatsapp.value) {
      await fetchSettings()
      if (!adminWhatsapp.value) {
        toast.error("Nomor WhatsApp admin belum dikonfigurasi. Hubungi admin.")
        return
      }
    }

    // Pastikan Snap bisa dimuat SEBELUM order dibuat, supaya tidak ada
    // order "nyangkut" yang tidak bisa dibayar karena script gagal dimuat.
    if (isGateway) {
      try {
        await loadSnap()
      } catch {
        toast.error("Pembayaran online belum bisa dipakai saat ini. Coba lagi atau pilih Cash.")
        return
      }
    }

    const orderData = {
      source:         "web",
      customer:       { phone: phone.value, name: cleanName(name.value) },
      payment_method: paymentMethod.value,
      promo_id:          appliedPromo.value?.promo_id || null,
      redeem_reward_ids: selectedRewardIds.value,
      // PIN hanya dikirim saat menukar poin; server memverifikasi ulang (kunci 5x salah).
      ...(selectedRewardIds.value.length ? { member_pin: memberPin.value } : {}),
      // Harga tidak dikirim: backend selalu pakai harga dari database.
      bundles: cartStore.bundleLines.map((line) => ({ bundle_id: line.id, quantity: line.quantity })),
      items: Object.values(cartStore.cart).map((item) => ({
        menu_id:  item.id,
        quantity: item.quantity,
        notes:    item.notes || "",
        options:  item.options || {},   // server memvalidasi & menghitung harga add-on sendiri
      })),
    }

    const res         = await orderAPI.create(orderData)
    const orderNumber = res.data?.order_number ?? res.data?.id

    // ── QRIS Online ──
    if (isGateway) {
      if (!res.data?.order_number) {
        // Order sudah ada di server: kosongkan form supaya klik ulang tidak membuat order ganda.
        resetForm()
        toast.error("Order dibuat, tapi nomor order tidak diterima. Hubungi admin.")
        return
      }

      payment.value = {
        orderNumber,
        total:     Number(res.data?.total_price ?? finalTotal.value),
        waMessage: buildWaMessage(orderNumber, "QRIS Online (sudah dibayar)"),
        items:     snapshotItems(),
        createdAt: Date.now(),
        message:   "",
        phase:     "starting",
      }
      persistPayment(payment.value)   // supaya refresh tidak menghilangkan status pembayaran
      resetForm()
      await openSnap()
      return
    }

    // ── Cash ──
    // Semua data panel diambil SEBELUM resetForm() (keranjang, promo, dan poin dikosongkan di sana).
    cashDone.value = {
      orderNumber,
      total:     Number(res.data?.total_price ?? finalTotal.value),
      waMessage: buildWaMessage(orderNumber, "Cash (bayar di toko)"),
      items:     snapshotItems(),
    }
    resetForm()
    toast.success("Pesanan berhasil dibuat!")
    window.scrollTo({ top: 0, behavior: "smooth" })
  } catch (error) {
    const message = error.response?.data?.detail || error.response?.data?.error || "Koneksi terputus"
    // PIN ditolak server (mis. PIN diganti admin): verifikasi lama tidak berlaku, minta masukkan ulang.
    if (error.response?.data?.pin_error) resetMember()

    // Keranjang tersimpan di localStorage, jadi bisa berisi menu yang belakangan jadi
    // secret/nonaktif/habis atau opsinya sudah diubah admin. Server menolak dengan 400 —
    // tawarkan kosongkan keranjang supaya customer tidak buntu.
    const cartProblem = error.response?.status === 400 && /keranjang|opsi|pilih|habis/i.test(message)
    toast.error(
      "Gagal memproses pesanan: " + message,
      cartProblem
        ? { action: { label: "Kosongkan keranjang", onClick: () => { cartStore.clearCart(); router.push("/menu") } } }
        : undefined
    )
  } finally {
    isProcessing.value = false
  }
}

// ── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(() => {
  fetchSettings()
  restorePendingPayment()
})

onBeforeUnmount(() => {
  stopPolling()
})
</script>

<style scoped>
/*
  Palet (sama dengan Home, Menu, dan Lokasi & Kontak)
  Warm black #080808 · Surface #141414 · Washi #FAFAFA
  Crimson #EE0000 (aksi) · Champagne #FFF500 (detail premium)
  Hijau hanya untuk status sukses dan tombol WhatsApp.
*/

.page-glow {
  background:
    radial-gradient(60% 70% at 15% 0%, rgba(238,0,0, 0.14), transparent 70%),
    radial-gradient(40% 50% at 90% 10%, rgba(255,245,0, 0.06), transparent 70%);
}

.card {
  border-radius: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.07);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.045), rgba(255, 255, 255, 0.012)), #141414;
  padding: 1.5rem;
}
@media (min-width: 640px) {
  .card { padding: 1.75rem; }
}

.card-item {
  border-radius: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.07);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.01)), #141414;
  padding: 1rem;
}
@media (min-width: 640px) {
  .card-item { padding: 1.25rem; }
}

.summary-box {
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.07);
  background: rgba(255, 255, 255, 0.025);
  padding: 1rem 1.125rem;
}

/* Input: 16px di HP supaya iOS tidak zoom otomatis */
.field {
  width: 100%;
  height: 3rem;
  border-radius: 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: #0D0D0D;
  padding: 0 1rem;
  font-size: 1rem;
  color: #FAFAFA;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
@media (min-width: 640px) {
  .field { font-size: 0.875rem; }
}
.field::placeholder { color: #737373; }
.field:hover { border-color: rgba(255, 255, 255, 0.2); }
.field:focus {
  border-color: rgba(255,245,0, 0.6);
  box-shadow: 0 0 0 3px rgba(255,245,0, 0.12);
}

.btn-primary,
.btn-ghost,
.btn-wa {
  display: flex;
  width: 100%;
  min-height: 3rem;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  border-radius: 9999px;
  padding: 0.75rem 1.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  transition: all 0.2s ease;
}
.btn-primary {
  background: #EE0000;
  color: #fff;
}
.btn-primary:hover:not(:disabled) {
  background: #C20000;
  box-shadow: 0 8px 24px -8px rgba(238,0,0, 0.6);
}
.btn-primary:disabled {
  cursor: not-allowed;
  opacity: 0.4;
}
.btn-ghost {
  border: 1px solid rgba(255, 255, 255, 0.16);
  color: #FAFAFA;
}
.btn-ghost:hover {
  border-color: rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.05);
}
.btn-wa {
  background: #1FA855;
  color: #fff;
}
.btn-wa:hover {
  background: #1A9149;
}
.btn-primary:active:not(:disabled),
.btn-ghost:active,
.btn-wa:active {
  transform: scale(0.98);
}

a:focus-visible,
button:focus-visible,
input:focus-visible {
  outline: 2px solid #FFF500;
  outline-offset: 3px;
}
.field:focus-visible { outline: none; }
.field-invalid,
.field-invalid:hover,
.field-invalid:focus {
  border-color: rgba(242, 112, 122, 0.7);
}
.field-invalid:focus {
  box-shadow: 0 0 0 3px rgba(242, 112, 122, 0.14);
}

@media (prefers-reduced-motion: reduce) {
  .animate-spin { animation-duration: 2s; }
}
</style>