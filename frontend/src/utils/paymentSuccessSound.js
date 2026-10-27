// src/utils/paymentSuccessSound.js
//
// Suara "pembayaran berhasil".
// Chime disintesis pakai Web Audio API (tanpa file audio), lalu disusul suara ngomong
// bahasa Indonesia lewat speechSynthesis bawaan browser, lengkap dengan nominal:
//   "Pembayaran berhasil, enam belas ribu lima ratus rupiah. Terima kasih"

const MIN_GAP_MS  = 3000   // jeda minimum antar suara (cegah dobel)
const SPEAK_DELAY = 750    // suara ngomong mulai setelah chime selesai

// ══════════════════════════════════════════════════════════════════════════════
// Chime (Web Audio)
// ══════════════════════════════════════════════════════════════════════════════
let ctx = null

function getContext() {
  if (!ctx) {
    const AC = window.AudioContext || window.webkitAudioContext
    if (!AC) return null
    ctx = new AC()
  }
  return ctx
}

// Satu nada dengan envelope (attack cepat, decay halus) supaya nggak "klik".
function tone(c, freq, start, duration, peak = 0.25) {
  const osc  = c.createOscillator()
  const gain = c.createGain()
  osc.type = 'sine'
  osc.frequency.setValueAtTime(freq, start)
  gain.gain.setValueAtTime(0.0001, start)
  gain.gain.exponentialRampToValueAtTime(peak, start + 0.02)
  gain.gain.exponentialRampToValueAtTime(0.0001, start + duration)
  osc.connect(gain).connect(c.destination)
  osc.start(start)
  osc.stop(start + duration + 0.05)
}

function playChime() {
  const c = getContext()
  if (!c) return
  try {
    if (c.state === 'suspended') c.resume().catch(() => {})
    const t = c.currentTime + 0.02
    tone(c, 523.25, t,        0.35)        // C5
    tone(c, 659.25, t + 0.14, 0.35)        // E5
    tone(c, 783.99, t + 0.28, 0.70, 0.3)   // G5 (ditahan lebih lama)
  } catch (err) {
    console.warn('Gagal memutar chime pembayaran:', err)
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// Suara ngomong (speechSynthesis)
// ══════════════════════════════════════════════════════════════════════════════
const synth =
  typeof window !== 'undefined' && 'speechSynthesis' in window
    ? window.speechSynthesis
    : null

let idVoice = null

// Android kadang melaporkan "id_ID" (pakai underscore), makanya dinormalisasi.
const normalizeLang = (lang) => (lang || '').replace('_', '-').toLowerCase()

function loadVoice() {
  if (!synth) return
  const voices = synth.getVoices()
  idVoice =
    voices.find((v) => normalizeLang(v.lang) === 'id-id') ||
    voices.find((v) => normalizeLang(v.lang).startsWith('id')) ||
    null
}

if (synth) {
  loadVoice()
  // Daftar suara sering baru terisi sesaat setelah halaman dibuka.
  synth.addEventListener?.('voiceschanged', loadVoice)
}

function speak(text) {
  if (!synth) return
  try {
    if (!idVoice) loadVoice()
    // Potong suara sebelumnya hanya kalau memang masih ada yang berjalan/antre.
    if (synth.speaking || synth.pending) synth.cancel()
    if (synth.paused) synth.resume()

    const u = new SpeechSynthesisUtterance(text)
    u.lang = 'id-ID'
    if (idVoice) u.voice = idVoice
    u.rate = 0.95
    synth.speak(u)
  } catch (err) {
    console.warn('Gagal memutar suara ngomong:', err)
  }
}

// ── Angka → kata Indonesia (16500 → "enam belas ribu lima ratus") ────────────
const SATUAN = ['', 'satu', 'dua', 'tiga', 'empat', 'lima', 'enam', 'tujuh', 'delapan', 'sembilan', 'sepuluh', 'sebelas']

// Sambung "<bagian> <sisa>" hanya kalau sisanya tidak nol.
const withRest = (head, rest) => (rest ? `${head} ${toWords(rest)}` : head)

function toWords(n) {
  if (n < 12)  return SATUAN[n]
  if (n < 20)  return `${toWords(n - 10)} belas`
  if (n < 100) return withRest(`${toWords(Math.floor(n / 10))} puluh`, n % 10)
  if (n < 200) return withRest('seratus', n % 100)
  if (n < 1e3) return withRest(`${toWords(Math.floor(n / 100))} ratus`, n % 100)
  if (n < 2e3) return withRest('seribu', n % 1e3)
  if (n < 1e6) return withRest(`${toWords(Math.floor(n / 1e3))} ribu`, n % 1e3)
  if (n < 1e9) return withRest(`${toWords(Math.floor(n / 1e6))} juta`, n % 1e6)
  if (n < 1e12) return withRest(`${toWords(Math.floor(n / 1e9))} miliar`, n % 1e9)
  return String(n)
}

export function terbilang(value) {
  const n = Math.floor(Number(value))
  if (!Number.isFinite(n) || n < 0) return ''
  if (n === 0) return 'nol'
  return toWords(n)
}

// ══════════════════════════════════════════════════════════════════════════════
// API publik
// ══════════════════════════════════════════════════════════════════════════════
let speechUnlocked = false

/**
 * Panggil di dalam handler klik/tap (sebelum await apa pun).
 * Browser (terutama iOS Safari) baru mengizinkan suara kalau dibuka dari gesture user.
 * Aman dipanggil berulang.
 */
export function unlockPaymentAudio() {
  const c = getContext()
  if (c && c.state === 'suspended') c.resume().catch(() => {})

  if (!synth) return
  loadVoice()
  if (speechUnlocked) return
  try {
    const u = new SpeechSynthesisUtterance(' ')
    u.volume = 0   // senyap, hanya untuk membuka kunci
    synth.speak(u)
    speechUnlocked = true
  } catch { /* abaikan */ }
}

let lastPlayedAt = 0

/**
 * Chime sukses (C5 → E5 → G5), lalu suara ngomong.
 *
 * @param {{ total?: number|string, force?: boolean }} opts
 *   total : nominal dalam rupiah (kalau kosong, nominal tidak disebut)
 *   force : lewati guard 3 detik (berguna di panel admin kalau ada dua pembayaran berdekatan)
 */
export function playPaymentSuccess({ total, force = false } = {}) {
  const now = Date.now()
  if (!force && now - lastPlayedAt < MIN_GAP_MS) return
  lastPlayedAt = now

  // Getar di HP (Android). Dilewati kalau user belum pernah berinteraksi dengan halaman,
  // karena Chrome menolak dan mencatat peringatan di console. iOS mengabaikan ini.
  try {
    const active = navigator.userActivation?.hasBeenActive ?? true
    if (active) navigator.vibrate?.([80, 40, 120])
  } catch { /* abaikan */ }

  playChime()

  const amount = Math.round(Number(total))
  const text = amount > 0
    ? `Pembayaran berhasil, ${terbilang(amount)} rupiah. Terima kasih`
    : 'Pembayaran berhasil. Terima kasih'

  setTimeout(() => speak(text), SPEAK_DELAY)
}