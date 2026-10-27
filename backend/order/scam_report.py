"""
Laporan anti-scam mingguan ke Telegram: apakah aturan (wajib QRIS, blokir, tanda) sudah efektif?

Hanya angka murah (beberapa query agregat), jadi aman dijalankan di serverless. Dikirim oleh cron
(lihat staff_views.cron_run): otomatis tiap Senin lewat job daily_report, atau manual lewat job=weekly_report.
"""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.utils import timezone

from . import blocklist
from . import telegram_ui as ui
from .models import BlockedContact, Order

WINDOW_DAYS = 7


def _auto_cancelled(since, until):
    return Order.objects.filter(
        source="web", events__action="auto_cancelled", events__created_at__gte=since, events__created_at__lt=until,
    ).distinct()


def build(now=None):
    now = now or timezone.now()
    since = now - timedelta(days=WINDOW_DAYS)
    before = since - timedelta(days=WINDOW_DAYS)

    web = Order.objects.filter(source="web", created_at__gte=since, created_at__lt=now)
    total = web.count()
    cash = web.filter(payment_method="cash").count()
    gateway = web.filter(payment_method="gateway").count()

    cancelled = _auto_cancelled(since, now)
    cancelled_n = cancelled.count()
    cancelled_rp = cancelled.aggregate(s=Sum("total_price"))["s"] or Decimal("0")
    cancelled_prev = _auto_cancelled(before, since).count()

    new_blocks = BlockedContact.objects.filter(blocked_at__gte=since).count()
    active_blocks = len(blocklist.active_list(limit=500))

    top_ips = list(
        web.exclude(client_ip__isnull=True).values("client_ip")
        .annotate(n=Count("id"), p=Count("customer_phone", distinct=True))
        .filter(n__gte=3).order_by("-n")[:3]
    )
    top_phones = list(
        cancelled.exclude(customer_phone="").values("customer_phone")
        .annotate(n=Count("id", distinct=True)).filter(n__gte=2).order_by("-n")[:3]
    )

    d0 = timezone.localtime(since).strftime("%d/%m")
    d1 = timezone.localtime(now).strftime("%d/%m")
    lines = [
        f"🛡️ Laporan anti-scam mingguan ({d0}–{d1})",
        "",
        f"Pesanan web: {total} (cash {cash}, QRIS {gateway})",
        f"Batal otomatis (tidak diterima kasir): {cancelled_n}"
        + (f" · ±{ui.rp(cancelled_rp)} tidak jadi masuk antrean" if cancelled_n else ""),
        f"Minggu sebelumnya: {cancelled_prev}"
        + (" → turun, aturan mulai efektif 👍" if cancelled_n < cancelled_prev else
           (" → naik, cek /lacak untuk pola barunya" if cancelled_n > cancelled_prev else "")),
        f"Diblokir minggu ini: {new_blocks} baru · {active_blocks} aktif",
    ]
    if top_ips:
        lines += ["", "IP paling sering memesan:"]
        lines += [f"• {r['client_ip']} — {r['n']} pesanan, {r['p']} nomor WA" for r in top_ips]
    if top_phones:
        lines += ["", "Nomor yang pesanannya berulang batal otomatis:"]
        lines += [f"• {r['customer_phone']} — {r['n']}×" for r in top_phones]
    if top_ips or top_phones:
        lines += ["", "Periksa dengan /lacak <IP>, blokir dengan /blokir <nomor|ip>."]
    elif total:
        lines += ["", "Tidak ada pola mencurigakan minggu ini ✅"]
    return "\n".join(lines)


def send(now=None):
    from . import notify

    return notify.send_report(build(now))
