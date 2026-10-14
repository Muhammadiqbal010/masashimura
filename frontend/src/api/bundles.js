import apiClient from "./client";

// Menu Paket. GET publik (angka web) / staf (lengkap); tulis hanya owner/admin.
// Body tulis: { name, description, price, is_available, items: [{ menu, quantity }] }
export const bundleAPI = {
  getAll: () => apiClient.get("/bundles/"),
  // Untuk halaman pelanggan: selalu harga web, walau yang buka sedang login sebagai staf.
  getPublic: () => apiClient.get("/bundles/", { params: { as: "public" } }),
  create: (data) => apiClient.post("/bundles/", data),
  update: (id, data) => apiClient.patch(`/bundles/${id}/`, data),
  remove: (id) => apiClient.delete(`/bundles/${id}/`),
};