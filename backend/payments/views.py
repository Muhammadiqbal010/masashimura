import hashlib
import hmac
import logging
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsStaffLevel
from order.models import Order, OrderPayment
from .services import cancel_midtrans_transaction, core, fetch_midtrans_status, snap
from .throttles import PaymentCreateThrottle, PaymentStatusThrottle

logger = logging.getLogger(__name__)


def _snap_item_details(order):
    """
    Rincian item untuk halaman Snap (tombol "Rincian"). Midtrans mewajibkan jumlah harga item sama
    dengan gross_amount, jadi selisih (diskon promo, poin, dll) dimasukkan sebagai satu baris
    penyesuaian. Kalau ada yang janggal, kirim tanpa rincian (jangan sampai membuat pembayaran gagal).
    """
    try:
        details = []
        for it in order.items.select_related("menu"):
            name = it.bundle_name or (it.menu.name if it.menu else "Item")
            details.append({
                "id": f"I{it.pk}",
                "price": int(it.price),
                "quantity": int(it.quantity),
                "name": name[:50],
            })
        diff = int(order.total_price) - sum(d["price"] * d["quantity"] for d in details)
        if diff:
            details.append({"id": "ADJ", "price": diff, "quantity": 1,
                            "name": "Diskon & penyesuaian" if diff < 0 else "Biaya tambahan"})
        return details
    except Exception:
        logger.warning("Gagal menyusun item_details %s", order.order_number, exc_info=True)
        return []


class CreatePaymentView(APIView):
    """POST /api/payments/create/<order_number>/  → { token }"""
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [PaymentCreateThrottle]

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
        items = _snap_item_details(order)
        if items:
            param["item_details"] = items
        try:
            trx = snap.create_transaction(param)
        except Exception:
            logger.exception("Gagal membuat transaksi Midtrans untuk %s", order.order_number)
            return Response({"detail": "Gagal membuat pembayaran, coba lagi."}, status=502)

        order.midtrans_snap_token = trx["token"]
        order.save(update_fields=["midtrans_snap_token"])
        return Response({"token": trx["token"]})


def apply_midtrans_status(order, verified, bill_qr=False):
    """
    Terapkan status transaksi yang SUDAH diverifikasi langsung dari Midtrans ke order
    (order harus sudah di-lock select_for_update). Dipakai webhook DAN pengecekan manual
    dari POS, supaya perilakunya sama persis. Mengembalikan Response hanya kalau error.
    """
    trx_status = verified.get("transaction_status")
    verified_gross = verified.get("gross_amount")

    # 3a) Lunas
    if trx_status == "settlement":
        if order.payment_status == "paid":
            return None  # webhook dobel, abaikan

        if order.status == "cancelled" or order.payment_status == "void":
            logger.error("Order %s dibayar SETELAH dibatalkan, perlu refund manual.", order.order_number)
            return None

        try:
            gross = Decimal(str(verified_gross))
        except InvalidOperation:
            return Response(status=400)
        if gross != order.total_price:
            logger.error("Nominal tidak cocok untuk %s: %s vs %s", order.order_number, gross, order.total_price)
            return None

        order._previous_status = order.status
        if bill_qr:
            order.payment_method = "gateway"   # nota "bayar nanti": metode baru ketahuan setelah dibayar
        order.payment_status = "paid"
        order.status = "completed"          # memicu signal poin loyalty
        order.amount_paid = order.total_price
        order.change_amount = Decimal("0")
        order.save()
        OrderPayment.objects.create(order=order, method="gateway", amount=order.total_price)

    # 3b) Gagal / kedaluwarsa → void + cancelled
    elif trx_status in ("deny", "cancel", "expire", "failure"):
        if bill_qr:
            return None          # nota tetap terbuka; QR-nya saja yang mati
        if order.payment_status not in ("paid", "void") and order.status != "cancelled":
            order._previous_status = order.status
            order.payment_status = "void"
            order.status = "cancelled"
            order.cancel_reason = "other"
            order.cancel_note = f"Pembayaran Midtrans: {trx_status}"
            order.cancelled_at = timezone.now()
            order.cancelled_by = "midtrans"
            order.save()
    return None


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
        trx_id = str(d.get("order_id", ""))
        order = (
            Order.objects.select_for_update()
            .filter(Q(order_number=trx_id, payment_method="gateway") | Q(midtrans_qr_ref=trx_id))
            .first()
        )
        if not order:
            return Response({"ok": True})
        # QR "bayar nanti" (nota yang sudah ada): hanya settlement yang mengubah nota. QR kedaluwarsa /
        # batal TIDAK boleh membatalkan nota, karena pelanggan masih bisa bayar cash atau minta QR baru.
        is_bill_qr = bool(order.midtrans_qr_ref) and trx_id == order.midtrans_qr_ref

        # 3) Konfirmasi ke Midtrans. Signature valid hanya membuktikan pengirimnya
        #    kenal server key; status & nominal yang dipakai diambil LANGSUNG dari
        #    Midtrans, bukan dari body request. Kalau Midtrans tidak terjangkau,
        #    balas 503 supaya Midtrans mengirim ulang notifikasinya nanti.
        try:
            verified = fetch_midtrans_status(trx_id)
        except Exception:
            logger.exception("Gagal konfirmasi status Midtrans untuk %s", trx_id)
            return Response({"detail": "Tidak bisa konfirmasi ke Midtrans."}, status=503)

        resp = apply_midtrans_status(order, verified, bill_qr=is_bill_qr)
        if resp is not None:
            return resp

        # "pending" → tidak ada yang perlu diubah
        return Response({"ok": True})


class PaymentStatusView(APIView):
    """GET /api/payments/status/<order_number>/ — buat polling dari frontend."""
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [PaymentStatusThrottle]

    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        return Response({"payment_status": order.payment_status, "status": order.status})


# ─────────────────────────────────────────────
# POS: QRIS dinamis (kasir menampilkan QR ke pelanggan)
# ─────────────────────────────────────────────
# Dua mode, endpoint sama:
#  A) "Bayar sekarang": order dibuat sebagai gateway/pending, transaksi Midtrans = order_number.
#     QR kedaluwarsa / dibatalkan → order dihapus bersih.
#  B) "Bayar nanti" (makan dulu / bungkus bayar setelah jadi): nota sudah ada (unpaid). Tiap QR punya
#     ID transaksi sendiri (NOMOR-Q1, -Q2, ...). QR mati TIDAK mengubah nota; bisa dibuat QR baru atau cash.

POS_QR_EXPIRY_MINUTES = 15


def _pos_qr_order(order_number):
    """
    Order yang bisa dibayar QRIS dinamis dari kasir, di-lock. 404 kalau bukan.
      A) POS "bayar sekarang": gateway + pending.
      B) Nota "bayar nanti": POS unpaid, ATAU order web yang bayar di toko (cash + pending).
    """
    return get_object_or_404(
        Order.objects.select_for_update().filter(
            Q(source="pos", payment_method="gateway", payment_status="pending")
            | Q(source="pos", payment_status="unpaid")
            | (Q(source="web", payment_status="pending") & ~Q(payment_method="gateway")),
        ),
        order_number=order_number,
    )


def _is_bill_mode(order):
    """Nota "bayar nanti" = semua order yang BUKAN gateway-pending (POS unpaid, web bayar di toko)."""
    return not (order.payment_method == "gateway" and order.payment_status == "pending")


def _trx_id(order):
    """ID transaksi Midtrans yang aktif untuk order ini."""
    return order.midtrans_qr_ref or order.order_number


def _next_ref(order):
    n = 0
    if order.midtrans_qr_ref and "-Q" in order.midtrans_qr_ref:
        try:
            n = int(order.midtrans_qr_ref.rsplit("-Q", 1)[1])
        except ValueError:
            n = 0
    return f"{order.order_number}-Q{n + 1}"


def _qr_alive(order):
    return bool(order.midtrans_qr_url and order.midtrans_qr_expires_at and order.midtrans_qr_expires_at > timezone.now())


def _qr_payload(order):
    return {
        "order_number": order.order_number,
        "total": int(order.total_price),
        "qr_url": order.midtrans_qr_url,
        "snap_token": order.midtrans_snap_token if order.midtrans_qr_url else "",
        "expires_at": order.midtrans_qr_expires_at,
        "payment_status": order.payment_status,
        "status": order.status,
        "mode": "bill" if _is_bill_mode(order) else "new",
    }


class PosQrisCreateView(APIView):
    """POST /api/payments/pos/<order_number>/qris/  → { qr_url, expires_at, total, mode, ... }"""
    permission_classes = [IsStaffLevel]

    @transaction.atomic
    def post(self, request, order_number):
        order = _pos_qr_order(order_number)

        if order.status == "cancelled" or order.payment_status == "void":
            return Response({"detail": "Order sudah dibatalkan."}, status=400)
        if order.total_price <= 0:
            return Response({"detail": "Total order Rp0, tidak perlu bayar QRIS."}, status=400)

        # QR yang masih berlaku dipakai ulang (tidak bikin transaksi kedua → tidak ada bayar dobel).
        if _qr_alive(order):
            return Response(_qr_payload(order))

        bill = _is_bill_mode(order)
        if order.midtrans_qr_url and not bill:
            return Response({"detail": "QR sudah kedaluwarsa. Batalkan lalu buat pesanan baru."}, status=410)

        old_ref = order.midtrans_qr_ref
        ref = _next_ref(order) if bill else order.order_number
        # Pakai jalur yang SAMA dengan checkout web (Snap + other_qris), karena itu yang terbukti aktif
        # di akun Midtrans. QR-nya ditampilkan frontend lewat Snap (snap.embed) memakai token ini.
        param = {
            "transaction_details": {
                "order_id": ref,
                "gross_amount": int(order.total_price),  # selalu dari DB
            },
            "enabled_payments": ["other_qris"],
            "customer_details": {
                "first_name": order.customer_name or "Customer",
                "phone": order.customer_phone or "",
            },
            "expiry": {"unit": "minutes", "duration": POS_QR_EXPIRY_MINUTES},
        }
        items = _snap_item_details(order)
        if items:
            param["item_details"] = items
        try:
            trx = snap.create_transaction(param)
        except Exception as exc:
            # Pesan asli Midtrans ikut dikirim (endpoint ini khusus staf) supaya penyebabnya langsung
            # kelihatan di layar kasir.
            code = getattr(exc, "http_status_code", None)
            reason = getattr(exc, "message", None) or str(exc) or exc.__class__.__name__
            logger.exception("Gagal membuat QRIS POS untuk %s (Midtrans %s): %s", order.order_number, code, reason)
            return Response(
                {"detail": f"Gagal membuat QR pembayaran. Midtrans: {reason}"[:300], "midtrans_status": code},
                status=502,
            )

        token = trx.get("token", "")
        if not token:
            logger.error("Respons Snap tanpa token untuk %s: %s", order.order_number, trx)
            return Response({"detail": "Midtrans tidak mengembalikan token, coba lagi."}, status=502)
        qr_url = trx.get("redirect_url") or "snap"   # penanda "QR sudah dibuat"; tampilan pakai snap_token

        order.midtrans_qr_url = qr_url
        order.midtrans_snap_token = token
        order.midtrans_qr_expires_at = timezone.now() + timedelta(minutes=POS_QR_EXPIRY_MINUTES)
        fields = ["midtrans_qr_url", "midtrans_snap_token", "midtrans_qr_expires_at"]
        if bill:
            order.midtrans_qr_ref = ref
            fields.append("midtrans_qr_ref")
        order.save(update_fields=fields)

        if bill and old_ref:   # QR lama sudah kedaluwarsa; tutup juga di sisi Midtrans (best-effort)
            transaction.on_commit(lambda: cancel_midtrans_transaction(old_ref))
        return Response(_qr_payload(order))


class PosQrisStatusView(APIView):
    """
    GET /api/payments/pos/<order_number>/status/
    Dipolling layar POS. Kalau belum lunas, status ditanyakan LANGSUNG ke Midtrans, jadi
    lunas tetap terdeteksi walau webhook telat atau belum diatur.
    """
    permission_classes = [IsStaffLevel]

    @transaction.atomic
    def get(self, request, order_number):
        order = get_object_or_404(
            Order.objects.select_for_update(), order_number=order_number, source__in=("pos", "web"),
        )

        if order.payment_status in ("pending", "unpaid") and order.midtrans_qr_url:
            try:
                verified = fetch_midtrans_status(_trx_id(order))
            except Exception:
                logger.warning("Gagal cek status Midtrans %s", order.order_number, exc_info=True)
            else:
                resp = apply_midtrans_status(order, verified, bill_qr=_is_bill_mode(order))
                if resp is not None:
                    return resp
                order.refresh_from_db()

        data = _qr_payload(order)
        data["expired"] = bool(
            order.payment_status in ("pending", "unpaid") and order.midtrans_qr_expires_at
            and order.midtrans_qr_expires_at <= timezone.now()
        )
        return Response(data)


class PosQrisCancelView(APIView):
    """
    POST /api/payments/pos/<order_number>/cancel/
    Kasir menutup QR. Mode A (bayar sekarang): order yang belum dibayar dihapus bersih (promo & poin
    dikembalikan). Mode B (bayar nanti): nota TETAP ada, hanya QR-nya yang ditutup.
    Kalau ternyata SUDAH dibayar → 409 dan nota dilunasi; uang pelanggan tidak boleh hilang.
    """
    permission_classes = [IsStaffLevel]

    @transaction.atomic
    def post(self, request, order_number):
        from order.views import _delete_order_permanently   # impor lokal: hindari impor melingkar

        order = _pos_qr_order_for_cancel(order_number)
        bill = _is_bill_mode(order)

        if order.payment_status == "paid":
            return Response({"paid": True, "detail": "Order ini sudah dibayar."}, status=409)

        if order.midtrans_qr_url:
            # Pastikan pelanggan belum bayar tepat sebelum dibatalkan.
            try:
                verified = fetch_midtrans_status(_trx_id(order))
            except Exception as exc:
                if getattr(exc, "http_status_code", None) == 404:
                    verified = {}   # Snap: pelanggan belum memilih/memindai apa pun → belum ada transaksi → belum bayar
                else:
                    logger.exception("Gagal cek status sebelum batal %s", order.order_number)
                    return Response({"detail": "Tidak bisa memastikan status ke Midtrans. Coba lagi."}, status=502)
            if verified.get("transaction_status") == "settlement":
                resp = apply_midtrans_status(order, verified, bill_qr=bill)
                if resp is not None:
                    return resp
                return Response({"paid": True, "detail": "Pelanggan ternyata sudah membayar."}, status=409)

        if bill:
            ref = order.midtrans_qr_ref
            order.midtrans_qr_url = ""
            order.midtrans_qr_expires_at = None
            order.save(update_fields=["midtrans_qr_url", "midtrans_qr_expires_at"])
            if ref:
                transaction.on_commit(lambda: cancel_midtrans_transaction(ref))
            return Response({"closed": True})

        # Mode A: order belum pernah dibayar → hapus bersih (menutup transaksi Midtrans setelah commit).
        _delete_order_permanently(order, deleted_by=getattr(request.user, "username", "") or "kasir")
        return Response({"deleted": True})


def _pos_qr_order_for_cancel(order_number):
    order = _pos_qr_order_any(order_number)
    if order.payment_status not in ("pending", "unpaid", "paid"):
        raise Http404
    return order


def _pos_qr_order_any(order_number):
    return get_object_or_404(Order.objects.select_for_update(), order_number=order_number, source__in=("pos", "web"))
