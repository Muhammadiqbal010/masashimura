import apiClient from "./client";

/**
 * Keramaian toko.
 *   getStatus()      publik — badge di halaman Menu pelanggan
 *   getStaffStatus() staf   — level aktif + level otomatis + angka pesanan
 *   setManual()      staf   — { level: 'santai'|'sedang'|'ramai'|'auto', duration_minutes } atau { level, until: 'HH:MM' }
 *   getBusyHours()   admin  — Peta Jam Sibuk
 */
export const crowdAPI = {
  getStatus: () => apiClient.get("/orders/crowd/"),
  getStaffStatus: () => apiClient.get("/orders/crowd/manual/"),
  setManual: (payload) => apiClient.post("/orders/crowd/manual/", payload),
  getBusyHours: (weeks = 8) => apiClient.get("/orders/busy-hours/", { params: { weeks } }),
};
