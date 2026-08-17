from rest_framework import serializers
from .models import Order, OrderItem, OrderPayment, LoyaltySettings, StoreSettings, PointReward
from menu.models import Menu, Category
import math

class MenuSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    category_name = serializers.CharField(source='category.name', read_only=True)

    # Write-only untuk upload
    image = serializers.ImageField(write_only=True, required=False, allow_null=True)
    # Read-only URL gambar
    image_url = serializers.SerializerMethodField(read_only=True)

    # Harga web = harga POS + 1% (dibulatkan ke atas ke kelipatan 100)
    web_price = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Menu
        fields = [
            "id",
            "name",
            "price",        # harga POS (normal)
            "web_price",    # harga web (markup 1%)
            "category",
            "category_name",
            "description",
            "image",
            "image_url",
            "is_available",
            "is_active",
        ]

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_web_price(self, obj):
        if obj.price:
            # Markup 1%, bulatkan ke atas ke kelipatan 500
            marked_up = float(obj.price) * 1.01
            rounded   = math.ceil(marked_up / 500) * 500
            return int(rounded)
        return None


class OrderItemSerializer(serializers.ModelSerializer):
    menu_name = serializers.CharField(source="menu.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "menu_name", "quantity", "price", "notes", "is_point_redemption"]


class OrderPaymentSerializer(serializers.ModelSerializer):
    method_display = serializers.CharField(source="get_method_display", read_only=True)

    class Meta:
        model = OrderPayment
        fields = ["id", "method", "method_display", "amount", "created_at"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payments = OrderPaymentSerializer(many=True, read_only=True)
    created_time = serializers.SerializerMethodField()

    amount_paid = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
        read_only=True
    )

    change_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
        read_only=True
    )

    kasir_name = serializers.CharField(read_only=True)

    cancel_reason         = serializers.CharField(read_only=True)
    cancel_reason_display = serializers.CharField(source="get_cancel_reason_display", read_only=True, default=None)
    cancel_note           = serializers.CharField(read_only=True)
    cancelled_at          = serializers.DateTimeField(read_only=True)
    cancelled_by          = serializers.CharField(read_only=True)

    # Kode promo yang dipakai (kalau ada) — biar bisa ditampilin di struk/admin
    # tanpa perlu request tambahan ke endpoint promo. default=None penting biar
    # order yang ngga pakai promo (promo=null) ngga bikin serializer error.
    promo_code = serializers.CharField(source="promo.code", read_only=True, default=None)

    def get_created_time(self, obj):
        return obj.created_at.strftime("%H:%M WIB")

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "source",
            "status",
            "payment_status",
            "payment_method",
            "is_deferred_payment",
            "customer_name",
            "customer_phone",
            "table_number",
            "subtotal",
            "discount_amount",
            "promo",
            "promo_code",
            "promo_discount_amount",
            "total_price",
            "notes",
            "created_at",
            "created_time",
            "items",
            "payments",
            "amount_paid",
            "change_amount",
            "kasir_name",
            "cancel_reason",
            "cancel_reason_display",
            "cancel_note",
            "cancelled_at",
            "cancelled_by",
        ]


class LoyaltySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltySettings
        fields = [
            "rupiah_per_point",      # rate poin masuk, diedit dari AdminPointRewards.vue
            "points_expiry_months",  # 0/3/6/12 — kapan poin hangus kalau customer ngga order
            "updated_at",
        ]
        read_only_fields = ["updated_at"]

class PointRewardSerializer(serializers.ModelSerializer):
    # Dipakai buat tabel admin — biar ngga perlu request tambahan buat nama/harga menu
    menu_name  = serializers.CharField(source='menu.name', read_only=True)
    menu_price = serializers.DecimalField(source='menu.price', max_digits=10, decimal_places=0, read_only=True)
    menu_image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PointReward
        fields = [
            'id', 'menu', 'menu_name', 'menu_price', 'menu_image_url',
            'point_cost', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_menu_image_url(self, obj):
        if obj.menu and obj.menu.image:
            return obj.menu.image.url
        return None


class StoreSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model  = StoreSettings
        fields = [
            "admin_whatsapp",
            "is_open_override",
            "closed_message",
            "operating_hours",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]