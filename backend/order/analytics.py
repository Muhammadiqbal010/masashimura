"""
Analitik menu untuk admin: Performa Menu, Pasangan Menu, dan Channel.

Semua memakai definisi order yang sama dengan laporan omzet: sudah dibayar
(payment_status='paid') dan tidak dibatalkan. Periode mengikuti parameter
order_full_report (period, days, offset, month, year), dengan batas hari
dihitung di WIB.

Tidak ada model baru dan tidak ada state: semua dihitung saat dibaca.
"""
import calendar
import datetime
from collections import Counter, defaultdict
from datetime import timedelta
from itertools import combinations

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.utils import timezone

from .crowd import DAY_NAMES, _demand_orders, schedule_for, to_wib
from .models import Order, OrderItem, PAYMENT_METHOD_CHOICES, WIB

MIN_ITEMS_FOR_CLASSES = 30      # di bawah ini pengelompokan menu dianggap belum meyakinkan
POPULAR_FACTOR = 0.7            # menu populer bila terjual >= 70% rata-rata (metode Kasavana-Smith)
PAIR_MIN_COUNT_DEFAULT = 2
PAIR_CANDIDATE_MIN_COUNT = 3    # kandidat paket: muncul bersama >= 3 kali dan lift > 1
PAIR_LIMIT = 20
DAILY_TREND_MAX_DAYS = 92       # lebih panjang dari ini, tren digabung per bulan

LINE_TOTAL = ExpressionWrapper(F("price") * F("quantity"), output_field=DecimalField())

CHANNEL_LABELS = {"web": "Web (pelanggan)", "pos": "POS (kasir)"}
BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


# ─────────────────────────────────────────────
# PERIODE & BASE QUERYSET
# ─────────────────────────────────────────────

def _int(params, name, default):
    try:
        return int(params.get(name, default))
    except (TypeError, ValueError):
        return default


def resolve_period(params, now=None):
    """
    Return (start_date | None, end_date | None). None/None = lifetime.
    Parameter sama dengan order_full_report: period=lifetime|week|month|year,
    days (7/14/28/30), offset, month, year.
    """
    today = to_wib(now or timezone.now()).date()
    period = params.get("period", "lifetime")
    year = _int(params, "year", today.year)
    month = _int(params, "month", today.month)
    days = _int(params, "days", 7)
    offset = max(0, _int(params, "offset", 0))

    if days not in (7, 14, 28, 30):
        days = 7
    if not 1 <= month <= 12:
        month = today.month
    if not 1970 <= year <= 2100:
        year = today.year

    if period == "week":
        end = today - timedelta(days=offset)
        return end - timedelta(days=days - 1), end
    if period == "month":
        return datetime.date(year, month, 1), datetime.date(year, month, calendar.monthrange(year, month)[1])
    if period == "year":
        return datetime.date(year, 1, 1), datetime.date(year, 12, 31)
    return None, None


def qualifying_orders(start, end):
    qs = Order.objects.filter(payment_status="paid").exclude(status="cancelled")
    if start and end:
        lo = datetime.datetime.combine(start, datetime.time.min, tzinfo=WIB)
        hi = datetime.datetime.combine(end + timedelta(days=1), datetime.time.min, tzinfo=WIB)
        qs = qs.filter(created_at__gte=lo, created_at__lt=hi)
    return qs


def _period_info(start, end):
    return {"start": start.isoformat() if start else None, "end": end.isoformat() if end else None}


# ─────────────────────────────────────────────
# PERFORMA MENU
# ─────────────────────────────────────────────

CLASS_LABELS = {
    "bintang":   "Bintang",
    "andalan":   "Andalan",
    "potensial": "Potensial",
    "evaluasi":  "Perlu evaluasi",
}
CLASS_HINTS = {
    "bintang":   "Laris dan harganya tinggi. Pertahankan.",
    "andalan":   "Laris tetapi harga per porsi rendah. Coba bundel dengan menu berharga lebih tinggi.",
    "potensial": "Harga tinggi tetapi kurang terjual. Layak didorong lewat promo atau posisi di menu.",
    "evaluasi":  "Kurang terjual dan harga rendah. Pertimbangkan ubah, ganti, atau hapus.",
}


def menu_performance(params, now=None):
    """
    Volume, kontribusi omzet, dan pengelompokan tiap menu aktif.

    Pengelompokan (mirip menu engineering, tetapi tanpa data HPP):
      - Populer  : terjual >= 70% dari rata-rata porsi per menu aktif.
      - Harga tinggi: harga rata-rata per porsi >= harga rata-rata tertimbang seluruh penjualan.
        Harga dipakai sebagai pendekatan margin karena biaya bahan tidak tercatat.
    """
    from menu.models import Menu

    start, end = resolve_period(params, now)
    order_ids = qualifying_orders(start, end).values("id")

    sold = {
        row["menu_id"]: row
        for row in (
            OrderItem.objects.filter(order_id__in=order_ids, menu__isnull=False)
            .values("menu_id")
            .annotate(qty=Sum("quantity"), revenue=Sum(LINE_TOTAL), orders=Count("order_id", distinct=True))
        )
    }

    menus = list(Menu.objects.filter(is_active=True).select_related("category"))
    total_qty = sum(int(r["qty"] or 0) for r in sold.values())
    total_rev = sum(float(r["revenue"] or 0) for r in sold.values())
    weighted_price = (total_rev / total_qty) if total_qty else 0
    avg_qty = (total_qty / len(menus)) if menus else 0
    popular_min = POPULAR_FACTOR * avg_qty

    rows = []
    for m in menus:
        s = sold.get(m.id)
        qty = int(s["qty"]) if s else 0
        rev = float(s["revenue"] or 0) if s else 0.0
        unit = (rev / qty) if qty else float(m.price)
        popular = qty >= popular_min and qty > 0
        high_price = unit >= weighted_price if weighted_price else False
        if popular and high_price:
            cls = "bintang"
        elif popular:
            cls = "andalan"
        elif high_price:
            cls = "potensial"
        else:
            cls = "evaluasi"
        rows.append({
            "id": m.id,
            "name": m.name,
            "category": m.category.name if m.category else None,
            "price": float(m.price),
            "qty": qty,
            "orders": int(s["orders"]) if s else 0,
            "revenue": rev,
            "revenue_share": round(rev / total_rev * 100, 1) if total_rev else 0,
            "unit_price": round(unit),
            "class": cls,
            "class_label": CLASS_LABELS[cls],
        })

    rows.sort(key=lambda r: (-r["revenue"], -r["qty"], r["name"]))

    summary = {k: 0 for k in CLASS_LABELS}
    for r in rows:
        summary[r["class"]] += 1

    return {
        "period": _period_info(start, end),
        "enough_data": total_qty >= MIN_ITEMS_FOR_CLASSES,
        "min_items_required": MIN_ITEMS_FOR_CLASSES,
        "total_qty": total_qty,
        "total_revenue": total_rev,
        "thresholds": {
            "popular_min_qty": round(popular_min, 1),
            "avg_unit_price": round(weighted_price),
            "avg_qty_per_menu": round(avg_qty, 1),
        },
        "class_labels": CLASS_LABELS,
        "class_hints": CLASS_HINTS,
        "summary": summary,
        "menus": rows,
    }


# ─────────────────────────────────────────────
# PASANGAN MENU
# ─────────────────────────────────────────────

def menu_pairs(params, now=None):
    """
    Menu yang sering dipesan dalam satu order.

    Untuk pasangan (A, B):
      count      = jumlah order yang memuat keduanya
      support    = count / total order
      confidence = P(B | A) dan P(A | B)
      lift       = support(A,B) / (support(A) * support(B)); > 1 berarti lebih sering
                   bersama daripada kebetulan.
    Item tukar poin tidak dihitung (bukan pilihan beli).
    """
    start, end = resolve_period(params, now)
    min_count = max(2, _int(params, "min_count", PAIR_MIN_COUNT_DEFAULT))
    order_ids = qualifying_orders(start, end).values("id")
    total_orders = qualifying_orders(start, end).count()

    baskets = defaultdict(set)
    names = {}
    rows = (
        OrderItem.objects.filter(order_id__in=order_ids, menu__isnull=False, is_point_redemption=False)
        .values_list("order_id", "menu_id", "menu__name")
    )
    for order_id, menu_id, name in rows:
        baskets[order_id].add(menu_id)
        names[menu_id] = name

    single = Counter()
    pair = Counter()
    multi = 0
    for items in baskets.values():
        single.update(items)
        if len(items) >= 2:
            multi += 1
            pair.update(combinations(sorted(items), 2))

    result = []
    for (a, b), count in pair.items():
        if count < min_count:
            continue
        support = count / total_orders
        lift = support / ((single[a] / total_orders) * (single[b] / total_orders))
        result.append({
            "a": {"id": a, "name": names[a]},
            "b": {"id": b, "name": names[b]},
            "count": count,
            "support": round(support * 100, 1),
            "confidence_a_to_b": round(count / single[a] * 100, 1),
            "confidence_b_to_a": round(count / single[b] * 100, 1),
            "lift": round(lift, 2),
            "bundle_candidate": count >= PAIR_CANDIDATE_MIN_COUNT and lift > 1,
        })
    result.sort(key=lambda r: (-r["count"], -r["lift"], r["a"]["name"], r["b"]["name"]))

    return {
        "period": _period_info(start, end),
        "total_orders": total_orders,
        "multi_item_orders": multi,
        "min_count": min_count,
        "enough_data": multi >= 10,
        "pairs": result[:PAIR_LIMIT],
        "pairs_total": len(result),
    }


# ─────────────────────────────────────────────
# CHANNEL
# ─────────────────────────────────────────────

def channels(params, now=None):
    """Per channel pesanan (web / POS): omzet, jumlah order, rata-rata order, metode bayar, dan tren."""
    start, end = resolve_period(params, now)
    qs = qualifying_orders(start, end)
    method_labels = dict(PAYMENT_METHOD_CHOICES)

    rows = list(qs.values_list("created_at", "source", "total_price", "payment_method"))
    item_qty = {
        r["order__source"]: int(r["qty"] or 0)
        for r in (
            OrderItem.objects.filter(order_id__in=qs.values("id"))
            .values("order__source").annotate(qty=Sum("quantity"))
        )
    }

    agg = {}
    pay = defaultdict(lambda: defaultdict(lambda: {"count": 0, "total": 0.0}))
    daily = defaultdict(lambda: defaultdict(float))
    dates = []

    for created, source, total, method in rows:
        total = float(total or 0)
        a = agg.setdefault(source, {"orders": 0, "revenue": 0.0})
        a["orders"] += 1
        a["revenue"] += total
        p = pay[source][method or "-"]
        p["count"] += 1
        p["total"] += total
        d = to_wib(created).date()
        dates.append(d)
        daily[d][source] += total

    grand_orders = sum(a["orders"] for a in agg.values())
    grand_rev = sum(a["revenue"] for a in agg.values())

    out_channels = []
    for source in sorted(agg, key=lambda s: -agg[s]["revenue"]):
        a = agg[source]
        out_channels.append({
            "source": source,
            "label": CHANNEL_LABELS.get(source, source),
            "orders": a["orders"],
            "revenue": a["revenue"],
            "avg_order": round(a["revenue"] / a["orders"]) if a["orders"] else 0,
            "items_per_order": round(item_qty.get(source, 0) / a["orders"], 1) if a["orders"] else 0,
            "order_share": round(a["orders"] / grand_orders * 100, 1) if grand_orders else 0,
            "revenue_share": round(a["revenue"] / grand_rev * 100, 1) if grand_rev else 0,
            "payment_methods": [
                {
                    "method": m,
                    "label": method_labels.get(m, "Tidak tercatat"),
                    "count": v["count"],
                    "total": v["total"],
                    "share": round(v["count"] / a["orders"] * 100, 1),
                }
                for m, v in sorted(pay[source].items(), key=lambda kv: -kv[1]["count"])
            ],
        })

    # Tren: harian bila rentang pendek, bulanan bila panjang.
    trend = {"unit": "day", "labels": [], "series": {s: [] for s in CHANNEL_LABELS}}
    if dates:
        first, last = start or min(dates), end or max(dates)
        if (last - first).days + 1 > DAILY_TREND_MAX_DAYS:
            trend["unit"] = "month"
            buckets = defaultdict(lambda: defaultdict(float))
            for d, per in daily.items():
                for s, v in per.items():
                    buckets[(d.year, d.month)][s] += v
            keys, y, m = [], first.year, first.month
            while (y, m) <= (last.year, last.month):
                keys.append((y, m))
                y, m = (y + 1, 1) if m == 12 else (y, m + 1)
            trend["labels"] = [f"{BULAN[m - 1]} {str(y)[2:]}" for y, m in keys]
            for s in trend["series"]:
                trend["series"][s] = [buckets[k][s] for k in keys]
        else:
            days = [first + timedelta(days=i) for i in range((last - first).days + 1)]
            trend["labels"] = [f"{d.day} {BULAN[d.month - 1]}" for d in days]
            for s in trend["series"]:
                trend["series"][s] = [daily[d][s] if d in daily else 0 for d in days]

    return {
        "period": _period_info(start, end),
        "total_orders": grand_orders,
        "total_revenue": grand_rev,
        "enough_data": grand_orders >= 10,
        "channels": out_channels,
        "trend": trend,
    }


# ─────────────────────────────────────────────
# PERKIRAAN MENU BESOK (persiapan)
# ─────────────────────────────────────────────

TOMORROW_WEEKS = 8              # berapa hari yang sama (mis. Selasa) ke belakang yang dilihat
TOMORROW_DECAY = 0.8            # bobot hari ke-k terbaru = 0.8 ** k (sama dengan baseline omzet)
TOMORROW_MIN_SAMPLE_DAYS = 3    # di bawah ini pola dianggap belum meyakinkan
TOMORROW_HIGH_RATIO = 0.6       # skor >= 60% skor peringkat 1 = "tinggi", selebihnya "sedang"
TOMORROW_LIMIT = 5

TOMORROW_LABELS = {"tinggi": "Tinggi", "sedang": "Sedang"}


def menu_tomorrow(store, now=None):
    """
    Peringkat 5 menu yang diperkirakan paling banyak dipesan BESOK, dari pola
    penjualan hari yang sama dalam beberapa minggu terakhir (minggu terbaru
    berbobot lebih besar). Hanya peringkat dan label tinggi/sedang, tanpa angka porsi.

    Ini pola historis, BUKAN keluaran model prediksi omzet.

    Definisi penjualan = permintaan nyata (order tidak dibatalkan dan tidak void,
    termasuk yang belum lunas), karena dapur menyiapkan menu untuk semua pesanan itu.
    Hari tanpa satu pun pesanan dianggap toko tidak buka dan tidak ikut dihitung.
    Besok libur rutin -> tidak ada perkiraan.
    """
    now_wib = to_wib(now or timezone.now())
    target = now_wib.date() + timedelta(days=1)
    dow = target.weekday()

    base = {
        "target_date": target.isoformat(),
        "day_name": DAY_NAMES[dow],
        "closed": False,
        "weeks": TOMORROW_WEEKS,
        "sample_days": 0,
        "enough_data": False,
        "min_sample_days": TOMORROW_MIN_SAMPLE_DAYS,
        "basis": "Pola penjualan historis hari yang sama. Bukan keluaran model prediksi omzet.",
        "menus": [],
    }

    if schedule_for(store, dow) is None:
        return {**base, "closed": True}

    days = [target - timedelta(days=7 * k) for k in range(1, TOMORROW_WEEKS + 1)]
    window = Q()
    for d in days:
        lo = datetime.datetime.combine(d, datetime.time.min, tzinfo=WIB)
        window |= Q(order__created_at__gte=lo, order__created_at__lt=lo + timedelta(days=1))

    rows = (
        OrderItem.objects
        .filter(order_id__in=_demand_orders().values("id"), menu__isnull=False, menu__is_active=True)
        .filter(window)
        .values_list("order__created_at", "menu_id", "menu__name", "quantity")
    )

    per_day = defaultdict(lambda: defaultdict(int))     # tanggal -> menu_id -> porsi
    names = {}
    for created, menu_id, name, qty in rows:
        per_day[to_wib(created).date()][menu_id] += int(qty or 0)
        names[menu_id] = name

    sample = sorted(per_day, reverse=True)               # hari yang ada penjualan, terbaru dulu
    if not sample:
        return base

    weights = [TOMORROW_DECAY ** k for k in range(len(sample))]
    total_w = sum(weights)
    score = defaultdict(float)
    sold_days = defaultdict(int)
    for w, d in zip(weights, sample):
        for menu_id, qty in per_day[d].items():
            score[menu_id] += w * qty
            sold_days[menu_id] += 1

    ranked = sorted(score, key=lambda m: (-score[m], names[m]))[:TOMORROW_LIMIT]
    top = score[ranked[0]] if ranked else 0
    menus = []
    for i, menu_id in enumerate(ranked, start=1):
        level = "tinggi" if top and score[menu_id] >= TOMORROW_HIGH_RATIO * top else "sedang"
        menus.append({
            "rank": i,
            "id": menu_id,
            "name": names[menu_id],
            "level": level,
            "level_label": TOMORROW_LABELS[level],
            "sold_days": sold_days[menu_id],
        })

    return {
        **base,
        "sample_days": len(sample),
        "enough_data": len(sample) >= TOMORROW_MIN_SAMPLE_DAYS,
        "menus": menus,
        "total_weight": round(total_w, 2),
    }

