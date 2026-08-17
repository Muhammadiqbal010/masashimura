<template>
  <div class="min-h-screen bg-[#050505] font-manrope">
    <!-- 🟢 Halaman Publik (Muncul Navbar & Footer) -->
    <!-- Logika: Jika BUKAN rute admin DAN BUKAN rute yang disembunyikan metanya -->
    <template v-if="!isAdminRoute && !route.meta.hideNavFooter">
      <Navbar />
      <router-view />
      <Footer />
    </template>

    <!-- 🔒 Halaman Internal Area / Login / Register (Tanpa Navbar & Footer Publik) -->
    <template v-else>
      <router-view />
    </template>

    <Toaster position="top-center" richColors theme="dark" expand />
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import { Toaster } from "vue-sonner";

// Pastikan path import merujuk langsung ke file .vue
import Navbar from "@/components/ui/layouts/Navbar.vue";
import Footer from "@/components/ui/layouts/Footer.vue";

const route = useRoute();

// Mengecek apakah user sedang berada di halaman yang diawali dengan /admin
const isAdminRoute = computed(() => route.path.startsWith("/admin"));
</script>