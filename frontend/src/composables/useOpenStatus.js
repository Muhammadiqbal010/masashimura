import { ref, computed, onMounted, onUnmounted } from "vue"

/**
 * Jam operasional — satu-satunya sumber kebenaran.
 * Key = hari (0 Minggu … 6 Sabtu), value = [buka, tutup] dalam menit sejak 00.00.
 * null = libur.
 */
export const OPEN_HOURS = {
  0: null,
  1: [11 * 60, 22 * 60 + 30],
  2: [11 * 60, 22 * 60 + 30],
  3: [11 * 60, 22 * 60 + 30],
  4: [11 * 60, 22 * 60 + 30],
  5: [11 * 60, 22 * 60 + 30],
  6: [11 * 60, 22 * 60 + 30],
}

export const SCHEDULE_TEXT = "Senin – Sabtu · 11.00 – 22.30 WIB"

const DAY_NAMES = ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]
const WEEKDAY_INDEX = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 }

const fmt = (m) =>
  `${String(Math.floor(m / 60)).padStart(2, "0")}.${String(m % 60).padStart(2, "0")}`

// Selalu pakai waktu Jakarta, bukan jam perangkat pengunjung
const getJakartaNow = () => {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Jakarta",
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(new Date())
  const get = (type) => parts.find((p) => p.type === type)?.value
  return {
    day: WEEKDAY_INDEX[get("weekday")] ?? 0,
    minutes: Number(get("hour")) * 60 + Number(get("minute")),
  }
}

// Satu timer dipakai bersama (hero + footer), jalan selama ada komponen yang memakai
const tick = ref(Date.now())
let subscribers = 0
let timer = null

export function useOpenStatus() {
  onMounted(() => {
    subscribers++
    tick.value = Date.now()
    if (!timer) timer = setInterval(() => { tick.value = Date.now() }, 30_000)
  })
  onUnmounted(() => {
    subscribers = Math.max(0, subscribers - 1)
    if (subscribers === 0 && timer) {
      clearInterval(timer)
      timer = null
    }
  })

  const status = computed(() => {
    tick.value // dependensi reaktif
    const { day, minutes } = getJakartaNow()
    const today = OPEN_HOURS[day]

    if (today && minutes >= today[0] && minutes < today[1]) {
      return { isOpen: true, label: "Buka sekarang", detail: `Tutup ${fmt(today[1])}` }
    }

    if (today && minutes < today[0]) {
      return { isOpen: false, label: "Tutup", detail: `Buka hari ini ${fmt(today[0])}` }
    }

    for (let i = 1; i <= 7; i++) {
      const d = (day + i) % 7
      const hours = OPEN_HOURS[d]
      if (!hours) continue
      return {
        isOpen: false,
        label: "Tutup",
        detail: i === 1 ? `Buka besok ${fmt(hours[0])}` : `Buka lagi ${DAY_NAMES[d]} ${fmt(hours[0])}`,
      }
    }
    return { isOpen: false, label: "Tutup", detail: "" }
  })

  return { status, scheduleText: SCHEDULE_TEXT }
}