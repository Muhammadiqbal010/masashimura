"""
Simulasi (#19), hanya skenario yang punya dasar data historis.

1. Simulasi target (aritmatika): "kalau rata-rata harian naik X%, bulan ini mencapai Rp Y".
   Dasarnya omzet berjalan bulan ini, rata-rata omzet per HARI BUKA (hari yang sudah lewat),
   dan sisa hari buka. Persentase X dihitung di frontend (slider) dari angka dasar ini.
   Ini hitungan sederhana, BUKAN keluaran model prediksi.

2. Simulasi promo (estimasi kasar): selisih rata-rata omzet hari ber-promo dibanding hari tanpa
   promo selama beberapa bulan terakhir. Itu korelasi, bukan bukti promo penyebabnya (hari ber-promo
   bisa kebetulan hari ramai), jadi di layar wajib berlabel "estimasi".

Skenario tanpa data (mis. "buka sampai jam 23.00") sengaja tidak dibuat.
"""
import calendar
from collections import defaultdict
from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from .analytics import qualifying_orders
from .briefing import BULAN_PANJANG
from .crowd import schedule_for, to_wib
from .models import StoreSettings

MIN_OPEN_DAYS = 3             # di bawah ini rata-rata harian belum meyakinkan
PROMO_LOOKBACK_DAYS = 90
MIN_DAYS_PER_GROUP = 5        # hari ber-promo dan tanpa promo masing-masing minimal ini


def _revenue(start, end):
    total = qualifying_orders(start, end).aggregate(t=Sum("total_price"))["t"]
    return float(total or 0)


def _open_days(store, start, end):
    """Jumlah hari buka (menurut jadwal toko) pada rentang tanggal start..end, inklusif."""
    if end < start:
        return 0
    days, d = 0, start
    while d <= end:
        if schedule_for(store, d.weekday()) is not None:
            days += 1
        d += timedelta(days=1)
    return days


def target_base(store, today):
    month_start = today.replace(day=1)
    month_end = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    before = _revenue(month_start, today - timedelta(days=1)) if today > month_start else 0.0
    realized = before + _revenue(today, today)
    open_elapsed = _open_days(store, month_start, today - timedelta(days=1))
    remaining = _open_days(store, today + timedelta(days=1), month_end)

    enough = open_elapsed >= MIN_OPEN_DAYS
    avg = before / open_elapsed if open_elapsed else None
    target = int(store.monthly_revenue_target or 0)

    projected = realized + avg * remaining if (enough and avg is not None) else None
    needed = None
    if enough and target and avg and remaining > 0 and realized < target:
        needed = round(((target - realized) / (avg * remaining) - 1) * 100, 1)

    return {
        "month_label": f"{BULAN_PANJANG[today.month - 1]} {today.year}",
        "enough_data": enough,
        "min_open_days": MIN_OPEN_DAYS,
        "target": target or None,
        "realized": round(realized),
        "avg_open_day": round(avg) if avg is not None else None,
        "open_days_elapsed": open_elapsed,
        "remaining_open_days": remaining,
        "projected_base": round(projected) if projected is not None else None,
        "needed_growth_pct": needed,
        "target_reached": bool(target) and realized >= target,
    }


def promo_base(today):
    start = today - timedelta(days=PROMO_LOOKBACK_DAYS)
    end = today - timedelta(days=1)

    revenue = defaultdict(float)
    promo_days = set()
    rows = qualifying_orders(start, end).values_list("created_at", "total_price", "promo_id", "promo_discount_amount")
    for created, total, promo_id, discount in rows:
        d = to_wib(created).date()
        revenue[d] += float(total or 0)
        if promo_id or (discount or 0) > 0:
            promo_days.add(d)

    with_promo = [v for d, v in revenue.items() if d in promo_days and v > 0]
    without = [v for d, v in revenue.items() if d not in promo_days and v > 0]
    enough = len(with_promo) >= MIN_DAYS_PER_GROUP and len(without) >= MIN_DAYS_PER_GROUP

    avg_with = sum(with_promo) / len(with_promo) if with_promo else None
    avg_without = sum(without) / len(without) if without else None
    diff = diff_pct = None
    if enough and avg_without:
        diff = avg_with - avg_without
        diff_pct = round(diff / avg_without * 100, 1)

    return {
        "enough_data": enough,
        "lookback_days": PROMO_LOOKBACK_DAYS,
        "min_days_per_group": MIN_DAYS_PER_GROUP,
        "promo_days": len(with_promo),
        "non_promo_days": len(without),
        "avg_promo_day": round(avg_with) if avg_with is not None else None,
        "avg_non_promo_day": round(avg_without) if avg_without is not None else None,
        "diff": round(diff) if diff is not None else None,
        "diff_pct": diff_pct,
    }


def simulation(params=None, now=None):
    now = now or timezone.now()
    today = to_wib(now).date()
    store = StoreSettings.get()
    return {
        "target": target_base(store, today),
        "promo": promo_base(today),
        "notes": {
            "target": "Hitungan aritmatika dari rata-rata omzet per hari buka bulan ini, bukan keluaran model prediksi.",
            "promo": (
                "Estimasi kasar dari selisih rata-rata omzet hari ber-promo dan hari tanpa promo. "
                "Ini korelasi, bukan bukti promo menyebabkan kenaikan (hari ber-promo bisa kebetulan hari ramai)."
            ),
        },
    }
