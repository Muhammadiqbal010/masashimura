// Dipakai di Home DAN halaman Menu supaya harga selalu sama.
export const getWebPrice = (item) => {
  const n = Number(item?.price_web ?? item?.price)
  return Number.isFinite(n) ? n : 0
}

export const formatRupiah = (n) => `Rp ${Number(n || 0).toLocaleString("id-ID")}`