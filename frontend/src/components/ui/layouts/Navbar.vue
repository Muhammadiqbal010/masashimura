<template>
  <nav
    v-if="!isAdminRoute"
    :class="[
      'fixed top-0 z-50 w-full transition-[background-color,padding,backdrop-filter] duration-300',
      isScrolled || isOpen
        ? 'bg-[#111111]/92 py-3 backdrop-blur-xl'
        : 'bg-transparent py-5',
    ]"
  >
    <div class="mx-auto flex max-w-7xl items-center justify-between px-6 md:px-12">

      <!-- Logo -->
      <router-link
        to="/"
        class="flex shrink-0 items-center"
        @click="closeMenu"
        aria-label="Masashimura – Beranda"
      >
        <img
          src="@/assets/masashimura-logo.png"
          alt="Masashimura"
          class="w-[128px] object-contain md:w-[152px]"
        />
      </router-link>

      <!-- Desktop Nav -->
      <div class="hidden items-center gap-1 md:flex">
        <router-link
          v-for="link in navLinks"
          :key="link.path"
          :to="link.path"
          class="relative rounded-xl px-4 py-2 text-sm font-semibold transition-colors duration-200"
          :class="isExact(link.path) ? 'text-white' : 'text-white/65 hover:text-white'"
          :aria-current="isExact(link.path) ? 'page' : undefined"
        >
          {{ link.name }}
          <!-- Penanda halaman aktif: titik kecil, bukan garis panjang -->
          <span
            class="absolute -bottom-0.5 left-1/2 h-1 w-1 -translate-x-1/2 rounded-full bg-[#FFD400] transition-opacity duration-200"
            :class="isExact(link.path) ? 'opacity-100' : 'opacity-0'"
            aria-hidden="true"
          />
        </router-link>
        <router-link
          to="/menu"
          class="ml-3 inline-flex items-center rounded-xl bg-[#D71920] px-5 py-2.5 text-sm font-bold text-white transition-colors duration-200 hover:bg-[#B5121B] active:scale-[0.98]"
        >
          Pesan sekarang
        </router-link>
      </div>

      <!-- Hamburger -->
      <button
        class="relative flex h-11 w-11 flex-col items-center justify-center gap-[5px] rounded-xl bg-white/[0.06] transition-colors hover:bg-white/[0.1] md:hidden"
        @click="toggleMenu"
        :aria-expanded="isOpen"
        aria-controls="mobile-menu"
        aria-label="Toggle navigasi"
      >
        <span
          class="block h-0.5 w-5 origin-center rounded bg-white transition-all duration-300"
          :class="isOpen ? 'translate-y-[7px] rotate-45' : ''"
        />
        <span
          class="block h-0.5 w-5 rounded bg-white transition-all duration-200"
          :class="isOpen ? 'w-0 opacity-0' : 'opacity-100'"
        />
        <span
          class="block h-0.5 w-5 origin-center rounded bg-white transition-all duration-300"
          :class="isOpen ? '-translate-y-[7px] -rotate-45' : ''"
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
        class="absolute left-0 top-full w-full bg-[#111111]/97 backdrop-blur-xl md:hidden"
      >
        <div class="mx-auto max-w-7xl space-y-1 px-6 pb-6 pt-3">
          <router-link
            v-for="link in navLinks"
            :key="link.path"
            :to="link.path"
            class="flex min-h-[48px] items-center justify-between rounded-xl px-4 text-base font-semibold transition-colors duration-200"
            :class="isExact(link.path)
              ? 'bg-white/[0.08] text-white'
              : 'text-white/75 hover:bg-white/[0.05] hover:text-white'"
            :aria-current="isExact(link.path) ? 'page' : undefined"
            @click="closeMenu"
          >
            {{ link.name }}
            <span v-if="isExact(link.path)" class="h-1.5 w-1.5 rounded-full bg-[#FFD400]" aria-hidden="true"></span>
          </router-link>
          <router-link
            to="/menu"
            class="mt-3 flex min-h-[48px] w-full items-center justify-center rounded-xl bg-[#D71920] px-4 text-base font-bold text-white transition-colors hover:bg-[#B5121B] active:scale-[0.98]"
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