"""Endpoint khusus alur staff: ringkasan, antrean prioritas, dan pekerjaan berkala (cron)."""
import hmac
import logging

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from accounts.permissions import IsAdminLevel, IsStaffLevel

from . import guards, housekeeping, scam_report, staff_summary

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsStaffLevel])
def staff_summary_view(request):
    """
    GET /api/orders/staff-summary/?date=YYYY-MM-DD   (default hari ini WIB)

    Isi: antrean prioritas, ringkasan hari, jam sibuk, kecepatan layanan, aksi per staff, menu terlaris.
    Angka uang (omzet, nominal tagihan) HANYA untuk owner/admin; kasir menerimanya sebagai null.
    """
    raw = request.query_params.get("date")
    day = parse_date(raw) if raw else None
    if raw and not day:
        return Response({"detail": "Format tanggal harus YYYY-MM-DD."}, status=400)
    money = IsAdminLevel().has_permission(request, None)

    guards.process_unconfirmed()   # data antrean harus sesudah pembatalan/pengingat otomatis
    data = staff_summary.build_summary(day=day, include_money=money)
    if data["is_today"]:
        items = staff_summary.queue_items()
        if not money:
            for it in items:
                it.pop("amount", None)
        data["queue_items"] = items[:30]
    return Response(data)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def cron_run(request):
    """
    Dipanggil Vercel Cron (header `Authorization: Bearer <CRON_SECRET>`).
      ?job=tick          batalkan otomatis + kirim pengingat order belum diterima (default)
      ?job=daily_report  kirim ringkasan harian ke Telegram; sekalian bersih-bersih jejak IP lama
                         dan (tiap hari Senin) laporan anti-scam mingguan
      ?job=housekeeping  hanya bersih-bersih: hapus jejak IP order lama (90 hari) + tutup blokir IP kedaluwarsa
      ?job=weekly_report kirim laporan anti-scam mingguan sekarang
    CRON_SECRET kosong = endpoint mati.
    """
    secret = (getattr(settings, "CRON_SECRET", "") or "").strip()
    header = request.headers.get("Authorization", "")
    expected = f"Bearer {secret}"
    if not secret or not hmac.compare_digest(header.encode(), expected.encode()):
        return Response(status=403)

    job = request.query_params.get("job", "tick")
    if job == "tick":
        return Response({"job": job, **guards.process_unconfirmed()})
    if job == "daily_report":
        sent = staff_summary.send_daily_report()
        extra = {}
        try:   # pekerjaan tambahan tidak boleh menggagalkan laporan harian
            extra["housekeeping"] = housekeeping.run_daily()
            if timezone.localtime(timezone.now()).weekday() == 0:   # Senin (WIB)
                extra["weekly_report_sent"] = bool(scam_report.send())
        except Exception:   # noqa: BLE001
            logger.exception("Pekerjaan tambahan cron daily_report gagal")
            extra["extra_error"] = True
        return Response({"job": job, "sent": bool(sent), **extra})
    if job == "housekeeping":
        return Response({"job": job, **housekeeping.run_daily()})
    if job == "weekly_report":
        return Response({"job": job, "sent": bool(scam_report.send())})
    return Response({"detail": "job tidak dikenal"}, status=400)
