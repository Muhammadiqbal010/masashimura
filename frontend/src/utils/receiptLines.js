// Baris struk / riwayat order.
// Item hasil pecahan paket (bundle_name terisi) digabung jadi SATU blok paket: judul + harga total
// paket, lalu isinya tanpa harga. Harga pecahan per baris (mis. 53.220 / 17.741) hanya hasil
// pembagian internal supaya total paket pas bulat, tidak boleh tampil ke pelanggan.
//
// Return: [{ type: "item", item } | { type: "bundle", name, total, contents: [{ menu_name, quantity }] }]
export const groupReceiptLines = (items) => {
  const lines = []
  const bundleIdx = {}
  for (const item of items || []) {
    const qty = parseInt(item.quantity || 1)
    if (!item.bundle_name) {
      lines.push({ type: "item", item })
      continue
    }
    let line = lines[bundleIdx[item.bundle_name]]
    if (!line) {
      line = { type: "bundle", name: item.bundle_name, total: 0, contents: [] }
      bundleIdx[item.bundle_name] = lines.push(line) - 1
    }
    line.total += (parseFloat(item.price) || 0) * qty
    const same = line.contents.find((c) => c.menu_name === item.menu_name)
    if (same) same.quantity += qty
    else line.contents.push({ menu_name: item.menu_name, quantity: qty })
  }
  return lines
}