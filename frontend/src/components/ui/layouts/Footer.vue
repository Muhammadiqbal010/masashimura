<template>
  <footer class="site-footer relative overflow-hidden bg-[#111113] text-white">
    <div class="stripe-edge" aria-hidden="true"></div>
    <div class="pattern-seigaiha pointer-events-none absolute inset-0 top-3" aria-hidden="true"></div>
    <p class="jp-outline pointer-events-none absolute -bottom-6 right-0 select-none whitespace-nowrap text-[9rem] leading-none sm:text-[13rem]" aria-hidden="true">ありがとう</p>

    <div class="relative mx-auto max-w-7xl px-5 pb-8 pt-14 sm:px-8 lg:px-10 lg:pt-16">
      <div class="grid grid-cols-1 gap-12 pb-12 sm:grid-cols-2 lg:grid-cols-12">

        <!-- Brand -->
        <div class="space-y-5 sm:col-span-2 lg:col-span-5">
          <div class="flex items-center gap-3">
            <img src="@/assets/masashimura-logo.png" alt="Masashimura" loading="lazy" class="pointer-events-none h-10 w-auto select-none" />
            <span class="hanko" aria-hidden="true">ま</span>
          </div>
          <p class="max-w-xs text-[0.9375rem] leading-relaxed text-[#C9C9D0]">
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
              class="social-btn"
            >
              <component :is="s.icon" :size="18" />
            </a>
          </div>
        </div>

        <!-- Halaman -->
        <div class="space-y-4 lg:col-span-3">
          <h3 class="footer-h">Halaman</h3>
          <nav class="space-y-0.5" aria-label="Footer">
            <router-link v-for="link in navLinks" :key="link.path" :to="link.path" class="footer-link">
              <span class="h-2 w-2 rotate-45 bg-[#D92B22]" aria-hidden="true"></span>
              {{ link.name }}
            </router-link>
          </nav>
        </div>

        <!-- Kontak -->
        <div class="space-y-4 lg:col-span-4">
          <h3 class="footer-h">Kontak</h3>
          <div class="space-y-4">
            <a href="mailto:kedaimasashimura@gmail.com" class="group flex items-start gap-3">
              <span class="social-btn !h-10 !w-10 shrink-0"><Mail :size="16" /></span>
              <span class="break-all pt-2 text-[0.9375rem] leading-snug text-[#C9C9D0] transition-colors group-hover:text-white">kedaimasashimura@gmail.com</span>
            </a>
            <div class="flex items-start gap-3">
              <span class="social-btn !h-10 !w-10 shrink-0"><MapPin :size="16" /></span>
              <div class="space-y-1 pt-0.5">
                <p class="text-[0.9375rem] font-bold leading-snug text-white">Jl. Pintu Air No.48</p>
                <p class="text-sm leading-relaxed text-[#C9C9D0]">Harapan Mulya, Medan Satria,<br />Kota Bekasi, Jawa Barat</p>
                <a href="https://maps.app.goo.gl/xtLih1iDMfdLnqQC8" target="_blank" rel="noopener" class="inline-flex min-h-[36px] items-center gap-1 text-sm font-bold text-[#F4C542] underline-offset-4 hover:underline">
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
        <div v-if="status.ready" class="flex flex-col items-center gap-2 text-center sm:flex-row sm:gap-3 sm:text-right" role="status">
          <span class="inline-flex items-center gap-2 rounded-full border-2 border-white/15 bg-[#111113]/80 px-3.5 py-1.5">
            <span class="relative flex h-2 w-2 shrink-0">
              <span v-if="status.isOpen" class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
              <span class="relative inline-flex h-2 w-2 rounded-full" :class="status.isOpen ? 'bg-emerald-400' : 'bg-[#D92B22]'" />
            </span>
            <span class="text-[0.8125rem] font-bold text-white">{{ status.label }}<template v-if="status.detail"> · {{ status.detail }}</template></span>
          </span>
          <span v-if="scheduleText" class="text-[0.8125rem] text-[#9A9AA3]">{{ scheduleText }}</span>
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

<style scoped>
.footer-h { font-size: 0.8125rem; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; color: #F4C542; }
.footer-link { display: flex; align-items: center; gap: 0.75rem; min-height: 40px; font-size: 0.9375rem; font-weight: 700; color: #E6E6EA; transition: color 0.15s, transform 0.15s; }
.footer-link:hover { color: #F4C542; transform: translateX(3px); }
.social-btn { display: inline-flex; align-items: center; justify-content: center; width: 44px; height: 44px; border-radius: 14px; border: 2px solid rgb(255 255 255 / 0.18); background: rgb(255 255 255 / 0.04); color: #E6E6EA; transition: background-color 0.2s, color 0.2s, border-color 0.2s, transform 0.15s; }
a:hover > .social-btn,
a.social-btn:hover { background: #F4C542; border-color: #F4C542; color: #111113; transform: translateY(-2px); }
</style>
