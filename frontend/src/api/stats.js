import apiClient from "./client";

export const statsAPI = {
  getDashboardSummary: () => apiClient.get("/orders/stats/"),
  getLoyalCustomers: (month = null) => {
    const params = month ? { month } : {};
    return apiClient.get("/orders/loyal/", { params });
  },
  getMonthlyStats: (year = null) => {
    const params = year ? { year } : {};
    return apiClient.get("/stats/monthly/", { params });
  },
};
