import axios from "axios";

// 1. Definisikan Base URL dan Export API_ORIGIN
const API_BASE_URL = "http://127.0.0.1:8000/api";
export const API_ORIGIN = "http://127.0.0.1:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor Request
apiClient.interceptors.request.use(
  (config) => {
    if (config.url.includes("/login/")) return config;

    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Token ${token}`;
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
      localStorage.removeItem("token");
      localStorage.removeItem("role");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// Helper function
export const getMediaUrl = (path) => {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  return `${API_ORIGIN}${path.startsWith('/') ? '' : '/'}${path}`;
};

export default apiClient;