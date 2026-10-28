// Pencarian global admin (Ctrl/Cmd+K): mencocokkan query ke data pesanan, menu, promo,
// pelanggan, dan reward poin yang sudah dimuat di klien. Murni fungsi, tanpa panggilan API.
export const norm = (s) => String(s ?? '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')

const tokenize = (s) => norm(s).split(/[^a-z0-9]+/).filter(Boolean)

// fields[0] = judul utama (bobot terbesar). Semua kata query harus cocok di salah satu field.
// Kata cocok bila awal kata (token) di field, atau, untuk query >= 3 karakter, bila ada di dalam teks
// (supaya potongan nomor HP / nomor order tetap ketemu). 0 = tidak cocok.
export function matchScore(words, fields) {
  if (!words.length) return 0
  const normed = fields.map(norm)
  const tokens = normed.map((f) => f.split(/[^a-z0-9]+/).filter(Boolean))
  let total = 0
  for (const w of words) {
    let best = 0
    normed.forEach((f, i) => {
      const primary = i === 0
      if (primary && f.startsWith(w)) best = Math.max(best, 4)
      else if (tokens[i].some((t) => t.startsWith(w))) best = Math.max(best, primary ? 3 : 2)
      else if (w.length >= 3 && f.includes(w)) best = Math.max(best, primary ? 1.5 : 1)
    })
    if (!best) return 0
    total += best
  }
  return total
}

const rupiah = (v) => 'Rp ' + Math.round(Number(v) || 0).toLocaleString('id-ID')
const wibDate = (iso) => {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleDateString('en-CA', { timeZone: 'Asia/Jakarta' }) // YYYY-MM-DD
}
const shortDate = (iso) => {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleDateString('id-ID', { day: 'numeric', month: 'short', timeZone: 'Asia/Jakarta' })
}
const q = (v) => encodeURIComponent(v)

function top(list, words, build, limit) {
  const scored = []
  for (const item of list) {
    const built = build(item)
    const score = matchScore(words, built.fields)
    if (score) scored.push({ score, built })
  }
  scored.sort((a, b) => b.score - a.score || (b.built.order || 0) - (a.built.order || 0))
  return scored.slice(0, limit).map((s) => s.built.result)
}

export function searchEntities(query, data) {
  const words = norm(query).split(/\s+/).filter(Boolean)
  const sections = []
  if (!words.length || norm(query).length < 2) return sections

  const orders = top(data.orders || [], words, (o) => {
    const date = wibDate(o.created_at)
    const status = o.status === 'cancelled' ? 'Dibatalkan' : (o.payment_status === 'paid' ? 'Lunas' : 'Belum bayar')
    return {
      order: new Date(o.created_at).getTime() || 0,
      fields: [o.order_number, o.customer_name, o.customer_phone, ...(o.items || []).map((i) => i.menu_name)],
      result: {
        key: `order-${o.id}`,
        label: `${o.order_number} · ${o.customer_name || 'Walk In'}`,
        hint: `${shortDate(o.created_at)} · ${rupiah(o.total_price)} · ${status}`,
        to: `/admin/orders?date=${date}&q=${q(o.order_number)}`,
      },
    }
  }, 6)
  if (orders.length) sections.push({ title: 'Pesanan', items: orders })

  const menus = top(data.menus || [], words, (m) => ({
    fields: [m.name, m.category_name],
    result: { key: `menu-${m.id}`, label: m.name, hint: `${m.category_name || 'Menu'} · ${rupiah(m.price)}`, to: `/admin/menus?q=${q(m.name)}` },
  }), 4)
  if (menus.length) sections.push({ title: 'Menu', items: menus })

  const customers = top(data.customers || [], words, (c) => ({
    fields: [c.name, c.phone],
    result: { key: `cust-${c.phone}`, label: c.name || c.phone, hint: `${c.phone} · ${(c.points || 0).toLocaleString('id-ID')} poin`, to: `/admin/customers?q=${q(c.phone)}` },
  }), 4)
  if (customers.length) sections.push({ title: 'Pelanggan', items: customers })

  const promos = top(data.promos || [], words, (p) => ({
    fields: [p.code, p.description],
    result: { key: `promo-${p.id}`, label: p.code, hint: (p.description || '').slice(0, 40) || (p.is_active ? 'Aktif' : 'Nonaktif'), to: `/admin/promos?q=${q(p.code)}` },
  }), 4)
  if (promos.length) sections.push({ title: 'Promo', items: promos })

  const rewards = top(data.rewards || [], words, (r) => ({
    fields: [r.menu_name],
    result: { key: `reward-${r.id}`, label: r.menu_name, hint: `${(r.point_cost || 0).toLocaleString('id-ID')} poin`, to: `/admin/point-rewards?q=${q(r.menu_name)}` },
  }), 3)
  if (rewards.length) sections.push({ title: 'Reward Poin', items: rewards })

  return sections
}
