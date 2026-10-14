from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Sum, Q, Count
from django.db.models.deletion import ProtectedError
from django.db.models.functions import Coalesce

from accounts.permissions import IsAdminLevel, IsStaffLevel
from .models import Menu, Category, MenuBundle
from .serializers import (
    MenuSerializer, PublicMenuSerializer, CategorySerializer,
    BundleSerializer, PublicBundleSerializer,
)
from order.permissions import PublicReadStaffWrite


def _is_staff(request):
    user = getattr(request, "user", None)
    return bool(user and user.is_authenticated and user.is_staff)


class CategoryViewSet(viewsets.ModelViewSet):
    # annotate(Count) supaya menu_count dihitung dalam 1 query, bukan 1 query per kategori
    queryset = Category.objects.annotate(menu_count=Count("menu")).order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [PublicReadStaffWrite]


class MenuViewSet(viewsets.ModelViewSet):
    queryset = Menu.objects.select_related("category").all()
    serializer_class = MenuSerializer
    permission_classes = [PublicReadStaffWrite]

    def get_queryset(self):
        qs = super().get_queryset()
        if _is_staff(self.request):
            return qs
        # Publik: secret menu dan menu nonaktif TIDAK PERNAH keluar dari API.
        return qs.filter(is_active=True, is_secret=False)

    def get_serializer_class(self):
        if self.request.method == "GET" and not _is_staff(self.request):
            return PublicMenuSerializer
        return MenuSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Menu yang masih ada di paket tidak boleh dihapus diam-diam: admin harus
        # mengeluarkannya dari paket (atau menghapus paketnya) dulu.
        in_bundles = list(
            MenuBundle.objects.filter(items__menu=instance).values_list("name", flat=True).distinct()
        )
        if in_bundles:
            return Response(
                {"detail": f"Menu ini ada di paket: {', '.join(in_bundles)}. Keluarkan dari paket atau hapus paketnya dulu.",
                 "bundles": in_bundles},
                status=status.HTTP_409_CONFLICT,
            )
        try:
            instance.delete()
            return Response(
                {"detail": "Menu berhasil dihapus.", "deactivated": False},
                status=status.HTTP_200_OK,
            )
        except ProtectedError:
            instance.is_active = False
            instance.is_available = False
            instance.save()
            return Response(
                {"detail": "Menu memiliki riwayat order, jadi dinonaktifkan (tidak dihapus).", "deactivated": True},
                status=status.HTTP_200_OK,
            )


class TopBestSellersMenuView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Endpoint publik: secret menu tidak boleh ikut, dan harga asli (price) tidak boleh bocor.
        # Tidak ada fallback: kalau belum ada order lunas, hasilnya kosong supaya
        # badge "Terlaris" tidak menempel di menu acak.
        top_menus = list(
            Menu.objects.select_related("category")
            .annotate(
                total_ordered=Coalesce(
                    Sum(
                        "orderitem__quantity",
                        filter=Q(
                            orderitem__order__status="completed",
                            orderitem__order__payment_status="paid",
                        ),
                    ),
                    0,
                )
            )
            .filter(total_ordered__gt=0, is_active=True, is_secret=False)
            .order_by("-total_ordered")[:3]
        )

        return Response(PublicMenuSerializer(top_menus, many=True).data)


class BundleViewSet(viewsets.ModelViewSet):
    """
    Menu Paket. Publik hanya membaca (angka web, tanpa paket berisi menu nonaktif/secret).
    Staf (kasir termasuk, untuk POS) membaca lengkap; menulis hanya owner/admin.
    """
    queryset = MenuBundle.objects.prefetch_related("items__menu").all()

    def _staff_view(self):
        # Halaman pelanggan (web) minta ?as=public supaya SELALU dapat harga web, walau browser-nya
        # kebetulan sedang login sebagai staf. Tanpa ini staf melihat harga POS di checkout,
        # padahal server menagih harga web (selisih seperti Rp88.000 vs Rp90.000).
        if self.request.query_params.get("as") == "public":
            return False
        return IsStaffLevel().has_permission(self.request, self)

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAdminLevel()]

    def get_serializer_class(self):
        return BundleSerializer if self._staff_view() else PublicBundleSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self._staff_view():
            return qs
        return qs.exclude(items__menu__is_active=False).exclude(items__menu__is_secret=True).distinct()