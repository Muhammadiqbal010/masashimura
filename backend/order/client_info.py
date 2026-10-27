"""
Jejak asal pemesan web (IP, lokasi perkiraan, perangkat) untuk melacak pesanan bodong / scam.
MURNI: tanpa Django/DB, jadi bisa dites dengan Python biasa.

Sumber data = header yang dipasang Vercel di setiap request ke backend:
  x-forwarded-for            IP asli pengguna (Vercel menimpanya, jadi tidak bisa dipalsukan dari browser)
  x-vercel-ip-country        kode negara (ID, MY, SG, ...)
  x-vercel-ip-country-region kode wilayah ISO 3166-2 (JB = Jawa Barat)
  x-vercel-ip-city           nama kota (URL-encoded)
  x-vercel-ip-latitude/longitude, x-vercel-ip-timezone

PENTING: lokasi dari IP hanyalah PERKIRAAN (level kota, kadang meleset; pengguna paket data seluler
sering terbaca di kota pusat operator; VPN menampilkan lokasi server VPN). Jadikan petunjuk dan pola,
bukan bukti mutlak.
"""
import ipaddress
import math
import re
from urllib.parse import unquote

# Ambang tanda mencurigakan (lihat assess()).
MANY_ORDERS_24H = 3        # >= sekian pesanan dari satu IP dalam 24 jam
MANY_PHONES_24H = 3        # >= sekian nomor WA berbeda dari satu IP dalam 24 jam
MANY_AUTO_CANCELLED_7D = 2  # >= sekian pesanan lama dari IP ini yang batal otomatis (tak pernah diterima kasir)
DEFAULT_RADIUS_KM = 30

# Kode ISO 3166-2:ID (format region dari Vercel) -> nama provinsi.
ID_REGIONS = {
    "AC": "Aceh", "SU": "Sumatera Utara", "SB": "Sumatera Barat", "RI": "Riau", "KR": "Kepulauan Riau",
    "JA": "Jambi", "SS": "Sumatera Selatan", "BB": "Bangka Belitung", "BE": "Bengkulu", "LA": "Lampung",
    "JK": "DKI Jakarta", "BT": "Banten", "JB": "Jawa Barat", "JT": "Jawa Tengah", "YO": "DI Yogyakarta",
    "JI": "Jawa Timur", "BA": "Bali", "NB": "Nusa Tenggara Barat", "NT": "Nusa Tenggara Timur",
    "KB": "Kalimantan Barat", "KT": "Kalimantan Tengah", "KS": "Kalimantan Selatan",
    "KI": "Kalimantan Timur", "KU": "Kalimantan Utara", "SA": "Sulawesi Utara", "ST": "Sulawesi Tengah",
    "SN": "Sulawesi Selatan", "SG": "Sulawesi Tenggara", "GO": "Gorontalo", "SR": "Sulawesi Barat",
    "MA": "Maluku", "MU": "Maluku Utara", "PA": "Papua", "PB": "Papua Barat", "PS": "Papua Selatan",
    "PT": "Papua Tengah", "PE": "Papua Pegunungan", "PD": "Papua Barat Daya",
}

# User-Agent yang bukan browser manusia biasa (skrip, alat uji API, browser tanpa layar).
_BOT_UA = re.compile(
    r"(python-requests|python-urllib|aiohttp|httpx|curl/|wget/|postman|insomnia|go-http-client|"
    r"java/|libwww|headlesschrome|phantomjs|puppeteer|playwright|selenium|scrapy|node-fetch|axios/|okhttp)",
    re.I,
)


# ── IP ──────────────────────────────────────────────────────────────────────

def _valid_ip(raw):
    s = str(raw or "").strip().strip('"')
    if not s:
        return None
    if s.startswith("[") and "]" in s:          # [2001:db8::1]:443
        s = s[1:s.index("]")]
    elif s.count(":") == 1 and "." in s:        # 1.2.3.4:5678
        s = s.split(":")[0]
    try:
        return str(ipaddress.ip_address(s))
    except ValueError:
        return None


def get_ip(meta):
    """IP pengguna. Di Vercel entri PERTAMA x-forwarded-for = IP asli (header ini ditimpa Vercel)."""
    xff = str(meta.get("HTTP_X_FORWARDED_FOR") or "")
    first = _valid_ip(xff.split(",")[0]) if xff else None
    return first or _valid_ip(meta.get("HTTP_X_REAL_IP")) or _valid_ip(meta.get("REMOTE_ADDR")) or ""


# ── Lokasi & perangkat ──────────────────────────────────────────────────────

def _float(raw, lo, hi):
    try:
        val = float(str(raw).strip())
    except (TypeError, ValueError):
        return None
    return val if lo <= val <= hi else None


def region_name(country, region):
    region = str(region or "").strip()
    if country == "ID" and region.upper() in ID_REGIONS:
        return ID_REGIONS[region.upper()]
    return region


def flag_emoji(country):
    c = str(country or "").upper()
    if len(c) != 2 or not c.isalpha():
        return ""
    return "".join(chr(0x1F1E6 + ord(ch) - 65) for ch in c)


def country_label(country):
    c = str(country or "").upper()
    if not c:
        return ""
    return f"{flag_emoji(c)} Indonesia".strip() if c == "ID" else f"{flag_emoji(c)} {c}".strip()


def parse_device(ua):
    """Ringkas User-Agent jadi 'Android 13 · Chrome (SM-A546E)'. Tidak dikenali → ''."""
    ua = str(ua or "")
    os_name, model = "", ""
    m = re.search(r"Android\s([\d.]+)", ua)
    if m:
        os_name = f"Android {m.group(1)}"
        mm = re.search(r"Android\s[\d.]+;\s*([^;)]+?)(?:\sBuild|\)|;|$)", ua)
        if mm and len(mm.group(1).strip()) > 2:   # Chrome modern hanya menulis "K" → abaikan
            model = mm.group(1).strip()
    elif "iPhone" in ua or "iPad" in ua:
        m = re.search(r"OS (\d+)", ua)
        os_name = f"iOS {m.group(1)}" if m else "iOS"
    elif "Windows NT" in ua:
        os_name = "Windows"
    elif "Mac OS X" in ua or "Macintosh" in ua:
        os_name = "macOS"
    elif "CrOS" in ua:
        os_name = "ChromeOS"
    elif "Linux" in ua:
        os_name = "Linux"

    browser = ""
    for needle, label in (
        ("Edg", "Edge"), ("OPR/", "Opera"), ("SamsungBrowser", "Samsung Internet"),
        ("Firefox", "Firefox"), ("FxiOS", "Firefox"), ("CriOS", "Chrome"), ("Chrome", "Chrome"),
        ("Safari", "Safari"),
    ):
        if needle in ua:
            browser = label
            break

    text = " · ".join(p for p in (os_name, browser) if p)
    if model:
        text += f" ({model})"
    return text


def looks_like_bot(ua):
    ua = str(ua or "").strip()
    return (not ua) or bool(_BOT_UA.search(ua)) or not ua.startswith("Mozilla/")


def collect(meta):
    """
    Kumpulkan jejak dari request.META. Selalu mengembalikan dict (nilai kosong kalau header tidak ada):
      ip, country, region, city, lat, lng, tz, device, ua, bot
    """
    country = str(meta.get("HTTP_X_VERCEL_IP_COUNTRY") or "").strip().upper()[:2]
    ua = str(meta.get("HTTP_USER_AGENT") or "").strip()
    return {
        "ip": get_ip(meta),
        "country": country if country.isalpha() else "",
        "region": region_name(country, meta.get("HTTP_X_VERCEL_IP_COUNTRY_REGION"))[:60],
        "city": unquote(str(meta.get("HTTP_X_VERCEL_IP_CITY") or "")).strip()[:80],
        "lat": _float(meta.get("HTTP_X_VERCEL_IP_LATITUDE"), -90, 90),
        "lng": _float(meta.get("HTTP_X_VERCEL_IP_LONGITUDE"), -180, 180),
        "tz": str(meta.get("HTTP_X_VERCEL_IP_TIMEZONE") or "").strip()[:40],
        "device": parse_device(ua),
        "ua": ua[:250],
        "bot": looks_like_bot(ua),
    }


# ── Peta & jarak ────────────────────────────────────────────────────────────

def maps_url(lat, lng):
    if lat is None or lng is None:
        return ""
    return f"https://www.google.com/maps?q={lat:.4f},{lng:.4f}"


def distance_km(lat1, lng1, lat2, lng2):
    """Jarak garis lurus (haversine), km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371.0088 * 2 * math.asin(math.sqrt(a))


def distance_from_store(info, store):
    """store = (lat, lng) atau None. None kalau toko / lokasi pemesan tidak diketahui."""
    if not store or info.get("lat") is None or info.get("lng") is None:
        return None
    return distance_km(info["lat"], info["lng"], store[0], store[1])


# ── Penilaian ───────────────────────────────────────────────────────────────

# Bobot tiap tanda (dipakai untuk skor 🟢/🟡/🔴): 1 = patut dilirik, 2 = kuat.
RISK_YELLOW_AT = 1   # skor >= ini → 🟡 PERIKSA
RISK_RED_AT = 3      # skor >= ini → 🔴 CURIGA
BIG_PORTIONS_MIN = 12       # porsi minimal supaya dianggap "besar"
BIG_PORTIONS_FACTOR = 3     # ...dan minimal sekian kali rata-rata porsi per pesanan toko
MANY_SAME_NAME_PHONES = 2   # >= sekian nomor berbeda dengan nama yang sama dari satu IP dalam 24 jam

# Link/ajakan pindah chat di catatan pesanan: pola khas scam ("transfer dulu ke ...", "klik link ...").
_LINK_RE = re.compile(
    r"(https?://|www\.|wa\.me|t\.me|bit\.ly|tinyurl|\b[a-z0-9-]+\.(?:com|net|org|id|co|me|link|xyz|top|site|online|info)\b)",
    re.I,
)


def has_link(text):
    return bool(_LINK_RE.search(str(text or "")))


def normalize_name(name):
    return " ".join(str(name or "").lower().split())


def assess_detail(ip, info, history=None, distance=None, radius_km=DEFAULT_RADIUS_KM):
    """
    Daftar (teks tanda, bobot) yang patut dicek kasir (kosong = tidak ada yang janggal terdeteksi).
    history (semua kunci boleh kosong):
      orders_24h, phones_24h, auto_cancelled_7d   dari IP yang sama
      same_name_phones                            nomor berbeda dengan NAMA SAMA dari IP yang sama (24 jam)
      ip_blocked                                  IP ada di daftar blokir
      after_hours                                 order masuk di luar jam buka toko
      portions, avg_portions                      porsi order ini dan rata-rata porsi per pesanan toko
      link_in_notes                               catatan pesanan memuat link
    Ini petunjuk, bukan vonis: IP wifi bersama / jaringan seluler bisa dipakai banyak orang sekaligus.
    """
    history = history or {}
    flags = []
    if not ip:
        flags.append(("IP tidak terbaca", 1))
    country = info.get("country")
    if country and country != "ID":
        flags.append((f"Berasal dari luar Indonesia ({country})", 2))
    if info.get("bot"):
        flags.append(("Perangkat tidak seperti browser biasa (kemungkinan skrip/bot)", 2))
    if distance is not None and radius_km and distance > radius_km:
        flags.append((f"Jauh dari toko (±{round(distance)} km)", 1))
    if history.get("ip_blocked"):
        flags.append(("IP ini ada di daftar blokir", 2))
    n = history.get("orders_24h") or 0
    if n >= MANY_ORDERS_24H:
        flags.append((f"IP ini sudah {n} pesanan dalam 24 jam", 1))
    p = history.get("phones_24h") or 0
    if p >= MANY_PHONES_24H:
        flags.append((f"IP ini dipakai {p} nomor WA berbeda dalam 24 jam", 1))
    sn = history.get("same_name_phones") or 0
    if sn >= MANY_SAME_NAME_PHONES:
        flags.append((f"Nama yang sama dipakai {sn} nomor WA berbeda dari IP ini", 2))
    c = history.get("auto_cancelled_7d") or 0
    if c >= MANY_AUTO_CANCELLED_7D:
        flags.append((f"{c} pesanan sebelumnya dari IP ini tidak pernah diterima (batal otomatis)", 2))
    if history.get("after_hours"):
        flags.append(("Masuk di luar jam buka toko", 1))
    portions = history.get("portions") or 0
    avg = history.get("avg_portions") or 0
    if portions >= BIG_PORTIONS_MIN and avg and portions >= BIG_PORTIONS_FACTOR * avg:
        flags.append((f"Porsi jauh di atas kebiasaan toko ({portions} porsi, biasanya ±{round(avg)})", 1))
    if history.get("link_in_notes"):
        flags.append(("Catatan pesanan berisi link", 2))
    return flags


def assess(ip, info, history=None, distance=None, radius_km=DEFAULT_RADIUS_KM):
    """Hanya teks tandanya (lihat assess_detail)."""
    return [text for text, _ in assess_detail(ip, info, history, distance, radius_km)]


def risk_level(details, completed_orders=None):
    """
    'green' (AMAN) / 'yellow' (PERIKSA) / 'red' (CURIGA) dari hasil assess_detail.
    Pelanggan lama (>= 1 pesanan selesai) hampir pasti asli: skor turun 1. Nomor baru dengan tanda
    apa pun naik 1. Nomor baru TANPA tanda tetap hijau (kebanyakan pelanggan baru itu asli).
    """
    score = sum(weight for _, weight in details)
    if score and completed_orders is not None:
        score += -1 if completed_orders >= 1 else 1
    score = max(score, 0)
    if score >= RISK_RED_AT:
        return "red"
    if score >= RISK_YELLOW_AT:
        return "yellow"
    return "green"
