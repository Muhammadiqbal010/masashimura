/**
 * Aturan nomor WhatsApp pelanggan (format lokal Indonesia):
 * hanya angka, diawali 08, panjang 10-13 digit.
 *
 * Aturan yang sama dicek ulang di backend (order/views.py), karena
 * validasi di browser bisa dilewati.
 */
export const PHONE_MIN = 10
export const PHONE_MAX = 13
const PHONE_RE = /^08\d{8,11}$/

/** Ambil angka saja dan batasi panjangnya. Dipakai di setiap ketikan. */
export const sanitizePhone = (raw) =>
  String(raw ?? '').replace(/\D/g, '').slice(0, PHONE_MAX)

/** Untuk paste: "+62 812-3456-7890" atau "6281234567890" jadi "081234567890". */
export const normalizePastedPhone = (raw) => {
  let digits = String(raw ?? '').replace(/\D/g, '')
  if (digits.startsWith('62')) digits = '0' + digits.slice(2)
  return digits.slice(0, PHONE_MAX)
}

export const isValidPhone = (value) => PHONE_RE.test(String(value ?? ''))

/** Awalan masih mungkin menuju "08" (kosong, "0", atau "08...")? */
export const hasValidPhonePrefix = (value) =>
  '08'.startsWith(String(value ?? '').slice(0, 2))

/** Pesan error untuk ditampilkan ke pelanggan. String kosong = nomor valid. */
export const phoneError = (value) => {
  const v = String(value ?? '')
  if (!v) return 'Nomor WhatsApp wajib diisi.'
  if (!hasValidPhonePrefix(v)) return 'Nomor harus diawali 08.'
  if (v.length < PHONE_MIN) return `Nomor minimal ${PHONE_MIN} digit.`
  if (v.length > PHONE_MAX) return `Nomor maksimal ${PHONE_MAX} digit.`
  return ''
}