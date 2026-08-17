from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from .models import Promo
from .serializers import PromoSerializer, ValidatePromoSerializer


class PromoViewSet(viewsets.ModelViewSet):
    queryset = Promo.objects.all()
    serializer_class = PromoSerializer
    permission_classes = [IsAdminUser]  # cuma admin/owner yang bisa CRUD

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    # Endpoint publik (kasir/customer) buat cek & apply kode promo
    @action(detail=False, methods=['post'], permission_classes=[])
    def validate(self, request):
        serializer = ValidatePromoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['code'].strip().upper()
        subtotal = serializer.validated_data['subtotal']

        try:
            promo = Promo.objects.get(code=code)
        except Promo.DoesNotExist:
            return Response({"valid": False, "message": "Kode promo tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        is_valid, message = promo.check_valid(subtotal)
        if not is_valid:
            return Response({"valid": False, "message": message}, status=status.HTTP_400_BAD_REQUEST)

        discount_amount = promo.calculate_discount(subtotal)
        return Response({
            "valid": True,
            "promo_id": promo.id,
            "code": promo.code,
            "discount_amount": discount_amount,
            "message": f"Promo {promo.code} berhasil dipakai!",
        })