<template>
  <footer class="bg-[#1B1B1B] text-white">
    <div class="mx-auto max-w-7xl px-6 pb-8 pt-16 md:px-12 md:pt-20">
      <div class="grid grid-cols-2 gap-x-8 gap-y-12 pb-14 md:grid-cols-12">

        <!-- Brand -->
        <div class="col-span-2 space-y-5 md:col-span-5">
          <img
            src="@/assets/masashimura-logo.png"
            alt="Masashimura"
            loading="lazy"
            class="pointer-events-none h-10 w-auto select-none md:h-12"
          />
          <p class="max-w-xs text-sm leading-relaxed text-white/70">
            Warkop modern di jantung Bekasi. Cozy, kustom, harga bersahabat.
          </p>
          <div class="flex items-center gap-2.5">
            <a
              v-for="s in socials"
              :key="s.href"
              :href="s.href"
              :aria-label="s.label"
              target="_blank"
              rel="noopener noreferrer"
              class="flex h-11 w-11 items-center justify-center rounded-xl bg-white/[0.06] text-white/75 transition-colors duration-200 hover:bg-[#FFD400] hover:text-[#171717]"
            >
              <component :is="s.icon" :size="18" />
            </a>
          </div>
        </div>

        <!-- Halaman -->
        <div class="col-span-2 space-y-4 md:col-span-3">
          <h3 class="text-sm font-semibold text-white">Halaman</h3>
          <nav class="space-y-0.5" aria-label="Footer">
            <router-link
              v-for="link in navLinks"
              :key="link.path"
              :to="link.path"
              class="flex py-2 text-sm text-white/70 transition-colors duration-150 hover:text-white"
            >
              {{ link.name }}
            </router-link>
          </nav>
        </div>

        <!-- Kontak -->
        <div class="col-span-2 space-y-4 md:col-span-4">
          <h3 class="text-sm font-semibold text-white">Kontak</h3>
          <div class="space-y-5">
            <a href="mailto:kedaimasashimura@gmail.com" class="group flex items-start gap-3">
              <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white/[0.06]">
                <Mail :size="15" class="text-white/70" />
              </span>
              <span class="break-all pt-1.5 text-sm leading-snug text-white/70 transition-colors duration-150 group-hover:text-white">
                kedaimasashimura@gmail.com
              </span>
            </a>

            <div class="flex items-start gap-3">
              <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white/[0.06]">
                <MapPin :size="15" class="text-white/70" />
              </span>
              <div class="space-y-1 pt-0.5">
                <p class="text-sm font-semibold leading-snug text-white">Jl. Pintu Air No.48</p>
                <p class="text-sm leading-relaxed text-white/60">
                  Harapan Mulya, Medan Satria,<br />Kota Bekasi, Jawa Barat
                </p>
                <a
                  href="https://maps.app.goo.gl/xtLih1iDMfdLnqQC8"
                  target="_blank"
                  rel="noopener"
                  class="inline-flex items-center gap-1 pt-1 text-sm font-semibold text-white underline-offset-4 transition-colors hover:text-[#FFD400] hover:underline"
                >
                  Buka di Maps <span aria-hidden="true">↗</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Bar bawah: dipisahkan oleh jarak, bukan garis -->
      <div class="flex flex-col items-center justify-between gap-4 pt-2 sm:flex-row">
        <p class="text-xs text-white/50">&copy; {{ currentYear }} Masashimura. All rights reserved.</p>
        <div class="flex flex-col items-center gap-1.5 text-center sm:flex-row sm:gap-6 sm:text-right" role="status">
          <span class="flex items-center gap-2">
            <span
              class="inline-flex h-2 w-2 shrink-0 rounded-full"
              :class="status.isOpen ? 'bg-emerald-400' : 'bg-[#D71920]'"
              aria-hidden="true"
            />
            <span class="text-xs font-semibold text-white/85">
              {{ status.label }}<template v-if="status.detail"> · {{ status.detail }}</template>
            </span>
          </span>
          <span class="text-xs text-white/50">{{ scheduleText }}</span>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed } from "vue"
import { Instagram, Music4, Mail, MapPin } from "lucide-vue-next"
import { useOpenStatus } from "@/composables/useOpenStatus"

const currentYear = computed(() => new Date().getFullYear())
const { status, scheduleText } = useOpenStatus()

const navLinks = [
  { name: "Home",   path: "/" },
  { name: "Menu",   path: "/menu" },
  { name: "Kontak", path: "/contact" },
]

const socials = [
  { href: "https://www.instagram.com/masashimura.id", label: "Instagram Masashimura", icon: Instagram },
  { href: "https://www.tiktok.com/@masashimura.id",   label: "TikTok Masashimura",    icon: Music4    },
]
</script>