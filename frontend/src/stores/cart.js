// src/stores/cart.js

import { defineStore } from "pinia"
import { ref, computed, watch } from "vue"
import { toast } from "vue-sonner"
import { orderAPI } from "@/api"

const STORAGE_KEY = "cart"
const BUNDLE_STORAGE_KEY = "cartBundles"
// Batas pesanan online (anti-iseng). Harus sama dengan guards.py di backend (WEB_MAX_PER_ITEM / WEB_MAX_PORTIONS).
export const MAX_PORTIONS_PER_MENU = 10
export const MAX_PORTIONS_PER_ORDER = 30
const MAX_BUNDLE_QTY = MAX_PORTIONS_PER_MENU

// Paket di keranjang disimpan terpisah dari menu biasa (tidak bercampur dengan logika opsi/catatan).
const loadBundles = () => {
  try {
    const parsed = JSON.parse(localStorage.getItem(BUNDLE_STORAGE_KEY) || "{}")
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {}
  } catch {
    return {}
  }
}

// Baca keranjang tersimpan. Kalau isinya rusak (JSON tidak valid atau bukan object),
// mulai dari keranjang kosong supaya seluruh aplikasi tidak error saat dibuka.
// Baris yang rusak (bukan object, jumlah <= 0 / bukan angka) dibuang, dan cartKey selalu
// disamakan dengan kuncinya, supaya tombol hapus/kurangi tidak menyasar `undefined`.
const loadCart = () => {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}")
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return {}
    const clean = {}
    for (const [key, item] of Object.entries(parsed)) {
      if (!item || typeof item !== "object") continue
      const quantity = Math.floor(Number(item.quantity))
      if (!Number.isFinite(quantity) || quantity <= 0) continue
      clean[key] = { ...item, cartKey: key, quantity }
    }
    return clean
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

// Apakah pilihan yang tersimpan di keranjang masih cocok dengan opsi menu TERBARU?
// (admin bisa menghapus/mengganti nama pilihan, atau mengubah grup jadi tidak boleh banyak.)
const selectionStillValid = (menu, selection) => {
  const groups = menu.options || []
  for (const [groupName, picks] of Object.entries(selection || {})) {
    const group = groups.find((g) => g.name === groupName)
    if (!group) return false
    if (!group.multiple && picks.length > 1) return false
    for (const label of picks) {
      if (!(group.choices || []).some((c) => c.label === label)) return false
    }
  }
  return missingRequiredGroup(menu, selection) === null
}

export const useCartStore = defineStore("cart", () => {
  // ── State ───────────────────────────────────────────────────────────────────
  const cart = ref(loadCart())
  // Paket: { [bundleId]: { id, cartKey, name, contents, price, normal_price, savings, quantity } }
  // Harga di sini hanya untuk tampilan; server menghitung ulang harga paket.
  const bundleCart = ref(loadBundles())

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

  watch(
    bundleCart,
    (value) => {
      try {
        localStorage.setItem(BUNDLE_STORAGE_KEY, JSON.stringify(value))
      } catch {
        /* abaikan: sama seperti keranjang menu */
      }
    },
    { deep: true }
  )

  // ── Getters ─────────────────────────────────────────────────────────────────
  const cartItems = computed(() => Object.values(cart.value))
  const bundleLines = computed(() => Object.values(bundleCart.value))

  // Jumlah porsi: tiap paket dihitung isinya (mis. 1 paket katsu + teh = 2 porsi).
  const bundlePortions = (line) =>
    (line.contents || []).reduce((s, c) => s + (Number(c.quantity) || 0), 0) * line.quantity

  const cartItemCount = computed(
    () =>
      cartItems.value.reduce((sum, item) => sum + item.quantity, 0) +
      bundleLines.value.reduce((sum, line) => sum + bundlePortions(line), 0)
  )

  const subtotal = computed(
    () =>
      cartItems.value.reduce((sum, item) => sum + (Number(item.price) || 0) * item.quantity, 0) +
      bundleLines.value.reduce((sum, line) => sum + (Number(line.price) || 0) * line.quantity, 0)
  )

  // Total murni subtotal: diskon member % sudah tidak ada. Potongan harga hanya dari
  // promo code dan tukar poin, dua-duanya ditangani terpisah di Checkout.vue.
  const totalPrice = computed(() => subtotal.value)

  const isEmpty = computed(() => cartItems.value.length === 0 && bundleLines.value.length === 0)

  // Pesan error kalau menambah `addPortions` porsi (untuk menu `menuId`, atau null untuk paket) melewati batas.
  const portionLimitError = (menuId, addPortions) => {
    if (menuId != null && quantityOfMenu(menuId) + addPortions > MAX_PORTIONS_PER_MENU) {
      return `Maksimal ${MAX_PORTIONS_PER_MENU} porsi per menu untuk pesanan online.`
    }
    if (cartItemCount.value + addPortions > MAX_PORTIONS_PER_ORDER) {
      return `Maksimal ${MAX_PORTIONS_PER_ORDER} porsi per pesanan online. Untuk pesanan besar, hubungi toko.`
    }
    return null
  }

  // Masih boleh menambah 1 porsi lagi untuk menu ini? (dipakai tombol + di drawer keranjang)
  const canAddMore = (menuId) => portionLimitError(menuId, 1) === null

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

    const limitError = portionLimitError(menu.id, qty)
    if (limitError) return { ok: false, error: limitError }

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

  // ── Actions: paket ──────────────────────────────────────────────────────────
  // `bundle` = objek dari GET /bundles/ (publik). Return { ok, error? }.
  const addBundle = (bundle, quantity = 1) => {
    if (!bundle || bundle.unavailable_reason) {
      return { ok: false, error: bundle?.unavailable_reason || "Paket tidak tersedia." }
    }
    const qty = Math.max(1, Math.floor(Number(quantity) || 1))
    const perBundle = (bundle.contents || []).reduce((s, c) => s + (Number(c.quantity) || 0), 0) || 1
    const limitError = portionLimitError(null, perBundle * qty)
    if (limitError) return { ok: false, error: limitError }
    if ((bundleCart.value[bundle.id]?.quantity || 0) + qty > MAX_BUNDLE_QTY) {
      return { ok: false, error: `Maksimal ${MAX_BUNDLE_QTY} paket yang sama untuk pesanan online.` }
    }
    const existing = bundleCart.value[bundle.id]
    if (existing) {
      existing.quantity = Math.min(MAX_BUNDLE_QTY, existing.quantity + qty)
      return { ok: true, merged: true }
    }
    bundleCart.value[bundle.id] = {
      id: bundle.id,
      cartKey: `bundle-${bundle.id}`,
      name: bundle.name,
      contents: bundle.contents || [],
      price: Number(bundle.price) || 0,
      normal_price: bundle.normal_price == null ? null : Number(bundle.normal_price),
      savings: Number(bundle.savings) || 0,
      quantity: Math.min(MAX_BUNDLE_QTY, qty),
    }
    return { ok: true, merged: false }
  }

  const quantityOfBundle = (bundleId) => bundleCart.value[bundleId]?.quantity || 0

  const updateBundleQuantity = (bundleId, delta) => {
    const line = bundleCart.value[bundleId]
    if (!line) return
    if (delta > 0) {
      const perBundle = (line.contents || []).reduce((s, c) => s + (Number(c.quantity) || 0), 0) || 1
      const limitError = line.quantity + delta > MAX_BUNDLE_QTY
        ? `Maksimal ${MAX_BUNDLE_QTY} paket yang sama untuk pesanan online.`
        : portionLimitError(null, perBundle * delta)
      if (limitError) { toast.error(limitError); return }
    }
    line.quantity = Math.min(MAX_BUNDLE_QTY, line.quantity + delta)
    if (line.quantity <= 0) delete bundleCart.value[bundleId]
  }

  const removeBundle = (bundleId) => {
    delete bundleCart.value[bundleId]
  }

  // Samakan paket di keranjang dengan daftar paket TERBARU dari server.
  // Dibuang bila paket dihapus / habis / tidak tersedia; harga & isi diperbarui bila berubah.
  const reconcileBundles = (bundles) => {
    const result = { removed: [], soldOut: [], repriced: [] }
    if (!Array.isArray(bundles)) return result
    const byId = new Map(bundles.map((b) => [b.id, b]))
    for (const key of Object.keys(bundleCart.value)) {
      const line = bundleCart.value[key]
      const fresh = byId.get(line.id)
      if (!fresh) {
        result.removed.push(line.name)
        delete bundleCart.value[key]
        continue
      }
      if (fresh.unavailable_reason) {
        result.soldOut.push(line.name)
        delete bundleCart.value[key]
        continue
      }
      if (Number(fresh.price) !== Number(line.price)) result.repriced.push(line.name)
      line.name = fresh.name
      line.contents = fresh.contents || []
      line.price = Number(fresh.price) || 0
      line.normal_price = fresh.normal_price == null ? null : Number(fresh.normal_price)
      line.savings = Number(fresh.savings) || 0
    }
    return result
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

    if (delta > 0) {
      const limitError = portionLimitError(item.id, delta)
      if (limitError) { toast.error(limitError); return }
    }
    item.quantity += delta
    if (item.quantity <= 0) delete cart.value[cartKey]
  }

  const removeFromCart = (cartKey) => {
    delete cart.value[cartKey]
  }

  // Samakan keranjang (yang tersimpan di HP) dengan daftar menu TERBARU dari server.
  // Dipanggil setelah daftar menu berhasil dimuat. Hasilnya:
  //   - menu sudah tidak ada (dihapus / nonaktif / jadi secret)  → baris dibuang
  //   - menu habis                                               → baris dibuang
  //   - pilihan opsi tidak cocok lagi dengan opsi menu           → baris dibuang (customer pilih ulang)
  //   - harga berubah                                            → harga baris diperbarui
  // Return rincian supaya pemanggil bisa memberi tahu customer.
  const reconcileWithMenus = (menus) => {
    const result = { removed: [], soldOut: [], optionsChanged: [], repriced: [] }
    if (!Array.isArray(menus) || menus.length === 0) return result

    const byId = new Map(menus.map((m) => [m.id, m]))

    for (const key of Object.keys(cart.value)) {
      const item = cart.value[key]
      const menu = byId.get(item.id)

      if (!menu) {
        result.removed.push(item.name)
        delete cart.value[key]
        continue
      }
      if (!menu.is_available) {
        result.soldOut.push(menu.name)
        delete cart.value[key]
        continue
      }
      // Catatan: item.options di keranjang = PILIHAN customer (bukan daftar opsi menu).
      if (!selectionStillValid(menu, item.options)) {
        result.optionsChanged.push(menu.name)
        delete cart.value[key]
        continue
      }

      const priceWeb = Number(menu.price_web ?? menu.price) || 0
      const optionDetails = describeSelection(menu, item.options)
      const extraPrice = optionDetails.reduce((sum, d) => sum + d.price, 0)
      const unitPrice = priceWeb + extraPrice

      if (unitPrice !== Number(item.price)) result.repriced.push(menu.name)

      item.name = menu.name
      item.image_url = menu.image_url
      item.is_available = menu.is_available
      item.price_web = priceWeb
      item.extra_price = extraPrice
      item.optionDetails = optionDetails
      item.price = unitPrice
    }
    return result
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
    bundleCart.value = {}
    resetLoyalty()
  }

  return {
    cart,
    bundleCart,
    bundleLines,

    isMember,
    points,
    pointsExpiringNote,

    cartItems,
    cartItemCount,

    subtotal,
    totalPrice,
    isEmpty,

    addToCart,
    addBundle,
    quantityOfBundle,
    updateBundleQuantity,
    removeBundle,
    reconcileBundles,
    quantityOfMenu,
    canAddMore,
    decrementMenu,
    updateQuantity,
    removeFromCart,
    reconcileWithMenus,
    clearCart,
    checkLoyalty,
    resetLoyalty,
  }
})