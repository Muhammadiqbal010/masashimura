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
};