"""
Tampilan pesan Telegram untuk order (MURNI: tanpa Django/DB, bisa dites dengan Python biasa).

Satu "view" order (dict sederhana, dirakit notify.order_view) menentukan:
  - teks pesan   -> render_text(view)
  - tombol       -> render_keyboard(view), reject_keyboard(order_id)
  - data tombol  -> build_callback / parse_callback (maks 64 byte, batas Telegram)

Kunci view yang dipakai (semua opsional kecuali id):
  id, order_number, customer_name, customer_phone, lines[list teks item], total, status,
  payment_status, payment_method, source, service_type, table_number, notes,
  awaiting, tracks_readiness, is_ready, ready_manual, confirm_minutes, minutes_left,
  cancel_reason, cancel_note, cancelled_by, last_event{label,actor,channel_label},
  banner ('reminder'), admin_url,
  client{ip,city,region,country,country_label,device,maps_url,distance_km,customer_tag,risk}, client_flags[list teks],
  can_block (bool), blocked{phone,ip} (bool)
"""
from urllib.parse import quote

PREFIX = "ao"

ACT_ACCEPT = "acc"
ACT_REJECT = "rjc"        # buka menu alasan
ACT_REJECT_DO = "rjd"     # tolak dengan alasan (arg = kode alasan)
ACT_READY = "rdy"
ACT_UNREADY = "unr"
ACT_REFRESH = "ref"       # tampilkan ulang status terbaru / kembali dari menu alasan
ACT_BLOCK = "blk"         # blokir nomor WA + IP pemesan
ACT_UNBLOCK = "unb"       # buka blokir
ACTIONS = {ACT_ACCEPT, ACT_REJECT, ACT_REJECT_DO, ACT_READY, ACT_UNREADY, ACT_REFRESH, ACT_BLOCK, ACT_UNBLOCK}

RISK_LABELS = {"green": "🟢 AMAN", "yellow": "🟡 PERIKSA", "red": "🔴 CURIGA"}

# Urutan = urutan tampil di tombol.
REASON_LABELS = {
    "out_of_stock": "Stok habis",
    "customer_cancel": "Pelanggan batal",
    "wrong_input": "Salah input",
    "other": "Lainnya",
}

S_AWAITING = "awaiting"
S_PROCESSING = "processing"
S_READY = "ready"
S_DONE = "done"
S_CANCELLED = "cancelled"

MAX_CALLBACK_BYTES = 64


# ── Data tombol ─────────────────────────────────────────────────────────────

def build_callback(act, order_id, arg=None):
    if act not in ACTIONS:
        raise ValueError(f"aksi tidak dikenal: {act}")
    data = f"{PREFIX}:{act}:{int(order_id)}" + (f":{arg}" if arg else "")
    if len(data.encode()) > MAX_CALLBACK_BYTES:
        raise ValueError("callback_data terlalu panjang")
    return data


def parse_callback(data):
    """('acc', 12, None) / ('rjd', 7, 'out_of_stock'), atau None kalau bukan data kita / rusak."""
    if not isinstance(data, str) or len(data.encode()) > MAX_CALLBACK_BYTES:
        return None
    parts = data.split(":")
    if len(parts) not in (3, 4) or parts[0] != PREFIX:
        return None
    act, raw_id = parts[1], parts[2]
    if act not in ACTIONS or not raw_id.isdigit() or int(raw_id) <= 0:
        return None
    arg = parts[3] if len(parts) == 4 else None
    if act == ACT_REJECT_DO:
        if arg not in REASON_LABELS:
            return None
    elif arg is not None:
        return None
    return act, int(raw_id), arg


# ── Util ────────────────────────────────────────────────────────────────────

def rp(n):
    return "Rp " + f"{int(round(float(n or 0))):,}".replace(",", ".")


def wa_digits(phone):
    digits = "".join(ch for ch in str(phone or "") if ch.isdigit())
    if not digits:
        return ""
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    return digits


def wa_link(phone, text=None):
    digits = wa_digits(phone)
    if not digits:
        return ""
    url = f"https://wa.me/{digits}"
    if text:
        url += "?text=" + quote(text, safe="")
    return url


def first_name(name):
    parts = str(name or "").strip().split()
    return parts[0] if parts else "Kak"


def state_of(v):
    if v.get("status") == "cancelled" or v.get("payment_status") == "void":
        return S_CANCELLED
    if v.get("awaiting"):
        return S_AWAITING
    if v.get("tracks_readiness"):
        return S_READY if v.get("is_ready") else S_PROCESSING
    return S_DONE


def can_cancel(v):
    return state_of(v) in (S_AWAITING, S_PROCESSING, S_READY) and v.get("status") not in ("completed", "cancelled")


def is_paid(v):
    return v.get("payment_status") == "paid"


# ── Pesan WhatsApp siap kirim (dibuka dari tombol, staff tinggal tekan kirim) ─

def wa_message(kind, v):
    nama = first_name(v.get("customer_name"))
    no = v.get("order_number") or f"#{v.get('id')}"
    if kind == "accepted":
        return f"Halo {nama}, pesanan {no} sudah kami terima dan sedang disiapkan. Terima kasih 🙏"
    if kind == "ready":
        return f"Halo {nama}, pesanan {no} sudah siap diambil. Silakan ke kasir ya 🙏"
    if kind == "confirm":
        return f"Halo {nama}, kami dari Masashimura. Mau konfirmasi pesanan {no}, benar Kakak yang pesan? Balas OK ya 🙏"
    reason = v.get("cancel_reason")
    alasan = {
        "out_of_stock": "karena stok menu habis",
        "customer_cancel": "sesuai permintaan Kakak",
    }.get(reason, "karena ada kendala")
    return f"Halo {nama}, mohon maaf pesanan {no} kami batalkan {alasan}. Silakan pesan lagi kapan saja ya 🙏"


# ── Teks ────────────────────────────────────────────────────────────────────

def _headline(v, state):
    if v.get("banner") == "reminder" and state == S_AWAITING:
        risk = ((v.get("client") or {}).get("risk"))
        prefix = f"{RISK_LABELS[risk]} · " if risk in RISK_LABELS else ""
        return f"{prefix}⏰ SEGERA TERIMA — sisa ±{v.get('minutes_left') or '?'} menit"
    if state == S_AWAITING:
        risk = ((v.get("client") or {}).get("risk"))
        prefix = f"{RISK_LABELS[risk]} · " if risk in RISK_LABELS else ""
        return f"{prefix}🛎️ PESANAN WEB BARU (bayar di toko)"
    if state == S_PROCESSING:
        return "✅ PESANAN WEB LUNAS (QRIS)" if is_paid(v) and v.get("payment_method") == "gateway" else "🍳 SEDANG DISIAPKAN"
    if state == S_READY:
        return "🍽 SIAP DIAMBIL"
    if state == S_DONE:
        return "✅ SELESAI"
    return "⌛ DIBATALKAN OTOMATIS" if v.get("cancelled_by") == "sistem" else "❌ DIBATALKAN"


def _footer(v, state):
    if state == S_AWAITING:
        left = v.get("minutes_left")
        if left is not None:
            return f"⏱ Terima dalam {max(int(left), 0)} menit, kalau tidak dibatalkan otomatis."
        return f"⏱ Terima dalam {v.get('confirm_minutes') or 15} menit, kalau tidak dibatalkan otomatis."
    if state == S_PROCESSING:
        return "Tekan Siap diambil kalau pesanan sudah jadi."
    if state == S_READY:
        return "Pesanan siap. Kabari pemesan lewat WA kalau perlu."
    if state == S_CANCELLED:
        if v.get("cancelled_by") == "sistem":
            return f"Tidak diterima kasir dalam {v.get('confirm_minutes') or 15} menit."
        label = REASON_LABELS.get(v.get("cancel_reason"), "")
        note = (v.get("cancel_note") or "").strip()
        out = f"Alasan: {label}" if label else "Dibatalkan"
        return f"{out} ({note})" if note else out
    return ""


def client_lines(v):
    """Blok 'Asal pemesan' (IP, lokasi perkiraan, perangkat, tanda mencurigakan). Kosong untuk order POS/lama."""
    c = v.get("client")
    if not c:
        return []
    lines = ["", "🌐 Asal pemesan (perkiraan)", f"IP: {c.get('ip') or 'tidak terbaca'}"]
    blocked = v.get("blocked") or {}
    if blocked.get("phone") or blocked.get("ip"):
        what = " & ".join(n for n, on in (("nomor WA", blocked.get("phone")), ("IP", blocked.get("ip"))) if on)
        lines.insert(2, f"🚫 DIBLOKIR: {what}")
    place = ", ".join(p for p in (c.get("city"), c.get("region")) if p)
    where = " ".join(p for p in (place, c.get("country_label")) if p)
    if where:
        lines.append(f"📍 {where}")
    if c.get("distance_km") is not None:
        lines.append(f"📏 ±{round(c['distance_km'])} km dari toko")
    if c.get("device"):
        lines.append(f"📱 {c['device']}")
    if c.get("customer_tag"):
        lines.append(f"👤 {c['customer_tag']}")
    if c.get("maps_url"):
        lines.append(f"🗺 {c['maps_url']}")
    flags = v.get("client_flags") or []
    if flags:
        lines.append("🚩 Perhatikan:")
        lines += [f"• {f}" for f in flags]
    else:
        lines.append("✅ Tidak ada tanda janggal terdeteksi")
    if c.get("risk") in RISK_LABELS:
        lines.append(f"Penilaian: {RISK_LABELS[c['risk']]}")
    return lines


def render_text(v):
    state = state_of(v)
    lines = [
        _headline(v, state),
        f"No. {v.get('order_number') or '#' + str(v.get('id'))}",
        f"Nama: {v.get('customer_name') or '-'}",
        f"WA: {v.get('customer_phone') or '-'}",
    ]
    svc = "Bungkus" if v.get("service_type") == "takeaway" else "Makan di tempat"
    if v.get("service_type") != "takeaway" and v.get("table_number"):
        svc += f" · Meja {v['table_number']}"
    lines.append(f"Jenis: {svc}")
    lines += ["", *(v.get("lines") or [])]
    notes = (v.get("notes") or "").strip()
    if notes:
        lines.append(f"Catatan: {notes[:200]}")
    lines += ["", f"Total: {rp(v.get('total'))}"]
    footer = _footer(v, state)
    if footer:
        lines.append(footer)
    lines += client_lines(v)
    last = v.get("last_event")
    if last and last.get("label"):
        who = f" · {last['actor']}" if last.get("actor") else ""
        via = f" · {last['channel_label']}" if last.get("channel_label") else ""
        lines.append(f"↳ {last['label']}{who}{via}")
    return "\n".join(lines)


# ── Tombol ──────────────────────────────────────────────────────────────────

def _cb(text, act, order_id, arg=None):
    return {"text": text, "callback_data": build_callback(act, order_id, arg)}


def render_keyboard(v):
    oid = v["id"]
    state = state_of(v)
    rows = []

    if state == S_AWAITING:
        rows.append([_cb("✅ Terima", ACT_ACCEPT, oid), _cb("❌ Tolak", ACT_REJECT, oid)])
    elif state == S_PROCESSING:
        rows.append([_cb("🍽 Siap diambil", ACT_READY, oid)])
        if can_cancel(v):
            rows[-1].append(_cb("❌ Batalkan", ACT_REJECT, oid))
    elif state == S_READY:
        if v.get("ready_manual"):
            rows.append([_cb("↩ Cabut tanda siap", ACT_UNREADY, oid)])
        if can_cancel(v):
            rows.append([_cb("❌ Batalkan", ACT_REJECT, oid)])

    links = []
    if v.get("admin_url"):
        links.append({"text": "Buka Active Orders", "url": v["admin_url"]})
    kind = {S_PROCESSING: "accepted", S_READY: "ready", S_CANCELLED: "cancelled"}.get(state)
    label = {"accepted": "💬 Kabari: diterima", "ready": "💬 Kabari: siap", "cancelled": "💬 Kabari: dibatalkan"}.get(kind)
    risky = state == S_AWAITING and (v.get("client") or {}).get("risk") in ("yellow", "red")
    if risky:   # order mencurigakan: kirim satu pesan konfirmasi dulu, terima hanya kalau dibalas
        kind, label = "confirm", "💬 Konfirmasi dulu (WA)"
    wa = wa_link(v.get("customer_phone"), wa_message(kind, v) if kind else None)
    if wa:
        links.append({"text": label or "💬 Chat pemesan (WA)", "url": wa})
    if links:
        rows.append(links)
    if v.get("can_block"):
        blocked = v.get("blocked") or {}
        if blocked.get("phone") or blocked.get("ip"):
            rows.append([_cb("♻ Buka blokir", ACT_UNBLOCK, oid)])
        else:
            rows.append([_cb("🚫 Blokir nomor & IP", ACT_BLOCK, oid)])
    return rows


def reject_keyboard(order_id):
    items = list(REASON_LABELS.items())
    rows = []
    for i in range(0, len(items), 2):
        rows.append([_cb(label, ACT_REJECT_DO, order_id, code) for code, label in items[i:i + 2]])
    rows.append([_cb("⬅ Kembali", ACT_REFRESH, order_id)])
    return rows


def reject_prompt(v):
    return render_text(v) + "\n\n❓ Pilih alasan menolak/membatalkan:"


# ── Perintah bot ────────────────────────────────────────────────────────────

HELP_TEXT = (
    "Perintah bot Masashimura:\n"
    "/antrean — order yang perlu tindakan sekarang\n"
    "/ringkasan — ringkasan hari ini\n"
    "/lacak — asal pemesan: /lacak MSM-261027-AB12, /lacak 114.122.1.2, atau /lacak 0812xxxx (nomor WA)\n"
    "/percobaan — yang mencoba memesan padahal sudah diblokir (7 hari)\n"
    "/blokir 0812xxxx — nomor ditolak total (atau IP: dipaksa QRIS)\n"
    "/bukablokir 0812xxxx — buka blokir nomor/IP\n"
    "/daftarblokir — yang sedang diblokir\n"
    "/bantuan — pesan ini\n\n"
    "Tombol di tiap pesan order: Terima, Tolak, Siap diambil, Blokir."
)


def render_queue(items, limit=12):
    """items: list dict {id, order_number, customer_name, tag, minutes}; urut prioritas dari pemanggil."""
    if not items:
        return "✅ Tidak ada order yang perlu tindakan. Semua beres."
    lines = [f"📋 Perlu tindakan ({len(items)}):"]
    for it in items[:limit]:
        mins = f" · {it['minutes']} mnt" if it.get("minutes") is not None else ""
        lines.append(f"• {it.get('tag', '')} {it.get('order_number') or '#' + str(it['id'])} — {it.get('customer_name') or 'Guest'}{mins}")
    if len(items) > limit:
        lines.append(f"…dan {len(items) - limit} lainnya. Buka Active Orders.")
    return "\n".join(lines)
