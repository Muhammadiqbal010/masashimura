// src/composables/useShareMenu.js
//
// Bagikan satu menu lewat WhatsApp: foto + nama + harga + deskripsi + link /menu?item=ID.
//
// - HP (Web Share API): foto dikirim sebagai FILE, caption = nama/harga/deskripsi/link.
//   Catatan: sebagian WhatsApp iOS membuang caption kalau ada file. Link tetap ikut
//   karena ada di dalam teks, tapi kalau caption hilang, penerima tetap dapat fotonya.
// - Desktop / share file tidak didukung: buka wa.me dengan teks yang sama + URL foto.
//
// Preview gambar otomatis dari link TIDAK bisa, karena aplikasi ini SPA dan WhatsApp
// tidak menjalankan JavaScript. Itu sebabnya foto dikirim sebagai file.

const MAX_DESC = 300

const slugify = (text) =>
  String(text || "menu")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "menu"

export const buildMenuShareText = (menu, formatPrice, link) => {
  const lines = [`*${menu.name}*`, formatPrice(menu.price_web)]

  const desc = (menu.description || "").trim()
  if (desc) lines.push("", desc.length > MAX_DESC ? `${desc.slice(0, MAX_DESC - 1)}…` : desc)

  lines.push("", `Pesan di Masashimura: ${link}`)
  return lines.join("\n")
}

const fetchImageFile = async (imageUrl, baseName) => {
  const res = await fetch(imageUrl, { mode: "cors" })
  if (!res.ok) throw new Error(`Foto gagal diambil (${res.status})`)
  const blob = await res.blob()
  const subtype = (blob.type.split("/")[1] || "jpeg").split("+")[0]
  const ext = subtype === "jpeg" ? "jpg" : subtype
  return new File([blob], `${baseName}.${ext}`, { type: blob.type || "image/jpeg" })
}

/**
 * @returns {Promise<"shared" | "cancelled" | "link">}
 *   shared    → dikirim lewat share sheet HP
 *   cancelled → pengguna menutup share sheet
 *   link      → membuka wa.me (desktop / fallback)
 */
export async function shareMenuToWhatsApp(menu, { formatPrice, getMediaUrl }) {
  const link = `${window.location.origin}/menu?item=${menu.id}`
  const text = buildMenuShareText(menu, formatPrice, link)
  const imageUrl = menu.image_url
    ? new URL(getMediaUrl(menu.image_url), window.location.origin).href
    : ""

  if (imageUrl && typeof navigator.canShare === "function") {
    try {
      const file = await fetchImageFile(imageUrl, slugify(menu.name))
      if (navigator.canShare({ files: [file] })) {
        await navigator.share({ files: [file], text })
        return "shared"
      }
    } catch (err) {
      if (err?.name === "AbortError") return "cancelled"
      // Foto gagal diambil / izin share kedaluwarsa → lanjut ke link WhatsApp
    }
  }

  const waText = imageUrl ? `${text}\n\nFoto: ${imageUrl}` : text
  const waUrl = `https://wa.me/?text=${encodeURIComponent(waText)}`
  // Setelah await, sebagian browser (Safari) memblokir popup → pindah halaman sebagai cadangan.
  const win = window.open(waUrl, "_blank")
  if (!win) window.location.assign(waUrl)
  return "link"
}