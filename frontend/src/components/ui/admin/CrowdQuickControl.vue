<!--
  CrowdQuickControl.vue — kontrol cepat keramaian untuk kasir/admin/owner.

  Dipakai di POS (NewOrder.vue) dan Active Orders. Dua ketukan: buka chip, pilih level.
  Level manual berlaku selama durasi yang dipilih, lalu badge kembali otomatis
  (dicek di server saat badge dibaca, tanpa cron).
-->
<template>
  <div class="cq-wrap" ref="rootRef">
    <button
      type="button"
      class="cq-chip"
      :class="[status ? `is-${status.level}` : '', { 'is-manual': isManual }]"
      :aria-expanded="open"
      aria-haspopup="dialog"
      title="Atur indikator keramaian"
      @click="toggle"
    >
      <span class="cq-dot" aria-hidden="true"></span>
      <span class="cq-chip-text">
        <template v-if="status">Keramaian: {{ status.label }}</template>
        <template v-else>Keramaian</template>
      </span>
      <span v-if="isManual" class="cq-chip-tag">manual</span>
    </button>

    <div v-if="open" class="cq-backdrop" @click="open = false"></div>
    <div v-if="open" class="cq-pop" role="dialog" aria-label="Atur keramaian">
      <p class="cq-title">Keramaian kedai</p>

      <p v-if="status && !status.enabled" class="cq-note cq-note--amber">
        Badge sedang dimatikan di Pengaturan, jadi pelanggan tidak melihatnya. Pilihan di sini tetap tersimpan.
      </p>
      <p v-else-if="status && !status.store_open" class="cq-note">
        Toko sedang tutup, badge tidak tampil ke pelanggan.
      </p>

      <div class="cq-levels" role="group" aria-label="Pilih level">
        <button
          v-for="lv in LEVELS"
          :key="lv.value"
          type="button"
          class="cq-level"
          :class="[`is-${lv.value}`, { 'is-active': isManual && status?.level === lv.value }]"
          :disabled="busy"
          @click="apply(lv.value)"
        >
          <span class="cq-dot" aria-hidden="true"></span>{{ lv.label }}
        </button>
      </div>

      <div class="cq-field">
        <span class="cq-label">Berlaku</span>
        <div class="cq-durations" role="group" aria-label="Lama berlaku">
          <button
            v-for="d in DURATIONS"
            :key="d.value"
            type="button"
            class="cq-dur"
            :class="{ 'is-on': duration === d.value }"
            @click="duration = d.value"
          >{{ d.label }}</button>
          <button
            type="button"
            class="cq-dur"
            :class="{ 'is-on': duration === 'until' }"
            @click="duration = 'until'"
          >Sampai jam</button>
        </div>
        <input
          v-if="duration === 'until'"
          v-model="untilTime"
          type="time"
          class="cq-time"
          aria-label="Berlaku sampai jam"
        />
      </div>

      <p v-if="errorText" class="cq-error" role="alert">{{ errorText }}</p>

      <div class="cq-foot">
        <p class="cq-auto" v-if="status?.auto">
          Otomatis saat ini: <strong>{{ labelOf(status.auto.level) }}</strong>
          · {{ status.auto.live_orders }} pesanan / 60 mnt
        </p>
        <p v-if="isManual" class="cq-until">
          Manual sampai {{ untilText }}.
        </p>
        <button
          v-if="isManual"
          type="button"
          class="cq-auto-btn"
          :disabled="busy"
          @click="apply('auto')"
        >Kembali otomatis</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from "vue"
import { toast } from "vue-sonner"
import { crowdAPI } from "@/api/crowd"

const LEVELS = [
  { value: "santai", label: "Santai" },
  { value: "sedang", label: "Sedang" },
  { value: "ramai",  label: "Ramai" },
]
const DURATIONS = [
  { value: 30,  label: "30 mnt" },
  { value: 60,  label: "60 mnt" },
  { value: 120, label: "2 jam" },
]
const REFRESH_MS = 60_000

const rootRef  = ref(null)
const open     = ref(false)
const busy     = ref(false)
const status   = ref(null)
const duration = ref(60)          // menit, atau "until"
const untilTime = ref("")
const errorText = ref("")
let timer = null

const labelOf = (lv) => LEVELS.find((l) => l.value === lv)?.label || ""
const isManual = computed(() => status.value?.mode === "manual")

const untilText = computed(() => {
  if (!status.value?.until) return ""
  return new Intl.DateTimeFormat("id-ID", {
    timeZone: "Asia/Jakarta", hour: "2-digit", minute: "2-digit", hourCycle: "h23",
  }).format(new Date(status.value.until)).replace(":", ".") + " WIB"
})

const load = async () => {
  try {
    const { data } = await crowdAPI.getStaffStatus()
    status.value = data
  } catch {
    /* diam: chip tetap menampilkan nilai terakhir */
  }
}

const toggle = () => {
  open.value = !open.value
  errorText.value = ""
  if (open.value) load()
}

const apply = async (level) => {
  errorText.value = ""
  const payload = { level }
  if (level !== "auto") {
    if (duration.value === "until") {
      if (!untilTime.value) { errorText.value = "Pilih jam berakhir dulu."; return }
      payload.until = untilTime.value
    } else {
      payload.duration_minutes = duration.value
    }
  }
  busy.value = true
  try {
    const { data } = await crowdAPI.setManual(payload)
    status.value = data
    toast.success(level === "auto" ? "Keramaian kembali otomatis" : `Keramaian diatur ke ${labelOf(level)}`)
    open.value = false
  } catch (e) {
    errorText.value = e?.response?.data?.detail || "Gagal menyimpan. Coba lagi."
  } finally {
    busy.value = false
  }
}

const onEsc = (e) => { if (e.key === "Escape") open.value = false }

onMounted(() => {
  load()
  timer = setInterval(() => { if (document.visibilityState === "visible") load() }, REFRESH_MS)
  document.addEventListener("keydown", onEsc)
})
onBeforeUnmount(() => {
  clearInterval(timer)
  document.removeEventListener("keydown", onEsc)
})
</script>

<style scoped>
.cq-wrap { position: relative; }

.cq-chip {
  --tone: var(--text-faint);
  display: inline-flex; align-items: center; gap: 0.5rem;
  min-height: 40px; padding: 0.5rem 0.9rem;
  background: var(--surface); border: 1px solid rgb(var(--ink) / 0.08);
  border-radius: 10px; color: var(--text-dim); cursor: pointer;
  font-family: 'Manrope', system-ui, sans-serif; font-size: 0.72rem;
  letter-spacing: -0.01em; white-space: nowrap;
  transition: border-color 0.15s, color 0.15s;
}
.cq-chip:hover { border-color: rgb(var(--ink) / 0.18); color: var(--text); }
.cq-chip:focus-visible, .cq-level:focus-visible, .cq-dur:focus-visible, .cq-auto-btn:focus-visible {
  outline: 2px solid var(--accent); outline-offset: 2px;
}
.cq-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--tone, var(--text-faint)); flex-shrink: 0; }
.cq-chip-tag {
  padding: 0.1rem 0.4rem; border-radius: 6px; font-size: 0.72rem;
  background: color-mix(in srgb, var(--amber) 14%, transparent); color: var(--amber-soft);
}

.cq-backdrop { position: fixed; inset: 0; z-index: 40; }
.cq-pop {
  position: absolute; top: calc(100% + 8px); right: 0; z-index: 41;
  width: min(340px, calc(100vw - 2rem)); padding: 0.9rem;
  display: flex; flex-direction: column; gap: 0.75rem;
  background: var(--surface); border: 1px solid rgb(var(--ink) / 0.1);
  border-radius: 12px; box-shadow: var(--shadow-lg);
  font-family: inherit; text-transform: none; letter-spacing: normal;
}
.cq-title { margin: 0; font-size: 0.72rem; letter-spacing: 0.14em; text-transform: uppercase; color: var(--text-faint); }
.cq-note {
  margin: 0; padding: 0.55rem 0.7rem; border-radius: 8px; font-size: 0.72rem; line-height: 1.45;
  background: rgb(var(--ink) / 0.04); color: var(--text-dim);
}
.cq-note--amber { background: color-mix(in srgb, var(--amber) 10%, transparent); color: var(--amber-soft); }

.cq-levels { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; }
.cq-level {
  --tone: var(--text-faint);
  display: flex; align-items: center; justify-content: center; gap: 0.45rem;
  min-height: 48px; border-radius: 10px; cursor: pointer;
  background: rgb(var(--ink) / 0.04); border: 1px solid rgb(var(--ink) / 0.1);
  color: var(--text); font-size: 0.85rem; font-weight: 600;
  transition: background 0.15s, border-color 0.15s;
}
.cq-level:hover:not(:disabled) { border-color: var(--tone); background: color-mix(in srgb, var(--tone) 10%, transparent); }
.cq-level.is-active { border-color: var(--tone); background: color-mix(in srgb, var(--tone) 16%, transparent); }
.cq-level:disabled { opacity: 0.55; cursor: wait; }
.cq-chip.is-santai, .cq-level.is-santai { --tone: var(--green-soft); }
.cq-chip.is-sedang, .cq-level.is-sedang { --tone: var(--amber-soft); }
.cq-chip.is-ramai,  .cq-level.is-ramai  { --tone: var(--red-soft); }

.cq-field { display: flex; flex-direction: column; gap: 0.4rem; }
.cq-label { font-size: 0.72rem; letter-spacing: 0.14em; text-transform: uppercase; color: var(--text-faint); }
.cq-durations { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.cq-dur {
  min-height: 36px; padding: 0.35rem 0.75rem; border-radius: 8px; cursor: pointer;
  background: transparent; border: 1px solid rgb(var(--ink) / 0.1);
  color: var(--text-dim); font-size: 0.75rem;
}
.cq-dur.is-on { background: rgb(var(--ink) / 0.09); border-color: rgb(var(--ink) / 0.25); color: var(--text); }
.cq-time {
  min-height: 40px; padding: 0.4rem 0.6rem; border-radius: 8px; font-size: 1rem;
  background: var(--bg); border: 1px solid rgb(var(--ink) / 0.12); color: var(--text);
}

.cq-error { margin: 0; font-size: 0.74rem; color: var(--red-soft); }
.cq-foot { display: flex; flex-direction: column; gap: 0.4rem; border-top: 1px solid rgb(var(--ink) / 0.06); padding-top: 0.65rem; }
.cq-auto, .cq-until { margin: 0; font-size: 0.72rem; color: var(--text-faint); }
.cq-auto strong { color: var(--text-dim); }
.cq-auto-btn {
  align-self: flex-start; min-height: 36px; padding: 0.35rem 0.8rem; border-radius: 8px; cursor: pointer;
  background: rgb(var(--ink) / 0.05); border: 1px solid rgb(var(--ink) / 0.1);
  color: var(--text-2); font-size: 0.74rem;
}
.cq-auto-btn:hover:not(:disabled) { color: var(--text); background: rgb(var(--ink) / 0.09); }

@media (max-width: 640px) {
  .cq-pop { left: 0; right: auto; }
}
@media (prefers-reduced-motion: reduce) {
  .cq-chip, .cq-level { transition: none; }
}
</style>
