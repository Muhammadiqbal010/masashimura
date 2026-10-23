<template>
  <nav v-if="!isAdminRoute" class="site-nav fixed inset-x-0 top-0 z-50 px-3 pt-3 sm:px-6 sm:pt-4" aria-label="Navigasi utama">
    <div class="nav-pill mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-2 sm:px-5" :class="{ 'is-solid': isScrolled || isOpen }">

      <!-- Logo -->
      <router-link to="/" class="flex shrink-0 items-center" @click="closeMenu" aria-label="Masashimura – Beranda">
        <img src="@/assets/masashimura-logo.png" alt="Masashimura" class="h-7 w-auto object-contain sm:h-8" />
      </router-link>

      <!-- Desktop Nav -->
      <div class="hidden items-center gap-1 md:flex">
        <router-link
          v-for="link in navLinks"
          :key="link.path"
          :to="link.path"
          class="nav-link"
          :class="{ 'is-active': isExact(link.path) }"
          :aria-current="isExact(link.path) ? 'page' : undefined"
        >
          <span class="nav-link-label">{{ link.name }}</span>
          <span class="nav-link-jp" aria-hidden="true">{{ link.jp }}</span>
        </router-link>
      </div>

      <div class="hidden md:block">
        <router-link to="/menu" class="pop-btn pop-btn--on-dark nav-cta">
          Pesan sekarang
          <span class="pop-btn-dot" aria-hidden="true"><ArrowUpRight :size="15" /></span>
        </router-link>
      </div>

      <!-- Hamburger -->
      <button
        class="flex h-11 w-11 flex-col items-center justify-center gap-[5px] rounded-full border-2 border-[#F4C542] bg-[#F4C542] md:hidden"
        @click="toggleMenu"
        :aria-expanded="isOpen"
        aria-controls="mobile-menu"
        aria-label="Buka atau tutup navigasi"
      >
        <span class="block h-0.5 w-5 origin-center rounded bg-[#111113] transition-all duration-300" :class="isOpen ? 'translate-y-[7px] rotate-45' : ''" />
        <span class="block h-0.5 w-5 rounded bg-[#111113] transition-all duration-200" :class="isOpen ? 'opacity-0' : ''" />
        <span class="block h-0.5 w-5 origin-center rounded bg-[#111113] transition-all duration-300" :class="isOpen ? '-translate-y-[7px] -rotate-45' : ''" />
      </button>
    </div>

    <!-- Mobile Menu -->
    <Transition
      enter-active-class="transition-all duration-250 ease-out"
      enter-from-class="opacity-0 -translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition-all duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-2"
    >
      <div v-if="isOpen" id="mobile-menu" class="mobile-sheet mx-auto mt-2 max-w-6xl p-3 md:hidden">
        <router-link
          v-for="link in navLinks"
          :key="link.path"
          :to="link.path"
          class="flex min-h-[56px] items-center justify-between rounded-2xl px-4 transition-colors"
          :class="isExact(link.path) ? 'bg-[#F4C542] text-[#111113]' : 'text-white/85 hover:bg-white/[0.07]'"
          @click="closeMenu"
        >
          <span class="text-base font-extrabold">{{ link.name }}</span>
          <span class="text-xs font-semibold opacity-70" aria-hidden="true">{{ link.jp }}</span>
        </router-link>
        <router-link to="/menu" class="pop-btn pop-btn--on-dark mt-3 w-full" @click="closeMenu">
          Pesan sekarang
          <span class="pop-btn-dot" aria-hidden="true"><ArrowUpRight :size="15" /></span>
        </router-link>
      </div>
    </Transition>
  </nav>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue"
import { useRoute } from "vue-router"
import { ArrowUpRight } from "lucide-vue-next"
import { useScrollLock } from "@/composables/useScrollLock"

const route = useRoute()
const { lock, unlock } = useScrollLock()

const isOpen     = ref(false)
const isScrolled = ref(false)

const isAdminRoute = computed(() => route.path.startsWith("/admin"))

const navLinks = [
  { name: "Home",   jp: "ホーム",  path: "/" },
  { name: "Menu",   jp: "メニュー", path: "/menu" },
  { name: "Kontak", jp: "連絡",    path: "/contact" },
]

// Exact match — "/" harus exact agar tidak aktif di semua halaman
const isExact = (path) =>
  path === "/" ? route.path === "/" : route.path.startsWith(path)

const toggleMenu = () => { isOpen.value = !isOpen.value }
const closeMenu  = () => { isOpen.value = false }

// Tutup mobile menu saat pindah halaman
watch(() => route.path, closeMenu)

// Kunci scroll lewat composable terpusat (tidak bentrok dengan lightbox)
watch(isOpen, (val) => (val ? lock() : unlock()))

const handleScroll = () => { isScrolled.value = window.scrollY > 40 }
const handleKeydown = (e) => {
  if (e.key === "Escape" && isOpen.value) closeMenu()
}

onMounted(() => {
  window.addEventListener("scroll", handleScroll, { passive: true })
  window.addEventListener("keydown", handleKeydown)
  handleScroll()
})
onUnmounted(() => {
  window.removeEventListener("scroll", handleScroll)
  window.removeEventListener("keydown", handleKeydown)
})
</script>

<style scoped>
.nav-pill {
  border: 2px solid rgb(255 255 255 / 0.12);
  border-radius: 999px;
  background: rgb(17 17 19 / 0.9);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  transition: background-color 0.25s, border-color 0.25s;
}
.nav-pill.is-solid { background: rgb(17 17 19 / 0.95); border-color: rgb(255 255 255 / 0.2); }

.nav-link {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 48px;
  padding: 0 1.15rem;
  border-radius: 999px;
  color: rgb(255 255 255 / 0.82);
  line-height: 1.1;
  transition: background-color 0.2s, color 0.2s;
}
.nav-link:hover { color: #fff; background: rgb(255 255 255 / 0.08); }
.nav-link-label { font-size: 0.9375rem; font-weight: 800; }
.nav-link-jp { margin-top: 2px; font-size: 0.6875rem; font-weight: 500; opacity: 0.6; }
.nav-link.is-active { background: #F4C542; color: #111113; }
.nav-link.is-active:hover { background: #F4C542; }
.nav-cta { min-height: 46px; padding: 0 0.5rem 0 1.25rem; font-size: 0.875rem; }

.mobile-sheet {
  border: 2px solid rgb(255 255 255 / 0.14);
  border-radius: 28px;
  background: rgb(17 17 19 / 0.97);
  backdrop-filter: blur(14px);
}
</style>
