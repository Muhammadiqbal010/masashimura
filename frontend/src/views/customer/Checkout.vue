<template>
  <div class="min-h-screen bg-[#060606] text-white pt-24 pb-24 font-inter">
    <div class="max-w-6xl mx-auto px-4 sm:px-8 py-6">

      <!-- Header -->
      <div class="mb-10 space-y-1">
        <div class="flex items-center gap-2">
          <span class="w-4 h-px bg-[#DC2626]"></span>
          <span class="font-mono text-[9px] tracking-[0.35em] text-[#DC2626] uppercase">Checkout</span>
        </div>
        <h1 class="font-sora text-3xl sm:text-4xl font-extrabold uppercase tracking-tight text-white">
          Pesanan Lo
        </h1>
      </div>

      <!-- ══ PANEL STATUS PEMBAYARAN ONLINE (muncul setelah order gateway dibuat) ══ -->
      <div
        v-if="payment"
        class="max-w-md mx-auto bg-[#0d0d0d] border border-white/[0.06] rounded-2xl p-6 sm:p-8 text-center space-y-5"
      >
        <div
          class="mx-auto w-14 h-14 rounded-2xl border flex items-center justify-center"
          :class="phaseIconClass"
        >
          <div
            v-if="payment.phase === 'starting' || payment.phase === 'waiting'"
            class="w-6 h-6 border-2 border-white/20 border-t-white rounded-full animate-spin"
          ></div>
          <Check v-else-if="payment.phase === 'paid'" :size="24" class="text-emerald-400" />
          <X v-else-if="payment.phase === 'failed'" :size="24" class="text-red-400" />
          <Clock v-else :size="24" class="text-amber-400" />
        </div>

        <div class="space-y-1.5">
          <h2 class="font-sora text-lg font-extrabold uppercase tracking-tight text-white">{{ phaseTitle }}</h2>
          <p class="font-mono text-[11px] text-zinc-500 leading-relaxed">{{ phaseDescription }}</p>
        </div>

        <div class="bg-white/[0.03] border border-white/[0.06] rounded-xl p-4 space-y-2 text-left">
          <div class="flex justify-between items-center">
            <span class="font-mono text-[10px] uppercase tracking-widest text-zinc-600">No. Order</span>
            <span class="font-mono text-[12px] text-white">#{{ payment.orderNumber }}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="font-mono text-[10px] uppercase tracking-widest text-zinc-600">Total</span>
            <span class="font-mono text-[14px] font-bold text-amber-400">{{ formatPrice(payment.total) }}</span>
          </div>
        </div>

        <div class="space-y-2">
          <!-- Berhasil -->
          <template v-if="payment.phase === 'paid'">
            <button
              v-if="payment.waMessage"
              type="button"
              class="w-full py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-sora text-[11px] font-bold uppercase tracking-widest transition-all duration-200 active:scale-[0.98]"
              @click="openWhatsApp(payment.waMessage)"
            >
              Kabari Admin via WhatsApp
            </button>
            <button
              type="button"
              class="w-full py-3.5 rounded-xl border border-white/[0.1] text-zinc-400 hover:text-white hover:border-white/20 font-sora text-[11px] font-bold uppercase tracking-widest transition-all duration-200"
              @click="finishPayment"
            >
              Selesai
            </button>
          </template>

          <!-- Gagal / kedaluwarsa -->
          <template v-else-if="payment.phase === 'failed'">
            <button
              type="button"
              class="w-full py-3.5 rounded-xl bg-[#DC2626] hover:bg-red-700 text-white font-sora text-[11px] font-bold uppercase tracking-widest transition-all duration-200 active:scale-[0.98]"
              @click="backToMenu"
            >
              Kembali ke Menu
            </button>
          </template>

          <!-- Belum terkonfirmasi -->
          <template v-else-if="payment.phase === 'pending'">
            <button
              type="button"
              class="w-full py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-sora text-[11px] font-bold uppercase tracking-widest transition-all duration-200 active:scale-[0.98]"
              @click="openSnap"
            >
              Lanjutkan Bayar
            </button>
            <button
              type="button"
              class="w-full py-3.5 rounded-xl border border-white/[0.1] text-zinc-400 hover:text-white hover:border-white/20 font-sora text-[11px] font-bold uppercase tracking-widest transition-all duration-200"
              @click="onCheckStatusClick"
            >
              Cek Status
            </button>
            <p class="font-mono text-[9px] text-zinc-700 pt-1">
              Order otomatis dibatalkan kalau tidak dibayar dalam 30 menit.
            </p>
          </template>
        </div>
      </div>

      <!-- ══ FORM CHECKOUT NORMAL ══ -->
      <div v-else class="grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-6 lg:gap-8 items-start">

        <!-- ── KIRI: List Item ──────────────────────────────────── -->
        <div class="space-y-3">

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
        </div>

        <!-- ── KANAN: Form & Payment ────────────────────────────── -->
        <div class="bg-[#0d0d0d] border border-white/[0.06] rounded-2xl p-5 sm:p-6 sticky top-24 space-y-5">

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
                :disabled="gatewayUnavailable"
                @click="selectPayment('gateway')"
                :class="[
                  'py-3 rounded-xl text-[10px] font-sora font-bold uppercase tracking-widest border transition-all duration-150 disabled:opacity-30 disabled:cursor-not-allowed',
                  paymentMethod === 'gateway'
                    ? 'bg-[#DC2626] border-[#DC2626] text-white'
                    : 'bg-white/[0.03] border-white/[0.08] text-zinc-600 hover:text-zinc-300 hover:border-white/[0.15]'
                ]"
              >
                QRIS Online
              </button>
            </div>
            <p class="font-mono text-[9px] text-zinc-700 leading-relaxed pt-0.5">
              <template v-if="paymentMethod === 'cash'">
                Bayar langsung di toko. Kasir yang mengonfirmasi pembayaranmu.
              </template>
              <template v-else>
                Bayar lewat QRIS di popup Midtrans. Pesanan diproses setelah pembayaran terkonfirmasi otomatis.
              </template>
            </p>
            <p v-if="gatewayUnavailable && !cartStore.isEmpty" class="font-mono text-[9px] text-amber-600">
              Total Rp0 (semua item tukar poin), pembayaran online tidak diperlukan. Pakai Cash.
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
import { unlockPaymentAudio, playPaymentSuccess } from "@/utils/paymentSuccessSound"

const cartStore     = useCartStore()
const router        = useRouter()

const name            = ref("")
const phone           = ref("")
const paymentMethod   = ref("cash")   // "cash" | "gateway" (Midtrans)
const isProcessing    = ref(false)
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

// Total setelah dikurangi diskon promo (reward poin gratis Rp0, dihandle backend).
// Ini cuma estimasi tampilan; nominal sebenarnya selalu dihitung ulang di backend.
const finalTotal = computed(() => {
  const promoDiscount = appliedPromo.value?.discount_amount || 0
  return Math.max(cartStore.totalPrice - promoDiscount, 0)
})

const onPromoApplied = (promo) => { appliedPromo.value = promo }
const onPromoRemoved  = () => { appliedPromo.value = null }

// ── Admin WhatsApp (dinamis dari API / localStorage) ──────────────────────────
const { adminWhatsapp, isStoreOpen, fetchSettings } = useStoreSettings()
onMounted(() => fetchSettings())

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

onBeforeUnmount(() => {
  clearTimeout(debounceTimer)
  stopPolling()
})

// ══════════════════════════════════════════════════════════════════════════════
// MIDTRANS SNAP
// ══════════════════════════════════════════════════════════════════════════════
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

// ── Metode pembayaran ─────────────────────────────────────────────────────────
// Order Rp0 (semua item tukar poin) ditolak endpoint pembayaran, jadi QRIS dimatikan.
const gatewayUnavailable = computed(() => finalTotal.value <= 0)

const selectPayment = (method) => {
  if (method === "gateway" && gatewayUnavailable.value) return
  paymentMethod.value = method
}

watch(gatewayUnavailable, (unavailable) => {
  if (unavailable && paymentMethod.value === "gateway") {
    paymentMethod.value = "cash"
    if (!cartStore.isEmpty && !payment.value) {
      toast.info("Total Rp0, pembayaran dialihkan ke Cash.")
    }
  }
})

// ── Status pembayaran online ──────────────────────────────────────────────────
// payment = null          → form checkout biasa
// payment = { orderNumber, total, waMessage, message, phase }
//   phase: "starting" | "waiting" | "paid" | "failed" | "pending"
const payment = ref(null)

const POLL_INTERVAL_MS   = 2000
const POLL_MAX_ATTEMPTS  = 30   // ≈ 60 detik

let pollRun = 0
const stopPolling = () => { pollRun++ }

// Sumber kebenaran = status di backend (diubah webhook Midtrans), BUKAN callback Snap.
// Callback Snap di browser bisa terlewat (tab ditutup, internet putus).
const pollStatus = async (maxAttempts = POLL_MAX_ATTEMPTS) => {
  const p = payment.value
  if (!p) return

  stopPolling()
  const run = pollRun
  p.phase = "waiting"
  p.message = ""

  for (let i = 0; i < maxAttempts; i++) {
    if (run !== pollRun) return
    try {
      const { data } = await paymentAPI.getStatus(p.orderNumber)
      if (run !== pollRun) return

      if (data.payment_status === "paid") {
        p.phase = "paid"
        // Suara hanya dibunyikan setelah backend mengonfirmasi lunas,
        // supaya customer tidak pernah dapat "sukses" palsu.
        playPaymentSuccess()
        toast.success("Pembayaran berhasil!")
        return
      }
      if (data.payment_status === "void" || data.status === "cancelled") {
        p.phase = "failed"
        return
      }
    } catch {
      // koneksi putus sebentar, lanjut coba lagi
    }
    if (i < maxAttempts - 1) {
      await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS))
    }
  }

  if (run === pollRun) {
    p.phase = "pending"
    p.message =
      "Pembayaran belum terkonfirmasi. Kalau kamu sudah membayar, tunggu beberapa detik lalu klik Cek Status."
  }
}

// Tombol "Cek Status" = tap user, jadi sekalian buka kunci audio.
const onCheckStatusClick = () => {
  unlockPaymentAudio()
  pollStatus(5)
}

// Minta token (token yang sama dipakai ulang backend) lalu buka popup Snap.
// Fungsi ini tidak pernah throw; error ditampilkan lewat panel.
const openSnap = async () => {
  const p = payment.value
  if (!p) return

  // Aman dipanggil berulang. Penting kalau dipicu dari tombol "Lanjutkan Bayar".
  unlockPaymentAudio()

  stopPolling()
  p.phase = "starting"
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
      onError:   () => { handled = true; pollStatus(3) },
      // Popup ditutup tanpa menyelesaikan: cek sebentar, bisa jadi sudah bayar lalu menutup.
      onClose:   () => { if (!handled) pollStatus(2) },
    })
  } catch (err) {
    p.phase = "pending"
    p.message =
      err.response?.data?.detail ||
      "Gagal membuka pembayaran. Cek koneksi lalu coba lagi."
  }
}

const finishPayment = () => {
  stopPolling()
  payment.value = null
  router.push("/")
}

const backToMenu = () => {
  stopPolling()
  payment.value = null
  router.push("/menu")
}

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
  paid:    "bg-emerald-500/10 border-emerald-500/30",
  failed:  "bg-red-500/10 border-red-500/30",
  pending: "bg-amber-500/10 border-amber-500/30",
}[payment.value?.phase] || "bg-white/[0.04] border-white/[0.08]"))

// ── Checkout disabled ─────────────────────────────────────────────────────────
const isCheckoutDisabled = computed(() => {
  if (!isStoreOpen.value) return true
  if (cartStore.isEmpty || !phone.value || !name.value || isProcessing.value) return true
  if (paymentMethod.value === "gateway" && gatewayUnavailable.value) return true
  return false
})

const ctaLabel = computed(() => {
  if (isProcessing.value) return "Memproses..."
  return paymentMethod.value === "gateway" ? "Bayar Sekarang" : "Buat Pesanan"
})

// ── WhatsApp ──────────────────────────────────────────────────────────────────
// Pesan dibangun SEBELUM keranjang dikosongkan, lalu dikirim sekarang (cash)
// atau lewat tombol setelah pembayaran terkonfirmasi (online).
const buildWaMessage = (orderNumber, paymentLabel) => {
  const itemsText = Object.values(cartStore.cart)
    .map((item) => {
      const line = `   • ${item.name} x${item.quantity} — Rp ${(Number(item.price_web) * item.quantity).toLocaleString("id-ID")}`
      return item.notes ? `${line}\n     📋 ${item.notes}` : line
    })
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

// ── Reset form setelah order berhasil dibuat ──────────────────────────────────
const resetForm = () => {
  cartStore.clearCart()
  name.value  = ""
  phone.value = ""
  promoBoxRef.value?.removePromo()
  resetPointRewards()
}

// ── Checkout ──────────────────────────────────────────────────────────────────
const checkout = async () => {
  // HARUS paling awal dan sebelum `await` apa pun: browser (terutama iOS Safari)
  // hanya mengizinkan audio dibuka di dalam gesture tap. Kalau ditaruh setelah
  // await, suara sukses nanti diblok browser.
  unlockPaymentAudio()

  if (!name.value)  return toast.error("Mohon isi nama kamu")
  if (!phone.value) return toast.error("Mohon isi nomor WhatsApp")

  const isGateway = paymentMethod.value === "gateway"
  if (isGateway && finalTotal.value <= 0) {
    return toast.error("Total Rp0, pakai metode Cash.")
  }

  // Guard nomor admin hanya untuk Cash (WA langsung dikirim).
  // Untuk online, WA cuma tombol opsional setelah bayar, jadi tidak memblokir.
  if (!isGateway && !adminWhatsapp.value) {
    await fetchSettings()
    if (!adminWhatsapp.value) {
      toast.error("Nomor WhatsApp admin belum dikonfigurasi. Hubungi admin.")
      return
    }
  }

  isProcessing.value = true
  try {
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
      customer:       { phone: phone.value, name: name.value },
      payment_method: paymentMethod.value,
      promo_id:               appliedPromo.value?.promo_id || null,
      redeem_reward_ids:      selectedRewardIds.value,
      // Harga tidak dikirim: backend selalu pakai harga dari database.
      items: Object.values(cartStore.cart).map((item) => ({
        menu_id:  item.id,
        quantity: item.quantity,
        notes:    item.notes || "",
      })),
    }

    const res         = await orderAPI.create(orderData)
    const orderNumber = res.data?.order_number ?? res.data?.id

    if (isGateway) {
      if (!res.data?.order_number) {
        toast.error("Order dibuat, tapi nomor order tidak diterima. Hubungi admin.")
        return
      }

      const waMessage = buildWaMessage(orderNumber, "QRIS Online (sudah dibayar)")
      payment.value = {
        orderNumber,
        total: Number(res.data?.total_price ?? finalTotal.value),
        waMessage,
        message: "",
        phase: "starting",
      }
      resetForm()
      await openSnap()
      return
    }

    // ── Cash ──
    toast.success("Pesanan berhasil dibuat!")
    openWhatsApp(buildWaMessage(orderNumber, "Cash (bayar di toko)"))
    resetForm()
    router.push("/")
  } catch (error) {
    toast.error(
      "Gagal memproses pesanan: " +
      (error.response?.data?.detail || error.response?.data?.error || "Koneksi terputus")
    )
  } finally {
    isProcessing.value = false
  }
}
</script>