import apiClient from "./client";

export const authAPI = {
  login: async (credentials) => {
    const response = await apiClient.post("/auth/login/", credentials);
    if (response.data.token) {
      localStorage.setItem("token", response.data.token);
      localStorage.setItem("role", response.data.user.role);
    }
    return response;
  },
  
  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("user"); 
  },

  createUser: (data) => {
    return apiClient.post("/auth/users/create/", data);
  },
};
