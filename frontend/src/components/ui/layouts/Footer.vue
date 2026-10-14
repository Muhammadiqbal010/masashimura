<template>
  <footer class="relative overflow-hidden bg-[#050505] font-inter text-white">
    <!-- Garis aksen brand -->
    <div class="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-[#EE0000] via-[#EE0000] to-[#FFF500]" />
    <div class="pointer-events-none absolute -bottom-40 -left-32 h-80 w-80 rounded-full bg-[#EE0000]/10 blur-3xl" />

    <div class="relative mx-auto max-w-7xl px-6 pb-8 pt-16 md:px-12">
      <div class="grid grid-cols-2 gap-x-8 gap-y-12 border-b border-white/10 pb-12 md:grid-cols-12">

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
              class="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/[0.05] text-white/70 transition-all duration-200 hover:border-[#FFF500] hover:bg-[#FFF500] hover:text-black"
            >
              <component :is="s.icon" :size="17" />
            </a>
          </div>
        </div>

        <!-- Halaman -->
        <div class="col-span-2 space-y-4 md:col-span-3">
          <h3 class="font-sora text-sm font-bold text-[#FFF500]">Halaman</h3>
          <nav class="space-y-1" aria-label="Footer">
            <router-link
              v-for="link in navLinks"
              :key="link.path"
              :to="link.path"
              class="group flex items-center gap-2.5 py-1.5 text-sm text-white/70 transition-colors duration-150 hover:text-white"
            >
              <span class="h-0.5 w-3 shrink-0 rounded bg-white/25 transition-all duration-200 group-hover:w-5 group-hover:bg-[#EE0000]" />
              {{ link.name }}
            </router-link>
          </nav>
        </div>

        <!-- Kontak -->
        <div class="col-span-2 space-y-4 md:col-span-4">
          <h3 class="font-sora text-sm font-bold text-[#FFF500]">Kontak</h3>
          <div class="space-y-4">
            <a href="mailto:kedaimasashimura@gmail.com" class="group flex items-start gap-3">
              <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/[0.05] transition-all duration-200 group-hover:border-[#EE0000]/60 group-hover:bg-[#EE0000]/10">
                <Mail :size="15" class="text-white/70 transition-colors duration-200 group-hover:text-[#FF2A2A]" />
              </div>
              <span class="break-all pt-1.5 text-sm leading-snug text-white/70 transition-colors duration-150 group-hover:text-white">
                kedaimasashimura@gmail.com
              </span>
            </a>

            <div class="flex items-start gap-3">
              <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/[0.05]">
                <MapPin :size="15" class="text-white/70" />
              </div>
              <div class="space-y-1 pt-0.5">
                <p class="text-sm font-semibold leading-snug text-white">Jl. Pintu Air No.48</p>
                <p class="text-sm leading-relaxed text-white/60">
                  Harapan Mulya, Medan Satria,<br />Kota Bekasi, Jawa Barat
                </p>
                <a
                  href="https://maps.app.goo.gl/xtLih1iDMfdLnqQC8"
                  target="_blank"
                  rel="noopener"
                  class="inline-flex items-center gap-1 pt-1 text-sm font-semibold text-[#FFF500] underline-offset-4 transition-colors hover:underline"
                >
                  Buka di Maps <span aria-hidden="true">↗</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom bar -->
      <div class="flex flex-col items-center justify-between gap-3 pt-6 sm:flex-row">
        <p class="text-xs text-white/50">&copy; {{ currentYear }} Masashimura. All rights reserved.</p>
        <div class="flex flex-col items-center gap-1.5 text-center sm:flex-row sm:gap-3 sm:text-right" role="status">
          <span class="flex items-center gap-2">
            <span class="relative flex h-2 w-2 shrink-0">
              <span
                v-if="status.isOpen"
                class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60"
              />
              <span
                class="relative inline-flex h-2 w-2 rounded-full"
                :class="status.isOpen ? 'bg-emerald-400' : 'bg-[#EE0000]'"
              />
            </span>
            <span class="text-xs font-semibold text-white/80">
              {{ status.label }}<template v-if="status.detail"> · {{ status.detail }}</template>
            </span>
          </span>
          <span class="hidden h-3 w-px bg-white/15 sm:block" />
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