from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Sum, Q
from django.db.models.deletion import ProtectedError
from rest_framework import viewsets, status
from django.db.models.functions import Coalesce

from .models import Menu, Category
from .serializers import MenuSerializer, CategorySerializer
from order.permissions import PublicReadStaffWrite


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [PublicReadStaffWrite]


class MenuViewSet(viewsets.ModelViewSet):
    queryset = Menu.objects.select_related("category").all()
    serializer_class = MenuSerializer
    permission_classes = [PublicReadStaffWrite]

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            instance.is_active = False
            instance.is_available = False
            instance.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            instance.delete()
            return Response(
                {"detail": "Menu berhasil dihapus."},
                status=status.HTTP_204_NO_CONTENT
            )
        except ProtectedError:
            instance.is_active = False
            instance.is_available = False
            instance.save()
            return Response(
                {"detail": "Menu memiliki riwayat order, dinonaktifkan.", "deactivated": True},
                status=status.HTTP_200_OK
            )


class TopBestSellersMenuView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # 1. Ambil menu terlaris yang statusnya Aktif
        top_menus_queryset = (
            Menu.objects.annotate(
                total_ordered=Coalesce(
                    Sum(
                        'orderitem__quantity',
                        filter=Q(orderitem__order__status='completed', orderitem__order__payment_status='paid'),
                    ),
                    0
                )
            )
            .filter(total_ordered__gt=0, is_active=True)
            .order_by('-total_ordered')[:3]
        )

        # Paksa evaluasi ke dalam bentuk list untuk memastikan data benar-benar ada
        top_menus_list = list(top_menus_queryset)

        # 2. SEBAGAI PENGAMAN (FALLBACK): Jika menu terlaris yang AKTIF kosong,
        # ambil menu apa saja di database yang berstatus aktif & tersedia untuk ditampilkan di homepage
        if not top_menus_list:
            fallback_menus = Menu.objects.filter(is_active=True, is_available=True)[:3]
            serializer = MenuSerializer(fallback_menus, many=True)
            return Response(serializer.data)

        # 3. Jika data terlaris ada, kirim data terlaris
        serializer = MenuSerializer(top_menus_list, many=True)
        return Response(serializer.data)