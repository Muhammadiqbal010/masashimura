/**
 * useStoreSettings
 *
 * Singleton composable — satu fetch, dibagi ke semua komponen.
 * Menggantikan useAdminWhatsapp.js sepenuhnya.
 *
 * Expose:
 *   settings        → reactive object (semua data dari API)
 *   settingsReady   → true setelah pengaturan dimuat (dari server atau cache)
 *   isStoreOpen     → computed boolean (sudah handle override + jadwal + hari, ikut waktu berjalan)
 *   closedMessage   → string pesan saat tutup
 *   nextOpenText    → "Buka hari ini pukul 11.00" / "Buka besok pukul 11.00" / "" (kosong kalau tidak relevan)
 *   closesText      → "Buka sampai pukul 22.30 WIB" saat buka menurut jadwal, selain itu ""
 *   openStatus      → { ready, isOpen, label, detail } untuk pil status (Home, Footer, Kontak)
 *   scheduleRows    → jadwal per kelompok hari: [{ label, time, closed, dayKeys }] (hari berurutan yang jamnya sama digabung)
 *   scheduleText    → ringkasan satu baris, mis. "Senin – Sabtu · 11.00 – 22.30 WIB" ("" kalau jadwal belum diisi)
 *   todayIndex      → hari ini (WIB) dalam sistem jadwal: 0=Senin … 6=Minggu
 *   adminWhatsapp   → string nomor WA admin
 *   fetchSettings() → fetch dari API (safe dipanggil berkali-kali)
 *   refetchSettings() → paksa fetch ulang (dipakai setelah admin save)
 *   saveSettings()  → tidak dipakai di sini, save dilakukan di AdminSettings.vue
 */

import { ref, computed, getCurrentInstance, onMounted, onUnmounted } from "vue"
import apiClient from "@/api/client"

const CACHE_KEY = "store_settings"
const DEFAULT_CLOSED_MESSAGE =
  "Maaf, kami sedang tidak beroperasi. Silakan kembali sesuai jam operasional kami."

const DAY_NAMES = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"] // 0=Senin

// ── Cache dari kunjungan sebelumnya ──────────────────────────────────────────
// Dipakai sebagai nilai awal supaya halaman tidak sempat berkedip "toko tutup"
// selama menunggu respons server.
const loadCached = () => {
  try {
    const parsed = JSON.parse(localStorage.getItem(CACHE_KEY) || "null")
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : null
  } catch {
    return null
  }
}

const cached = loadCached()

// ── Singleton state (di luar fungsi) ─────────────────────────────────────────
const settings = ref({
  admin_whatsapp:    "",
  is_open_override:  null,   // null = ikut jadwal | true = paksa buka | false = paksa tutup
  closed_message:    DEFAULT_CLOSED_MESSAGE,
  operating_hours:   {},     // { "0": { open:"08:00", close:"22:00" } | null, ... } 0=Senin
  ...(cached || {}),
})

// true kalau data pengaturan sudah diketahui (dari cache atau dari server)
const settingsReady = ref(!!cached)

let fetched      = false
let fetchPromise = null

// ── Jam berjalan ─────────────────────────────────────────────────────────────
// isStoreOpen harus ikut berubah saat jam buka/tutup terlewati walau halaman
// dibiarkan terbuka. Satu timer dipakai bersama selama ada komponen yang memakai.
const TICK_MS = 30_000
const nowTick = ref(Date.now())
let tickSubscribers = 0
let tickTimer = null

// ── Helper ─────────────────────────────────────────────────────────────────────
function getNowWIB(timestamp = Date.now()) {
  // WIB = UTC+7
  const wib = new Date(timestamp + 7 * 60 * 60 * 1000)
  return {
    day:     wib.getUTCDay(),           // 0=Minggu ... 6=Sabtu
    hours:   wib.getUTCHours(),
    minutes: wib.getUTCMinutes(),
    // Konversi ke sistem kita: 0=Senin ... 6=Minggu
    dayKey:  String(wib.getUTCDay() === 0 ? 6 : wib.getUTCDay() - 1),
  }
}

function timeToMinutes(timeStr) {
  // "08:30" → 510
  if (!timeStr) return 0
  const [h, m] = timeStr.split(":").map(Number)
  return h * 60 + m
}

// "11:00" → "11.00" (format penulisan jam yang dipakai di situs ini)
const displayTime = (timeStr) => String(timeStr || "").replace(":", ".")

// ── fetchSettings (singleton) ────────────────────────────────────────────────
const fetchSettings = () => {
  if (fetched) return Promise.resolve(settings.value)
  if (fetchPromise) return fetchPromise

  fetchPromise = apiClient
    .get("/orders/settings/")
    .then(({ data }) => {
      settings.value = {
        admin_whatsapp:   data.admin_whatsapp   || "",
        is_open_override: data.is_open_override ?? null,
        closed_message:   data.closed_message   || settings.value.closed_message,
        operating_hours:  data.operating_hours  || {},
      }
      try { localStorage.setItem(CACHE_KEY, JSON.stringify(settings.value)) } catch { /* abaikan */ }
      // Hanya ditandai selesai kalau berhasil. Kalau gagal, panggilan berikutnya mencoba lagi.
      fetched = true
    })
    .catch(() => {
      // Gagal: tetap pakai cache yang sudah dimuat di atas.
      // Nomor WA diisi dari fallback supaya tombol WhatsApp tetap bisa dipakai.
      if (!settings.value.admin_whatsapp) {
        let fallback = ""
        try { fallback = localStorage.getItem("admin_whatsapp") || "" } catch { /* abaikan */ }
        settings.value.admin_whatsapp = fallback || import.meta.env.VITE_ADMIN_WHATSAPP || ""
      }
    })
    .finally(() => {
      settingsReady.value = true
      fetchPromise = null
    })

  return fetchPromise
}

// Force re-fetch (dipakai setelah admin save)
const refetchSettings = () => {
  fetched = false
  return fetchSettings()
}

export function useStoreSettings() {

  // Daftarkan timer bersama (hanya kalau dipanggil di dalam komponen)
  if (getCurrentInstance()) {
    onMounted(() => {
      tickSubscribers++
      nowTick.value = Date.now()
      if (!tickTimer) tickTimer = setInterval(() => { nowTick.value = Date.now() }, TICK_MS)
    })
    onUnmounted(() => {
      tickSubscribers = Math.max(0, tickSubscribers - 1)
      if (tickSubscribers === 0 && tickTimer) {
        clearInterval(tickTimer)
        tickTimer = null
      }
    })
  }

  // ── isStoreOpen (computed) ───────────────────────────────────────────────────
  const isStoreOpen = computed(() => {
    // Pengaturan belum diketahui: jangan langsung menampilkan "tutup".
    // Server tetap yang menentukan saat pesanan dibuat.
    if (!settingsReady.value) return true

    // 1. Override manual
    if (settings.value.is_open_override === true)  return true
    if (settings.value.is_open_override === false) return false

    // 2. Ikut jadwal
    const hoursMap = settings.value.operating_hours || {}
    // Jadwal sama sekali belum ada (belum diatur / gagal dimuat): jangan menutup toko
    // tanpa dasar. Libur diwakili jadwal hari itu = null, bukan jadwal kosong.
    if (Object.keys(hoursMap).length === 0) return true

    const { dayKey, hours, minutes } = getNowWIB(nowTick.value)
    const todaySchedule = hoursMap[dayKey]

    // Hari libur (null / tidak ada jadwal)
    if (!todaySchedule || !todaySchedule.open || !todaySchedule.close) return false

    const nowMinutes   = hours * 60 + minutes
    const openMinutes  = timeToMinutes(todaySchedule.open)
    const closeMinutes = timeToMinutes(todaySchedule.close)

    return nowMinutes >= openMinutes && nowMinutes < closeMinutes
  })

  const closedMessage = computed(() =>
    settings.value.closed_message ||
    "Maaf, kami sedang tidak beroperasi."
  )

  // Kapan toko buka lagi, menurut jadwal. Kosong kalau toko sedang buka, atau kalau
  // admin menutup manual (override): saat itu kapan bukanya tidak bisa diketahui dari jadwal.
  const nextOpenText = computed(() => {
    if (!settingsReady.value || isStoreOpen.value) return ""
    if (settings.value.is_open_override === false) return ""

    const hoursMap = settings.value.operating_hours || {}
    const scheduleOf = (key) => {
      const s = hoursMap[String(key)]
      return s?.open && s?.close ? s : null
    }

    const { dayKey, hours, minutes } = getNowWIB(nowTick.value)
    const today = Number(dayKey)
    const nowMinutes = hours * 60 + minutes

    const todaySchedule = scheduleOf(today)
    if (todaySchedule && nowMinutes < timeToMinutes(todaySchedule.open)) {
      return `Buka hari ini pukul ${displayTime(todaySchedule.open)} WIB`
    }

    for (let i = 1; i <= 7; i++) {
      const key = (today + i) % 7
      const s = scheduleOf(key)
      if (!s) continue
      return i === 1
        ? `Buka besok pukul ${displayTime(s.open)} WIB`
        : `Buka lagi hari ${DAY_NAMES[key]} pukul ${displayTime(s.open)} WIB`
    }
    return ""
  })

  const adminWhatsapp = computed(() => settings.value.admin_whatsapp || "")

  // ── Tampilan jadwal & status ke pelanggan ────────────────────────────────────
  // Semua teks jam buka di situs diturunkan dari sini, jadi selalu sama dengan
  // yang diatur admin di Pengaturan Sistem (tidak ada jam yang ditulis manual di halaman).
  const todayIndex = computed(() => Number(getNowWIB(nowTick.value).dayKey))

  // Jadwal valid satu hari: { open, close } atau null (libur / jam tutup <= jam buka, sama seperti server).
  const rangeOf = (entry) => {
    if (!entry?.open || !entry?.close) return null
    return timeToMinutes(entry.close) > timeToMinutes(entry.open)
      ? { open: entry.open, close: entry.close }
      : null
  }

  const dayRangeLabel = (keys) => {
    if (keys.length === 7) return "Setiap hari"
    if (keys.length === 1) return DAY_NAMES[keys[0]]
    if (keys.length === 2) return `${DAY_NAMES[keys[0]]} & ${DAY_NAMES[keys[1]]}`
    return `${DAY_NAMES[keys[0]]} – ${DAY_NAMES[keys[keys.length - 1]]}`
  }

  const scheduleRows = computed(() => {
    const map = settings.value.operating_hours || {}
    if (Object.keys(map).length === 0) return []
    const days = Array.from({ length: 7 }, (_, i) => rangeOf(map[String(i)]))
    const sig = (r) => (r ? `${r.open}-${r.close}` : "off")
    const rows = []
    let start = 0
    for (let i = 1; i <= 7; i++) {
      if (i === 7 || sig(days[i]) !== sig(days[start])) {
        const keys = Array.from({ length: i - start }, (_, k) => start + k)
        const r = days[start]
        rows.push({
          label: dayRangeLabel(keys),
          time: r ? `${displayTime(r.open)} – ${displayTime(r.close)}` : "Tutup",
          closed: !r,
          dayKeys: keys,
        })
        start = i
      }
    }
    return rows
  })

  const scheduleText = computed(() => {
    const open = scheduleRows.value.filter((r) => !r.closed)
    if (!open.length) return ""
    return open.map((r) => `${r.label} · ${r.time}`).join("; ") + " WIB"
  })

  // Jadwal hari ini (null kalau libur / belum diatur)
  const todayRange = computed(() => rangeOf((settings.value.operating_hours || {})[String(todayIndex.value)]))

  const closesText = computed(() => {
    if (!settingsReady.value || !isStoreOpen.value) return ""
    if (settings.value.is_open_override === true) return ""   // dibuka paksa: jam tutup jadwal tidak berlaku
    return todayRange.value ? `Buka sampai pukul ${displayTime(todayRange.value.close)} WIB` : ""
  })

  const openStatus = computed(() => {
    if (!settingsReady.value) return { ready: false, isOpen: false, label: "", detail: "" }
    if (isStoreOpen.value) {
      return {
        ready: true,
        isOpen: true,
        label: "Buka sekarang",
        detail: closesText.value ? `Tutup ${displayTime(todayRange.value.close)}` : "",
      }
    }
    return {
      ready: true,
      isOpen: false,
      label: "Tutup",
      detail: settings.value.is_open_override === false ? "Sedang ditutup sementara" : nextOpenText.value,
    }
  })

  return {
    settings,
    settingsReady,
    isStoreOpen,
    closedMessage,
    nextOpenText,
    closesText,
    openStatus,
    scheduleRows,
    scheduleText,
    todayIndex,
    adminWhatsapp,
    fetchSettings,
    refetchSettings,
  }
}