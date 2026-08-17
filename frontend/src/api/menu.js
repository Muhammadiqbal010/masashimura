import apiClient from "./client";

export const menuAPI = {
  // Catatan: filter kategori dilakukan di FRONTEND (lihat Menu.vue -> filteredMenus).
  // Endpoint ini sengaja tidak menerima parameter kategori, supaya tidak ada
  // parameter yang dikirim tapi diabaikan oleh fungsi ini (bug sebelumnya).
  // Kalau nanti backend sudah mendukung filter server-side, tinggal tambahkan:
  //   getAll: (category) => apiClient.get("/menus/", { params: { category } })
  getAll: () => apiClient.get("/menus/"),
  create: (formData) =>
    apiClient.post("/menus/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  update: (id, formData) =>
    apiClient.put(`/menus/${id}/`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  delete: (id) => apiClient.delete(`/menus/${id}/`),
};
