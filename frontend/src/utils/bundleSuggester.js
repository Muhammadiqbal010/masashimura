// src/utils/bundleSuggester.js
//
// Saran paket (makanan + minuman) untuk owner. Modul MURNI, tanpa Vue dan tanpa API,
// supaya hasilnya mudah diuji dan dijelaskan di laporan.
//
// Tiga sinyal digabung:
//   1. Popularitas : menu terlaris di grupnya (makanan atau minuman), dari volume penjualan.
//   2. Dipesan bareng : pasangan yang benar-benar muncul dalam satu order (jumlah dan lift).
//   3. Kemiripan teks (TF-IDF): pasangan satu grup yang terlalu mirip dikurangi skornya karena
//      saling menggantikan, bukan melengkapi. Pasangan makanan + minuman tidak dipotong.
//
// Harga disarankan dari harga normal dikurangi diskon yang menyesuaikan bukti: pasangan yang
// sudah sering dipesan bareng cukup diberi diskon tipis, yang belum pernah butuh pemicu lebih besar.
// Biaya bahan (HPP) tidak tercatat di sistem, jadi margin TIDAK dihitung. Owner tetap harus
// memastikan harga akhir masih untung.

import { cosine } from "@/utils/recommender"

// Kategori dianggap "minuman" kalau namanya memuat salah satu kata ini. Selain itu = makanan.
// Kalau kategori kafe berbeda dari kata-kata ini, tambahkan di sini.
const DRINK_PATTERN = /minum|kopi|coffee|\bteh\b|\btea\b|\bjus\b|juice|drink|beverage|susu|\bes\b|smoothie|latte|boba|mojito/i

export const isDrinkMenu = (menu) => DRINK_PATTERN.test(String(menu?.category_name || ""))

const hasRequiredOption = (m) => (m.options || []).some((g) => g && g.required)

// Aturan yang sama dengan BundleManager: aktif, bukan secret, tanpa pilihan wajib. Ditambah: tersedia.
export const isBundleable = (m) =>
  m && m.id != null && m.is_active !== false && m.is_available !== false && !m.is_secret && !hasRequiredOption(m)

const roundDown500 = (n) => Math.floor(n / 500) * 500
const roundUp500 = (n) => Math.ceil(n / 500) * 500

const MIN_NORMAL = 6000          // di bawah ini diskon tidak bermakna
const POOL_SIZE = 6              // berapa menu terlaris per grup yang dipasangkan
const MAX_REUSE = 2              // satu menu maksimal muncul di 2 saran

// Diskon menyesuaikan bukti dipesan-bareng.
const discountRate = (co) => {
  if (co.count >= 3 && co.lift > 1) return 0.05   // sudah sering bareng: diskon tipis
  if (co.count >= 1) return 0.08
  return 0.12                                      // belum pernah bareng: butuh pemicu
}

export const evidenceLevel = (co) => {
  if (co.count >= 3 && co.lift > 1) return "kuat"
  if (co.count >= 1) return "sedang"
  return "dasar"
}

/**
 * Harga saran untuk dua menu.
 * @returns { normal, price, min, max, rate } atau null kalau harga terlalu kecil untuk diberi diskon.
 */
export const suggestPrice = (priceA, priceB, co = { count: 0, lift: 0 }) => {
  const normal = Number(priceA) + Number(priceB)
  if (!(normal >= MIN_NORMAL)) return null
  const min = roundUp500(normal * 0.85)                  // diskon terdalam yang masih wajar (15%)
  const max = Math.min(roundDown500(normal * 0.95), normal - 500)   // diskon tertipis (5%)
  if (max < min) return null
  const rate = discountRate(co)
  const price = Math.min(max, Math.max(min, roundDown500(normal * (1 - rate))))
  return { normal, price, min, max, rate: Math.round(((normal - price) / normal) * 100) }
}

/**
 * @param {object} p
 * @param {Array}  p.menus        daftar menu (Kelola Menu)
 * @param {Array}  p.performance  rows dari analytics menu-performance ({ id, qty, ... })
 * @param {Array}  p.pairs        pairs dari analytics menu-pairs ({ a:{id}, b:{id}, count, lift })
 * @param {Array}  p.bundles      paket yang sudah ada (untuk dilewati)
 * @param {object} p.index        indeks TF-IDF dari buildIndex (opsional)
 */
export const suggestBundles = ({ menus, performance = [], pairs = [], bundles = [], index = null, limit = 5 }) => {
  const qtyById = new Map(performance.map((r) => [r.id, Number(r.qty) || 0]))
  const eligible = (menus || []).filter(isBundleable)

  const rank = (list) =>
    list
      .map((m) => ({ menu: m, qty: qtyById.get(m.id) || 0 }))
      .filter((r) => r.qty > 0)
      .sort((a, b) => b.qty - a.qty || String(a.menu.name).localeCompare(String(b.menu.name), "id"))
      .slice(0, POOL_SIZE)

  const foods = rank(eligible.filter((m) => !isDrinkMenu(m)))
  const drinks = rank(eligible.filter((m) => isDrinkMenu(m)))
  if (!foods.length || !drinks.length) {
    return { suggestions: [], status: !performance.length ? "no_sales" : "no_group" }
  }

  const maxFood = foods[0].qty
  const maxDrink = drinks[0].qty

  const pairMap = new Map()
  let maxCount = 0
  for (const p of pairs) {
    const key = [p.a.id, p.b.id].sort((x, y) => x - y).join("-")
    pairMap.set(key, { count: Number(p.count) || 0, lift: Number(p.lift) || 0 })
    maxCount = Math.max(maxCount, Number(p.count) || 0)
  }
  const hasPairData = maxCount > 0

  const covered = new Set()
  for (const b of bundles || []) {
    const ids = (b.contents || []).map((c) => c.menu)
    for (const x of ids) for (const y of ids) if (x < y) covered.add(`${x}-${y}`)
  }

  const candidates = []
  foods.forEach((f, fi) => {
    drinks.forEach((d, di) => {
      const key = [f.menu.id, d.menu.id].sort((x, y) => x - y).join("-")
      if (covered.has(key)) return
      const co = pairMap.get(key) || { count: 0, lift: 0 }

      const popularity = Math.sqrt((f.qty / maxFood) * (d.qty / maxDrink))   // keduanya harus laris
      const coScore = hasPairData ? Math.min(1, co.count / maxCount) * (co.lift > 1 ? 1 : 0.6) : 0
      let score = hasPairData ? 0.55 * popularity + 0.45 * coScore : popularity

      // Makanan + minuman jarang saling menggantikan, tapi kalau teksnya sangat mirip, kurangi.
      const sim = index ? cosine(index, f.menu.id, d.menu.id) : 0
      score *= 1 - Math.min(0.5, sim)

      const price = suggestPrice(f.menu.price, d.menu.price, co)
      if (!price) return

      const reasons = [
        `${f.menu.name} terlaris ke-${fi + 1} di makanan (${f.qty} porsi)`,
        `${d.menu.name} terlaris ke-${di + 1} di minuman (${d.qty} porsi)`,
      ]
      reasons.push(
        co.count > 0
          ? `Dipesan bareng ${co.count}× dalam satu order${co.lift > 1 ? `, lift ${co.lift}` : ""}`
          : "Belum pernah dipesan bareng di data ini (saran murni dari popularitas)"
      )

      candidates.push({
        food: f.menu, drink: d.menu, score, price, co,
        evidence: evidenceLevel(co), reasons,
        draft: {
          name: `Paket ${f.menu.name} + ${d.menu.name}`.slice(0, 100),
          price: price.price,
          items: [{ menu: f.menu.id, quantity: 1 }, { menu: d.menu.id, quantity: 1 }],
        },
      })
    })
  })

  candidates.sort((a, b) => b.score - a.score)

  // Variasi: satu menu tidak dipakai berulang di semua saran.
  const used = new Map()
  const picked = []
  for (const c of candidates) {
    if ((used.get(c.food.id) || 0) >= MAX_REUSE || (used.get(c.drink.id) || 0) >= MAX_REUSE) continue
    picked.push(c)
    used.set(c.food.id, (used.get(c.food.id) || 0) + 1)
    used.set(c.drink.id, (used.get(c.drink.id) || 0) + 1)
    if (picked.length >= limit) break
  }
  return { suggestions: picked, status: picked.length ? "ok" : "none", hasPairData }
}
