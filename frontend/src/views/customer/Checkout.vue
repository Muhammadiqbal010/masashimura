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

      <div class="grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-6 lg:gap-8 items-start">

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
                @click="selectPayment('qris')"
                :class="[
                  'py-3 rounded-xl text-[10px] font-sora font-bold uppercase tracking-widest border transition-all duration-150',
                  paymentMethod === 'qris'
                    ? 'bg-[#DC2626] border-[#DC2626] text-white'
                    : 'bg-white/[0.03] border-white/[0.08] text-zinc-600 hover:text-zinc-300 hover:border-white/[0.15]'
                ]"
              >
                QRIS
              </button>
            </div>
          </div>

          <!-- QRIS Section -->
          <transition
            enter-active-class="transition-all duration-300 ease-out"
            enter-from-class="opacity-0 -translate-y-1"
            enter-to-class="opacity-100 translate-y-0"
            leave-active-class="transition-all duration-200 ease-in"
            leave-from-class="opacity-100"
            leave-to-class="opacity-0"
          >
            <div v-if="paymentMethod === 'qris'" class="space-y-4">

              <!-- QR Image -->
              <div class="bg-white rounded-2xl p-4 flex flex-col items-center gap-2">
                <span class="font-mono text-[9px] uppercase tracking-widest text-black/40">Scan untuk bayar</span>
                <img
                  src="https://res.cloudinary.com/dndonk7an/image/upload/v1782554914/qris_masashimura_v8yvxd.jpg"
                  alt="QRIS Masashimura"
                  class="w-full max-w-[200px] rounded-xl"
                />
                <p class="font-mono text-[9px] text-black/30 text-center">Bayar sesuai total, lalu upload bukti di bawah</p>
              </div>

              <!-- Upload Bukti -->
              <div class="space-y-1.5">
                <label class="block font-mono text-[9px] uppercase tracking-widest text-zinc-600">Bukti Pembayaran</label>

                <!-- Preview -->
                <div v-if="proofPreviewUrl" class="relative rounded-xl overflow-hidden border border-white/[0.06]">
                  <img :src="proofPreviewUrl" alt="Bukti Bayar" class="w-full object-cover max-h-44" />
                  <button
                    @click="clearProof"
                    class="absolute top-2 right-2 w-7 h-7 rounded-lg bg-black/70 text-white text-xs flex items-center justify-center hover:bg-[#DC2626] transition-colors duration-150"
                  >
                    <X :size="12" />
                  </button>
                  <div v-if="isUploadingProof" class="absolute inset-0 bg-black/60 flex flex-col items-center justify-center gap-2">
                    <div class="w-6 h-6 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                    <p class="font-mono text-[10px] text-white/60">Mengupload...</p>
                  </div>
                  <div v-else-if="proofCloudinaryUrl" class="absolute bottom-2 left-2 bg-emerald-500/90 text-white font-mono text-[9px] px-2 py-1 rounded-lg">
                    ✓ Terverifikasi
                  </div>
                </div>

                <!-- Drop zone -->
                <label
                  v-if="!proofPreviewUrl"
                  class="flex flex-col items-center justify-center gap-2 w-full border border-dashed border-white/[0.08] hover:border-[#DC2626]/40 rounded-xl py-6 cursor-pointer transition-all duration-150 group"
                >
                  <Upload :size="18" class="text-zinc-700 group-hover:text-zinc-500 transition-colors" />
                  <span class="font-mono text-[10px] text-zinc-700 group-hover:text-zinc-500 transition-colors">Klik untuk upload foto bukti</span>
                  <span class="font-mono text-[9px] text-zinc-800">JPG, PNG · Maks 5MB</span>
                  <input type="file" accept="image/*" class="hidden" @change="handleProofUpload" />
                </label>

                <p v-if="uploadError" class="font-mono text-[10px] text-red-500">{{ uploadError }}</p>
              </div>
            </div>
          </transition>

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
            <span>{{ isProcessing ? "Memproses..." : "Buat Pesanan" }}</span>
            <ArrowRight v-if="!isProcessing" :size="14" />
          </button>

          <p v-if="paymentMethod === 'qris' && !proofCloudinaryUrl && !cartStore.isEmpty" class="font-mono text-[9px] text-zinc-700 text-center -mt-2">
            Upload bukti bayar dulu sebelum buat pesanan
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue"
import { useRouter } from "vue-router"
import { useCartStore } from "@/stores/cart"
import { orderAPI, getMediaUrl } from "@/api"
import { toast } from "vue-sonner"
import { X, ShoppingCart, Upload, ArrowRight } from "lucide-vue-next"
import { useStoreSettings } from "@/composables/useStoreSettings"
import PromoCodeBox from "@/components/ui/PromoCodeBox.vue"
import PointRedeemBox from "@/components/ui/PointRedeemBox.vue"

const cartStore     = useCartStore()
const router        = useRouter()

const name          = ref("")
const phone         = ref("")
const paymentMethod = ref("cash")
const isProcessing  = ref(false)
const checkingLoyalty = ref(false)

const proofPreviewUrl    = ref("")
const proofCloudinaryUrl = ref("")
const isUploadingProof   = ref(false)
const uploadError        = ref("")

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
onMounted(() => fetchSettings())

const CLOUDINARY_CLOUD  = "dndonk7an"
const CLOUDINARY_PRESET = "masashimura_preset"
const CLOUDINARY_FOLDER = "bukti-qris"

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

onBeforeUnmount(() => clearTimeout(debounceTimer))

// ── Payment ───────────────────────────────────────────────────────────────────
const selectPayment = (method) => {
  paymentMethod.value = method
  if (method === "cash") clearProof()
}

// ── QRIS Proof ────────────────────────────────────────────────────────────────
const handleProofUpload = async (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  if (file.size > 5 * 1024 * 1024) { uploadError.value = "Ukuran file maksimal 5MB"; return }

  uploadError.value         = ""
  proofPreviewUrl.value     = URL.createObjectURL(file)
  isUploadingProof.value    = true
  proofCloudinaryUrl.value  = ""

  try {
    const formData = new FormData()
    formData.append("file", file)
    formData.append("upload_preset", CLOUDINARY_PRESET)
    formData.append("folder", CLOUDINARY_FOLDER)

    const res = await fetch(
      `https://api.cloudinary.com/v1_1/${CLOUDINARY_CLOUD}/image/upload`,
      { method: "POST", body: formData }
    )
    if (!res.ok) throw new Error("Upload gagal")
    const data = await res.json()
    proofCloudinaryUrl.value = data.secure_url
    toast.success("Bukti pembayaran berhasil diupload!")
  } catch {
    uploadError.value     = "Gagal upload bukti, coba lagi."
    proofPreviewUrl.value = ""
    toast.error("Upload bukti gagal")
  } finally {
    isUploadingProof.value = false
  }
}

const clearProof = () => {
  proofPreviewUrl.value    = ""
  proofCloudinaryUrl.value = ""
  uploadError.value        = ""
}

// ── Checkout disabled ─────────────────────────────────────────────────────────
const isCheckoutDisabled = computed(() => {
  if (!isStoreOpen.value) return true 
  if (cartStore.isEmpty || !phone.value || !name.value || isProcessing.value) return true
  if (paymentMethod.value === "qris" && !proofCloudinaryUrl.value) return true
  return false
})

// ── WhatsApp ──────────────────────────────────────────────────────────────────
const sendToWhatsApp = (orderNumber) => {
  // Ambil nomor dinamis; fallback ke env var kalau belum ke-fetch
  const targetNumber = adminWhatsapp.value
    || import.meta.env.VITE_ADMIN_WHATSAPP
    || ""

  if (!targetNumber) {
    toast.error("Nomor WhatsApp admin belum dikonfigurasi")
    return
  }

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

  const proofLine = proofCloudinaryUrl.value
    ? `\nBukti Bayar QRIS:\n${proofCloudinaryUrl.value}\n`
    : ""

  const message =
    `*ORDER BARU - MASASHIMURA*\n` +
    `===========================\n` +
    `No. Order  : *#${orderNumber}*\n` +
    `Nama       : ${name.value}\n` +
    `WhatsApp   : ${phone.value}\n` +
    `Pembayaran : ${paymentMethod.value === "qris" ? "QRIS" : "Cash"}\n` +
    `===========================\n` +
    `*Pesanan:*\n${itemsText}\n` +
    `===========================\n` +
    `${promoLine}` +
    `${rewardLine}` +
    `*TOTAL: Rp ${finalTotal.value.toLocaleString("id-ID")}*\n` +
    `${proofLine}` +
    `===========================\n` +
    `Mohon segera diproses, terima kasih!`

  window.open(`https://wa.me/${targetNumber}?text=${encodeURIComponent(message)}`, "_blank")
}

// ── Checkout ──────────────────────────────────────────────────────────────────
const checkout = async () => {
  if (!name.value)  return toast.error("Mohon isi nama kamu")
  if (!phone.value) return toast.error("Mohon isi nomor WhatsApp")
  if (paymentMethod.value === "qris" && !proofCloudinaryUrl.value)
    return toast.error("Upload bukti pembayaran QRIS dulu ya!")

  // Guard: pastikan nomor admin sudah ada sebelum proses
    if (!adminWhatsapp.value) {
    await fetchSettings()
    if (!adminWhatsapp.value) {
      toast.error("Nomor WhatsApp admin belum dikonfigurasi. Hubungi admin.")
      return
    }
  }

  isProcessing.value = true
  try {
    const orderData = {
      source:         "web",
      customer:       { phone: phone.value, name: name.value },
      payment_method: paymentMethod.value,
      proof_image_url: paymentMethod.value === "qris" ? proofCloudinaryUrl.value : "",
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

    toast.success("Pesanan berhasil dibuat!")
    sendToWhatsApp(orderNumber)
    cartStore.clearCart()
    name.value  = ""
    phone.value = ""
    clearProof()
    promoBoxRef.value?.removePromo()
    resetPointRewards()
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