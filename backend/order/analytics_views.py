from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminLevel

from . import analytics, briefing, effectiveness, simulation
from .models import StoreSettings


class _AnalyticsView(APIView):
    """Dasar: hanya owner/admin, parameter periode sama dengan /orders/reports/full/."""
    permission_classes = [IsAdminLevel]
    compute = None

    def get(self, request):
        return Response(type(self).compute(request.query_params))


class MenuPerformanceView(_AnalyticsView):
    """GET /orders/analytics/menu-performance/"""
    compute = staticmethod(analytics.menu_performance)


class MenuPairsView(_AnalyticsView):
    """GET /orders/analytics/menu-pairs/?min_count=2"""
    compute = staticmethod(analytics.menu_pairs)


class ChannelsView(_AnalyticsView):
    """GET /orders/analytics/channels/"""
    compute = staticmethod(analytics.channels)


class PromoEffectivenessView(_AnalyticsView):
    """GET /orders/analytics/promo-effectiveness/ — dipakai halaman Kelola Promo."""
    compute = staticmethod(effectiveness.promo_effectiveness)


class PointEffectivenessView(_AnalyticsView):
    """GET /orders/analytics/point-effectiveness/ — dipakai halaman Kelola Reward Poin."""
    compute = staticmethod(effectiveness.point_effectiveness)


class SimulationView(_AnalyticsView):
    """GET /orders/analytics/simulation/ — data dasar tab Simulasi di bagian Prediksi (Dashboard)."""
    compute = staticmethod(simulation.simulation)


class MenuTomorrowView(APIView):
    """GET /orders/analytics/menu-tomorrow/ — perkiraan 5 menu teratas besok (pola historis)."""
    permission_classes = [IsAdminLevel]

    def get(self, request):
        return Response(analytics.menu_tomorrow(StoreSettings.get()))


class BriefingView(APIView):
    """
    GET /orders/briefing/ — Strip Briefing Dashboard (selalu hari ini, tidak ikut filter tanggal).
    Bagian yang gagal dihitung bernilai null dan tercatat di `errors`.
    """
    permission_classes = [IsAdminLevel]

    def get(self, request):
        response = Response(briefing.briefing(StoreSettings.get()))
        response["Cache-Control"] = "no-store"
        return response

