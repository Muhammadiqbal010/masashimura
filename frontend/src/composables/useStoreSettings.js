/**
 * useStoreSettings
 *
 * Singleton composable — satu fetch, dibagi ke semua komponen.
 * Menggantikan useAdminWhatsapp.js sepenuhnya.
 *
 * Expose:
 *   settings        → reactive object (semua data dari API)
 *   isStoreOpen     → computed boolean (sudah handle override + jadwal + hari)
 *   closedMessage   → string pesan saat tutup
 *   adminWhatsapp   → string nomor WA admin
 *   fetchSettings() → fetch dari API (safe dipanggil berkali-kali)
 *   saveSettings()  → tidak dipakai di sini, save dilakukan di AdminSettings.vue
 */

import { ref, computed } from "vue"
import apiClient from "@/api/client"

// ── Singleton state (di luar fungsi) ─────────────────────────────────────────
const settings = ref({
  admin_whatsapp:    "",
  is_open_override:  null,   // null = ikut jadwal | true = paksa buka | false = paksa tutup
  closed_message:    "Maaf, kami sedang tidak beroperasi. Silakan kembali sesuai jam operasional kami.",
  operating_hours:   {},     // { "0": { open:"08:00", close:"22:00" } | null, ... } 0=Senin
})

let fetched      = false
let fetchPromise = null

// ── Helper ─────────────────────────────────────────────────────────────────────
function getNowWIB() {
  // WIB = UTC+7
  const now = new Date()
  const wib = new Date(now.getTime() + 7 * 60 * 60 * 1000)
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

export function useStoreSettings() {

  // ── isStoreOpen (computed) ───────────────────────────────────────────────────
  const isStoreOpen = computed(() => {
    // 1. Override manual
    if (settings.value.is_open_override === true)  return true
    if (settings.value.is_open_override === false) return false

    // 2. Ikut jadwal
    const { dayKey, hours, minutes } = getNowWIB()
    const todaySchedule = settings.value.operating_hours?.[dayKey]

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

  const adminWhatsapp = computed(() => settings.value.admin_whatsapp || "")

  // ── fetchSettings ────────────────────────────────────────────────────────────
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
        // Cache ke localStorage
        localStorage.setItem("store_settings", JSON.stringify(settings.value))
      })
      .catch(() => {
        // Fallback: localStorage
        try {
          const cached = localStorage.getItem("store_settings")
          if (cached) {
            const parsed = JSON.parse(cached)
            settings.value = { ...settings.value, ...parsed }
          } else {
            // Last resort: env var untuk WA
            settings.value.admin_whatsapp =
              localStorage.getItem("admin_whatsapp") ||
              import.meta.env.VITE_ADMIN_WHATSAPP ||
              ""
          }
        } catch { /* ignore */ }
      })
      .finally(() => {
        fetched      = true
        fetchPromise = null
      })

    return fetchPromise
  }

  // Force re-fetch (dipakai setelah admin save)
  const refetchSettings = () => {
    fetched = false
    return fetchSettings()
  }

  return {
    settings,
    isStoreOpen,
    closedMessage,
    adminWhatsapp,
    fetchSettings,
    refetchSettings,
  }
}