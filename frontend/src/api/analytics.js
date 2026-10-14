import apiClient from "./client";

/**
 * Analitik menu (owner/admin). `params` = parameter periode yang sama dengan
 * /orders/reports/full/: { period, days, offset, month, year }.
 */
export const analyticsAPI = {
  getMenuPerformance: (params) => apiClient.get("/orders/analytics/menu-performance/", { params }),
  getMenuPairs: (params) => apiClient.get("/orders/analytics/menu-pairs/", { params }),
  getChannels: (params) => apiClient.get("/orders/analytics/channels/", { params }),
  // Perkiraan 5 menu teratas besok (pola penjualan hari yang sama, bukan model prediksi omzet).
  getMenuTomorrow: () => apiClient.get("/orders/analytics/menu-tomorrow/"),
  // Strip Briefing Dashboard: selalu hari ini, tidak ikut filter tanggal.
  // Data dasar tab Simulasi (Dashboard, bagian Prediksi): aritmatika target + estimasi promo.
  getSimulation: () => apiClient.get("/orders/analytics/simulation/"),
  getBriefing: () => apiClient.get("/orders/briefing/"),
  // Efektivitas promo (Kelola Promo) dan poin (Kelola Reward Poin). Parameter periode sama.
  getPromoEffectiveness: (params) => apiClient.get("/orders/analytics/promo-effectiveness/", { params }),
  getPointEffectiveness: (params) => apiClient.get("/orders/analytics/point-effectiveness/", { params }),
};
