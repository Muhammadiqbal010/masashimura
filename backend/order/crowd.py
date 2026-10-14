"""
Keramaian toko: Peta Jam Sibuk (admin) dan indikator keramaian (pelanggan).

Semua perhitungan dilakukan saat dibaca, tanpa cron dan tanpa state di memori,
jadi aman untuk backend serverless.

Definisi "pesanan" di sini = permintaan nyata dari pelanggan: semua order yang
TIDAK dibatalkan dan TIDAK void. Sengaja berbeda dari definisi omzet (yang hanya
menghitung order lunas), karena pelanggan POS yang makan dulu baru bayar tetap
ikut membuat toko ramai.

"Hari" dan "jam" selalu WIB (lihat order.models.WIB), tidak bergantung setting
TIME_ZONE server.
"""
import math
from collections import Counter
from datetime import datetime, timedelta

from django.utils import timezone

from .models import Order, WIB

LEVELS = ("santai", "sedang", "ramai")
LEVEL_LABELS = {"santai": "Santai", "sedang": "Sedang", "ramai": "Ramai"}

DAY_NAMES = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]  # 0=Senin

HISTORY_WEEKS = 8                       # jendela riwayat default
MIN_WEEKS, MAX_WEEKS = 2, 26
LIVE_WINDOW = timedelta(minutes=60)     # "sekarang" = pesanan 60 menit terakhir
MIN_HISTORY_ORDERS = 30                 # di bawah ini data dianggap belum cukup
FALLBACK_THRESHOLDS = (2, 5)            # (batas Santai, batas Sedang) bila data kurang
PCT_LOW, PCT_HIGH = 40, 80              # persentil sebaran pesanan per jam

MANUAL_MIN_MINUTES, MANUAL_MAX_MINUTES = 5, 12 * 60


# ─────────────────────────────────────────────
# HELPER WAKTU & JADWAL
# ─────────────────────────────────────────────

def to_wib(dt):
    """Datetime apa pun -> aware di WIB (naive dianggap sudah WIB)."""
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, WIB)
    return dt.astimezone(WIB)


def _hhmm_to_minutes(value):
    try:
        h, m = str(value).split(":")[:2]
        h, m = int(h), int(m)
    except (TypeError, ValueError):
        return None
    if not (0 <= h <= 24 and 0 <= m < 60):
        return None
    return h * 60 + m


def schedule_for(store, weekday):
    """
    (buka, tutup) dalam menit untuk hari ini (0=Senin), atau None kalau libur.
    Jadwal belum diisi sama sekali -> semua hari dianggap buka, dikembalikan
    sebagai (0, 1440) supaya perhitungan lain tetap jalan.
    """
    hours = store.operating_hours or {}
    if not hours:
        return (0, 24 * 60)
    entry = hours.get(str(weekday))
    if not entry:
        return None
    open_m = _hhmm_to_minutes(entry.get("open"))
    close_m = _hhmm_to_minutes(entry.get("close"))
    if open_m is None or close_m is None or close_m <= open_m:
        return None
    return (open_m, close_m)


def is_store_open(store, now=None):
    """Sama persis dengan isStoreOpen di useStoreSettings.js (override lalu jadwal)."""
    if store.is_open_override is True:
        return True
    if store.is_open_override is False:
        return False
    if not (store.operating_hours or {}):
        return True
    now = to_wib(now or timezone.now())
    sched = schedule_for(store, now.weekday())
    if not sched:
        return False
    minutes = now.hour * 60 + now.minute
    return sched[0] <= minutes < sched[1]


def _demand_orders():
    return Order.objects.exclude(status="cancelled").exclude(payment_status="void")


def _percentile(sorted_values, pct):
    """Nearest-rank pada list yang sudah terurut; list kosong -> 0."""
    if not sorted_values:
        return 0
    k = max(0, math.ceil(pct / 100 * len(sorted_values)) - 1)
    return sorted_values[min(k, len(sorted_values) - 1)]


# ─────────────────────────────────────────────
# RIWAYAT PER JAM
# ─────────────────────────────────────────────

def _history(store, now, weeks):
    """
    Hitung pesanan per (tanggal, jam) selama `weeks` minggu sampai KEMARIN
    (hari ini dibuang karena belum tuntas, sama seperti data prediksi omzet).

    Return (counter, dates, total) dengan:
      counter = {(date, hour): jumlah}
      dates   = daftar tanggal efektif (mulai dari order pertama di jendela itu,
                supaya toko yang baru berjalan tidak dianggap sepi di hari sebelum buka)
      total   = jumlah pesanan di jendela
    """
    now = to_wib(now)
    end_date = now.date() - timedelta(days=1)
    start_date = end_date - timedelta(days=weeks * 7 - 1)

    start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=WIB)
    end_dt = datetime.combine(now.date(), datetime.min.time(), tzinfo=WIB)

    counter = Counter()
    first_date = None
    total = 0
    rows = (
        _demand_orders()
        .filter(created_at__gte=start_dt, created_at__lt=end_dt)
        .values_list("created_at", flat=True)
    )
    for created in rows:
        local = to_wib(created)
        counter[(local.date(), local.hour)] += 1
        total += 1
        if first_date is None or local.date() < first_date:
            first_date = local.date()

    if first_date is None:
        return counter, [], 0

    eff_start = max(start_date, first_date)
    dates = [eff_start + timedelta(days=i) for i in range((end_date - eff_start).days + 1)]
    return counter, dates, total


def _slot_in_hours(sched, hour, fully=False):
    """Apakah jam `hour` (hour:00 sampai hour+1:00) berada di jam operasional."""
    if not sched:
        return False
    start, end = hour * 60, (hour + 1) * 60
    if fully:
        return start >= sched[0] and end <= sched[1]
    return start < sched[1] and end > sched[0]


# ─────────────────────────────────────────────
# AMBANG BATAS & LEVEL OTOMATIS
# ─────────────────────────────────────────────

def thresholds(store, now=None, weeks=HISTORY_WEEKS, history=None):
    """
    (batas_santai, batas_sedang, sumber).
    live <= batas_santai -> Santai; <= batas_sedang -> Sedang; selebihnya Ramai.
    Diambil dari sebaran jumlah pesanan per jam di jam buka (termasuk jam tanpa pesanan)
    selama riwayat. Data terlalu sedikit -> ambang tetap.
    """
    now = to_wib(now or timezone.now())
    counter, dates, total = history or _history(store, now, weeks)
    if total < MIN_HISTORY_ORDERS:
        return FALLBACK_THRESHOLDS[0], FALLBACK_THRESHOLDS[1], "fallback"

    slots = []
    for d in dates:
        sched = schedule_for(store, d.weekday())
        if not sched:
            continue
        for h in range(24):
            if _slot_in_hours(sched, h):
                slots.append(counter.get((d, h), 0))
    if not slots:
        return FALLBACK_THRESHOLDS[0], FALLBACK_THRESHOLDS[1], "fallback"

    slots.sort()
    low = _percentile(slots, PCT_LOW)
    high = max(_percentile(slots, PCT_HIGH), low + 1)
    return low, high, "history"


def live_orders(now=None):
    """Jumlah pesanan dalam 60 menit terakhir."""
    now = now or timezone.now()
    return _demand_orders().filter(created_at__gt=now - LIVE_WINDOW, created_at__lte=now).count()


def auto_level(store, now=None):
    now = now or timezone.now()
    low, high, source = thresholds(store, now)
    live = live_orders(now)
    if live <= low:
        level = "santai"
    elif live <= high:
        level = "sedang"
    else:
        level = "ramai"
    return {"level": level, "live_orders": live, "low": low, "high": high, "source": source}


# ─────────────────────────────────────────────
# STATUS (dibaca pelanggan & kasir)
# ─────────────────────────────────────────────

def manual_active(store, now=None):
    now = now or timezone.now()
    return bool(
        store.crowd_manual_level in LEVELS
        and store.crowd_manual_until
        and now < store.crowd_manual_until
    )


def crowd_status(store, now=None, detail=False):
    """
    Status untuk pelanggan (detail=False) atau kasir/admin (detail=True).

    Pelanggan: badge hanya terlihat kalau saklar menyala DAN toko buka.
    Kasir: selalu dapat level + mode + level otomatis, supaya kontrol cepat
    tetap bisa dipakai walau badge sedang disembunyikan.
    """
    now = now or timezone.now()
    enabled = bool(store.crowd_indicator_enabled)
    store_open = is_store_open(store, now)
    manual = manual_active(store, now)

    payload = {
        "enabled": enabled,
        "store_open": store_open,
        "visible": enabled and store_open,
        "level": None,
        "label": None,
        "mode": "manual" if manual else "auto",
        "until": store.crowd_manual_until.isoformat() if manual else None,
    }

    need_level = payload["visible"] or detail
    if need_level:
        if manual:
            payload["level"] = store.crowd_manual_level
            if detail:
                payload["auto"] = auto_level(store, now)
        else:
            auto = auto_level(store, now)
            payload["level"] = auto["level"]
            if detail:
                payload["auto"] = auto
        payload["label"] = LEVEL_LABELS[payload["level"]]
    return payload


def set_manual(store, level, minutes=None, until=None, now=None):
    """
    Atur mode manual. level 'auto' = kembali otomatis.
    Durasi lewat `minutes` (5 sampai 720) atau `until` ("HH:MM" WIB hari ini).
    Return None kalau sukses, atau pesan error.
    """
    now = now or timezone.now()

    if level == "auto":
        store.crowd_manual_level = ""
        store.crowd_manual_until = None
        store.save(update_fields=["crowd_manual_level", "crowd_manual_until", "updated_at"])
        return None

    if level not in LEVELS:
        return "Level harus santai, sedang, ramai, atau auto."

    if until not in (None, ""):
        minutes_of_day = _hhmm_to_minutes(until)
        if minutes_of_day is None or minutes_of_day >= 24 * 60:
            return "Format jam harus HH:MM, contoh 20:00."
        now_wib = to_wib(now)
        target = datetime.combine(now_wib.date(), datetime.min.time(), tzinfo=WIB) + timedelta(minutes=minutes_of_day)
        if target <= now_wib:
            return "Jam berakhir sudah lewat. Pilih jam setelah sekarang."
        if target - now_wib > timedelta(minutes=MANUAL_MAX_MINUTES):
            return "Maksimal 12 jam dari sekarang."
        expires = target
    else:
        try:
            minutes = int(minutes)
        except (TypeError, ValueError):
            return "Durasi (menit) wajib diisi."
        if not (MANUAL_MIN_MINUTES <= minutes <= MANUAL_MAX_MINUTES):
            return f"Durasi harus {MANUAL_MIN_MINUTES} sampai {MANUAL_MAX_MINUTES} menit."
        expires = now + timedelta(minutes=minutes)

    store.crowd_manual_level = level
    store.crowd_manual_until = expires
    store.save(update_fields=["crowd_manual_level", "crowd_manual_until", "updated_at"])
    return None


# ─────────────────────────────────────────────
# PETA JAM SIBUK (admin)
# ─────────────────────────────────────────────

def _slot_label(weekday, hour):
    return f"{DAY_NAMES[weekday]} {hour:02d}.00–{(hour + 1) % 24:02d}.00"


def busy_hours(store, now=None, weeks=HISTORY_WEEKS):
    """
    Rata-rata jumlah pesanan per jam untuk tiap hari dalam seminggu.
    grid[hari][jam] = pesanan / berapa kali hari itu terjadi di jendela riwayat.
    """
    now = to_wib(now or timezone.now())
    weeks = max(MIN_WEEKS, min(MAX_WEEKS, int(weeks)))
    counter, dates, total = _history(store, now, weeks)

    occurrences = [0] * 7
    for d in dates:
        occurrences[d.weekday()] += 1

    sums = [[0] * 24 for _ in range(7)]
    for (d, h), n in counter.items():
        sums[d.weekday()][h] += n

    grid = [
        [round(sums[w][h] / occurrences[w], 2) if occurrences[w] else 0 for h in range(24)]
        for w in range(7)
    ]

    scheds = [schedule_for(store, w) for w in range(7)]
    has_schedule = bool(store.operating_hours)

    open_hours = [
        [sched[0] // 60, math.ceil(sched[1] / 60)] if sched else None
        for sched in scheds
    ]

    # Rentang jam yang ditampilkan: gabungan jam buka. Tanpa jadwal -> jam yang ada pesanannya.
    if has_schedule and any(open_hours):
        hour_min = min(o[0] for o in open_hours if o)
        hour_max = max(o[1] for o in open_hours if o)
    else:
        hours_with_orders = [h for w in range(7) for h in range(24) if sums[w][h]]
        hour_min = min(hours_with_orders) if hours_with_orders else 8
        hour_max = (max(hours_with_orders) + 1) if hours_with_orders else 22

    by_weekday = [
        round(sum(sums[w]) / occurrences[w], 1) if occurrences[w] else 0
        for w in range(7)
    ]

    busiest = sorted(
        (
            (grid[w][h], w, h)
            for w in range(7) for h in range(24)
            if scheds[w] and _slot_in_hours(scheds[w], h) and grid[w][h] > 0
        ),
        key=lambda t: (-t[0], t[1], t[2]),
    )[:3]

    # "Paling sepi": hanya jam yang sepenuhnya di jam buka (jam setengah buka bias rendah),
    # dan hanya hari yang punya data pembanding.
    quietest = sorted(
        (
            (grid[w][h], w, h)
            for w in range(7) for h in range(24)
            if occurrences[w] and scheds[w] and _slot_in_hours(scheds[w], h, fully=True)
        ),
        key=lambda t: (t[0], t[1], t[2]),
    )[:3]

    low, high, source = thresholds(store, now, weeks, history=(counter, dates, total))
    pack = lambda rows: [
        {"day": w, "hour": h, "label": _slot_label(w, h), "avg": avg} for avg, w, h in rows
    ]

    return {
        "weeks": weeks,
        "range": {
            "start": dates[0].isoformat() if dates else None,
            "end": dates[-1].isoformat() if dates else None,
        },
        "total_orders": total,
        "enough_data": total >= MIN_HISTORY_ORDERS,
        "min_orders_required": MIN_HISTORY_ORDERS,
        "day_names": DAY_NAMES,
        "grid": grid,
        "occurrences": occurrences,
        "open_hours": open_hours,
        "hour_range": [hour_min, hour_max],
        "by_weekday": by_weekday,
        "busiest": pack(busiest),
        "quietest": pack(quietest),
        "thresholds": {"santai_max": low, "sedang_max": high, "source": source},
    }
