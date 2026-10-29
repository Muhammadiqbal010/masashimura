"""
Bersih-bersih berkala data anti-scam (dipanggil cron harian dan perintah purge_client_info).

- Jejak IP/lokasi di order lama dihapus: IP termasuk data pribadi, simpan seperlunya saja.
  Order, total, dan laporan tidak tersentuh.
- Blokir IP yang sudah lewat masa berlakunya dinonaktifkan (lihat blocklist.IP_BLOCK_DAYS).
- Catatan percobaan order dari nomor/IP terblokir yang sangat lama dihapus (blocklist.ATTEMPT_KEEP_DAYS).
"""
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from . import blocklist
from .models import Order

TRACE_KEEP_DAYS = 90


def purge_client_traces(days=TRACE_KEEP_DAYS, dry_run=False):
    """Hapus client_ip/client_info dari order yang lebih tua dari `days`. Mengembalikan jumlah order terdampak."""
    days = max(int(days), 1)
    cutoff = timezone.now() - timedelta(days=days)
    qs = Order.objects.filter(created_at__lt=cutoff).filter(Q(client_ip__isnull=False) | ~Q(client_info={}))
    count = qs.count()
    if not dry_run and count:
        qs.update(client_ip=None, client_info={})
    return count


def run_daily(days=TRACE_KEEP_DAYS):
    """Satu pintu untuk cron: hapus jejak lama + tutup blokir IP kedaluwarsa. Aman dipanggil berkali-kali."""
    return {
        "purged_orders": purge_client_traces(days=days),
        "expired_ip_blocks": blocklist.expire_old_ip_blocks(),
        "purged_attempts": blocklist.purge_old_attempts(),
    }
