// src/stores/loyalty.js
import { defineStore } from "pinia";
import { ref } from "vue";
import { statsAPI } from "@/api";

export const useLoyaltyStore = defineStore("loyalty", () => {
  const loyalCustomers = ref([]);
  const loading = ref(false);

  const fetchLoyalCustomers = async () => {
    loading.value = true;

    try {
      const response = await statsAPI.getLoyalCustomers();
      // Pastikan data yang diterima adalah array sebelum disimpan
      loyalCustomers.value = Array.isArray(response.data) ? response.data : [];
    } catch (error) {
      console.warn(
        "⚠️ Gagal mengambil data pelanggan loyal, menggunakan dummy data:",
        error,
      );

      // Dummy data tetap disediakan agar UI tetap bisa diuji saat backend belum siap
      loyalCustomers.value = [
        {
          phone: "6281234567890",
          name: "Budi",
          total_orders: 15,
          total_spent: 2450000,
          points: 42,
          last_order_at: new Date().toISOString(),
          points_expired: false,
        },
        {
          phone: "6289876543210",
          name: "Siti",
          total_orders: 12,
          total_spent: 1850000,
          points: 8,
          last_order_at: new Date().toISOString(),
          points_expired: false,
        },
      ];
    } finally {
      loading.value = false;
    }
  };

  return {
    loyalCustomers,
    loading,
    fetchLoyalCustomers,
  };
});