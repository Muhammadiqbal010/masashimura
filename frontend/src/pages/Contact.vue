<template>
  <div class="page relative min-h-screen overflow-x-hidden bg-[#0B0A0A] font-inter text-[#F5F0EA]">
    <!-- Atmosfer latar: glow halus, tidak mengganggu konten -->
    <div class="page-glow pointer-events-none absolute inset-x-0 top-0 h-[520px]" aria-hidden="true"></div>

    <div class="relative mx-auto max-w-7xl px-5 sm:px-8 lg:px-10">

      <!-- ── HEADER ──────────────────────────────────────────────────────── -->
      <header class="pt-28 pb-10 sm:pt-32 sm:pb-12">
        <div
          class="mb-6 inline-flex items-center gap-2 rounded-full border px-3.5 py-1.5 text-xs font-medium backdrop-blur"
          :class="isOpen
            ? 'border-emerald-400/25 bg-emerald-400/10 text-emerald-300'
            : 'border-white/10 bg-white/[0.04] text-[#A39A93]'"
        >
          <span
            class="h-1.5 w-1.5 rounded-full"
            :class="isOpen ? 'animate-pulse bg-emerald-400' : 'bg-[#6F6761]'"
          ></span>
          {{ isOpen ? "Buka sekarang" : "Sedang tutup" }}
        </div>

        <h1 class="font-sora text-4xl font-semibold leading-[1.05] tracking-tight text-[#F5F0EA] sm:text-5xl lg:text-6xl">
          Lokasi dan kontak
        </h1>
        <p class="mt-4 max-w-md text-base leading-relaxed text-[#A39A93] sm:text-lg">
          Kunjungi Masashimura di Bekasi, atau hubungi kami lewat kontak resmi di bawah.
        </p>
      </header>

      <!-- ── MAP + ALAMAT + JAM BUKA ─────────────────────────────────────── -->
      <section v-reveal class="grid gap-4 lg:grid-cols-5 lg:gap-5">

        <!-- Map -->
        <div
          class="relative h-[340px] overflow-hidden rounded-3xl border border-white/[0.08] bg-[#141211] sm:h-[440px] lg:col-span-3 lg:h-auto lg:min-h-[600px]"
          @pointerleave="onMapLeave"
        >
          <div class="absolute inset-0">
            <iframe
              :src="locationUrl"
              title="Lokasi Masashimura di Google Maps"
              width="100%"
              height="100%"
              style="border:0"
              allowfullscreen=""
              loading="lazy"
              referrerpolicy="no-referrer-when-downgrade"
              class="h-full w-full transition-all duration-500"
              :class="mapActive ? '' : 'grayscale opacity-75 brightness-90'"
            />
          </div>

          <!-- Topbar mengambang -->
          <div class="pointer-events-none absolute inset-x-0 top-0 z-10 flex items-start justify-between gap-3 p-3 sm:p-4">
            <div class="flex min-w-0 items-center gap-2 rounded-full border border-white/10 bg-black/60 py-2 pl-3 pr-4 backdrop-blur-md">
              <MapPin :size="14" class="shrink-0 text-[#E5484D]" />
              <span class="truncate text-xs font-medium text-[#F5F0EA] sm:text-[13px]">Masashimura, Bekasi</span>
            </div>
            <a
              :href="mapsUrl"
              target="_blank"
              rel="noopener"
              class="pointer-events-auto flex shrink-0 items-center gap-1.5 rounded-full border border-white/10 bg-black/60 px-4 py-2 text-xs font-medium text-[#F5F0EA] backdrop-blur-md transition-colors duration-150 hover:bg-white hover:text-[#0B0A0A] sm:text-[13px]"
            >
              Buka di Maps
              <ArrowUpRight :size="13" />
            </a>
          </div>

          <!-- Overlay: cegah peta "menyedot" scroll halaman sampai diketuk -->
          <button
            v-if="!mapActive"
            type="button"
            @click="mapActive = true"
            aria-label="Aktifkan peta supaya bisa digeser dan di-zoom"
            class="absolute inset-0 z-[5] flex cursor-pointer items-end justify-center pb-5 sm:pb-6"
          >
            <span class="rounded-full border border-white/15 bg-black/70 px-5 py-2.5 text-xs font-medium text-[#F5F0EA] backdrop-blur-md sm:text-[13px]">
              Ketuk untuk menjelajahi peta
            </span>
          </button>
        </div>

        <!-- Kolom kanan -->
        <div class="flex flex-col gap-4 lg:col-span-2 lg:gap-5">

          <!-- Alamat -->
          <article class="card flex flex-col gap-6">
            <div class="flex items-center gap-3">
              <div class="icon-tile"><MapPin :size="17" /></div>
              <h2 class="font-sora text-base font-semibold text-[#F5F0EA]">Alamat</h2>
            </div>

            <div class="space-y-1.5">
              <p class="font-sora text-xl font-semibold leading-snug text-[#F5F0EA]">Jl. Pintu Air No.48</p>
              <p class="text-sm leading-relaxed text-[#A39A93]">
                Harapan Mulya, Medan Satria,<br />Kota Bekasi, Jawa Barat
              </p>
              <p class="inline-flex items-center gap-2 pt-3 text-[13px] font-medium text-[#D4B483]">
                <span class="h-1.5 w-1.5 rounded-full bg-[#D4B483]"></span>
                Depan PN Bekasi
              </p>
            </div>

            <div class="flex flex-wrap gap-2.5">
              <a
                :href="mapsUrl"
                target="_blank"
                rel="noopener"
                class="btn-primary"
              >
                Petunjuk arah
                <ArrowUpRight :size="15" />
              </a>
              <button type="button" @click="copyAddress" class="btn-ghost">
                <component :is="copied ? Check : Copy" :size="15" :class="copied ? 'text-emerald-400' : ''" />
                {{ copied ? "Tersalin" : "Salin alamat" }}
              </button>
            </div>
          </article>

          <!-- Jam buka -->
          <article class="card flex flex-1 flex-col gap-5">
            <div class="flex items-center justify-between gap-3">
              <div class="flex items-center gap-3">
                <div class="icon-tile"><Clock :size="17" /></div>
                <h2 class="font-sora text-base font-semibold text-[#F5F0EA]">Jam buka</h2>
              </div>
              <span
                class="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium"
                :class="isOpen
                  ? 'border-emerald-400/25 bg-emerald-400/10 text-emerald-300'
                  : 'border-white/10 bg-white/[0.05] text-[#A39A93]'"
              >
                <span
                  :class="isOpen ? 'animate-pulse bg-emerald-400' : 'bg-[#6F6761]'"
                  class="h-1.5 w-1.5 shrink-0 rounded-full"
                ></span>
                {{ isOpen ? "Buka" : "Tutup" }}
              </span>
            </div>

            <div class="space-y-2">
              <div
                v-for="row in schedule"
                :key="row.label"
                class="flex items-center justify-between gap-3 rounded-xl border px-4 py-3.5 transition-colors"
                :class="isToday(row)
                  ? 'border-[#D7263D]/30 bg-[#D7263D]/[0.08]'
                  : 'border-transparent bg-white/[0.025]'"
              >
                <span class="flex items-center gap-2.5 text-sm" :class="isToday(row) ? 'font-medium text-[#F5F0EA]' : 'text-[#A39A93]'">
                  {{ row.label }}
                  <span
                    v-if="isToday(row)"
                    class="rounded-full bg-[#D7263D] px-2 py-0.5 text-[10px] font-semibold text-white"
                  >Hari ini</span>
                </span>
                <span
                  class="whitespace-nowrap text-sm font-semibold tabular-nums"
                  :class="row.closed ? 'text-[#6F6761]' : 'text-[#F5F0EA]'"
                >
                  {{ row.time }}
                </span>
              </div>
            </div>

            <div class="mt-auto space-y-0.5 border-t border-white/[0.07] pt-4">
              <p class="text-sm font-medium" :class="isOpen ? 'text-emerald-300' : 'text-[#F5F0EA]'">{{ statusNote }}</p>
              <p class="text-xs text-[#6F6761]">Waktu Indonesia Barat (WIB)</p>
            </div>
          </article>
        </div>
      </section>

      <!-- ── EMAIL + CTA ─────────────────────────────────────────────────── -->
      <section v-reveal class="mt-4 grid gap-4 pb-20 sm:pb-28 lg:mt-5 lg:grid-cols-5 lg:gap-5">

        <!-- Email -->
        <a
          href="mailto:masashimura.id@gmail.com"
          class="card group flex flex-col gap-6 transition-colors duration-300 hover:border-[#D4B483]/40 lg:col-span-2"
        >
          <div class="flex items-center justify-between gap-3">
            <div class="flex items-center gap-3">
              <div class="icon-tile transition-colors duration-300 group-hover:bg-[#D4B483]/20"><Mail :size="17" /></div>
              <h2 class="font-sora text-base font-semibold text-[#F5F0EA]">Email</h2>
            </div>
            <span class="flex h-9 w-9 items-center justify-center rounded-full border border-white/10 text-[#A39A93] transition-all duration-300 group-hover:border-[#D4B483] group-hover:bg-[#D4B483] group-hover:text-[#0B0A0A]">
              <ArrowUpRight :size="16" />
            </span>
          </div>
          <div class="space-y-1.5">
            <p class="font-sora text-xl font-semibold text-[#F5F0EA]">Kirim pesan</p>
            <p class="break-all text-sm text-[#A39A93]">masashimura.id@gmail.com</p>
          </div>
        </a>

        <!-- CTA: satu-satunya blok berwarna penuh di halaman -->
        <div class="cta relative flex flex-col justify-between gap-8 overflow-hidden rounded-3xl p-7 sm:flex-row sm:items-center sm:p-10 lg:col-span-3">
          <div class="cta-sheen pointer-events-none absolute inset-0" aria-hidden="true"></div>

          <div class="relative max-w-sm space-y-3">
            <h2 class="font-sora text-2xl font-semibold leading-tight tracking-tight text-white sm:text-3xl">
              Mau order dari rumah?
            </h2>
            <p class="text-sm leading-relaxed text-white/75 sm:text-base">
              Pilih menu favorit dan pesan langsung, tanpa harus keluar.
            </p>
          </div>

          <router-link
            to="/menu"
            class="group relative inline-flex w-full items-center justify-center gap-2.5 whitespace-nowrap rounded-full bg-[#F5F0EA] px-8 py-4 font-sora text-sm font-semibold text-[#2A0A0F] transition-all duration-200 hover:bg-white active:scale-[0.98] sm:w-auto"
          >
            Lihat menu
            <ArrowRight :size="16" class="transition-transform duration-200 group-hover:translate-x-1" />
          </router-link>
        </div>
      </section>

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
let copyTimer = null
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
/*
  Palet
  - Warm black  #0B0A0A  → latar
  - Surface     #141211  → kartu
  - Washi       #F5F0EA  → teks utama (putih hangat, bukan putih murni)
  - Crimson     #D7263D  → aksi & penanda "hari ini"
  - Champagne   #D4B483  → detail premium (ikon, landmark, hover)
*/

.page-glow {
  background:
    radial-gradient(60% 70% at 15% 0%, rgba(215, 38, 61, 0.16), transparent 70%),
    radial-gradient(40% 50% at 90% 10%, rgba(212, 180, 131, 0.07), transparent 70%);
}

.card {
  border-radius: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.07);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.045), rgba(255, 255, 255, 0.012)), #141211;
  padding: 1.5rem;
}
@media (min-width: 640px) {
  .card { padding: 1.75rem; }
}

.icon-tile {
  display: flex;
  height: 2.5rem;
  width: 2.5rem;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 0.75rem;
  border: 1px solid rgba(212, 180, 131, 0.22);
  background: rgba(212, 180, 131, 0.1);
  color: #D4B483;
}

.btn-primary,
.btn-ghost {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  border-radius: 9999px;
  padding: 0.75rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  transition: all 0.2s ease;
}
.btn-primary {
  background: #D7263D;
  color: #fff;
}
.btn-primary:hover {
  background: #B91C32;
  box-shadow: 0 8px 24px -8px rgba(215, 38, 61, 0.6);
}
.btn-ghost {
  border: 1px solid rgba(255, 255, 255, 0.14);
  color: #F5F0EA;
}
.btn-ghost:hover {
  border-color: rgba(255, 255, 255, 0.35);
  background: rgba(255, 255, 255, 0.05);
}
.btn-primary:active,
.btn-ghost:active {
  transform: scale(0.98);
}

.cta {
  background: linear-gradient(135deg, #8E1426 0%, #B01E31 45%, #5A0D1A 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.cta-sheen {
  background:
    radial-gradient(60% 90% at 100% 0%, rgba(255, 214, 170, 0.22), transparent 65%),
    radial-gradient(50% 70% at 0% 100%, rgba(0, 0, 0, 0.35), transparent 70%);
}

a:focus-visible,
button:focus-visible {
  outline: 2px solid #D4B483;
  outline-offset: 3px;
}

.reveal {
  opacity: 0;
  transform: translateY(20px);
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