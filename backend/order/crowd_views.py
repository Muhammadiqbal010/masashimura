from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminLevel, IsStaffLevel

from . import crowd
from .models import StoreSettings


class CrowdStatusView(APIView):
    """
    GET /orders/crowd/ — publik. Dipakai badge di halaman Menu pelanggan.
    Tidak membocorkan angka: hanya level, mode, dan apakah badge tampil.
    """
    permission_classes = [AllowAny]
    authentication_classes = []   # publik: token usang di browser tidak boleh bikin 401

    def get(self, request):
        data = crowd.crowd_status(StoreSettings.get())
        response = Response(data)
        # Cache singkat di CDN/browser meringankan serverless; tidak jadi sumber kebenaran.
        response["Cache-Control"] = "public, max-age=30"
        return response


class CrowdManualView(APIView):
    """
    Kontrol cepat untuk kasir/admin/owner.

    GET  /orders/crowd/manual/  -> status lengkap (termasuk level otomatis & angka pesanan)
    POST /orders/crowd/manual/  -> {"level": "santai|sedang|ramai|auto",
                                    "duration_minutes": 60}        atau
                                   {"level": "ramai", "until": "20:00"}
    """
    permission_classes = [IsStaffLevel]

    def get(self, request):
        return Response(crowd.crowd_status(StoreSettings.get(), detail=True))

    def post(self, request):
        store = StoreSettings.get()
        error = crowd.set_manual(
            store,
            level=request.data.get("level"),
            minutes=request.data.get("duration_minutes"),
            until=request.data.get("until"),
        )
        if error:
            return Response({"detail": error}, status=400)
        return Response(crowd.crowd_status(store, detail=True))


class BusyHoursView(APIView):
    """GET /orders/busy-hours/?weeks=8 — Peta Jam Sibuk, hanya owner/admin."""
    permission_classes = [IsAdminLevel]

    def get(self, request):
        try:
            weeks = int(request.query_params.get("weeks", crowd.HISTORY_WEEKS))
        except (TypeError, ValueError):
            weeks = crowd.HISTORY_WEEKS
        return Response(crowd.busy_hours(StoreSettings.get(), weeks=weeks))
