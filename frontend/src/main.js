// src/main.js
import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import { useAuthStore } from "./stores/auth";
import "./index.css";

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);

// Inisialisasi Auth Store setelah Pinia aktif
const auth = useAuthStore();
auth.checkAuth(); // Ini penting agar user langsung ter-load

app.mount("#app");
