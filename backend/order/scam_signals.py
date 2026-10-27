"""
Sinyal tambahan untuk menilai order web (di luar IP/lokasi): jam order, besar porsi, catatan berisi link.
Semua murah (beberapa query ringan) dan hanya dipakai untuk TANDA di Telegram, tidak pernah menolak order.
"""
from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from . import client_info as ci

BASELINE_DAYS = 30
BASELINE_MIN_ORDERS = 10   # kurang dari ini: rata-rata porsi belum bisa dipercaya, tanda porsi dimatikan


def after_hours(dt):
    """True kalau `dt` jatuh di luar jam buka menurut jadwal StoreSettings. Jadwal kosong = tidak pernah True."""
    from . import crowd
    from .models import StoreSettings

    store = StoreSettings.objects.filter(pk=1).first()
    if not store or not (store.operating_hours or {}):
        return False
    local = crowd.to_wib(dt)
    sched = crowd.schedule_for(store, local.weekday())
    if not sched:
        return True   # hari libur menurut jadwal
    minutes = local.hour * 60 + local.minute
    return not (sched[0] <= minutes < sched[1])


def order_portions(order):
    return order.items.aggregate(n=Sum("quantity"))["n"] or 0


def avg_portions(exclude_pk=None, now=None):
    """Rata-rata porsi per pesanan (30 hari terakhir, tanpa yang batal). 0 kalau datanya belum cukup."""
    from .models import Order, OrderItem

    since = (now or timezone.now()) - timedelta(days=BASELINE_DAYS)
    orders = Order.objects.filter(created_at__gte=since).exclude(status="cancelled").exclude(payment_status="void")
    if exclude_pk:
        orders = orders.exclude(pk=exclude_pk)
    count = orders.count()
    if count < BASELINE_MIN_ORDERS:
        return 0
    total = OrderItem.objects.filter(order__in=orders).aggregate(n=Sum("quantity"))["n"] or 0
    return total / count


def notes_have_link(order):
    if ci.has_link(order.notes):
        return True
    return any(ci.has_link(n) for n in order.items.values_list("notes", flat=True) if n)
