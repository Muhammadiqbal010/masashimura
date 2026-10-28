"""
API Daftar Blokir anti-scam untuk dashboard (khusus OWNER).

Melengkapi kontrol lewat Telegram (/blokir, /bukablokir, /daftarblokir) tanpa mengubah logika
anti-scam: semua aksi memakai fungsi yang sama di blocklist.py, jadi hasilnya identik dan dua
jalur ini saling melihat perubahan satu sama lain.

  GET  /orders/blocklist/                 daftar + ringkasan (?view=active|history|all, ?kind=phone|ip, ?q=)
  POST /orders/blocklist/                 blokir manual {target, reason?}; target = nomor WA atau IP
  POST /orders/blocklist/<id>/unblock/    buka blokir

Kenapa owner saja: isinya nomor HP dan IP pelanggan, dan membuka blokir berdampak langsung
ke pesanan web (nomor yang dibuka bisa memesan lagi, IP yang dibuka tidak lagi dipaksa QRIS).
"""
from collections import defaultdict
from datetime import timedelta

from django.db.models import Count, Max, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import blocklist, client_info as ci, events
from .models import BlockedContact, Order

LIST_LIMIT = 500          # daftar aktif tidak dipotong sampai sejauh ini
HISTORY_LIMIT = 100       # riwayat (sudah dibuka / kedaluwarsa) hanya yang terbaru
EXPIRING_SOON_DAYS = 14   # IP yang masa blokirnya tinggal segini ditandai "segera berakhir"
MAX_NAMES = 3             # nama pemesan yang ditampilkan per nomor/IP
MAX_REASON = 255

EFFECTS = {
    blocklist.KIND_PHONE: "Pesanan web dari nomor ini ditolak total.",
    blocklist.KIND_IP: "Pesanan cash web dari IP ini dipaksa bayar QRIS (tidak ditolak, karena satu IP bisa dipakai banyak orang).",
}
KIND_LABELS = {blocklist.KIND_PHONE: "Nomor WA", blocklist.KIND_IP: "IP"}


# ─────────────────────────────────────────────
# Izin
# ─────────────────────────────────────────────

class IsOwnerRole(BasePermission):
    """
    Owner saja (admin dan kasir ditolak). Owner = superuser, atau akun dengan UserProfile.role 'owner'
    (sama seperti yang dianggap owner oleh frontend, lihat meta roles di router).
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return getattr(getattr(user, "profile", None), "role", None) == "owner"


# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────

def _state(row, now):
    """
    (status, expires_at, days_left) untuk satu baris.
      active  = berlaku sekarang
      expired = IP yang masa berlakunya habis (flag aktif di database, tetapi sudah tidak dicek lagi)
      lifted  = dibuka manual
    Nomor WA tidak pernah kedaluwarsa, jadi expires_at dan days_left kosong.
    """
    expires_at = days_left = None
    if row.kind == blocklist.KIND_IP:
        expires_at = row.blocked_at + timedelta(days=blocklist.IP_BLOCK_DAYS)
    if not row.is_active:
        return "lifted", expires_at, None
    if expires_at is not None:
        if expires_at <= now:
            return "expired", expires_at, 0
        days_left = (expires_at - now).days + 1   # dibulatkan ke atas: sisa 0,5 hari tetap "1 hari"
    return "active", expires_at, days_left


def _activity(rows):
    """
    Jejak pesanan tiap nomor/IP sekaligus (3 query untuk seluruh daftar, bukan per baris):
    jumlah order, order terakhir, dan beberapa nama pemesan.
    """
    phones = {r.value for r in rows if r.kind == blocklist.KIND_PHONE}
    ips = {r.value for r in rows if r.kind == blocklist.KIND_IP}
    counts = {}
    names = defaultdict(list)

    if phones:
        for r in (Order.objects.filter(customer_phone__in=phones).order_by()
                  .values("customer_phone").annotate(n=Count("id"), last=Max("created_at"))):
            counts[(blocklist.KIND_PHONE, r["customer_phone"])] = (r["n"], r["last"])
    if ips:
        for r in (Order.objects.filter(client_ip__in=ips).order_by()
                  .values("client_ip").annotate(n=Count("id"), last=Max("created_at"))):
            counts[(blocklist.KIND_IP, r["client_ip"])] = (r["n"], r["last"])

    if phones or ips:
        recent = (Order.objects.filter(Q(customer_phone__in=phones) | Q(client_ip__in=ips))
                  .exclude(customer_name="").order_by("-created_at")
                  .values_list("customer_phone", "client_ip", "customer_name")[:3000])
        for phone, ip, name in recent:
            for key in ((blocklist.KIND_PHONE, phone), (blocklist.KIND_IP, ip)):
                bucket = names[key]
                if key in counts and name not in bucket and len(bucket) < MAX_NAMES:
                    bucket.append(name)
    return counts, names


def _location(info):
    """Perkiraan lokasi dari client_info satu order (header Vercel). Hanya petunjuk level kota."""
    info = info or {}
    city, region = info.get("city") or "", info.get("region") or ""
    country = info.get("country") or ""
    parts = [p for p in (city, region) if p]
    if country:
        parts.append("Indonesia" if country == "ID" else country)
    lat, lng = info.get("lat"), info.get("lng")
    return {
        "city": city,
        "region": region,
        "country": country,
        "text": ", ".join(parts),
        "device": info.get("device") or "",
        "timezone": info.get("tz") or "",
        "bot": bool(info.get("bot")),
        "maps_url": ci.maps_url(lat, lng) if isinstance(lat, (int, float)) and isinstance(lng, (int, float)) else "",
    }


def _footprint(rows):
    """
    Jejak asal tiap nomor/IP dari order-ordernya (query tunggal, order terbaru dulu):
      latest[key]  = (order_number, created_at, client_info, ip_atau_nomor_lawan)
      places[key]  = daftar lokasi berbeda (maks 5), terbaru dulu
      related[key] = IP yang pernah dipakai nomor itu / nomor yang pernah muncul dari IP itu (maks 5)
    """
    phones = {r.value for r in rows if r.kind == blocklist.KIND_PHONE}
    ips = {r.value for r in rows if r.kind == blocklist.KIND_IP}
    latest, places, related = {}, defaultdict(list), defaultdict(list)
    if not (phones or ips):
        return latest, places, related

    recent = (Order.objects.filter(Q(customer_phone__in=phones) | Q(client_ip__in=ips))
              .order_by("-created_at")
              .values_list("order_number", "created_at", "customer_phone", "client_ip", "client_info")[:3000])
    for number, created, phone, ip, info in recent:
        pairs = ((blocklist.KIND_PHONE, phone, ip), (blocklist.KIND_IP, ip, phone))
        for kind, mine, other in pairs:
            if not mine or (kind == blocklist.KIND_PHONE and mine not in phones) or (kind == blocklist.KIND_IP and mine not in ips):
                continue
            key = (kind, mine)
            if key not in latest:
                latest[key] = (number, created, info or {}, other)
            text = _location(info)["text"]
            if text and text not in places[key] and len(places[key]) < 5:
                places[key].append(text)
            if other and other not in related[key] and len(related[key]) < 5:
                related[key].append(other)
    return latest, places, related


def _serialize(rows, now=None):
    now = now or timezone.now()
    rows = list(rows)
    counts, names = _activity(rows)
    latest, places, related = _footprint(rows)
    order_numbers = {r.order_number for r in rows if r.order_number}
    order_ids = dict(Order.objects.filter(order_number__in=order_numbers).values_list("order_number", "id")) if order_numbers else {}

    out = []
    for r in rows:
        st, expires_at, days_left = _state(r, now)
        n, last = counts.get((r.kind, r.value), (0, None))
        key = (r.kind, r.value)
        seen = latest.get(key)
        loc = _location(seen[2]) if seen else None
        out.append({
            "id": r.pk,
            "kind": r.kind,
            "kind_label": KIND_LABELS.get(r.kind, r.kind),
            "value": r.value,
            "status": st,
            "is_active": r.is_active,
            "effect": EFFECTS.get(r.kind, ""),
            "reason": r.reason,
            "blocked_by": r.blocked_by,
            "order_number": r.order_number,
            "order_id": order_ids.get(r.order_number),
            "blocked_at": r.blocked_at,
            "unblocked_at": r.unblocked_at,
            "expires_at": expires_at,
            "days_left": days_left,
            "expiring_soon": st == "active" and days_left is not None and days_left <= EXPIRING_SOON_DAYS,
            "order_count": n,
            "last_order_at": last,
            "names": names.get(key, []),
            # Jejak asal (PERKIRAAN dari header Vercel pada order terakhir; bukan alamat jalan/rumah)
            "location": loc,
            "location_order_number": seen[0] if seen else "",
            "location_at": seen[1] if seen else None,
            "other_locations": [p for p in places.get(key, []) if not loc or p != loc["text"]],
            "related_label": "IP yang pernah dipakai" if r.kind == blocklist.KIND_PHONE else "Nomor WA yang pernah muncul",
            "related": related.get(key, []),
        })
    return out


def _summary(now=None):
    now = now or timezone.now()
    cutoff = now - timedelta(days=blocklist.IP_BLOCK_DAYS)
    soon_cutoff = now - timedelta(days=blocklist.IP_BLOCK_DAYS - EXPIRING_SOON_DAYS)

    effective = BlockedContact.objects.filter(is_active=True).filter(
        Q(kind=blocklist.KIND_PHONE) | Q(kind=blocklist.KIND_IP, blocked_at__gte=cutoff)
    )
    return {
        "active": effective.count(),
        "phone": effective.filter(kind=blocklist.KIND_PHONE).count(),
        "ip": effective.filter(kind=blocklist.KIND_IP).count(),
        "ip_expiring_soon": effective.filter(kind=blocklist.KIND_IP, blocked_at__lt=soon_cutoff).count(),
        "history": BlockedContact.objects.exclude(pk__in=effective.values("pk")).count(),
        "ip_block_days": blocklist.IP_BLOCK_DAYS,
        "expiring_soon_days": EXPIRING_SOON_DAYS,
    }


def _search(qs, text):
    text = (text or "").strip()
    if not text:
        return qs
    cond = (Q(value__icontains=text) | Q(reason__icontains=text)
            | Q(order_number__icontains=text) | Q(blocked_by__icontains=text))
    target = blocklist.parse_target(text)   # "+62 812-3456-7890" juga ketemu sebagai 081234567890
    if target:
        cond |= Q(kind=target[0], value=target[1])
    return qs.filter(cond)


def _one(row):
    return _serialize([row])[0]


# ─────────────────────────────────────────────
# Views
# ─────────────────────────────────────────────

class BlocklistView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerRole]

    def get(self, request):
        now = timezone.now()
        view = request.query_params.get("view", "active")
        kind = request.query_params.get("kind", "")
        cutoff = now - timedelta(days=blocklist.IP_BLOCK_DAYS)

        qs = BlockedContact.objects.all()
        if kind in (blocklist.KIND_PHONE, blocklist.KIND_IP):
            qs = qs.filter(kind=kind)
        qs = _search(qs, request.query_params.get("q"))

        effective = Q(is_active=True) & (Q(kind=blocklist.KIND_PHONE) | Q(kind=blocklist.KIND_IP, blocked_at__gte=cutoff))
        if view == "history":
            qs = qs.exclude(effective).order_by("-unblocked_at", "-blocked_at")[:HISTORY_LIMIT]
        elif view == "all":
            qs = qs.order_by("-blocked_at")[:LIST_LIMIT]
        else:
            view = "active"
            qs = qs.filter(effective).order_by("-blocked_at")[:LIST_LIMIT]

        return Response({"view": view, "summary": _summary(now), "results": _serialize(qs, now)})

    def post(self, request):
        raw = request.data.get("target")
        reason = str(request.data.get("reason") or "").strip()[:MAX_REASON]
        parsed = blocklist.parse_target(raw)
        if not parsed:
            return Response(
                {"detail": "Isi dengan nomor WhatsApp (contoh 081234567890) atau alamat IP (contoh 114.122.1.2)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        kind, value = parsed
        actor = f"{events.actor_from_request(request) or 'Owner'} (dashboard)"
        fresh = blocklist.block(kind, value, actor=actor, reason=reason or "Manual lewat dashboard")
        row = BlockedContact.objects.get(kind=kind, value=value)
        label = KIND_LABELS[kind]
        return Response(
            {
                "created": fresh,
                "message": (f"{label} {value} diblokir. {EFFECTS[kind]}" if fresh
                           else f"{label} {value} sudah ada di daftar blokir."),
                "item": _one(row),
                "summary": _summary(),
            },
            status=status.HTTP_201_CREATED if fresh else status.HTTP_200_OK,
        )


class BlocklistUnblockView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerRole]

    def post(self, request, pk):
        try:
            row = BlockedContact.objects.get(pk=pk)
        except BlockedContact.DoesNotExist:
            return Response({"detail": "Data blokir tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)

        changed = blocklist.unblock(row.kind, row.value)
        row.refresh_from_db()
        label = KIND_LABELS.get(row.kind, row.kind)
        return Response({
            "changed": changed,
            "message": (f"Blokir {label} {row.value} dibuka." if changed
                        else f"{label} {row.value} sudah tidak diblokir."),
            "item": _one(row),
            "summary": _summary(),
        })
