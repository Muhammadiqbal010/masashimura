"""
Ringkasan untuk staff: antrean prioritas ("perlu tindakan"), ringkasan hari, jam sibuk,
kecepatan layanan, aksi per staff. Dipakai endpoint /orders/staff-summary/, bot Telegram, dan laporan harian.

Hari = hari kalender WIB. Uang (omzet) hanya diisi bila include_money=True (peran admin/owner).
Semua angka dihitung dari data order + OrderEvent; tidak ada tabel tambahan.
"""
import datetime
from collections import Counter, defaultdict
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from .crowd import to_wib
from .models import WIB, Order, OrderEvent, OrderItem, kitchen_open_q

HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
CANCEL_LABELS = {"wrong_input": "salah input", "customer_cancel": "pelanggan batal", "out_of_stock": "stok habis", "other": "lainnya"}
UNPAID_STALE_MINUTES = 30
KIND_PRIORITY = {"awaiting": 0, "late": 1, "refund": 2, "unpaid": 3, "preparing": 4}
KIND_TAG = {"awaiting": "🛎 Terima", "late": "🔥 Telat", "refund": "↩ Refund", "unpaid": "💸 Belum bayar", "preparing": "🍳 Disiapkan"}


def _day_bounds(day):
    lo = datetime.datetime.combine(day, datetime.time.min, tzinfo=WIB)
    return lo, lo + timedelta(days=1)


def date_label(day):
    return f"{HARI[day.weekday()]}, {day.day} {BULAN[day.month - 1]} {day.year}"


def _avg_minutes(deltas):
    secs = [d.total_seconds() for d in deltas if d is not None and d.total_seconds() >= 0]
    return round(sum(secs) / len(secs) / 60, 1) if secs else None


# ── Antrean prioritas ──────────────────────────────────────────────────────

def queue_items(now=None):
    """
    Order yang perlu perhatian staff SEKARANG, terurut dari paling mendesak:
    menunggu diterima → telat → refund belum diserahkan → belum dibayar lama → sedang disiapkan.
    """
    from .guards import confirm_deadline
    from .serializers import late_minutes_setting
    from .views import GATEWAY_NOT_PAID_Q

    now = now or timezone.now()
    late_after = late_minutes_setting()
    items = []

    open_qs = (
        Order.objects.filter(kitchen_open_q(now))
        .exclude(status="cancelled").exclude(payment_status="void").exclude(GATEWAY_NOT_PAID_Q)
        .prefetch_related("items").order_by("created_at")
    )
    for o in open_qs[:300]:
        if o.awaiting_confirmation:
            left = max(int((confirm_deadline(o) - now).total_seconds() // 60), 0)
            items.append({"kind": "awaiting", "minutes": left})
        elif o.tracks_readiness and o.ready_source(now) is None:
            waited = max(int((now - o.kitchen_clock_start()).total_seconds() // 60), 0)
            items.append({"kind": "late" if waited >= late_after else "preparing", "minutes": waited})
        elif o.payment_status != "paid" and (now - o.created_at) >= timedelta(minutes=UNPAID_STALE_MINUTES):
            items.append({"kind": "unpaid", "minutes": int((now - o.created_at).total_seconds() // 60), "amount": float(o.total_price)})
        else:
            continue
        items[-1].update(id=o.pk, order_number=o.order_number, customer_name=o.customer_name)

    refunds = Order.objects.filter(refund_due__gt=0, refunded_at__isnull=True).exclude(status="cancelled").order_by("created_at")[:50]
    for o in refunds:
        items.append({
            "kind": "refund", "minutes": int((now - o.created_at).total_seconds() // 60),
            "id": o.pk, "order_number": o.order_number, "customer_name": o.customer_name, "amount": float(o.refund_due),
        })

    for it in items:
        it["tag"] = KIND_TAG[it["kind"]]
    # awaiting: sisa waktu paling kecil dulu; lainnya: yang menunggu paling lama dulu
    items.sort(key=lambda i: (KIND_PRIORITY[i["kind"]], i["minutes"] if i["kind"] == "awaiting" else -i["minutes"]))
    return items


def _queue_counts(items, include_money):
    unpaid = [i for i in items if i["kind"] == "unpaid"]
    refunds = [i for i in items if i["kind"] == "refund"]
    return {
        "awaiting": sum(1 for i in items if i["kind"] == "awaiting"),
        "late": sum(1 for i in items if i["kind"] == "late"),
        "preparing": sum(1 for i in items if i["kind"] == "preparing"),
        "unpaid": len(unpaid),
        "unpaid_total": sum(i["amount"] for i in unpaid) if include_money else None,
        "refunds": len(refunds),
        "refund_total": sum(i["amount"] for i in refunds) if include_money else None,
    }


# ── Ringkasan hari ─────────────────────────────────────────────────────────

def _official(qs):
    from .views import GATEWAY_NOT_PAID_Q
    return qs.exclude(GATEWAY_NOT_PAID_Q)


def build_summary(day=None, include_money=False, now=None):
    now = now or timezone.now()
    today = to_wib(now).date()
    day = day or today
    lo, hi = _day_bounds(day)

    rows = list(_official(Order.objects.filter(created_at__gte=lo, created_at__lt=hi)).values(
        "id", "created_at", "source", "service_type", "status", "payment_status", "total_price",
        "accepted_at", "ready_at", "cancel_reason", "cancelled_by",
    ))
    live = [r for r in rows if r["status"] != "cancelled"]
    cancelled = [r for r in rows if r["status"] == "cancelled"]

    paid_total = sum(float(r["total_price"]) for r in live if r["payment_status"] == "paid")
    reasons = Counter(CANCEL_LABELS.get(r["cancel_reason"], "lainnya") for r in cancelled)

    live_ids = [r["id"] for r in live]
    menu_qty = defaultdict(int)
    for name, bundle, qty in OrderItem.objects.filter(order_id__in=live_ids).values_list("menu__name", "bundle_name", "quantity"):
        menu_qty[bundle or name or "Item"] += qty
    items_sold = sum(menu_qty.values())
    top_menus = [{"name": n, "qty": q} for n, q in sorted(menu_qty.items(), key=lambda kv: (-kv[1], kv[0]))[:5]]

    hours = Counter(to_wib(r["created_at"]).hour for r in live)
    busy = [{"hour": h, "orders": hours[h]} for h in sorted(hours)]
    peak = max(hours, key=lambda h: (hours[h], -h)) if hours else None

    web_live = [r for r in live if r["source"] == "web"]
    accept_avg = _avg_minutes([r["accepted_at"] - r["created_at"] for r in web_live if r["accepted_at"]])
    ready_avg = _avg_minutes([r["ready_at"] - r["created_at"] for r in web_live if r["ready_at"]])

    ev = (
        OrderEvent.objects.filter(created_at__gte=lo, created_at__lt=hi, channel__in=["staff", "telegram"])
        .exclude(actor="").values("actor", "action").annotate(n=Count("id"))
    )
    staff = defaultdict(lambda: {"accepted": 0, "ready": 0, "cancelled": 0})
    for e in ev:
        if e["action"] in ("accepted", "ready", "cancelled"):
            staff[e["actor"]][e["action"]] += e["n"]
    staff_list = sorted(
        ({"actor": a, **c} for a, c in staff.items()),
        key=lambda s: -(s["accepted"] + s["ready"] + s["cancelled"]),
    )

    # Pembanding: hari yang sama minggu lalu (kalau hari ini: sampai jam yang sama)
    prev_day = day - timedelta(days=7)
    plo, phi = _day_bounds(prev_day)
    if day == today:
        phi = min(phi, plo + (to_wib(now) - lo))
    prev = list(_official(Order.objects.filter(created_at__gte=plo, created_at__lt=phi)).exclude(status="cancelled").values("payment_status", "total_price"))
    cmp_ = {
        "label": f"{HARI[prev_day.weekday()]} lalu" + (" (jam yang sama)" if day == today else ""),
        "orders": len(prev),
        "revenue": sum(float(r["total_price"]) for r in prev if r["payment_status"] == "paid") if include_money else None,
    }

    q_items = queue_items(now) if day == today else []
    return {
        "date": day.isoformat(),
        "date_label": date_label(day),
        "is_today": day == today,
        "generated_at": now.isoformat(),
        "queue": _queue_counts(q_items, include_money),
        "today": {
            "orders": len(live),
            "web": sum(1 for r in live if r["source"] == "web"),
            "pos": sum(1 for r in live if r["source"] == "pos"),
            "dine_in": sum(1 for r in live if r["service_type"] != "takeaway"),
            "takeaway": sum(1 for r in live if r["service_type"] == "takeaway"),
            "cancelled": len(cancelled),
            "auto_cancelled": sum(1 for r in cancelled if r["cancelled_by"] == "sistem"),
            "cancel_reasons": dict(reasons),
            "items_sold": items_sold,
            "revenue": paid_total if include_money else None,
            "avg_order": round(paid_total / max(sum(1 for r in live if r["payment_status"] == "paid"), 1)) if include_money and paid_total else None,
        },
        "compare": cmp_,
        "busy_hours": busy,
        "peak_hour": peak,
        "service": {"avg_accept_minutes": accept_avg, "avg_ready_minutes": ready_avg},
        "top_menus": top_menus,
        "staff": staff_list,
    }


def send_daily_report(day=None, now=None):
    """Bangun laporan harian lengkap (dengan omzet) dan kirim ke semua chat Telegram terdaftar."""
    from . import notify, report_format

    summary = build_summary(day=day, include_money=True, now=now)
    return notify.send_report(report_format.format_daily_report(summary))
