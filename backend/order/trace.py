"""
Pelacakan asal pemesan untuk bot Telegram:  /lacak MSM-261027-AB12   atau   /lacak 114.122.1.2

Dipakai setelah kejadian ("pesanan ini ternyata scam, dari mana dia?"): menampilkan IP, lokasi perkiraan,
perangkat, tanda mencurigakan, dan SEMUA pesanan web lain dari IP yang sama (30 hari terakhir).
Hanya bisa dipanggil dari chat Telegram yang terdaftar (dicek di telegram_bot.handle_command).
"""
from datetime import timedelta

from django.utils import timezone

from . import client_info as ci
from . import notify
from . import telegram_ui as ui
from .models import Order

WINDOW_DAYS = 30
MAX_LIST = 10

USAGE = (
    "Cara pakai:\n"
    "/lacak MSM-261027-AB12 — jejak satu pesanan (boleh 4 karakter terakhirnya saja)\n"
    "/lacak 114.122.1.2 — semua pesanan dari satu IP"
)


def _status_label(o):
    if o.status == "cancelled" or o.payment_status == "void":
        return "batal otomatis" if o.cancelled_by == "sistem" else "dibatalkan"
    if o.awaiting_confirmation:
        return "menunggu diterima"
    if o.status == "completed":
        return "selesai"
    return "diproses"


def _when(dt):
    return timezone.localtime(dt).strftime("%d/%m %H:%M")


def _order_line(o):
    return (
        f"• {o.order_number} · {o.customer_name or 'Guest'} · {o.customer_phone or '-'} · "
        f"{ui.rp(o.total_price)} · {_status_label(o)} · {_when(o.created_at)}"
    )


def _find_order(q):
    exact = Order.objects.filter(order_number__iexact=q).first()
    if exact:
        return exact
    if len(q) >= 4:
        matches = list(Order.objects.filter(order_number__iendswith=q)[:2])
        if len(matches) == 1:
            return matches[0]
    return None


def _block(order):
    """Teks 'Asal pemesan' untuk satu order (memakai penilaian yang sama dengan pesan Telegram)."""
    client, flags = notify.client_view(order)
    if not client:
        return ["", "Tidak ada jejak asal untuk pesanan ini (pesanan POS, atau dibuat sebelum fitur pelacakan aktif)."]
    return ui.client_lines({"client": client, "client_flags": flags})


def _others(ip, exclude_pk=None):
    since = timezone.now() - timedelta(days=WINDOW_DAYS)
    qs = Order.objects.filter(source="web", client_ip=ip, created_at__gte=since).order_by("-created_at")
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    total = qs.count()
    return list(qs[:MAX_LIST]), total, qs.exclude(customer_phone="").values("customer_phone").distinct().count()


def _others_lines(ip, exclude_pk=None):
    rows, total, phones = _others(ip, exclude_pk)
    if not rows:
        return ["", f"Tidak ada pesanan web lain dari IP ini dalam {WINDOW_DAYS} hari terakhir."]
    head = f"Pesanan web lain dari IP ini ({WINDOW_DAYS} hari): {total}, {phones} nomor WA berbeda"
    lines = ["", head, *(_order_line(o) for o in rows)]
    if total > len(rows):
        lines.append(f"…dan {total - len(rows)} lainnya.")
    return lines


def lookup(query):
    q = str(query or "").strip()
    if not q:
        return USAGE

    ip = ci._valid_ip(q)
    if ip:
        latest = Order.objects.filter(source="web", client_ip=ip).order_by("-created_at").first()
        if not latest:
            return f"Tidak ada pesanan web dari IP {ip}."
        lines = [f"🔎 Jejak IP {ip}", *_block(latest), *_others_lines(ip)]
        return "\n".join(lines)

    order = _find_order(q)
    if not order:
        return f"Pesanan “{q[:40]}” tidak ditemukan.\n\n{USAGE}"
    lines = [
        f"🔎 Jejak {order.order_number}",
        f"Nama: {order.customer_name or '-'} · WA: {order.customer_phone or '-'}",
        f"Status: {_status_label(order)} · {_when(order.created_at)} WIB · {ui.rp(order.total_price)}",
        *_block(order),
    ]
    if order.client_ip:
        lines += _others_lines(order.client_ip, exclude_pk=order.pk)
    return "\n".join(lines)
