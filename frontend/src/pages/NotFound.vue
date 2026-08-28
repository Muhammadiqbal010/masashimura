<template>
  <div class="not-found">
    <img :src="logo" alt="Masashimura" class="not-found__logo" />
    <h1>404</h1>
    <p>Halaman yang lu cari gak ketemu.</p>
    <router-link to="/" class="not-found__link">Kembali ke Beranda</router-link>
  </div>
</template>

<script setup>
import logo from "../assets/masashimura-logo.png";
</script>

<style scoped>
.not-found {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  background: #080808;
  color: #fff;
  text-align: center;
  padding: 2rem;
}
.not-found__logo {
  width: 280px;
  max-width: 80%;
  height: auto;
}
.not-found h1 {
  font-size: 5rem;
  margin: 0;
  color: #dc2626;
  font-family: 'Oswald', sans-serif;
  letter-spacing: 2px;
}
.not-found p {
  color: #aaa;
  font-family: 'Inter', sans-serif;
}
.not-found__link {
  margin-top: 0.5rem;
  padding: 0.6rem 1.5rem;
  background: #dc2626;
  color: #fff;
  border-radius: 6px;
  text-decoration: none;
  font-family: 'Inter', sans-serif;
  transition: opacity 0.2s;
}
.not-found__link:hover {
  opacity: 0.85;
}
</style>