"""
Notifikasi pesanan web ke Telegram (masuk ke HP walau browser ditutup) + bot aksi cepat.

Aktif kalau env TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID diisi (chat id boleh beberapa, dipisah koma).
Gagal kirim tidak pernah menggagalkan order: semua error ditelan dan dicatat di log.

Pesan order memakai tombol aksi (Terima / Tolak / Siap diambil). Tombolnya ditangani webhook
(telegram_bot.py → staff_actions.py); teks & tombol dirakit di telegram_ui.py (modul murni).
"""
import json
import logging
import math
import urllib.request

from django.conf import settings
from django.utils import timezone

from . import telegram_ui as ui
from .guards import CONFIRM_TIMEOUT_MINUTES, confirm_deadline

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 3   # Vercel serverless: jangan menahan respons ke pelanggan terlalu lama
EVENT_LABELS = {
    "accepted": "Diterima", "paid": "Dilunasi", "cancelled": "Dibatalkan", "auto_cancelled": "Dibatalkan otomatis",
    "ready": "Siap diambil", "unready": "Tanda siap dicabut", "refunded": "Refund diserahkan",
}
CHANNEL_LABELS = {"staff": "Admin", "telegram": "Telegram", "system": "Sistem"}


# ── Konfigurasi ────────────────────────────────────────────────────────────

def _token():
    return (getattr(settings, "TELEGRAM_BOT_TOKEN", "") or "").strip()


def _chat_ids():
    raw = getattr(settings, "TELEGRAM_CHAT_ID", "") or ""
    return [c.strip() for c in str(raw).split(",") if c.strip()]


def enabled():
    return bool(_token() and _chat_ids())


def is_allowed_chat(chat_id):
    """Hanya chat yang terdaftar di TELEGRAM_CHAT_ID yang boleh memakai bot."""
    return str(chat_id) in _chat_ids()


def is_allowed_user(user_id):
    """
    Opsional: TELEGRAM_ALLOWED_USER_IDS (dipisah koma) membatasi siapa yang boleh menekan tombol
    di grup. Kosong = semua anggota chat terdaftar boleh.
    """
    raw = str(getattr(settings, "TELEGRAM_ALLOWED_USER_IDS", "") or "").strip()
    if not raw:
        return True
    return str(user_id) in {c.strip() for c in raw.split(",") if c.strip()}


def _admin_url():
    return getattr(settings, "ADMIN_ORDERS_URL", "") or "https://masashimura.vercel.app/admin/orders"


# ── Panggilan API Telegram ─────────────────────────────────────────────────

def _call(method, payload):
    """Panggil metode Bot API. Mengembalikan (ok, data). Tidak pernah melempar error."""
    if not _token():
        return False, None
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{_token()}/{method}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        raw = urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS).read()
    except Exception as exc:   # jangan log exc penuh: bisa memuat URL yang berisi token bot
        logger.warning("Telegram %s gagal (%s)", method, exc.__class__.__name__)
        return False, None
    try:
        return True, json.loads(raw)
    except Exception:   # noqa: BLE001 - respons tidak bisa dibaca, tapi permintaan sukses
        return True, None


def _markup(buttons):
    """Terima daftar tombol datar (satu baris, gaya lama) atau daftar baris."""
    if not buttons:
        return None
    rows = [buttons] if isinstance(buttons[0], dict) else buttons
    return {"inline_keyboard": rows}


def send(text, buttons=None, chat_ids=None):
    """Kirim pesan ke semua chat id (atau `chat_ids`). True kalau minimal satu terkirim."""
    if not enabled():
        return False
    ok = False
    for chat_id in (chat_ids or _chat_ids()):
        payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
        markup = _markup(buttons)
        if markup:
            payload["reply_markup"] = markup
        sent, _ = _call("sendMessage", payload)
        ok = ok or sent
    return ok


def edit_message(chat_id, message_id, text, buttons=None):
    payload = {
        "chat_id": chat_id, "message_id": message_id, "text": text,
        "disable_web_page_preview": True,
        "reply_markup": _markup(buttons) or {"inline_keyboard": []},
    }
    return _call("editMessageText", payload)[0]


def answer_callback(callback_id, text="", alert=False):
    return _call("answerCallbackQuery", {
        "callback_query_id": callback_id, "text": (text or "")[:190], "show_alert": bool(alert),
    })[0]


# ── Perakit tampilan order ─────────────────────────────────────────────────

def order_view(order, banner=None):
    """Ubah Order jadi dict untuk telegram_ui. Satu-satunya tempat yang membaca DB untuk pesan."""
    items = list(order.items.select_related("menu"))
    lines = []
    for it in items[:8]:
        name = it.bundle_name or (it.menu.name if it.menu else "Item")
        lines.append(f"• {it.quantity}× {name}")
    if len(items) > 8:
        lines.append(f"• …dan {len(items) - 8} item lain")

    minutes_left = None
    if order.awaiting_confirmation:
        secs = (confirm_deadline(order) - timezone.now()).total_seconds()
        minutes_left = max(math.ceil(secs / 60), 0)

    last = (
        order.events.exclude(action="reminded").order_by("-created_at", "-id").first()
    )
    last_event = None
    if last:
        last_event = {
            "label": EVENT_LABELS.get(last.action, last.action),
            "actor": last.actor,
            "channel_label": CHANNEL_LABELS.get(last.channel, last.channel),
        }

    return {
        "id": order.pk,
        "order_number": order.order_number,
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "lines": lines,
        "total": order.total_price,
        "status": order.status,
        "payment_status": order.payment_status,
        "payment_method": order.payment_method,
        "source": order.source,
        "service_type": order.service_type,
        "table_number": order.table_number,
        "notes": order.notes,
        "awaiting": bool(order.awaiting_confirmation),
        "tracks_readiness": order.tracks_readiness,
        "is_ready": order.ready_source() is not None,
        "ready_manual": order.ready_at is not None,
        "confirm_minutes": CONFIRM_TIMEOUT_MINUTES,
        "minutes_left": minutes_left,
        "cancel_reason": order.cancel_reason,
        "cancel_note": order.cancel_note,
        "cancelled_by": order.cancelled_by,
        "last_event": last_event,
        "banner": banner,
        "admin_url": _admin_url(),
    }


def _load(order_pk):
    from .models import Order
    return Order.objects.filter(pk=order_pk).first()


def message_for(order, banner=None):
    """(teks, tombol) terbaru untuk satu order; dipakai pesan baru dan penyegaran lewat webhook."""
    v = order_view(order, banner=banner)
    return ui.render_text(v), ui.render_keyboard(v)


# ── Pesan otomatis ─────────────────────────────────────────────────────────

def new_web_cash_order(order_pk):
    """Order web bayar di toko: harus diterima kasir dalam CONFIRM_TIMEOUT_MINUTES."""
    if not enabled():
        return False
    order = _load(order_pk)
    if not order:
        return False
    return send(*message_for(order))


def web_order_paid(order_pk):
    """Order web yang dibayar online (QRIS) dan sudah lunas."""
    if not enabled():
        return False
    order = _load(order_pk)
    if not order:
        return False
    return send(*message_for(order))


def order_reminder(order_pk):
    """Pengingat: order belum diterima dan sisa waktunya tinggal sedikit."""
    if not enabled():
        return False
    order = _load(order_pk)
    if not order or not order.awaiting_confirmation or order.status != "pending":
        return False   # sudah diterima/dibatalkan sejak dijadwalkan
    return send(*message_for(order, banner="reminder"))


def order_auto_cancelled(order_pk):
    """Kabar: order dibatalkan otomatis karena tidak diterima tepat waktu."""
    if not enabled():
        return False
    order = _load(order_pk)
    if not order or order.status != "cancelled":
        return False
    return send(*message_for(order))


def send_report(text):
    """Laporan teks (ringkasan harian) ke semua chat terdaftar."""
    return send(text)
