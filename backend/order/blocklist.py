"""
Daftar blokir anti-scam: nomor WA yang ditolak total dan IP yang dipaksa bayar QRIS.

Dipakai dari tombol "🚫 Blokir" / "♻ Buka blokir" di Telegram (telegram_bot.py), perintah /blokir,
/bukablokir, /daftarblokir, dan dicek saat pelanggan membuat order web (views.create_order).

Kenapa IP tidak ditolak total: satu IP bisa dipakai banyak orang (WiFi kafe/kampus, data seluler).
Menolak total berisiko menolak pelanggan asli, jadi IP yang diblokir hanya dipaksa QRIS.
Blokir IP juga kedaluwarsa sendiri setelah IP_BLOCK_DAYS karena IP sering berganti pemilik.
"""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from . import client_info as ci
from . import events, guards
from .models import BlockedContact

IP_BLOCK_DAYS = 90
KIND_PHONE = "phone"
KIND_IP = "ip"


def parse_target(raw):
    """'0812-3456-7890' -> ('phone', '081234567890'); '114.122.1.2' -> ('ip', '114.122.1.2'); lainnya None."""
    text = str(raw or "").strip()
    if not text:
        return None
    ip = ci._valid_ip(text) if (":" in text or text.count(".") == 3) else None
    if ip:
        return KIND_IP, ip
    phone = guards.normalize_phone(text)
    if phone and phone.isdigit() and 9 <= len(phone) <= 15:
        return KIND_PHONE, phone
    return None


def _ip_cutoff(now=None):
    return (now or timezone.now()) - timedelta(days=IP_BLOCK_DAYS)


def is_phone_blocked(phone):
    phone = guards.normalize_phone(phone)
    return bool(phone) and BlockedContact.objects.filter(kind=KIND_PHONE, value=phone, is_active=True).exists()


def is_ip_blocked(ip):
    ip = str(ip or "").strip()
    return bool(ip) and BlockedContact.objects.filter(
        kind=KIND_IP, value=ip, is_active=True, blocked_at__gte=_ip_cutoff(),
    ).exists()


def block(kind, value, actor="", reason="", order_number=""):
    """Blokir satu nomor/IP. Mengembalikan True kalau sebelumnya belum aktif diblokir."""
    value = str(value or "").strip()
    if kind not in (KIND_PHONE, KIND_IP) or not value:
        return False
    now = timezone.now()
    with transaction.atomic():
        obj, created = BlockedContact.objects.select_for_update().get_or_create(
            kind=kind, value=value,
            defaults={"reason": reason[:255], "blocked_by": actor[:100], "order_number": order_number[:40], "blocked_at": now},
        )
        if created:
            return True
        was_active = obj.is_active and (kind == KIND_PHONE or obj.blocked_at >= _ip_cutoff(now))
        obj.is_active = True
        obj.unblocked_at = None
        obj.blocked_at = now
        obj.reason = reason[:255] or obj.reason
        obj.blocked_by = actor[:100] or obj.blocked_by
        obj.order_number = order_number[:40] or obj.order_number
        obj.save()
        return not was_active


def unblock(kind, value):
    """Buka blokir. Mengembalikan True kalau memang ada yang dibuka."""
    return bool(
        BlockedContact.objects.filter(kind=kind, value=str(value or "").strip(), is_active=True)
        .update(is_active=False, unblocked_at=timezone.now())
    )


def block_order(order, actor="", channel="telegram"):
    """
    Blokir nomor WA dan IP milik order ini. Mengembalikan (jumlah_baru, nomor_atau_ip_terblokir[list]).
    Order itu sendiri TIDAK dibatalkan (kasir memutuskan lewat tombol Tolak).
    """
    targets = []
    if order.customer_phone:
        targets.append((KIND_PHONE, order.customer_phone))
    if order.client_ip:
        targets.append((KIND_IP, order.client_ip))
    fresh = 0
    for kind, value in targets:
        if block(kind, value, actor=actor, reason=f"Order {order.order_number}", order_number=order.order_number):
            fresh += 1
    if targets:
        events.record(order, "blocked", actor=actor, channel=channel,
                      note=", ".join(f"{k}:{v}" for k, v in targets)[:250])
    return fresh, targets


def unblock_order(order, actor="", channel="telegram"):
    opened = 0
    targets = []
    if order.customer_phone:
        targets.append((KIND_PHONE, order.customer_phone))
    if order.client_ip:
        targets.append((KIND_IP, order.client_ip))
    for kind, value in targets:
        if unblock(kind, value):
            opened += 1
    if opened:
        events.record(order, "unblocked", actor=actor, channel=channel)
    return opened, targets


def order_status(order):
    """{'phone': bool, 'ip': bool} untuk tampilan tombol di Telegram."""
    return {
        "phone": bool(order.customer_phone) and is_phone_blocked(order.customer_phone),
        "ip": bool(order.client_ip) and is_ip_blocked(order.client_ip),
    }


def active_list(limit=30):
    rows = list(BlockedContact.objects.filter(is_active=True).order_by("-blocked_at")[:200])
    cutoff = _ip_cutoff()
    rows = [r for r in rows if r.kind == KIND_PHONE or r.blocked_at >= cutoff]
    return rows[:limit]


def expire_old_ip_blocks():
    """Bersih-bersih: tandai blokir IP yang sudah lewat masa berlakunya sebagai tidak aktif."""
    return BlockedContact.objects.filter(
        kind=KIND_IP, is_active=True, blocked_at__lt=_ip_cutoff(),
    ).update(is_active=False, unblocked_at=timezone.now())
