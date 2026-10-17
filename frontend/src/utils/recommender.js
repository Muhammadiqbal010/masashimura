// src/utils/recommender.js
//
// Content-based filtering untuk menu Masashimura: TF-IDF + cosine similarity.
// Modul MURNI (tanpa Vue, tanpa API, tanpa localStorage) supaya mudah diuji dan
// mudah dijelaskan di laporan. Hanya butuh data menu, tidak butuh riwayat transaksi
// maupun identitas pelanggan.
//
// Alur:
//   1. Tiap menu diubah jadi "dokumen teks" (nama, kategori, deskripsi, pilihan opsi).
//   2. Teks di-tokenisasi (huruf kecil, buang stopword, stemming ringan).
//   3. Tiap dokumen jadi vektor TF-IDF (sparse), lalu dinormalisasi (L2).
//   4. Kemiripan dua menu = cosine similarity = dot product dua vektor ternormalisasi.

// Bobot tiap field: nama paling menentukan, kategori cukup kuat, sisanya pendukung.
// Diterapkan sebagai pengali frekuensi term (TF) dari field tersebut.
export const FIELD_WEIGHTS = { name: 3, category: 2, description: 1, options: 1 }

// Skor di bawah ini dianggap tidak mirip sama sekali (hindari rekomendasi asal-asalan).
export const MIN_SCORE = 0.03

const STOPWORDS = new Set([
  "dan", "dengan", "yang", "di", "ke", "dari", "untuk", "atau", "pada", "ini", "itu",
  "dalam", "serta", "juga", "bisa", "dapat", "lebih", "sangat", "tanpa", "ada", "adalah",
  "khas", "spesial", "special", "menu", "andalan", "pilihan", "porsi", "paket", "nikmat",
  "enak", "lezat", "segar", "the", "and", "with", "of", "a",
])

// Stemming ringan: cukup buang akhiran "nya" dan "-lah"/"-kah". Sengaja tidak memakai
// stemmer penuh (Nazief-Adriani) karena nama menu banyak istilah asing (katsu, ramen,
// matcha) yang justru rusak kalau di-stem agresif.
const stem = (token) => {
  if (token.length > 5 && token.endsWith("nya")) return token.slice(0, -3)
  return token
}

export const tokenize = (text) => {
  if (!text) return []
  return String(text)
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((t) => t.length >= 3 && !STOPWORDS.has(t) && !/^\d+$/.test(t))
    .map(stem)
}

// Kumpulkan teks dari opsi menu: nama grup + label pilihan ("Level Pedas", "Extra keju", ...).
const optionsText = (options) => {
  if (!Array.isArray(options)) return ""
  const parts = []
  for (const group of options) {
    if (group?.name) parts.push(group.name)
    for (const c of group?.choices || []) if (c?.label) parts.push(c.label)
  }
  return parts.join(" ")
}

// Frekuensi term berbobot untuk satu menu: Map(term -> bobot mentah).
const termCounts = (menu) => {
  const counts = new Map()
  const add = (text, weight) => {
    for (const t of tokenize(text)) counts.set(t, (counts.get(t) || 0) + weight)
  }
  add(menu.name, FIELD_WEIGHTS.name)
  add(menu.category_name, FIELD_WEIGHTS.category)
  add(menu.description, FIELD_WEIGHTS.description)
  add(optionsText(menu.options), FIELD_WEIGHTS.options)
  return counts
}

/**
 * Bangun indeks TF-IDF dari daftar menu.
 * TF  = 1 + ln(count)                 (sublinear, supaya satu kata diulang tidak mendominasi)
 * IDF = ln((N + 1) / (df + 1)) + 1    (smoothed, tidak pernah nol atau negatif)
 * Vektor akhir dinormalisasi L2 sehingga cosine = dot product.
 */
export const buildIndex = (menus) => {
  const list = (menus || []).filter((m) => m && m.id != null)
  const counts = new Map()
  const df = new Map()

  for (const m of list) {
    const c = termCounts(m)
    counts.set(m.id, c)
    for (const term of c.keys()) df.set(term, (df.get(term) || 0) + 1)
  }

  const N = list.length
  const idf = new Map()
  for (const [term, n] of df) idf.set(term, Math.log((N + 1) / (n + 1)) + 1)

  const docs = new Map()
  for (const m of list) {
    const vec = new Map()
    let sumSq = 0
    for (const [term, count] of counts.get(m.id)) {
      const w = (1 + Math.log(count)) * idf.get(term)
      vec.set(term, w)
      sumSq += w * w
    }
    const norm = Math.sqrt(sumSq) || 1
    for (const [term, w] of vec) vec.set(term, w / norm)
    docs.set(m.id, { menu: m, vec })
  }
  return { docs, idf, size: N }
}

// Dot product dua vektor sparse (iterasi yang lebih kecil).
const dot = (a, b) => {
  const [small, big] = a.size <= b.size ? [a, b] : [b, a]
  let sum = 0
  for (const [term, w] of small) {
    const o = big.get(term)
    if (o !== undefined) sum += w * o
  }
  return sum
}

// Dua menu: cosine similarity (0..1).
export const cosine = (index, idA, idB) => {
  const a = index.docs.get(idA)
  const b = index.docs.get(idB)
  return a && b ? dot(a.vec, b.vec) : 0
}

// Term yang paling berkontribusi pada kemiripan dua menu (untuk keterangan "mirip karena ...").
export const sharedTerms = (index, idA, idB, limit = 2) => {
  const a = index.docs.get(idA)
  const b = index.docs.get(idB)
  if (!a || !b) return []
  const out = []
  for (const [term, w] of a.vec) {
    const o = b.vec.get(term)
    if (o !== undefined) out.push([term, w * o])
  }
  return out.sort((x, y) => y[1] - x[1]).slice(0, limit).map(([t]) => t)
}

// Hanya menu yang bisa dipesan yang layak direkomendasikan ke pelanggan dan kasir.
const isRecommendable = (m) => m.is_available !== false && m.is_active !== false && !m.is_secret

// Untuk admin: menu habis atau secret tetap ikut dianalisis (hanya yang nonaktif dibuang),
// karena admin justru perlu melihat kemiripan semua menu yang ada di daftar.
const isListed = (m) => m.is_active !== false

// Pilih `limit` hasil dari daftar yang sudah terurut skor.
// `crossSlots` slot terakhir disisihkan untuk menu dari kategori LAIN (content-based
// cenderung hanya menyarankan menu sejenis; slot ini memberi variasi lintas kategori).
const diversify = (ranked, limit, crossSlots, refCategories) => {
  if (crossSlots <= 0 || ranked.length <= limit - crossSlots) return ranked.slice(0, limit)
  const sameCount = limit - crossSlots
  const picked = ranked.filter((r) => refCategories.has(r.menu.category_name)).slice(0, sameCount)
  const pickedIds = new Set(picked.map((r) => r.menu.id))
  const cross = ranked
    .filter((r) => !refCategories.has(r.menu.category_name) && !pickedIds.has(r.menu.id))
    .slice(0, crossSlots)
  const merged = [...picked, ...cross]
  // Kalau salah satu kelompok kurang, isi sisanya dari peringkat teratas.
  for (const r of ranked) {
    if (merged.length >= limit) break
    if (!merged.some((x) => x.menu.id === r.menu.id)) merged.push(r)
  }
  return merged.sort((x, y) => y.score - x.score).slice(0, limit)
}

/**
 * Menu serupa untuk satu menu (dipakai di modal detail).
 * @returns [{ menu, score, reason: string[] }]
 */
export const similarTo = (index, menuId, { limit = 3, crossSlots = 0, includeHidden = false } = {}) => {
  const base = index.docs.get(menuId)
  if (!base) return []
  const eligible = includeHidden ? isListed : isRecommendable
  const ranked = []
  for (const [id, doc] of index.docs) {
    if (id === menuId || !eligible(doc.menu)) continue
    const score = dot(base.vec, doc.vec)
    if (score >= MIN_SCORE) ranked.push({ menu: doc.menu, score, reason: sharedTerms(index, menuId, id, 3) })
  }
  ranked.sort((a, b) => b.score - a.score)
  return diversify(ranked, limit, crossSlots, new Set([base.menu.category_name]))
}

/**
 * Rekomendasi berdasarkan isi keranjang (dipakai di drawer keranjang).
 * Profil = rata-rata vektor menu di keranjang (centroid), lalu diurutkan dengan cosine.
 * Menu yang sudah ada di keranjang tidak ikut direkomendasikan.
 */
export const forCart = (index, menuIds, { limit = 3, crossSlots = 1 } = {}) => {
  const ids = [...new Set((menuIds || []).filter((id) => index.docs.has(id)))]
  if (!ids.length) return []

  const profile = new Map()
  for (const id of ids) {
    for (const [term, w] of index.docs.get(id).vec) {
      profile.set(term, (profile.get(term) || 0) + w / ids.length)
    }
  }
  let sumSq = 0
  for (const w of profile.values()) sumSq += w * w
  const norm = Math.sqrt(sumSq) || 1
  for (const [term, w] of profile) profile.set(term, w / norm)

  const inCart = new Set(ids)
  const refCategories = new Set(ids.map((id) => index.docs.get(id).menu.category_name))
  const ranked = []
  for (const [id, doc] of index.docs) {
    if (inCart.has(id) || !isRecommendable(doc.menu)) continue
    const score = dot(profile, doc.vec)
    if (score >= MIN_SCORE) ranked.push({ menu: doc.menu, score, reason: [] })
  }
  ranked.sort((a, b) => b.score - a.score)
  return diversify(ranked, limit, crossSlots, refCategories)
}

/**
 * Pasangan menu yang paling mirip satu sama lain (dipakai panel admin).
 * Semua pasangan dihitung sekali (i < j), jadi biayanya O(N^2) — aman untuk daftar menu
 * puluhan sampai ratusan item.
 * @returns [{ a, b, score, reason: string[], sameCategory: boolean }]
 */
export const similarPairs = (index, { limit = 8, minScore = 0.15 } = {}) => {
  const docs = [...index.docs.values()].filter((d) => isListed(d.menu))
  const out = []
  for (let i = 0; i < docs.length; i++) {
    for (let j = i + 1; j < docs.length; j++) {
      const score = dot(docs[i].vec, docs[j].vec)
      if (score < minScore) continue
      out.push({
        a: docs[i].menu,
        b: docs[j].menu,
        score,
        reason: sharedTerms(index, docs[i].menu.id, docs[j].menu.id, 3),
        sameCategory: docs[i].menu.category_name === docs[j].menu.category_name,
      })
    }
  }
  return out.sort((x, y) => y.score - x.score).slice(0, limit)
}