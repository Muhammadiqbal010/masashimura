"""
Hapus jejak IP/lokasi dari order lama (IP termasuk data pribadi; simpan seperlunya saja).

  python manage.py purge_client_info --dry-run     # lihat berapa yang akan dihapus
  python manage.py purge_client_info --days 90     # hapus jejak order yang lebih tua dari 90 hari

Hanya menghapus kolom jejak (client_ip, client_info); order, total, dan laporan tidak tersentuh.
"""
from django.core.management.base import BaseCommand

from order import housekeeping


class Command(BaseCommand):
    help = "Hapus jejak IP/lokasi pemesan dari order yang lebih tua dari N hari"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=housekeeping.TRACE_KEEP_DAYS, help="Umur minimal order (hari), bawaan 90")
        parser.add_argument("--dry-run", action="store_true", help="Hanya hitung, jangan hapus")

    def handle(self, *args, **opts):
        days = max(int(opts["days"]), 1)
        count = housekeeping.purge_client_traces(days=days, dry_run=opts["dry_run"])
        if opts["dry_run"]:
            self.stdout.write(f"{count} order lebih tua dari {days} hari masih menyimpan jejak (dry-run, tidak ada yang dihapus).")
            return
        self.stdout.write(self.style.SUCCESS(f"Jejak dihapus dari {count} order (lebih tua dari {days} hari)."))
