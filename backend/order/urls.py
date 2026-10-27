from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    # Orders
    list_orders,
    get_order,
    create_order,
    pay_order,
    accept_order,
    cancel_order,
    unpaid_orders,
    order_history,
    new_order_notifications,
    active_orders_per_day,
    add_order_item,
    order_item_detail,
    split_order,
    mark_order_ready,
    mark_items_unavailable,
    confirm_refund,
    pending_refunds,
    orders_affected_by_menu,
    # Loyalty & point rewards
    check_loyalty_status,
    available_point_rewards,
    member_verify,
    LoyalCustomerPinView,
    LoyaltySettingsView,
    LoyalCustomersView,
    LoyalCustomerDetailView,
    LoyalCustomersBulkDeleteView,
    AdjustPointsView,
    PointRewardViewSet,
    # Reports, dashboard & finance
    order_reports,
    order_full_report,
    DashboardStatsView,
    admin_dashboard_daily_stats,
    export_excel_report,
    export_pdf_report,
    finance_monthly_summary,
    finance_daily_summary,
    # Settings
    StoreSettingsView,
)
from .analytics_views import (
    MenuPerformanceView, MenuPairsView, ChannelsView, MenuTomorrowView, BriefingView,
    PromoEffectivenessView, PointEffectivenessView, SimulationView,
)
from .crowd_views import CrowdStatusView, CrowdManualView, BusyHoursView
from .finance_excel import export_finance_excel_view
from .finance_pdf import export_finance_pdf_view

app_name = "orders"

# CRUD admin PointReward (mirip PromoViewSet) -> <prefix>/point-rewards/
router = DefaultRouter()
router.register(r"point-rewards", PointRewardViewSet, basename="point-rewards")

urlpatterns = [
    # ── Orders: create & list ────────────────────────────────────────────────
    path("orders/",      create_order, name="order-create"),
    path("orders/list/", list_orders,  name="order-list"),

    # ── Tagihan belum lunas, riwayat & notifikasi ────────────────────────────
    path("orders/unpaid/",        unpaid_orders,           name="unpaid-orders"),
    path("orders/history/",       order_history,           name="order-history"),
    path("orders/notifications/", new_order_notifications, name="order-notifications"),
    path("orders/pending-refunds/", pending_refunds, name="pending-refunds"),
    path("orders/affected-by-menu/<int:menu_id>/", orders_affected_by_menu, name="orders-affected-by-menu"),

    # ── Active orders (prefix berbeda) ───────────────────────────────────────
    path("active-orders/", active_orders_per_day, name="active-orders"),

    # ── Loyalty — publik ─────────────────────────────────────────────────────
    path("orders/check_loyalty_status/",     check_loyalty_status,    name="check-loyalty"),
    path("orders/point-rewards/available/",  available_point_rewards, name="point-rewards-available"),
    path("orders/member/verify/",            member_verify,           name="member-verify"),

    # ── Loyalty — admin ──────────────────────────────────────────────────────
    path("orders/loyalty-settings/",          LoyaltySettingsView.as_view(), name="loyalty-settings"),
    path("orders/loyal-customers/",           LoyalCustomersView.as_view(),  name="loyal-customers-admin"),
    path("orders/loyal-customers/bulk-delete/", LoyalCustomersBulkDeleteView.as_view(), name="loyal-customers-bulk-delete"),
    path("orders/loyal-customers/<str:phone>/pin/", LoyalCustomerPinView.as_view(), name="loyal-customer-pin"),
    path("orders/loyal-customers/<str:phone>/", LoyalCustomerDetailView.as_view(), name="loyal-customer-detail"),
    path("orders/adjust-points/<str:phone>/", AdjustPointsView.as_view(),    name="adjust-points"),

    # ── Reports & dashboard ──────────────────────────────────────────────────
    path("orders/reports/",                     order_reports,                name="order-reports"),
    path("orders/reports/full/",                order_full_report,            name="order-reports-full"),
    path("orders/stats/",                       DashboardStatsView.as_view(), name="dashboard-stats"),
    path("orders/admin_dashboard_daily_stats/", admin_dashboard_daily_stats,  name="admin-daily-stats"),
    path("orders/export_excel_report/",         export_excel_report,          name="export-excel"),
    path("orders/export_pdf_report/",           export_pdf_report,            name="export-pdf"),

    # ── Finance ──────────────────────────────────────────────────────────────
    path("orders/finance/monthly/",       finance_monthly_summary,  name="finance-monthly"),
    path("orders/finance/daily/",         finance_daily_summary,    name="finance-daily"),
    path("orders/export/finance-excel/",  export_finance_excel_view, name="finance-export-excel"),
    path("orders/export/finance-pdf/",    export_finance_pdf_view,   name="finance-export-pdf"),

    # ── Keramaian: badge publik, kontrol cepat staf, Peta Jam Sibuk admin ────
    path("orders/crowd/",         CrowdStatusView.as_view(), name="crowd-status"),
    path("orders/crowd/manual/",  CrowdManualView.as_view(), name="crowd-manual"),
    path("orders/busy-hours/",    BusyHoursView.as_view(),   name="busy-hours"),

    # ── Analitik menu (admin) ────────────────────────────────────────────────
    path("orders/analytics/menu-performance/", MenuPerformanceView.as_view(), name="analytics-menu-performance"),
    path("orders/analytics/menu-pairs/",       MenuPairsView.as_view(),       name="analytics-menu-pairs"),
    path("orders/analytics/channels/",         ChannelsView.as_view(),        name="analytics-channels"),
    path("orders/analytics/simulation/",       SimulationView.as_view(),      name="analytics-simulation"),
    path("orders/analytics/menu-tomorrow/",    MenuTomorrowView.as_view(),    name="analytics-menu-tomorrow"),
    path("orders/analytics/promo-effectiveness/", PromoEffectivenessView.as_view(), name="analytics-promo-effectiveness"),
    path("orders/analytics/point-effectiveness/", PointEffectivenessView.as_view(), name="analytics-point-effectiveness"),

    # ── Strip Briefing Dashboard (admin) ─────────────────────────────────────
    path("orders/briefing/",                   BriefingView.as_view(),        name="briefing"),

    # ── Store settings ───────────────────────────────────────────────────────
    path("orders/settings/", StoreSettingsView.as_view(), name="store-settings"),

    # ── Per-order (<int:pk>) — taruh paling bawah biar rapi ──────────────────
    path("orders/<int:pk>/",                   get_order,           name="order-detail"),
    path("orders/<int:pk>/pay/",               pay_order,           name="pay-order"),
    path("orders/<int:pk>/accept/",            accept_order,        name="accept-order"),
    path("orders/<int:pk>/cancel/",            cancel_order,        name="cancel-order"),
    path("orders/<int:pk>/items/",             add_order_item,      name="order-item-add"),
    path("orders/<int:pk>/items/<int:item_id>/", order_item_detail, name="order-item-detail"),
    path("orders/<int:pk>/split/",             split_order,         name="order-split"),
    path("orders/<int:pk>/ready/",             mark_order_ready,    name="order-ready"),
    path("orders/<int:pk>/unavailable/",       mark_items_unavailable, name="order-unavailable"),
    path("orders/<int:pk>/refund/",            confirm_refund,      name="order-refund"),
] + router.urls