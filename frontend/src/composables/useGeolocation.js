// Lokasi pelanggan dari browser (Geolocation API). Gratis, tanpa API key.
// Dipakai di Checkout.vue. TIDAK PERNAH memblokir order: ditolak, timeout,
// atau tidak didukung -> mengembalikan null, backend lalu fallback ke lokasi IP.

const WAIT_MS = 8000 // batas tunggu total (termasuk pelanggan membaca popup izin)

export function getCustomerLocation() {
  return new Promise((resolve) => {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      return resolve(null)
    }

    let done = false
    const finish = (value) => {
      if (done) return
      done = true
      clearTimeout(timer)
      resolve(value)
    }
    const timer = setTimeout(() => finish(null), WAIT_MS)

    navigator.geolocation.getCurrentPosition(
      (pos) =>
        finish({
          lat: Number(pos.coords.latitude.toFixed(6)),
          lng: Number(pos.coords.longitude.toFixed(6)),
          accuracy: Math.round(pos.coords.accuracy || 0), // meter
        }),
      () => finish(null), // ditolak / gagal / timeout
      { enableHighAccuracy: true, timeout: 6000, maximumAge: 60000 },
    )
  })
}
