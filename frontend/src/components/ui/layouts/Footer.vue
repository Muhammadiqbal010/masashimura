<template>
  <footer class="site-footer relative overflow-hidden bg-[#111113] text-white">
    <div class="relative mx-auto max-w-7xl px-5 pb-8 pt-16 sm:px-8 lg:px-10 lg:pt-20">
      <div class="grid grid-cols-1 gap-12 pb-12 sm:grid-cols-2 lg:grid-cols-12">

        <!-- Brand -->
        <div class="space-y-5 sm:col-span-2 lg:col-span-5">
          <img
            src="@/assets/masashimura-logo.png"
            alt="Masashimura"
            loading="lazy"
            class="pointer-events-none h-11 w-auto select-none"
          />
          <p class="max-w-xs text-[0.9375rem] leading-relaxed text-[#B8B8C0]">
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
              class="flex h-11 w-11 items-center justify-center rounded-xl bg-white/[0.07] text-white/80 transition-colors duration-200 hover:bg-[#F4C542] hover:text-[#111113]"
            >
              <component :is="s.icon" :size="18" />
            </a>
          </div>
        </div>

        <!-- Halaman -->
        <div class="space-y-4 lg:col-span-3">
          <h3 class="text-sm font-bold text-white">Halaman</h3>
          <nav class="space-y-0.5" aria-label="Footer">
            <router-link
              v-for="link in navLinks"
              :key="link.path"
              :to="link.path"
              class="flex min-h-[40px] items-center text-[0.9375rem] text-[#B8B8C0] transition-colors duration-150 hover:text-[#F4C542]"
            >
              {{ link.name }}
            </router-link>
          </nav>
        </div>

        <!-- Kontak -->
        <div class="space-y-4 lg:col-span-4">
          <h3 class="text-sm font-bold text-white">Kontak</h3>
          <div class="space-y-4">
            <a href="mailto:kedaimasashimura@gmail.com" class="group flex items-start gap-3">
              <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/[0.07] transition-colors duration-200 group-hover:bg-[#D92B22]/20">
                <Mail :size="16" class="text-[#B8B8C0] transition-colors duration-200 group-hover:text-[#F0524A]" />
              </span>
              <span class="break-all pt-2 text-[0.9375rem] leading-snug text-[#B8B8C0] transition-colors duration-150 group-hover:text-white">
                kedaimasashimura@gmail.com
              </span>
            </a>

            <div class="flex items-start gap-3">
              <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/[0.07]">
                <MapPin :size="16" class="text-[#B8B8C0]" />
              </span>
              <div class="space-y-1 pt-0.5">
                <p class="text-[0.9375rem] font-semibold leading-snug text-white">Jl. Pintu Air No.48</p>
                <p class="text-sm leading-relaxed text-[#B8B8C0]">
                  Harapan Mulya, Medan Satria,<br />Kota Bekasi, Jawa Barat
                </p>
                <a
                  href="https://maps.app.goo.gl/xtLih1iDMfdLnqQC8"
                  target="_blank"
                  rel="noopener"
                  class="inline-flex min-h-[36px] items-center gap-1 text-sm font-semibold text-[#F4C542] underline-offset-4 hover:underline"
                >
                  Buka di Maps <span aria-hidden="true">↗</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom bar -->
      <div class="flex flex-col items-center justify-between gap-3 pt-2 sm:flex-row">
        <p class="text-[0.8125rem] text-[#9A9AA3]">&copy; {{ currentYear }} Masashimura. All rights reserved.</p>
        <div class="flex flex-col items-center gap-1.5 text-center sm:flex-row sm:gap-3 sm:text-right" role="status">
          <span class="flex items-center gap-2">
            <span class="relative flex h-2 w-2 shrink-0">
              <span
                v-if="status.isOpen"
                class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60"
              />
              <span
                class="relative inline-flex h-2 w-2 rounded-full"
                :class="status.isOpen ? 'bg-emerald-400' : 'bg-[#D92B22]'"
              />
            </span>
            <span class="text-[0.8125rem] font-semibold text-white/85">
              {{ status.label }}<template v-if="status.detail"> · {{ status.detail }}</template>
            </span>
          </span>
          <span class="text-[0.8125rem] text-[#9A9AA3]">{{ scheduleText }}</span>
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