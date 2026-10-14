/**
 * Aturan nama pemesan: hanya huruf dan spasi, 3-50 karakter, tanpa angka atau tanda baca.
 * Aturan yang sama dicek ulang di backend (order/views.py).
 */
export const NAME_MIN = 3
export const NAME_MAX = 50

/** Dipakai di setiap ketikan: buang selain huruf/spasi, rapikan spasi, batasi panjang. */
export const sanitizeName = (raw) =>
  String(raw ?? '')
    .replace(/[^\p{L} ]/gu, '')   // huruf (termasuk beraksen) dan spasi saja
    .replace(/ {2,}/g, ' ')       // spasi ganda jadi satu
    .replace(/^ /, '')            // tidak boleh diawali spasi
    .slice(0, NAME_MAX)

/** Nama final untuk dikirim: spasi ujung dibuang. */
export const cleanName = (raw) => sanitizeName(raw).trim()

/** Pesan error untuk pelanggan. String kosong = nama valid. */
export const nameError = (raw) => {
  const name = cleanName(raw)
  if (!name) return 'Nama wajib diisi.'
  if (name.replace(/ /g, '').length < NAME_MIN) return `Nama minimal ${NAME_MIN} huruf.`
  if (/(\p{L})\1{2,}/iu.test(name)) return 'Nama tidak boleh berisi huruf yang sama berulang.'
  if (!/[aiueo]/i.test(name)) return 'Nama tidak valid, pakai nama aslimu.'
  return ''
}

export const isValidName = (raw) => nameError(raw) === ''