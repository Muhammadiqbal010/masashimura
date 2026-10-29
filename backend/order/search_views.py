"""
Pencarian admin (Ctrl/Cmd+K) sisi server:  GET /orders/admin-search/?q=<teks>

Kenapa di server: pencarian lama hanya melihat data yang sudah dimuat browser (pesanan terbatas, tanpa IP
dan lokasi, tanpa blokir/percobaan/staf/pengeluaran). Di sini semuanya dicari langsung di database dan
dikembalikan LENGKAP (nomor WA, nomor order, IP, lokasi perkiraan, tautan Google Maps).

Hak akses per peran:
  owner  : semua bagian, termasuk IP/lokasi, blokir, percobaan terblokir, staf, pengeluaran
  admin  : pesanan (tanpa IP/lokasi) dan pelanggan
  kasir  : hanya pesanan HARI INI (sama dengan halaman Pesanan), tanpa IP/lokasi
Menu, promo, dan reward poin tetap dicari di browser (datanya kecil dan sudah dimuat).
"""
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import blocklist, dossier, guards
from .models import BlockedAttempt, BlockedContact, CustomerLoyalty, Order, WIB
from .permissions import IsStaffOrOwner

MIN_QUERY = 2
LIMITS = {"orders": 8, "customers": 5, "blocked": 5, "attempts": 5, "staff": 5, "expenses": 5}


def _role(user):
    if user.is_superuser:
        return "owner"
    return (getattr(getattr(user, "profile", None), "role", "") or "").lower()


def _rp(v):
    return "Rp " + f"{int(round(float(v or 0))):,}".replace(",", ".")


def _day(dt):
    return timezone.localtime(dt, WIB).strftime("%Y-%m-%d")


def _when(dt):
    return timezone.localtime(dt, WIB).strftime("%d/%m %H:%M")


def _phone_variants(text):
    """'+62 812-3456' juga harus cocok dengan '0812…': kembalikan teks asli + bentuk lokal + potongan digit."""
    out = {text}
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) >= 4:
        out.add(digits)
        local = guards.normalize_phone(text)
        if local:
            out.add(local)
    return {v for v in out if v}


def _cond(fields, variants):
    cond = Q()
    for f in fields:
        for v in variants:
            cond |= Q(**{f"{f}__icontains": v})
    return cond


def _orders(text, role):
    variants = _phone_variants(text)
    cond = _cond(["order_number", "customer_name", "customer_phone", "table_number", "notes",
                  "items__menu__name", "items__bundle_name"], variants)
    owner = role == "owner"
    if owner:
        cond |= _cond(["client_ip", "client_info__city", "client_info__region"], variants)
    qs = Order.objects.filter(cond).distinct()
    if role not in ("owner", "admin"):
        start = timezone.localtime(timezone.now(), WIB).replace(hour=0, minute=0, second=0, microsecond=0)
        qs = qs.filter(created_at__gte=start)
    rows = qs.order_by("-created_at", "-id").values(*dossier.ORDER_FIELDS)[:LIMITS["orders"]]
    out = []
    for r in rows:
        o = dossier.order_row(r)
        details = [f"WA {o['phone']}" if o["phone"] else "Tanpa nomor"]
        if owner and o["ip"]:
            details.append(f"IP {o['ip']}")
        if owner and o["location_text"]:
            details.append(o["location_text"])
        out.append({
            "key": f"order-{o['id']}",
            "label": f"{o['order_number']} · {o['name'] or 'Walk In'}",
            "hint": f"{_when(o['created_at'])} · {_rp(o['total'])} · {o['status_label']}",
            "details": details,
            "maps_url": o["maps_url"] if owner else "",
            "to": f"/admin/orders?date={_day(o['created_at'])}&q={o['order_number']}",
        })
    return out


def _customers(text):
    variants = _phone_variants(text)
    rows = CustomerLoyalty.objects.filter(_cond(["name", "phone"], variants)).order_by("-total_spent")[:LIMITS["customers"]]
    return [{
        "key": f"cust-{c.phone}",
        "label": c.name or c.phone,
        "hint": f"{c.points:,} poin · {c.total_orders} pesanan".replace(",", "."),
        "details": [f"WA {c.phone}"],
        "to": f"/admin/customers?q={c.phone}",
    } for c in rows]


def _blocked(text):
    variants = _phone_variants(text)
    target = blocklist.parse_target(text)
    cond = _cond(["value", "reason", "order_number", "blocked_by"], variants)
    if target:
        cond |= Q(kind=target[0], value=target[1])
    out = []
    for b in BlockedContact.objects.filter(cond).order_by("-blocked_at")[:LIMITS["blocked"]]:
        kind = "Nomor WA" if b.kind == blocklist.KIND_PHONE else "IP"
        state = "Diblokir" if b.is_active else "Blokir dibuka"
        details = [b.reason] if b.reason else []
        if b.order_number:
            details.append(f"Order {b.order_number}")
        out.append({
            "key": f"block-{b.pk}",
            "label": f"{kind} {b.value}",
            "hint": f"{state} · {_when(b.blocked_at)}",
            "details": details,
            "to": f"/admin/settings?q={b.value}#blokir",
        })
    return out


def _attempts(text):
    variants = _phone_variants(text)
    cond = _cond(["value", "phone", "name", "client_ip"], variants)
    out = []
    for a in BlockedAttempt.objects.filter(cond).order_by("-created_at")[:LIMITS["attempts"]]:
        loc = dossier.location(a.client_info)
        details = [f"WA {a.phone}" if a.phone else "", f"IP {a.client_ip}" if a.client_ip else "", loc["text"]]
        out.append({
            "key": f"attempt-{a.pk}",
            "label": f"Percobaan terblokir · {a.name or a.value}",
            "hint": _when(a.created_at),
            "details": [d for d in details if d],
            "maps_url": loc["maps_url"],
            "to": f"/admin/settings?q={a.value}#blokir",
        })
    return out


def _staff(text):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    variants = _phone_variants(text)
    cond = _cond(["username", "first_name", "last_name", "profile__phone"], variants)
    rows = (User.objects.filter(cond).filter(profile__role__in=["owner", "admin", "kasir"])
            .select_related("profile").order_by("username")[:LIMITS["staff"]])
    return [{
        "key": f"staff-{u.pk}",
        "label": (u.get_full_name() or u.username),
        "hint": f"Staf · {u.profile.role}",
        "details": [f"@{u.username}"] + ([f"WA {u.profile.phone}"] if u.profile.phone else []),
        "to": f"/admin/staff?q={u.username}",
    } for u in rows]


def _expenses(text):
    from finance.models import Expense

    out = []
    for e in Expense.objects.filter(description__icontains=text).order_by("-date", "-id")[:LIMITS["expenses"]]:
        out.append({
            "key": f"expense-{e.pk}",
            "label": e.description,
            "hint": f"{e.date:%d/%m/%Y} · {_rp(e.amount)}",
            "details": [],
            "to": f"/admin/finance?date={e.date:%Y-%m-%d}",
        })
    return out


class AdminSearchView(APIView):
    permission_classes = [IsAuthenticated, IsStaffOrOwner]

    def get(self, request):
        text = (request.query_params.get("q") or "").strip()[:80]
        if len(text) < MIN_QUERY:
            return Response({"q": text, "sections": []})
        role = _role(request.user)

        builders = [("Pesanan", lambda: _orders(text, role))]
        if role in ("owner", "admin"):
            builders.append(("Pelanggan", lambda: _customers(text)))
        if role == "owner":
            builders += [
                ("Blokir anti-scam", lambda: _blocked(text)),
                ("Percobaan terblokir", lambda: _attempts(text)),
                ("Staf", lambda: _staff(text)),
                ("Pengeluaran", lambda: _expenses(text)),
            ]
        sections = []
        for title, build in builders:
            items = build()
            if items:
                sections.append({"title": title, "items": items})
        return Response({"q": text, "sections": sections})
