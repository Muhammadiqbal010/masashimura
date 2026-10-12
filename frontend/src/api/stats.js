import apiClient from "./client";

export const statsAPI = {
  getDashboardSummary: () => apiClient.get("/orders/stats/"),
  // Respons: { settings, customers: [...] }
  getLoyalCustomers: () => apiClient.get("/orders/loyal-customers/"),
};