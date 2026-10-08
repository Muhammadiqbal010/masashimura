// src/stores/cart.js

import { defineStore } from "pinia"
import { ref, computed, watch } from "vue"
import { orderAPI } from "@/api"

const STORAGE_KEY = "cart"

// Baca keranjang tersimpan. Kalau isinya rusak (JSON tidak valid atau bukan object),
// mulai dari keranjang kosong supaya seluruh aplikasi tidak error saat dibuka.
const loadCart = () => {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}")
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {}
  } catch {
    return {}
  }
}

export const useCartStore = defineStore("cart", () => {
  // ── State ───────────────────────────────────────────────────────────────────
  const cart = ref(loadCart())

  // Diskon member % SUDAH DIHAPUS: sistem loyalty sekarang murni poin
  // (tukar menu gratis, ditangani terpisah lewat PointRedeemBox di Checkout.vue).
  // isMember/points di sini cuma buat nampilin badge info, BUKAN buat motong harga.
  const isMember = ref(false)
  const points = ref(0)
  const pointsExpiringNote = ref(null)

  // Simpan otomatis tiap keranjang berubah.
  watch(
    cart,
    (value) => {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(value))
      } catch {
        /* storage penuh / mode private: keranjang tetap jalan, hanya tidak tersimpan */
      }
    },
    { deep: true }
  )

  // ── Getters ─────────────────────────────────────────────────────────────────
  const cartItems = computed(() => Object.values(cart.value))

  const cartItemCount = computed(() =>
    cartItems.value.reduce((sum, item) => sum + item.quantity, 0)
  )

  const subtotal = computed(() =>
    cartItems.value.reduce(
      (sum, item) => sum + (Number(item.price) || 0) * item.quantity,
      0
    )
  )

  // Total murni subtotal: diskon member % sudah tidak ada. Potongan harga hanya dari
  // promo code dan tukar poin, dua-duanya ditangani terpisah di Checkout.vue.
  const totalPrice = computed(() => subtotal.value)

  const isEmpty = computed(() => cartItems.value.length === 0)

  // ── Actions: keranjang ──────────────────────────────────────────────────────
  const addToCart = (menu) => {
    // price_web sudah dihitung di backend saat menu disimpan. Kalau belum ada
    // (menu lama), pakai harga biasa supaya tampilan dan total tetap sama.
    const priceWeb = Number(menu.price_web ?? menu.price) || 0

    // Tiap klik = baris baru (catatan per item). Suffix acak mencegah bentrok
    // kalau dua item ditambah di milidetik yang sama.
    const cartKey = `${menu.id}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`

    cart.value[cartKey] = {
      ...menu,
      cartKey,
      quantity: 1,
      notes: "",
      price: priceWeb,       // dipakai untuk subtotal
      price_pos: menu.price,
      price_web: priceWeb,   // dipakai untuk tampilan di Checkout
    }
  }

  const updateQuantity = (cartKey, delta) => {
    const item = cart.value[cartKey]
    if (!item) return

    item.quantity += delta
    if (item.quantity <= 0) delete cart.value[cartKey]
  }

  const removeFromCart = (cartKey) => {
    delete cart.value[cartKey]
  }

  // ── Actions: loyalty ────────────────────────────────────────────────────────
  // Nomor permintaan terakhir. Kalau respons lama datang terlambat (nomor HP sudah
  // berganti atau dihapus), hasilnya diabaikan supaya status member tidak salah.
  let loyaltyRequestId = 0

  const resetLoyalty = () => {
    loyaltyRequestId++
    isMember.value = false
    points.value = 0
    pointsExpiringNote.value = null
  }

  const checkLoyalty = async (phone) => {
    if (!phone || phone.length < 9) {
      resetLoyalty()
      return
    }

    const requestId = ++loyaltyRequestId
    try {
      const { data } = await orderAPI.checkLoyalty(phone)
      if (requestId !== loyaltyRequestId) return

      isMember.value = data.is_member ?? false
      points.value = data.points ?? 0
      pointsExpiringNote.value = data.points_expiring_note ?? null
    } catch (err) {
      if (requestId !== loyaltyRequestId) return
      console.error(err)
      resetLoyalty()
    }
  }

  const clearCart = () => {
    cart.value = {}
    resetLoyalty()
  }

  return {
    cart,

    isMember,
    points,
    pointsExpiringNote,

    cartItems,
    cartItemCount,

    subtotal,
    totalPrice,
    isEmpty,

    addToCart,
    updateQuantity,
    removeFromCart,
    clearCart,
    checkLoyalty,
    resetLoyalty,
  }
})