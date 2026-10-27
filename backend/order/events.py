"""Pencatat riwayat aksi per order (model OrderEvent) dan bentuk timeline-nya untuk API."""
import logging

from django.utils import timezone

from .models import ORDER_EVENT_ACTION_CHOICES, OrderEvent

logger = logging.getLogger(__name__)

ACTION_LABELS = dict(ORDER_EVENT_ACTION_CHOICES)
CHANNEL_LABELS = {"staff": "Admin", "telegram": "Telegram", "system": "Sistem"}


def record(order, action, actor="", channel="staff", note=""):
    """
    Catat satu kejadian. Tidak pernah melempar error ke pemanggil: log yang gagal tidak boleh
    menggagalkan aksi staff. Pakai savepoint supaya error DB di sini tidak merusak transaksi luar.
    """
    from django.db import transaction

    try:
        with transaction.atomic():
            return OrderEvent.objects.create(
                order=order,
                action=action,
                actor=(actor or "")[:100],
                channel=channel,
                note=(note or "")[:255],
                created_at=timezone.now(),
            )
    except Exception:   # noqa: BLE001 - audit log bersifat pelengkap
        logger.exception("Gagal mencatat event %s untuk order %s", action, getattr(order, "pk", "?"))
        return None


def timeline(order):
    """Daftar event terurut waktu, siap di-JSON-kan."""
    return [
        {
            "id": e.pk,
            "action": e.action,
            "label": ACTION_LABELS.get(e.action, e.action),
            "actor": e.actor,
            "channel": e.channel,
            "channel_label": CHANNEL_LABELS.get(e.channel, e.channel),
            "note": e.note,
            "created_at": e.created_at,
        }
        for e in order.events.all()
    ]


def actor_from_request(request):
    """
    Nama pelaku untuk log. Utamakan nama kasir yang diketik di UI (kasir_name), lalu nama akun.
    Tidak pernah memakai data sensitif selain nama tampilan.
    """
    name = ""
    data = getattr(request, "data", None)
    if hasattr(data, "get"):
        name = str(data.get("kasir_name") or "").strip()
    if not name:
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            name = (user.get_full_name() or user.get_username() or "").strip()
    return name[:100]
