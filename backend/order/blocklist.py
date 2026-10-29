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
from .models import BlockedAttempt, BlockedContact

IP_BLOCK_DAYS = 90
ATTEMPT_ALERT_GAP_MINUTES = 30   # alert Telegram untuk nomor/IP yang sama paling sering sekali per jeda ini
ATTEMPT_KEEP_DAYS = 180          # percobaan lebih tua dari ini boleh dibersihkan
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


# ── Percobaan order dari nomor/IP yang diblokir ─────────────────────────────

def record_attempt(kind, value, phone="", name="", ip=None, info=None):
    """
    Catat satu percobaan order web dari nomor/IP yang sedang diblokir.
    Mengembalikan (attempt, kirim_alert): kirim_alert True kalau sudah lewat ATTEMPT_ALERT_GAP_MINUTES
    sejak percobaan sebelumnya dari nomor/IP yang sama (supaya Telegram tidak banjir saat orang yang sama
    menekan tombol pesan berulang-ulang). Tidak pernah melempar error ke pemanggil.
    """
    value = str(value or "").strip()
    if kind not in (KIND_PHONE, KIND_IP) or not value:
        return None, False
    try:
        gap_from = timezone.now() - timedelta(minutes=ATTEMPT_ALERT_GAP_MINUTES)
        recent = BlockedAttempt.objects.filter(kind=kind, value=value, created_at__gte=gap_from).exists()
        attempt = BlockedAttempt.objects.create(
            kind=kind, value=value[:64], phone=str(phone or "")[:20], name=str(name or "")[:100],
            client_ip=ip or None, client_info=dict(info or {}),
        )
        return attempt, not recent
    except Exception:   # noqa: BLE001 - mencatat percobaan tidak boleh menggagalkan respons ke pelanggan
        import logging
        logging.getLogger(__name__).exception("Gagal mencatat percobaan order terblokir")
        return None, False


def attempt_counts(keys):
    """{(kind, value): (jumlah, terakhir)} untuk daftar kunci (kind, value) — 1 query per jenis."""
    from django.db.models import Count, Max

    out = {}
    for kind in (KIND_PHONE, KIND_IP):
        values = {v for k, v in keys if k == kind}
        if not values:
            continue
        for r in (BlockedAttempt.objects.filter(kind=kind, value__in=values).order_by()
                  .values("value").annotate(n=Count("id"), last=Max("created_at"))):
            out[(kind, r["value"])] = (r["n"], r["last"])
    return out


def purge_old_attempts(now=None):
    """Hapus catatan percobaan yang sudah lewat ATTEMPT_KEEP_DAYS. Mengembalikan jumlah yang dihapus."""
    cutoff = (now or timezone.now()) - timedelta(days=ATTEMPT_KEEP_DAYS)
    return BlockedAttempt.objects.filter(created_at__lt=cutoff).delete()[0]
