<template>
  <footer class="relative bg-[#060606] text-white font-inter overflow-hidden">

    <!-- Top divider -->
    <div class="absolute inset-x-0 top-0 h-px bg-white/[0.06]" />

    <!-- ── MAIN FOOTER ── -->
    <div class="relative max-w-7xl mx-auto px-6 md:px-12 pt-14 pb-8">
      <div class="grid grid-cols-2 md:grid-cols-12 gap-x-8 gap-y-12 pb-10 border-b border-white/[0.05]">

        <!-- Brand (full width on mobile, 5 cols on desktop) -->
        <div class="col-span-2 md:col-span-5 space-y-5">
          <img
            src="@/assets/masashimura-logo.png"
            alt="Masashimura"
            loading="lazy"
            class="h-10 md:h-12 w-auto select-none pointer-events-none"
          />
          <p class="text-zinc-500 text-[13px] leading-relaxed max-w-[260px]">
            Kedai Jepang kekinian di jantung Bekasi. Cozy, kustom, harga bersahabat.
          </p>
          <!-- Social row -->
          <div class="flex items-center gap-2.5">
            <a
              v-for="s in socials"
              :key="s.href"
              :href="s.href"
              :aria-label="s.label"
              target="_blank"
              rel="noopener noreferrer"
              class="w-9 h-9 rounded-xl bg-white/[0.05] border border-white/[0.08] flex items-center justify-center text-zinc-500 hover:text-white hover:border-white/20 hover:bg-white/10 transition-all duration-200"
            >
              <component :is="s.icon" :size="15" />
            </a>
          </div>
        </div>

        <!-- Halaman (1 col on mobile, 3 cols on desktop) -->
        <div class="col-span-1 md:col-span-3 space-y-5">
          <p class="font-mono text-[9px] tracking-[0.3em] uppercase text-zinc-700">Halaman</p>
          <nav class="space-y-0.5">
            <router-link
              v-for="link in navLinks"
              :key="link.path"
              :to="link.path"
              class="group flex items-center gap-2.5 py-2 text-[13px] text-zinc-500 hover:text-white transition-colors duration-150"
            >
              <span class="w-2.5 h-px bg-zinc-800 group-hover:w-4 group-hover:bg-[#DC2626] transition-all duration-200 shrink-0" />
              {{ link.name }}
            </router-link>
          </nav>
        </div>

        <!-- Kontak (1 col on mobile, 4 cols on desktop) -->
        <div class="col-span-1 md:col-span-4 space-y-5">
          <p class="font-mono text-[9px] tracking-[0.3em] uppercase text-zinc-700">Kontak</p>
          <div class="space-y-4">

            <a href="mailto:masashimura.id@gmail.com" class="group flex items-start gap-3">
              <div class="w-8 h-8 rounded-xl bg-white/[0.04] border border-white/[0.07] flex items-center justify-center shrink-0 group-hover:border-[#DC2626]/40 group-hover:bg-[#DC2626]/5 transition-all duration-200">
                <Mail :size="13" class="text-zinc-600 group-hover:text-[#DC2626] transition-colors duration-200" />
              </div>
              <div class="pt-1">
                <p class="font-mono text-[11px] text-zinc-500 group-hover:text-white transition-colors duration-150 break-all leading-snug">
                  masashimura.id@gmail.com
                </p>
              </div>
            </a>

            <div class="flex items-start gap-3">
              <div class="w-8 h-8 rounded-xl bg-white/[0.04] border border-white/[0.07] flex items-center justify-center shrink-0">
                <MapPin :size="13" class="text-zinc-600" />
              </div>
              <div class="pt-1 space-y-1">
                <p class="text-[12px] font-semibold text-white leading-snug">Jl. Pintu Air No.48</p>
                <p class="text-zinc-600 text-[11px] leading-relaxed">
                  Harapan Mulya, Medan Satria,<br />Kota Bekasi, Jawa Barat
                </p>
                <a
                  href="https://maps.app.goo.gl/xtLih1iDMfdLnqQC8"
                  target="_blank"
                  rel="noopener"
                  class="inline-flex items-center gap-1 pt-0.5 font-mono text-[9px] tracking-[0.15em] uppercase text-zinc-700 hover:text-[#DC2626] transition-colors duration-150"
                >
                  Buka Maps <span class="text-[#DC2626]">↗</span>
                </a>
              </div>
            </div>

          </div>
        </div>
      </div>

      <!-- Bottom bar -->
      <div class="pt-6 flex flex-col sm:flex-row items-center justify-between gap-3">
        <p class="font-mono text-[10px] text-zinc-700 tracking-wider">
          &copy; {{ currentYear }} Masashimura. All rights reserved.
        </p>
        <div class="flex items-center gap-2">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shrink-0" />
          <span class="font-mono text-[9px] tracking-[0.18em] uppercase text-zinc-700">
            Buka Senin – Sabtu &nbsp;·&nbsp; 11.00 – 22.30 WIB
          </span>
        </div>
      </div>
    </div>

  </footer>
</template>

<script setup>
import { computed } from "vue"
import { Instagram, Music4, MessageCircle, Mail, MapPin } from "lucide-vue-next"

const currentYear = computed(() => new Date().getFullYear())

const navLinks = [
  { name: "Home",   path: "/" },
  { name: "Menu",   path: "/menu" },
  { name: "Kontak", path: "/contact" },
]

const socials = [
  { href: "https://www.instagram.com/masashimura.id?igsh=aWdwemFoZHJyMGd4",  label: "Instagram Masashimura", icon: Instagram     },
  { href: "https://www.tiktok.com/@masashimura.id?_r=1&_d=f38e5ga547698m&sec_uid=MS4wLjABAAAA1-eEz10qZSYQro3iEvI4zRAS99Wvns1CtDuIpVSmB6UTgQfKNvet5Qpygdlq8lAC&share_author_id=7127158177099383835&sharer_language=id&source=h5_t&u_code=e2i24ec15jml4d&timestamp=1782825174&user_id=7117580086647620609&sec_user_id=MS4wLjABAAAAXgDON-GVMjr2LsCnwBStw6PMVAVGV3oTYoKExKyw6jUofn8z29xgPjMcyoi2ODSu&item_author_type=2&utm_source=whatsapp&utm_campaign=client_share&utm_medium=android&share_iid=7654320356233185045&share_link_id=0ce00482-3200-4348-97bc-357ec1b8b47e&share_app_id=1180&ugbiz_name=ACCOUNT&ug_btm=b6880%2Cb5836&social_share_type=5&share_enter_from=others_homepage&item_author_type=2&enable_checksum=1",    label: "TikTok Masashimura",    icon: Music4        },
]
</script>