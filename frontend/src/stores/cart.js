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

// ── Opsi pilihan menu (pedas, suhu, add-on) ─────────────────────────────────
// Format pilihan: { "Level Pedas": ["Pedas"], "Tambahan": ["Extra keju"] }
// Perhitungan di sini hanya untuk TAMPILAN. Server memvalidasi ulang pilihan
// terhadap data menu dan menghitung sendiri harga add-on.

// Buang grup kosong + urutkan, supaya pilihan yang sama selalu menghasilkan tanda yang sama.
const normalizeSelection = (selection) => {
  const out = {}
  for (const key of Object.keys(selection || {}).sort()) {
    const raw = selection[key]
    const picks = (Array.isArray(raw) ? raw : raw ? [raw] : []).filter(Boolean)
    if (picks.length) out[key] = [...picks].sort()
  }
  return out
}

const selectionSignature = (selection) => JSON.stringify(normalizeSelection(selection))

// Rincian pilihan sesuai urutan grup di menu: [{ group, label, price }]
const describeSelection = (menu, selection) => {
  const details = []
  for (const group of menu.options || []) {
    const picks = selection?.[group.name] || []
    for (const label of picks) {
      const choice = (group.choices || []).find((c) => c.label === label)
      if (choice) details.push({ group: group.name, label: choice.label, price: Number(choice.price) || 0 })
    }
  }
  return details
}

// Grup wajib yang belum dipilih (nama grup pertama), atau null kalau lengkap.
const missingRequiredGroup = (menu, selection) => {
  for (const group of menu.options || []) {
    if (group.required && !(selection?.[group.name] || []).length) return group.name
  }
  return null
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
  // Tambah menu ke keranjang. `selection` = pilihan opsi (lihat format di atas).
  // Return { ok: true } atau { ok: false, error } kalau ada opsi wajib yang belum dipilih.
  //
  // Aturan baris: menu + pilihan yang sama + catatan masih kosong → jumlahnya ditambah
  // (bukan baris baru). Kalau baris itu sudah diberi catatan, dibuat baris baru supaya
  // catatannya tidak ikut berlaku ke porsi tambahan.
  const addToCart = (menu, selection = {}, quantity = 1) => {
    const missing = missingRequiredGroup(menu, selection)
    if (missing) return { ok: false, error: `Pilih "${missing}" dulu.` }

    const chosen = normalizeSelection(selection)
    const signature = selectionSignature(chosen)
    const qty = Math.max(1, Math.floor(Number(quantity) || 1))

    const existing = cartItems.value.find(
      (item) =>
        item.id === menu.id &&
        (item.optionSignature ?? "{}") === signature &&
        !(item.notes || "").trim()
    )
    if (existing) {
      existing.quantity += qty
      return { ok: true, merged: true }
    }

    // price_web sudah dihitung di backend saat menu disimpan. Kalau belum ada
    // (menu lama), pakai harga biasa supaya tampilan dan total tetap sama.
    const priceWeb = Number(menu.price_web ?? menu.price) || 0
    const optionDetails = describeSelection(menu, chosen)
    const extraPrice = optionDetails.reduce((sum, d) => sum + d.price, 0)

    // Suffix acak mencegah bentrok kalau dua baris dibuat di milidetik yang sama.
    const cartKey = `${menu.id}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`

    cart.value[cartKey] = {
      ...menu,
      cartKey,
      quantity: qty,
      notes: "",
      options: chosen,                 // dikirim ke server saat checkout
      optionSignature: signature,
      optionDetails,                   // tampilan: [{ group, label, price }]
      extra_price: extraPrice,
      price: priceWeb + extraPrice,    // harga SATUAN termasuk add-on (dipakai untuk subtotal)
      price_pos: menu.price,
      price_web: priceWeb,             // harga dasar menu tanpa add-on
    }
    return { ok: true, merged: false }
  }

  // Jumlah total satu menu di keranjang (semua variasi opsi), untuk badge/stepper di kartu menu.
  const quantityOfMenu = (menuId) =>
    cartItems.value.reduce((sum, item) => (item.id === menuId ? sum + item.quantity : sum), 0)

  // Kurangi satu porsi menu dari baris terakhir yang ada (dipakai tombol − di kartu menu).
  const decrementMenu = (menuId) => {
    const lines = cartItems.value.filter((item) => item.id === menuId)
    const last = lines[lines.length - 1]
    if (last) updateQuantity(last.cartKey, -1)
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
    quantityOfMenu,
    decrementMenu,
    updateQuantity,
    removeFromCart,
    clearCart,
    checkLoyalty,
    resetLoyalty,
  }
})