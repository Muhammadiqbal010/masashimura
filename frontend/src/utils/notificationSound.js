const NOTIFICATION_SOUND_URL =
  'https://res.cloudinary.com/dndonk7an/video/upload/v1783788054/MASASHIMURA_xsl8nr.aac';

let audioEl = null;
let unlocked = false;

function getAudioElement() {
  if (!audioEl) {
    audioEl = new Audio(NOTIFICATION_SOUND_URL);
    audioEl.preload = 'auto';
  }
  return audioEl;
}

export function unlockNotificationAudio() {
  if (unlocked) return;
  const el = getAudioElement();

  // Trik unlock autoplay browser: play super pelan sekali, lalu reset
  el.volume = 0;
  el.play()
    .then(() => {
      el.pause();
      el.currentTime = 0;
      el.volume = 1;
      unlocked = true;
    })
    .catch(() => {
      // Browser masih nge-block (belum ada interaksi user), coba lagi nanti
    });
}

export function playNewOrderChime() {
  const el = getAudioElement();
  try {
    el.currentTime = 0;
    el.volume = 1;
    const playPromise = el.play();
    if (playPromise !== undefined) {
      playPromise.catch((err) => {
        console.warn('Gagal memutar notifikasi suara:', err);
      });
    }
  } catch (err) {
    console.warn('Gagal memutar notifikasi suara:', err);
  }
}