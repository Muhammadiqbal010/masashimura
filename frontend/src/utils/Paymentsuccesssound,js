// Suara "pembayaran berhasil" untuk sisi customer.
// Disintesis dengan Web Audio API, jadi tidak butuh file audio / koneksi ke CDN
// dan tidak ada delay download saat bunyi.

let ctx = null;

function getContext() {
  if (!ctx) {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    ctx = new AC();
  }
  return ctx;
}

/**
 * Panggil SEKALI di dalam handler klik/tap customer (mis. tombol "Bayar" /
 * "Pesan Sekarang"). Browser (terutama iOS Safari) baru mengizinkan suara
 * kalau AudioContext dibuat/di-resume dari gesture user. Kalau ini dilewatkan,
 * suara sukses yang bunyi beberapa detik kemudian (setelah bayar di popup)
 * akan diblok browser.
 */
export function unlockPaymentAudio() {
  const c = getContext();
  if (c && c.state === 'suspended') c.resume().catch(() => {});
}

// Satu nada dengan envelope (attack cepat, decay halus) supaya nggak "klik".
function tone(c, freq, start, duration, peak = 0.25) {
  const osc = c.createOscillator();
  const gain = c.createGain();
  osc.type = 'sine';
  osc.frequency.setValueAtTime(freq, start);
  gain.gain.setValueAtTime(0.0001, start);
  gain.gain.exponentialRampToValueAtTime(peak, start + 0.02);
  gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);
  osc.connect(gain).connect(c.destination);
  osc.start(start);
  osc.stop(start + duration + 0.05);
}

let lastPlayedAt = 0;

/**
 * Bunyikan chime sukses (C5 -> E5 -> G5, naik = "berhasil").
 * Ada guard 3 detik supaya tidak dobel kalau callback Snap dan polling
 * backend sama-sama memicu.
 */
export function playPaymentSuccess() {
  const now = Date.now();
  if (now - lastPlayedAt < 3000) return;
  lastPlayedAt = now;

  // Getar di HP (Android). iOS mengabaikan ini, aman.
  try { navigator.vibrate?.([80, 40, 120]); } catch { /* abaikan */ }

  const c = getContext();
  if (!c) return;
  try {
    if (c.state === 'suspended') c.resume().catch(() => {});
    const t = c.currentTime + 0.02;
    tone(c, 523.25, t,        0.35);          // C5
    tone(c, 659.25, t + 0.14, 0.35);          // E5
    tone(c, 783.99, t + 0.28, 0.70, 0.3);     // G5 (ditahan lebih lama)
  } catch (err) {
    console.warn('Gagal memutar suara pembayaran:', err);
  }
}