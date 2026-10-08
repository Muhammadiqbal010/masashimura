<template>
  <div class="min-h-screen bg-[#060606] text-white font-inter overflow-x-hidden">

    <!-- ── HEADER ──────────────────────────────────────────────────────────── -->
    <div class="pt-24 sm:pt-28 pb-10 sm:pb-12 px-6 sm:px-10 max-w-7xl mx-auto">
      <div class="space-y-4">
        <div class="flex items-center gap-3">
          <span class="w-6 h-px bg-[#DC2626]"></span>
          <span class="font-mono text-[10px] tracking-[0.3em] text-[#DC2626] uppercase">Hubungi Kami</span>
        </div>
        <h1 class="font-sora text-4xl sm:text-5xl md:text-6xl font-extrabold uppercase tracking-tight leading-[0.95] text-white">
          Lokasi &amp; <span class="text-[#DC2626]">Kontak</span>
        </h1>
        <p class="text-zinc-400 text-sm sm:text-base font-light max-w-md leading-relaxed">
          Kunjungi Masashimura kami di Bekasi atau hubungi lewat kontak resmi di bawah.
        </p>
      </div>
    </div>

    <!-- ── MAP ─────────────────────────────────────────────────────────────── -->
    <div v-reveal class="px-6 sm:px-10 max-w-7xl mx-auto mb-4 sm:mb-5">
      <div
        class="relative w-full overflow-hidden border border-white/[0.08] bg-zinc-900"
        @pointerleave="onMapLeave"
      >
        <!-- Aksen sudut merah -->
        <div class="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-[#DC2626] z-20 pointer-events-none"></div>
        <div class="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-[#DC2626] z-20 pointer-events-none"></div>

        <!-- Map topbar -->
        <div class="absolute top-0 left-0 right-0 z-10 flex items-center justify-between gap-3 px-4 sm:px-5 py-3 bg-gradient-to-b from-black/90 to-transparent pointer-events-none">
          <div class="flex items-center gap-2 min-w-0">
            <MapPin :size="13" class="text-[#DC2626] shrink-0" />
            <span class="font-mono text-[10px] tracking-[0.2em] uppercase text-white/70 truncate">Masashimura · Bekasi</span>
          </div>
          <a
            :href="mapsUrl"
            target="_blank"
            rel="noopener"
            class="pointer-events-auto shrink-0 flex items-center gap-1.5 py-2 pl-2 font-mono text-[10px] tracking-wider uppercase text-zinc-300 hover:text-white transition-colors duration-150"
          >
            Buka Maps
            <ArrowUpRight :size="12" class="text-[#DC2626]" />
          </a>
        </div>

        <!-- iFrame -->
        <div class="w-full h-[280px] sm:h-[360px] md:h-[440px]">
          <iframe
            :src="locationUrl"
            title="Lokasi Masashimura di Google Maps"
            width="100%"
            height="100%"
            style="border:0"
            allowfullscreen=""
            loading="lazy"
            referrerpolicy="no-referrer-when-downgrade"
            class="w-full h-full transition-all duration-500"
            :class="mapActive ? '' : 'grayscale opacity-80'"
          />
        </div>

        <!-- Overlay: cegah peta "menyedot" scroll halaman sampai diketuk -->
        <button
          v-if="!mapActive"
          type="button"
          @click="mapActive = true"
          aria-label="Aktifkan peta supaya bisa digeser dan di-zoom"
          class="absolute inset-0 z-[5] flex items-end justify-center pb-5 cursor-pointer"
        >
          <span class="font-mono text-[10px] tracking-[0.2em] uppercase text-white bg-black/70 backdrop-blur-sm border border-white/15 px-4 py-2.5">
            Ketuk untuk menjelajahi peta
          </span>
        </button>
      </div>
    </div>

    <!-- ── 3 CARDS ─────────────────────────────────────────────────────────── -->
    <div v-reveal class="px-6 sm:px-10 max-w-7xl mx-auto pb-4 sm:pb-5">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-5">

        <!-- Alamat -->
        <div class="bg-[#0d0d0d] border border-white/[0.07] p-6 flex flex-col gap-5 hover:border-[#DC2626]/40 transition-colors duration-300">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 bg-[#DC2626]/10 border border-[#DC2626]/25 flex items-center justify-center flex-shrink-0">
              <MapPin :size="15" class="text-[#DC2626]" />
            </div>
            <span class="font-mono text-[10px] tracking-[0.25em] uppercase text-zinc-500">Alamat</span>
          </div>

          <div class="flex-1 space-y-2">
            <p class="font-sora text-sm font-bold text-white leading-snug">Jl. Pintu Air No.48</p>
            <p class="text-zinc-400 text-xs sm:text-[13px] font-light leading-relaxed">
              Harapan Mulya, Medan Satria,<br />Kota Bekasi, Jawa Barat
            </p>
            <div class="flex items-center gap-2 pt-1">
              <span class="w-1.5 h-1.5 rounded-full bg-[#DC2626] flex-shrink-0"></span>
              <p class="font-mono text-[10px] tracking-wide text-zinc-300">Depan PN Bekasi</p>
            </div>
          </div>

          <div class="flex flex-wrap gap-2 pt-4 border-t border-white/[0.07]">
            <a
              :href="mapsUrl"
              target="_blank"
              rel="noopener"
              class="inline-flex items-center gap-1.5 bg-[#DC2626] hover:bg-red-700 text-white font-sora text-[10px] uppercase tracking-widest font-bold px-3.5 py-2.5 transition-colors"
            >
              Petunjuk Arah
              <ArrowUpRight :size="12" />
            </a>
            <button
              type="button"
              @click="copyAddress"
              class="inline-flex items-center gap-1.5 border border-white/15 hover:border-white/40 hover:bg-white/5 text-zinc-300 hover:text-white font-sora text-[10px] uppercase tracking-widest font-bold px-3.5 py-2.5 transition-all"
            >
              <component :is="copied ? Check : Copy" :size="12" :class="copied ? 'text-emerald-400' : ''" />
              {{ copied ? "Tersalin" : "Salin" }}
            </button>
          </div>
        </div>

        <!-- Jam Buka -->
        <div class="bg-[#0d0d0d] border border-white/[0.07] p-6 flex flex-col gap-5 hover:border-[#DC2626]/40 transition-colors duration-300">
          <div class="flex items-center justify-between gap-3">
            <div class="flex items-center gap-3">
              <div class="w-9 h-9 bg-[#DC2626]/10 border border-[#DC2626]/25 flex items-center justify-center flex-shrink-0">
                <Clock :size="15" class="text-[#DC2626]" />
              </div>
              <span class="font-mono text-[10px] tracking-[0.25em] uppercase text-zinc-500">Jam Buka</span>
            </div>
            <span
              class="inline-flex items-center gap-1.5 px-2.5 py-1 border font-mono text-[10px] tracking-wider uppercase"
              :class="isOpen
                ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
                : 'border-white/10 bg-white/5 text-zinc-400'"
            >
              <span :class="isOpen ? 'bg-emerald-400 animate-pulse' : 'bg-zinc-500'" class="w-1.5 h-1.5 rounded-full flex-shrink-0"></span>
              {{ isOpen ? "Buka" : "Tutup" }}
            </span>
          </div>

          <div class="flex-1 space-y-1">
            <div
              v-for="row in schedule"
              :key="row.label"
              class="flex justify-between items-center gap-3 py-2.5 pl-3 border-l-2 transition-colors"
              :class="isToday(row) ? 'border-[#DC2626] bg-white/[0.02]' : 'border-transparent'"
            >
              <span class="flex items-center gap-2 text-xs sm:text-[13px]" :class="isToday(row) ? 'text-white' : 'text-zinc-400'">
                {{ row.label }}
                <span v-if="isToday(row)" class="font-mono text-[8px] tracking-[0.2em] uppercase text-[#DC2626]">Hari ini</span>
              </span>
              <span class="font-mono text-xs font-bold whitespace-nowrap" :class="row.closed ? 'text-zinc-500' : 'text-white'">
                {{ row.time }}
              </span>
            </div>
          </div>

          <div class="pt-4 border-t border-white/[0.07] space-y-1">
            <p class="font-mono text-[11px]" :class="isOpen ? 'text-emerald-400' : 'text-zinc-300'">{{ statusNote }}</p>
            <p class="font-mono text-[10px] text-zinc-500">Waktu Indonesia Barat (WIB)</p>
          </div>
        </div>

        <!-- Email -->
        <a
          href="mailto:masashimura.id@gmail.com"
          class="group bg-[#0d0d0d] border border-white/[0.07] p-6 flex flex-col gap-5 hover:border-[#DC2626]/40 hover:bg-[#101010] transition-all duration-300"
        >
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 bg-[#DC2626]/10 border border-[#DC2626]/25 flex items-center justify-center flex-shrink-0 group-hover:bg-[#DC2626]/20 transition-colors duration-300">
              <Mail :size="15" class="text-[#DC2626]" />
            </div>
            <span class="font-mono text-[10px] tracking-[0.25em] uppercase text-zinc-500">Email</span>
          </div>
          <div class="flex-1 space-y-2">
            <p class="font-sora text-sm font-bold text-white group-hover:text-[#DC2626] transition-colors duration-200">Kirim Pesan</p>
            <p class="font-mono text-xs text-zinc-400 break-all">masashimura.id@gmail.com</p>
          </div>
          <div class="flex items-center gap-2 pt-4 border-t border-white/[0.07] font-mono text-[10px] tracking-wider uppercase text-zinc-400 group-hover:text-white transition-colors duration-200">
            Kirim Email
            <span class="w-4 h-px bg-zinc-600 group-hover:w-8 group-hover:bg-[#DC2626] transition-all duration-300"></span>
          </div>
        </a>

      </div>
    </div>

    <!-- ── CTA BANNER ──────────────────────────────────────────────────────── -->
    <div v-reveal class="px-6 sm:px-10 max-w-7xl mx-auto pb-20 sm:pb-24">
      <div class="relative overflow-hidden bg-[#0d0d0d] border border-white/[0.07] p-7 sm:p-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-8">
        <div class="cta-glow absolute inset-0 pointer-events-none"></div>

        <div class="relative space-y-3">
          <div class="flex items-center gap-3">
            <span class="w-6 h-px bg-[#DC2626]"></span>
            <span class="font-mono text-[10px] tracking-[0.3em] uppercase text-[#DC2626]">Order Online</span>
          </div>
          <h2 class="font-sora text-2xl sm:text-3xl font-extrabold uppercase tracking-tight text-white leading-tight">
            Mau Order<br class="sm:hidden" /> dari Rumah?
          </h2>
          <p class="text-zinc-400 text-xs sm:text-sm font-light max-w-xs leading-relaxed">
            Pilih menu favorit dan pesan langsung tanpa harus keluar.
          </p>
        </div>

        <router-link
          to="/menu"
          class="relative group w-full sm:w-auto inline-flex items-center justify-center gap-3 bg-[#DC2626] hover:bg-red-700 active:scale-[0.98] text-white font-sora text-[11px] uppercase tracking-[0.2em] px-10 py-4 font-bold transition-all duration-200 whitespace-nowrap hover:-translate-y-0.5"
        >
          Lihat Menu
          <ArrowRight :size="14" class="transition-transform duration-200 group-hover:translate-x-1" />
        </router-link>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue"
import { MapPin, Clock, Mail, ArrowRight, ArrowUpRight, Copy, Check } from "lucide-vue-next"
import { toast } from "vue-sonner"

const locationUrl = ref(
  "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3966.2474247843616!2d106.9974506!3d-6.231077499999999!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x2e698d4a2a564acb%3A0x5647f35252d3d568!2sMasashimura!5e0!3m2!1sid!2sid!4v1781883172371!5m2!1sid!2sid"
)
const mapsUrl = "https://maps.app.goo.gl/xtLih1iDMfdLnqQC8"

// ── Scroll reveal directive (sama kayak homepage) ─────────────────────────
const vReveal = {
  mounted(el) {
    el.classList.add("reveal")
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          el.classList.add("reveal-visible")
          observer.unobserve(el)
        }
      })
    }, { threshold: 0.1 })
    observer.observe(el)
  }
}

// ── Peta: aktif setelah diketuk, balik terkunci pas mouse keluar ──────────
const mapActive = ref(false)
const onMapLeave = (e) => {
  if (e.pointerType === "mouse") mapActive.value = false
}

// ── Jam buka ──────────────────────────────────────────────────────────────
// Selalu dihitung pakai WIB, jadi status "Buka/Tutup" tetap benar
// walau pengunjung membuka dari zona waktu lain.
const OPEN_MIN  = 11 * 60        // 11.00
const CLOSE_MIN = 22 * 60 + 30   // 22.30

const schedule = [
  { label: "Senin – Sabtu", time: "11.00 – 22.30", closed: false, days: [1, 2, 3, 4, 5, 6] },
  { label: "Minggu",        time: "Tutup",         closed: true,  days: [0] },
]

const getWIB = () => {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Jakarta",
    weekday: "short",
    hour: "numeric",
    minute: "numeric",
    hour12: false,
  }).formatToParts(new Date())
  const get = (t) => parts.find(p => p.type === t)?.value
  const dayMap = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 }
  let hour = parseInt(get("hour"), 10)
  if (hour === 24) hour = 0
  return { day: dayMap[get("weekday")] ?? 0, minutes: hour * 60 + parseInt(get("minute"), 10) }
}

const now = ref(getWIB())
let clockTimer = null
onMounted(() => {
  now.value = getWIB()
  clockTimer = setInterval(() => { now.value = getWIB() }, 60000) // update tiap menit
})
onUnmounted(() => {
  clearInterval(clockTimer)
  clearTimeout(copyTimer)
})

const isOpen = computed(() => {
  const { day, minutes } = now.value
  if (day === 0) return false // Tutup Minggu
  return minutes >= OPEN_MIN && minutes < CLOSE_MIN
})

const isToday = (row) => row.days.includes(now.value.day)

const statusNote = computed(() => {
  const { day, minutes } = now.value
  if (isOpen.value) return "Buka sampai pukul 22.30"
  if (day === 0) return "Buka lagi Senin pukul 11.00"
  if (minutes < OPEN_MIN) return "Buka hari ini pukul 11.00"
  return day === 6 ? "Buka lagi Senin pukul 11.00" : "Buka lagi besok pukul 11.00"
})

// ── Salin alamat ──────────────────────────────────────────────────────────
const copied = ref(false)
let copyTimer = null
const copyAddress = async () => {
  const text = "Jl. Pintu Air No.48, Harapan Mulya, Medan Satria, Kota Bekasi, Jawa Barat"
  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    toast.success("Alamat disalin")
    clearTimeout(copyTimer)
    copyTimer = setTimeout(() => { copied.value = false }, 2000)
  } catch {
    toast.error("Gagal menyalin alamat")
  }
}
</script>

<style scoped>
a:focus-visible,
button:focus-visible {
  outline: 2px solid #DC2626;
  outline-offset: 3px;
}

.cta-glow {
  background: radial-gradient(50% 80% at 100% 100%, rgba(220, 38, 38, 0.14), transparent 70%);
}

.reveal {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 0.7s cubic-bezier(0.16, 1, 0.3, 1), transform 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}
.reveal-visible {
  opacity: 1;
  transform: none;
}

@media (prefers-reduced-motion: reduce) {
  .reveal {
    transition: none;
    opacity: 1;
    transform: none;
  }
}
</style>