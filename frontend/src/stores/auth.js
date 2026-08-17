// src/stores/auth.js
import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { authAPI } from "@/api";

export const useAuthStore = defineStore("auth", () => {
  const user = ref(null);
  const loading = ref(false);
  const error = ref(null);

  // Computed Properties untuk Role
  const isOwner = computed(() => user.value?.role === "owner");
  const isAdmin = computed(() => user.value?.role === "admin");
  const isKasir = computed(() => user.value?.role === "kasir");
  const isLoggedIn = computed(() => !!user.value);

  // Getter untuk role saat ini (default ke 'pelanggan' jika tidak ada)
  const userRole = computed(() => user.value?.role || "pelanggan");

  const checkAuth = () => {
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      try {
        user.value = JSON.parse(savedUser);
      } catch (e) {
        logout();
      }
    }
  };

  const mapUserRole = (userData) => {
    if (!userData) return null;
    const updatedUser = { ...userData };

    if (updatedUser.is_superuser) updatedUser.role = "owner";
    else if (updatedUser.is_staff) updatedUser.role = "admin";
    else if (!updatedUser.role || updatedUser.role === "-")
      updatedUser.role = "kasir";

    return updatedUser;
  };

  const login = async (credentials) => {
    loading.value = true;
    error.value = null; // Reset error sebelum login
    try {
      const response = await authAPI.login(credentials);
      const { token, user: userData } = response.data;
      const processedUser = mapUserRole(userData);

      localStorage.setItem("token", token);
      localStorage.setItem("user", JSON.stringify(processedUser));
      localStorage.setItem("role", processedUser.role);

      user.value = processedUser;
      return processedUser;
    } catch (err) {
      // Mengambil error spesifik dari response Django (jika ada non_field_errors)
      error.value =
        err.response?.data?.non_field_errors?.[0] ||
        err.response?.data?.detail ||
        "Login gagal. Periksa kembali username/password.";
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const logout = () => {
    user.value = null;
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("role");
    window.location.href = "/login";
  };

  return {
    user,
    loading,
    error,
    isOwner,
    isAdmin,
    isKasir,
    isLoggedIn,
    userRole,
    checkAuth,
    login,
    logout,
  };
});
