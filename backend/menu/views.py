from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Sum, Q
from django.db.models.deletion import ProtectedError
from django.db.models.functions import Coalesce

from .models import Menu, Category
from .serializers import MenuSerializer, PublicMenuSerializer, CategorySerializer
from order.permissions import PublicReadStaffWrite


def _is_staff(request):
    user = getattr(request, "user", None)
    return bool(user and user.is_authenticated and user.is_staff)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
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
        # Endpoint publik: secret menu tidak boleh ikut, dan harga asli (price) tidak boleh bocor.
        top_menus = list(
            Menu.objects.select_related("category")
            .annotate(
                total_ordered=Coalesce(
                    Sum(
                        'orderitem__quantity',
                        filter=Q(orderitem__order__status='completed', orderitem__order__payment_status='paid'),
                    ),
                    0
                )
            )
            .filter(total_ordered__gt=0, is_active=True, is_secret=False)
            .order_by('-total_ordered')[:3]
        )

        if not top_menus:
            top_menus = list(
                Menu.objects.select_related("category")
                .filter(is_active=True, is_available=True, is_secret=False)[:3]
            )

        return Response(PublicMenuSerializer(top_menus, many=True).data)