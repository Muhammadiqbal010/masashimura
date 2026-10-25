import apiClient from "./client";

// Midtrans Snap — endpoint ada di app `payments` (backend).
export const paymentAPI = {
  // Minta snap token untuk order web ber-payment_method "gateway".
  // Token yang sama dikembalikan kalau sudah pernah dibuat,
  // jadi aman dipanggil ulang untuk "Bayar lagi".
  createSnapToken: (orderNumber) =>
    apiClient.post(`/payments/create/${orderNumber}/`),

  // Dipakai untuk polling. Yang mengubah status adalah webhook Midtrans,
  // bukan callback Snap di browser.
  getStatus: (orderNumber) =>
    apiClient.get(`/payments/status/${orderNumber}/`),

  // ── POS: QRIS dinamis yang ditampilkan kasir ke pelanggan (khusus staf) ──
  posQrisCreate: (orderNumber) =>
    apiClient.post(`/payments/pos/${orderNumber}/qris/`),
  // Menanyakan status langsung ke Midtrans, jadi tetap akurat walau webhook telat.
  posQrisStatus: (orderNumber) =>
    apiClient.get(`/payments/pos/${orderNumber}/status/`),
  // 200 = order dihapus bersih; 409 = ternyata sudah dibayar.
  posQrisCancel: (orderNumber) =>
    apiClient.post(`/payments/pos/${orderNumber}/cancel/`),
};