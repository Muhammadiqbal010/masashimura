<template>
  <div class="min-h-screen bg-[#060606] text-white pt-24 pb-24 font-inter">
    <div class="max-w-6xl mx-auto px-4 sm:px-8 py-6">

      <!-- Header -->
      <div class="mb-10 space-y-1">
        <div class="flex items-center gap-2">
          <span class="w-4 h-px bg-[#DC2626]"></span>
          <span class="font-mono text-[9px] tracking-[0.35em] text-[#DC2626] uppercase">
            {{ payment ? "Pembayaran" : "Checkout" }}
          </span>
        </div>
        <h1 class="font-sora text-3xl sm:text-4xl font-extrabold uppercase tracking-tight text-white">
          {{ payment ? "Bayar via QRIS" : "Pesanan Lo" }}
        </h1>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-6 lg:gap-8 items-start">

        <!-- ── KIRI: List Item ──────────────────────────────────── -->
        <div class="space-y-3">

          <!-- Mode pembayaran: ringkasan order yang sudah dibuat (read-only) -->
          <template v-if="payment">
            <div
              v-for="(item, idx) in payment.snapshot.items"
              :key="`snap-${idx}`"
              class="bg-[#0d0d0d] border border-white/[0.06] rounded-2xl p-4 sm:p-5 flex gap-4"
            >
              <div class="flex-1 min-w-0">
                <h4 class="font-sora text-[12px] font-bold uppercase tracking-wide text-white leading-tight">
                  {{ item.name }}
                </h4>
                <div class="flex items-center gap-1.5 mt-1">
                  <span class="font-mono text-[11px] text-zinc-600">{{ item.quantity }}x</span>
                  <span class="font-mono text-[11px] text-zinc-700">·</span>
                  <span class="font-mono text-[11px] text-zinc-600">{{ formatPrice(item.price) }}</span>
                </div>
                <p v-if="item.notes" class="mt-1.5 font-mono text-[10px] text-amber-500/70 italic">
                  "{{ item.notes }}"
                </p>
              </div>
              <div class="flex-shrink-0 text-right">
                <span class="font-mono text-[13px] font-bold text-amber-400">
                  {{ formatPrice(item.price * item.quantity) }}
                </span>
              </div>
            </div>
          </template>

          <template v-else>
            <!-- Empty -->
            <div
              v-if="cartStore.isEmpty"
              class="bg-[#0d0d0d] border border-white/[0.06] rounded-2xl p-16 text-center space-y-4"
            >
              <div class="w-12 h-12 rounded-2xl bg-[#111] border border-white/5 flex items-center justify-center mx-auto">
                <ShoppingCart :size="20" class="text-zinc-700" />
              </div>
              <p class="font-sora text-[11px] font-bold uppercase tracking-widest text-zinc-600">Keranjang masih kosong</p>
              <router-link
                to="/menu"
                class="inline-block font-mono text-[10px] tracking-widest text-[#DC2626] uppercase border border-[#DC2626]/30 hover:border-[#DC2626]/60 px-4 py-2 rounded-lg transition-all duration-150"
              >
                Lihat Menu
              </router-link>
            </div>

            <!-- Items -->
            <div
              v-for="item in Object.values(cartStore.cart)"
              :key="item.cartKey"
              class="bg-[#0d0d0d] border border-white/[0.06] rounded-2xl p-4 sm:p-5 flex gap-4 group"
            >
              <!-- Thumbnail -->
              <div class="w-16 h-16 sm:w-[72px] sm:h-[72px] rounded-xl overflow-hidden bg-[#111] border border-white/[0.06] flex-shrink-0">
                <img
                  v-if="item.image_url"
                  :src="getMediaUrl(item.image_url)"
                  class="w-full h-full object-cover pointer-events-none"
                  :alt="item.name"
                />
                <div v-else class="w-full h-full flex items-center justify-center text-zinc-800 text-xl">🍜</div>
              </div>

              <!-- Detail -->
              <div class="flex-1 min-w-0">
                <div class="flex items-start justify-between gap-3">
                  <h4 class="font-sora text-[12px] font-bold uppercase tracking-wide text-white leading-tight">
                    {{ item.name }}
                  </h4>
                  <button
                    @click="cartStore.removeFromCart(item.cartKey)"
                    class="flex-shrink-0 text-zinc-800 hover:text-red-500 transition-colors duration-150 p-0.5 -mt-0.5"
                  >
                    <X :size="13" />
                  </button>
                </div>

                <div class="flex items-center gap-1.5 mt-1">
                  <span class="font-mono text-[11px] text-zinc-600">{{ item.quantity }}x</span>
                  <span class="font-mono text-[11px] text-zinc-700">·</span>
                  <span class="font-mono text-[11px] text-zinc-600">
                    {{ formatPrice(item.price_web) }}
                  </span>
                </div>

                <p v-if="item.notes" class="mt-1.5 font-mono text-[10px] text-amber-500/70 italic">
                  "{{ item.notes }}"
                </p>
              </div>

              <!-- Subtotal -->
              <div class="flex-shrink-0 text-right">
                <span class="font-mono text-[13px] font-bold text-amber-400">
                  {{ formatPrice(item.price_web * item.quantity) }}
                </span>
              </div>
            </div>
          </template>
        </div>

        <!-- ── KANAN ────────────────────────────────────────────── -->
        <div class="bg-[#0d0d0d] border border-white/[0.06] rounded-2xl p-5 sm:p-6 sticky top-24 space-y-5">

          <!-- ═══ PANEL STATUS PEMBAYARAN (alur QRIS) ═══ -->
          <template v-if="payment">
            <div class="flex items-center gap-2 pb-1">
              <span class="w-3 h-px bg-zinc-700"></span>
              <span class="font-mono text-[9px] tracking-[0.3em] text-zinc-600 uppercase">
                Order #{{ payment.orderNumber }}
              </span>
            </div>

            <!-- PAID -->
            <div v-if="payStatus === 'paid'" class="space-y-4 text-center">
              <div class="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center mx-auto">
                <CheckCircle2 :size="26" class="text-emerald-400" />
              </div>
              <div class="space-y-1">
                <p class="font-sora text-sm font-bold uppercase tracking-widest text-emerald-400">Pembayaran Berhasil</p>
                <p class="font-mono text-[11px] text-zinc-500">
                  Pesanan lo sudah masuk dan sedang diproses.
                </p>
              </div>
              <button
                type="button"
                class="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-sora text-[11px] font-bold uppercase tracking-widest py-4 rounded-xl transition-all duration-200 active:scale-[0.98]"
                @click="notifyAdminViaWhatsApp"
              >
                Kabari admin via WhatsApp
              </button>
              <p class="font-mono text-[9px] text-zinc-700">
                Opsional. Pesanan tetap terlihat oleh admin walau lo nggak kirim WhatsApp.
              </p>
              <button
                type="button"
                class="w-full font-mono text-[10px] tracking-widest uppercase text-zinc-500 hover:text-zinc-300 border border-white/[0.08] hover:border-white/[0.15] py-3 rounded-xl transition-all duration-150"
                @click="leavePayment('/')"
              >
                Kembali ke Beranda
              </button>
            </div>

            <!-- VOID -->
            <div v-else-if="payStatus === 'void'" class="space-y-4 text-center">
              <div class="w-14 h-14 rounded-2xl bg-red-500/10 border border-red-500/30 flex items-center justify-center mx-auto">
                <XCircle :size="26" class="text-red-400" />
              </div>
              <div class="space-y-1">
                <p class="font-sora text-sm font-bold uppercase tracking-widest text-red-400">Pembayaran Gagal</p>
                <p class="font-mono text-[11px] text-zinc-500">
                  Pembayaran dibatalkan atau kedaluwarsa. Order ini tidak bisa dibayar lagi.
                </p>
              </div>
              <button
                type="button"
                class="w-full bg-[#DC2626] hover:bg-red-500 text-white font-sora text-[11px] font-bold uppercase tracking-widest py-4 rounded-xl transition-all duration-200 active:scale-[0.98]"
                @click="leavePayment('/menu')"
              >
                Pesan Lagi
              </button>
            </div>

            <!-- PENDING -->
            <div v-else class="space-y-4">
              <div class="flex flex-col items-center gap-3 py-2 text-center">
                <div
                  v-if="isPolling"
                  class="w-8 h-8 border-2 border-white/10 border-t-amber-400 rounded-full animate-spin"
                ></div>
                <div v-else class="w-12 h-12 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center">
                  <span class="text-lg">⏳</span>
                </div>
                <div class="space-y-1">
                  <p class="font-sora text-sm font-bold uppercase tracking-widest text-amber-400">
                    {{ isPolling ? "Mengecek Pembayaran..." : "Menunggu Pembayaran" }}
                  </p>
                  <p class="font-mono text-[11px] text-zinc-500">
                    Total {{ formatPrice(payment.snapshot.total) }}
                  </p>
                </div>
              </div>

              <p v-if="payError" class="font-mono text-[10px] text-red-500 text-center">{{ payError }}</p>

              <button
                type="button"
                class="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-30 disabled:cursor-not-allowed text-white font-sora text-[11px] font-bold uppercase tracking-widest py-4 rounded-xl transition-all duration-200 active:scale-[0.98]"
                :disabled="isOpeningSnap"
                @click="openSnap"
              >
                <span>{{ isOpeningSnap ? "Membuka..." : "Lanjutkan Bayar" }}</span>
                <ArrowRight v-if="!isOpeningSnap" :size="14" />
              </button>

              <button
                type="button"
                class="w-full font-mono text-[10px] tracking-widest uppercase text-zinc-500 hover:text-zinc-300 disabled:opacity-30 border border-white/[0.08] hover:border-white/[0.15] py-3 rounded-xl transition-all duration-150"
                :disabled="isPolling"
                @click="startPolling"
              >
                Cek Status
              </button>

              <p class="font-mono text-[9px] text-zinc-700 text-center">
                Sudah bayar tapi status belum berubah? Tunggu beberapa detik lalu tekan Cek Status.
                Order yang tidak dibayar akan dibatalkan otomatis sekitar 30 menit.
              </p>
            </div>
          </template>

          <!-- ═══ FORM CHECKOUT ═══ -->
          <template v-else>
            <!-- Section label -->
            <div class="flex items-center gap-2 pb-1">
              <span class="w-3 h-px bg-zinc-700"></span>
              <span class="font-mono text-[9px] tracking-[0.3em] text-zinc-600 uppercase">Data Pemesan</span>
            </div>

            <!-- Nama -->
            <div class="space-y-1.5">
              <label class="block font-mono text-[9px] uppercase tracking-widest text-zinc-600">Nama</label>
              <input
                v-model="name"
                type="text"
                class="w-full bg-white/[0.03] border border-white/[0.08] hover:border-white/[0.12] focus:border-[#DC2626]/50 rounded-xl px-4 py-3 text-[13px] text-white placeholder:text-zinc-700 outline-none transition-colors duration-150 font-inter"
                placeholder="Nama kamu"
              />
            </div>

            <!-- Nomor WA -->
            <div class="space-y-1.5">
              <label class="block font-mono text-[9px] uppercase tracking-widest text-zinc-600">Nomor WhatsApp</label>
              <input
                v-model="phone"
                type="tel"
                class="w-full bg-white/[0.03] border border-white/[0.08] hover:border-white/[0.12] focus:border-[#DC2626]/50 rounded-xl px-4 py-3 text-[13px] text-white placeholder:text-zinc-700 outline-none transition-colors duration-150 font-mono"
                placeholder="08123456789"
              />
              <p v-if="checkingLoyalty" class="font-mono text-[10px] text-zinc-700">Mengecek status member...</p>
              <div v-else-if="cartStore.isMember" class="flex items-center gap-1.5 mt-1">
                <span class="w-3 h-px bg-emerald-500/60"></span>
                <p class="font-mono text-[10px] text-emerald-500">
                  Member aktif · Poin saat ini: {{ cartStore.points }}
                </p>
              </div>
            </div>

            <!-- Metode Pembayaran -->
            <div class="space-y-1.5">
              <label class="block font-mono text-[9px] uppercase tracking-widest text-zinc-600">Pembayaran</label>
              <div class="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  @click="selectPayment('cash')"
                  :class="[
                    'py-3 rounded-xl text-[10px] font-sora font-bold uppercase tracking-widest border transition-all duration-150',
                    paymentMethod === 'cash'
                      ? 'bg-[#DC2626] border-[#DC2626] text-white'
                      : 'bg-white/[0.03] border-white/[0.08] text-zinc-600 hover:text-zinc-300 hover:border-white/[0.15]'
                  ]"
                >
                  Cash
                </button>
                <button
                  type="button"
                  :disabled="qrisDisabled"
                  @click="selectPayment('qris')"
                  :class="[
                    'py-3 rounded-xl text-[10px] font-sora font-bold uppercase tracking-widest border transition-all duration-150 disabled:opacity-30 disabled:cursor-not-allowed',
                    paymentMethod === 'qris'
                      ? 'bg-[#DC2626] border-[#DC2626] text-white'
                      : 'bg-white/[0.03] border-white/[0.08] text-zinc-600 hover:text-zinc-300 hover:border-white/[0.15]'
                  ]"
                >
                  QRIS
                </button>
              </div>
              <p v-if="paymentMethod === 'cash'" class="font-mono text-[9px] text-zinc-700">
                Bayar langsung di toko saat ambil pesanan.
              </p>
              <p v-else-if="paymentMethod === 'qris'" class="font-mono text-[9px] text-zinc-700">
                Popup QRIS terbuka setelah pesanan dibuat. Pembayaran dikonfirmasi otomatis.
              </p>
              <p v-if="qrisDisabled && !cartStore.isEmpty" class="font-mono text-[9px] text-zinc-700">
                QRIS tidak tersedia untuk total Rp0. Pilih Cash.
              </p>
            </div>

            <div class="border-t border-white/[0.05]"></div>

            <!-- Ringkasan Harga -->
            <div class="space-y-2.5">
              <div class="flex justify-between items-center">
                <span class="font-mono text-[11px] text-zinc-600">Subtotal</span>
                <span class="font-mono text-[11px] text-zinc-400">{{ formatPrice(cartStore.subtotal) }}</span>
              </div>

              <!-- Kode Promo -->
              <PromoCodeBox
                ref="promoBoxRef"
                :subtotal="cartStore.totalPrice"
                @applied="onPromoApplied"
                @removed="onPromoRemoved"
              />

              <div v-if="appliedPromo" class="flex justify-between items-center">
                <span class="font-mono text-[11px] text-emerald-600">Diskon Promo ({{ appliedPromo.code }})</span>
                <span class="font-mono text-[11px] text-emerald-500">−{{ formatPrice(appliedPromo.discount_amount) }}</span>
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
                class="flex justify-between items-center"
              >
                <span class="font-mono text-[11px] text-amber-500">🎁 {{ reward.menu_name }} (gratis)</span>
                <span class="font-mono text-[11px] text-zinc-600">−{{ reward.point_cost.toLocaleString("id-ID") }} poin</span>
              </div>

              <div class="flex justify-between items-center pt-2 border-t border-white/[0.05]">
                <span class="font-mono text-[10px] tracking-widest text-zinc-600 uppercase">Total Bayar</span>
                <span class="font-mono text-xl font-bold text-amber-400 tracking-tight leading-none">
                  {{ formatPrice(finalTotal) }}
                </span>
              </div>
            </div>

            <!-- CTA -->
            <button
              class="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-30 disabled:cursor-not-allowed text-white font-sora text-[11px] font-bold uppercase tracking-widest py-4 rounded-xl transition-all duration-200 active:scale-[0.98]"
              @click="checkout"
              :disabled="isCheckoutDisabled"
            >
              <span>{{ ctaLabel }}</span>
              <ArrowRight v-if="!isProcessing" :size="14" />
            </button>
          </template>
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
import { X, ShoppingCart, ArrowRight, CheckCircle2, XCircle } from "lucide-vue-next"
import { useStoreSettings } from "@/composables/useStoreSettings"
import PromoCodeBox from "@/components/ui/PromoCodeBox.vue"
import PointRedeemBox from "@/components/ui/PointRedeemBox.vue"

const cartStore     = useCartStore()
const router        = useRouter()

const name          = ref("")
const phone         = ref("")
const paymentMethod = ref("cash")      // UI: "cash" | "qris"  (qris dikirim ke backend sebagai "gateway")
const isProcessing  = ref(false)
const checkingLoyalty = ref(false)

// ── Promo code ──────────────────────────────────────────────────────────────
const promoBoxRef  = ref(null)
const appliedPromo = ref(null)

// ── Tukar poin loyalty ───────────────────────────────────────────────────────
const pointsBalance     = ref(0)
const affordableRewards = ref([])
const lockedRewards     = ref([])
const selectedRewardIds = ref([])

const selectedRewards = computed(() =>
  affordableRewards.value.filter((r) => selectedRewardIds.value.includes(r.id))
)

const fetchPointRewards = async (phoneNumber) => {
  try {
    const { data } = await orderAPI.getAvailablePointRewards(phoneNumber)
    pointsBalance.value     = data.points ?? 0
    affordableRewards.value = data.affordable ?? []
    lockedRewards.value     = data.locked ?? []
  } catch (err) {
    console.error(err)
    pointsBalance.value = 0
    affordableRewards.value = []
    lockedRewards.value = []
  }
}

const resetPointRewards = () => {
  pointsBalance.value = 0
  affordableRewards.value = []
  lockedRewards.value = []
  selectedRewardIds.value = []
}

// Total setelah dikurangi diskon promo (reward poin gratis Rp0, dihandle backend)
const finalTotal = computed(() => {
  const promoDiscount = appliedPromo.value?.discount_amount || 0
  return Math.max(cartStore.totalPrice - promoDiscount, 0)
})

const onPromoApplied = (promo) => { appliedPromo.value = promo }
const onPromoRemoved  = () => { appliedPromo.value = null }

// ── Admin WhatsApp (dinamis dari API / localStorage) ──────────────────────────
const { adminWhatsapp, isStoreOpen, fetchSettings } = useStoreSettings()

const formatPrice = (p) =>
  new Intl.NumberFormat("id-ID", {
    style: "currency", currency: "IDR", minimumFractionDigits: 0,
  }).format(p || 0)

// ── Loyalty ───────────────────────────────────────────────────────────────────
let debounceTimer = null
watch(phone, (newPhone) => {
  clearTimeout(debounceTimer)

  if (!newPhone || newPhone.length < 9) {
    cartStore.isMember = false
    cartStore.points = 0
    resetPointRewards()
    return
  }

  checkingLoyalty.value = true
  debounceTimer = setTimeout(async () => {
    await Promise.all([
      cartStore.checkLoyalty(newPhone),
      fetchPointRewards(newPhone),
    ])
    checkingLoyalty.value = false
  }, 600)
})

// ── Metode pembayaran ─────────────────────────────────────────────────────────
// Backend menolak order gateway dengan total 0 (tidak bisa dibayar siapa pun),
// jadi QRIS dimatikan saat total Rp0.
const qrisDisabled = computed(() => finalTotal.value <= 0)

const selectPayment = (method) => {
  if (method === "qris" && qrisDisabled.value) return
  paymentMethod.value = method
}

watch(qrisDisabled, (disabled) => {
  if (disabled && paymentMethod.value === "qris" && !payment.value) {
    paymentMethod.value = "cash"
  }
})

const isCheckoutDisabled = computed(() => {
  if (!isStoreOpen.value) return true
  if (cartStore.isEmpty || !phone.value || !name.value || isProcessing.value) return true
  if (paymentMethod.value === "qris" && qrisDisabled.value) return true
  return false
})

const ctaLabel = computed(() => {
  if (isProcessing.value) return "Memproses..."
  return paymentMethod.value === "qris" ? "Bayar Sekarang" : "Buat Pesanan"
})

// ── Midtrans Snap ─────────────────────────────────────────────────────────────
const MIDTRANS_CLIENT_KEY = import.meta.env.VITE_MIDTRANS_CLIENT_KEY || ""
// Key sandbox diawali "SB-Mid-client-", jadi URL snap.js ditentukan dari situ.
const SNAP_SRC = MIDTRANS_CLIENT_KEY.startsWith("SB-")
  ? "https://app.sandbox.midtrans.com/snap/snap.js"
  : "https://app.midtrans.com/snap/snap.js"

let snapScriptPromise = null
const loadSnap = () => {
  if (window.snap) return Promise.resolve()
  if (!MIDTRANS_CLIENT_KEY) {
    return Promise.reject(new Error("VITE_MIDTRANS_CLIENT_KEY belum diset"))
  }
  if (snapScriptPromise) return snapScriptPromise

  snapScriptPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script")
    script.src = SNAP_SRC
    script.setAttribute("data-client-key", MIDTRANS_CLIENT_KEY)
    script.async = true
    script.onload = () => resolve()
    script.onerror = () => {
      script.remove()
      snapScriptPromise = null // izinkan retry
      reject(new Error("Gagal memuat Midtrans Snap"))
    }
    document.head.appendChild(script)
  })
  return snapScriptPromise
}

// State panel pembayaran. `payment` terisi setelah order QRIS berhasil dibuat.
const payment      = ref(null)      // { orderNumber, snapshot }
const payStatus    = ref("pending") // "pending" | "paid" | "void" — selalu dari backend
const payError     = ref("")
const snapToken    = ref("")
const isOpeningSnap = ref(false)
const isPolling    = ref(false)

// Polling status: tiap 3 detik, maksimal 60 detik.
// Callback Snap (onSuccess/onPending/onError/onClose) TIDAK dipercaya,
// cuma dipakai sebagai pemicu polling. Sumber kebenaran = webhook di backend.
const POLL_INTERVAL_MS = 3000
const POLL_MAX_MS      = 60000
let pollTimer = null
let pollRun   = 0

const stopPolling = () => {
  pollRun++ // tick lama yang masih in-flight akan diabaikan
  clearTimeout(pollTimer)
  pollTimer = null
  isPolling.value = false
}

const startPolling = () => {
  if (!payment.value) return
  stopPolling()
  const run         = pollRun
  const orderNumber = payment.value.orderNumber
  const startedAt   = Date.now()
  isPolling.value   = true

  const tick = async () => {
    try {
      const { data } = await paymentAPI.getStatus(orderNumber)
      if (run !== pollRun) return

      payError.value = ""
      if (data.payment_status === "paid") {
        payStatus.value = "paid"
        stopPolling()
        toast.success("Pembayaran berhasil!")
        return
      }
      if (data.payment_status === "void") {
        payStatus.value = "void"
        stopPolling()
        return
      }
    } catch (err) {
      if (run !== pollRun) return
      console.error(err)
      payError.value = "Gagal mengecek status. Coba tekan Cek Status lagi."
    }

    if (Date.now() - startedAt >= POLL_MAX_MS) {
      stopPolling()
      return
    }
    pollTimer = setTimeout(tick, POLL_INTERVAL_MS)
  }

  tick()
}

const openSnap = async () => {
  if (!payment.value || isOpeningSnap.value || payStatus.value !== "pending") return
  isOpeningSnap.value = true
  payError.value = ""

  try {
    // Token yang sama dikembalikan backend kalau sudah pernah dibuat,
    // jadi "Lanjutkan bayar" aman dan tidak bikin transaksi dobel.
    if (!snapToken.value) {
      const { data } = await paymentAPI.createSnapToken(payment.value.orderNumber)
      if (!data?.token) throw new Error("Token pembayaran kosong")
      snapToken.value = data.token
    }

    await loadSnap()

    window.snap.pay(snapToken.value, {
      onSuccess: startPolling,
      onPending: startPolling,
      onError:   startPolling,
      onClose:   startPolling,
    })
  } catch (err) {
    console.error(err)
    const msg =
      err.response?.data?.detail ||
      err.response?.data?.error ||
      err.message ||
      "Gagal membuka pembayaran"
    payError.value = msg
    toast.error(msg)
    // Mungkin order sudah dibayar / berubah status; sinkronkan dari backend.
    startPolling()
  } finally {
    isOpeningSnap.value = false
  }
}

// ── WhatsApp ──────────────────────────────────────────────────────────────────
// Snapshot dibuat SEBELUM keranjang dikosongkan, supaya pesan WA tetap bisa
// dibuat setelah pembayaran selesai.
const makeSnapshot = (orderNumber) => ({
  orderNumber,
  name:  name.value,
  phone: phone.value,
  total: finalTotal.value,
  items: Object.values(cartStore.cart).map((item) => ({
    name:     item.name,
    quantity: item.quantity,
    price:    Number(item.price_web),
    notes:    item.notes || "",
  })),
  promo: appliedPromo.value
    ? { code: appliedPromo.value.code, discount_amount: appliedPromo.value.discount_amount }
    : null,
  rewards: selectedRewards.value.map((r) => ({
    menu_name:  r.menu_name,
    point_cost: r.point_cost,
  })),
})

const buildWhatsAppUrl = (snap, paymentLabel) => {
  const targetNumber = adminWhatsapp.value
    || import.meta.env.VITE_ADMIN_WHATSAPP
    || ""

  if (!targetNumber) return null

  const itemsText = snap.items
    .map((item) => {
      const line = `   • ${item.name} x${item.quantity} — Rp ${(item.price * item.quantity).toLocaleString("id-ID")}`
      return item.notes ? `${line}\n     📋 ${item.notes}` : line
    })
    .join("\n")

  const promoLine = snap.promo
    ? `Diskon Promo (${snap.promo.code}): -Rp ${snap.promo.discount_amount.toLocaleString("id-ID")}\n`
    : ""

  const rewardLine = snap.rewards.length
    ? snap.rewards
        .map((r) => `   🎁 ${r.menu_name} (tukar ${r.point_cost.toLocaleString("id-ID")} poin)`)
        .join("\n") + "\n"
    : ""

  const message =
    `*ORDER BARU - MASASHIMURA*\n` +
    `===========================\n` +
    `No. Order  : *#${snap.orderNumber}*\n` +
    `Nama       : ${snap.name}\n` +
    `WhatsApp   : ${snap.phone}\n` +
    `Pembayaran : ${paymentLabel}\n` +
    `===========================\n` +
    `*Pesanan:*\n${itemsText}\n` +
    `===========================\n` +
    `${promoLine}` +
    `${rewardLine}` +
    `*TOTAL: Rp ${snap.total.toLocaleString("id-ID")}*\n` +
    `===========================\n` +
    `Mohon segera diproses, terima kasih!`

  return `https://wa.me/${targetNumber}?text=${encodeURIComponent(message)}`
}

// Jalur Cash: dipanggil langsung setelah order dibuat.
const sendCashToWhatsApp = (snap) => {
  const url = buildWhatsAppUrl(snap, "Cash (bayar di toko)")
  if (!url) {
    toast.error("Nomor WhatsApp admin belum dikonfigurasi")
    return
  }
  window.open(url, "_blank")
}

// Jalur QRIS: dipanggil dari klik tombol user (bukan dari polling),
// supaya tidak diblok popup blocker.
const notifyAdminViaWhatsApp = () => {
  if (!payment.value) return
  const url = buildWhatsAppUrl(payment.value.snapshot, "QRIS (LUNAS via Midtrans)")
  if (!url) {
    toast.error("Nomor WhatsApp admin belum dikonfigurasi")
    return
  }
  window.open(url, "_blank")
}

// ── Reset & navigasi ──────────────────────────────────────────────────────────
const resetForm = () => {
  cartStore.clearCart()
  name.value  = ""
  phone.value = ""
  appliedPromo.value = null
  promoBoxRef.value?.removePromo()
  resetPointRewards()
}

const leavePayment = (path) => {
  stopPolling()
  payment.value   = null
  payStatus.value = "pending"
  snapToken.value = ""
  payError.value  = ""
  router.push(path)
}

// ── Checkout ──────────────────────────────────────────────────────────────────
const checkout = async () => {
  if (isProcessing.value) return
  if (!name.value)  return toast.error("Mohon isi nama kamu")
  if (!phone.value) return toast.error("Mohon isi nomor WhatsApp")

  const isOnline = paymentMethod.value === "qris"

  if (isOnline && qrisDisabled.value) {
    return toast.error("QRIS tidak tersedia untuk total Rp0. Pilih Cash.")
  }

  // Guard nomor admin hanya untuk Cash (WA langsung terkirim).
  // Jalur QRIS pakai tombol WA manual setelah bayar, jadi tidak diblok.
  if (!isOnline && !adminWhatsapp.value) {
    await fetchSettings()
    if (!adminWhatsapp.value && !import.meta.env.VITE_ADMIN_WHATSAPP) {
      toast.error("Nomor WhatsApp admin belum dikonfigurasi. Hubungi admin.")
      return
    }
  }

  isProcessing.value = true
  try {
    const orderData = {
      source:         "web",
      customer:       { phone: phone.value, name: name.value },
      payment_method: isOnline ? "gateway" : "cash",
      promo_id:               appliedPromo.value?.promo_id || null,
      promo_discount_amount:  appliedPromo.value?.discount_amount || 0,
      redeem_reward_ids:      selectedRewardIds.value,
      items: Object.values(cartStore.cart).map((item) => ({
        menu_id:  item.id,
        quantity: item.quantity,
        price:    item.price_web,
        notes:    item.notes || "",
      })),
    }

    const res         = await orderAPI.create(orderData)
    const orderNumber = res.data?.order_number ?? res.data?.id
    const snapshot    = makeSnapshot(orderNumber)

    if (!isOnline) {
      // ── Cash: order dibuat, WA langsung ke admin, selesai ──
      toast.success("Pesanan berhasil dibuat!")
      sendCashToWhatsApp(snapshot)
      resetForm()
      router.push("/")
      return
    }

    // ── QRIS: order sudah ada di server, keranjang dikosongkan ──
    if (!res.data?.order_number) {
      toast.error("Order dibuat, tapi nomor order tidak diterima. Hubungi admin.")
      resetForm()
      return
    }

    payment.value   = { orderNumber, snapshot }
    payStatus.value = "pending"
    payError.value  = ""
    snapToken.value = ""
    resetForm()

    toast.success("Pesanan dibuat. Silakan selesaikan pembayaran.")
    openSnap()
  } catch (error) {
    toast.error(
      "Gagal memproses pesanan: " +
      (error.response?.data?.detail || error.response?.data?.error || "Koneksi terputus")
    )
  } finally {
    isProcessing.value = false
  }
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────
onMounted(() => {
  fetchSettings()
  // Preload snap.js supaya popup terbuka cepat saat checkout.
  if (MIDTRANS_CLIENT_KEY) loadSnap().catch((err) => console.error(err))
})

onBeforeUnmount(() => {
  clearTimeout(debounceTimer)
  stopPolling()
})
</script>