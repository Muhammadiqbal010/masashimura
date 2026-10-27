"""
Pengaman order web (anti-iseng) dan format nomor HP.

- Batas porsi: tiap menu maks WEB_MAX_PER_ITEM, seluruh pesanan maks WEB_MAX_PORTIONS.
- Cash di atas WEB_CASH_MAX wajib bayar online (QRIS).
- Order web bayar di toko harus DITERIMA kasir dalam CONFIRM_TIMEOUT_MINUTES, kalau tidak dibatalkan otomatis.
"""
import re
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

WEB_MAX_PER_ITEM = 10
WEB_MAX_PORTIONS = 30
WEB_CASH_MAX = Decimal("150000")
CONFIRM_TIMEOUT_MINUTES = 15
REMINDER_LEAD_MINUTES = 5   # pengingat Telegram dikirim saat sisa waktu terima tinggal sekian menit


# ── Nomor HP ────────────────────────────────────────────────────────────────

def normalize_phone(raw):
    """
    Seragamkan nomor HP Indonesia ke format lokal 08xxx.
      "+62 812-3456-7890" / "6281234567890" / "81234567890" → "081234567890"
    Nomor yang bukan pola itu (mis. sudah 08xxx, atau kosong) hanya dibersihkan dari spasi dan tanda baca.
    """
    s = str(raw or "").strip()
    if not s:
        return ""
    digits = re.sub(r"\D", "", s)
    if not digits:
        return ""
    if s.startswith("+62") or digits.startswith("62"):
        digits = "0" + digits[2:]
    elif digits.startswith("8"):
        digits = "0" + digits
    return digits


# ── Batas porsi & nominal cash ──────────────────────────────────────────────

def web_portion_error(portions_by_menu, total_portions):
    """Pesan error kalau jumlah porsi order web melewati batas, atau None."""
    for qty in portions_by_menu.values():
        if qty > WEB_MAX_PER_ITEM:
            return f"Maksimal {WEB_MAX_PER_ITEM} porsi per menu untuk pesanan online."
    if total_portions > WEB_MAX_PORTIONS:
        return f"Maksimal {WEB_MAX_PORTIONS} porsi per pesanan online. Untuk pesanan besar, hubungi toko."
    return None


def web_cash_error(total_price):
    if Decimal(total_price) > WEB_CASH_MAX:
        return (
            f"Pesanan di atas Rp{int(WEB_CASH_MAX):,}".replace(",", ".")
            + " harus dibayar online (QRIS). Pilih QRIS atau kurangi pesanan."
        )
    return None


# ── Konfirmasi kasir & pembatalan otomatis ──────────────────────────────────

def confirm_deadline(order):
    return order.created_at + timedelta(minutes=CONFIRM_TIMEOUT_MINUTES)


def accept_now(order):
    """Tandai order sudah diterima kasir (di memori; pemanggil yang menyimpan)."""
    if getattr(order, "awaiting_confirmation", False):
        order.awaiting_confirmation = False
        order.accepted_at = timezone.now()
        return True
    return False


def _notify_later(func_name, order_pk):
    """Kirim notifikasi Telegram SETELAH transaksi commit; error Telegram tidak boleh merusak apa pun."""
    def _go():
        try:
            from . import notify
            getattr(notify, func_name)(order_pk)
        except Exception:   # noqa: BLE001
            import logging
            logging.getLogger(__name__).exception("Notifikasi %s gagal untuk order %s", func_name, order_pk)
    transaction.on_commit(_go)


def expire_unconfirmed_orders(now=None):
    """
    Batalkan order web bayar-di-toko yang tidak diterima kasir dalam CONFIRM_TIMEOUT_MINUTES.
    Dipanggil setiap kali staf memuat daftar order dan oleh cron (lihat process_unconfirmed).
    Setiap pembatalan dicatat di riwayat order dan dikabarkan ke Telegram. Mengembalikan jumlah yang dibatalkan.
    """
    from . import events
    from .models import Order

    now = now or timezone.now()
    cutoff = now - timedelta(minutes=CONFIRM_TIMEOUT_MINUTES)
    ids = list(
        Order.objects.filter(
            source="web", awaiting_confirmation=True, status="pending", created_at__lt=cutoff,
        ).values_list("pk", flat=True)[:50]
    )
    cancelled = 0
    for pk in ids:
        with transaction.atomic():
            order = Order.objects.select_for_update().filter(pk=pk, awaiting_confirmation=True).first()
            # Sudah diterima / dibayar / dibatalkan di antara dua query → lewati.
            if not order or order.status != "pending" or order.payment_status != "pending":
                continue
            order._previous_status = order.status
            order.status = "cancelled"
            order.payment_status = "void"
            order.awaiting_confirmation = False
            order.cancel_reason = "other"
            order.cancel_note = f"Tidak diterima kasir dalam {CONFIRM_TIMEOUT_MINUTES} menit"
            order.cancelled_at = now
            order.cancelled_by = "sistem"
            order.save()
            events.record(order, "auto_cancelled", actor="sistem", channel="system", note=order.cancel_note)
            _notify_later("order_auto_cancelled", order.pk)
            cancelled += 1
    return cancelled


def remind_unconfirmed_orders(now=None):
    """
    Kirim SATU pengingat Telegram per order yang sisa waktu terimanya tinggal REMINDER_LEAD_MINUTES.
    Dijamin tidak dobel: pengingat dicatat sebagai OrderEvent 'reminded' di dalam kunci baris order.
    Mengembalikan jumlah pengingat yang dikirim.
    """
    from . import events
    from .models import Order

    now = now or timezone.now()
    expire_cutoff = now - timedelta(minutes=CONFIRM_TIMEOUT_MINUTES)
    remind_cutoff = now - timedelta(minutes=CONFIRM_TIMEOUT_MINUTES - REMINDER_LEAD_MINUTES)
    ids = list(
        Order.objects.filter(
            source="web", awaiting_confirmation=True, status="pending",
            created_at__lte=remind_cutoff, created_at__gte=expire_cutoff,
        ).exclude(events__action="reminded").values_list("pk", flat=True)[:50]
    )
    sent = 0
    for pk in ids:
        with transaction.atomic():
            order = Order.objects.select_for_update().filter(pk=pk, awaiting_confirmation=True, status="pending").first()
            if not order or order.events.filter(action="reminded").exists():
                continue
            events.record(order, "reminded", actor="sistem", channel="system",
                          note=f"Sisa waktu terima ±{REMINDER_LEAD_MINUTES} menit")
            _notify_later("order_reminder", order.pk)
            sent += 1
    return sent


def process_unconfirmed(now=None):
    """
    Satu pintu untuk pekerjaan berkala order yang belum diterima: batalkan yang kedaluwarsa,
    lalu ingatkan yang hampir kedaluwarsa. Dipanggil dari endpoint daftar order (tidak ada proses
    latar di Vercel) dan dari cron. Aman dipanggil berkali-kali.
    """
    now = now or timezone.now()
    return {"cancelled": expire_unconfirmed_orders(now), "reminded": remind_unconfirmed_orders(now)}
