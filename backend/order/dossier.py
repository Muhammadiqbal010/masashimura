"""
Rangkuman jejak satu pesanan / nomor WA / IP dalam bentuk dict siap pakai.

Dipakai bersama oleh: daftar blokir di dashboard (blocklist_views), pencarian admin (search_views),
dan bot Telegram (/lacak, alert percobaan terblokir) supaya semuanya menampilkan data yang SAMA.

Catatan data: model Order TIDAK punya alamat jalan/rumah (pesanan web hanya makan di tempat atau bungkus).
Satu-satunya petunjuk "dari mana" adalah perkiraan lokasi dari IP (kota/provinsi/negara + koordinat pusat
kota, dari header Vercel, lihat client_info.py). Itu yang ditampilkan sebagai "lokasi" dan tautan Google Maps;
akurasinya level kota, bukan alamat rumah, dan data seluler/VPN bisa meleset jauh.
"""
from . import client_info as ci

ORDER_FIELDS = (
    "id", "order_number", "source", "status", "payment_status", "payment_method", "awaiting_confirmation",
    "cancelled_by", "customer_name", "customer_phone", "total_price", "created_at", "client_ip", "client_info",
    "table_number", "service_type",
)


def location(info):
    """Perkiraan lokasi dari client_info satu order. Hanya petunjuk level kota."""
    info = info or {}
    city, region = info.get("city") or "", info.get("region") or ""
    country = info.get("country") or ""
    parts = [p for p in (city, region) if p]
    if country:
        parts.append("Indonesia" if country == "ID" else country)
    lat, lng = info.get("lat"), info.get("lng")
    has_xy = isinstance(lat, (int, float)) and isinstance(lng, (int, float))
    return {
        "city": city,
        "region": region,
        "country": country,
        "text": ", ".join(parts),
        "device": info.get("device") or "",
        "timezone": info.get("tz") or "",
        "bot": bool(info.get("bot")),
        "lat": lat if has_xy else None,
        "lng": lng if has_xy else None,
        "maps_url": ci.maps_url(lat, lng) if has_xy else "",
    }


def status_label(status, payment_status, awaiting, cancelled_by):
    if status == "cancelled" or payment_status == "void":
        return "Batal otomatis" if cancelled_by == "sistem" else "Dibatalkan"
    if awaiting:
        return "Menunggu diterima"
    if status == "completed":
        return "Selesai"
    return "Diproses"


def order_row(o):
    """
    Satu order → dict. `o` boleh instance Order atau dict dari .values(*ORDER_FIELDS).
    Berisi SEMUA yang dibutuhkan untuk melacak: nama, nomor, IP, lokasi perkiraan, tautan Maps, perangkat.
    """
    get = (lambda k: o.get(k)) if isinstance(o, dict) else (lambda k: getattr(o, k, None))
    loc = location(get("client_info"))
    return {
        "id": get("id"),
        "order_number": get("order_number") or "",
        "source": get("source") or "",
        "name": get("customer_name") or "",
        "phone": get("customer_phone") or "",
        "ip": get("client_ip") or "",
        "total": float(get("total_price") or 0),
        "status": get("status") or "",
        "payment_method": get("payment_method") or "",
        "status_label": status_label(get("status"), get("payment_status"), get("awaiting_confirmation"), get("cancelled_by")),
        "created_at": get("created_at"),
        "table_number": get("table_number") or "",
        "service_type": get("service_type") or "",
        "location": loc,
        "location_text": loc["text"],
        "maps_url": loc["maps_url"],
        "device": loc["device"],
    }


def recent_orders_for(kind, value, limit=5):
    """Pesanan terakhir untuk satu nomor WA ('phone') atau IP ('ip'), terbaru dulu."""
    from .models import Order

    field = "customer_phone" if kind == "phone" else "client_ip"
    if not value:
        return []
    rows = Order.objects.filter(**{field: value}).order_by("-created_at", "-id").values(*ORDER_FIELDS)[:limit]
    return [order_row(r) for r in rows]
