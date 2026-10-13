<!--
  PromoCard.vue  →  src/components/ui/PromoCard.vue
  Satu kartu promo. Dipakai oleh PromoSection.vue (jangan dipakai sendirian).

  Props:
    promo    = satu objek dari /homepage/promos/
    now      = Date.now() dari parent (untuk hitung mundur)
    compact  = true kalau kartu berbagi baris dengan kartu lain (2-3 menyamping)
-->
<template>
  <article class="promo-card" :class="cardClass" :style="[vars, cardStyle]">

    <button
      v-if="p.dismissible"
      type="button"
      class="promo-close"
      aria-label="Tutup promo"
      @click="$emit('dismiss', p)"
    >
      <X :size="16" />
    </button>

    <span v-if="layout === 'text'" class="promo-icon"><Tag :size="20" /></span>

    <div v-if="layout !== 'text'" class="promo-media" :style="mediaStyle">
      <img
        :src="p.image"
        :alt="p.image_alt || ''"
        :style="{ objectPosition: focusCss }"
        loading="lazy"
        decoding="async"
        @error="imgFailed = true"
      />
      <div v-if="layout === 'overlay'" class="promo-shade" :style="{ background: shade }"></div>
    </div>

    <div class="promo-copy" :class="{ 'is-center': isCenter }">
      <p class="promo-eyebrow"><i></i>{{ p.badge || "Promo & Event" }}</p>
      <h2 class="promo-title" :class="'promo-title--' + layout">{{ p.title }}</h2>
      <p v-if="p.text" class="promo-text">{{ p.text }}</p>
      <p v-if="metaText" class="promo-meta">{{ metaText }}</p>

      <component
        v-if="p.link"
        :is="isExternal ? 'a' : RouterLink"
        v-bind="isExternal
          ? { href: p.link, target: '_blank', rel: 'noopener noreferrer' }
          : { to: p.link }"
        class="promo-btn group"
      >
        {{ p.link_label || "Lihat Detail" }}
        <ArrowRight :size="14" class="promo-btn-arrow" />
      </component>
    </div>
  </article>
</template>

<script setup>
import { ref, computed } from "vue"
import { RouterLink } from "vue-router"
import { Tag, X, ArrowRight } from "lucide-vue-next"
import { FOCUS, THEMES, ratioOf, endMs } from "@/utils/promo"

const props = defineProps({
  promo:   { type: Object, required: true },
  now:     { type: Number, default: () => Date.now() },
  compact: { type: Boolean, default: false },
})
defineEmits(["dismiss"])

const LAYOUTS = ["split", "overlay", "poster"]
const p = computed(() => props.promo || {})

const imgFailed = ref(false)
const hasImage = computed(() => !!p.value.image && !imgFailed.value)
const layout = computed(() => {
  if (!hasImage.value) return "text"
  return LAYOUTS.includes(p.value.layout) ? p.value.layout : "split"
})
const ratio = computed(() => ratioOf(p.value))
const focusCss = computed(() => FOCUS[p.value.focus] || FOCUS.center)
const theme = computed(() => THEMES[p.value.theme] || THEMES.red)
const isCenter = computed(() => layout.value !== "split" && layout.value !== "text" && p.value.align === "center")
const isExternal = computed(() => /^https?:\/\//i.test(p.value.link || ""))

const vars = computed(() => ({
  "--pa": theme.value.accent,
  "--pa-ink": theme.value.ink,
  "--pa-soft": `${theme.value.accent}22`,
  "--pa-line": `${theme.value.accent}66`,
}))

const cardClass = computed(() => [
  `promo-card--${layout.value}`,
  layout.value === "split" && p.value.image_side === "right" ? "is-right" : "",
  isCenter.value ? "is-center" : "",
  props.compact ? "is-compact" : "",
])

// Overlay: kartu mengikuti rasio gambar (portrait dibatasi lebarnya kalau sendirian)
const cardStyle = computed(() => {
  if (layout.value !== "overlay") return {}
  const n = ratio.value.num
  const alone = !props.compact
  return {
    "--ratio": ratio.value.css,
    maxWidth: alone && n < 1 ? "26rem" : "100%",
    marginInline: alone && n < 1 ? "auto" : "0",
  }
})

// Split/poster: lebar gambar menyesuaikan rasio. Compact = penuh selebar kolom.
const mediaStyle = computed(() => {
  if (layout.value === "overlay") return {}
  const n = ratio.value.num
  if (props.compact) return { "--media-w": "100%", aspectRatio: ratio.value.css }
  let width
  if (layout.value === "split") {
    width = n >= 1.5 ? "46%" : n >= 1.2 ? "40%" : n >= 0.95 ? "32%" : n >= 0.7 ? "26%" : "20%"
  } else {
    width = n >= 1.5 ? "min(100%, 44rem)" : n >= 1.2 ? "min(100%, 36rem)" : n >= 0.95 ? "min(100%, 26rem)" : n >= 0.7 ? "min(100%, 22rem)" : "min(100%, 18rem)"
  }
  return { "--media-w": width, aspectRatio: ratio.value.css }
})

const shade = computed(() => {
  const s = Math.min(Math.max(Number(p.value.overlay) || 0, 0), 90) / 100
  return `linear-gradient(to top, rgba(8,8,8,${Math.min(1, s + 0.35)}), rgba(8,8,8,${(s * 0.55).toFixed(2)}) 60%, rgba(8,8,8,${(s * 0.2).toFixed(2)}))`
})

// ── Teks tanggal + hitung mundur ─────────────────────────────────────────
const untilLabel = computed(() => {
  if (!p.value.show_until) return ""
  const d = new Date(`${p.value.show_until}T12:00:00+07:00`)
  return isNaN(d) ? p.value.show_until : d.toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" })
})

const countdownText = computed(() => {
  const end = endMs(p.value)
  if (!p.value.countdown || end === null) return ""
  const left = end - props.now
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
.promo-card { position: relative; display: flex; align-items: center; gap: 1.5rem; min-width: 0; }
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
.promo-card--split .promo-close,
.promo-card--poster .promo-close,
.promo-card--text .promo-close { top: -0.25rem; right: -0.25rem; }
.promo-card--split.is-compact .promo-close,
.promo-card--poster.is-compact .promo-close { top: 0; right: 0; } /* di atas gambar */

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

/* Compact: berbagi baris -> gambar di atas, teks di bawah */
.promo-card--split.is-compact { flex-direction: column; align-items: stretch; gap: 1rem; }
.promo-card--split.is-compact .promo-copy,
.promo-card--poster.is-compact .promo-copy { max-width: none; }
.promo-card--poster.is-compact { align-items: stretch; gap: 1rem; }

/* Teks */
.promo-copy { position: relative; z-index: 1; min-width: 0; flex: 1; display: flex; flex-direction: column; gap: 0.5rem; }
.promo-card--overlay .promo-copy { justify-content: flex-end; padding: 1.5rem 1.75rem; }
.promo-card--overlay.is-compact .promo-copy { padding: 1.1rem; }
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
.is-compact .promo-title,
.is-compact .promo-title--split,
.is-compact .promo-title--overlay { font-size: clamp(1.1rem, 0.9rem + 0.9vw, 1.5rem); }

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
.is-compact .promo-btn { padding: 0.8rem 1.4rem; letter-spacing: 0.15em; }
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
</style>