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

from . import blocklist, dossier, events
from .models import BlockedAttempt, BlockedContact, Order

LIST_LIMIT = 500          # daftar aktif tidak dipotong sampai sejauh ini
HISTORY_LIMIT = 100       # riwayat (sudah dibuka / kedaluwarsa) hanya yang terbaru
EXPIRING_SOON_DAYS = 14   # IP yang masa blokirnya tinggal segini ditandai "segera berakhir"
MAX_NAMES = 3             # nama pemesan yang ditampilkan per nomor/IP
RECENT_ORDERS = 5         # pesanan terakhir yang ditampilkan per nomor/IP
ATTEMPTS_SHOWN = 5        # percobaan terbaru yang ditampilkan per nomor/IP
ATTEMPT_LIST_LIMIT = 200  # daftar percobaan terbaru (halaman Percobaan)
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


_location = dossier.location   # satu sumber dengan pencarian admin & bot Telegram


def _footprint(rows):
    """
    Jejak asal tiap nomor/IP dari order-ordernya (query tunggal, order terbaru dulu):
      latest[key]  = (order_number, created_at, client_info, ip_atau_nomor_lawan)
      places[key]  = daftar lokasi berbeda (maks 5), terbaru dulu
      related[key] = IP yang pernah dipakai nomor itu / nomor yang pernah muncul dari IP itu (maks 5)
      recent[key]  = pesanan terakhir (maks RECENT_ORDERS) lengkap: nama, nomor, IP, lokasi, tautan Maps
    """
    phones = {r.value for r in rows if r.kind == blocklist.KIND_PHONE}
    ips = {r.value for r in rows if r.kind == blocklist.KIND_IP}
    latest, places, related, recent_orders = {}, defaultdict(list), defaultdict(list), defaultdict(list)
    if not (phones or ips):
        return latest, places, related, recent_orders

    recent = (Order.objects.filter(Q(customer_phone__in=phones) | Q(client_ip__in=ips))
              .order_by("-created_at", "-id").values(*dossier.ORDER_FIELDS)[:3000])
    for row in recent:
        number, created, phone, ip, info = (row["order_number"], row["created_at"], row["customer_phone"],
                                            row["client_ip"], row["client_info"])
        built = None
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
            if len(recent_orders[key]) < RECENT_ORDERS:
                built = built or dossier.order_row(row)
                recent_orders[key].append(built)
    return latest, places, related, recent_orders


def _ips_blocked(attempts):
    """Himpunan IP (dari daftar percobaan) yang sedang diblokir efektif — 1 query untuk seluruh daftar."""
    ips = {a.client_ip for a in attempts if a.client_ip}
    if not ips:
        return set()
    cutoff = timezone.now() - timedelta(days=blocklist.IP_BLOCK_DAYS)
    return set(BlockedContact.objects.filter(kind=blocklist.KIND_IP, is_active=True, blocked_at__gte=cutoff,
                                             value__in=ips).values_list("value", flat=True))


def _attempt_row(a, blocked_ips=None):
    loc = _location(a.client_info)
    return {
        "id": a.pk,
        "kind": a.kind,
        "kind_label": KIND_LABELS.get(a.kind, a.kind),
        "value": a.value,
        "phone": a.phone,
        "name": a.name,
        "ip": a.client_ip or "",
        # None = tidak dihitung (tampilan ringkas di dalam daftar blokir); True/False = status blokir IP saat ini
        "ip_blocked": None if blocked_ips is None else (a.client_ip in blocked_ips),
        "created_at": a.created_at,
        "location": loc,
        "location_text": loc["text"],
        "maps_url": loc["maps_url"],
        "device": loc["device"],
        "bot": loc["bot"],
    }


def _attempts(rows):
    """{key: [percobaan terbaru…]} untuk semua baris sekaligus (1 query, maks ATTEMPTS_SHOWN per kunci)."""
    keys = {(r.kind, r.value) for r in rows}
    out = defaultdict(list)
    if not keys:
        return out
    values = {v for _, v in keys}
    for a in BlockedAttempt.objects.filter(value__in=values).order_by("-created_at")[:3000]:
        key = (a.kind, a.value)
        if key in keys and len(out[key]) < ATTEMPTS_SHOWN:
            out[key].append(_attempt_row(a))
    return out


def _serialize(rows, now=None):
    now = now or timezone.now()
    rows = list(rows)
    counts, names = _activity(rows)
    latest, places, related, recent_orders = _footprint(rows)
    attempt_totals = blocklist.attempt_counts({(r.kind, r.value) for r in rows})
    attempts = _attempts(rows)
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
            # Pesanan terakhir dari nomor/IP ini (nama, nomor WA, IP, lokasi perkiraan, tautan Google Maps)
            "recent_orders": recent_orders.get(key, []),
            # Percobaan order SETELAH diblokir (ditolak/dipaksa QRIS)
            "attempt_count": attempt_totals.get(key, (0, None))[0],
            "last_attempt_at": attempt_totals.get(key, (0, None))[1],
            "attempts": attempts.get(key, []),
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
        "attempts_7d": BlockedAttempt.objects.filter(created_at__gte=now - timedelta(days=7)).count(),
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


class BlocklistAttemptsView(APIView):
    """
    GET /orders/blocklist/attempts/  — percobaan order dari nomor/IP yang sudah diblokir, terbaru dulu.
    Parameter: ?days=7 (1–180), ?q=<nomor|IP|nama>. Berguna untuk melihat blokir benar-benar bekerja dan
    menemukan nomor/IP baru yang dipakai orang yang sama.
    """
    permission_classes = [IsAuthenticated, IsOwnerRole]

    def get(self, request):
        try:
            days = max(1, min(int(request.query_params.get("days", 7)), blocklist.ATTEMPT_KEEP_DAYS))
        except (TypeError, ValueError):
            days = 7
        qs = BlockedAttempt.objects.filter(created_at__gte=timezone.now() - timedelta(days=days))
        text = (request.query_params.get("q") or "").strip()
        if text:
            cond = Q(value__icontains=text) | Q(phone__icontains=text) | Q(name__icontains=text) | Q(client_ip__icontains=text)
            target = blocklist.parse_target(text)
            if target:
                cond |= Q(kind=target[0], value=target[1]) | Q(phone=target[1])
            qs = qs.filter(cond)
        total = qs.count()
        rows = list(qs.order_by("-created_at")[:ATTEMPT_LIST_LIMIT])
        blocked_ips = _ips_blocked(rows)
        return Response({
            "days": days,
            "total": total,
            "results": [_attempt_row(a, blocked_ips) for a in rows],
        })


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
