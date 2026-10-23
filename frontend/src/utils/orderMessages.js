/**
 * Pesan WhatsApp ke pelanggan dari Active Orders. Semua nominal diambil dari
 * data order terbaru (hasil serializer backend), jadi angkanya sama dengan yang tampil di struk.
 */

const rupiah = (n) =>
  new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(Number(n) || 0)

/** "0812..." / "+62812..." / "62812..." → "62812..." (format wa.me). Kosong kalau bukan nomor. */
export const waNumber = (raw) => {
  const digits = String(raw || '').replace(/\D/g, '')
  if (!digits) return ''
  if (digits.startsWith('62')) return digits
  if (digits.startsWith('0')) return '62' + digits.slice(1)
  return digits
}

export const waLink = (phone, text) => {
  const n = waNumber(phone)
  return n ? `https://wa.me/${n}?text=${encodeURIComponent(text)}` : ''
}

const hello = (o) => `Halo${o.customer_name ? ' ' + o.customer_name : ''}`
const ref = (o) => o.order_number || '#' + o.id

const methodText = (m) =>
  ({ qris: 'QRIS', qris_manual: 'QRIS', gateway: 'QRIS', cash: 'cash', mixed: 'pembayaran' })[m] || 'pembayaran'

/** Nama menu yang habis, lengkap dengan harga: "Kukubima x1 (Rp7.500)" */
export const unavailableList = (o) =>
  (o.unavailable_items || [])
    .map((u) => `${u.name} x${u.quantity} (${rupiah(u.price * u.quantity)})`)
    .join(', ')

/** Daftar menu yang MASIH dibuat, satu baris per menu, lengkap dengan catatan & subtotal. */
const itemLines = (o) =>
  (o.items || [])
    .map((i) => `• ${i.menu_name} x${i.quantity}${i.notes ? ` (${i.notes})` : ''} — ${rupiah(i.price * i.quantity)}`)
    .join('\n')

const orderBlock = (o) => {
  const lines = itemLines(o)
  return lines ? `\nPesanan:\n${lines}\nTotal: ${rupiah(o.total_price)}` : `\nTotal: ${rupiah(o.total_price)}`
}

/** Status pembayaran + aturan uang. Lunas → refund saat diambil; belum bayar → total yang harus dibayar. */
export const moneyLine = (o) => {
  if (o.refund_due > 0 && !o.refunded_at) {
    return `Pembayaran ${methodText(o.payment_method)} kamu dikembalikan ${rupiah(o.refund_due)} saat pesanan diambil di kasir.`
  }
  if (o.amount_to_pay_now > 0) {
    return `Total yang perlu dibayar sekarang ${rupiah(o.amount_to_pay_now)}.`
  }
  if (o.payment_status === 'paid') return `Pesanan sudah lunas (${methodText(o.payment_method)}), tidak ada tagihan lagi.`
  return ''
}

const fmtDate = (v) => {
  const d = new Date(v)
  if (!v || isNaN(d)) return ''
  return d.toLocaleString('id-ID', {
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
    hour12: false, timeZone: 'Asia/Jakarta',
  }) + ' WIB'
}

const payMethodName = (m) =>
  ({ cash: 'Cash', qris: 'QRIS', qris_manual: 'QRIS', gateway: 'QRIS', mixed: 'Campuran' })[m] || '-'

/** Nota dalam bentuk teks (wa.me hanya bisa mengirim teks, bukan gambar/PDF). */
export const receiptText = (o) => {
  const rows = [
    '*MASASHIMURA*',
    `Nota: ${ref(o)}`,
    `Waktu: ${fmtDate(o.created_at)}`,
  ]
  if (o.kasir_name) rows.push(`Kasir: ${o.kasir_name}`)
  if (o.customer_name) rows.push(`Pelanggan: ${o.customer_name}`)
  rows.push('--------------------------------')
  for (const i of o.items || []) {
    rows.push(`${i.menu_name} x${i.quantity}${i.is_point_redemption ? ' (tukar poin)' : ''}`)
    if (i.notes) rows.push(`   ${i.notes}`)
    rows.push(`   ${rupiah(i.price * i.quantity)}`)
  }
  rows.push('--------------------------------')
  const discount = Number(o.promo_discount_amount || 0) + Number(o.discount_amount || 0)
  if (discount > 0) {
    rows.push(`Subtotal: ${rupiah(o.subtotal)}`)
    rows.push(`Diskon${o.promo_code ? ` (${o.promo_code})` : ''}: -${rupiah(discount)}`)
  }
  rows.push(`*Total: ${rupiah(o.total_price)}*`)
  if (o.payment_status === 'paid') {
    rows.push(`Pembayaran: ${payMethodName(o.payment_method)} · LUNAS`)
    if (Number(o.change_amount) > 0) rows.push(`Kembalian: ${rupiah(o.change_amount)}`)
  } else {
    rows.push('Pembayaran: BELUM DIBAYAR')
  }
  if (o.unavailable_items?.length) rows.push(`Menu habis (tidak dibuat): ${unavailableList(o)}`)
  return rows.join('\n')
}

/** Nota lengkap, lalu tulisan "siap diambil" (+ refund / tagihan kalau ada) di bawahnya. */
export const msgReady = (o) => {
  const footer = [`${hello(o)}, pesanan kamu sudah siap diambil ya 🍽️`]
  const money = moneyLine(o)
  if (money) footer.push(money)
  footer.push('Terima kasih sudah jajan di Masashimura 🙏')
  return `${receiptText(o)}\n\n${footer.join('\n')}`
}

export const msgLate = (o) => {
  const wait = o.wait_minutes ? ` (sudah ${o.wait_minutes} menit sejak dipesan)` : ''
  const parts = [
    `${hello(o)}, mohon maaf pesanan ${ref(o)} di Masashimura agak telat dari perkiraan${wait}. Sedang kami kerjakan, ditunggu sebentar lagi ya 🙏`,
    orderBlock(o),
  ]
  const money = moneyLine(o)
  if (money) parts.push(`\n${money}`)
  return parts.join('')
}

export const msgUnavailable = (o) => {
  const parts = [
    `${hello(o)}, mohon maaf, menu berikut pada pesanan ${ref(o)} habis dan tidak bisa kami buat:\n${unavailableList(o) || '-'}`,
  ]
  const lines = itemLines(o)
  if (lines) parts.push(`\n\nYang tetap kami buat:\n${lines}`)
  parts.push(`\nTotal pesanan sekarang: ${rupiah(o.total_price)}`)
  const money = moneyLine(o)
  if (money) parts.push(`\n${money}`)
  parts.push('\n\nTerima kasih atas pengertiannya 🙏')
  return parts.join('')
}

export const msgRefundReminder = (o) =>
  `${hello(o)}, ada pengembalian dana ${rupiah(o.refund_due)} untuk pesanan ${ref(o)} di Masashimura ` +
  `karena menu habis (${unavailableList(o) || 'lihat nota'}). Silakan ambil di kasir ya 🙏`

export const msgPaymentReminder = (o) =>
  `${hello(o)}, pesanan ${ref(o)} di Masashimura belum dibayar.${orderBlock(o)}\n\n` +
  `Total yang perlu dibayar ${rupiah(o.amount_to_pay_now || o.total_price)}. Mohon konfirmasinya ya, terima kasih 🙏`
