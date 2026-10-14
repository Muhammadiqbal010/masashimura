"""
Strip Briefing di atas Dashboard: prediksi hari ini, keramaian, target bulan ini
beserta proyeksinya, tagihan belum lunas, dan 2 sampai 3 saran.

Selalu "hari ini" (WIB), tidak ikut filter tanggal dashboard. Tiap bagian dihitung
terpisah dan dibungkus try/except, jadi satu bagian yang error tidak mematikan
bagian lain; yang gagal tercatat di `errors` dan nilainya None.

Saran dibuat rule-based ("jika X maka sarankan Y"), tanpa model bahasa: gratis,
cepat, dan tiap saran menyebut dasar hitungannya (`reason`).

Proyeksi bulan ini = omzet kemarin ke belakang (bulan berjalan)
                   + kontribusi hari ini
                   + prediksi omzet hari-hari tersisa sampai akhir bulan.
Kontribusi hari ini = yang lebih besar antara omzet sejauh ini dan prediksi hari ini,
kecuali toko sudah lewat jam tutup atau hari ini libur rutin (pakai omzet aktual saja).
"""
import calendar
import logging
from datetime import datetime, time, timedelta

from django.db.models import Count, Sum
from django.utils import timezone

from . import crowd
from .analytics import menu_performance, qualifying_orders
from .crowd import schedule_for, to_wib
from .segmentation import AT_RISK_DAYS, AT_RISK_MIN_ORDERS, ACTIVE_DAYS, at_risk_count
from .models import Order, WIB

logger = logging.getLogger(__name__)

BULAN_PANJANG = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]
MAX_RECOMMENDATIONS = 3
PROMO_MIN_AGE_DAYS = 14        # promo baru berjalan kurang dari ini belum dinilai
PROMO_LOW_USE = 2              # dipakai <= ini kali selama berjalan = hampir tidak dipakai
POTENSIAL_WINDOW_DAYS = 28     # jendela penentuan menu Potensial untuk saran
MAX_POTENSIAL_SHOWN = 2

CONFIDENCE_NOTES = {
    "rendah": "Data historis masih sedikit, jadi prediksi dan proyeksi ini masih kasar.",
    "sedang": "Data historis mulai cukup tetapi masih terbatas. Pakai sebagai acuan.",
    "tinggi": None,
}


def rp(value):
    return "Rp" + f"{int(round(value or 0)):,}".replace(",", ".")


def _revenue(start, end):
    """Omzet (lunas, tidak dibatalkan) tanggal start..end WIB, sama dengan kartu Total Revenue."""
    total = qualifying_orders(start, end).aggregate(t=Sum("total_price"))["t"]
    return float(total or 0)


# ─────────────────────────────────────────────
# BAGIAN-BAGIAN
# ─────────────────────────────────────────────

def _predict_pack(dates, today):
    """Prediksi untuk `dates` (mulai hari ini) + simpan sebagai snapshot. None bila belum ada data."""
    from prediction import snapshots
    from prediction.ml.predict import ModelNotTrainedError, predict_dates

    try:
        pack = predict_dates(dates)
    except ModelNotTrainedError:
        return None
    snapshots.save_forecast(pack["days"], method=pack["method"], made_on=today)
    return pack


def _today_section(pack, today_actual):
    section = {
        "actual_so_far": today_actual,
        "predicted": None, "lower": None, "upper": None,
        "confidence": None, "is_closed_day": False, "method": None,
    }
    if pack and pack["days"]:
        d = pack["days"][0]
        section.update(
            predicted=d["predicted_revenue"], lower=d["lower_bound"], upper=d["upper_bound"],
            confidence=d["confidence"], is_closed_day=d["is_regular_closed_day"], method=pack["method"],
        )
    return section


def _crowd_section(store, now):
    st = crowd.crowd_status(store, now, detail=True)
    return {
        "enabled": st["enabled"],
        "store_open": st["store_open"],
        "level": st["level"],
        "label": st["label"],
        "mode": st["mode"],
        "until": st["until"],
        "live_orders": (st.get("auto") or {}).get("live_orders"),
    }


def _target_section(store, pack, today, local, month_start, month_end):
    target = int(store.monthly_revenue_target or 0)
    realized_before = _revenue(month_start, today - timedelta(days=1)) if today > month_start else 0.0
    today_actual = _revenue(today, today)
    realized = realized_before + today_actual
    days_left = (month_end - today).days

    projected = None
    if pack and pack["days"]:
        today_pred = pack["days"][0]
        sched = schedule_for(store, today.weekday())
        minutes_now = local.hour * 60 + local.minute
        finished = (sched is None) or minutes_now >= sched[1]
        if today_pred["is_regular_closed_day"] or finished:
            today_part = today_actual
        else:
            today_part = max(today_actual, today_pred["predicted_revenue"])
        remaining = sum(d["predicted_revenue"] for d in pack["days"][1:])
        projected = realized_before + today_part + remaining

    if not target:
        status = "belum_ada_target"
    elif realized >= target:
        status = "tercapai"
    elif projected is None:
        status = "proyeksi_tidak_tersedia"
    elif projected >= target:
        status = "di_jalur"
    else:
        status = "di_bawah"

    return {
        "month_label": f"{BULAN_PANJANG[today.month - 1]} {today.year}",
        "target": target or None,
        "realized": realized,
        "realized_pct": round(realized / target * 100, 1) if target else None,
        "projected": round(projected) if projected is not None else None,
        "projected_pct": round(projected / target * 100, 1) if target and projected is not None else None,
        "gap": round(max(0, target - projected)) if target and projected is not None else None,
        "days_left": days_left,
        "confidence": pack["confidence"] if pack else None,
        "status": status,
    }


def _unpaid_section(today):
    from .views import GATEWAY_NOT_PAID_Q   # satu sumber definisi "tagihan" dengan halaman Tagihan

    qs = (
        Order.objects.filter(payment_status__in=["unpaid", "pending"])
        .exclude(status="cancelled")
        .exclude(GATEWAY_NOT_PAID_Q)
    )
    start_today = datetime.combine(today, time.min, tzinfo=WIB)
    all_ = qs.aggregate(n=Count("id"), t=Sum("total_price"))
    old = qs.filter(created_at__lt=start_today).aggregate(n=Count("id"), t=Sum("total_price"))
    return {
        "count": all_["n"] or 0,
        "total": float(all_["t"] or 0),
        "older_count": old["n"] or 0,
        "older_total": float(old["t"] or 0),
    }


# ─────────────────────────────────────────────
# SARAN (rule-based)
# ─────────────────────────────────────────────

def _short_advice(store, now):
    """Potongan saran untuk proyeksi di bawah target: jam paling sepi dan menu Potensial."""
    parts = []
    try:
        busy = crowd.busy_hours(store, now)
        if busy["enough_data"] and busy["quietest"]:
            parts.append(f"Coba promo di {busy['quietest'][0]['label']} (jam paling sepi)")
    except Exception:
        logger.exception("Briefing: jam sepi gagal dihitung")
    try:
        perf = menu_performance({"period": "week", "days": POTENSIAL_WINDOW_DAYS, "offset": 0}, now)
        if perf["enough_data"]:
            names = [m["name"] for m in perf["menus"] if m["class"] == "potensial"][:MAX_POTENSIAL_SHOWN]
            if names:
                parts.append("dorong menu Potensial " + " dan ".join(names))
    except Exception:
        logger.exception("Briefing: menu Potensial gagal dihitung")
    try:
        at_risk = at_risk_count(now)
        if at_risk:
            parts.append(f"hubungi {at_risk} pelanggan Berisiko")
    except Exception:
        logger.exception("Briefing: segmen Berisiko gagal dihitung")
    return parts


def _promo_unused(now):
    from promotions.models import Promo

    cutoff = now - timedelta(days=PROMO_MIN_AGE_DAYS)
    qs = Promo.objects.filter(
        is_active=True, valid_from__lte=cutoff, valid_until__gte=now, used_count__lte=PROMO_LOW_USE,
    ).order_by("valid_from")
    return [(p.code, p.used_count, max(1, (now - p.valid_from).days)) for p in qs[:1]]


def _recommendations(store, now, target, unpaid):
    recs = []   # (prioritas, dict); prioritas kecil tampil dulu

    if target:
        status = target["status"]
        basis = (
            f"Proyeksi = omzet sejauh ini + prediksi {target['days_left']} hari tersisa."
            if target["days_left"] else "Proyeksi = omzet bulan ini sampai hari ini."
        )
        if status == "di_bawah":
            parts = _short_advice(store, now)
            text = f"Proyeksi bulan ini kurang sekitar {rp(target['gap'])} dari target."
            if parts:
                text += " " + ", ".join(parts) + "."
            recs.append((1, {"id": "target_short", "tone": "warn", "text": text, "reason": basis}))
        elif status == "di_jalur":
            recs.append((6, {
                "id": "target_on_track", "tone": "good",
                "text": f"Proyeksi bulan ini sekitar {rp(target['projected'])} ({target['projected_pct']:.0f}% dari target). Masih di jalur.",
                "reason": basis,
            }))
        elif status == "tercapai":
            recs.append((6, {
                "id": "target_done", "tone": "good",
                "text": "Target omzet bulan ini sudah tercapai.",
                "reason": f"Omzet sejauh ini {rp(target['realized'])}.",
            }))
        elif status == "belum_ada_target":
            recs.append((5, {
                "id": "target_missing", "tone": "info",
                "text": "Target bulanan belum diatur. Isi di Pengaturan agar proyeksi bisa dibandingkan.",
                "reason": "Target dipakai untuk membandingkan proyeksi omzet bulan ini.",
            }))

    if unpaid and unpaid["older_count"] > 0:
        recs.append((2, {
            "id": "unpaid_old", "tone": "warn",
            "text": f"{unpaid['older_count']} tagihan dari hari sebelumnya belum lunas ({rp(unpaid['older_total'])}). Tagih atau batalkan agar omzet tercatat benar.",
            "reason": "Tagihan belum lunas tidak dihitung sebagai omzet.",
        }))

    try:
        for code, used, age in _promo_unused(now):
            recs.append((4, {
                "id": "promo_unused", "tone": "info",
                "text": f"Promo {code} hampir tidak dipakai ({used}x dalam {age} hari). Pertimbangkan mengubah atau menonaktifkan.",
                "reason": f"Promo aktif lebih dari {PROMO_MIN_AGE_DAYS} hari dan dipakai paling banyak {PROMO_LOW_USE} kali.",
            }))
    except Exception:
        logger.exception("Briefing: cek promo gagal")

    # Saran pelanggan Berisiko berdiri sendiri hanya bila belum ikut disebut di saran target.
    if not (target and target["status"] == "di_bawah"):
        try:
            at_risk = at_risk_count(now)
            if at_risk:
                recs.append((3, {
                    "id": "customers_at_risk", "tone": "info",
                    "text": f"{at_risk} pelanggan Berisiko belum order lagi. Hubungi mereka lewat WhatsApp sebelum benar-benar hilang.",
                    "reason": (
                        f"Berisiko = pernah order {AT_RISK_MIN_ORDERS} kali atau lebih, tetapi terakhir order "
                        f"{ACTIVE_DAYS + 1} sampai {AT_RISK_DAYS} hari lalu. Daftarnya ada di Pelanggan Setia."
                    ),
                }))
        except Exception:
            logger.exception("Briefing: cek pelanggan Berisiko gagal")

    recs.sort(key=lambda r: r[0])
    return [r for _, r in recs[:MAX_RECOMMENDATIONS]]


# ─────────────────────────────────────────────
# PINTU MASUK
# ─────────────────────────────────────────────

def briefing(store, now=None):
    now = now or timezone.now()
    local = to_wib(now)
    today = local.date()
    month_start = today.replace(day=1)
    month_end = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    dates = [today + timedelta(days=i) for i in range((month_end - today).days + 1)]
    errors = []

    def safe(name, fn):
        try:
            return fn()
        except Exception:
            logger.exception("Briefing: bagian %s gagal", name)
            errors.append(name)
            return None

    pack = safe("prediction", lambda: _predict_pack(dates, today))
    today_actual = safe("actual_today", lambda: _revenue(today, today))
    prediction_today = _today_section(pack, today_actual or 0.0) if today_actual is not None else None
    crowd_section = safe("crowd", lambda: _crowd_section(store, now))
    target = safe("target", lambda: _target_section(store, pack, today, local, month_start, month_end))
    unpaid = safe("unpaid", lambda: _unpaid_section(today))
    recs = safe("recommendations", lambda: _recommendations(store, now, target, unpaid)) or []

    return {
        "generated_at": now.isoformat(),
        "date": today.isoformat(),
        "day_name": crowd.DAY_NAMES[today.weekday()],
        "prediction_today": prediction_today,
        "crowd": crowd_section,
        "target": target,
        "unpaid": unpaid,
        "recommendations": recs,
        "data_note": CONFIDENCE_NOTES.get(pack["confidence"]) if pack else None,
        "errors": errors,
    }
