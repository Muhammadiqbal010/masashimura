import apiClient from "./client";

export const statsAPI = {
  getDashboardSummary: () => apiClient.get("/orders/stats/"),
  // Respons: { settings, customers: [...] }
  getLoyalCustomers: () => apiClient.get("/orders/loyal-customers/"),
  // Atur / ganti PIN member. Body kosong = PIN acak 4 digit. PIN asli hanya ada di respons ini.
  setLoyalCustomerPin: (phone, pin) =>
    apiClient.post(`/orders/loyal-customers/${encodeURIComponent(phone)}/pin/`, pin ? { pin } : {}),
  // Hapus permanen (hard delete, riwayat penyesuaian poin ikut terhapus).
  deleteLoyalCustomer: (phone) => apiClient.delete(`/orders/loyal-customers/${encodeURIComponent(phone)}/`),
  // Body: { phones: [...] } atau { all: true }, plus confirm: "HAPUS" (dicek juga di server).
  bulkDeleteLoyalCustomers: (body) => apiClient.post("/orders/loyal-customers/bulk-delete/", body),
};