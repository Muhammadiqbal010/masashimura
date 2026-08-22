from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    list_orders,
    get_order,
    create_order,
    check_loyalty_status,
    order_reports,
    order_full_report, 
    active_orders_per_day,
    DashboardStatsView,
    LoyaltySettingsView,
    LoyalCustomersView,
    AdjustPointsView,
    admin_dashboard_daily_stats,
    export_excel_report,
    export_pdf_report,
    unpaid_orders,
    pay_order,
    cancel_order,
    order_history,
    new_order_notifications,
    finance_monthly_summary,
    finance_daily_summary,
    StoreSettingsView,
    available_point_rewards,
    PointRewardViewSet,
    verify_qris_payment,
)
from .finance_excel import export_finance_excel_view
from .finance_pdf import export_finance_pdf_view

app_name = "orders"

# CRUD admin buat PointReward (mirip PromoViewSet) — /api/point-rewards/
router = DefaultRouter()
router.register(r'point-rewards', PointRewardViewSet, basename='point-rewards')

urlpatterns = [
    # ── Orders CRUD ──────────────────────────────────────────────────────────
    path("orders/",          create_order, name="order-create"),
    path("orders/list/",     list_orders,  name="order-list"),

    # PENTING: semua path statis HARUS di atas <int:pk>
    # agar Django tidak mencoba cast string ke integer dan gagal 404.

    # ── Loyalty — publik ─────────────────────────────────────────────────────
    path("orders/check_loyalty_status/", check_loyalty_status, name="check-loyalty"),

    # ── Point Rewards — publik (cek saldo + rekomendasi tukar) ───────────────
    path("orders/point-rewards/available/", available_point_rewards, name="point-rewards-available"),

    # ── Loyalty — admin ──────────────────────────────────────────────────────
    path("orders/loyalty-settings/",               LoyaltySettingsView.as_view(),  name="loyalty-settings"),
    path("orders/loyal-customers/",           LoyalCustomersView.as_view(), name="loyal-customers-admin"),
    path("orders/adjust-points/<str:phone>/", AdjustPointsView.as_view(),   name="adjust-points"),

    # ── Reports & dashboard ──────────────────────────────────────────────────
    path("orders/reports/",                        order_reports,                name="order-reports"),
    path("orders/stats/",                          DashboardStatsView.as_view(), name="dashboard-stats"),
    path("orders/admin_dashboard_daily_stats/",    admin_dashboard_daily_stats,  name="admin-daily-stats"),
    path("orders/export_excel_report/",            export_excel_report,          name="export-excel"),
    path("orders/export_pdf_report/",              export_pdf_report,            name="export-pdf"),
    path("orders/finance/monthly/", finance_monthly_summary, name="finance-monthly"),
    path("orders/finance/daily/",   finance_daily_summary,   name="finance-daily"),
    path("orders/export/finance-excel/", export_finance_excel_view, name="finance-export-excel"),
    path("orders/export/finance-pdf/", export_finance_pdf_view, name="finance-export-pdf"),
    path("orders/reports/full/",                   order_full_report,            name="order-reports-full"), 
    
    # ── Tagihan belum lunas & riwayat ─────────────────────────────────────────
    path("orders/unpaid/",   unpaid_orders, name="unpaid-orders"),
    path("orders/history/",  order_history, name="order-history"),
    path("orders/notifications/", new_order_notifications, name="order-notifications"),

    # ── Active orders (prefix berbeda) ────────────────────────────────────────
    path("active-orders/",   active_orders_per_day, name="active-orders"),

    path("orders/settings/", StoreSettingsView.as_view(), name="store-settings"),

    # ── Detail & pay — HARUS PALING BAWAH karena pakai <int:pk> ─────────────
    path("orders/<int:pk>/",         get_order,    name="order-detail"),
    path("orders/<int:pk>/pay/",            pay_order,           name="pay-order"),
    path("orders/<int:pk>/cancel/",         cancel_order,        name="cancel-order"),
    path("orders/<int:pk>/verify-payment/", verify_qris_payment, name="verify-qris-payment"),
] + router.urls

