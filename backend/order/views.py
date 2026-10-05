import calendar
import datetime
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import (
    Count, DecimalField, ExpressionWrapper, F, Max, Min, Q, Sum,
)
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.models import Expense
from menu.models import Menu
from promotions.models import Promo  # validasi & kunci kuota server-side saat create_order

from .pricing import web_price
from .models import (
    CANCEL_REASON_CHOICES,
    PAYMENT_METHOD_CHOICES,
    CustomerLoyalty,
    LoyaltySettings,
    Order,
    OrderDeletionLog,
    OrderItem,
    OrderPayment,
    PointAdjustment,
    PointReward,
    StoreSettings,
)
from .serializers import (
    LoyaltySettingsSerializer,
    OrderSerializer,
    PointRewardSerializer,
    StoreSettingsSerializer,
)


# ─────────────────────────────────────────────
# HELPERS BERSAMA
# ─────────────────────────────────────────────

# Subtotal per baris item (price * quantity), dipakai di beberapa agregasi.
LINE_TOTAL = ExpressionWrapper(
    F("price") * F("quantity"),
    output_field=DecimalField(),
)


def _int_param(request, name, default):
    """Ambil query param integer; kalau kosong/invalid balik ke default (bukan 500)."""
    try:
        return int(request.query_params.get(name, default))
    except (TypeError, ValueError):
        return default


def _price_for(source, menu):
    """
    Harga item: web = markup 1% (dibulatkan ke atas kelipatan 500),
    POS = harga normal. SATU-SATUNYA tempat aturan ini ditulis.
    """
    if source == "web":
        return web_price(menu.price)
    return menu.price


def _calc_promo_discount(promo, subtotal):
    """
    Nominal diskon promo untuk subtotal tertentu. SATU-SATUNYA tempat aturan
    ini ditulis (dipakai create_order & _refresh_totals).
    ASUMSI field Promo: discount_type ('percentage'/'fixed'), discount_value,
    max_discount_amount.
    """
    if not promo:
        return Decimal("0")

    discount_value = Decimal(str(getattr(promo, "discount_value", 0) or 0))
    if getattr(promo, "discount_type", "fixed") == "percentage":
        discount = subtotal * discount_value / Decimal("100")
        max_discount = getattr(promo, "max_discount_amount", None)
        if max_discount:
            discount = min(discount, Decimal(str(max_discount)))
    else:
        discount = discount_value

    return min(discount, subtotal)


# ─────────────────────────────────────────────
# ORDERS — CRUD
# ─────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
@transaction.atomic
def create_order(request):
    data       = request.data
    items_data = data.get('items', [])

    if not items_data:
        return Response({"error": "Items kosong"}, status=400)

    customer_data = data.get('customer') or {}
    phone = (customer_data.get('phone') or data.get('customer_phone', '') or '').strip()
    name  = (customer_data.get('name')  or data.get('customer_name',  '') or '').strip()

    source         = data.get('source', 'pos')
    payment_method = data.get('payment_method', 'cash')

    # PENTING: source='pos' cuma boleh dipercaya kalau request ini beneran
    # datang dari staff yang login. Tanpa ini, siapa pun tanpa login bisa
    # POST /orders/ langsung dengan source='pos' dan order-nya otomatis
    # ke-mark 'paid'+'completed' di bawah — bypass total alur web/QRIS.
    if source == 'pos' and not (request.user and request.user.is_authenticated and request.user.is_staff):
        source = 'web'

    table_number = data.get('table_number')
    notes        = data.get('notes', '')

    try:
        amount_paid = Decimal(str(data.get('amount_paid', 0) or 0))
    except Exception:
        return Response({"error": "amount_paid tidak valid"}, status=400)
    kasir_name = (data.get('kasir_name') or '').strip()

    promo_id = data.get('promo_id')

    # Poin yang mau ditukar (list of PointReward id, bisa ada duplikat kalau
    # customer nuker reward yang sama lebih dari 1x)
    redeem_reward_ids = data.get('redeem_reward_ids') or []

    raw_payment_status = data.get('payment_status', '')

    is_qris         = payment_method in ('qris', 'qris_manual', 'gateway')
    proof_image_url = (data.get('proof_image_url') or '').strip()

    if source == 'web' and is_qris and not proof_image_url:
        return Response({"error": "Bukti pembayaran QRIS wajib diupload"}, status=400)

    if source == 'web':
        if is_qris:
            # Web + QRIS → JANGAN langsung 'paid'. Nunggu admin cek manual
            # bukti pembayaran lewat endpoint verify-payment sebelum order
            # dianggap lunas & masuk laporan omzet.
            payment_status = 'pending_verification'
        else:
            payment_status = 'pending'
        is_deferred  = False
        order_status = 'pending'
    elif raw_payment_status == 'pending' and not is_qris:
        # POS "Makan Dulu" — hanya boleh cash
        payment_status = 'unpaid'
        is_deferred    = True
        order_status   = 'pending'
    else:
        # POS bayar sekarang (cash atau qris)
        payment_status = 'paid'
        is_deferred    = False
        order_status   = 'completed'

    # ── Validasi & kunci promo (kalau ada) ──────────────────────────
    promo_obj = None
    if promo_id:
        promo_obj = Promo.objects.select_for_update().filter(pk=promo_id, is_active=True).first()
        if not promo_obj:
            return Response({"error": "Promo tidak valid atau sudah tidak aktif"}, status=400)

        quota = getattr(promo_obj, "quota", None)
        if quota is not None and promo_obj.used_count >= quota:
            return Response({"error": "Kuota promo sudah habis"}, status=400)

    # ── Bikin Order dulu (item & payment nyusul, biar dapet FK) ─────
    # status sengaja 'pending' dulu — status final (mis. 'completed' buat POS
    # bayar langsung) baru diset di save() TERAKHIR, setelah total_price
    # terisi. Kalau tidak, signal loyalty (post_save) jalan saat total masih 0
    # dan poin customer tidak pernah ke-earn.
    order = Order.objects.create(
        source=source,
        status='pending',
        payment_status=payment_status,
        payment_method=payment_method,
        is_deferred_payment=is_deferred,
        customer_name=name,
        customer_phone=phone,
        table_number=table_number,
        notes=notes,
        kasir_name=kasir_name,
        proof_image_url=proof_image_url,
        promo=promo_obj,
    )

    # ── Bikin OrderItem dari items_data ──────────────────────────────
    subtotal = Decimal('0')
    for item in items_data:
        menu_id    = item.get('menu_id') or item.get('menu')
        item_notes = (item.get('notes') or '').strip()
        try:
            quantity = int(item.get('quantity', 1) or 1)
        except (TypeError, ValueError):
            quantity = 0

        if not menu_id or quantity <= 0:
            transaction.set_rollback(True)
            return Response({"error": "Data item tidak valid (menu_id/quantity)"}, status=400)

        menu  = get_object_or_404(Menu, pk=menu_id)
        price = _price_for(source, menu)

        OrderItem.objects.create(
            order=order, menu=menu, quantity=quantity,
            price=price, notes=item_notes,
        )
        subtotal += price * quantity

    # ── Redeem poin (kalau ada) ──────────────────────────────────────
    total_point_cost = 0
    if redeem_reward_ids:
        if not phone:
            transaction.set_rollback(True)
            return Response({"error": "Nomor HP wajib diisi buat nuker poin"}, status=400)

        loyalty = CustomerLoyalty.objects.select_for_update().filter(phone=phone).first()
        if not loyalty:
            transaction.set_rollback(True)
            return Response({"error": "Customer belum terdaftar loyalty, belum punya poin"}, status=400)

        loyalty.check_and_expire_points()

        for reward_id in redeem_reward_ids:
            reward = (
                PointReward.objects
                .filter(pk=reward_id, is_active=True)
                .select_related('menu')
                .first()
            )
            if not reward:
                transaction.set_rollback(True)
                return Response({"error": "Salah satu reward tidak valid/tidak aktif"}, status=400)

            OrderItem.objects.create(
                order=order, menu=reward.menu, quantity=1,
                price=Decimal('0'), is_point_redemption=True,
            )
            total_point_cost += reward.point_cost

        if total_point_cost > loyalty.points:
            transaction.set_rollback(True)
            return Response(
                {"error": f"Poin tidak cukup. Saldo {loyalty.points}, butuh {total_point_cost}"},
                status=400,
            )

        loyalty.points -= total_point_cost
        loyalty.save(update_fields=['points'])
        PointAdjustment.objects.create(
            customer=loyalty, amount=-total_point_cost, reason='manual',
            note=f"Redeem reward saat order {order.order_number}",
            admin_name=kasir_name or 'system',
        )

    # ── Hitung diskon promo & total akhir ────────────────────────────
    promo_discount_amount = _calc_promo_discount(promo_obj, subtotal)
    if promo_obj:
        Promo.objects.filter(pk=promo_obj.pk).update(used_count=F('used_count') + 1)

    order.subtotal              = subtotal
    order.promo_discount_amount = promo_discount_amount
    total = subtotal - promo_discount_amount
    order.total_price = total if total > 0 else Decimal('0')
    order.status      = order_status   # trigger signal loyalty dengan total yang sudah benar

    # Bayar langsung cash tapi uang diterima kurang dari total → tolak
    # (jangan sampai order ke-mark lunas padahal kurang bayar).
    if payment_status == 'paid' and payment_method == 'cash' and 0 < amount_paid < order.total_price:
        transaction.set_rollback(True)
        return Response({"error": "Uang diterima kurang dari total tagihan"}, status=400)

    if amount_paid > 0:
        order.amount_paid   = amount_paid
        order.change_amount = max(amount_paid - order.total_price, Decimal('0'))
    elif payment_status == 'paid':
        order.amount_paid = order.total_price

    order.save()

    # ── Catat baris pembayaran (kalau order langsung lunas) ──────────
    if order.payment_status == 'paid' and order.payment_method:
        OrderPayment.objects.create(
            order=order,
            method=order.payment_method,
            amount=order.amount_paid or order.total_price,
        )

    order.refresh_from_db()
    return Response(OrderSerializer(order).data, status=201)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def list_orders(request):
    orders = (
        Order.objects
        .prefetch_related("items__menu")
        .order_by("-created_at")
    )
    return Response(OrderSerializer(orders, many=True).data)


# ─────────────────────────────────────────────
# HAPUS PERMANEN — helper (dipakai get_order saat method DELETE)
# ─────────────────────────────────────────────
# Beda dari cancel_order (void): cancel_order cuma ubah status, row Order
# tetap ada buat audit. Ini beneran ngilangin row Order dari DB (+
# OrderItem/OrderPayment ikut CASCADE) — dipakai buat kasus salah input
# yang baru ketauan belakangan, duplikat, dsb, TERMASUK order yang sudah
# completed/paid.
#
# Sebelum row-nya hilang:
#   1. Reverse poin loyalty yang sudah kadung di-earn dari order ini
#      (kalau order.loyalty_applied True) — di-clamp ke 0.
#   2. Reverse kuota promo (used_count) kalau order ini pakai promo.
#   3. Simpan snapshot lengkap ke OrderDeletionLog.
@transaction.atomic
def _delete_order_permanently(order, deleted_by=""):
    items_snapshot = [
        {
            "menu_name": item.menu.name if item.menu else "(menu dihapus)",
            "quantity": item.quantity,
            "price": float(item.price),
            "notes": item.notes,
            "is_point_redemption": item.is_point_redemption,
        }
        for item in order.items.select_related("menu").all()
    ]
    payments_snapshot = [
        {"method": p.method, "amount": float(p.amount)}
        for p in order.payments.all()
    ]

    loyalty_points_reverted = 0
    loyalty_clamped = False

    # Reverse poin HANYA kalau order ini memang pernah trigger penambahan poin.
    if order.loyalty_applied and order.customer_phone:
        loyalty = CustomerLoyalty.objects.select_for_update().filter(
            phone=order.customer_phone
        ).first()

        if loyalty:
            points_to_revert = order.loyalty_points_earned
            if points_to_revert > loyalty.points:
                loyalty_clamped = True

            new_points = max(loyalty.points - points_to_revert, 0)
            loyalty_points_reverted = loyalty.points - new_points

            loyalty.points = new_points
            loyalty.total_spent = max(loyalty.total_spent - order.total_price, Decimal("0"))
            loyalty.total_orders = max(loyalty.total_orders - 1, 0)

            # Recompute last_order_at dari order completed LAIN milik customer ini.
            loyalty.last_order_at = (
                Order.objects.filter(customer_phone=order.customer_phone, status="completed")
                .exclude(pk=order.pk)
                .aggregate(latest=Max("created_at"))["latest"]
            )

            loyalty.save(update_fields=["points", "total_spent", "total_orders", "last_order_at"])

            PointAdjustment.objects.create(
                customer=loyalty,
                amount=-loyalty_points_reverted,
                reason="manual",
                note=(
                    f"Reversal otomatis — order {order.order_number} dihapus permanen"
                    + (" (poin di-clamp ke 0, saldo sudah kurang dari yang di-reverse)" if loyalty_clamped else "")
                ),
                admin_name=deleted_by or "system",
            )

    # Reverse kuota promo (jangan sampai used_count jadi minus).
    promo_code_reverted = ""
    if order.promo_id:
        Promo.objects.filter(pk=order.promo_id, used_count__gt=0).update(used_count=F("used_count") - 1)
        promo_code_reverted = getattr(order.promo, "code", str(order.promo_id))

    OrderDeletionLog.objects.create(
        order_number=order.order_number,
        order_source=order.source,
        order_status=order.status,
        payment_status=order.payment_status,
        payment_method=order.payment_method,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        total_price=order.total_price,
        amount_paid=order.amount_paid,
        original_created_at=order.created_at,
        items_snapshot=items_snapshot,
        payments_snapshot=payments_snapshot,
        loyalty_points_reverted=loyalty_points_reverted,
        loyalty_clamped=loyalty_clamped,
        promo_code_reverted=promo_code_reverted,
        deleted_by=deleted_by,
    )

    order_number = order.order_number
    order.delete()
    return order_number


@api_view(["GET", "DELETE"])
@permission_classes([IsAdminUser])
def get_order(request, pk):
    order = get_object_or_404(
        Order.objects.select_related("promo").prefetch_related("items__menu", "payments"),
        pk=pk,
    )

    if request.method == "DELETE":
        # IsAdminUser cuma cek is_staff — BUKAN role owner. Hapus permanen
        # cuma boleh owner, jadi dicek manual di sini juga.
        profile = getattr(request.user, "profile", None)
        if not profile or profile.role != "owner":
            return Response(
                {"detail": "Hanya owner yang boleh menghapus order secara permanen."},
                status=403,
            )

        deleted_by = getattr(request.user, "username", "") or "owner"
        order_number = _delete_order_permanently(order, deleted_by=deleted_by)

        return Response({
            "success": True,
            "order_number": order_number,
            "detail": f"Order {order_number} dihapus permanen. Poin loyalty & kuota promo sudah di-reverse.",
        })

    return Response(OrderSerializer(order).data)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def active_orders_per_day(request):
    target_date = request.query_params.get("target_date")
    if not target_date:
        return Response({"error": "Parameter target_date wajib diisi"}, status=400)

    orders = (
        Order.objects
        .filter(created_at__date=target_date)
        .prefetch_related("items__menu")
        .order_by("-created_at")
    )
    return Response(OrderSerializer(orders, many=True).data)


# ─────────────────────────────────────────────
# LOYALTY — PUBLIK
# ─────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def check_loyalty_status(request):
    """
    GET /api/orders/check_loyalty_status/?phone=08xxx

    Response (poin, BUKAN diskon lagi):
      - is_member            → True kalau nomor ini udah tercatat di CustomerLoyalty
      - points               → saldo poin aktif saat ini (udah lewat cek hangus)
      - points_expiring_note → pesan kalau poin baru aja hangus / estimasi hangusnya
    """
    phone = request.query_params.get("phone", "").strip()
    if not phone:
        return Response({"is_member": False, "points": 0, "points_expiring_note": None})

    loyalty = CustomerLoyalty.objects.filter(phone=phone).first()
    if not loyalty:
        return Response({"is_member": False, "points": 0, "points_expiring_note": None})

    # Cek hangus SEBELUM ditampilkan, biar saldo selalu akurat real-time.
    just_expired = loyalty.check_and_expire_points()

    note = None
    if just_expired:
        note = (
            f"Poin hangus karena tidak ada pesanan selama "
            f"{loyalty.expiry_months_setting()} bulan (order terakhir "
            f"{loyalty.last_order_at:%d %b %Y})" if loyalty.last_order_at else "Poin hangus otomatis"
        )
    else:
        expiry_date = loyalty.expiry_estimate_date()
        if expiry_date:
            note = f"Poin akan hangus sekitar {expiry_date:%d %b %Y} kalau tidak ada pesanan lagi"

    return Response({
        "is_member":            True,
        "points":               loyalty.points,
        "points_expiring_note": note,
    })


# ─────────────────────────────────────────────
# POINT REWARDS — PUBLIK
# ─────────────────────────────────────────────

LOCKED_RECOMMENDATION_LIMIT = 5


@api_view(["GET"])
@permission_classes([AllowAny])
def available_point_rewards(request):
    """
    GET /api/orders/point-rewards/available/?phone=08xxx

    Response:
      - points: saldo poin customer saat ini (0 kalau belum punya akun loyalty)
      - affordable: reward yang poinnya cukup, diurutkan dari yang paling MAHAL.
      - locked: reward yang paling DEKAT ke saldo poin (missing_points paling
        kecil), max 5 — biar rekomendasinya kerasa achievable.
    """
    phone  = request.query_params.get("phone", "").strip()
    points = 0
    if phone:
        loyalty = CustomerLoyalty.objects.filter(phone=phone).first()
        points = loyalty.points if loyalty else 0

    rewards = PointReward.objects.filter(is_active=True).select_related('menu')

    affordable, locked = [], []
    for reward in rewards:
        data = PointRewardSerializer(reward).data
        if reward.point_cost <= points:
            affordable.append((reward.point_cost, data))
        else:
            data["missing_points"] = reward.point_cost - points
            locked.append((reward.point_cost - points, data))

    affordable.sort(key=lambda pair: pair[0], reverse=True)
    locked.sort(key=lambda pair: pair[0])

    return Response({
        "points": points,
        "affordable": [data for _, data in affordable],
        "locked": [data for _, data in locked[:LOCKED_RECOMMENDATION_LIMIT]],
    })


# ─────────────────────────────────────────────
# POINT REWARDS — ADMIN CRUD
# ─────────────────────────────────────────────

class PointRewardViewSet(viewsets.ModelViewSet):
    queryset = PointReward.objects.select_related('menu').all()
    serializer_class = PointRewardSerializer
    permission_classes = [IsAdminUser]


# ─────────────────────────────────────────────
# REPORTS & DASHBOARD
# ─────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAdminUser])
def order_reports(request):
    month = request.query_params.get("month")
    year  = request.query_params.get("year")

    # Konsisten dengan dashboard & laporan lengkap: hanya order lunas, bukan batal.
    qs = Order.objects.filter(payment_status='paid').exclude(status='cancelled')
    if month and year:
        qs = qs.filter(created_at__month=month, created_at__year=year)
    elif year:
        qs = qs.filter(created_at__year=year)

    top_menus = (
        OrderItem.objects.filter(order__in=qs)
        .values("menu__name")
        .annotate(total_qty=Sum("quantity"))
        .order_by("-total_qty")[:5]
    )

    return Response({
        "total_orders":  qs.count(),
        "total_revenue": qs.aggregate(total=Sum("total_price"))["total"] or 0,
        "top_menus":     list(top_menus),
    })


class DashboardStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        date_from = request.query_params.get('date_from')
        date_to   = request.query_params.get('date_to')

        paid_qs = Order.objects.filter(payment_status='paid').exclude(status='cancelled')
        all_qs  = Order.objects.all()
        top_menu_qs = OrderItem.objects.filter(
            order__payment_status='paid',
        ).exclude(order__status='cancelled')

        if date_from:
            paid_qs     = paid_qs.filter(created_at__date__gte=date_from)
            all_qs      = all_qs.filter(created_at__date__gte=date_from)
            top_menu_qs = top_menu_qs.filter(order__created_at__date__gte=date_from)
        if date_to:
            paid_qs     = paid_qs.filter(created_at__date__lte=date_to)
            all_qs      = all_qs.filter(created_at__date__lte=date_to)
            top_menu_qs = top_menu_qs.filter(order__created_at__date__lte=date_to)

        paid_stats = paid_qs.aggregate(
            total_revenue=Sum("total_price"),
            total_orders=Count("id"),
        )

        pending   = all_qs.filter(status="pending").count()
        completed = all_qs.filter(status="completed").count()

        top_menus = (
            top_menu_qs
            .values("menu__name")
            .annotate(total_qty=Sum("quantity"), total_revenue=Sum(LINE_TOTAL))
            .order_by("-total_qty")[:5]
        )

        # Member loyal = punya poin aktif (gak ada lagi tier min_orders/min_spending).
        loyal_count = CustomerLoyalty.objects.filter(points__gt=0).count()

        return Response({
            "total_revenue":    paid_stats["total_revenue"] or 0,
            "total_orders":     paid_stats["total_orders"]  or 0,
            "pending_orders":   pending,
            "completed_orders": completed,
            "top_menus": [
                {
                    "name":          m["menu__name"],
                    "total_qty":     m["total_qty"],
                    "total_revenue": m["total_revenue"] or 0,
                }
                for m in top_menus
            ],
            "loyal_users": loyal_count,
        })


@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_dashboard_daily_stats(request):
    target_date = request.query_params.get("target_date")

    revenue        = 0
    expenses_total = 0

    if target_date:
        revenue = Order.objects.filter(
            created_at__date=target_date,
            payment_status='paid',
        ).exclude(status='cancelled').aggregate(
            total=Sum("total_price")
        )["total"] or 0

        expenses_total = Expense.objects.filter(
            date=target_date
        ).aggregate(total=Sum("amount"))["total"] or 0

    return Response({
        "revenue":    revenue,
        "expenses":   expenses_total,
        "net_profit": revenue - expenses_total,
    })


@api_view(["GET"])
@permission_classes([IsAdminUser])
def finance_monthly_summary(request):
    from django.db.models.functions import ExtractMonth, TruncMonth

    year = _int_param(request, "year", timezone.now().year)

    revenue_qs = (
        Order.objects
        .filter(created_at__year=year, payment_status='paid')
        .exclude(status='cancelled')
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('total_price'))
        .order_by('month')
    )
    revenue_map = {r['month'].month: r['total'] for r in revenue_qs}

    expense_qs = (
        Expense.objects
        .filter(date__year=year)
        .annotate(month_num=ExtractMonth('date'))
        .values('month_num')
        .annotate(total=Sum('amount'))
    )
    expense_map = {e['month_num']: e['total'] for e in expense_qs}

    result = []
    for m in range(1, 13):
        rev = revenue_map.get(m, 0)
        exp = expense_map.get(m, 0)
        result.append({
            "month":      m,
            "month_name": calendar.month_name[m],
            "revenue":    rev,
            "expenses":   exp,
            "net_profit": rev - exp,
        })

    return Response({"year": year, "data": result})


@api_view(["GET"])
@permission_classes([IsAdminUser])
def finance_daily_summary(request):
    """
    GET /api/orders/finance/daily/?year=2026&month=6
    Pendapatan & pengeluaran per hari dalam satu bulan.
    """
    from django.db.models.functions import TruncDate

    now   = timezone.now()
    year  = _int_param(request, "year",  now.year)
    month = _int_param(request, "month", now.month)
    if not 1 <= month <= 12:
        month = now.month

    revenue_qs = (
        Order.objects
        .filter(created_at__year=year, created_at__month=month, payment_status='paid')
        .exclude(status='cancelled')
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(total=Sum('total_price'))
        .order_by('day')
    )
    revenue_map = {str(r['day']): r['total'] for r in revenue_qs}

    expense_qs = (
        Expense.objects
        .filter(date__year=year, date__month=month)
        .values('date')
        .annotate(total=Sum('amount'))
    )
    expense_map = {str(e['date']): e['total'] for e in expense_qs}

    days_in_month = calendar.monthrange(year, month)[1]
    result = []
    for d in range(1, days_in_month + 1):
        date_str = f"{year}-{month:02d}-{d:02d}"
        rev = revenue_map.get(date_str, 0)
        exp = expense_map.get(date_str, 0)
        result.append({
            "date":       date_str,
            "day":        d,
            "revenue":    rev,
            "expenses":   exp,
            "net_profit": rev - exp,
        })

    return Response({"year": year, "month": month, "data": result})


# ─────────────────────────────────────────────
# EXPORT
# ─────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAdminUser])
def export_excel_report(request):
    """
    GET /api/orders/export/finance-excel/?mode=monthly&month=7&year=2026
    GET /api/orders/export/finance-excel/?mode=yearly&year=2026
    """
    from .finance_excel import export_finance_excel_view
    return export_finance_excel_view(request)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def export_pdf_report(request):
    """
    GET /api/orders/export/finance-pdf/?mode=monthly&month=7&year=2026
    GET /api/orders/export/finance-pdf/?mode=yearly&year=2026
    """
    from .finance_pdf import export_finance_pdf_view
    return export_finance_pdf_view(request)


# ─────────────────────────────────────────────
# LOYALTY — ADMIN
# ─────────────────────────────────────────────

class LoyaltySettingsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response(LoyaltySettingsSerializer(LoyaltySettings.get_settings()).data)

    def put(self, request):
        settings   = LoyaltySettings.get_settings()
        serializer = LoyaltySettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LoyalCustomersView(APIView):
    """
    Sumber data langsung dari CustomerLoyalty (points/total_spent/total_orders/
    last_order_at udah kesimpen real-time lewat signal tiap order completed).
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        settings  = LoyaltySettings.get_settings()
        customers = [
            {
                "phone":           cl.phone,
                "name":            cl.name,
                "points":          cl.points,
                "total_orders":    cl.total_orders,
                "total_spent":     cl.total_spent,
                "last_order_at":   cl.last_order_at,
                "expiry_estimate": cl.expiry_estimate_date(),
                "points_expired":  cl.points_expired(),
            }
            for cl in CustomerLoyalty.objects.all().order_by('-points')
        ]

        return Response({
            "settings":  LoyaltySettingsSerializer(settings).data,
            "customers": customers,
        })


class AdjustPointsView(APIView):
    """
    Adjust poin manual (nambah/mengurangi), alasan wajib & tercatat sebagai
    PointAdjustment (audit log).
    """
    permission_classes = [IsAdminUser]

    @transaction.atomic
    def post(self, request, phone):
        amount = request.data.get('amount')
        note   = (request.data.get('note') or '').strip()

        if amount is None:
            return Response({'detail': 'amount wajib diisi'}, status=400)
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            return Response({'detail': 'amount harus berupa angka bulat'}, status=400)
        if amount == 0:
            return Response({'detail': 'amount tidak boleh 0'}, status=400)
        if not note:
            return Response({'detail': 'Alasan (note) wajib diisi buat jejak audit'}, status=400)

        CustomerLoyalty.objects.get_or_create(
            phone=phone,
            defaults={'name': request.data.get('name', '')},
        )
        # Lock row biar dua adjust barengan gak saling timpa saldo.
        loyalty = CustomerLoyalty.objects.select_for_update().get(phone=phone)

        new_balance = loyalty.points + amount
        if new_balance < 0:
            return Response(
                {'detail': f'Saldo poin cuma {loyalty.points}, gak bisa dikurangin {abs(amount)}'},
                status=400,
            )

        loyalty.points = new_balance
        loyalty.save(update_fields=['points'])

        admin_name = getattr(request.user, 'username', '') or 'admin'
        PointAdjustment.objects.create(
            customer=loyalty, amount=amount, reason='manual',
            note=note, admin_name=admin_name,
        )

        return Response({'phone': phone, 'points': loyalty.points})


# ─────────────────────────────────────────────
# UNPAID ORDERS, PAYMENT, CANCEL
# ─────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAdminUser])
def unpaid_orders(request):
    search = request.query_params.get("search", "")

    qs = (
        Order.objects
        .filter(payment_status__in=["unpaid", "pending"])
        .exclude(status="cancelled")
        .prefetch_related("items__menu")
    )

    if search:
        qs = qs.filter(
            Q(customer_name__icontains=search)
            | Q(customer_phone__icontains=search)
            | Q(order_number__icontains=search)
        )

    return Response(OrderSerializer(qs.order_by("-created_at"), many=True).data)


@api_view(["PATCH"])
@permission_classes([IsAdminUser])
@transaction.atomic
def pay_order(request, pk):
    """
    Melunasi order. Mendukung 2 format request:

    1. FORMAT BARU (split bill / multi-payment) — kirim list `payments`:
       { "payments": [{"method": "cash", "amount": 5000}, {"method": "qris_manual", "amount": 8000}],
         "kasir_name": "Budi" }

    2. FORMAT LAMA (satu metode, satu jumlah):
       { "payment_method": "cash", "amount_paid": 20000, "kasir_name": "Budi" }

    Order di-lock selama proses, dan order yang sudah lunas / dibatalkan
    ditolak — jadi double-klik / request barengan tidak bikin bayar dua kali.
    """
    order = get_object_or_404(Order.objects.select_for_update(), pk=pk)

    if order.status == "cancelled" or order.payment_status in ("paid", "void"):
        return Response(
            {"detail": "Order ini sudah lunas atau dibatalkan, tidak bisa dibayar lagi."},
            status=400,
        )

    previous_status = order.status
    kasir_name      = (request.data.get('kasir_name') or '').strip()
    payments_data   = request.data.get('payments')

    if payments_data:
        # ── Format baru: banyak baris pembayaran ──
        valid_methods = {choice[0] for choice in PAYMENT_METHOD_CHOICES if choice[0] != 'mixed'}
        parsed_rows = []
        for row in payments_data:
            method = (row.get('method') or '').strip()
            try:
                amount = Decimal(str(row.get('amount', 0) or 0))
            except Exception:
                return Response({"detail": "Nominal pembayaran tidak valid."}, status=400)

            if method not in valid_methods:
                return Response({"detail": f"Metode pembayaran '{method}' tidak valid."}, status=400)
            if amount <= 0:
                return Response({"detail": "Nominal tiap baris pembayaran harus lebih dari 0."}, status=400)

            parsed_rows.append((method, amount))

        if not parsed_rows:
            return Response({"detail": "Minimal harus ada satu baris pembayaran."}, status=400)

        total_paid = sum(amount for _, amount in parsed_rows)
        if total_paid < order.total_price:
            return Response({"detail": "Total pembayaran belum menutupi tagihan."}, status=400)

        order.payments.all().delete()
        for method, amount in parsed_rows:
            OrderPayment.objects.create(order=order, method=method, amount=amount)

        distinct_methods = {method for method, _ in parsed_rows}
        order.payment_method = "mixed" if len(distinct_methods) > 1 else next(iter(distinct_methods))
        order.amount_paid    = total_paid
        order.change_amount  = max(total_paid - order.total_price, Decimal('0'))

    else:
        # ── Format lama: satu metode, satu jumlah ──
        try:
            amount_paid = Decimal(str(request.data.get('amount_paid', 0) or 0))
        except Exception:
            return Response({"detail": "Nominal pembayaran tidak valid."}, status=400)
        method = request.data.get("payment_method") or order.payment_method or "cash"

        order.payments.all().delete()
        OrderPayment.objects.create(
            order=order, method=method,
            amount=amount_paid if amount_paid > 0 else order.total_price,
        )

        order.payment_method = method
        order.amount_paid    = amount_paid
        if amount_paid > 0:
            order.change_amount = max(amount_paid - order.total_price, Decimal('0'))

    order.payment_status = "paid"
    order.status         = "completed"
    order.kasir_name     = kasir_name or order.kasir_name

    order._previous_status = previous_status
    order.save()
    order.refresh_from_db()

    return Response({
        "success":        True,
        "order_number":   order.order_number,
        "change_amount":  float(order.change_amount),
        "amount_paid":    float(order.amount_paid),
        "payment_method": order.payment_method,
    })


@api_view(["PATCH"])
@permission_classes([IsAdminUser])
@transaction.atomic
def verify_qris_payment(request, pk):
    """
    PATCH /api/orders/<id>/verify-payment/
    Body: { "approve": true/false, "kasir_name": "...", "reject_note": "..." }

    approve=true → order lunas (paid+completed).
    approve=false → order dibatalkan (pembayaran tidak valid).
    """
    order = get_object_or_404(Order.objects.select_for_update(), pk=pk)

    if order.payment_status != 'pending_verification':
        return Response(
            {"detail": "Order ini bukan status menunggu verifikasi."},
            status=400,
        )

    approve         = request.data.get('approve', True)
    kasir_name      = (request.data.get('kasir_name') or '').strip()
    previous_status = order.status

    if approve:
        order.payment_status = 'paid'
        order.status         = 'completed'
        order.amount_paid    = order.total_price
        order.kasir_name     = kasir_name or order.kasir_name
    else:
        order.payment_status = 'void'
        order.status         = 'cancelled'
        order.cancel_reason  = 'other'
        order.cancel_note    = (request.data.get('reject_note') or 'Bukti pembayaran QRIS tidak valid').strip()
        order.cancelled_at   = timezone.now()
        order.cancelled_by   = kasir_name

    order._previous_status = previous_status
    order.save()
    order.refresh_from_db()

    return Response(OrderSerializer(order).data)


@api_view(["PATCH"])
@permission_classes([IsAdminUser])
@transaction.atomic
def cancel_order(request, pk):
    """
    Void/batalkan order dengan alasan wajib. Order TIDAK dihapus dari
    database, cuma diubah statusnya jadi 'cancelled' + dicatat alasannya.
    """
    order = get_object_or_404(Order.objects.select_for_update(), pk=pk)
    previous_status = order.status

    if order.status == "completed":
        return Response(
            {"detail": "Order yang sudah selesai (completed) tidak bisa dibatalkan lewat sini."},
            status=400,
        )
    if order.status == "cancelled":
        return Response({"detail": "Order ini sudah dibatalkan sebelumnya."}, status=400)

    reason = (request.data.get("cancel_reason") or "").strip()
    valid_reasons = {choice[0] for choice in CANCEL_REASON_CHOICES}
    if reason not in valid_reasons:
        return Response(
            {"detail": "Alasan pembatalan wajib diisi dan harus valid."},
            status=400,
        )

    order.status         = "cancelled"
    order.payment_status = "void"
    order.cancel_reason  = reason
    order.cancel_note    = (request.data.get("cancel_note") or "").strip()
    order.cancelled_at   = timezone.now()
    order.cancelled_by   = (request.data.get("kasir_name") or "").strip()

    order._previous_status = previous_status
    order.save()
    order.refresh_from_db()

    return Response({
        "success":       True,
        "order_number":  order.order_number,
        "status":        order.status,
        "cancel_reason": order.cancel_reason,
    })


# ─────────────────────────────────────────────
# NOTIFIKASI ORDER BARU
# ─────────────────────────────────────────────

NOTIFICATION_BACKLOG_SKIP_THRESHOLD = 50


@api_view(["GET"])
@permission_classes([IsAdminUser])
def new_order_notifications(request):
    """
    GET /api/orders/notifications/?after_id=123

    Polling ringan buat deteksi order BARU sejak id terakhir yang diketahui
    frontend (toast + suara di admin dashboard).

    - Order POS (source='pos') di-exclude.
    - Tanpa `after_id` (pemanggilan pertama), balikin new_orders kosong +
      `latest_id` sebagai starting point, biar order lama gak ke-notif ulang.
    - Gap after_id → latest_id lebih besar dari
      NOTIFICATION_BACKLOG_SKIP_THRESHOLD dianggap bulk insert: cursor
      di-jump dan `backlog_skipped: True` dikirim ke frontend.
    """
    latest_id = Order.objects.order_by('-id').values_list('id', flat=True).first() or 0

    after_id_raw = request.query_params.get("after_id")
    if after_id_raw is None:
        return Response({'new_orders': [], 'latest_id': latest_id})

    try:
        after_id = int(after_id_raw)
    except (TypeError, ValueError):
        return Response({'new_orders': [], 'latest_id': latest_id})

    gap = latest_id - after_id
    if gap > NOTIFICATION_BACKLOG_SKIP_THRESHOLD:
        return Response({
            'new_orders': [],
            'latest_id': latest_id,
            'backlog_skipped': True,
            'backlog_count': gap,
        })

    new_orders_qs = (
        Order.objects
        .filter(id__gt=after_id)
        .exclude(source='pos')
        .order_by('id')[:20]
    )

    data = [
        {
            'id':            o.id,
            'order_number':  o.order_number,
            'customer_name': o.customer_name or 'Pelanggan',
            'total_price':   o.total_price,
            'source':        o.source,
            'created_at':    o.created_at,
        }
        for o in new_orders_qs
    ]
    return Response({'new_orders': data, 'latest_id': latest_id})


# ─────────────────────────────────────────────
# HISTORY & LAPORAN LENGKAP
# ─────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAdminUser])
def order_history(request):
    """
    GET /api/orders/history/?period=today|week|month|year
    GET /api/orders/history/?period=month&year=2026&month=6
    """
    period = request.query_params.get("period", "today")
    now    = timezone.now()

    qs = Order.objects.prefetch_related("items__menu")

    if period == "today":
        qs = qs.filter(created_at__date=now.date())

    elif period == "week":
        qs = qs.filter(created_at__gte=now - timedelta(days=7))

    elif period == "month":
        qs = qs.filter(
            created_at__year=_int_param(request, "year", now.year),
            created_at__month=_int_param(request, "month", now.month),
        )

    elif period == "year":
        qs = qs.filter(created_at__year=_int_param(request, "year", now.year))

    return Response(OrderSerializer(qs.order_by("-created_at"), many=True).data)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def order_full_report(request):
    from django.db.models.functions import ExtractHour, TruncDate, TruncMonth

    period = request.query_params.get("period", "lifetime")
    now    = timezone.now()
    year   = _int_param(request, "year",   now.year)
    month  = _int_param(request, "month",  now.month)
    days   = _int_param(request, "days",   7)
    offset = _int_param(request, "offset", 0)

    if days not in (7, 14, 28, 30):
        days = 7
    if not 1 <= month <= 12:
        month = now.month

    # ── 1. Tentukan period_start / period_end ──────────────────────────
    period_start = None
    period_end   = None

    if period == "week":
        period_end   = now.date() - timedelta(days=offset)
        period_start = period_end - timedelta(days=days - 1)

    elif period == "month":
        period_start = datetime.date(year, month, 1)
        period_end   = datetime.date(year, month, calendar.monthrange(year, month)[1])

    elif period == "year":
        period_start = datetime.date(year, 1, 1)
        period_end   = datetime.date(year, 12, 31)

    # ── 2. Base queryset ───────────────────────────────────────────────
    paid_qs = Order.objects.filter(payment_status="paid").exclude(status="cancelled")

    qualifying_qs = paid_qs
    if period_start and period_end:
        qualifying_qs = qualifying_qs.filter(
            created_at__date__gte=period_start,
            created_at__date__lte=period_end,
        )

    qualifying_ids = list(qualifying_qs.values_list("id", flat=True))

    # ── 3. Stats utama ─────────────────────────────────────────────────
    main_stats = qualifying_qs.aggregate(
        total_omzet=Sum("total_price"),
        total_transaksi=Count("id"),
    )
    total_omzet     = main_stats["total_omzet"] or 0
    total_transaksi = main_stats["total_transaksi"] or 0
    rata_rata       = (total_omzet / total_transaksi) if total_transaksi else 0
    menu_aktif      = Menu.objects.filter(is_active=True).count()

    # ── 4. Trend ───────────────────────────────────────────────────────
    if period == "year":
        BULAN_ID = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
        trend_qs = (
            qualifying_qs
            .annotate(period_label=TruncMonth("created_at"))
            .values("period_label")
            .annotate(omzet=Sum("total_price"), transaksi=Count("id"))
            .order_by("period_label")
        )
        trend_labels    = [BULAN_ID[t["period_label"].month - 1] for t in trend_qs]
        trend_dates     = [str(t["period_label"].date()) for t in trend_qs]
        trend_omzet     = [float(t["omzet"] or 0) for t in trend_qs]
        trend_transaksi = [t["transaksi"] for t in trend_qs]

    elif period in ("week", "month") and period_start and period_end:
        trend_qs = (
            qualifying_qs
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(omzet=Sum("total_price"), transaksi=Count("id"))
        )
        trend_map = {}
        for row in trend_qs:
            d = row["day"]
            if hasattr(d, "date"):
                d = d.date()
            trend_map[d] = row

        HARI_ID = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
        trend_labels, trend_dates, trend_omzet, trend_transaksi = [], [], [], []
        for i in range((period_end - period_start).days + 1):
            d   = period_start + timedelta(days=i)
            row = trend_map.get(d)
            trend_labels.append(HARI_ID[d.weekday()])
            trend_dates.append(str(d))
            trend_omzet.append(float(row["omzet"]) if row else 0)
            trend_transaksi.append(row["transaksi"] if row else 0)

    else:
        # Lifetime — by date
        trend_qs = (
            qualifying_qs
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(omzet=Sum("total_price"), transaksi=Count("id"))
            .order_by("day")
        )
        trend_labels    = [str(t["day"]) for t in trend_qs]
        trend_dates     = trend_labels[:]
        trend_omzet     = [float(t["omzet"] or 0) for t in trend_qs]
        trend_transaksi = [t["transaksi"] for t in trend_qs]

    # ── 5. Top menu ────────────────────────────────────────────────────
    base_item_qs = OrderItem.objects.filter(order_id__in=qualifying_ids)

    top_by_qty = list(
        base_item_qs.values("menu__name")
        .annotate(qty=Sum("quantity"), omzet=Sum(LINE_TOTAL))
        .order_by("-qty")[:10]
    )
    top_by_omzet = list(
        base_item_qs.values("menu__name")
        .annotate(omzet=Sum(LINE_TOTAL))
        .order_by("-omzet")[:5]
    )

    # ── 6. Menu tidak laku ─────────────────────────────────────────────
    menu_tidak_laku = list(
        Menu.objects.filter(is_active=True)
        .annotate(
            transaksi=Count("orderitem", filter=Q(orderitem__order_id__in=qualifying_ids))
        )
        .order_by("transaksi", "name")
        .values("name", "transaksi")[:10]
    )

    # ── 7. Metode pembayaran ───────────────────────────────────────────
    pembayaran_qs = (
        qualifying_qs.values("payment_method")
        .annotate(count=Count("id"), total=Sum("total_price"))
        .order_by("-total")
    )
    method_labels         = dict(PAYMENT_METHOD_CHOICES)
    total_revenue_for_pct = float(total_omzet) or 1
    metode_pembayaran = [
        {
            "method":  row["payment_method"],
            "label":   method_labels.get(row["payment_method"], row["payment_method"] or "Lainnya"),
            "count":   row["count"],
            "total":   float(row["total"] or 0),
            "percent": round(float(row["total"] or 0) / total_revenue_for_pct * 100, 1),
        }
        for row in pembayaran_qs
    ]

    # ── 8. Pelanggan ───────────────────────────────────────────────────
    first_order_map = {
        row["customer_phone"]: row["first_date"]
        for row in (
            paid_qs.exclude(customer_phone="")
            .values("customer_phone")
            .annotate(first_date=Min("created_at"))
        )
    }
    phones_in_period = list(
        qualifying_qs.exclude(customer_phone="")
        .values_list("customer_phone", flat=True)
        .distinct()
    )
    pelanggan_baru = 0
    pelanggan_lama = 0
    for phone in phones_in_period:
        first_date = first_order_map.get(phone)
        if not first_date:
            continue
        if period_start and first_date.date() < period_start:
            pelanggan_lama += 1
        else:
            pelanggan_baru += 1

    # Member loyal = customer di periode ini yang punya poin aktif.
    member_loyal = CustomerLoyalty.objects.filter(
        phone__in=phones_in_period, points__gt=0
    ).count()

    # ── 9. Jam teramai ─────────────────────────────────────────────────
    jam_qs = (
        qualifying_qs.annotate(hour=ExtractHour("created_at"))
        .values("hour")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )
    jam_teramai = [
        {
            "hour":  row["hour"],
            "label": f"{row['hour']:02d}.00 - {(row['hour'] + 1) % 24:02d}.00",
            "count": row["count"],
        }
        for row in sorted(jam_qs, key=lambda x: x["hour"])
    ]

    return Response({
        "period": {
            "mode":  period,
            "year":  year,
            "month": month,
            "days":  days,
            "start": str(period_start) if period_start else None,
            "end":   str(period_end)   if period_end   else None,
        },
        "stats": {
            "total_omzet":         float(total_omzet),
            "total_transaksi":     total_transaksi,
            "rata_rata_transaksi": float(rata_rata),
            "menu_aktif":          menu_aktif,
        },
        "trend": {
            "labels":    trend_labels,
            "dates":     trend_dates,
            "omzet":     trend_omzet,
            "transaksi": trend_transaksi,
        },
        "top_menu": [
            {"name": r["menu__name"], "qty": r["qty"], "omzet": float(r["omzet"] or 0)}
            for r in top_by_qty
        ],
        "menu_paling_menghasilkan": [
            {"name": r["menu__name"], "omzet": float(r["omzet"] or 0)}
            for r in top_by_omzet
        ],
        "menu_tidak_laku":   menu_tidak_laku,
        "metode_pembayaran": metode_pembayaran,
        "pelanggan": {
            "baru":         pelanggan_baru,
            "lama":         pelanggan_lama,
            "loyal_member": member_loyal,
        },
        "jam_teramai": jam_teramai,
    })


# ─────────────────────────────────────────────
# STORE SETTINGS
# ─────────────────────────────────────────────

class StoreSettingsView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdminUser()]

    def get(self, request):
        return Response(StoreSettingsSerializer(StoreSettings.get()).data)

    def put(self, request):
        settings   = StoreSettings.get()
        serializer = StoreSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ─────────────────────────────────────────────
# EDIT ITEM & PISAH NOTA (order belum lunas)
# ─────────────────────────────────────────────

def _check_editable(order):
    """Item cuma boleh diubah selama order belum dibayar & belum dibatalkan."""
    if order.status in ("completed", "cancelled") or order.payment_status not in ("unpaid", "pending"):
        return Response(
            {"detail": "Order ini sudah lunas / dibatalkan, item tidak bisa diubah lagi."},
            status=400,
        )
    return None


def _refresh_totals(order):
    """
    Hitung ulang subtotal, diskon promo, dan total. Diskon promo ikut dihitung
    ulang (promo persen berubah saat item ditambah/dikurangi). Item tukar poin
    harganya 0, jadi tidak mempengaruhi subtotal.
    """
    subtotal = sum((i.subtotal for i in order.items.all()), Decimal("0"))
    promo_discount = _calc_promo_discount(order.promo, subtotal)

    order.subtotal = subtotal
    order.promo_discount_amount = promo_discount
    total = subtotal - order.discount_amount - promo_discount
    order.total_price = total if total > 0 else Decimal("0")
    order.save(update_fields=["subtotal", "promo_discount_amount", "total_price"])


@api_view(["POST"])
@permission_classes([IsAdminUser])
@transaction.atomic
def add_order_item(request, pk):
    """
    Tambah menu ke order yang belum lunas.
    Body: { "menu_id": 5, "quantity": 1, "notes": "" }
    Menu + catatan yang sama sudah ada di nota → quantity-nya yang ditambah.
    """
    order = get_object_or_404(Order.objects.select_for_update(), pk=pk)
    err = _check_editable(order)
    if err:
        return err

    menu = get_object_or_404(Menu, pk=request.data.get("menu_id"))
    try:
        quantity = int(request.data.get("quantity", 1) or 1)
    except (TypeError, ValueError):
        return Response({"detail": "Quantity tidak valid."}, status=400)
    if quantity <= 0:
        return Response({"detail": "Quantity harus lebih dari 0."}, status=400)

    notes = (request.data.get("notes") or "").strip()

    existing = order.items.filter(menu=menu, notes=notes, is_point_redemption=False).first()
    if existing:
        existing.quantity += quantity
        existing.save(update_fields=["quantity"])
    else:
        OrderItem.objects.create(
            order=order, menu=menu, quantity=quantity,
            price=_price_for(order.source, menu), notes=notes,
        )

    _refresh_totals(order)
    order.refresh_from_db()
    return Response(OrderSerializer(order).data)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAdminUser])
@transaction.atomic
def order_item_detail(request, pk, item_id):
    """
    PATCH  { "quantity": 3 }  → ubah jumlah (0 = hapus item)
    DELETE                    → hapus item
    """
    order = get_object_or_404(Order.objects.select_for_update(), pk=pk)
    err = _check_editable(order)
    if err:
        return err

    item = get_object_or_404(OrderItem, pk=item_id, order=order)

    if item.is_point_redemption:
        return Response(
            {"detail": "Item hasil tukar poin tidak bisa diubah (poin sudah terpotong). "
                       "Kalau salah, batalkan order-nya."},
            status=400,
        )

    if request.method == "DELETE":
        new_qty = 0
    else:
        try:
            new_qty = int(request.data.get("quantity", item.quantity))
        except (TypeError, ValueError):
            return Response({"detail": "Quantity tidak valid."}, status=400)

    if new_qty <= 0:
        if order.items.count() <= 1:
            return Response(
                {"detail": "Ini item terakhir di nota. Kalau mau dibatalkan semua, pakai Batalkan Order."},
                status=400,
            )
        item.delete()
    else:
        item.quantity = new_qty
        item.save(update_fields=["quantity"])

    _refresh_totals(order)
    order.refresh_from_db()
    return Response(OrderSerializer(order).data)


@api_view(["POST"])
@permission_classes([IsAdminUser])
@transaction.atomic
def split_order(request, pk):
    """
    Pisah sebagian item ke NOTA BARU supaya bisa dibayar terpisah.

    Body:
    {
      "items": [{"item_id": 12, "quantity": 1}, {"item_id": 13, "quantity": 2}],
      "customer_name": "Budi",     # opsional, nama nota baru
      "kasir_name": "Wawan"
    }
    quantity < jumlah di nota → itemnya dipecah (sisanya tetap di nota asal).
    """
    order = get_object_or_404(Order.objects.select_for_update(), pk=pk)
    err = _check_editable(order)
    if err:
        return err

    rows = request.data.get("items") or []
    if not rows:
        return Response({"detail": "Pilih minimal satu item yang mau dipisah."}, status=400)

    moves, seen = [], set()
    for row in rows:
        item = order.items.filter(pk=row.get("item_id")).first()
        if not item or item.pk in seen:
            return Response({"detail": "Item tidak ditemukan / dobel di request."}, status=400)
        if item.is_point_redemption:
            return Response({"detail": "Item hasil tukar poin tidak bisa dipisah."}, status=400)
        try:
            qty = int(row.get("quantity") or 0)
        except (TypeError, ValueError):
            return Response({"detail": "Quantity tidak valid."}, status=400)
        if qty <= 0 or qty > item.quantity:
            return Response({"detail": f"Jumlah untuk {item.menu.name} tidak valid."}, status=400)
        seen.add(item.pk)
        moves.append((item, qty))

    total_units = sum(i.quantity for i in order.items.all())
    if total_units - sum(q for _, q in moves) <= 0:
        return Response(
            {"detail": "Sisakan minimal satu item di nota asal. Kalau semua dipindah, tidak perlu dipisah."},
            status=400,
        )

    new_name   = (request.data.get("customer_name") or "").strip()
    kasir_name = (request.data.get("kasir_name") or "").strip()

    new_order = Order.objects.create(
        source=order.source,
        status="pending",
        payment_status=order.payment_status,
        payment_method=order.payment_method,
        is_deferred_payment=order.is_deferred_payment,
        customer_name=new_name or (f"{order.customer_name} (pisah)" if order.customer_name else "Pisahan"),
        customer_phone="",   # sengaja kosong: poin loyalty tetap di nota asal
        table_number=order.table_number,
        notes=f"Dipisah dari {order.order_number}",
        kasir_name=kasir_name or order.kasir_name,
    )

    for item, qty in moves:
        if qty == item.quantity:
            item.order = new_order
            item.save(update_fields=["order"])
        else:
            item.quantity -= qty
            item.save(update_fields=["quantity"])
            OrderItem.objects.create(
                order=new_order, menu=item.menu, quantity=qty,
                price=item.price, notes=item.notes,
            )

    _refresh_totals(order)      # promo (kalau ada) tetap menempel di nota asal
    _refresh_totals(new_order)
    order.refresh_from_db()
    new_order.refresh_from_db()

    return Response({
        "original":  OrderSerializer(order).data,
        "new_order": OrderSerializer(new_order).data,
    }, status=201)