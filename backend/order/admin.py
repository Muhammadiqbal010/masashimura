from django.contrib import admin
from .models import (
    Order,
    OrderItem,
    CustomerLoyalty,
    LoyaltySettings,
    PointReward,
    PointAdjustment,
)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("menu", "quantity", "price")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order_number",
        "customer_name",
        "customer_phone",
        "client_ip",
        "total_price",
        "payment_method",
        "payment_status",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "payment_status",
        "payment_method",
        "source",
    )

    search_fields = (
        "order_number",
        "customer_name",
        "customer_phone",
        "client_ip",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "client_ip",
        "client_info",
    )

    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "menu",
        "quantity",
        "price",
    )

    list_filter = ("menu",)


@admin.register(CustomerLoyalty)
class CustomerLoyaltyAdmin(admin.ModelAdmin):
    list_display = (
        "phone",
        "name",
        "points",
        "total_orders",
        "total_spent",
        "last_order_at",
    )

    search_fields = (
        "phone",
        "name",
    )


@admin.register(LoyaltySettings)
class LoyaltySettingsAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return not LoyaltySettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PointReward)
class PointRewardAdmin(admin.ModelAdmin):
    list_display = ("menu", "point_cost", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("menu__name",)


@admin.register(PointAdjustment)
class PointAdjustmentAdmin(admin.ModelAdmin):
    list_display = ("customer", "amount", "reason", "admin_name", "created_at")
    list_filter = ("reason",)
    search_fields = ("customer__phone", "customer__name", "note")
    readonly_fields = ("created_at",)

from .models import OrderEvent  # noqa: E402


@admin.register(OrderEvent)
class OrderEventAdmin(admin.ModelAdmin):
    """Riwayat aksi staff: hanya untuk dilihat (audit), tidak boleh diubah dari sini."""
    list_display = ("created_at", "order", "action", "actor", "channel", "note")
    list_filter = ("action", "channel")
    search_fields = ("order__order_number", "actor", "note")
    readonly_fields = ("order", "action", "actor", "channel", "note", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
