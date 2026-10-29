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

  // Lihat poin & tukar poin di web wajib PIN member. Gagal = 403 dengan pesan yang sama untuk semua sebab.
  verifyMember: (phone, pin) => apiClient.post("/orders/member/verify/", { phone, pin }),

  getOrderReports: (params = {}) =>
    apiClient.get("/orders/reports/", { params }),

  // Dipakai oleh ActiveOrders.vue
  getActiveOrders: (targetDate) =>
    apiClient.get("/active-orders/", { params: { target_date: targetDate } }),

  // ── Active Orders: tambah menu, pisah nota, siap diambil, menu habis, refund ──
  addItem: (orderId, payload) => apiClient.post(`/orders/${orderId}/items/`, payload),
  updateItem: (orderId, itemId, quantity) =>
    apiClient.patch(`/orders/${orderId}/items/${itemId}/`, { quantity }),
  splitOrder: (orderId, payload) => apiClient.post(`/orders/${orderId}/split/`, payload),
  // Ubah tanggal & jam order. Hanya order yang belum lunas (server menolak yang sudah lunas/batal).
  updateTime: (orderId, payload) => apiClient.patch(`/orders/${orderId}/time/`, payload),
  // Kasir menerima order web bayar-di-toko (tanpa ini dibatalkan otomatis setelah 15 menit).
  acceptOrder: (orderId) => apiClient.patch(`/orders/${orderId}/accept/`, {}),
  markReady: (orderId, ready = true) => apiClient.patch(`/orders/${orderId}/ready/`, { ready }),
  markUnavailable: (orderId, payload) => apiClient.post(`/orders/${orderId}/unavailable/`, payload),
  confirmRefund: (orderId, payload = {}) => apiClient.patch(`/orders/${orderId}/refund/`, payload),
  getPendingRefunds: () => apiClient.get("/orders/pending-refunds/"),
  getAffectedByMenu: (menuId) => apiClient.get(`/orders/affected-by-menu/${menuId}/`),

  // Alur staff: ringkasan layanan + antrean prioritas (uang hanya terisi untuk owner/admin) dan riwayat aksi per order.
  getStaffSummary: (date) => apiClient.get("/orders/staff-summary/", { params: date ? { date } : {} }),
  getEvents: (orderId) => apiClient.get(`/orders/${orderId}/events/`),
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

// Daftar blokir anti-scam (khusus owner; BlocklistCard.vue di Pengaturan Sistem).
// list: params { view: 'active' | 'history' | 'all', kind: 'phone' | 'ip', q }
// add: target = nomor WA atau IP (server yang menormalkan dan memvalidasi)
export const blocklistAPI = {
  list: (params = {}) => apiClient.get("/orders/blocklist/", { params }),
  add: (target, reason = "") => apiClient.post("/orders/blocklist/", { target, reason }),
  unblock: (id) => apiClient.post(`/orders/blocklist/${id}/unblock/`),
  attempts: (params = {}) => apiClient.get("/orders/blocklist/attempts/", { params }),
};

// Pencarian admin lengkap (Ctrl/Cmd+K): pesanan, pelanggan, blokir, percobaan, staf, pengeluaran.
// Isinya mengikuti peran: IP, lokasi, blokir, staf, dan pengeluaran hanya untuk owner.
export const adminSearchAPI = {
  search: (q, config = {}) => apiClient.get("/orders/admin-search/", { params: { q }, ...config }),
};
