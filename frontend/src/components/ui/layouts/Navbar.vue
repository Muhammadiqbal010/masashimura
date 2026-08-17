<template>
  <nav
    v-if="!isAdminRoute"
    :class="[
      'fixed top-0 w-full z-50 transition-all duration-500',
      isScrolled || isOpen
        ? 'bg-[#060606]/95 backdrop-blur-xl border-b border-white/[0.06] py-3'
        : 'bg-transparent py-5',
    ]"
  >
    <!-- Progress shimmer line saat scrolled -->
    <div
      class="absolute bottom-0 left-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent w-full transition-opacity duration-500"
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
      <div class="hidden md:flex items-center gap-1">
        <router-link
          v-for="link in navLinks"
          :key="link.path"
          :to="link.path"
          class="relative px-4 py-2 text-[11px] uppercase tracking-[0.2em] font-bold font-oswald transition-colors duration-200 group"
          :class="isExact(link.path) ? 'text-white' : 'text-white/40 hover:text-white/80'"
        >
          {{ link.name }}
          <!-- Animated underline -->
          <span
            class="absolute bottom-0 left-4 right-4 h-px bg-[#DC2626] transition-all duration-300 origin-left"
            :class="isExact(link.path) ? 'scale-x-100 opacity-100' : 'scale-x-0 opacity-0 group-hover:scale-x-100 group-hover:opacity-60'"
          />
        </router-link>
      </div>

      <!-- Hamburger -->
      <button
        class="md:hidden relative w-10 h-10 flex flex-col items-center justify-center gap-[5px] cursor-pointer group"
        @click="toggleMenu"
        :aria-expanded="isOpen"
        aria-label="Toggle navigasi"
      >
        <span
          class="block w-5 h-px bg-white transition-all duration-300 origin-center"
          :class="isOpen ? 'rotate-45 translate-y-[6px]' : ''"
        />
        <span
          class="block h-px bg-white transition-all duration-200"
          :class="isOpen ? 'w-0 opacity-0' : 'w-4 opacity-60'"
        />
        <span
          class="block w-5 h-px bg-white transition-all duration-300 origin-center"
          :class="isOpen ? '-rotate-45 -translate-y-[6px]' : ''"
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
        class="md:hidden absolute top-full left-0 w-full bg-[#060606]/98 backdrop-blur-xl border-b border-white/[0.06] shadow-2xl"
      >
        <div class="max-w-7xl mx-auto px-6 py-6 space-y-1">
          <router-link
            v-for="link in navLinks"
            :key="link.path"
            :to="link.path"
            class="flex items-center justify-between px-4 py-4 rounded-xl transition-all duration-200 group"
            :class="isExact(link.path)
              ? 'bg-white/[0.04] text-white'
              : 'text-white/40 hover:text-white hover:bg-white/[0.03]'"
            @click="closeMenu"
          >
            <span class="font-oswald text-base uppercase tracking-[0.15em] font-bold">{{ link.name }}</span>
            <span
              class="text-[#DC2626] text-lg transition-transform duration-200 group-hover:translate-x-0.5"
              :class="isExact(link.path) ? 'opacity-100' : 'opacity-0 group-hover:opacity-60'"
            >→</span>
          </router-link>
        </div>
      </div>
    </Transition>
  </nav>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue"
import { useRoute } from "vue-router"

const route = useRoute()

const isOpen    = ref(false)
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

const toggleMenu  = () => { isOpen.value = !isOpen.value }
const closeMenu   = () => { isOpen.value = false }

// Tutup mobile menu saat pindah halaman
watch(() => route.path, closeMenu)

// Kunci scroll body saat mobile menu terbuka
watch(isOpen, (val) => {
  document.body.style.overflow = val ? "hidden" : ""
})

const handleScroll = () => { isScrolled.value = window.scrollY > 40 }

onMounted(() => {
  window.addEventListener("scroll", handleScroll, { passive: true })
  handleScroll()
})
onUnmounted(() => {
  window.removeEventListener("scroll", handleScroll)
  document.body.style.overflow = ""
})
</script>