"""
Notifikasi pesanan web ke Telegram (masuk ke HP walau browser ditutup).

Aktif kalau env TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID diisi (chat id boleh beberapa, dipisah koma).
Gagal kirim tidak pernah menggagalkan order: semua error ditelan dan dicatat di log.
"""
import json
import logging
import urllib.request

from django.conf import settings

from .guards import CONFIRM_TIMEOUT_MINUTES

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 3   # Vercel serverless: jangan menahan respons ke pelanggan terlalu lama


def _token():
    return (getattr(settings, "TELEGRAM_BOT_TOKEN", "") or "").strip()


def _chat_ids():
    raw = getattr(settings, "TELEGRAM_CHAT_ID", "") or ""
    return [c.strip() for c in str(raw).split(",") if c.strip()]


def enabled():
    return bool(_token() and _chat_ids())


def send(text, buttons=None):
    """Kirim pesan ke semua chat id. Mengembalikan True kalau minimal satu terkirim."""
    if not enabled():
        return False
    ok = False
    for chat_id in _chat_ids():
        payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
        if buttons:
            payload["reply_markup"] = {"inline_keyboard": [buttons]}
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{_token()}/sendMessage",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS).read()
            ok = True
        except Exception as exc:   # jangan log exc penuh: bisa memuat URL yang berisi token bot
            logger.warning("Telegram gagal terkirim ke %s (%s)", chat_id, exc.__class__.__name__)
    return ok


def _rp(n):
    return "Rp " + f"{int(n):,}".replace(",", ".")


def _wa_link(phone):
    digits = "".join(ch for ch in str(phone or "") if ch.isdigit())
    if not digits:
        return ""
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    return f"https://wa.me/{digits}"


def _admin_url():
    return getattr(settings, "ADMIN_ORDERS_URL", "") or "https://masashimura.vercel.app/admin/orders"


def _describe(order, header, footer):
    items = list(order.items.select_related("menu"))
    lines = []
    for it in items[:8]:
        name = it.bundle_name or (it.menu.name if it.menu else "Item")
        lines.append(f"• {it.quantity}× {name}")
    if len(items) > 8:
        lines.append(f"• …dan {len(items) - 8} item lain")
    parts = [
        header,
        f"No. {order.order_number}",
        f"Nama: {order.customer_name or '-'}",
        f"WA: {order.customer_phone or '-'}",
        "",
        *lines,
        "",
        f"Total: {_rp(order.total_price)}",
        footer,
    ]
    return "\n".join(parts)


def _buttons(order):
    buttons = [{"text": "Buka Active Orders", "url": _admin_url()}]
    wa = _wa_link(order.customer_phone)
    if wa:
        buttons.append({"text": "Chat pemesan (WA)", "url": wa})
    return buttons


def new_web_cash_order(order_pk):
    """Order web bayar di toko: harus diterima kasir dalam CONFIRM_TIMEOUT_MINUTES."""
    from .models import Order

    if not enabled():
        return False
    order = Order.objects.filter(pk=order_pk).first()
    if not order:
        return False
    text = _describe(
        order,
        "🛎️ PESANAN WEB BARU (bayar di toko)",
        f"⏱ Terima di Active Orders dalam {CONFIRM_TIMEOUT_MINUTES} menit, kalau tidak dibatalkan otomatis.",
    )
    return send(text, _buttons(order))


def web_order_paid(order_pk):
    """Order web yang dibayar online (QRIS) dan sudah lunas."""
    from .models import Order

    if not enabled():
        return False
    order = Order.objects.filter(pk=order_pk).first()
    if not order:
        return False
    text = _describe(order, "✅ PESANAN WEB LUNAS (QRIS)", "Pembayaran sudah masuk. Siap diproses dapur.")
    return send(text, _buttons(order))
