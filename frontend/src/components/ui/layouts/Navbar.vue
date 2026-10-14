<template>
  <nav
    v-if="!isAdminRoute"
    :class="[
      'fixed top-0 w-full z-50 transition-all duration-500',
      isScrolled || isOpen
        ? 'bg-[#060606]/90 backdrop-blur-xl border-b border-white/[0.08] py-3'
        : 'bg-gradient-to-b from-black/70 to-transparent py-5',
    ]"
  >
    <!-- Progress shimmer line saat scrolled -->
    <div
      class="absolute bottom-0 left-0 h-[2px] w-full bg-gradient-to-r from-[#EE0000] via-[#EE0000] to-[#FFF500] transition-opacity duration-500"
      :class="isScrolled ? 'opacity-100' : 'opacity-0'"
    />

    <div class="max-w-7xl mx-auto px-6 md:px-12 flex justify-between items-center">

      <!-- Logo -->
      <router-link
        to="/"
        class="flex items-center shrink-0"
        @click="closeMenu"
        aria-label="Masashimura – Beranda"
      >
        <img
          src="@/assets/masashimura-logo.png"
          alt="Masashimura"
          class="object-contain transition-all duration-300 w-[130px] md:w-[160px]"
          :class="isScrolled ? 'opacity-90' : 'opacity-100'"
        />
      </router-link>

      <!-- Desktop Nav -->
      <div class="hidden md:flex items-center gap-2">
        <router-link
          v-for="link in navLinks"
          :key="link.path"
          :to="link.path"
          class="relative rounded-full px-4 py-2 text-sm font-semibold transition-colors duration-200"
          :class="isExact(link.path) ? 'text-[#FFF500]' : 'text-white/70 hover:text-white'"
          :aria-current="isExact(link.path) ? 'page' : undefined"
        >
          {{ link.name }}
          <span
            class="absolute -bottom-0.5 left-4 right-4 h-[2px] rounded-full bg-[#FFF500] transition-transform duration-300 origin-left"
            :class="isExact(link.path) ? 'scale-x-100' : 'scale-x-0'"
          />
        </router-link>
        <router-link
          to="/menu"
          class="ml-3 inline-flex items-center rounded-full bg-[#EE0000] px-5 py-2.5 text-sm font-bold text-white transition hover:bg-[#C20000] hover:shadow-[0_8px_24px_-8px_rgba(238,0,0,0.7)] active:scale-95"
        >
          Pesan sekarang
        </router-link>
      </div>

      <!-- Hamburger -->
      <button
        class="md:hidden relative w-10 h-10 flex flex-col items-center justify-center gap-[5px] cursor-pointer rounded-xl border border-white/10 bg-white/[0.04]"
        @click="toggleMenu"
        :aria-expanded="isOpen"
        aria-controls="mobile-menu"
        aria-label="Toggle navigasi"
      >
        <span
          class="block w-5 h-0.5 rounded bg-white transition-all duration-300 origin-center"
          :class="isOpen ? 'rotate-45 translate-y-[7px]' : ''"
        />
        <span
          class="block h-0.5 rounded bg-[#FFF500] transition-all duration-200"
          :class="isOpen ? 'w-0 opacity-0' : 'w-4 opacity-60'"
        />
        <span
          class="block w-5 h-0.5 rounded bg-white transition-all duration-300 origin-center"
          :class="isOpen ? '-rotate-45 -translate-y-[7px]' : ''"
        />
      </button>
    </div>

    <!-- Mobile Menu -->
    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0 -translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-2"
    >
      <div
        v-if="isOpen"
        id="mobile-menu"
        class="md:hidden absolute top-full left-0 w-full bg-[#060606]/95 backdrop-blur-xl border-b border-white/[0.06] shadow-2xl"
      >
        <div class="max-w-7xl mx-auto px-6 py-5 space-y-1">
          <router-link
            v-for="link in navLinks"
            :key="link.path"
            :to="link.path"
            class="flex items-center justify-between rounded-xl px-4 py-4 text-base font-semibold transition-colors duration-200"
            :class="isExact(link.path)
              ? 'bg-[#FFF500]/10 text-[#FFF500]'
              : 'text-white/80 hover:bg-white/[0.05] hover:text-white'"
            @click="closeMenu"
          >
            {{ link.name }}
            <span v-if="isExact(link.path)" class="h-2 w-2 rounded-full bg-[#FFF500]" aria-hidden="true"></span>
          </router-link>
          <router-link
            to="/menu"
            class="mt-3 flex w-full items-center justify-center rounded-xl bg-[#EE0000] px-4 py-4 text-base font-bold text-white active:scale-[0.98]"
            @click="closeMenu"
          >
            Pesan sekarang
          </router-link>
        </div>
      </div>
    </Transition>
  </nav>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue"
import { useRoute } from "vue-router"
import { useScrollLock } from "@/composables/useScrollLock"

const route = useRoute()
const { lock, unlock } = useScrollLock()

const isOpen     = ref(false)
const isScrolled = ref(false)

const isAdminRoute = computed(() => route.path.startsWith("/admin"))

const navLinks = [
  { name: "Home",   path: "/" },
  { name: "Menu",   path: "/menu" },
  { name: "Kontak", path: "/contact" },
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