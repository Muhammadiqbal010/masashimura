// Daftar halaman admin untuk pencarian cepat (Ctrl/Cmd+K).
// Role mengikuti meta.roles di router/index.js — kalau rute berubah, ubah juga di sini.
export const ADMIN_DESTINATIONS = [
  { to: '/admin', label: 'Dashboard', group: 'Ringkasan', roles: ['owner', 'admin'], keywords: 'beranda ringkasan statistik grafik omzet' },
  { to: '/admin/pos', label: 'Pesanan Baru (POS)', group: 'Operasional', roles: ['owner', 'admin', 'kasir'], keywords: 'kasir pos order input transaksi bayar' },
  { to: '/admin/orders', label: 'Riwayat Pesanan', group: 'Operasional', roles: ['owner', 'admin', 'kasir'], keywords: 'active orders pesanan nota struk lunas tagihan' },
  { to: '/admin/menus', label: 'Kelola Menu', group: 'Data & CMS', roles: ['owner', 'admin'], keywords: 'menu makanan minuman harga stok paket' },
  { to: '/admin/promos', label: 'Kelola Promo', group: 'Data & CMS', roles: ['owner', 'admin'], keywords: 'promo diskon kode event' },
  { to: '/admin/point-rewards', label: 'Kelola Reward Poin', group: 'Data & CMS', roles: ['owner', 'admin'], keywords: 'poin reward loyalitas tukar' },
  { to: '/admin/reports', label: 'Laporan Menu', group: 'Data & CMS', roles: ['owner', 'admin'], keywords: 'laporan report analitik menu terlaris' },
  { to: '/admin/reports?tab=performa', label: 'Laporan: Performa Menu', group: 'Laporan', roles: ['owner', 'admin'], keywords: 'laporan performa menu kontribusi omzet volume' },
  { to: '/admin/reports?tab=pasangan', label: 'Laporan: Pasangan Menu', group: 'Laporan', roles: ['owner', 'admin'], keywords: 'laporan pasangan menu paket bareng' },
  { to: '/admin/reports?tab=channel', label: 'Laporan: Channel Web vs POS', group: 'Laporan', roles: ['owner', 'admin'], keywords: 'laporan channel web pos kasir pelanggan perbandingan' },
  { to: '/admin/reports?tab=jam', label: 'Laporan: Jam Sibuk', group: 'Laporan', roles: ['owner', 'admin'], keywords: 'laporan jam sibuk hari ramai' },
  { to: '/admin/edit-homepage', label: 'Ubah Beranda', group: 'Data & CMS', roles: ['owner', 'admin'], keywords: 'homepage beranda banner galeri konten cms' },
  { to: '/admin/customers', label: 'Pelanggan Setia', group: 'Data & CMS', roles: ['owner', 'admin'], keywords: 'pelanggan member loyal customer' },
  { to: '/admin/finance', label: 'Buku Kas & Keuangan', group: 'Internal', roles: ['owner'], keywords: 'finance keuangan kas pemasukan pengeluaran laba' },
  { to: '/admin/registerinternal', label: 'Daftarkan Staf Baru', group: 'Internal', roles: ['owner'], keywords: 'staf staff daftar register akun' },
  { to: '/admin/staff', label: 'Kelola PIN Staf', group: 'Internal', roles: ['owner'], keywords: 'staf staff pin' },
  { to: '/admin/settings', label: 'Pengaturan Sistem', group: 'Internal', roles: ['owner'], keywords: 'settings pengaturan sistem toko jam buka' },
  { to: '/admin/settings#blokir', label: 'Daftar Blokir Anti-Scam', group: 'Internal', roles: ['owner'], keywords: 'blokir blacklist scam penipu nomor ip buka blokir telegram' },
  { to: '/admin/profile', label: 'Profil Saya', group: 'Akun', roles: ['owner', 'admin', 'kasir'], keywords: 'profil akun password' },
]

const norm = (s) => String(s || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')

// Skor sederhana: judul diawali query > judul memuat query > kata kunci memuat query.
// Query dipecah per kata; semua kata harus cocok di judul/kata kunci/grup.
export function searchDestinations(query, role) {
  const allowed = ADMIN_DESTINATIONS.filter((d) => d.roles.includes(role))
  const words = norm(query).split(/\s+/).filter(Boolean)
  if (!words.length) return allowed

  const scored = []
  for (const d of allowed) {
    const label = norm(d.label)
    // Cocokkan awal kata (bukan sembarang potongan) supaya "kas" tidak ikut menjaring "ringkasan".
    const tokens = `${label} ${norm(d.keywords)} ${norm(d.group)}`.split(/[^a-z0-9]+/).filter(Boolean)
    const labelTokens = label.split(/[^a-z0-9]+/).filter(Boolean)
    if (!words.every((w) => tokens.some((t) => t.startsWith(w)))) continue
    let score = 0
    for (const w of words) {
      if (label.startsWith(w)) score += 3
      else if (labelTokens.some((t) => t.startsWith(w))) score += 2
      else score += 1
    }
    scored.push({ d, score })
  }
  return scored.sort((a, b) => b.score - a.score).map((s) => s.d)
}
