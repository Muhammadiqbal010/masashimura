"""
Aksi staff pada order: terima, batalkan, siap diambil.

Satu sumber logika untuk dua pintu masuk: tombol di Active Orders (views.py) dan tombol di Telegram
(telegram_bot.py). Pemanggil menangkap ActionError dan menerjemahkannya ke respons masing-masing.
Semua aksi idempotent: menekan dua kali (apalagi dari dua HP) tidak merusak data.
"""
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from payments.services import cancel_midtrans_transaction

from . import events, guards
from .models import CANCEL_REASON_CHOICES, Order

CANCEL_REASON_LABELS = dict(CANCEL_REASON_CHOICES)


class ActionError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def _auto_cancel_text(order):
    return (
        "Order ini sudah dibatalkan otomatis "
        f"(tidak diterima dalam {guards.CONFIRM_TIMEOUT_MINUTES} menit)."
    )


def accept(pk, actor="", channel="staff"):
    """Terima order web bayar-di-toko. Mengembalikan (order, changed)."""
    guards.expire_unconfirmed_orders()   # kalau sudah lewat batas waktu, order dibatalkan dulu
    with transaction.atomic():
        order = get_object_or_404(Order.objects.select_for_update(), pk=pk)
        if order.status == "cancelled":
            raise ActionError(
                _auto_cancel_text(order) if order.cancelled_by == "sistem" else "Order ini sudah dibatalkan.",
                status=409,
            )
        changed = guards.accept_now(order)
        if changed:
            order.save(update_fields=["awaiting_confirmation", "accepted_at", "updated_at"])
            events.record(order, "accepted", actor=actor, channel=channel)
    return order, changed


def cancel(pk, reason, note="", actor="", channel="staff", cancelled_by=""):
    """Void order dengan alasan wajib. Order tidak dihapus, hanya diubah statusnya."""
    reason = (reason or "").strip()
    note = (note or "").strip()
    if reason not in CANCEL_REASON_LABELS:
        raise ActionError("Alasan pembatalan wajib diisi dan harus valid.", status=400)

    with transaction.atomic():
        order = get_object_or_404(Order.objects.select_for_update(), pk=pk)
        previous_status = order.status
        was_gateway_pending = order.payment_method == "gateway" and order.payment_status == "pending"

        if order.status == "completed":
            raise ActionError("Order yang sudah selesai (completed) tidak bisa dibatalkan lewat sini.", status=400)
        if order.status == "cancelled":
            raise ActionError("Order ini sudah dibatalkan sebelumnya.", status=400)

        order.status = "cancelled"
        order.payment_status = "void"
        order.awaiting_confirmation = False
        order.cancel_reason = reason
        order.cancel_note = note[:255]
        order.cancelled_at = timezone.now()
        order.cancelled_by = (cancelled_by or actor or "")[:100]
        order._previous_status = previous_status
        order.save()

        label = CANCEL_REASON_LABELS[reason]
        events.record(order, "cancelled", actor=actor or cancelled_by, channel=channel,
                      note=f"{label}: {note}" if note else label)

        # Tutup transaksi di Midtrans supaya QR lama tidak bisa dibayar lagi.
        if was_gateway_pending:
            order_number = order.order_number
            transaction.on_commit(lambda: cancel_midtrans_transaction(order_number))
        elif order.midtrans_qr_ref:
            qr_ref = order.midtrans_qr_ref
            transaction.on_commit(lambda: cancel_midtrans_transaction(qr_ref))

    order.refresh_from_db()
    return order


def set_ready(pk, ready=True, actor="", channel="staff"):
    """Tandai siap diambil / cabut tandanya. Mengembalikan (order, changed)."""
    with transaction.atomic():
        order = get_object_or_404(Order.objects.select_for_update(), pk=pk)
        if order.status == "cancelled" or order.payment_status == "void":
            raise ActionError("Order ini sudah dibatalkan.", status=400)
        if not order.tracks_readiness:
            raise ActionError("Order POS tidak memakai status siap (pelanggan sudah di warung).", status=400)
        if ready and order.awaiting_confirmation:
            raise ActionError("Terima order ini dulu sebelum menandainya siap.", status=400)

        already = order.ready_at is not None
        if ready == already:
            return order, False
        order.ready_at = timezone.now() if ready else None
        order.save(update_fields=["ready_at"])
        events.record(order, "ready" if ready else "unready", actor=actor, channel=channel)
    order.refresh_from_db()
    return order, True
