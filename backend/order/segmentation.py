"""
Segmentasi Pelanggan Setia (#13), rule-based dan bisa dijelaskan.

Dasarnya hanya tiga angka yang sudah tersimpan di CustomerLoyalty:
  - recency   = hari sejak order terakhir (last_order_at, dihitung di WIB)
  - frekuensi = total_orders (lifetime)
Tidak ada model baru dan tidak ada state: segmen dihitung saat dibaca.

Urutan aturan (yang pertama cocok menang):
  Setia    : order >= 5 kali dan terakhir order <= 30 hari lalu
  Baru     : order <= 1 kali dan terakhir order <= 30 hari lalu
             (juga untuk member yang belum punya order selesai sama sekali)
  Aktif    : terakhir order <= 30 hari lalu (selain dua di atas)
  Berisiko : sudah order >= 2 kali, tetapi terakhir order 31 sampai 60 hari lalu
  Tidur    : sisanya (lebih dari 60 hari, atau baru sekali order lalu menghilang)

Berisiko sengaja hanya untuk pelanggan yang pernah kembali order: mereka yang paling
layak dihubungi sebelum benar-benar hilang. Batas hari ada di konstanta supaya mudah
disesuaikan dan disebut apa adanya di laporan.
"""
from django.utils import timezone

from .crowd import to_wib
from .models import CustomerLoyalty

ACTIVE_DAYS = 30            # order terakhir <= ini = masih aktif
AT_RISK_DAYS = 60           # 31..60 hari = berisiko (bila pernah kembali order)
LOYAL_MIN_ORDERS = 5
AT_RISK_MIN_ORDERS = 2

SEGMENT_ORDER = ["setia", "aktif", "baru", "berisiko", "tidur"]

SEGMENT_LABELS = {
    "setia":    "Setia",
    "aktif":    "Aktif",
    "baru":     "Baru",
    "berisiko": "Berisiko",
    "tidur":    "Tidur",
}

SEGMENT_HINTS = {
    "setia":    f"Order {LOYAL_MIN_ORDERS} kali atau lebih dan terakhir order dalam {ACTIVE_DAYS} hari.",
    "aktif":    f"Terakhir order dalam {ACTIVE_DAYS} hari.",
    "baru":     f"Baru order {AT_RISK_MIN_ORDERS - 1} kali atau belum ada order selesai, dalam {ACTIVE_DAYS} hari terakhir.",
    "berisiko": f"Pernah order {AT_RISK_MIN_ORDERS} kali atau lebih, tetapi terakhir order {ACTIVE_DAYS + 1} sampai {AT_RISK_DAYS} hari lalu. Layak dihubungi.",
    "tidur":    f"Tidak order lebih dari {AT_RISK_DAYS} hari, atau baru sekali order lalu tidak kembali.",
}


def days_since(last_order_at, now=None):
    """Hari penuh sejak order terakhir (tanggal WIB), None bila belum pernah order."""
    if not last_order_at:
        return None
    today = to_wib(now or timezone.now()).date()
    return max(0, (today - to_wib(last_order_at).date()).days)


def classify(total_orders, last_order_at, now=None):
    """Return (key_segmen, hari_sejak_order_terakhir | None)."""
    days = days_since(last_order_at, now)
    if days is None:
        return "baru", None
    if days <= ACTIVE_DAYS:
        if total_orders >= LOYAL_MIN_ORDERS:
            return "setia", days
        if total_orders <= 1:
            return "baru", days
        return "aktif", days
    if total_orders >= AT_RISK_MIN_ORDERS and days <= AT_RISK_DAYS:
        return "berisiko", days
    return "tidur", days


def segment_overview(customers, now=None):
    """
    `customers` = iterable CustomerLoyalty. Return (peta phone -> (segmen, hari), ringkasan).
    Ringkasan = daftar {key, label, hint, count} sesuai SEGMENT_ORDER, selalu lengkap (count 0 pun ada).
    """
    assigned = {}
    counts = {key: 0 for key in SEGMENT_ORDER}
    for cl in customers:
        key, days = classify(cl.total_orders, cl.last_order_at, now)
        assigned[cl.phone] = (key, days)
        counts[key] += 1
    summary = [
        {"key": k, "label": SEGMENT_LABELS[k], "hint": SEGMENT_HINTS[k], "count": counts[k]}
        for k in SEGMENT_ORDER
    ]
    return assigned, summary


def at_risk_count(now=None):
    """Jumlah pelanggan Berisiko, dipakai saran di Strip Briefing."""
    return sum(
        1
        for cl in CustomerLoyalty.objects.only("total_orders", "last_order_at").iterator()
        if classify(cl.total_orders, cl.last_order_at, now)[0] == "berisiko"
    )
