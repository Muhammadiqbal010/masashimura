import apiClient from "./client";

export const orderAPI = {
  getAll: () => apiClient.get("/orders/list/"),
  getById: (id) => apiClient.get(`/orders/${id}/`),
  create: (orderData) => apiClient.post("/orders/", orderData),

  // Dipakai untuk silent loyalty check di Checkout.vue (lihat stores/cart.js -> checkLoyalty)
  checkLoyalty: (phone) =>
    apiClient.get("/orders/check_loyalty_status/", { params: { phone } }),

  // Saldo poin + rekomendasi menu yang bisa ditukar (Checkout.vue)
  getAvailablePointRewards: (phone) =>
    apiClient.get("/orders/point-rewards/available/", { params: { phone } }),

  getLoyalCustomers: () => apiClient.get("/orders/loyal/"),
  getOrderReports: (params = {}) =>
    apiClient.get("/orders/reports/", { params }),

  // Dipakai oleh ActiveOrders.vue
  getActiveOrders: (targetDate) =>
    apiClient.get("/active-orders/", { params: { target_date: targetDate } }),
};

// Admin CRUD buat katalog reward poin (AdminPointRewards.vue)
export const pointRewardAPI = {
  getAll: () => apiClient.get("/point-rewards/"),
  create: (data) => apiClient.post("/point-rewards/", data),
  update: (id, data) => apiClient.patch(`/point-rewards/${id}/`, data),
  remove: (id) => apiClient.delete(`/point-rewards/${id}/`),
};

// Pengaturan poin (rate "belanja Rp berapa = 1 poin", dll) — AdminPointRewards.vue
export const loyaltySettingsAPI = {
  get: () => apiClient.get("/orders/loyalty-settings/"),
  update: (data) => apiClient.put("/orders/loyalty-settings/", data),
};