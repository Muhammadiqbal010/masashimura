export const greetingByTime = (d = new Date()) => {
  const h = d.getHours()
  if (h >= 4 && h < 11) return 'pagi'
  if (h >= 11 && h < 15) return 'siang'
  if (h >= 15 && h < 18) return 'sore'
  return 'malam'
}

const rp = (n) => 'Rp ' + Math.round(Number(n) || 0).toLocaleString('id-ID')
const nota = (o) => o?.order_number || (o?.id ? '#' + o.id : '')

const hello = (o) => {
  const name = (o?.customer_name || '').trim()
  return `Halo kakak${name ? ' ' + name : ''}, selamat ${greetingByTime()} 😊`
}
const thanks = 'Terima kasih sudah jajan di Masashimura 🙏'

// Caption yang menyertai struk GAMBAR. Isinya menyesuaikan: sudah siap atau belum.
export const msgReceipt = (o) => {
  const body = o?.is_ready
    ? 'Pesanan kakak sudah siap diambil ya 🍽️'
    : 'Ini struk pesanan kakak di Masashimura ya 🧾'
  return `${hello(o)}\n${body}\n${thanks}`
}

export const msgLate = (o) => {
  const wait = Number(o?.wait_minutes) > 0 ? ` (sudah sekitar ${o.wait_minutes} menit)` : ''
  return [
    hello(o),
    `Mohon maaf ya kak, pesanan kakak (nota ${nota(o)}) masih kami siapkan dan agak lebih lama dari biasanya${wait} 🙏`,
    'Kami usahakan secepatnya ya kak, ditunggu sebentar lagi.',
    'Terima kasih banyak atas kesabarannya 🙏',
  ].join('\n')
}

export const msgUnavailable = (o) => {
  const gone = o?.unavailable_items || []
  const kept = (o?.items || []).filter((i) => i && i.menu_name)
  const lines = [
    hello(o),
    'Mohon maaf ya kak, ada menu yang sedang habis sehingga belum bisa kami buatkan:',
    ...gone.map((u) => `• ${u.name} × ${u.quantity} (${rp(u.price * u.quantity)})`),
  ]
  if (kept.length) {
    lines.push('', 'Menu yang tetap kami buatkan:', ...kept.map((i) => `• ${i.quantity}× ${i.menu_name}`))
  }
  lines.push('', `Total pesanan sekarang: ${rp(o?.total_price)}`)
  const due = Number(o?.refund_due) || 0
  const paid = o?.payment_status === 'paid'
  if (due > 0 && !o?.refunded_at) {
    lines.push(`Uang sebesar ${rp(due)} akan kami kembalikan ya kak.`)
  } else if (!paid && o?.status !== 'cancelled') {
    lines.push(`Jadi yang perlu dibayar sekarang ${rp(o?.total_price)} ya kak.`)
  }
  lines.push('Sekali lagi mohon maaf atas ketidaknyamanannya ya kak 🙏')
  return lines.join('\n')
}

export const msgRefundReminder = (o) => [
  hello(o),
  `Kami mau mengingatkan ya kak, ada pengembalian dana sebesar ${rp(o?.refund_due)} dari pesanan kakak (nota ${nota(o)}) karena ada menu yang habis.`,
  'Silakan diambil di kasir saat kakak mampir ke Masashimura ya 🙏',
  'Terima kasih banyak kak 😊',
].join('\n')

export const msgPaymentReminder = (o) => [
  hello(o),
  `Kami mau mengingatkan ya kak, pesanan kakak (nota ${nota(o)}) sebesar ${rp(o?.total_price)} belum dibayar.`,
  'Kakak bisa membayar di kasir, bisa cash atau QRIS ya.',
  'Terima kasih banyak kak 🙏',
].join('\n')
