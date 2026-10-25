import calendar
import datetime
import re
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import (
    Count, DecimalField, ExpressionWrapper, F, Max, Min, Q, Sum,
)
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from accounts.permissions import IsAdminLevel, IsStaffLevel
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.models import Expense
from menu import bundles as bundle_logic
from menu.models import Menu, MenuBundle
from menu.options import resolve_selection, OptionError
from promotions.models import Promo  # validasi & kunci kuota server-side saat create_order
from payments.services import cancel_midtrans_transaction
from .pricing import web_price
from . import member_pin
from .crowd import to_wib
from .segmentation import segment_overview
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
    WIB,
    kitchen_open_q,
)
from .serializers import (
    LoyaltySettingsSerializer,
    OrderSerializer,
    PointRewardSerializer,
    StoreSettingsSerializer,
    reset_late_minutes_cache,
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

def _orderable_problem(menu, source, backdated=False):
    """
    Pesan error kalau menu TIDAK boleh dipesan dari source ini, atau None kalau aman.
    - Web: secret & nonaktif ditolak (pesan generik, nama secret menu tidak dibocorkan).
    - Web DAN POS: menu yang ditandai habis (is_available=False) ditolak. Dicek di server,
      bukan cuma di tampilan, supaya tidak bisa lolos lewat tab lama / POST langsung.
    - POS lainnya (secret / nonaktif) tidak dibatasi, kasir yang menentukan.
    - backdated=True (input susulan order lama): menu habis TIDAK ditolak, karena saat
      kejadian aslinya menu itu memang masih ada.
    """
    if source == "web":
        if menu.is_secret or not menu.is_active:
            return "Ada menu di keranjang yang sudah tidak tersedia. Kosongkan keranjang lalu pilih ulang."
    if not menu.is_available and not backdated:
        if source == "web":
            return f"Menu {menu.name} sedang habis."
        return f"Menu {menu.name} sedang habis. Aktifkan lagi di Kelola Menu kalau stoknya sudah ada."
    return None


def _join_notes(option_text, free_text):
    """Gabung teks pilihan opsi + catatan bebas jadi satu string (maks 255 karakter)."""
    parts = [p for p in ((option_text or "").strip(), (free_text or "").strip()) if p]
    return " · ".join(parts)[:255]


# ─────────────────────────────────────────────
# ORDERS — CRUD
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# WAKTU ORDER MANUAL (input susulan)
# ─────────────────────────────────────────────
# Kasus: order salah input baru ketahuan di hari lain. Admin (staff) boleh
# menginput ulang order dengan tanggal & jam sesuai kejadian aslinya, jadi
# order masuk ke laporan hari itu dan tampil berurutan menurut jam di
# Active Orders. Cuma untuk source='pos' yang dikirim staff login.
BACKDATE_MAX_DAYS         = 366   # batas mundur — jaga dari salah ketik tahun
BACKDATE_FUTURE_TOLERANCE = timedelta(minutes=2)
BACKDATE_NOW_TOLERANCE    = timedelta(minutes=2)   # selisih sekecil ini dianggap "sekarang"


def _parse_backdate(raw):
    """
    Return (datetime_aware | None, error | None).
    None tanpa error = pakai waktu sekarang (kosong / selisih < 2 menit dari sekarang).
    """
    if raw in (None, ""):
        return None, None

    try:
        dt = parse_datetime(str(raw))
    except ValueError:
        dt = None
    if dt is None:
        return None, "Format tanggal/jam order tidak valid."
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, WIB)   # tanpa offset = dianggap WIB

    now = timezone.now()
    if dt > now + BACKDATE_FUTURE_TOLERANCE:
        return None, "Waktu order tidak boleh di masa depan."
    if dt < now - timedelta(days=BACKDATE_MAX_DAYS):
        return None, f"Waktu order terlalu lama (maksimal {BACKDATE_MAX_DAYS} hari ke belakang). Cek tahunnya."
    if dt >= now - BACKDATE_NOW_TOLERANCE:
        return None, None
    return dt, None


# Nomor WhatsApp order web: hanya angka, diawali 08, 10-13 digit.
# Aturan yang sama dipakai di frontend (src/utils/phone.js); di sini dicek ulang karena
# request bisa dikirim langsung tanpa lewat form. Order POS (kasir) tidak dibatasi.
WEB_PHONE_RE = re.compile(r'^08\d{8,11}$')
CUSTOMER_NAME_MAX = 100   # = max_length Order.customer_name

# Nama order web: hanya huruf dan spasi, 3-50 karakter (aturan sama dengan src/utils/name.js).
WEB_NAME_RE = re.compile(r'^[^\W\d_]+(?: [^\W\d_]+)*$')
WEB_NAME_MIN, WEB_NAME_MAX = 3, 50


def _web_name_error(name):
    """Pesan error untuk nama order web, atau None kalau valid."""
    letters = name.replace(' ', '')
    if not WEB_NAME_RE.match(name) or not (WEB_NAME_MIN <= len(letters) and len(name) <= WEB_NAME_MAX):
        return "Nama harus 3-50 karakter, hanya huruf dan spasi"
    if re.search(r'(.)\1\1', name, re.IGNORECASE) or not re.search(r'[aiueo]', name, re.IGNORECASE):
        return "Nama tidak valid"
    return None


@api_view(['POST'])
@permission_classes([AllowAny])
@transaction.atomic
def create_order(request):
    data       = request.data
    items_data = data.get('items') or []
    # Menu Paket: [{"bundle_id": 3, "quantity": 2}]. Harga dihitung server (menu/bundles.py).
    bundles_data = data.get('bundles') or []

    if not items_data and not bundles_data:
        return Response({"error": "Items kosong"}, status=400)
    if not isinstance(bundles_data, list) or not isinstance(items_data, list):
        return Response({"error": "Format items/bundles tidak valid"}, status=400)

    customer_data = data.get('customer') or {}
    phone = (customer_data.get('phone') or data.get('customer_phone', '') or '').strip()
    name  = ' '.join((customer_data.get('name') or data.get('customer_name', '') or '').split())

    source         = data.get('source', 'pos')
    payment_method = data.get('payment_method', 'cash')

    # PENTING: source='pos' cuma boleh dipercaya kalau request ini beneran
    # datang dari staff yang login. Tanpa ini, siapa pun tanpa login bisa
    # POST /orders/ langsung dengan source='pos' dan order-nya otomatis
    # ke-mark 'paid'+'completed' di bawah — bypass total alur web/QRIS.
    if source == 'pos' and not (request.user and request.user.is_authenticated and request.user.is_staff):
        source = 'web'

    if source == 'web':
        name_error = _web_name_error(name)
        if name_error:
            return Response({"error": name_error}, status=400)
    name = name[:CUSTOMER_NAME_MAX]

    if source == 'web' and not WEB_PHONE_RE.match(phone):
        return Response(
            {"error": "Nomor WhatsApp harus diawali 08 dan terdiri dari 10-13 digit angka"},
            status=400,
        )

    # Gateway (Midtrans): order web, atau order POS yang dibayar QRIS dinamis
    # (QR ditampilkan kasir ke pelanggan, lunas otomatis lewat webhook).
    pos_gateway = source == 'pos' and payment_method == 'gateway'

    # Order web cuma boleh: cash (bayar di kasir) atau gateway (Midtrans).
    # QRIS manual + upload bukti sudah dihapus.
    if source == 'web' and payment_method not in ('cash', 'gateway'):
        return Response(
            {"error": "Metode pembayaran web hanya cash atau gateway"}, status=400
        )

    # Waktu order manual — HANYA berlaku untuk source='pos' (di titik ini sudah
    # dipastikan staff login). Dari order web / tanpa login, created_at diabaikan.
    backdated_at = None
    if source == 'pos':
        backdated_at, backdate_error = _parse_backdate(data.get('created_at'))
        if backdate_error:
            return Response({"error": backdate_error}, status=400)
        if pos_gateway and backdated_at:
            return Response({"error": "Input susulan tidak bisa dibayar QRIS otomatis. Pakai Cash atau QRIS Manual."}, status=400)
    time_fields = (
        {"created_at": backdated_at, "entered_at": timezone.now()} if backdated_at else {}
    )

    table_number = data.get('table_number')
    notes        = data.get('notes', '')

    service_type = data.get('service_type') or 'dine_in'
    if service_type not in ('dine_in', 'takeaway'):
        return Response({"error": "service_type harus dine_in atau takeaway"}, status=400)

    try:
        amount_paid = Decimal(str(data.get('amount_paid', 0) or 0))
    except Exception:
        return Response({"error": "amount_paid tidak valid"}, status=400)
    kasir_name = (data.get('kasir_name') or '').strip()

    promo_id = data.get('promo_id')

    # Poin yang mau ditukar (list of PointReward id, bisa ada duplikat kalau
    # customer nuker reward yang sama lebih dari 1x)
    redeem_reward_ids = data.get('redeem_reward_ids') or []

    # Tukar poin dari WEB wajib PIN member (dicek di server, bukan hanya di frontend). Kasir (POS)
    # tidak memakai PIN. Dicek SEBELUM ada data ditulis dan tanpa set_rollback, supaya hitungan
    # salah/kunci tetap tersimpan.
    if redeem_reward_ids and source == 'web':
        if not member_pin.verify_pin(phone, data.get('member_pin')):
            return Response({"error": member_pin.NEUTRAL_ERROR, "pin_error": True}, status=403)

    raw_payment_status = data.get('payment_status', '')

    is_qris = payment_method in ('qris', 'qris_manual')   # QRIS di kasir (POS)

    if source == 'web' or pos_gateway:
        # Web / POS + gateway → 'pending' sampai webhook Midtrans bilang settlement.
        # Web + cash    → 'pending' sampai kasir melunasi di toko.
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
        service_type=service_type,
        customer_name=name,
        customer_phone=phone,
        table_number=table_number,
        notes=notes,
        kasir_name=kasir_name,
        promo=promo_obj,
        **time_fields,
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

        menu = get_object_or_404(Menu, pk=menu_id)

        problem = _orderable_problem(menu, source, backdated=bool(backdated_at))
        if problem:
            transaction.set_rollback(True)
            return Response({"error": problem}, status=400)

        # Pilihan opsi divalidasi terhadap data menu di database; harga add-on dihitung di sini,
        # bukan dipercaya dari client. Add-on tidak kena markup web.
        try:
            chosen, extra_price, option_text = resolve_selection(menu, item.get('options'))
        except OptionError as e:
            transaction.set_rollback(True)
            return Response({"error": str(e)}, status=400)

        price = _price_for(source, menu) + extra_price

        OrderItem.objects.create(
            order=order, menu=menu, quantity=quantity,
            price=price, notes=_join_notes(option_text, item_notes),
            selected_options=chosen,
        )
        subtotal += price * quantity

    # ── Menu Paket: dipecah jadi item biasa, total = harga paket ─────
    for entry in bundles_data:
        try:
            bundle_id = int(entry.get('bundle_id'))
            # quantity 0 harus DITOLAK (bukan diam-diam jadi 1), jadi jangan pakai `or 1`.
            raw_qty = entry.get('quantity', 1)
            bundle_qty = int(1 if raw_qty is None else raw_qty)
        except (TypeError, ValueError, AttributeError):
            transaction.set_rollback(True)
            return Response({"error": "Data paket tidak valid (bundle_id/quantity)"}, status=400)
        if bundle_qty <= 0 or bundle_qty > 50:
            transaction.set_rollback(True)
            return Response({"error": "Jumlah paket tidak valid"}, status=400)

        bundle = MenuBundle.objects.prefetch_related('items__menu').filter(pk=bundle_id).first()
        if not bundle:
            transaction.set_rollback(True)
            return Response({"error": "Ada paket di keranjang yang sudah tidak tersedia. Kosongkan keranjang lalu pilih ulang."}, status=400)
        problem = bundle_logic.unavailable_reason(bundle, source)
        if problem:
            transaction.set_rollback(True)
            return Response({"error": f"Paket {bundle.name}: {problem}"}, status=400)

        for menu, unit, qty in bundle_logic.order_rows(bundle, bundle_qty, source):
            OrderItem.objects.create(
                order=order, menu=menu, quantity=qty, price=unit, bundle_name=bundle.name,
            )
            subtotal += unit * qty

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

            if reward.menu and _orderable_problem(reward.menu, source, backdated=bool(backdated_at)):
                transaction.set_rollback(True)
                return Response({"error": "Salah satu reward tidak tersedia saat ini"}, status=400)

            # Reward = 1 porsi gratis tanpa opsi (menu beropsi wajib tetap boleh ditukar; pilihan default kosong).
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
        payment_row = OrderPayment.objects.create(
            order=order,
            method=order.payment_method,
            amount=order.amount_paid or order.total_price,
        )
        if backdated_at:
            # created_at pembayaran auto_now_add (selalu "sekarang"); untuk order
            # input susulan yang langsung lunas, waktu bayar = waktu order.
            OrderPayment.objects.filter(pk=payment_row.pk).update(created_at=order.created_at)

    order.refresh_from_db()
    return Response(OrderSerializer(order).data, status=201)


# Order gateway (Midtrans) yang belum pernah lunas = belum "resmi masuk" ke
# operasional (checkout QRIS yang popup-nya ditutup / kedaluwarsa).
# amount_paid=0 supaya order gateway yang sudah dibayar lalu dibatalkan
# (refund) tetap kelihatan di admin.
GATEWAY_NOT_PAID_Q = (
    Q(payment_method="gateway", amount_paid=0) & ~Q(payment_status="paid")
)


@api_view(["GET"])
@permission_classes([IsAdminLevel])
def list_orders(request):
    orders = (
        Order.objects
        .exclude(GATEWAY_NOT_PAID_Q)
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
# Semua efek order ini dibalikkan, sesuai isi nota yang dihapus:
#   1. Menu (OrderItem, termasuk baris pecahan paket) dan pembayaran
#      (OrderPayment: metode, nominal, split bill) ikut terhapus (CASCADE).
#   2. Poin loyalty yang DIPAKAI buat tukar reward dikembalikan ke saldo.
#   3. Poin loyalty yang di-EARN dari order ini ditarik balik (di-clamp ke 0),
#      beserta total belanja & jumlah order customer.
#   4. Kuota promo (used_count) dikembalikan kalau order ini pakai promo.
#   5. Transaksi Midtrans yang masih menunggu bayar ditutup (QR lama tidak bisa dibayar).
#   6. Snapshot lengkap disimpan ke OrderDeletionLog sebagai jejak audit.
#
# Return: dict ringkasan (dipakai buat pesan ke kasir).
@transaction.atomic
def _delete_order_permanently(order, deleted_by=""):
    items = list(order.items.select_related("menu").all())
    payments = list(order.payments.all())

    items_snapshot = [
        {
            "menu_name": item.menu.name if item.menu else "(menu dihapus)",
            "quantity": item.quantity,
            "price": float(item.price),
            "notes": item.notes,
            "is_point_redemption": item.is_point_redemption,
            "bundle_name": item.bundle_name,
            "selected_options": item.selected_options,
        }
        for item in items
    ]
    payments_snapshot = [{"method": p.method, "amount": float(p.amount)} for p in payments]

    has_redemption = any(i.is_point_redemption for i in items)
    was_gateway_pending = order.payment_method == "gateway" and order.payment_status == "pending"
    gateway_paid = any(p.method == "gateway" for p in payments)

    loyalty_points_reverted = 0
    loyalty_points_refunded = 0
    loyalty_clamped = False

    # Satu kali lock customer untuk refund + reversal, supaya saldo akhirnya konsisten.
    loyalty = None
    if order.customer_phone and (order.loyalty_applied or has_redemption):
        loyalty = CustomerLoyalty.objects.select_for_update().filter(
            phone=order.customer_phone
        ).first()

    if loyalty:
        adjustments = []

        # (2) Kembalikan poin yang dipakai buat tukar reward di order ini. Jumlahnya diambil dari
        # catatan potongan saat order dibuat (bukan dihitung ulang dari point_cost sekarang,
        # yang bisa saja sudah diubah admin). Dilakukan SEBELUM reversal poin earn supaya
        # saldo tidak ke-clamp padahal poinnya sebenarnya cukup.
        if has_redemption:
            spent = PointAdjustment.objects.filter(
                customer=loyalty,
                amount__lt=0,
                note__startswith=f"Redeem reward saat order {order.order_number}",
            ).aggregate(total=Sum("amount"))["total"] or 0
            loyalty_points_refunded = -spent
            if loyalty_points_refunded > 0:
                loyalty.points += loyalty_points_refunded
                adjustments.append((
                    loyalty_points_refunded,
                    f"Poin tukar reward dikembalikan — order {order.order_number} dihapus permanen",
                ))

        # (3) Tarik balik poin yang di-earn HANYA kalau order ini memang pernah menambah poin.
        if order.loyalty_applied:
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

            if loyalty_points_reverted:
                adjustments.append((
                    -loyalty_points_reverted,
                    f"Reversal otomatis — order {order.order_number} dihapus permanen"
                    + (" (poin di-clamp ke 0, saldo sudah kurang dari yang di-reverse)" if loyalty_clamped else ""),
                ))

        loyalty.save()

        for amount, note in adjustments:
            PointAdjustment.objects.create(
                customer=loyalty,
                amount=amount,
                reason="manual",
                note=note,
                admin_name=deleted_by or "system",
            )

    # (4) Reverse kuota promo (jangan sampai used_count jadi minus).
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
        loyalty_points_refunded=loyalty_points_refunded,
        loyalty_clamped=loyalty_clamped,
        promo_code_reverted=promo_code_reverted,
        deleted_by=deleted_by,
    )

    order_number = order.order_number

    # (5) Tutup transaksi Midtrans yang belum dibayar setelah commit berhasil.
    if was_gateway_pending:
        transaction.on_commit(lambda: cancel_midtrans_transaction(order_number))

    order.delete()
    return {
        "order_number": order_number,
        "points_reverted": loyalty_points_reverted,
        "points_refunded": loyalty_points_refunded,
        "promo_code_reverted": promo_code_reverted,
        "gateway_paid": gateway_paid,
    }


@api_view(["GET", "DELETE"])
@permission_classes([IsStaffLevel])
def get_order(request, pk):
    order = get_object_or_404(
        Order.objects.select_related("promo").prefetch_related("items__menu", "payments"),
        pk=pk,
    )

    if request.method == "DELETE":
        # IsStaffLevel mengizinkan owner, admin, dan kasir. Hapus permanen
        # cuma boleh owner, jadi dicek manual di sini.
        profile = getattr(request.user, "profile", None)
        if not profile or profile.role != "owner":
            return Response(
                {"detail": "Hanya owner yang boleh menghapus order secara permanen."},
                status=403,
            )

        deleted_by = getattr(request.user, "username", "") or "owner"
        result = _delete_order_permanently(order, deleted_by=deleted_by)
        order_number = result["order_number"]

        notes = []
        if result["points_refunded"]:
            notes.append(f"{result['points_refunded']} poin tukar reward dikembalikan")
        if result["points_reverted"]:
            notes.append(f"{result['points_reverted']} poin hasil belanja ditarik balik")
        if result["promo_code_reverted"]:
            notes.append(f"kuota promo {result['promo_code_reverted']} dikembalikan")
        detail = f"Order {order_number} dihapus permanen beserta menu dan pembayarannya."
        if notes:
            detail += " " + ", ".join(notes).capitalize() + "."
        if result["gateway_paid"]:
            detail += " Pembayaran online (QRIS) sudah masuk ke Midtrans; refund ke pelanggan harus diproses manual di dashboard Midtrans."

        return Response({"success": True, **result, "detail": detail})

    return Response(OrderSerializer(order).data)

@api_view(["GET"])
@permission_classes([IsStaffLevel])
def active_orders_per_day(request):
    raw_date = request.query_params.get("target_date")
    if not raw_date:
        return Response({"error": "Parameter target_date wajib diisi"}, status=400)

    target_date = parse_date(raw_date)   # None kalau formatnya salah (bukan 500)
    if target_date is None:
        return Response({"error": "Format target_date harus YYYY-MM-DD"}, status=400)

    # "Hari" = 00:00–24:00 WIB (eksplisit, tidak bergantung setting TIME_ZONE).
    day_start = datetime.datetime.combine(target_date, datetime.time.min, tzinfo=WIB)
    day_end   = day_start + timedelta(days=1)

    # Urut berdasarkan JAM ORDER (created_at), terbaru di atas. -id jadi
    # tie-break supaya urutan stabil kalau dua order punya jam yang sama
    # (mis. nota hasil pisah, atau dua input susulan di menit yang sama).
    orders = (
        Order.objects
        .filter(created_at__gte=day_start, created_at__lt=day_end)
        .prefetch_related("items__menu")
        .exclude(GATEWAY_NOT_PAID_Q)
        .order_by("-created_at", "-id")
    )
    return Response(OrderSerializer(orders, many=True).data)


# ─────────────────────────────────────────────
# LOYALTY — PUBLIK
# ─────────────────────────────────────────────

def _is_pos_staff(request):
    """Staf yang login: sama dengan syarat create_order mempercayai source='pos'. Tidak perlu PIN."""
    user = getattr(request, "user", None)
    return bool(user and user.is_authenticated and user.is_staff)


def _days_until(dt, now=None):
    """Selisih hari kalender (WIB) dari sekarang ke dt. Negatif = sudah lewat."""
    if not dt:
        return None
    return (to_wib(dt).date() - to_wib(now or timezone.now()).date()).days


def _expiry_note(loyalty, just_expired):
    if just_expired:
        if not loyalty.last_order_at:
            return "Poin hangus otomatis"
        return (
            f"Poin hangus karena tidak ada pesanan selama "
            f"{loyalty.expiry_months_setting()} bulan (order terakhir {loyalty.last_order_at:%d %b %Y})"
        )
    expiry_date = loyalty.expiry_estimate_date()
    if expiry_date:
        return f"Poin akan hangus sekitar {expiry_date:%d %b %Y} kalau tidak ada pesanan lagi"
    return None


@api_view(["GET"])
@permission_classes([AllowAny])
def check_loyalty_status(request):
    """
    GET /api/orders/check_loyalty_status/?phone=08xxx

    - Staf login (POS): status member + saldo poin, seperti sebelumnya.
    - Publik (web): SELALU jawaban kosong yang sama untuk semua nomor. Saldo poin dan status
      member hanya keluar lewat POST /orders/member/verify/ dengan PIN yang benar, supaya
      nomor HP orang lain tidak bisa diintip.
    """
    empty = {"is_member": False, "points": 0, "points_expiring_note": None}
    if not _is_pos_staff(request):
        return Response(empty)

    phone = request.query_params.get("phone", "").strip()
    loyalty = CustomerLoyalty.objects.filter(phone=phone).first() if phone else None
    if not loyalty:
        return Response(empty)

    # Cek hangus SEBELUM ditampilkan, biar saldo selalu akurat real-time.
    just_expired = loyalty.check_and_expire_points()
    return Response({
        "is_member":            True,
        "points":               loyalty.points,
        "points_expiring_note": _expiry_note(loyalty, just_expired),
    })


# ─────────────────────────────────────────────
# POINT REWARDS — PUBLIK
# ─────────────────────────────────────────────

LOCKED_RECOMMENDATION_LIMIT = 5


def _reward_lists(points, staff):
    """(affordable, locked) untuk saldo `points`. Publik tidak melihat reward secret/nonaktif."""
    rewards = PointReward.objects.filter(is_active=True).select_related('menu')
    if not staff:
        rewards = rewards.filter(menu__is_secret=False, menu__is_active=True)

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
    return [d for _, d in affordable], [d for _, d in locked[:LOCKED_RECOMMENDATION_LIMIT]]


@api_view(["GET"])
@permission_classes([AllowAny])
def available_point_rewards(request):
    """
    GET /api/orders/point-rewards/available/?phone=08xxx

    Staf (POS): saldo poin nomor itu + reward yang bisa ditukar / paling dekat.
    Publik: saldo SELALU dianggap 0 (tidak ada angka poin yang bocor); web memakai
    POST /orders/member/verify/ untuk melihat saldo setelah PIN benar.
    """
    staff = _is_pos_staff(request)
    points = 0
    if staff:
        phone = request.query_params.get("phone", "").strip()
        loyalty = CustomerLoyalty.objects.filter(phone=phone).first() if phone else None
        points = loyalty.points if loyalty else 0

    affordable, locked = _reward_lists(points, staff)
    return Response({"points": points, "affordable": affordable, "locked": locked})


@api_view(["POST"])
@permission_classes([AllowAny])
def member_verify(request):
    """
    POST /api/orders/member/verify/   { "phone": "08..", "pin": "1234" }

    PIN benar → saldo poin, kapan poin hangus, bar menuju reward termurah, dan daftar reward.
    Apa pun yang salah → 403 dengan pesan yang sama (tidak membedakan alasan).
    """
    loyalty = member_pin.verify_pin(request.data.get("phone"), request.data.get("pin"))
    if not loyalty:
        return Response({"detail": member_pin.NEUTRAL_ERROR}, status=403)

    just_expired = loyalty.check_and_expire_points()
    now = timezone.now()
    affordable, locked = _reward_lists(loyalty.points, False)

    cheapest = (
        PointReward.objects.filter(is_active=True, menu__is_secret=False, menu__is_active=True)
        .select_related("menu").order_by("point_cost").first()
    )
    expiry_date = loyalty.expiry_estimate_date() if loyalty.points > 0 else None

    response = Response({
        "verified": True,
        "name": loyalty.name,
        "points": loyalty.points,
        "total_orders": loyalty.total_orders,
        "last_order_at": loyalty.last_order_at,
        "expiry_months": loyalty.expiry_months_setting(),
        "expiry_date": expiry_date,
        "days_until_expiry": _days_until(expiry_date, now),
        "points_expiring_note": _expiry_note(loyalty, just_expired),
        "progress": (
            {"target_name": cheapest.menu.name, "target_cost": cheapest.point_cost, "points": loyalty.points}
            if cheapest else None
        ),
        "affordable": affordable,
        "locked": locked,
    })
    response["Cache-Control"] = "no-store"
    return response


# ─────────────────────────────────────────────
# POINT REWARDS — ADMIN CRUD
# ─────────────────────────────────────────────

class PointRewardViewSet(viewsets.ModelViewSet):
    queryset = PointReward.objects.select_related('menu').all()
    serializer_class = PointRewardSerializer
    permission_classes = [IsAdminLevel]


# ─────────────────────────────────────────────
# REPORTS & DASHBOARD
# ─────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAdminLevel])
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
    permission_classes = [IsAdminLevel]

    def get(self, request):
        date_from = request.query_params.get('date_from')
        date_to   = request.query_params.get('date_to')

        paid_qs = Order.objects.filter(payment_status='paid').exclude(status='cancelled')
        all_qs  = Order.objects.exclude(GATEWAY_NOT_PAID_Q)
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
@permission_classes([IsAdminLevel])
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
@permission_classes([IsAdminLevel])
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
@permission_classes([IsAdminLevel])
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
@permission_classes([IsAdminLevel])
def export_excel_report(request):
    """
    GET /api/orders/export/finance-excel/?mode=monthly&month=7&year=2026
    GET /api/orders/export/finance-excel/?mode=yearly&year=2026
    """
    from .finance_excel import export_finance_excel_view
    return export_finance_excel_view(request)


@api_view(["GET"])
@permission_classes([IsAdminLevel])
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
    permission_classes = [IsAdminLevel]

    def get(self, request):
        return Response(LoyaltySettingsSerializer(LoyaltySettings.get_settings()).data)

    def put(self, request):
        settings   = LoyaltySettings.get_settings()
        serializer = LoyaltySettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        reset_late_minutes_cache()
        return Response(serializer.data)


class LoyalCustomersView(APIView):
    """
    Sumber data langsung dari CustomerLoyalty (points/total_spent/total_orders/
    last_order_at udah kesimpen real-time lewat signal tiap order completed).
    """
    permission_classes = [IsAdminLevel]

    def get(self, request):
        settings  = LoyaltySettings.get_settings()
        loyalties = list(CustomerLoyalty.objects.all().order_by('-points'))
        now       = timezone.now()
        assigned, segment_summary = segment_overview(loyalties)
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
                "segment":         assigned[cl.phone][0],
                "days_since_last_order": assigned[cl.phone][1],
                "has_pin":         cl.has_pin,
                "pin_set_at":      cl.pin_set_at,
                "pin_locked":      bool(cl.pin_locked_until and cl.pin_locked_until > now),
                "days_until_expiry": _days_until(cl.expiry_estimate_date(), now) if cl.points > 0 else None,
                "expiry_state":    _expiry_state(cl, settings.points_expiry_months, now),
            }
            for cl in loyalties
        ]

        return Response({
            "settings":  LoyaltySettingsSerializer(settings).data,
            "customers": customers,
            "segments":  segment_summary,
        })


EXPIRY_SOON_DAYS = 14


def _expiry_state(loyalty, months, now):
    """off = fitur hangus dimatikan, none = tidak ada poin, expired / soon / ok."""
    if not months:
        return "off"
    if loyalty.points <= 0:
        return "none"
    if loyalty.points_expired():
        return "expired"
    days = _days_until(loyalty.expiry_estimate_date(), now)
    return "soon" if days is not None and days <= EXPIRY_SOON_DAYS else "ok"


BULK_DELETE_CONFIRM_TEXT = "HAPUS"


class LoyalCustomerDetailView(APIView):
    """
    DELETE /orders/loyal-customers/<phone>/ — hapus permanen satu member.

    Hard delete: riwayat penyesuaian poin (PointAdjustment, CASCADE) ikut terhapus,
    termasuk jejak audit-nya. Order lama TIDAK dihapus (hanya menyimpan nomor HP), jadi
    data omzet, Jam Sibuk, Performa Menu, dan prediksi tidak berubah. Bila nomor yang sama
    order lagi, member baru dibuat dari nol.
    """
    permission_classes = [IsAdminLevel]

    @transaction.atomic
    def delete(self, request, phone):
        loyalty = CustomerLoyalty.objects.select_for_update().filter(phone=phone).first()
        if not loyalty:
            return Response({'detail': 'Member tidak ditemukan'}, status=404)
        adjustments = loyalty.adjustments.count()
        loyalty.delete()
        return Response({'deleted': 1, 'adjustments_deleted': adjustments})


class LoyalCustomerPinView(APIView):
    """
    POST /orders/loyal-customers/<phone>/pin/   { "pin": "1234" }   ("pin" opsional)

    Atur PIN pertama kali atau ganti PIN (sekaligus membuka kunci). Tanpa "pin", sistem
    membuat 4 digit acak. PIN asli dikembalikan SEKALI di respons ini; di database hanya hash.
    Hanya admin/owner, supaya pelanggan tidak bisa mengklaim nomor orang lain.
    """
    permission_classes = [IsAdminLevel]

    @transaction.atomic
    def post(self, request, phone):
        loyalty = CustomerLoyalty.objects.select_for_update().filter(phone=phone).first()
        if not loyalty:
            return Response({'detail': 'Member tidak ditemukan'}, status=404)

        raw = request.data.get('pin')
        if raw in (None, ''):
            raw = member_pin.generate_pin()
        elif not member_pin.is_valid_format(str(raw)):
            return Response({'detail': f'PIN harus {member_pin.PIN_LENGTH} digit angka'}, status=400)
        raw = str(raw)

        had_pin = loyalty.has_pin
        member_pin.set_pin(loyalty, raw)
        response = Response({'pin': raw, 'had_pin': had_pin, 'pin_set_at': loyalty.pin_set_at})
        response['Cache-Control'] = 'no-store'
        return response


class LoyalCustomersBulkDeleteView(APIView):
    """
    POST /orders/loyal-customers/bulk-delete/
      { "phones": ["0812...", "0813..."], "confirm": "HAPUS" }   → hapus yang dipilih
      { "all": true,                       "confirm": "HAPUS" }   → hapus SEMUA member

    Konfirmasi kuat dicek di server (bukan hanya di dialog frontend), supaya endpoint ini
    tidak bisa terpanggil tanpa sengaja. Hard delete, sama seperti hapus satu member.
    """
    permission_classes = [IsAdminLevel]

    @transaction.atomic
    def post(self, request):
        if str(request.data.get('confirm') or '').strip() != BULK_DELETE_CONFIRM_TEXT:
            return Response(
                {'detail': f'Ketik {BULK_DELETE_CONFIRM_TEXT} untuk mengonfirmasi penghapusan'},
                status=400,
            )

        if request.data.get('all') is True:
            qs = CustomerLoyalty.objects.all()
        else:
            phones = request.data.get('phones')
            if not isinstance(phones, list) or not phones:
                return Response({'detail': 'phones wajib berupa daftar nomor HP yang tidak kosong'}, status=400)
            qs = CustomerLoyalty.objects.filter(phone__in=[str(p) for p in phones])

        ids = list(qs.values_list('id', flat=True))
        adjustments = PointAdjustment.objects.filter(customer_id__in=ids).count()
        CustomerLoyalty.objects.filter(id__in=ids).delete()
        return Response({'deleted': len(ids), 'adjustments_deleted': adjustments})


class AdjustPointsView(APIView):
    """
    Adjust poin manual (nambah/mengurangi), alasan wajib & tercatat sebagai
    PointAdjustment (audit log).
    """
    permission_classes = [IsAdminLevel]

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
@permission_classes([IsStaffLevel])
def unpaid_orders(request):
    search = request.query_params.get("search", "")

    qs = (
        Order.objects
        .filter(payment_status__in=["unpaid", "pending"])
        .exclude(status="cancelled")
        .exclude(GATEWAY_NOT_PAID_Q)
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
@permission_classes([IsStaffLevel])
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
    blocked = active_qr_block(order)
    if blocked:
        return blocked

    if order.payment_method == "gateway" and order.payment_status == "pending":
        return Response(
            {"detail": "Order ini menunggu pembayaran online (Midtrans). Batalkan order dulu kalau customer tidak jadi bayar online."},
            status=400,
        )

    previous_status = order.status
    kasir_name      = (request.data.get('kasir_name') or '').strip()
    payments_data   = request.data.get('payments')

    if payments_data:
        # ── Format baru: banyak baris pembayaran ──
        valid_methods = {choice[0] for choice in PAYMENT_METHOD_CHOICES if choice[0] not in ('mixed', 'gateway')}
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
@permission_classes([IsStaffLevel])
@transaction.atomic
def cancel_order(request, pk):
    """
    Void/batalkan order dengan alasan wajib. Order TIDAK dihapus dari
    database, cuma diubah statusnya jadi 'cancelled' + dicatat alasannya.
    """
    order = get_object_or_404(Order.objects.select_for_update(), pk=pk)
    previous_status = order.status
    was_gateway_pending = order.payment_method == "gateway" and order.payment_status == "pending"

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

    # Tutup transaksi di Midtrans supaya QR lama tidak bisa dibayar lagi.
    if was_gateway_pending:
        order_number = order.order_number
        transaction.on_commit(lambda: cancel_midtrans_transaction(order_number))
    elif order.midtrans_qr_ref:
        qr_ref = order.midtrans_qr_ref
        transaction.on_commit(lambda: cancel_midtrans_transaction(qr_ref))

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
@permission_classes([IsStaffLevel])
def new_order_notifications(request):
    """
    GET /api/orders/notifications/?after_id=123&after_payment_id=45

    - new_orders      : order BARU (cash/POS-web) sejak after_id. Order gateway
                        TIDAK ikut di sini.
    - new_paid_orders : order gateway yang pembayarannya MASUK sejak
                        after_payment_id (kursor = id OrderPayment).
    """
    latest_id = Order.objects.order_by("-id").values_list("id", flat=True).first() or 0
    latest_payment_id = (
        OrderPayment.objects.filter(method="gateway")
        .order_by("-id").values_list("id", flat=True).first() or 0
    )
    base = {
        "new_orders": [], "new_paid_orders": [],
        "latest_id": latest_id, "latest_payment_id": latest_payment_id,
    }

    after_id_raw = request.query_params.get("after_id")
    if after_id_raw is None:
        return Response(base)
    try:
        after_id = int(after_id_raw)
    except (TypeError, ValueError):
        return Response(base)

    gap = latest_id - after_id
    if gap > NOTIFICATION_BACKLOG_SKIP_THRESHOLD:
        return Response({**base, "backlog_skipped": True, "backlog_count": gap})

    # Frontend lama (belum kirim after_payment_id): jangan banjir notif.
    try:
        after_payment_id = int(request.query_params.get("after_payment_id"))
    except (TypeError, ValueError):
        after_payment_id = latest_payment_id

    new_orders_qs = (
        Order.objects
        .filter(id__gt=after_id)
        .exclude(source="pos")
        .exclude(payment_method="gateway")
        .order_by("id")[:20]
    )
    paid_qs = (
        OrderPayment.objects
        .filter(method="gateway", id__gt=after_payment_id)
        .select_related("order")
        .order_by("id")[:20]
    )

    def _row(o, **extra):
        return {
            "id": o.id,
            "order_number": o.order_number,
            "customer_name": o.customer_name or "Pelanggan",
            "total_price": o.total_price,
            "source": o.source,
            "created_at": o.created_at,
            **extra,
        }

    return Response({
        **base,
        "new_orders": [_row(o) for o in new_orders_qs],
        "new_paid_orders": [_row(p.order, payment_id=p.id, paid=True) for p in paid_qs],
    })

# ─────────────────────────────────────────────
# HISTORY & LAPORAN LENGKAP
# ─────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAdminLevel])
def order_history(request):
    """
    GET /api/orders/history/?period=today|week|month|year
    GET /api/orders/history/?period=month&year=2026&month=6
    """
    period = request.query_params.get("period", "today")
    now    = timezone.now()

    qs = Order.objects.exclude(GATEWAY_NOT_PAID_Q).prefetch_related("items__menu")

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
@permission_classes([IsAdminLevel])
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
        return [IsAdminLevel()]

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

def active_qr_block(order):
    """
    409 kalau nota "bayar nanti" punya QR QRIS yang masih berlaku. Selama QR hidup, nominal tidak
    boleh berubah dan nota tidak boleh dilunasi cara lain (pelanggan bisa membayar dobel / nominal tidak cocok).
    """
    if (
        order.midtrans_qr_ref and order.payment_status == "unpaid"
        and order.midtrans_qr_expires_at and order.midtrans_qr_expires_at > timezone.now()
    ):
        return Response(
            {"detail": "Nota ini punya QR QRIS yang masih aktif. Batalkan QR di layar kasir dulu."},
            status=409,
        )
    return None


def _check_editable(order):
    """Item cuma boleh diubah selama order belum dibayar & belum dibatalkan."""
    blocked = active_qr_block(order)
    if blocked:
        return blocked
    if order.payment_method == "gateway" and order.payment_status == "pending":
        return Response(
            {"detail": "Order menunggu pembayaran online, item tidak bisa diubah. Batalkan order lalu input ulang."},
            status=400,
        )
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
@permission_classes([IsStaffLevel])
@transaction.atomic
def add_order_item(request, pk):
    """
    Tambah menu ke order yang belum lunas.
    Body: { "menu_id": 5, "quantity": 1, "notes": "", "options": {"Level Pedas": ["Pedas"]} }
    Baris yang sama persis (menu, pilihan opsi, catatan, harga) → quantity-nya yang ditambah.
    """
    order = get_object_or_404(Order.objects.select_for_update(), pk=pk)
    err = _check_editable(order)
    if err:
        return err

    menu = get_object_or_404(Menu, pk=request.data.get("menu_id"))
    if not menu.is_available:
        return Response(
            {"detail": f"Menu {menu.name} sedang habis. Aktifkan lagi di Kelola Menu kalau stoknya sudah ada."},
            status=400,
        )
    try:
        quantity = int(request.data.get("quantity", 1) or 1)
    except (TypeError, ValueError):
        return Response({"detail": "Quantity tidak valid."}, status=400)
    if quantity <= 0:
        return Response({"detail": "Quantity harus lebih dari 0."}, status=400)

    try:
        chosen, extra_price, option_text = resolve_selection(menu, request.data.get("options"))
    except OptionError as e:
        return Response({"detail": str(e)}, status=400)

    notes      = _join_notes(option_text, request.data.get("notes"))
    unit_price = _price_for(order.source, menu) + extra_price

    existing = next(
        (
            i for i in order.items.filter(menu=menu, notes=notes, is_point_redemption=False, bundle_name="")
            if i.selected_options == chosen and i.price == unit_price
        ),
        None,
    )
    now = timezone.now()
    # Menambah ke nota yang sudah punya item = "pesanan ditambah". Nota yang
    # masih kosong (belum ada item) tidak ditandai, karena itu bukan tambahan.
    is_addition = order.items.exists()
    if existing:
        existing.quantity += quantity
        update_fields = ["quantity"]
        if is_addition:
            existing.added_qty += quantity
            existing.added_at = now
            update_fields += ["added_qty", "added_at"]
        existing.save(update_fields=update_fields)
    else:
        OrderItem.objects.create(
            order=order, menu=menu, quantity=quantity,
            price=unit_price, notes=notes, selected_options=chosen,
            added_at=now if is_addition else None,
            added_qty=quantity if is_addition else 0,
        )
    # Ada tambahan menu = dapur harus bikin lagi, jadi status "siap" dicabut.
    if is_addition and order.ready_at:
        order.ready_at = None
        order.save(update_fields=["ready_at"])

    _refresh_totals(order)
    order.refresh_from_db()
    return Response(OrderSerializer(order).data)

@api_view(["PATCH", "DELETE"])
@permission_classes([IsStaffLevel])
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
        diff = new_qty - item.quantity
        item.quantity = new_qty
        update_fields = ["quantity"]
        if diff > 0:
            item.added_qty += diff
            item.added_at = timezone.now()
            update_fields += ["added_qty", "added_at"]
            if order.ready_at:
                order.ready_at = None
                order.save(update_fields=["ready_at"])
        elif diff < 0 and item.added_qty:
            # Pengurangan memakan jatah "tambahan" dulu, supaya badge tidak menipu.
            item.added_qty = max(item.added_qty + diff, 0)
            if item.added_qty == 0:
                item.added_at = None
            update_fields += ["added_qty", "added_at"]
        item.save(update_fields=update_fields)

    _refresh_totals(order)
    order.refresh_from_db()
    return Response(OrderSerializer(order).data)


@api_view(["POST"])
@permission_classes([IsStaffLevel])
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
        service_type=order.service_type,
        customer_name=new_name or (f"{order.customer_name} (pisah)" if order.customer_name else "Pisahan"),
        customer_phone="",   # sengaja kosong: poin loyalty tetap di nota asal
        table_number=order.table_number,
        notes=f"Dipisah dari {order.order_number}",
        # Nota hasil pisah tetap di hari & jam order asal (bukan "sekarang"),
        # jadi order dari hari lain tidak loncat ke laporan hari ini.
        created_at=order.created_at,
        kasir_name=kasir_name or order.kasir_name,
    )

    for item, qty in moves:
        if qty == item.quantity:
            item.order = new_order
            item.save(update_fields=["order"])
        else:
            item.quantity -= qty
            item.save(update_fields=["quantity"])
            moved_added = min(item.added_qty, qty)
            original_added_at = item.added_at
            item.added_qty -= moved_added
            if item.added_qty == 0:
                item.added_at = None
            item.save(update_fields=["added_qty", "added_at"])
            OrderItem.objects.create(
                order=new_order, menu=item.menu, quantity=qty,
                price=item.price, notes=item.notes,
                selected_options=item.selected_options,
                bundle_name=item.bundle_name,
                added_qty=moved_added,
                added_at=original_added_at if moved_added else None,
            )

    _refresh_totals(order)      # promo (kalau ada) tetap menempel di nota asal
    _refresh_totals(new_order)
    order.refresh_from_db()
    new_order.refresh_from_db()

    return Response({
        "original":  OrderSerializer(order).data,
        "new_order": OrderSerializer(new_order).data,
    }, status=201)



# ─────────────────────────────────────────────
# DAPUR: SIAP DIAMBIL, MENU HABIS, REFUND
# ─────────────────────────────────────────────
#
# Aturan uang saat menu habis SETELAH order dibuat (lihat mark_items_unavailable):
#   • Order BELUM dibayar (cash bayar di akhir / makan dulu): item habis langsung
#     dikeluarkan dari nota, total turun, pelanggan cukup bayar total baru.
#   • Order SUDAH lunas (QRIS / gateway / cash di muka): item dikeluarkan dan total
#     turun, selisihnya dicatat sebagai refund_due. Kasir menyerahkan uangnya waktu
#     pesanan diambil, lalu menandai "sudah dikembalikan" (confirm_refund).


def _shrink_loyalty_after_reduction(order, old_total, new_total):
    """Tarik balik poin/total belanja yang sudah dicatat untuk order lunas yang totalnya turun."""
    if not (order.loyalty_applied and order.customer_phone):
        return 0
    loyalty = (
        CustomerLoyalty.objects.select_for_update()
        .filter(phone=order.customer_phone).first()
    )
    if not loyalty:
        return 0

    rate = LoyaltySettings.get_settings().rupiah_per_point or 10000
    new_earned = int(new_total // rate)
    drop = max(order.loyalty_points_earned - new_earned, 0)
    take = min(drop, loyalty.points)   # jangan sampai minus kalau poinnya sudah terpakai

    loyalty.points = loyalty.points - take
    loyalty.total_spent = max(loyalty.total_spent - (old_total - new_total), Decimal("0"))
    loyalty.save(update_fields=["points", "total_spent", "updated_at"])

    if drop:
        # update() supaya tidak memicu signal post_save lagi.
        Order.objects.filter(pk=order.pk).update(loyalty_points_earned=order.loyalty_points_earned - drop)
    return take


def _open_orders_with_menus(menu_ids, exclude_pk=None):
    """Nota yang masih berjalan (24 jam terakhir, belum siap, belum batal) dan memuat salah satu menu ini."""
    if not menu_ids:
        return Order.objects.none()
    since = timezone.now() - timedelta(hours=24)
    qs = (
        Order.objects
        .filter(kitchen_open_q(), items__menu_id__in=menu_ids, created_at__gte=since)
        .exclude(status="cancelled")
        .exclude(payment_status="void")
        .exclude(GATEWAY_NOT_PAID_Q)
        .distinct()
        .order_by("created_at")
    )
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs


def _sold_out_menus(menu_ids):
    """
    Tandai menu jadi habis di katalog (Kelola Menu), supaya tidak bisa dipesan lagi
    di POS maupun web. Return daftar menu yang BARU berubah dari tersedia → habis.
    """
    ids = {m for m in menu_ids if m}
    if not ids:
        return []
    changed = list(Menu.objects.filter(pk__in=ids, is_available=True).values("id", "name"))
    if changed:
        Menu.objects.filter(pk__in=[m["id"] for m in changed]).update(is_available=False)
    return changed


def _unavailable_extras(order, menu_ids, changed_menus):
    """Bagian respons tambahan: menu yang ikut ditandai habis + nota lain yang masih memuat menu itu."""
    others = _open_orders_with_menus(menu_ids, exclude_pk=order.pk)
    return {
        "menus_marked": changed_menus,
        "other_orders": [
            {"id": o.pk, "order_number": o.order_number, "customer_name": o.customer_name}
            for o in others[:20]
        ],
    }


@api_view(["PATCH"])
@permission_classes([IsStaffLevel])
@transaction.atomic
def mark_order_ready(request, pk):
    """
    Tandai pesanan siap diambil / batalkan tandanya.
    Body: { "ready": true }   (default true; false = cabut tanda siap)
    """
    order = get_object_or_404(Order.objects.select_for_update(), pk=pk)
    if order.status == "cancelled" or order.payment_status == "void":
        return Response({"detail": "Order ini sudah dibatalkan."}, status=400)
    if not order.tracks_readiness:
        return Response({"detail": "Order POS tidak memakai status siap (pelanggan sudah di warung)."}, status=400)

    raw = request.data.get("ready", True)
    ready = raw if isinstance(raw, bool) else str(raw).strip().lower() in ("1", "true", "yes", "ya")

    order.ready_at = timezone.now() if ready else None
    order.save(update_fields=["ready_at"])
    order.refresh_from_db()
    return Response(OrderSerializer(order).data)


@api_view(["POST"])
@permission_classes([IsStaffLevel])
@transaction.atomic
def mark_items_unavailable(request, pk):
    """
    Menu habis setelah order dibuat. Item dikeluarkan dari nota dan totalnya dihitung ulang.

    Body:
    {
      "items": [{"item_id": 12, "quantity": 1}],   # quantity kosong = seluruh baris
      "kasir_name": "Wawan",
      "note": "",                                   # opsional
      "mark_menu_sold_out": true                    # default true: menu ikut jadi HABIS di Kelola Menu
    }

    Menu yang ditandai habis di sini otomatis tidak bisa dipesan lagi di POS maupun web
    (sampai diaktifkan lagi di Kelola Menu). Kirim false kalau cuma porsi di nota ini yang kurang.

    Respons: order terbaru + "summary" (nominal yang hilang, refund / kurang bayar)
    + "menus_marked" (menu yang baru jadi habis) + "other_orders" (nota lain yang masih memuat menu itu).
    """
    order = get_object_or_404(Order.objects.select_for_update(), pk=pk)

    if order.status == "cancelled" or order.payment_status == "void":
        return Response({"detail": "Order ini sudah dibatalkan."}, status=400)
    blocked = active_qr_block(order)
    if blocked:
        return blocked
    if order.payment_method == "gateway" and order.payment_status == "pending":
        return Response(
            {"detail": "Order menunggu pembayaran online, item tidak bisa diubah. Batalkan order lalu input ulang."},
            status=400,
        )

    rows = request.data.get("items") or []
    if not rows:
        return Response({"detail": "Pilih minimal satu item yang habis."}, status=400)

    moves, seen = [], set()
    for row in rows:
        item = order.items.select_related("menu").filter(pk=row.get("item_id")).first()
        if not item or item.pk in seen:
            return Response({"detail": "Item tidak ditemukan / dobel di request."}, status=400)
        if item.is_point_redemption:
            return Response(
                {"detail": "Item hasil tukar poin tidak bisa dikeluarkan dari sini (poin sudah terpotong). "
                           "Batalkan / void order-nya supaya poin dikembalikan."},
                status=400,
            )
        raw_qty = row.get("quantity")
        try:
            qty = item.quantity if raw_qty in (None, "") else int(raw_qty)
        except (TypeError, ValueError):
            return Response({"detail": "Quantity tidak valid."}, status=400)
        name = item.menu.name if item.menu else "Menu"
        if qty <= 0 or qty > item.quantity:
            return Response({"detail": f"Jumlah untuk {name} tidak valid."}, status=400)
        seen.add(item.pk)
        moves.append((item, qty, name))

    is_paid = order.payment_status == "paid"
    kasir_name = (request.data.get("kasir_name") or "").strip()
    note = (request.data.get("note") or "").strip()[:200]
    now = timezone.now()

    raw_flag = request.data.get("mark_menu_sold_out", True)
    mark_sold_out = raw_flag if isinstance(raw_flag, bool) else str(raw_flag).strip().lower() not in ("0", "false", "no", "tidak")
    menu_ids = [item.menu_id for item, _, _ in moves if item.menu_id]

    total_units = sum(i.quantity for i in order.items.all())
    if total_units - sum(q for _, q, _ in moves) <= 0:
        # Semua menu di nota habis.
        if is_paid:
            return Response(
                {"detail": "Semua item di nota ini habis, padahal sudah dibayar. Hapus / void order lewat menu Hapus "
                           "supaya poin & laporan ikut dibalik, lalu kembalikan uangnya ke pelanggan."},
                status=400,
            )
        previous_status = order.status
        order.status = "cancelled"
        order.payment_status = "void"
        order.cancel_reason = "out_of_stock"
        order.cancel_note = note or "Semua menu habis"
        order.cancelled_at = now
        order.cancelled_by = kasir_name
        order._previous_status = previous_status
        order.save()
        order.refresh_from_db()
        changed = _sold_out_menus(menu_ids) if mark_sold_out else []
        return Response({
            "order": OrderSerializer(order).data,
            "summary": {"cancelled": True, "lost_amount": 0, "refund_due": 0, "amount_to_pay_now": 0},
            **_unavailable_extras(order, menu_ids, changed),
        })

    old_total = order.total_price
    log = list(order.unavailable_items or [])
    lost_gross = Decimal("0")
    for item, qty, name in moves:
        lost_gross += item.price * qty
        log.append({
            "name": name,
            "quantity": qty,
            "price": int(item.price),
            "notes": item.notes,
            "at": now.isoformat(),
            "by": kasir_name,
            "note": note,
        })
        if qty == item.quantity:
            item.delete()
        else:
            item.quantity -= qty
            item.added_qty = min(item.added_qty, item.quantity)
            if item.added_qty == 0:
                item.added_at = None
            item.save(update_fields=["quantity", "added_qty", "added_at"])

    _refresh_totals(order)           # subtotal, promo, total dihitung ulang
    order.refresh_from_db()
    new_total = order.total_price
    # Selisih yang BENAR-BENAR berubah di tagihan (sudah memperhitungkan promo).
    drop = max(old_total - new_total, Decimal("0"))

    order.unavailable_items = log
    update_fields = ["unavailable_items"]

    refund_due = order.refund_due
    if is_paid and drop > 0:
        if order.refunded_at is not None:
            # Refund sebelumnya sudah diserahkan; ini utang baru yang terpisah.
            order.refund_due = drop
        else:
            order.refund_due = order.refund_due + drop
        order.refunded_at = None
        order.refunded_by = ""
        update_fields += ["refund_due", "refunded_at", "refunded_by"]
        _shrink_loyalty_after_reduction(order, old_total, new_total)
        refund_due = order.refund_due

    order.save(update_fields=update_fields)
    order.refresh_from_db()

    changed = _sold_out_menus(menu_ids) if mark_sold_out else []

    return Response({
        "order": OrderSerializer(order).data,
        **_unavailable_extras(order, menu_ids, changed),
        "summary": {
            "cancelled": False,
            "lost_amount": int(lost_gross),
            "bill_drop": int(drop),
            "old_total": int(old_total),
            "new_total": int(new_total),
            "is_paid": is_paid,
            "refund_due": int(refund_due) if is_paid else 0,
            "amount_to_pay_now": 0 if is_paid else int(new_total),
            "payment_method": order.payment_method,
        },
    })


@api_view(["PATCH"])
@permission_classes([IsStaffLevel])
@transaction.atomic
def confirm_refund(request, pk):
    """
    Tandai uang refund sudah diserahkan ke pelanggan (saat pesanan diambil).
    Body: { "kasir_name": "Wawan" }      → tandai sudah dikembalikan
          { "undo": true }               → batalkan tanda (salah klik)
    """
    order = get_object_or_404(Order.objects.select_for_update(), pk=pk)
    if not order.refund_due or order.refund_due <= 0:
        return Response({"detail": "Order ini tidak punya refund."}, status=400)

    if request.data.get("undo"):
        order.refunded_at = None
        order.refunded_by = ""
    else:
        if order.refunded_at is not None:
            return Response({"detail": "Refund order ini sudah ditandai dikembalikan."}, status=400)
        order.refunded_at = timezone.now()
        order.refunded_by = (request.data.get("kasir_name") or "").strip()
    order.save(update_fields=["refunded_at", "refunded_by"])
    order.refresh_from_db()
    return Response(OrderSerializer(order).data)


@api_view(["GET"])
@permission_classes([IsStaffLevel])
def pending_refunds(request):
    """Semua refund yang belum diserahkan (lintas hari), supaya tidak ada uang pelanggan yang terlewat."""
    qs = (
        Order.objects
        .filter(refund_due__gt=0, refunded_at__isnull=True)
        .exclude(status="cancelled")
        .prefetch_related("items__menu")
        .order_by("-created_at")
    )
    return Response(OrderSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([IsStaffLevel])
def orders_affected_by_menu(request, menu_id):
    """
    Order yang masih berjalan (belum siap, belum batal, 24 jam terakhir) dan memuat menu ini.
    Dipakai setelah menu ditandai habis: kasir langsung tahu nota mana yang harus dikabari.
    """
    since = timezone.now() - timedelta(hours=24)
    qs = (
        Order.objects
        .filter(kitchen_open_q(), items__menu_id=menu_id, created_at__gte=since)
        .exclude(status="cancelled")
        .exclude(payment_status="void")
        .exclude(GATEWAY_NOT_PAID_Q)
        .prefetch_related("items__menu")
        .distinct()
        .order_by("created_at")
    )
    return Response(OrderSerializer(qs, many=True).data)
