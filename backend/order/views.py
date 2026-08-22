from django.db import transaction, models
from django.db.models import Count, Sum, Max
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal
from django.db.models import Q
import math
import calendar
import datetime
from datetime import timedelta

# Finance app
from finance.models import Expense

# Promo — dipakai buat validasi & kunci kuota server-side saat create_order
from promotions.models import Promo

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order, OrderItem, OrderPayment, CustomerLoyalty, LoyaltySettings, PAYMENT_METHOD_CHOICES, CANCEL_REASON_CHOICES, StoreSettings, PointReward, PointAdjustment, OrderDeletionLog
from menu.models import Menu
from .serializers import OrderSerializer, LoyaltySettingsSerializer, StoreSettingsSerializer, PointRewardSerializer
from rest_framework import viewsets


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
    phone = (customer_data.get('phone') or data.get('customer_phone', '')).strip()
    name  = (customer_data.get('name')  or data.get('customer_name',  '')).strip()

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

    amount_paid = Decimal(str(data.get('amount_paid', 0) or 0))
    kasir_name  = data.get('kasir_name', '').strip()

    promo_id = data.get('promo_id')

    # Poin yang mau ditukar (list of PointReward id, bisa ada duplikat kalau
    # customer nuker reward yang sama lebih dari 1x)
    redeem_reward_ids = data.get('redeem_reward_ids') or []

    raw_payment_status = data.get('payment_status', '')

    # Logika payment_status
    is_qris = payment_method in ('qris', 'qris_manual', 'gateway')
    proof_image_url = (data.get('proof_image_url') or '').strip()

    if source == 'web' and is_qris and not proof_image_url:
        return Response({"error": "Bukti pembayaran QRIS wajib diupload"}, status=400)

    if source == 'web':
        if is_qris:
            # Web + QRIS → JANGAN langsung 'paid'. Nunggu admin cek manual
            # bukti pembayaran (proof_image_url) lewat endpoint verify-payment
            # sebelum order dianggap lunas & masuk laporan omzet.
            payment_status = 'pending_verification'
            is_deferred    = False
            order_status   = 'pending'
        else:
            # Web + cash → pending seperti biasa
            payment_status = 'pending'
            is_deferred    = False
            order_status   = 'pending'
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
    # ASUMSI field Promo: is_active, used_count, discount_type
    # ('percentage'/'fixed'), discount_value, max_discount_amount, quota.
    # SESUAIKAN kalau struktur promotions.models.Promo lo beda.
    promo_obj = None
    if promo_id:
        promo_obj = Promo.objects.select_for_update().filter(pk=promo_id, is_active=True).first()
        if not promo_obj:
            return Response({"error": "Promo tidak valid atau sudah tidak aktif"}, status=400)

        quota = getattr(promo_obj, "quota", None)
        if quota is not None and promo_obj.used_count >= quota:
            return Response({"error": "Kuota promo sudah habis"}, status=400)

    # ── Bikin Order dulu (item & payment nyusul, biar dapet FK) ─────
    order = Order.objects.create(
        source=source,
        status=order_status,
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
        quantity   = int(item.get('quantity', 1) or 1)
        item_notes = (item.get('notes') or '').strip()

        if not menu_id or quantity <= 0:
            transaction.set_rollback(True)
            return Response({"error": "Data item tidak valid (menu_id/quantity)"}, status=400)

        menu = get_object_or_404(Menu, pk=menu_id)

        # Web pakai harga markup 1% (dibulatkan ke atas kelipatan 500),
        # POS pakai harga normal.
        if source == 'web':
            marked_up = float(menu.price) * 1.01
            price = Decimal(int(math.ceil(marked_up / 500) * 500))
        else:
            price = menu.price

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
    promo_discount_amount = Decimal('0')
    if promo_obj:
        discount_type  = getattr(promo_obj, 'discount_type', 'fixed')
        discount_value = Decimal(str(getattr(promo_obj, 'discount_value', 0) or 0))

        if discount_type == 'percentage':
            promo_discount_amount = subtotal * discount_value / Decimal('100')
            max_discount = getattr(promo_obj, 'max_discount_amount', None)
            if max_discount:
                promo_discount_amount = min(promo_discount_amount, Decimal(str(max_discount)))
        else:
            promo_discount_amount = discount_value

        promo_discount_amount = min(promo_discount_amount, subtotal)
        Promo.objects.filter(pk=promo_obj.pk).update(used_count=models.F('used_count') + 1)

    order.subtotal              = subtotal
    order.promo_discount_amount = promo_discount_amount
    total = subtotal - promo_discount_amount
    order.total_price = total if total > 0 else Decimal('0')

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
# HAPUS PERMANEN — helper (dipakai oleh get_order saat method DELETE)
# ─────────────────────────────────────────────
# Beda dari cancel_order (void): cancel_order cuma ubah status, row Order
# tetap ada buat audit. Ini beneran ngilangin row Order dari DB (+
# OrderItem/OrderPayment ikut CASCADE) — dipakai buat kasus salah input
# yang baru ketauan belakangan, duplikat, dsb, TERMASUK order yang sudah
# completed/paid.
#
# Karena ini destruktif & permanen, sebelum row-nya beneran hilang kita:
#   1. Reverse poin loyalty yang sudah kadung di-earn dari order ini
#      (kalau order.loyalty_applied True) — di-clamp ke 0, tidak dipaksa
#      minus, kalau saldo customer sekarang sudah lebih kecil dari yang
#      seharusnya di-reverse (kemungkinan sudah kepakai buat redeem lain).
#   2. Reverse kuota promo (used_count) kalau order ini pakai promo.
#   3. Simpan snapshot lengkap ke OrderDeletionLog, biar tetap ada jejak
#      audit meskipun row Order-nya sendiri sudah hilang.
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

    # ── Reverse poin loyalty — HANYA kalau order ini memang pernah
    # trigger penambahan poin (loyalty_applied), biar nggak salah
    # mengurangi poin dari order yang belum pernah completed.
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

            # Recompute last_order_at dari order completed LAIN milik
            # customer ini (selain yang mau dihapus), biar estimasi
            # kedaluwarsa poin tetap akurat.
            other_last_order = (
                Order.objects.filter(customer_phone=order.customer_phone, status="completed")
                .exclude(pk=order.pk)
                .aggregate(latest=Max("created_at"))["latest"]
            )
            loyalty.last_order_at = other_last_order

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

    # ── Reverse kuota promo ──────────────────────────────────────────
    promo_code_reverted = ""
    if order.promo_id:
        Promo.objects.filter(pk=order.promo_id).update(used_count=models.F("used_count") - 1)
        promo_code_reverted = getattr(order.promo, "code", str(order.promo_id))

    # ── Simpan snapshot audit SEBELUM row-nya kehapus ────────────────
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
        # IsAdminUser di atas cuma cek is_staff (akses admin panel secara
        # umum) — BUKAN role owner spesifik. Hapus permanen cuma boleh
        # role owner, jadi dicek manual di sini juga, biar request langsung
        # ke API (bypass tombol UI) tetap ke-block.
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
      - is_member       → True kalau nomor ini udah pernah tercatat di CustomerLoyalty
      - points          → saldo poin aktif saat ini (udah lewat cek hangus)
      - points_expiring_note → pesan kalau poin baru aja hangus atau kapan estimasi hangusnya
    """
    phone = request.query_params.get("phone", "").strip()
    if not phone:
        return Response({"is_member": False, "points": 0, "points_expiring_note": None})

    loyalty = CustomerLoyalty.objects.filter(phone=phone).first()
    if not loyalty:
        return Response({"is_member": False, "points": 0, "points_expiring_note": None})

    # Cek hangus SEBELUM ditampilkan, biar customer selalu liat saldo yang akurat
    # real-time — bukan cuma pas order baru selesai.
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
# POINT REWARDS — PUBLIK (cek saldo + rekomendasi tukar)
# ─────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def available_point_rewards(request):
    """
    GET /api/orders/point-rewards/available/?phone=08xxx

    Response:
      - points: saldo poin customer saat ini (0 kalau belum punya akun loyalty)
      - affordable: reward yang poinnya udah cukup buat ditukar sekarang,
        diurutkan dari yang paling MAHAL dulu (biar customer liat reward
        paling worth-it dari poinnya, bukan yang termurah/paling gampang).
      - locked: HANYA reward yang paling DEKAT ke saldo poin customer
        (missing_points paling kecil), dibatasi max 5 — bukan seluruh
        katalog. Ini biar rekomendasinya kerasa relevan/achievable ("dikit
        lagi!"), bukan nge-dump semua menu yang masih jauh dari jangkauan.
    """
    phone = request.query_params.get("phone", "").strip()
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

    # Affordable: yang paling mahal (paling "untung" buat ditukar) duluan.
    affordable.sort(key=lambda pair: pair[0], reverse=True)
    # Locked: yang paling DEKAT (missing_points paling kecil) duluan,
    # dibatasi 5 biar rekomendasinya fokus & achievable.
    locked.sort(key=lambda pair: pair[0])

    LOCKED_RECOMMENDATION_LIMIT = 5

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

    qs = Order.objects.all()
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

        paid_qs = Order.objects.filter(
            payment_status='paid',
        ).exclude(status='cancelled')

        if date_from:
            paid_qs = paid_qs.filter(created_at__date__gte=date_from)
        if date_to:
            paid_qs = paid_qs.filter(created_at__date__lte=date_to)

        paid_stats = paid_qs.aggregate(
            total_revenue=Sum("total_price"),
            total_orders=Count("id"),
        )

        all_qs = Order.objects.all()
        if date_from:
            all_qs = all_qs.filter(created_at__date__gte=date_from)
        if date_to:
            all_qs = all_qs.filter(created_at__date__lte=date_to)

        pending   = all_qs.filter(status="pending").count()
        completed = all_qs.filter(status="completed").count()

        top_menu_qs = OrderItem.objects.filter(
            order__payment_status='paid',
        ).exclude(order__status='cancelled')

        if date_from:
            top_menu_qs = top_menu_qs.filter(order__created_at__date__gte=date_from)
        if date_to:
            top_menu_qs = top_menu_qs.filter(order__created_at__date__lte=date_to)

        top_menus = (
            top_menu_qs
            .values("menu__name")
            .annotate(
                total_qty=Sum("quantity"),
                total_revenue=Sum(
                    models.ExpressionWrapper(
                        models.F("price") * models.F("quantity"),
                        output_field=models.DecimalField(),
                    )
                ),
            )
            .order_by("-total_qty")[:5]
        )

        # Member loyal sekarang cuma soal "punya poin aktif atau enggak",
        # gak ada lagi hitungan tier min_orders/min_spending.
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
    from django.db.models.functions import TruncMonth, ExtractMonth

    year = int(request.query_params.get("year", timezone.now().year))

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
    Mengembalikan pendapatan & pengeluaran per hari dalam satu bulan.
    """
    from django.db.models.functions import TruncDate

    year  = int(request.query_params.get("year",  timezone.now().year))
    month = int(request.query_params.get("month", timezone.now().month))

    revenue_qs = (
        Order.objects
        .filter(
            created_at__year=year,
            created_at__month=month,
            payment_status='paid',
        )
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
    Sekarang sumber datanya langsung dari CustomerLoyalty (bukan agregasi
    Order lagi) — karena points/total_spent/total_orders/last_order_at
    semua udah kesimpen di sana secara real-time lewat signal tiap order
    completed. Ngga ada lagi konsep "LOYAL MEMBER vs REGULAR" berdasarkan
    tier — semua customer yang punya poin ya ditampilin apa adanya.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        settings  = LoyaltySettings.get_settings()
        customers = []

        for cl in CustomerLoyalty.objects.all().order_by('-points'):
            customers.append({
                "phone":            cl.phone,
                "name":             cl.name,
                "points":           cl.points,
                "total_orders":     cl.total_orders,
                "total_spent":      cl.total_spent,
                "last_order_at":    cl.last_order_at,
                "expiry_estimate":  cl.expiry_estimate_date(),
                "points_expired":   cl.points_expired(),
            })

        return Response({
            "settings":  LoyaltySettingsSerializer(settings).data,
            "customers": customers,
        })


class AdjustPointsView(APIView):
    """
    Pengganti GiveSpecialPriceView lama. Dulu admin kasih "diskon spesial %"
    per customer — sekarang diganti adjust poin manual (nambah/mengurangi),
    dengan alasan wajib diisi & tercatat sebagai PointAdjustment (audit log),
    bukan cuma angka yang berubah tanpa jejak.
    """
    permission_classes = [IsAdminUser]

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

        loyalty, _ = CustomerLoyalty.objects.get_or_create(
            phone=phone,
            defaults={'name': request.data.get('name', '')},
        )

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

        return Response({
            'phone':  phone,
            'points': loyalty.points,
        })


# ─────────────────────────────────────────────
# UNPAID ORDERS & HISTORY
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

    return Response(
        OrderSerializer(qs.order_by("-created_at"), many=True).data
    )


@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def pay_order(request, pk):
    """
    Melunasi order. Mendukung 2 format request:

    1. FORMAT BARU (split bill / multi-payment) — kirim list `payments`:
       { "payments": [{"method": "cash", "amount": 5000}, {"method": "qris_manual", "amount": 8000}],
         "kasir_name": "Budi" }
       Dipakai kalau bayarnya dicampur beberapa metode, atau dibagi
       beberapa orang (tiap orang jadi satu baris payments).

    2. FORMAT LAMA (satu metode, satu jumlah) — tetap didukung biar
       kompatibel sama caller lain yang belum diupdate:
       { "payment_method": "cash", "amount_paid": 20000, "kasir_name": "Budi" }
    """
    order = get_object_or_404(Order, pk=pk)
    previous_status = order.status

    kasir_name    = (request.data.get('kasir_name') or '').strip()
    payments_data = request.data.get('payments')

    if payments_data:
        # ── Format baru: banyak baris pembayaran ──
        parsed_rows = []
        for row in payments_data:
            method = (row.get('method') or '').strip()
            try:
                amount = Decimal(str(row.get('amount', 0) or 0))
            except Exception:
                return Response({"detail": "Nominal pembayaran tidak valid."}, status=400)

            valid_methods = {choice[0] for choice in PAYMENT_METHOD_CHOICES if choice[0] != 'mixed'}
            if method not in valid_methods:
                return Response({"detail": f"Metode pembayaran '{method}' tidak valid."}, status=400)
            if amount <= 0:
                return Response({"detail": "Nominal tiap baris pembayaran harus lebih dari 0."}, status=400)

            parsed_rows.append((method, amount))

        if not parsed_rows:
            return Response({"detail": "Minimal harus ada satu baris pembayaran."}, status=400)

        total_paid = sum(amount for _, amount in parsed_rows)
        if total_paid < order.total_price:
            return Response(
                {"detail": "Total pembayaran belum menutupi tagihan."},
                status=400,
            )

        # Hapus baris pembayaran lama kalau ini pengulangan (mis. retry), biar gak dobel.
        order.payments.all().delete()
        for method, amount in parsed_rows:
            OrderPayment.objects.create(order=order, method=method, amount=amount)

        distinct_methods = {method for method, _ in parsed_rows}
        order.payment_method = "mixed" if len(distinct_methods) > 1 else next(iter(distinct_methods))
        order.amount_paid     = total_paid
        order.change_amount   = max(total_paid - order.total_price, Decimal('0'))

    else:
        # ── Format lama: satu metode, satu jumlah ──
        amount_paid = Decimal(str(request.data.get('amount_paid', 0) or 0))
        method = request.data.get("payment_method") or order.payment_method or "cash"

        order.payments.all().delete()
        OrderPayment.objects.create(
            order=order, method=method,
            amount=amount_paid if amount_paid > 0 else order.total_price,
        )

        order.payment_method = method
        order.amount_paid     = amount_paid
        if amount_paid > 0:
            order.change_amount = max(amount_paid - order.total_price, Decimal('0'))

    order.payment_status = "paid"
    order.status         = "completed"
    order.kasir_name     = kasir_name or order.kasir_name

    order._previous_status = previous_status
    order.save()
    order.refresh_from_db()

    return Response({
        "success":       True,
        "order_number":  order.order_number,
        "change_amount": float(order.change_amount),
        "amount_paid":   float(order.amount_paid),
        "payment_method": order.payment_method,
    })

@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def verify_qris_payment(request, pk):
    """
    PATCH /api/orders/<id>/verify-payment/
    Body: { "approve": true/false, "kasir_name": "...", "reject_note": "..." }

    Dipanggil admin setelah ngecek proof_image_url order yang statusnya
    'pending_verification'. approve=true → order dianggap lunas
    (paid+completed). approve=false → order dibatalkan, dianggap
    pembayaran tidak valid.
    """
    order = get_object_or_404(Order, pk=pk)

    if order.payment_status != 'pending_verification':
        return Response(
            {"detail": "Order ini bukan status menunggu verifikasi."},
            status=400,
        )

    approve    = request.data.get('approve', True)
    kasir_name = (request.data.get('kasir_name') or '').strip()
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
def cancel_order(request, pk):
    """
    Void/batalkan order dengan alasan wajib — dipakai kalau order salah
    input, pelanggan batal, dsb. Order TIDAK dihapus dari database, cuma
    diubah statusnya jadi 'cancelled' + dicatat alasannya, biar tetap ada
    jejak buat audit/laporan (gak ada transaksi yang tiba-tiba hilang).
    """
    order = get_object_or_404(Order, pk=pk)
    previous_status = order.status

    if order.status == "completed":
        return Response(
            {"detail": "Order yang sudah selesai (completed) tidak bisa dibatalkan lewat sini."},
            status=400,
        )
    if order.status == "cancelled":
        return Response(
            {"detail": "Order ini sudah dibatalkan sebelumnya."},
            status=400,
        )

    reason = (request.data.get("cancel_reason") or "").strip()
    valid_reasons = {choice[0] for choice in CANCEL_REASON_CHOICES}
    if reason not in valid_reasons:
        return Response(
            {"detail": "Alasan pembatalan wajib diisi dan harus valid."},
            status=400,
        )

    note       = (request.data.get("cancel_note") or "").strip()
    kasir_name = (request.data.get("kasir_name") or "").strip()

    order.status         = "cancelled"
    order.payment_status = "void"
    order.cancel_reason  = reason
    order.cancel_note    = note
    order.cancelled_at   = timezone.now()
    order.cancelled_by   = kasir_name

    order._previous_status = previous_status
    order.save()
    order.refresh_from_db()

    return Response({
        "success":      True,
        "order_number": order.order_number,
        "status":       order.status,
        "cancel_reason": order.cancel_reason,
    })

NOTIFICATION_BACKLOG_SKIP_THRESHOLD = 50

@api_view(["GET"])
@permission_classes([IsAdminUser])
def new_order_notifications(request):
    """
    GET /api/orders/notifications/?after_id=123
 
    Polling ringan (bukan full order list) buat deteksi order BARU masuk
    sejak id terakhir yang udah diketahui frontend. Dipakai admin dashboard
    buat munculin toast + suara notifikasi tanpa nge-refetch semua data
    order tiap beberapa detik.
 
    - Order dari POS (source='pos') di-exclude, karena itu diinput admin
      sendiri di tempat — gak perlu notif ke diri sendiri.
    - Kalau `after_id` gak dikirim (pemanggilan pertama kali pas dashboard
      dibuka), balikin new_orders kosong — cuma ngasih tau `latest_id`
      sebagai starting point. Ini penting biar order-order lama yang udah
      ada dari sebelumnya gak ikut ke-notif ulang tiap kali admin refresh
      halaman/pindah tab.
    - Kalau gap antara after_id dan latest_id kelewat gede (lihat
      NOTIFICATION_BACKLOG_SKIP_THRESHOLD), dianggap bulk insert, bukan
      order beneran — cursor di-jump langsung, `backlog_skipped: True`
      dikasih tau ke frontend biar bisa kasih pesan yang sesuai (bukan
      diem-diem aja, biar admin ngerti kenapa gak ada toast satu-satu).
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
            'id':             o.id,
            'order_number':   o.order_number,
            'customer_name':  o.customer_name or 'Pelanggan',
            'total_price':    o.total_price,
            'source':         o.source,
            'created_at':     o.created_at,
        }
        for o in new_orders_qs
    ]
    return Response({'new_orders': data, 'latest_id': latest_id})


@api_view(["GET"])
@permission_classes([IsAdminUser])
def order_history(request):
    """
    GET /api/orders/history/?period=today|week|month
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
        year  = request.query_params.get("year",  now.year)
        month = request.query_params.get("month", now.month)
        qs    = qs.filter(
            created_at__year=int(year),
            created_at__month=int(month),
        )

    elif period == "year":
        year = request.query_params.get("year", now.year)
        qs   = qs.filter(created_at__year=int(year))

    return Response(
        OrderSerializer(qs.order_by("-created_at"), many=True).data
    )


@api_view(["GET"])
@permission_classes([IsAdminUser])
def order_full_report(request):
    from django.db.models.functions import ExtractHour, TruncDate, TruncMonth

    period = request.query_params.get("period", "lifetime")
    now    = timezone.now()
    year   = int(request.query_params.get("year",  now.year))
    month  = int(request.query_params.get("month", now.month))
    days   = int(request.query_params.get("days",  7))
    offset = int(request.query_params.get("offset", 0))

    if days not in (7, 14, 28, 30):
        days = 7

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
    qualifying_qs = Order.objects.filter(payment_status="paid").exclude(status="cancelled")
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
    base_trend_qs = (
        Order.objects.filter(payment_status="paid").exclude(status="cancelled")
    )

    if period == "year":
        BULAN_ID = ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"]
        trend_qs = (
            base_trend_qs
            .filter(created_at__date__gte=period_start, created_at__date__lte=period_end)
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
            base_trend_qs
            .filter(created_at__date__gte=period_start, created_at__date__lte=period_end)
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

        HARI_ID = ["Sen","Sel","Rab","Kam","Jum","Sab","Min"]
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
            base_trend_qs
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
        .annotate(
            qty=Sum("quantity"),
            omzet=Sum(
                models.ExpressionWrapper(
                    models.F("price") * models.F("quantity"),
                    output_field=models.DecimalField(),
                )
            ),
        )
        .order_by("-qty")[:10]
    )
    top_by_omzet = list(
        base_item_qs.values("menu__name")
        .annotate(
            omzet=Sum(
                models.ExpressionWrapper(
                    models.F("price") * models.F("quantity"),
                    output_field=models.DecimalField(),
                )
            ),
        )
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
            Order.objects.filter(payment_status="paid")
            .exclude(status="cancelled")
            .exclude(customer_phone="")
            .values("customer_phone")
            .annotate(first_date=models.Min("created_at"))
        )
    }
    phones_in_period = (
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

    # Member loyal sekarang = customer yang punya poin aktif (bukan tier
    # min_orders/min_spending atau override diskon manual lagi).
    per_phone_stats = qualifying_qs.exclude(customer_phone="").values_list(
        "customer_phone", flat=True
    ).distinct()
    member_loyal = CustomerLoyalty.objects.filter(
        phone__in=list(per_phone_stats), points__gt=0
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
            "mode":   period,
            "year":   year,
            "month":  month,
            "days":   days,
            "start":  str(period_start) if period_start else None,
            "end":    str(period_end)   if period_end   else None,
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
        "menu_tidak_laku": menu_tidak_laku,
        "metode_pembayaran": metode_pembayaran,
        "pelanggan": {
            "baru":         pelanggan_baru,
            "lama":         pelanggan_lama,
            "loyal_member": member_loyal,
        },
        "jam_teramai": jam_teramai,
    })

class StoreSettingsView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdminUser()]
 
    def get(self, request):
        settings = StoreSettings.get()
        return Response(StoreSettingsSerializer(settings).data)
 
    def put(self, request):
        settings   = StoreSettings.get()
        serializer = StoreSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)