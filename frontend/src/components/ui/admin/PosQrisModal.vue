<template>
  <Teleport to="body">
  <transition name="qr-fade">
    <div v-if="qr.open" class="modal-overlay qr-overlay" role="dialog" aria-modal="true" aria-label="Pembayaran QRIS">
      <div class="qr-box" :class="`is-${qr.state}`">

        <!-- Ringkasan: selalu tampil -->
        <header class="qr-top">
          <span class="qr-chip">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><path d="M14 14h3v3h-3zM20 14v.01M14 20v.01M20 20v.01M17 17h3v3"/></svg>
            QRIS Otomatis
          </span>
          <p class="qr-amount">{{ formatPrice(qr.total) }}</p>
          <p class="qr-meta">
            <span v-if="qr.name">{{ qr.name }} · </span><span class="qr-meta-no">{{ qr.orderNumber }}</span>
          </p>
        </header>

        <!-- Membuat QR -->
        <div v-if="qr.state === 'loading'" class="qr-stage qr-stage--center">
          <div class="qr-skeleton" aria-hidden="true"></div>
          <p class="qr-status"><span class="qr-dot"></span> Menyiapkan QR…</p>
        </div>

        <!-- Menunggu bayar -->
        <div v-else-if="qr.state === 'waiting'" class="qr-stage">
          <!-- QR ditampilkan Midtrans Snap (jalur sama dengan checkout web) -->
          <div class="qr-frame qr-frame--embed" :class="{ 'is-full': qr.fullEmbed }">
            <span class="qr-corner qr-corner--tl"></span><span class="qr-corner qr-corner--tr"></span>
            <span class="qr-corner qr-corner--bl"></span><span class="qr-corner qr-corner--br"></span>
            <div class="qr-embed-loading" aria-hidden="true"><span class="qr-dot qr-dot--live"></span> Memuat QR…</div>
            <div id="pos-snap-embed" class="qr-embed"></div>
          </div>
          <p v-if="qr.embedError" class="qr-hint" role="alert">{{ qr.embedError }}</p>
          <button type="button" class="qr-link qr-open" @click="qr.fullEmbed = !qr.fullEmbed">{{ qr.fullEmbed ? 'Tampilkan hanya QR' : 'QR terpotong? Tampilan lengkap' }}</button>

          <p class="qr-brand" aria-hidden="true"><span class="qr-hanko">支払</span> Masashimura · QRIS</p>
          <p class="qr-status" role="status"><span class="qr-dot qr-dot--live"></span> Menunggu pembayaran</p>
          <p class="qr-hint">Scan dengan GoPay, OVO, DANA, ShopeePay, atau m-banking apa saja.</p>

          <div class="qr-timer" :class="{ 'is-low': qr.secondsLeft <= 120 }">
            <div class="qr-timer-bar"><span :style="{ width: qrProgress + '%' }"></span></div>
            <span class="qr-timer-text">Berlaku {{ qrClock }}</span>
          </div>
        </div>

        <!-- Lunas -->
        <div v-else-if="qr.state === 'paid'" class="qr-stage qr-stage--center">
          <div class="qr-success" aria-hidden="true">
            <span class="qr-ripple"></span><span class="qr-ripple qr-ripple--2"></span>
            <svg viewBox="0 0 52 52" class="qr-tick"><circle cx="26" cy="26" r="24" class="qr-tick-ring"/><path d="M14 27l8 8 16-17" class="qr-tick-path"/></svg>
          </div>
          <p class="qr-ok-title">Pembayaran diterima</p>
          <p class="qr-hint">Terima kasih! Nota sudah tercatat lunas.</p>
        </div>

        <!-- Kedaluwarsa -->
        <div v-else-if="qr.state === 'expired'" class="qr-stage qr-stage--center">
          <div class="qr-expired" aria-hidden="true">⏱</div>
          <p class="qr-ok-title">QR kedaluwarsa</p>
          <p class="qr-hint">
            {{ qr.mode === 'bill' ? 'Tagihan masih aman. Buat QR baru atau bayar dengan cara lain.' : 'Tutup, lalu buat pesanan lagi atau pilih metode lain.' }}
          </p>
        </div>

        <!-- Aksi -->
        <footer class="qr-actions">
          <template v-if="qr.state === 'paid'">
            <button type="button" class="submit-btn" @click="finishQr">Selesai</button>
            <div class="qr-auto"><span></span></div>
          </template>
          <template v-else-if="qr.state === 'expired'">
            <button v-if="qr.mode === 'bill'" type="button" class="submit-btn" :disabled="qr.busy" @click="retryBillQr">Buat QR baru</button>
            <button type="button" class="qr-link" :disabled="qr.busy" @click="cancelQr">{{ qr.busy ? 'Menutup…' : 'Tutup' }}</button>
          </template>
          <template v-else>
            <button type="button" class="qr-link" :disabled="qr.busy || qr.state === 'loading'" @click="cancelQr">
              {{ qr.busy ? 'Menutup…' : qr.mode === 'bill' ? 'Tutup QR · tagihan tetap tersimpan' : 'Batalkan · ganti metode' }}
            </button>
          </template>
        </footer>
      </div>
    </div>
  </transition>
  </Teleport>
</template>

<script setup>
// Modal QRIS otomatis untuk nota "bayar nanti" (dipakai Active Order). Logikanya sama dengan modal di POS.
import { ref, computed, nextTick, onBeforeUnmount } from "vue";
import { toast } from "vue-sonner";
import { paymentAPI } from "@/api";
import { unlockPaymentAudio, playPaymentSuccess } from "@/utils/paymentSuccessSound.js";

const emit = defineEmits(["paid", "closed"]);

const formatPrice = (p) =>
  new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", minimumFractionDigits: 0 }).format(Number(p) || 0);

const QR_TTL = 15 * 60;   // detik; harus sama dengan POS_QR_EXPIRY_MINUTES di backend
const blank = () => ({ open: false, state: "idle", mode: "bill", name: "", orderNumber: "", total: 0, url: "", snapToken: "", embedError: "", fullEmbed: false, expiresAt: 0, secondsLeft: 0, busy: false });
const qr = ref(blank());
let qrPollTimer = null;
let qrTickTimer = null;

const stopQrTimers = () => {
  clearInterval(qrPollTimer); clearInterval(qrTickTimer);
  qrPollTimer = null; qrTickTimer = null;
};
const qrProgress = computed(() => Math.min(100, Math.max(0, (qr.value.secondsLeft / QR_TTL) * 100)));
const qrClock = computed(() => {
  const s = Math.max(qr.value.secondsLeft, 0);
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
});

// ── Midtrans Snap (QR lewat snap.embed, sama seperti checkout web) ──
const MIDTRANS_CLIENT_KEY = import.meta.env.VITE_MIDTRANS_CLIENT_KEY || "";
const SNAP_URL = import.meta.env.VITE_MIDTRANS_IS_PRODUCTION === "true"
  ? "https://app.midtrans.com/snap/snap.js"
  : "https://app.sandbox.midtrans.com/snap/snap.js";
let snapLoading = null;
const loadSnap = () => {
  if (window.snap) return Promise.resolve();
  if (!MIDTRANS_CLIENT_KEY) return Promise.reject(new Error("VITE_MIDTRANS_CLIENT_KEY belum diisi"));
  if (snapLoading) return snapLoading;
  snapLoading = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = SNAP_URL;
    script.setAttribute("data-client-key", MIDTRANS_CLIENT_KEY);
    script.onload = () => resolve();
    script.onerror = () => { snapLoading = null; script.remove(); reject(new Error("Gagal memuat Midtrans Snap")); };
    document.head.appendChild(script);
  });
  return snapLoading;
};
const hideSnapEmbed = () => { try { window.snap?.hide(); } catch { /* abaikan */ } };

const mountSnapQr = async (token) => {
  if (!token) return;
  qr.value.embedError = "";
  try {
    await loadSnap();
    await nextTick();
    hideSnapEmbed();   // embed order sebelumnya masih tercatat aktif di Snap
    await new Promise((r) => setTimeout(r, 80));
    const done = () => pollQr();   // status asli selalu dari backend, bukan dari callback Snap
    window.snap.embed(token, { embedId: "pos-snap-embed", onSuccess: done, onPending: done, onError: done, onClose: done });
  } catch (e) {
    qr.value.embedError = e?.message || "Gagal menampilkan QR. Tutup lalu coba lagi.";
  }
};

const apiError = (e, fallback) => toast.error(e?.response?.data?.detail || fallback);

const applyQrData = (d) => {
  qr.value.url = d.qr_url || qr.value.url;
  qr.value.snapToken = d.snap_token || qr.value.snapToken;
  qr.value.total = Number(d.total ?? qr.value.total);
  qr.value.expiresAt = d.expires_at ? new Date(d.expires_at).getTime() : qr.value.expiresAt;
  qr.value.secondsLeft = Math.floor((qr.value.expiresAt - Date.now()) / 1000);
  qr.value.state = "waiting";
  mountSnapQr(qr.value.snapToken);
};

let currentOrder = null;
const start = async (order) => {
  if (!order) return;
  unlockPaymentAudio();
  currentOrder = order;
  stopQrTimers();
  qr.value = { ...blank(), open: true, state: "loading", name: order.customer_name || "", orderNumber: order.order_number, total: Number(order.total_price || 0) };
  try {
    const { data } = await paymentAPI.posQrisCreate(order.order_number);
    applyQrData(data);
    qrPollTimer = setInterval(pollQr, 2500);
    qrTickTimer = setInterval(tickQr, 1000);
  } catch (e) {
    stopQrTimers();
    qr.value.open = false;
    apiError(e, "Gagal membuat QR pembayaran.");
    emit("closed");
  }
};

const tickQr = () => {
  if (qr.value.state !== "waiting") return;
  qr.value.secondsLeft = Math.floor((qr.value.expiresAt - Date.now()) / 1000);
  if (qr.value.secondsLeft <= -5) { qr.value.state = "expired"; stopQrTimers(); }
};

const onQrPaid = () => {
  if (qr.value.state === "paid") return;
  stopQrTimers();
  qr.value.state = "paid";
  playPaymentSuccess({ total: qr.value.total, force: true });
  setTimeout(() => { if (qr.value.state === "paid") finishQr(); }, 4000);
};

const pollQr = async () => {
  if (qr.value.state !== "waiting") return;
  try {
    const { data } = await paymentAPI.posQrisStatus(qr.value.orderNumber);
    if (data.payment_status === "paid") return onQrPaid();
    if (data.payment_status === "void" || data.status === "cancelled" || data.expired) {
      qr.value.state = "expired"; stopQrTimers();
    }
  } catch { /* jaringan putus sebentar: coba lagi di putaran berikutnya */ }
};

const finishQr = () => {
  const wasPaid = qr.value.state === "paid";
  stopQrTimers();
  hideSnapEmbed();
  qr.value.open = false;
  qr.value.state = "idle";
  if (wasPaid) emit("paid", currentOrder);
  emit("closed");
};

const retryBillQr = () => start(currentOrder);

// Tutup QR: nota TETAP ada (hanya QR-nya yang ditutup). Kalau ternyata sudah dibayar → 409.
const cancelQr = async () => {
  if (qr.value.state === "paid") return finishQr();
  qr.value.busy = true;
  try {
    await paymentAPI.posQrisCancel(qr.value.orderNumber);
    stopQrTimers();
    hideSnapEmbed();
    qr.value.open = false;
    qr.value.state = "idle";
    toast.info("QR ditutup. Tagihan masih tersimpan.");
    emit("closed");
  } catch (e) {
    if (e?.response?.status === 409) onQrPaid();
    else apiError(e, "Gagal menutup QR.");
  } finally {
    qr.value.busy = false;
  }
};

onBeforeUnmount(stopQrTimers);
defineExpose({ start });
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; z-index: 70;
  background: var(--overlay); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; padding: 1rem;
}
.submit-btn {
  display: flex; align-items: center; justify-content: center; gap: 0.45rem;
  padding: 0.85rem; border-radius: 12px; border: none;
  background: var(--accent); color: var(--on-accent);
  font-family: var(--font-body); font-size: 0.8rem;
  letter-spacing: -0.01em;
  cursor: pointer; transition: background 0.15s;
  box-shadow: 0 4px 20px color-mix(in srgb, var(--accent) 20%, transparent);
}
.submit-btn:hover:not(:disabled) { background: var(--accent-hover); }
.submit-btn:disabled { background: rgb(var(--ink) / 0.06); color: var(--text-faint); cursor: not-allowed; box-shadow: none; }

/* ── Modal QRIS otomatis ─────────────────────────────────────────── */
.qr-overlay { z-index: 90; }
.qr-fade-enter-active, .qr-fade-leave-active { transition: opacity 0.2s ease; }
.qr-fade-enter-from, .qr-fade-leave-to { opacity: 0; }
.qr-fade-enter-active .qr-box { animation: qr-rise 0.28s cubic-bezier(0.2, 0.8, 0.2, 1); }
@keyframes qr-rise { from { transform: translateY(14px) scale(0.97); opacity: 0; } to { transform: none; opacity: 1; } }

.qr-box {
  width: 100%; max-width: 420px; max-height: 94dvh; overflow-y: auto;
  display: flex; flex-direction: column; align-items: center; gap: 1rem;
  padding: 1.4rem 1.25rem 1.1rem; text-align: center; color: var(--text);
  background: var(--surface); border: 1px solid rgb(var(--ink) / 0.08); border-radius: 22px;
  box-shadow: 0 24px 60px rgb(0 0 0 / 0.35);
}
.qr-top { display: flex; flex-direction: column; align-items: center; gap: 0.2rem; }
.qr-chip {
  display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.22rem 0.65rem; border-radius: 99px;
  background: rgb(var(--ink) / 0.06); font-size: 0.7rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: var(--text-dim);
}
.qr-amount { margin: 0.35rem 0 0; font-family: var(--font-mono); font-size: 2.1rem; font-weight: 800; letter-spacing: -0.02em; line-height: 1.1; }
.qr-meta { margin: 0; font-size: 0.8rem; color: var(--text-dim); max-width: 100%; overflow-wrap: anywhere; }
.qr-meta-no { font-family: var(--font-mono); font-size: 0.74rem; color: var(--text-faint); }

.qr-stage { display: flex; flex-direction: column; align-items: center; gap: 0.7rem; width: 100%; }
.qr-stage--center { padding: 0.6rem 0 0.2rem; }

/* Bingkai QR: selalu putih supaya mudah di-scan, di tema gelap sekalipun */
.qr-frame { position: relative; padding: 0.9rem; border-radius: 20px; background: #fff; box-shadow: 0 6px 24px rgb(0 0 0 / 0.18); overflow: hidden; }
.qr-frame--embed { width: 100%; padding: 0; height: 300px; }
.qr-frame--embed.is-full { height: min(62dvh, 560px); }
.qr-embed { position: relative; z-index: 1; width: 100%; height: 100%; overflow: hidden; border-radius: 20px; }
/* Header, nominal & timer bawaan Snap digeser keluar bingkai: kasir cukup melihat QR-nya (nominal, timer, tombol sudah ada di modal ini). */
.qr-embed :deep(iframe) { display: block; width: 100% !important; height: 780px !important; border: 0; margin-top: -192px; }
.is-full .qr-embed { overflow-y: auto; }
.is-full .qr-embed :deep(iframe) { height: 100% !important; margin-top: 0; }
.qr-embed-loading { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; gap: 0.5rem; font-size: 0.85rem; color: #666; }
.qr-open { font-size: 0.8rem; text-decoration: none; }
.qr-frame--embed .qr-corner { z-index: 3; pointer-events: none; }
.qr-frame--embed::after {   /* garis scan halus di atas QR */
  content: ""; position: absolute; left: 14px; right: 14px; top: 14px; height: 2px; z-index: 3; pointer-events: none;
  background: linear-gradient(90deg, transparent, var(--accent, #d92b22), transparent); opacity: 0.55;
  animation: qr-sweep 2.4s ease-in-out infinite alternate;
}
@keyframes qr-sweep { from { transform: translateY(0); } to { transform: translateY(268px); } }
.is-full::after { display: none; }
.qr-brand { display: inline-flex; align-items: center; gap: 0.45rem; margin: 0; font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-muted, rgb(var(--ink) / 0.55)); }
.qr-hanko {
  display: inline-grid; place-items: center; width: 1.5rem; height: 1.5rem; border-radius: 0.3rem;
  background: var(--accent, #d92b22); color: #fff; font-size: 0.62rem; font-weight: 700; letter-spacing: 0; transform: rotate(-6deg);
}
/* Pita merah bergaris + watermark kanji di modal QR */
.qr-box { position: relative; overflow-x: hidden; }
.qr-box::before {
  content: ""; position: absolute; left: 0; right: 0; top: 0; height: 7px; pointer-events: none;
  background: repeating-linear-gradient(135deg, var(--accent, #d92b22) 0 10px, rgb(var(--ink) / 0.85) 10px 20px);
}
.qr-box::after {
  content: "支払"; position: absolute; right: -0.4rem; bottom: 2.2rem; font-size: 6.5rem; font-weight: 800; line-height: 1;
  color: var(--accent, #d92b22); opacity: 0.06; pointer-events: none; user-select: none;
}
.qr-img { display: block; width: min(64vw, 248px); height: auto; aspect-ratio: 1; image-rendering: pixelated; }
.qr-corner { position: absolute; width: 22px; height: 22px; border: 3px solid var(--accent, #d92b22); opacity: 0.9; }
.qr-corner--tl { top: 7px; left: 7px; border-right: 0; border-bottom: 0; border-top-left-radius: 8px; }
.qr-corner--tr { top: 7px; right: 7px; border-left: 0; border-bottom: 0; border-top-right-radius: 8px; }
.qr-corner--bl { bottom: 7px; left: 7px; border-right: 0; border-top: 0; border-bottom-left-radius: 8px; }
.qr-corner--br { bottom: 7px; right: 7px; border-left: 0; border-top: 0; border-bottom-right-radius: 8px; }
.qr-scan {
  position: absolute; left: 12px; right: 12px; top: 12px; height: 2px; border-radius: 2px; pointer-events: none;
  background: linear-gradient(90deg, transparent, var(--accent, #d92b22), transparent); opacity: 0.55;
  animation: qr-scan 2.6s ease-in-out infinite;
}
@keyframes qr-scan { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(calc(min(64vw, 248px) + 4px)); } }

.qr-skeleton { width: min(64vw, 248px); aspect-ratio: 1; border-radius: 20px; background: linear-gradient(110deg, rgb(var(--ink) / 0.05) 30%, rgb(var(--ink) / 0.11) 50%, rgb(var(--ink) / 0.05) 70%); background-size: 200% 100%; animation: qr-shimmer 1.2s linear infinite; }
@keyframes qr-shimmer { to { background-position: -200% 0; } }

.qr-status { display: inline-flex; align-items: center; gap: 0.5rem; margin: 0.1rem 0 0; font-size: 0.9rem; font-weight: 700; }
.qr-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--text-faint); }
.qr-dot--live { background: #f59e0b; box-shadow: 0 0 0 0 rgb(245 158 11 / 0.55); animation: qr-pulse 1.6s ease-out infinite; }
@keyframes qr-pulse { 0% { box-shadow: 0 0 0 0 rgb(245 158 11 / 0.55); } 100% { box-shadow: 0 0 0 10px rgb(245 158 11 / 0); } }
.qr-hint { margin: 0; max-width: 28ch; font-size: 0.8rem; line-height: 1.45; color: var(--text-dim); }

.qr-timer { display: flex; flex-direction: column; align-items: center; gap: 0.35rem; width: 100%; max-width: 248px; }
.qr-timer-bar { width: 100%; height: 5px; border-radius: 99px; background: rgb(var(--ink) / 0.08); overflow: hidden; }
.qr-timer-bar span { display: block; height: 100%; border-radius: inherit; background: var(--text-dim); transition: width 1s linear; }
.qr-timer-text { font-family: var(--font-mono); font-size: 0.75rem; font-weight: 600; color: var(--text-dim); }
.qr-timer.is-low .qr-timer-bar span { background: #ef4444; }
.qr-timer.is-low .qr-timer-text { color: #ef4444; }

/* Sukses */
.qr-success { position: relative; display: flex; align-items: center; justify-content: center; width: 96px; height: 96px; }
.qr-ripple { position: absolute; inset: 0; border-radius: 50%; background: rgb(22 163 74 / 0.22); animation: qr-ripple 1.8s ease-out infinite; }
.qr-ripple--2 { animation-delay: 0.9s; }
@keyframes qr-ripple { from { transform: scale(0.7); opacity: 0.9; } to { transform: scale(1.5); opacity: 0; } }
.qr-tick { position: relative; width: 84px; height: 84px; }
.qr-tick-ring { fill: #16a34a; }
.qr-tick-path { fill: none; stroke: #fff; stroke-width: 4.5; stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 40; stroke-dashoffset: 40; animation: qr-draw 0.5s 0.2s ease-out forwards; }
@keyframes qr-draw { to { stroke-dashoffset: 0; } }
.qr-ok-title { margin: 0; font-size: 1.15rem; font-weight: 800; }
.qr-expired { display: flex; align-items: center; justify-content: center; width: 72px; height: 72px; border-radius: 50%; background: rgb(var(--ink) / 0.07); font-size: 2rem; }

/* Aksi */
.qr-actions { display: flex; flex-direction: column; align-items: stretch; gap: 0.35rem; width: 100%; }
.qr-actions .submit-btn { width: 100%; }
.qr-link { min-height: 42px; border: 0; background: transparent; color: var(--text-dim); font-family: inherit; font-size: 0.82rem; font-weight: 600; cursor: pointer; border-radius: 10px; }
.qr-link:hover:not(:disabled) { background: rgb(var(--ink) / 0.06); color: var(--text); }
.qr-link:disabled { opacity: 0.5; cursor: not-allowed; }
.qr-auto { height: 3px; border-radius: 99px; background: rgb(var(--ink) / 0.08); overflow: hidden; }
.qr-auto span { display: block; height: 100%; background: #16a34a; transform-origin: left; animation: qr-auto 4s linear forwards; }
@keyframes qr-auto { from { transform: scaleX(1); } to { transform: scaleX(0); } }

@media (prefers-reduced-motion: reduce) {
  .qr-scan, .qr-dot--live, .qr-ripple, .qr-skeleton, .qr-fade-enter-active .qr-box { animation: none; }
  .qr-tick-path { animation: none; stroke-dashoffset: 0; }
  .qr-auto span { animation-duration: 0.01s; }
}


</style>
