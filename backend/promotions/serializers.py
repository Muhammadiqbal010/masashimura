from rest_framework import serializers
from .models import Promo


class PromoSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    remaining_usage = serializers.SerializerMethodField()

    class Meta:
        model = Promo
        fields = [
            'id', 'code', 'description', 'discount_type', 'discount_value',
            'max_discount_amount', 'min_purchase', 'max_usage', 'used_count',
            'remaining_usage', 'valid_from', 'valid_until', 'is_active',
            'created_by_name', 'created_at',
        ]
        read_only_fields = ['used_count', 'created_at']

    def get_remaining_usage(self, obj):
        if obj.max_usage is None:
            return None
        return max(obj.max_usage - obj.used_count, 0)

    def validate_code(self, value):
        return value.strip().upper()


class ValidatePromoSerializer(serializers.Serializer):
    code = serializers.CharField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)