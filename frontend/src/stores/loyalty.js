// src/stores/loyalty.js
import { defineStore } from "pinia";
import { ref } from "vue";
import { statsAPI } from "@/api";

export const useLoyaltyStore = defineStore("loyalty", () => {
  const loyalCustomers = ref([]);
  const expiryMonths = ref(0);
  const segments = ref([]);
  const loading = ref(false);
  const error = ref("");

  const fetchLoyalCustomers = async () => {
    loading.value = true;
    error.value = "";

    try {
      const { data } = await statsAPI.getLoyalCustomers();

      if (Array.isArray(data?.customers)) {
        // Bentuk respons saat ini: { settings, customers }
        loyalCustomers.value = data.customers;
        expiryMonths.value = data.settings?.points_expiry_months ?? 0;
        segments.value = Array.isArray(data.segments) ? data.segments : [];
      } else if (Array.isArray(data)) {
        loyalCustomers.value = data;
      } else {
        loyalCustomers.value = [];
      }
    } catch (err) {
      // JANGAN pernah mengisi data dummy di sini: admin bisa mengira itu pelanggan
      // asli dan menyesuaikan poinnya. Cukup kosongkan dan tampilkan error yang jujur.
      loyalCustomers.value = [];
      segments.value = [];
      const status = err?.response?.status;
      if (!err?.response) {
        error.value = "Tidak dapat terhubung ke server. Periksa koneksi lalu coba lagi.";
      } else if (status === 403) {
        error.value = "Akun kamu tidak punya akses ke data pelanggan loyal.";
      } else {
        error.value = `Server mengembalikan error (${status}). Data pelanggan tidak hilang, coba lagi sebentar.`;
      }
      console.error("Gagal memuat pelanggan loyal:", err);
    } finally {
      loading.value = false;
    }
  };

  return {
    loyalCustomers,
    expiryMonths,
    segments,
    loading,
    error,
    fetchLoyalCustomers,
  };
});