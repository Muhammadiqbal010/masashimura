import hashlib
import hmac
import logging
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from order.models import Order, OrderPayment
from .services import snap

logger = logging.getLogger(__name__)


class CreatePaymentView(APIView):
    """POST /api/payments/create/<order_number>/  → { token }"""
    authentication_classes = []
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request, order_number):
        order = get_object_or_404(
            Order.objects.select_for_update(),
            order_number=order_number, source="web", payment_method="gateway",
        )

        if order.status == "cancelled" or order.payment_status == "void":
            return Response({"detail": "Order sudah dibatalkan."}, status=400)
        if order.payment_status == "paid":
            return Response({"detail": "Order sudah dibayar."}, status=400)
        if order.payment_status != "pending":
            return Response({"detail": "Order ini tidak menunggu pembayaran online."}, status=400)
        if order.total_price <= 0:
            return Response({"detail": "Total order Rp0, tidak perlu bayar."}, status=400)

        # Token sudah ada → pakai ulang (tidak bikin transaksi kedua)
        if order.midtrans_snap_token:
            return Response({"token": order.midtrans_snap_token})

        param = {
            "transaction_details": {
                "order_id": order.order_number,
                "gross_amount": int(order.total_price),  # selalu dari DB, bukan dari frontend
            },
            "enabled_payments": ["other_qris"],
            "customer_details": {
                "first_name": order.customer_name or "Customer",
                "phone": order.customer_phone or "",
            },
            "expiry": {"unit": "minutes", "duration": 30},
        }
        try:
            trx = snap.create_transaction(param)
        except Exception:
            logger.exception("Gagal membuat transaksi Midtrans untuk %s", order.order_number)
            return Response({"detail": "Gagal membuat pembayaran, coba lagi."}, status=502)

        order.midtrans_snap_token = trx["token"]
        order.save(update_fields=["midtrans_snap_token"])
        return Response({"token": trx["token"]})


class MidtransWebhookView(APIView):
    """POST /api/payments/webhook/  — dipanggil server Midtrans."""
    authentication_classes = []   # tanpa auth/CSRF
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        d = request.data

        # 1) Verifikasi signature
        raw = (
            f'{d.get("order_id", "")}{d.get("status_code", "")}'
            f'{d.get("gross_amount", "")}{settings.MIDTRANS_SERVER_KEY}'
        )
        expected = hashlib.sha512(raw.encode()).hexdigest()
        if not hmac.compare_digest(expected, str(d.get("signature_key", ""))):
            return Response(status=403)

        # 2) Cari order. Tidak ketemu (mis. "Test notification" di dashboard)
        #    → tetap 200 supaya Midtrans tidak retry.
        order = (
            Order.objects.select_for_update()
            .filter(order_number=d.get("order_id"), payment_method="gateway")
            .first()
        )
        if not order:
            return Response({"ok": True})

        trx_status = d.get("transaction_status")

        # 3a) Lunas
        if trx_status == "settlement":
            if order.payment_status == "paid":
                return Response({"ok": True})  # webhook dobel, abaikan

            if order.status == "cancelled" or order.payment_status == "void":
                logger.error("Order %s dibayar SETELAH dibatalkan, perlu refund manual.", order.order_number)
                return Response({"ok": True})

            try:
                gross = Decimal(str(d.get("gross_amount")))
            except InvalidOperation:
                return Response(status=400)
            if gross != order.total_price:
                logger.error("Nominal tidak cocok untuk %s: %s vs %s", order.order_number, gross, order.total_price)
                return Response({"ok": True})

            order._previous_status = order.status
            order.payment_status = "paid"
            order.status = "completed"          # memicu signal poin loyalty
            order.amount_paid = order.total_price
            order.change_amount = Decimal("0")
            order.save()
            OrderPayment.objects.create(order=order, method="gateway", amount=order.total_price)

        # 3b) Gagal / kedaluwarsa → void + cancelled
        elif trx_status in ("deny", "cancel", "expire", "failure"):
            if order.payment_status not in ("paid", "void") and order.status != "cancelled":
                order._previous_status = order.status
                order.payment_status = "void"
                order.status = "cancelled"
                order.cancel_reason = "other"
                order.cancel_note = f"Pembayaran Midtrans: {trx_status}"
                order.cancelled_at = timezone.now()
                order.cancelled_by = "midtrans"
                order.save()

        # "pending" → tidak ada yang perlu diubah
        return Response({"ok": True})


class PaymentStatusView(APIView):
    """GET /api/payments/status/<order_number>/ — buat polling dari frontend."""
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        return Response({"payment_status": order.payment_status, "status": order.status})