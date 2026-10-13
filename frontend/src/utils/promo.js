// src/utils/promo.js
// Helper bersama untuk PromoSection.vue & PromoCard.vue.
// Nama opsi harus sama dengan admin (EditHomepage.vue) dan models.py (PromoItem).

export const PROMO_MAX = 5

export const RATIOS = {
  "16:9": { css: "16 / 9", num: 16 / 9 },
  "21:9": { css: "21 / 9", num: 21 / 9 },
  "4:3":  { css: "4 / 3",  num: 4 / 3 },
  "1:1":  { css: "1 / 1",  num: 1 },
  "4:5":  { css: "4 / 5",  num: 4 / 5 },
  "3:4":  { css: "3 / 4",  num: 3 / 4 },
  "9:16": { css: "9 / 16", num: 9 / 16 },
}
export const FOCUS = {
  "top-left": "0% 0%",   "top": "50% 0%",      "top-right": "100% 0%",
  "left": "0% 50%",      "center": "50% 50%",  "right": "100% 50%",
  "bottom-left": "0% 100%", "bottom": "50% 100%", "bottom-right": "100% 100%",
}
export const THEMES = {
  red:     { accent: "#DC2626", ink: "#ffffff" },
  amber:   { accent: "#F59E0B", ink: "#1c1300" },
  emerald: { accent: "#10B981", ink: "#03150d" },
  sky:     { accent: "#0EA5E9", ink: "#02131c" },
  violet:  { accent: "#8B5CF6", ink: "#ffffff" },
  pink:    { accent: "#EC4899", ink: "#ffffff" },
}

export const ratioOf = (p) => RATIOS[p?.image_ratio] || RATIOS["16:9"]

// ── Jadwal (WIB). show_until berlaku sampai akhir hari ───────────────────
export const startMs = (p) => {
  if (!p?.show_from) return null
  const t = new Date(`${p.show_from}T00:00:00+07:00`).getTime()
  return isNaN(t) ? null : t
}
export const endMs = (p) => {
  if (!p?.show_until) return null
  const t = new Date(`${p.show_until}T23:59:59+07:00`).getTime()
  return isNaN(t) ? null : t
}
export const hasContent = (p) => !!(p?.title || p?.text || p?.image)
export const inSchedule = (p, now) => {
  const s = startMs(p), e = endMs(p)
  if (s !== null && now < s) return false
  if (e !== null && now > e) return false
  return true
}

// Tanda tangan isi promo: tombol tutup diingat per isi, muncul lagi kalau isinya diganti
export const signature = (p) => {
  const raw = [p.id, p.badge, p.title, p.text, p.image, p.link, p.show_from, p.show_until].join("|")
  let h = 5381
  for (let i = 0; i < raw.length; i++) h = ((h << 5) + h + raw.charCodeAt(i)) | 0
  return String(h >>> 0)
}

// ── Susunan baris di homepage ────────────────────────────────────────────
// Gambar lebar (16:9, 21:9, 4:3) atau promo tanpa gambar -> 1 baris penuh (memanjang).
// Gambar kotak/portrait (1:1, 4:5, 3:4, 9:16) yang berurutan -> berjajar 2-3 per baris.
export const isWide = (p) => !p?.image || ratioOf(p).num >= 1.2

const chunkSizes = (n) => (n <= 3 ? [n] : n === 4 ? [2, 2] : [3, ...chunkSizes(n - 3)])

export const buildRows = (items) => {
  const rows = []
  let i = 0
  while (i < items.length) {
    if (isWide(items[i])) {
      rows.push({ key: `w${items[i].id}`, cols: 1, items: [items[i]] })
      i++
      continue
    }
    let j = i
    while (j < items.length && !isWide(items[j])) j++
    const run = items.slice(i, j)
    let k = 0
    for (const size of chunkSizes(run.length)) {
      const part = run.slice(k, k + size)
      rows.push({ key: `n${part.map((x) => x.id).join("-")}`, cols: size, items: part })
      k += size
    }
    i = j
  }
  return rows
}