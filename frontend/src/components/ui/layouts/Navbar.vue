<template>
  <nav
    v-if="!isAdminRoute"
    :class="[
      'site-nav fixed top-0 z-50 w-full transition-[padding,background-color] duration-300',
      isScrolled || isOpen ? 'is-solid py-2.5' : 'py-4',
    ]"
  >
    <div class="mx-auto flex max-w-7xl items-center justify-between px-5 sm:px-8 lg:px-10">

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
          class="w-[128px] object-contain transition-all duration-300 md:w-[148px]"
        />
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
          {{ link.name }}
        </router-link>
        <router-link to="/menu" class="nav-cta ml-4">
          Pesan sekarang
        </router-link>
      </div>

      <!-- Hamburger -->
      <button
        class="relative flex h-11 w-11 flex-col items-center justify-center gap-[5px] rounded-xl border border-white/12 bg-white/[0.05] md:hidden"
        @click="toggleMenu"
        :aria-expanded="isOpen"
        aria-controls="mobile-menu"
        aria-label="Buka atau tutup navigasi"
      >
        <span
          class="block h-0.5 w-5 origin-center rounded bg-white transition-all duration-300"
          :class="isOpen ? 'translate-y-[7px] rotate-45' : ''"
        />
        <span
          class="block h-0.5 rounded bg-[#F4C542] transition-all duration-200"
          :class="isOpen ? 'w-0 opacity-0' : 'w-3.5 opacity-90'"
        />
        <span
          class="block h-0.5 w-5 origin-center rounded bg-white transition-all duration-300"
          :class="isOpen ? '-translate-y-[7px] -rotate-45' : ''"
        />
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
      <div
        v-if="isOpen"
        id="mobile-menu"
        class="absolute left-0 top-full w-full bg-[#111113] pb-6 md:hidden"
      >
        <div class="mx-auto max-w-7xl space-y-1 px-5 pt-2 sm:px-8">
          <router-link
            v-for="link in navLinks"
            :key="link.path"
            :to="link.path"
            class="flex min-h-[52px] items-center justify-between rounded-xl px-4 text-base font-semibold transition-colors duration-200"
            :class="isExact(link.path)
              ? 'bg-[#F4C542]/12 text-[#F4C542]'
              : 'text-white/80 hover:bg-white/[0.05] hover:text-white'"
            @click="closeMenu"
          >
            {{ link.name }}
            <span v-if="isExact(link.path)" class="h-2 w-2 rounded-full bg-[#F4C542]" aria-hidden="true"></span>
          </router-link>
          <router-link
            to="/menu"
            class="nav-cta mt-3 flex w-full !min-h-[52px] justify-center text-base"
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

<style scoped>
/* Bar charcoal menyatu dengan hero gelap — tanpa garis pemisah */
.site-nav { background: linear-gradient(180deg, #111113 0%, rgb(17 17 19 / 0.88) 100%); }
.site-nav.is-solid { background: rgb(17 17 19 / 0.94); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); }

.nav-link {
  position: relative;
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  padding: 0 0.95rem;
  border-radius: 10px;
  font-size: 0.875rem;
  font-weight: 600;
  color: rgb(255 255 255 / 0.78);
  transition: color 0.2s;
}
.nav-link:hover { color: #fff; }
.nav-link.is-active { color: #F4C542; }
.nav-link.is-active::after {
  content: "";
  position: absolute;
  left: 50%;
  bottom: 4px;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #F4C542;
  transform: translateX(-50%);
}

.nav-cta {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  padding: 0 1.4rem;
  border-radius: 12px;
  background: #D92B22;
  color: #fff;
  font-size: 0.875rem;
  font-weight: 700;
  transition: background 0.2s, transform 0.15s;
}
.nav-cta:hover { background: #B8201A; }
.nav-cta:active { transform: translateY(1px); }
</style>
