import axios from "axios";

// 1. Definisikan Base URL dan Export API_ORIGIN
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";
export const API_ORIGIN = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL.replace(/\/api\/?$/, "")
  : "http://127.0.0.1:8000";

// Path login staff (harus sama dengan route "Login" di router)
const LOGIN_PATH = "/masashimura-internalakses";

// Endpoint publik (GET) yang TIDAK boleh bawa token.
// Kalau token basi ikut terkirim, DRF balas 401 walau endpoint-nya AllowAny.
const PUBLIC_GET_PREFIXES = [
  "/homepage/",
  "/menus/bestsellers/",
];

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

const normalizeUrl = (url = "") => (url.startsWith("/") ? url : `/${url}`);

const isPublicGet = (config) => {
  const method = (config.method || "get").toLowerCase();
  if (method !== "get") return false;
  const url = normalizeUrl(config.url);
  return PUBLIC_GET_PREFIXES.some((prefix) => url.startsWith(prefix));
};

const clearSession = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("role");
  localStorage.removeItem("user");
};

// Interceptor Request
apiClient.interceptors.request.use(
  (config) => {
    // Endpoint login: jangan kirim token
    if (config.url.includes("/login/")) return config;

    // Endpoint publik: jangan kirim token
    if (!isPublicGet(config)) {
      const token = localStorage.getItem("token");
      if (token) {
        config.headers.Authorization = `Token ${token}`;
      }
    }

    // Kalau body-nya FormData (upload file), JANGAN paksa Content-Type json.
    // Biarkan browser yang set otomatis multipart/form-data + boundary-nya.
    if (config.data instanceof FormData) {
      delete config.headers["Content-Type"];
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor Response
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const requestUrl = error.config?.url || "";

      // 401 dari form login = password salah, bukan sesi habis.
      // Biarkan halaman login yang nampilin pesan errornya.
      if (requestUrl.includes("/login/")) {
        return Promise.reject(error);
      }

      // Token memang invalid, bersihkan supaya gak kebawa terus
      clearSession();

      // Redirect HANYA kalau lagi di area admin.
      // Pengunjung publik jangan pernah dilempar ke halaman login.
      const { pathname } = window.location;
      if (pathname.startsWith("/admin")) {
        window.location.href = LOGIN_PATH;
      }
    }
    return Promise.reject(error);
  }
);

// Helper function
export const getMediaUrl = (path) => {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  return `${API_ORIGIN}${path.startsWith("/") ? "" : "/"}${path}`;
};

export default apiClient;