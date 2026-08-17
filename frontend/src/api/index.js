import api from "./client"; // Ini adalah axios instance (apiClient)

// Eksport semua API module
export { authAPI } from "./auth";
export { menuAPI } from "./menu";
export { orderAPI, pointRewardAPI, loyaltySettingsAPI } from "./order";
export { statsAPI } from "./stats";
export { API_ORIGIN } from "./client"; // Import konstanta saja

// Eksport helper fungsi yang bersih (hanya satu kali)
export const getMediaUrl = (url) => {
  if (!url) return null;
  if (url.startsWith('http')) return url;
  return `http://127.0.0.1:8000${url}`;
};

// Eksport apiClient/api sebagai default dan named export
export const apiClient = api;
export default api;