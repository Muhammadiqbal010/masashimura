"""
Webhook bot Telegram: menangani tombol (Terima / Tolak / Siap / Blokir) dan perintah
(/antrean, /ringkasan, /lacak, /percobaan, /blokir, /bukablokir, /daftarblokir).

Keamanan:
  - Telegram mengirim header X-Telegram-Bot-Api-Secret-Token yang kita set saat setWebhook
    (TELEGRAM_WEBHOOK_SECRET). Tanpa itu / salah → 403. Env kosong → webhook mati total.
  - Hanya chat di TELEGRAM_CHAT_ID (dan opsional user di TELEGRAM_ALLOWED_USER_IDS) yang dilayani.
  - Semua aksi lewat staff_actions, jadi aturan bisnisnya sama dengan Active Orders di web.
Webhook SELALU membalas 200 untuk update yang sah (error ditelan + dicatat) supaya Telegram tidak
mengulang-ulang update yang sama.
"""
import hmac
import logging

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from . import blocklist, notify, staff_actions
from . import telegram_ui as ui
from .models import Order

logger = logging.getLogger(__name__)


def _actor_name(user):
    user = user or {}
    if user.get("username"):
        return f"@{user['username']}"[:100]
    name = " ".join(p for p in (user.get("first_name"), user.get("last_name")) if p).strip()
    return (name or f"tg:{user.get('id', '?')}")[:100]


def _refresh(chat_id, message_id, order_pk, prompt_reject=False):
    order = Order.objects.filter(pk=order_pk).first()
    if not order:
        return
    if prompt_reject:
        v = notify.order_view(order)
        notify.edit_message(chat_id, message_id, ui.reject_prompt(v), ui.reject_keyboard(order.pk))
        return
    text, keyboard = notify.message_for(order)
    notify.edit_message(chat_id, message_id, text, keyboard)


def handle_callback(cq):
    cb_id = cq.get("id")
    msg = cq.get("message") or {}
    chat_id = (msg.get("chat") or {}).get("id")
    message_id = msg.get("message_id")
    user = cq.get("from") or {}

    if not notify.is_allowed_chat(chat_id) or not notify.is_allowed_user(user.get("id")):
        notify.answer_callback(cb_id, "Kamu tidak punya izin memakai tombol ini.", alert=True)
        return
    parsed = ui.parse_callback(cq.get("data"))
    if not parsed:
        notify.answer_callback(cb_id, "Tombol ini sudah tidak berlaku.")
        return

    act, order_pk, arg = parsed
    actor = _actor_name(user)
    toast = ""
    prompt_reject = False
    try:
        if act == ui.ACT_ACCEPT:
            _, changed = staff_actions.accept(order_pk, actor=actor, channel="telegram")
            toast = "✅ Diterima" if changed else "Order ini sudah diterima sebelumnya."
        elif act == ui.ACT_REJECT:
            prompt_reject = True
        elif act == ui.ACT_REJECT_DO:
            staff_actions.cancel(order_pk, reason=arg, actor=actor, channel="telegram", cancelled_by=actor)
            toast = "❌ Order dibatalkan"
        elif act == ui.ACT_READY:
            _, changed = staff_actions.set_ready(order_pk, True, actor=actor, channel="telegram")
            toast = "🍽 Ditandai siap diambil" if changed else "Sudah ditandai siap."
        elif act == ui.ACT_UNREADY:
            _, changed = staff_actions.set_ready(order_pk, False, actor=actor, channel="telegram")
            toast = "Tanda siap dicabut" if changed else "Order belum ditandai siap."
        elif act == ui.ACT_BLOCK:
            fresh, targets = blocklist.block_order(get_object_or_404(Order, pk=order_pk), actor=actor)
            if not targets:
                toast = "Tidak ada nomor/IP untuk diblokir."
            else:
                toast = "🚫 Nomor & IP diblokir" if fresh else "Sudah diblokir sebelumnya."
        elif act == ui.ACT_UNBLOCK:
            opened, targets = blocklist.unblock_order(get_object_or_404(Order, pk=order_pk), actor=actor)
            toast = "♻ Blokir dibuka" if opened else "Tidak ada blokir aktif."
        # ACT_REFRESH: hanya menyegarkan tampilan
    except staff_actions.ActionError as exc:
        toast = exc.message
    except Http404:
        notify.answer_callback(cb_id, "Order tidak ditemukan (mungkin sudah dihapus).", alert=True)
        return

    notify.answer_callback(cb_id, toast)
    _refresh(chat_id, message_id, order_pk, prompt_reject=prompt_reject)


def _block_command(cmd, arg, actor=""):
    """/blokir <nomor|ip> dan /bukablokir <nomor|ip>. Mengembalikan teks balasan."""
    target = blocklist.parse_target(arg)
    name = "bukablokir" if cmd == "/bukablokir" else "blokir"
    if not target:
        return f"Cara pakai: /{name} 081234567890  (nomor WA)  atau  /{name} 114.122.1.2  (IP)"
    kind, value = target
    label = "Nomor" if kind == blocklist.KIND_PHONE else "IP"
    if name == "blokir":
        fresh = blocklist.block(kind, value, actor=actor, reason="Manual lewat Telegram")
        if not fresh:
            return f"{label} {value} sudah ada di daftar blokir."
        effect = "ditolak total" if kind == blocklist.KIND_PHONE else "dipaksa bayar QRIS"
        return f"🚫 {label} {value} diblokir: pesanan web {effect}."
    return f"♻ Blokir {label} {value} dibuka." if blocklist.unblock(kind, value) else f"{label} {value} tidak ada di daftar blokir."


def _block_list_text():
    rows = blocklist.active_list()
    if not rows:
        return "Daftar blokir kosong."
    lines = [f"🚫 Daftar blokir ({len(rows)}):"]
    for r in rows:
        label = "WA" if r.kind == blocklist.KIND_PHONE else "IP"
        when = r.blocked_at.strftime("%d/%m")
        extra = f" · {r.order_number}" if r.order_number else ""
        lines.append(f"• {label} {r.value} · {when}{extra}")
    lines.append("Buka blokir: /bukablokir <nomor|ip>")
    return "\n".join(lines)


def handle_command(message):
    chat_id = (message.get("chat") or {}).get("id")
    user = message.get("from") or {}
    if not notify.is_allowed_chat(chat_id) or not notify.is_allowed_user(user.get("id")):
        return   # diam saja: jangan bocorkan bahwa bot ini hidup ke orang asing
    parts = (message.get("text") or "").split()
    cmd = parts[0].split("@")[0].lower()
    arg = " ".join(parts[1:])

    if cmd in ("/start", "/bantuan", "/help"):
        notify.send(ui.HELP_TEXT, chat_ids=[str(chat_id)])
    elif cmd == "/antrean":
        from . import staff_summary
        notify.send(ui.render_queue(staff_summary.queue_items()), chat_ids=[str(chat_id)])
    elif cmd == "/lacak":
        from . import trace
        notify.send(trace.lookup(arg), chat_ids=[str(chat_id)])
    elif cmd in ("/blokir", "/bukablokir"):
        notify.send(_block_command(cmd, arg, actor=_actor_name(user)), chat_ids=[str(chat_id)])
    elif cmd == "/percobaan":
        from . import trace
        notify.send(trace.attempts_text(), chat_ids=[str(chat_id)])
    elif cmd == "/daftarblokir":
        notify.send(_block_list_text(), chat_ids=[str(chat_id)])
    elif cmd == "/ringkasan":
        from . import report_format, staff_summary
        text = report_format.format_daily_report(staff_summary.build_summary(include_money=True))
        notify.send(text, chat_ids=[str(chat_id)])


def handle_update(update):
    if not isinstance(update, dict):
        return
    if update.get("callback_query"):
        handle_callback(update["callback_query"])
    elif isinstance(update.get("message"), dict) and str(update["message"].get("text") or "").startswith("/"):
        handle_command(update["message"])


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def telegram_webhook(request):
    secret = (getattr(settings, "TELEGRAM_WEBHOOK_SECRET", "") or "").strip()
    given = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not secret or not hmac.compare_digest(given.encode(), secret.encode()):
        return Response(status=403)
    try:
        handle_update(request.data)
    except Exception:   # noqa: BLE001 - jangan sampai Telegram mengulang update ini
        logger.exception("Gagal memproses update Telegram")
    return Response({"ok": True})
