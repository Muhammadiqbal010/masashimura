import api, { API_ORIGIN } from "./client"; // api = axios instance (apiClient)

// Eksport semua API module
export { authAPI } from "./auth";
export { menuAPI } from "./menu";
export { orderAPI, pointRewardAPI, loyaltySettingsAPI } from "./order";
export { paymentAPI } from "./payments";
export { statsAPI } from "./stats";
export { API_ORIGIN };

// Origin untuk path media relatif (mis. "/media/..."). Foto Cloudinary sudah berupa
// URL penuh, jadi tidak lewat sini. Tidak lagi hardcode 127.0.0.1 supaya aman di production.
const MEDIA_ORIGIN = String(
  API_ORIGIN || import.meta.env.VITE_API_ORIGIN || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

// Sisipkan transformasi Cloudinary (format & kualitas otomatis + batas lebar) setelah "/upload/".
// Hanya jalan kalau `width` diberikan dan URL-nya memang Cloudinary. Selain itu URL dikembalikan apa adanya.
const withCloudinaryTransform = (url, width) => {
  if (!width || !url.includes("res.cloudinary.com") || !url.includes("/upload/")) return url;
  // Sudah ada transformasi di URL? Jangan ditumpuk.
  if (/\/upload\/[^/]*(f_auto|q_auto|w_\d+)/.test(url)) return url;

  // `width` dalam px CSS. Layar retina dapat 2x, dibatasi supaya tidak boros data.
  const dpr = typeof window !== "undefined" ? Math.min(window.devicePixelRatio || 1, 2) : 1;
  const px = Math.max(1, Math.round(width * dpr));
  return url.replace("/upload/", `/upload/f_auto,q_auto,c_limit,w_${px}/`);
};

/**
 * URL media siap pakai.
 *   getMediaUrl(url)       → URL asli (dipakai untuk share WhatsApp, supaya formatnya tidak berubah)
 *   getMediaUrl(url, 640)  → versi Cloudinary yang dioptimalkan untuk tampilan selebar ±640px
 */
export const getMediaUrl = (url, width) => {
  if (!url) return null;
  if (/^https?:\/\//i.test(url)) return withCloudinaryTransform(url, width);
  return `${MEDIA_ORIGIN}${url.startsWith("/") ? "" : "/"}${url}`;
};

// Eksport apiClient/api sebagai default dan named export
export const apiClient = api;
export default api;