"""
Ringkasan Order Reports (tab pertama) untuk admin.

Definisi order sama dengan tab analitik lain: sudah dibayar (payment_status='paid') dan tidak
dibatalkan. Batas hari dihitung di WIB lewat analytics.resolve_period / qualifying_orders, jadi
angka Ringkasan, Performa Menu, Pasangan Menu, dan Channel selalu sebanding.

Dibanding versi lama (order_full_report di views.py):
  - perbandingan dengan periode sebelumnya (delta omzet / transaksi / rata-rata / porsi)
  - tren tidak lagi bolong: hari tanpa order tetap tampil 0, dan digabung per bulan bila terlalu panjang
  - rata-rata bergerak 7 hari untuk tren harian
  - omzet per kategori, per jenis layanan, per hari dalam seminggu
  - distribusi jam penuh (bukan hanya 5 jam teratas yang disortir berdasarkan jam)
  - ringkasan: hari terbaik, rata-rata omzet per hari aktif, diskon yang diberikan
  - menu tanpa nama (menu terhapus) tidak lagi muncul sebagai "None" di Top Menu
Semua key lama tetap ada supaya klien lain tidak rusak.
"""
import calendar
import datetime
from zoneinfo import ZoneInfo
from collections import defaultdict
from datetime import timedelta

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Min, Q, Sum
from django.db.models.functions import ExtractHour

from .analytics import BULAN, resolve_period, qualifying_orders
from .crowd import to_wib
from .models import (
    CustomerLoyalty, Order, OrderItem,
    ORDER_SERVICE_TYPE_CHOICES, PAYMENT_METHOD_CHOICES, WIB,
)

# Offset tetap (WIB) menghasilkan nama zona "+0700" yang diubah Django jadi "-0700:00" dan ditolak
# PostgreSQL. Untuk konversi di sisi database pakai zona bernama; Jakarta tanpa DST, hasilnya sama.
WIB_DB_TZ = ZoneInfo("Asia/Jakarta")

HARI = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
HARI_PENUH = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
DAILY_TREND_MAX_DAYS = 92
MOVING_AVG_WINDOW = 7
TOP_LIMIT = 10

LINE_TOTAL = ExpressionWrapper(F("price") * F("quantity"), output_field=DecimalField())
SERVICE_LABELS = dict(ORDER_SERVICE_TYPE_CHOICES)


# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────

def _pct_change(cur, prev):
    """Persen perubahan; None bila periode sebelumnya kosong (tidak bisa dibandingkan)."""
    if not prev:
        return None
    return round((cur - prev) / prev * 100, 1)


def _share(part, whole):
    return round(part / whole * 100, 1) if whole else 0


def _previous_period(params, start, end):
    """(start, end, label) periode pembanding. Lifetime tidak punya pembanding."""
    if not start or not end:
        return None, None, None
    mode = params.get("period", "lifetime")
    if mode == "week":
        length = (end - start).days + 1
        p_end = start - timedelta(days=1)
        p_start = p_end - timedelta(days=length - 1)
        label = "periode sebelumnya"
        if length == 7:
            label = "minggu sebelumnya"
        return p_start, p_end, label
    if mode == "month":
        y, m = (start.year - 1, 12) if start.month == 1 else (start.year, start.month - 1)
        return (
            datetime.date(y, m, 1),
            datetime.date(y, m, calendar.monthrange(y, m)[1]),
            f"{BULAN[m - 1]} {y}",
        )
    if mode == "year":
        y = start.year - 1
        return datetime.date(y, 1, 1), datetime.date(y, 12, 31), str(y)
    return None, None, None


def _totals(qs):
    agg = qs.aggregate(omzet=Sum("total_price"), trx=Count("id"))
    omzet = float(agg["omzet"] or 0)
    trx = agg["trx"] or 0
    porsi = int(
        OrderItem.objects.filter(order_id__in=qs.values("id")).aggregate(q=Sum("quantity"))["q"] or 0
    )
    return {
        "omzet": omzet,
        "transaksi": trx,
        "rata_rata": (omzet / trx) if trx else 0.0,
        "porsi": porsi,
    }


def _daily_map(qs):
    """tanggal (WIB) -> [omzet, jumlah order]. Satu sumber untuk tren dan hari terbaik."""
    per_day = defaultdict(lambda: [0.0, 0])
    for created, total in qs.values_list("created_at", "total_price"):
        d = to_wib(created).date()
        per_day[d][0] += float(total or 0)
        per_day[d][1] += 1
    return per_day


def _trend(per_day, start, end):
    """Deret omzet/transaksi tanpa lubang. Harian bila rentang <= 92 hari, selebihnya bulanan."""
    if not per_day and not (start and end):
        return {"unit": "day", "labels": [], "dates": [], "omzet": [], "transaksi": [], "moving_avg": []}

    first = start or min(per_day)
    last = end or max(per_day)

    if (last - first).days + 1 > DAILY_TREND_MAX_DAYS:
        buckets = defaultdict(lambda: [0.0, 0])
        for d, (o, t) in per_day.items():
            buckets[(d.year, d.month)][0] += o
            buckets[(d.year, d.month)][1] += t
        keys, y, m = [], first.year, first.month
        while (y, m) <= (last.year, last.month):
            keys.append((y, m))
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        single_year = first.year == last.year
        return {
            "unit": "month",
            "labels": [BULAN[m - 1] if single_year else f"{BULAN[m - 1]} {str(y)[2:]}" for y, m in keys],
            "dates": [datetime.date(y, m, 1).isoformat() for y, m in keys],
            "omzet": [buckets[k][0] for k in keys],
            "transaksi": [buckets[k][1] for k in keys],
            "moving_avg": [],
        }

    days = [first + timedelta(days=i) for i in range((last - first).days + 1)]
    short = len(days) <= 14
    omzet = [per_day[d][0] if d in per_day else 0.0 for d in days]
    moving = []
    if len(days) >= MOVING_AVG_WINDOW + 3:
        for i in range(len(days)):
            window = omzet[max(0, i - MOVING_AVG_WINDOW + 1): i + 1]
            moving.append(round(sum(window) / len(window)))
    return {
        "unit": "day",
        "labels": [f"{HARI[d.weekday()]} {d.day}" if short else f"{d.day} {BULAN[d.month - 1]}" for d in days],
        "dates": [d.isoformat() for d in days],
        "omzet": omzet,
        "transaksi": [per_day[d][1] if d in per_day else 0 for d in days],
        "moving_avg": moving,
    }


# ─────────────────────────────────────────────
# Laporan utama
# ─────────────────────────────────────────────

def full_report(params, now=None):
    from menu.models import Menu

    start, end = resolve_period(params, now)
    qs = qualifying_orders(start, end)
    order_ids = qs.values("id")

    cur = _totals(qs)
    menu_aktif = Menu.objects.filter(is_active=True).count()

    # ── Pembanding ────────────────────────────────────────────────────
    p_start, p_end, p_label = _previous_period(params, start, end)
    previous, delta = None, None
    if p_start:
        prev = _totals(qualifying_orders(p_start, p_end))
        previous = {**prev, "label": p_label, "start": p_start.isoformat(), "end": p_end.isoformat()}
        delta = {k: _pct_change(cur[k], prev[k]) for k in ("omzet", "transaksi", "rata_rata", "porsi")}

    per_day = _daily_map(qs)
    trend = _trend(per_day, start, end)

    # ── Ringkasan tambahan ────────────────────────────────────────────
    day_rows = [(d.isoformat(), o, t) for d, (o, t) in per_day.items() if t]
    best = max(day_rows, key=lambda r: r[1], default=None)
    active_days = len(day_rows)
    discount = float(qs.aggregate(x=Sum("discount_amount"))["x"] or 0)

    highlights = {
        "active_days": active_days,
        "avg_omzet_per_active_day": round(cur["omzet"] / active_days) if active_days else 0,
        "avg_trx_per_active_day": round(cur["transaksi"] / active_days, 1) if active_days else 0,
        "best_day": (
            {
                "date": best[0],
                "label": (lambda d: f"{HARI_PENUH[d.weekday()]}, {d.day} {BULAN[d.month - 1]}")(
                    datetime.date.fromisoformat(best[0])
                ),
                "omzet": best[1],
                "transaksi": best[2],
            }
            if best else None
        ),
        "discount_total": discount,
        "discount_share": _share(discount, cur["omzet"] + discount),
    }

    # ── Menu ──────────────────────────────────────────────────────────
    items = OrderItem.objects.filter(order_id__in=order_ids, menu__isnull=False)
    by_menu = list(items.values("menu__name").annotate(qty=Sum("quantity"), omzet=Sum(LINE_TOTAL)))
    total_item_rev = sum(float(r["omzet"] or 0) for r in by_menu)

    def _menu_row(r):
        omzet = float(r["omzet"] or 0)
        return {"name": r["menu__name"], "qty": int(r["qty"] or 0), "omzet": omzet,
                "share": _share(omzet, total_item_rev)}

    top_menu = [_menu_row(r) for r in sorted(by_menu, key=lambda r: (-(r["qty"] or 0), r["menu__name"]))[:TOP_LIMIT]]
    top_omzet = [_menu_row(r) for r in sorted(by_menu, key=lambda r: (-float(r["omzet"] or 0), r["menu__name"]))[:TOP_LIMIT]]

    sold_names = {r["menu__name"] for r in by_menu}
    menu_tidak_laku = list(
        Menu.objects.filter(is_active=True)
        .annotate(transaksi=Count("orderitem", filter=Q(orderitem__order_id__in=order_ids)))
        .order_by("transaksi", "name")
        .values("name", "transaksi")[:TOP_LIMIT]
    )
    menu_tidak_terjual = Menu.objects.filter(is_active=True).exclude(name__in=sold_names).count()

    # ── Kategori ──────────────────────────────────────────────────────
    cat_rows = list(
        items.values("menu__category__name").annotate(qty=Sum("quantity"), omzet=Sum(LINE_TOTAL)).order_by("-omzet")
    )
    kategori = [
        {
            "name": r["menu__category__name"] or "Tanpa kategori",
            "qty": int(r["qty"] or 0),
            "omzet": float(r["omzet"] or 0),
            "share": _share(float(r["omzet"] or 0), total_item_rev),
        }
        for r in cat_rows
    ]

    # ── Pembayaran, layanan, channel ──────────────────────────────────
    method_labels = dict(PAYMENT_METHOD_CHOICES)
    omzet_div = cur["omzet"] or 1
    metode_pembayaran = [
        {
            "method": r["payment_method"],
            "label": method_labels.get(r["payment_method"], r["payment_method"] or "Lainnya"),
            "count": r["count"],
            "total": float(r["total"] or 0),
            "percent": round(float(r["total"] or 0) / omzet_div * 100, 1),
        }
        for r in qs.values("payment_method").annotate(count=Count("id"), total=Sum("total_price")).order_by("-total")
    ]

    layanan = [
        {
            "service": r["service_type"],
            "label": SERVICE_LABELS.get(r["service_type"], r["service_type"]),
            "count": r["count"],
            "total": float(r["total"] or 0),
            "percent": _share(r["count"], cur["transaksi"]),
        }
        for r in qs.values("service_type").annotate(count=Count("id"), total=Sum("total_price")).order_by("-count")
    ]

    # ── Waktu: jam penuh + hari dalam seminggu ────────────────────────
    hour_counts = {
        r["hour"]: r["count"]
        for r in qs.annotate(hour=ExtractHour("created_at", tzinfo=WIB_DB_TZ)).values("hour").annotate(count=Count("id"))
    }
    jam_distribusi = []
    if hour_counts:
        lo, hi = min(hour_counts), max(hour_counts)
        jam_distribusi = [
            {"hour": h, "label": f"{h:02d}.00", "range": f"{h:02d}.00 - {(h + 1) % 24:02d}.00",
             "count": hour_counts.get(h, 0)}
            for h in range(lo, hi + 1)
        ]
    top5 = sorted(jam_distribusi, key=lambda x: -x["count"])[:5]
    jam_teramai = [
        {"hour": j["hour"], "label": j["range"], "count": j["count"]}
        for j in sorted(top5, key=lambda x: x["hour"]) if j["count"]
    ]

    weekday = defaultdict(lambda: [0, 0.0, set()])
    for created, total in qs.values_list("created_at", "total_price"):
        d = to_wib(created).date()
        weekday[d.weekday()][0] += 1
        weekday[d.weekday()][1] += float(total or 0)
        weekday[d.weekday()][2].add(d)
    per_hari = [
        {
            "day": i,
            "name": HARI_PENUH[i],
            "short": HARI[i],
            "count": weekday[i][0] if i in weekday else 0,
            "omzet": weekday[i][1] if i in weekday else 0.0,
            "active_days": len(weekday[i][2]) if i in weekday else 0,
            "avg_omzet": round(weekday[i][1] / len(weekday[i][2])) if i in weekday and weekday[i][2] else 0,
        }
        for i in range(7)
    ]

    # ── Pelanggan ─────────────────────────────────────────────────────
    paid_all = Order.objects.filter(payment_status="paid").exclude(status="cancelled")
    first_order = {
        r["customer_phone"]: to_wib(r["first"]).date()
        for r in paid_all.exclude(customer_phone="").order_by().values("customer_phone").annotate(first=Min("created_at"))
    }
    # order_by() wajib: ordering bawaan Order (-created_at) ikut masuk DISTINCT dan menggandakan nomor yang sama.
    phones = list(qs.exclude(customer_phone="").order_by().values_list("customer_phone", flat=True).distinct())
    baru = lama = 0
    for phone in phones:
        first_date = first_order.get(phone)
        if not first_date:
            continue
        if start and first_date < start:
            lama += 1
        else:
            baru += 1
    member_loyal = CustomerLoyalty.objects.filter(phone__in=phones, points__gt=0).count()
    tanpa_nomor = qs.filter(customer_phone="").count()
    known = baru + lama

    return {
        "period": {
            "mode": params.get("period", "lifetime"),
            "start": start.isoformat() if start else None,
            "end": end.isoformat() if end else None,
        },
        "stats": {
            "total_omzet": cur["omzet"],
            "total_transaksi": cur["transaksi"],
            "rata_rata_transaksi": cur["rata_rata"],
            "porsi_terjual": cur["porsi"],
            "menu_aktif": menu_aktif,
        },
        "previous": previous,
        "delta": delta,
        "highlights": highlights,
        "trend": trend,
        "top_menu": top_menu,
        "menu_paling_menghasilkan": top_omzet,
        "menu_tidak_laku": menu_tidak_laku,
        "menu_tidak_terjual": menu_tidak_terjual,
        "kategori": kategori,
        "metode_pembayaran": metode_pembayaran,
        "layanan": layanan,
        "pelanggan": {
            "baru": baru,
            "lama": lama,
            "loyal_member": member_loyal,
            "unik": known,
            "repeat_rate": _share(lama, known),
            "tanpa_nomor": tanpa_nomor,
        },
        "jam_teramai": jam_teramai,
        "jam_distribusi": jam_distribusi,
        "per_hari": per_hari,
    }