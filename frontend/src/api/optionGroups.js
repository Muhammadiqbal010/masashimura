import apiClient from "./client";

// Library "Grup Opsi" (Level Pedas, Suhu, Topping, dst) yang dibuat sekali lalu
// dipasang ke banyak menu. Bentuk data:
//   { id, name, required, multiple, choices: [{ label, price }],
//     menu_ids: [..], menu_count }
export const optionGroupAPI = {
  getAll: () => apiClient.get("/option-groups/"),
  create: (data) => apiClient.post("/option-groups/", data),
  update: (id, data) => apiClient.patch(`/option-groups/${id}/`, data),
  delete: (id) => apiClient.delete(`/option-groups/${id}/`),
};
