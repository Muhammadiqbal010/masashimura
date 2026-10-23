import time
from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers
from .models import Order, OrderItem, OrderPayment, LoyaltySettings, StoreSettings, PointReward, WIB
from menu.models import Menu, Category
from .pricing import web_price as calc_web_price

# Order yang belum siap tapi umurnya sudah lewat ini dianggap "terlupa ditandai",
# bukan telat betulan (mis. order kemarin yang tidak pernah ditekan "Siap").
STALE_ORDER_MINUTES = 6 * 60

_late_cache = {"value": 20, "at": 0.0}


def late_minutes_setting():
    """Batas telat (menit). Di-cache 15 detik supaya list order tidak query settings per baris."""
    now = time.monotonic()
    if now - _late_cache["at"] > 15:
        row = StoreSettings.objects.filter(pk=1).values_list("order_late_minutes", flat=True).first()
        _late_cache["value"] = row or 20
        _late_cache["at"] = now
    return _late_cache["value"]


def reset_late_minutes_cache():
    _late_cache["at"] = 0.0


class MenuSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    category_name = serializers.CharField(source='category.name', read_only=True)

    # Write-only untuk upload
    image = serializers.ImageField(write_only=True, required=False, allow_null=True)
    # Read-only URL gambar
    image_url = serializers.SerializerMethodField(read_only=True)

    # Harga web = harga POS + 1% (dibulatkan ke atas ke kelipatan 500)
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
            return int(calc_web_price(obj.price))
        return None


class OrderItemSerializer(serializers.ModelSerializer):
    menu_name = serializers.CharField(source="menu.name", read_only=True)
    menu_id   = serializers.IntegerField(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id", "menu_id", "menu_name", "quantity", "price", "notes", "selected_options",
            "is_point_redemption", "bundle_name", "added_at", "added_qty",
        ]


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

    # ── Status dapur ──────────────────────────────────────────────
    is_ready     = serializers.SerializerMethodField()
    is_late      = serializers.SerializerMethodField()
    wait_minutes = serializers.SerializerMethodField()
    late_after_minutes = serializers.SerializerMethodField()

    # ── Penanda tambahan item ─────────────────────────────────────
    has_additions = serializers.SerializerMethodField()

    # ── Uang: kurang bayar / kembalian karena menu habis ──────────
    amount_to_pay_now = serializers.SerializerMethodField()
    refund_pending    = serializers.SerializerMethodField()

    def _is_open_order(self, obj):
        return obj.status != "cancelled" and obj.payment_status != "void"

    def get_is_ready(self, obj):
        return obj.ready_at is not None

    def get_wait_minutes(self, obj):
        if obj.ready_at is not None or not self._is_open_order(obj):
            return None
        return max(int((timezone.now() - obj.created_at).total_seconds() // 60), 0)

    def get_is_late(self, obj):
        waited = self.get_wait_minutes(obj)
        if waited is None:
            return False
        return late_minutes_setting() <= waited <= STALE_ORDER_MINUTES

    def get_late_after_minutes(self, obj):
        return late_minutes_setting()

    def get_has_additions(self, obj):
        return any(i.added_at for i in obj.items.all())

    def get_amount_to_pay_now(self, obj):
        # Yang masih harus dibayar pelanggan sekarang. Order lunas = 0.
        if obj.payment_status in ("unpaid", "pending") and obj.status != "cancelled":
            return int(obj.total_price)
        return 0

    def get_refund_pending(self, obj):
        return bool(obj.refund_due and obj.refund_due > 0 and obj.refunded_at is None)

    def get_created_time(self, obj):
        # Konversi ke WIB dulu — created_at dari DB berupa UTC; tanpa ini jamnya
        # geser 7 jam padahal diberi label "WIB".
        return timezone.localtime(obj.created_at, WIB).strftime("%H:%M WIB")

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
            "entered_at",
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
            "ready_at",
            "is_ready",
            "is_late",
            "wait_minutes",
            "late_after_minutes",
            "has_additions",
            "unavailable_items",
            "refund_due",
            "refunded_at",
            "refunded_by",
            "refund_pending",
            "amount_to_pay_now",
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
            "crowd_indicator_enabled",
            "monthly_revenue_target",
            "order_late_minutes",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def validate_order_late_minutes(self, value):
        if value < 1 or value > 240:
            raise serializers.ValidationError("Batas telat harus 1-240 menit.")
        return value

    def validate_monthly_revenue_target(self, value):
        # 0 dan kosong sama-sama berarti "belum ada target".
        if not value:
            return None
        if value > 100_000_000_000:
            raise serializers.ValidationError("Target terlalu besar. Maksimal Rp 100.000.000.000.")
        return value
