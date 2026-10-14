"""
Efektivitas Promo dan Poin (#15).

Datanya sudah ada (Order.promo, Order.promo_discount_amount, Order.loyalty_points_earned,
PointAdjustment, OrderItem.is_point_redemption), jadi tidak ada model baru: satu endpoint
agregasi per halaman. Order yang dihitung sama dengan laporan omzet (lunas, tidak
dibatalkan). Parameter periode sama dengan analitik lain: period, days, offset, month, year.
"""
import datetime
from datetime import timedelta

from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

from .analytics import _period_info, qualifying_orders, resolve_period
from .models import CustomerLoyalty, OrderItem, PointAdjustment, PointReward, WIB
from .segmentation import ACTIVE_DAYS

MIN_ORDERS_PER_GROUP = 5     # di bawah ini perbandingan dengan vs tanpa promo belum meyakinkan
REDEEM_NOTE_PREFIX = "Redeem reward saat order"
TOP_REWARDS = 5


def _f(value):
    return float(value or 0)


def _in_period(qs, start, end, field="created_at"):
    """Filter hari WIB start..end pada field datetime, sama seperti qualifying_orders."""
    if not (start and end):
        return qs
    lo = datetime.datetime.combine(start, datetime.time.min, tzinfo=WIB)
    hi = datetime.datetime.combine(end + timedelta(days=1), datetime.time.min, tzinfo=WIB)
    return qs.filter(**{f"{field}__gte": lo, f"{field}__lt": hi})


# ─────────────────────────────────────────────
# PROMO
# ─────────────────────────────────────────────

def promo_effectiveness(params, now=None):
    from promotions.models import Promo

    now = now or timezone.now()
    start, end = resolve_period(params, now)
    orders = qualifying_orders(start, end)
    has_promo = Q(promo__isnull=False) | Q(promo_discount_amount__gt=0)

    with_promo = orders.filter(has_promo)
    without_promo = orders.exclude(has_promo)

    w = with_promo.aggregate(n=Count("id"), disc=Sum("promo_discount_amount"),
                             basket=Avg("subtotal"), paid=Avg("total_price"))
    wo = without_promo.aggregate(n=Count("id"), basket=Avg("subtotal"), paid=Avg("total_price"))
    n_with, n_without = w["n"] or 0, wo["n"] or 0
    enough = n_with >= MIN_ORDERS_PER_GROUP and n_without >= MIN_ORDERS_PER_GROUP

    basket_with, basket_without = _f(w["basket"]), _f(wo["basket"])
    basket_diff_pct = None
    if enough and basket_without > 0:
        basket_diff_pct = round((basket_with - basket_without) / basket_without * 100, 1)

    # Per promo (berdasarkan order di periode ini). Promo tanpa order tetap tampil agar
    # kelihatan mana yang tidak pernah dipakai.
    per_promo = {
        row["promo_id"]: row
        for row in with_promo.filter(promo__isnull=False).values("promo_id").annotate(
            n=Count("id"), disc=Sum("promo_discount_amount"), basket=Avg("subtotal"),
        )
    }
    promos = []
    for p in Promo.objects.all():
        row = per_promo.get(p.id)
        if not row and not p.is_active:
            continue   # promo nonaktif tanpa pemakaian di periode ini tidak perlu ditampilkan
        promos.append({
            "id": p.id,
            "code": p.code,
            "description": p.description,
            "is_active": p.is_active,
            "expired": p.valid_until < now,
            "orders": row["n"] if row else 0,
            "discount_total": _f(row["disc"]) if row else 0.0,
            "avg_basket": _f(row["basket"]) if row else 0.0,
            "used_count": p.used_count,
            "max_usage": p.max_usage,
        })
    promos.sort(key=lambda r: (-r["orders"], r["code"]))

    return {
        "period": _period_info(start, end),
        "enough_data": enough,
        "min_orders_per_group": MIN_ORDERS_PER_GROUP,
        "totals": {
            "orders": n_with + n_without,
            "orders_with_promo": n_with,
            "orders_without_promo": n_without,
            "discount_total": _f(w["disc"]),
        },
        "comparison": {
            "avg_basket_with": basket_with,
            "avg_basket_without": basket_without,
            "avg_paid_with": _f(w["paid"]),
            "avg_paid_without": _f(wo["paid"]),
            "basket_diff_pct": basket_diff_pct,
        },
        "promos": promos,
        "note": (
            "Perbandingan nilai keranjang (sebelum diskon) antara order dengan dan tanpa promo. "
            "Ini selisih rata-rata, bukan bukti bahwa promo yang menyebabkan keranjang lebih besar."
        ),
    }


# ─────────────────────────────────────────────
# POIN
# ─────────────────────────────────────────────

def point_effectiveness(params, now=None):
    now = now or timezone.now()
    start, end = resolve_period(params, now)
    orders = qualifying_orders(start, end)

    issued = orders.filter(loyalty_applied=True).aggregate(p=Sum("loyalty_points_earned"))["p"] or 0

    adj = _in_period(PointAdjustment.objects.all(), start, end)
    redeemed = -(adj.filter(amount__lt=0, note__startswith=REDEEM_NOTE_PREFIX)
                 .aggregate(p=Sum("amount"))["p"] or 0)
    expired = -(adj.filter(reason="expired").aggregate(p=Sum("amount"))["p"] or 0)
    manual = adj.filter(reason="manual").exclude(note__startswith=REDEEM_NOTE_PREFIX)
    manual_added = manual.filter(amount__gt=0).aggregate(p=Sum("amount"))["p"] or 0
    manual_removed = -(manual.filter(amount__lt=0).aggregate(p=Sum("amount"))["p"] or 0)

    redeem_rate = round(redeemed / issued * 100, 1) if issued > 0 else None

    # Reward paling sering ditukar: dari item order bertanda tukar poin.
    cost_by_menu = {}
    for r in PointReward.objects.all().order_by("point_cost"):
        cost_by_menu.setdefault(r.menu_id, r.point_cost)
    redeemed_items = (
        OrderItem.objects.filter(order__in=orders, is_point_redemption=True, menu__isnull=False)
        .values("menu_id", "menu__name").annotate(n=Sum("quantity")).order_by("-n", "menu__name")
    )
    top_rewards = [
        {
            "menu_id": row["menu_id"],
            "name": row["menu__name"],
            "times": row["n"],
            "point_cost": cost_by_menu.get(row["menu_id"]),
            "points_estimate": row["n"] * cost_by_menu[row["menu_id"]] if row["menu_id"] in cost_by_menu else None,
        }
        for row in redeemed_items[:TOP_REWARDS]
    ]
    redemption_orders = orders.filter(items__is_point_redemption=True).distinct().count()

    members = CustomerLoyalty.objects.aggregate(
        total=Count("id"),
        with_points=Count("id", filter=Q(points__gt=0)),
        outstanding=Sum("points"),
    )
    active_members = CustomerLoyalty.objects.filter(
        last_order_at__gte=now - timedelta(days=ACTIVE_DAYS),
    ).count()

    return {
        "period": _period_info(start, end),
        "points": {
            "issued": issued,
            "redeemed": redeemed,
            "expired": expired,
            "manual_added": manual_added,
            "manual_removed": manual_removed,
            "redeem_rate_pct": redeem_rate,
        },
        "redemption_orders": redemption_orders,
        "top_rewards": top_rewards,
        "members": {
            "total": members["total"] or 0,
            "with_points": members["with_points"] or 0,
            "outstanding_points": members["outstanding"] or 0,
            "active_last_days": ACTIVE_DAYS,
            "active": active_members,
        },
        "note": (
            "Poin terbit dihitung dari order lunas di periode ini. Poin tertukar dan hangus dihitung dari "
            "catatan penyesuaian poin. Total poin reward adalah estimasi memakai biaya poin saat ini."
        ),
    }
