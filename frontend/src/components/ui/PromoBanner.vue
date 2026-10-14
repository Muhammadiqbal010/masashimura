<!--
  PromoBanner.vue
  Taruh di src/components/ui/PromoBanner.vue

  Dipakai di Home.vue:
    import PromoBanner from "@/components/ui/PromoBanner.vue"
    <PromoBanner :promo="cms" />

  Props `promo` = objek dari /homepage/config/current/ (field promo_*).
  Semua opsi yang diatur di admin (Edit Homepage > Promo & Event) dibaca di sini:
  gambar, rasio, tata letak, posisi, fokus, warna, rata teks, overlay,
  jadwal, hitung mundur, dan tombol tutup.
-->
<template>
  <transition name="promo" appear>
    <section
      v-if="visible"
      class="promo border-b border-white/[0.06] bg-[#111111]"
      :style="vars"
      aria-label="Promo dan event"
    >
      <div class="max-w-7xl mx-auto px-6 sm:px-10 py-8 sm:py-10">
        <div class="promo-card" :class="cardClass" :style="cardStyle">

          <!-- Tombol tutup -->
          <button
            v-if="p.promo_dismissible"
            type="button"
            class="promo-close"
            aria-label="Tutup banner promo"
            @click="dismiss"
          >
            <X :size="16" />
          </button>

          <!-- Layout teks saja (tanpa gambar) -->
          <span v-if="layout === 'text'" class="promo-icon"><Tag :size="20" /></span>

          <!-- Gambar -->
          <div v-if="layout !== 'text'" class="promo-media" :style="mediaStyle">
            <img
              :src="p.promo_image"
              :alt="p.promo_image_alt || ''"
              :style="{ objectPosition: focusCss }"
              loading="lazy"
              decoding="async"
              @error="imgFailed = true"
            />
            <div v-if="layout === 'overlay'" class="promo-shade" :style="{ background: shade }"></div>
          </div>

          <!-- Teks -->
          <div class="promo-copy" :class="{ 'is-center': isCenter }">
            <p class="promo-eyebrow"><i></i>{{ p.promo_badge || "Promo & Event" }}</p>
            <h2 class="promo-title" :class="'promo-title--' + layout">{{ p.promo_title }}</h2>
            <p v-if="p.promo_text" class="promo-text">{{ p.promo_text }}</p>
            <p v-if="metaText" class="promo-meta">{{ metaText }}</p>

            <component
              v-if="p.promo_link"
              :is="isExternal ? 'a' : RouterLink"
              v-bind="isExternal
                ? { href: p.promo_link, target: '_blank', rel: 'noopener noreferrer' }
                : { to: p.promo_link }"
              class="promo-btn group"
            >
              {{ p.promo_link_label || "Lihat Detail" }}
              <ArrowRight :size="14" class="promo-btn-arrow" />
            </component>
          </div>
        </div>
      </div>
    </section>
  </transition>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue"
import { RouterLink } from "vue-router"
import { Tag, X, ArrowRight } from "lucide-vue-next"

const props = defineProps({
  promo: { type: Object, default: () => ({}) },
})

// ── Opsi (harus sama dengan admin & models.py) ───────────────────────────
const RATIOS = {
  "16:9": { css: "16 / 9", num: 16 / 9 },
  "21:9": { css: "21 / 9", num: 21 / 9 },
  "4:3":  { css: "4 / 3",  num: 4 / 3 },
  "1:1":  { css: "1 / 1",  num: 1 },
  "4:5":  { css: "4 / 5",  num: 4 / 5 },
  "3:4":  { css: "3 / 4",  num: 3 / 4 },
  "9:16": { css: "9 / 16", num: 9 / 16 },
}
const FOCUS = {
  "top-left": "0% 0%",   "top": "50% 0%",      "top-right": "100% 0%",
  "left": "0% 50%",      "center": "50% 50%",  "right": "100% 50%",
  "bottom-left": "0% 100%", "bottom": "50% 100%", "bottom-right": "100% 100%",
}
const THEMES = {
  red:     { accent: "#D71920", ink: "#ffffff" },
  amber:   { accent: "#FFD400", ink: "#1c1300" },
  emerald: { accent: "#10B981", ink: "#03150d" },
  sky:     { accent: "#0EA5E9", ink: "#02131c" },
  violet:  { accent: "#8B5CF6", ink: "#ffffff" },
  pink:    { accent: "#EC4899", ink: "#ffffff" },
}
const LAYOUTS = ["split", "overlay", "poster"]

const p = computed(() => props.promo || {})

// ── Waktu (diperbarui tiap 30 detik: hitung mundur & jadwal otomatis) ────
const now = ref(Date.now())
let timer = null
onMounted(() => { timer = setInterval(() => { now.value = Date.now() }, 30000) })
onUnmounted(() => { if (timer) clearInterval(timer) })

const startMs = computed(() => {
  const d = p.value.promo_from
  if (!d) return null
  const t = new Date(`${d}T00:00:00+07:00`).getTime()
  return isNaN(t) ? null : t
})
// promo_until berlaku sampai akhir hari (WIB)
const endMs = computed(() => {
  const d = p.value.promo_until
  if (!d) return null
  const t = new Date(`${d}T23:59:59+07:00`).getTime()
  return isNaN(t) ? null : t
})

// ── Isi & jadwal ─────────────────────────────────────────────────────────
const hasContent = computed(() => !!(p.value.promo_title || p.value.promo_text || p.value.promo_image))
const inSchedule = computed(() => {
  if (startMs.value !== null && now.value < startMs.value) return false
  if (endMs.value !== null && now.value > endMs.value) return false
  return true
})

// ── Tombol tutup: diingat per isi promo, muncul lagi kalau isinya diganti ─
const STORAGE_KEY = "masashimura:promo-dismissed"
const signature = computed(() => {
  const q = p.value
  const raw = [q.promo_badge, q.promo_title, q.promo_text, q.promo_image, q.promo_link, q.promo_from, q.promo_until].join("|")
  let h = 5381
  for (let i = 0; i < raw.length; i++) h = ((h << 5) + h + raw.charCodeAt(i)) | 0
  return String(h >>> 0)
})
const dismissedSig = ref(null)
try { dismissedSig.value = localStorage.getItem(STORAGE_KEY) } catch { /* storage diblokir: abaikan */ }

const isDismissed = computed(() => !!p.value.promo_dismissible && dismissedSig.value === signature.value)
const dismiss = () => {
  dismissedSig.value = signature.value
  try { localStorage.setItem(STORAGE_KEY, signature.value) } catch { /* abaikan */ }
}

const visible = computed(() => hasContent.value && inSchedule.value && !isDismissed.value)

// ── Gambar & layout ──────────────────────────────────────────────────────
const imgFailed = ref(false)
const hasImage = computed(() => !!p.value.promo_image && !imgFailed.value)
const layout = computed(() => {
  if (!hasImage.value) return "text"
  return LAYOUTS.includes(p.value.promo_layout) ? p.value.promo_layout : "split"
})
const ratio = computed(() => RATIOS[p.value.promo_image_ratio] || RATIOS["16:9"])
const focusCss = computed(() => FOCUS[p.value.promo_focus] || FOCUS.center)
const theme = computed(() => THEMES[p.value.promo_theme] || THEMES.red)
const isCenter = computed(() => layout.value !== "split" && layout.value !== "text" && p.value.promo_align === "center")
const isExternal = computed(() => /^https?:\/\//i.test(p.value.promo_link || ""))

const vars = computed(() => ({
  "--pa": theme.value.accent,
  "--pa-ink": theme.value.ink,
  "--pa-soft": `${theme.value.accent}22`,
  "--pa-line": `${theme.value.accent}66`,
}))

const cardClass = computed(() => [
  `promo-card--${layout.value}`,
  layout.value === "split" && p.value.promo_image_side === "right" ? "is-right" : "",
  isCenter.value ? "is-center" : "",
])

// Overlay: kartu mengikuti rasio gambar (portrait dibatasi lebarnya)
const cardStyle = computed(() => {
  if (layout.value !== "overlay") return {}
  const n = ratio.value.num
  return {
    "--ratio": ratio.value.css,
    maxWidth: n < 1 ? "26rem" : "100%",
    marginInline: n < 1 ? "auto" : "0",
  }
})

// Split/poster: lebar gambar menyesuaikan rasio supaya tinggi tetap wajar
const mediaStyle = computed(() => {
  const n = ratio.value.num
  if (layout.value === "overlay") return {}
  let width
  if (layout.value === "split") {
    width = n >= 1.5 ? "46%" : n >= 1.2 ? "40%" : n >= 0.95 ? "32%" : n >= 0.7 ? "26%" : "20%"
  } else {
    width = n >= 1.5 ? "min(100%, 44rem)" : n >= 1.2 ? "min(100%, 36rem)" : n >= 0.95 ? "min(100%, 26rem)" : n >= 0.7 ? "min(100%, 22rem)" : "min(100%, 18rem)"
  }
  return { "--media-w": width, aspectRatio: ratio.value.css }
})

const shade = computed(() => {
  const s = Math.min(Math.max(Number(p.value.promo_overlay) || 0, 0), 90) / 100
  return `linear-gradient(to top, rgba(8,8,8,${Math.min(1, s + 0.35)}), rgba(8,8,8,${(s * 0.55).toFixed(2)}) 60%, rgba(8,8,8,${(s * 0.2).toFixed(2)}))`
})

// ── Teks tanggal + hitung mundur ─────────────────────────────────────────
const untilLabel = computed(() => {
  if (!p.value.promo_until) return ""
  const d = new Date(`${p.value.promo_until}T12:00:00+07:00`)
  return isNaN(d) ? p.value.promo_until : d.toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" })
})

const countdownText = computed(() => {
  if (!p.value.promo_countdown || endMs.value === null) return ""
  const left = endMs.value - now.value
  if (left <= 0) return ""
  const MIN = 60 * 1000, HOUR = 60 * MIN, DAY = 24 * HOUR
  if (left >= DAY) return `Sisa ${Math.ceil(left / DAY)} hari`
  if (left >= HOUR) return `Sisa ${Math.floor(left / HOUR)} jam`
  return `Sisa ${Math.max(1, Math.ceil(left / MIN))} menit`
})

const metaText = computed(() => {
  const parts = []
  if (untilLabel.value) parts.push(`Sampai ${untilLabel.value}`)
  if (countdownText.value) parts.push(countdownText.value)
  return parts.join(" · ")
})
</script>

<style scoped>
/* Masuk / keluar */
.promo-enter-active,
.promo-leave-active { transition: opacity 0.5s ease, transform 0.5s cubic-bezier(0.16, 1, 0.3, 1); }
.promo-enter-from,
.promo-leave-to { opacity: 0; transform: translateY(14px); }

/* Kartu */
.promo-card { position: relative; display: flex; align-items: center; gap: 1.5rem; }
.promo-card--split.is-right { flex-direction: row-reverse; }
.promo-card--poster { flex-direction: column; align-items: flex-start; }
.promo-card--poster.is-center { align-items: center; }
.promo-card--text { justify-content: flex-start; }

/* Overlay: gambar jadi latar kartu */
.promo-card--overlay {
  align-items: stretch;
  aspect-ratio: var(--ratio, 16 / 9);
  min-height: 15rem;
  overflow: hidden;
  border: 1px solid rgb(255 255 255 / 0.1);
  background: #18181b;
}

/* Tombol tutup */
.promo-close {
  position: absolute; top: 0; right: 0; z-index: 3;
  display: flex; align-items: center; justify-content: center;
  width: 2.25rem; height: 2.25rem;
  color: #d4d4d8; background: rgb(0 0 0 / 0.55);
  border: 1px solid rgb(255 255 255 / 0.15);
  backdrop-filter: blur(4px); cursor: pointer;
  transition: background 0.2s, color 0.2s, border-color 0.2s;
}
.promo-close:hover { color: #fff; background: rgb(0 0 0 / 0.85); border-color: var(--pa); }
.promo-close:focus-visible { outline: 2px solid var(--pa); outline-offset: 2px; }
/* Di layout tanpa overlay, geser supaya tidak menimpa teks */
.promo-card--split .promo-close,
.promo-card--poster .promo-close,
.promo-card--text .promo-close { top: -0.25rem; right: -0.25rem; }

/* Ikon (layout teks) */
.promo-icon {
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  width: 2.75rem; height: 2.75rem;
  border: 1px solid var(--pa-line); background: var(--pa-soft); color: var(--pa);
}

/* Gambar */
.promo-media {
  position: relative; flex-shrink: 0; overflow: hidden;
  width: var(--media-w, auto);
  border: 1px solid rgb(255 255 255 / 0.1); background: #18181b;
}
.promo-media img { display: block; width: 100%; height: 100%; object-fit: cover; }
.promo-card--overlay .promo-media { position: absolute; inset: 0; width: auto; border: none; }
.promo-shade { position: absolute; inset: 0; pointer-events: none; }

/* Teks */
.promo-copy { position: relative; z-index: 1; min-width: 0; flex: 1; display: flex; flex-direction: column; gap: 0.5rem; }
.promo-card--overlay .promo-copy { justify-content: flex-end; padding: 1.5rem 1.75rem; }
.promo-card--poster .promo-copy { flex: none; width: 100%; max-width: 32rem; }
.promo-copy.is-center { align-items: center; text-align: center; }

.promo-eyebrow {
  display: flex; align-items: center; gap: 0.75rem; margin: 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 10px; letter-spacing: 0.3em; text-transform: uppercase; color: var(--pa);
}
.promo-eyebrow i { display: block; width: 1.5rem; height: 1px; background: var(--pa); }

.promo-title {
  margin: 0; font-weight: 800; text-transform: uppercase; letter-spacing: -0.01em;
  line-height: 1.1; color: #fff; overflow-wrap: anywhere;
  font-size: clamp(1.15rem, 1rem + 1vw, 1.6rem);
}
.promo-title--split,
.promo-title--overlay { font-size: clamp(1.4rem, 1rem + 2vw, 2.4rem); }

.promo-text { margin: 0; max-width: 36rem; font-size: 0.875rem; font-weight: 300; line-height: 1.6; color: #a1a1aa; }
.promo-meta {
  margin: 0; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 10px; letter-spacing: 0.15em; text-transform: uppercase; color: var(--pa);
}

/* Tombol */
.promo-btn {
  align-self: flex-start; display: inline-flex; align-items: center; justify-content: center; gap: 0.75rem;
  margin-top: 0.6rem; padding: 0.95rem 2rem;
  background: var(--pa); color: var(--pa-ink);
  font-size: 11px; font-weight: 700; letter-spacing: 0.2em; text-transform: uppercase;
  transition: transform 0.2s, filter 0.2s;
}
.promo-btn:hover { transform: translateY(-2px); filter: brightness(0.9); }
.promo-btn:focus-visible { outline: 2px solid #fff; outline-offset: 3px; }
.promo-btn-arrow { transition: transform 0.2s; }
.promo-btn:hover .promo-btn-arrow { transform: translateX(4px); }
.promo-copy.is-center .promo-btn { align-self: center; }

/* Layout teks saja: tombol di kanan pada layar lebar */
@media (min-width: 768px) {
  .promo-card--text { justify-content: space-between; }
  .promo-card--text .promo-copy { flex-direction: column; }
  .promo-card--text .promo-btn { margin-top: 0.4rem; }
}

/* Mobile */
@media (max-width: 767px) {
  .promo-card--split,
  .promo-card--split.is-right,
  .promo-card--text { flex-direction: column; align-items: stretch; gap: 1.1rem; }
  .promo-card--split .promo-media { width: 100%; max-width: 26rem; }
  .promo-card--text .promo-icon { align-self: flex-start; }
  .promo-btn { width: 100%; align-self: stretch; }
  .promo-card--poster .promo-btn { align-self: stretch; }
  .promo-card--overlay .promo-copy { padding: 1.1rem; }
  .promo-card--overlay .promo-btn { align-self: stretch; }
  .promo-card--overlay.is-center .promo-btn { align-self: stretch; }
}

@media (prefers-reduced-motion: reduce) {
  .promo-enter-active, .promo-leave-active, .promo-btn, .promo-btn-arrow { transition: none; }
}
</style>