<template>
  <div class="min-h-screen bg-[#060606] text-white font-inter">

    <!-- Header -->
    <div class="pt-28 pb-14 px-5 sm:px-10 max-w-6xl mx-auto">
      <div class="flex items-center gap-3 mb-5">
        <span class="w-6 h-px bg-[#DC2626]"></span>
        <span class="font-mono text-[9px] tracking-[0.35em] text-[#DC2626] uppercase">Hubungi Kami</span>
      </div>
      <h1 class="font-sora text-4xl sm:text-5xl md:text-6xl font-extrabold uppercase tracking-tight leading-[0.92] text-white mb-5">
        Lokasi &amp; Kontak
      </h1>
      <p class="text-zinc-600 text-[13px] font-light max-w-xs leading-relaxed">
        Kunjungi Masashimura kami di Bekasi atau hubungi lewat kontak resmi di bawah.
      </p>
    </div>

    <!-- Map -->
    <div class="px-5 sm:px-10 max-w-6xl mx-auto mb-5">
      <div class="w-full rounded-2xl overflow-hidden border border-white/[0.06] relative">

        <!-- Map Topbar -->
        <div class="absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-5 py-3.5 bg-gradient-to-b from-black/90 to-transparent">
          <div class="flex items-center gap-2">
            <MapPin :size="12" class="text-[#DC2626]" />
            <span class="font-mono text-[9px] tracking-[0.2em] uppercase text-white/60">Masashimura · Bekasi</span>
          </div>
          <a
            href="https://maps.app.goo.gl/xtLih1iDMfdLnqQC8"
            target="_blank"
            rel="noopener"
            class="flex items-center gap-1.5 font-mono text-[9px] tracking-wider uppercase text-zinc-500 hover:text-white transition-colors duration-150"
          >
            Buka Maps
            <span class="text-[#DC2626]">↗</span>
          </a>
        </div>

        <!-- iFrame -->
        <div class="w-full h-[240px] sm:h-[340px] md:h-[400px] bg-zinc-900">
          <iframe
            :src="locationUrl"
            width="100%"
            height="100%"
            style="border:0"
            allowfullscreen=""
            loading="lazy"
            referrerpolicy="no-referrer-when-downgrade"
            class="w-full h-full grayscale opacity-70 hover:grayscale-0 hover:opacity-100 transition-all duration-500"
          />
        </div>

      </div>
    </div>

    <!-- 3 Cards -->
    <div class="px-5 sm:px-10 max-w-6xl mx-auto pb-8">
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">

        <!-- Alamat -->
        <div class="bg-[#0d0d0d] border border-white/[0.06] rounded-2xl p-6 flex flex-col gap-5 hover:border-white/[0.12] transition-all duration-300">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-xl bg-[#DC2626]/10 border border-[#DC2626]/15 flex items-center justify-center flex-shrink-0">
              <MapPin :size="14" class="text-[#DC2626]" />
            </div>
            <span class="font-mono text-[9px] tracking-[0.25em] uppercase text-zinc-700">Alamat</span>
          </div>
          <div class="flex-1 space-y-1.5">
            <p class="font-sora text-[13px] font-bold text-white leading-snug">Jl. Pintu Air No.48</p>
            <p class="text-zinc-500 text-[11px] font-light leading-relaxed">
              Harapan Mulya, Medan Satria,<br />Kota Bekasi, Jawa Barat
            </p>
          </div>
          <div class="flex items-center gap-2 pt-4 border-t border-white/[0.05]">
            <span class="w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0"></span>
            <p class="font-mono text-[10px] text-amber-400">Depan PN Bekasi</p>
          </div>
        </div>

        <!-- Jam Buka -->
        <div class="bg-[#0d0d0d] border border-white/[0.06] rounded-2xl p-6 flex flex-col gap-5 hover:border-white/[0.12] transition-all duration-300">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/15 flex items-center justify-center flex-shrink-0">
                <Clock :size="14" class="text-emerald-400" />
              </div>
              <span class="font-mono text-[9px] tracking-[0.25em] uppercase text-zinc-700">Jam Buka</span>
            </div>
            <div class="flex items-center gap-1.5">
              <span :class="isOpen ? 'bg-emerald-400' : 'bg-zinc-700'" class="w-1.5 h-1.5 rounded-full flex-shrink-0"></span>
              <span :class="isOpen ? 'text-emerald-400' : 'text-zinc-600'" class="font-mono text-[9px] tracking-wider">
                {{ isOpen ? 'Buka' : 'Tutup' }}
              </span>
            </div>
          </div>
          <div class="flex-1 space-y-3">
            <div class="flex justify-between items-center">
              <span class="text-[11px] text-zinc-500">Senin – Sabtu</span>
              <span class="font-mono text-[11px] font-bold text-white">11.00 – 22.30</span>
            </div>
            <div class="h-px bg-white/[0.05]"></div>
            <div class="flex justify-between items-center">
              <span class="text-[11px] text-zinc-500">Minggu</span>
              <span class="font-mono text-[11px] text-zinc-700">Tutup</span>
            </div>
          </div>
          <div class="pt-4 border-t border-white/[0.05]">
            <p class="font-mono text-[10px] text-zinc-700">Waktu Indonesia Barat (WIB)</p>
          </div>
        </div>

        <!-- Email -->
        <a
          href="mailto:masashimura.id@gmail.com"
          class="bg-[#0d0d0d] border border-white/[0.06] rounded-2xl p-6 flex flex-col gap-5 hover:border-amber-500/20 hover:bg-amber-500/[0.02] transition-all duration-300 group"
        >
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-xl bg-amber-500/10 border border-amber-500/15 flex items-center justify-center flex-shrink-0 group-hover:bg-amber-500/20 transition-colors duration-300">
              <Mail :size="14" class="text-amber-400" />
            </div>
            <span class="font-mono text-[9px] tracking-[0.25em] uppercase text-zinc-700">Email</span>
          </div>
          <div class="flex-1 space-y-1.5">
            <p class="font-sora text-[13px] font-bold text-white group-hover:text-amber-400 transition-colors duration-200">Kirim Pesan</p>
            <p class="font-mono text-[11px] text-zinc-500 break-all">masashimura.id@gmail.com</p>
          </div>
          <div class="flex items-center gap-2 pt-4 border-t border-white/[0.05] font-mono text-[10px] tracking-wider uppercase text-zinc-700 group-hover:text-amber-400 transition-colors duration-200">
            Kirim Email
            <span class="w-4 h-px bg-zinc-800 group-hover:bg-amber-400 transition-colors duration-200"></span>
          </div>
        </a>

      </div>
    </div>

    <!-- CTA Banner -->
    <div class="px-5 sm:px-10 max-w-6xl mx-auto pb-24">
      <div class="bg-[#0d0d0d] border border-white/[0.06] rounded-2xl p-7 sm:p-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-8">
        <div class="space-y-2">
          <div class="flex items-center gap-2">
            <span class="w-4 h-px bg-[#DC2626]"></span>
            <span class="font-mono text-[9px] tracking-[0.35em] uppercase text-[#DC2626]">Order Online</span>
          </div>
          <h2 class="font-sora text-2xl sm:text-3xl font-extrabold uppercase tracking-tight text-white leading-tight">
            Mau Order<br class="sm:hidden" /> dari Rumah?
          </h2>
          <p class="text-zinc-600 text-[11px] font-light max-w-xs leading-relaxed">
            Pilih menu favorit dan pesan langsung tanpa harus keluar.
          </p>
        </div>
        <div class="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
          <router-link
            to="/menu"
            class="bg-[#DC2626] hover:bg-red-700 active:scale-[0.98] text-white font-sora text-[10px] uppercase tracking-widest px-8 py-4 font-bold transition-all duration-200 text-center rounded-xl whitespace-nowrap"
          >
            Lihat Menu
          </router-link>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from "vue"
import { MapPin, Clock, Mail } from "lucide-vue-next"

const locationUrl = ref(
  "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3966.2474247843616!2d106.9974506!3d-6.231077499999999!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x2e698d4a2a564acb%3A0x5647f35252d3d568!2sMasashimura!5e0!3m2!1sid!2sid!4v1781883172371!5m2!1sid!2sid"
)

const isOpen = computed(() => {
  const now  = new Date()
  const day  = now.getDay()          // 0 = Minggu, 1–6 = Senin–Sabtu
  const time = now.getHours() * 60 + now.getMinutes()
  if (day === 0) return false        // Tutup Minggu
  return time >= 660 && time < 1350  // 11:00 (660 mnt) – 22:30 (1350 mnt)
})
</script>