"""
Format teks ringkasan harian untuk Telegram (MURNI: tanpa Django/DB, bisa dites dengan Python biasa).

Masukan = dict hasil staff_summary.build_summary(). Kalau kunci uang bernilai None (peran kasir),
baris uang disembunyikan, jadi satu formatter melayani semua peran.
"""

BAR_FULL = "▇"
MAX_BAR = 8
MAX_HOUR_ROWS = 12


def rp(n):
    return "Rp " + f"{int(round(float(n or 0))):,}".replace(",", ".")


def minutes_text(m):
    if m is None:
        return "-"
    m = float(m)
    if m < 1:
        return "<1 mnt"
    if m >= 90:
        return f"{m / 60:.1f} jam"
    return f"{round(m)} mnt"


def delta_text(now, before):
    """'↑ 12%' / '↓ 8%' / '= sama'. None kalau pembanding kosong (tidak bisa dihitung)."""
    if before is None or before == 0:
        return None
    pct = round((now - before) / before * 100)
    if pct == 0:
        return "= sama"
    return f"{'↑' if pct > 0 else '↓'} {abs(pct)}%"


def hour_label(h):
    return f"{int(h):02d}.00"


def _bars(busy):
    rows = [b for b in busy if b.get("orders")][:MAX_HOUR_ROWS * 3]
    if not rows:
        return []
    top = max(b["orders"] for b in rows)
    out = []
    for b in rows[:MAX_HOUR_ROWS]:
        n = max(1, round(b["orders"] / top * MAX_BAR))
        out.append(f"{hour_label(b['hour'])} {BAR_FULL * n} {b['orders']}")
    return out


def format_daily_report(s):
    t = s.get("today") or {}
    q = s.get("queue") or {}
    cmp_ = s.get("compare") or {}
    lines = [f"📊 RINGKASAN {s.get('date_label', '')}".strip(), ""]

    # Ringkas order
    lines.append(f"🧾 Order: {t.get('orders', 0)} (Web {t.get('web', 0)} · POS {t.get('pos', 0)})")
    lines.append(f"   Makan di tempat {t.get('dine_in', 0)} · Bungkus {t.get('takeaway', 0)}")
    if t.get("revenue") is not None:
        lines.append(f"💰 Omzet: {rp(t['revenue'])}" + (f" · rata-rata {rp(t['avg_order'])}/order" if t.get("avg_order") else ""))
    if t.get("items_sold") is not None:
        lines.append(f"🍽 Porsi terjual: {t['items_sold']}")

    # Pembanding
    if cmp_.get("label"):
        bits = []
        d_orders = delta_text(t.get("orders", 0), cmp_.get("orders"))
        if d_orders:
            bits.append(f"order {d_orders}")
        if t.get("revenue") is not None and cmp_.get("revenue") is not None:
            d_rev = delta_text(t["revenue"], cmp_["revenue"])
            if d_rev:
                bits.append(f"omzet {d_rev}")
        if bits:
            lines.append(f"↔ Dibanding {cmp_['label']}: " + ", ".join(bits))

    # Pembatalan
    if t.get("cancelled"):
        reasons = ", ".join(f"{k} {v}" for k, v in (t.get("cancel_reasons") or {}).items())
        auto = f" ({t['auto_cancelled']} otomatis)" if t.get("auto_cancelled") else ""
        lines.append(f"❌ Dibatalkan: {t['cancelled']}{auto}" + (f" — {reasons}" if reasons else ""))

    # Layanan
    sv = s.get("service") or {}
    if sv.get("avg_accept_minutes") is not None or sv.get("avg_ready_minutes") is not None:
        lines += ["", "⏱ Kecepatan layanan (order web)"]
        if sv.get("avg_accept_minutes") is not None:
            lines.append(f"• Rata-rata sampai diterima: {minutes_text(sv['avg_accept_minutes'])}")
        if sv.get("avg_ready_minutes") is not None:
            lines.append(f"• Rata-rata sampai siap: {minutes_text(sv['avg_ready_minutes'])}")

    # Jam sibuk
    bars = _bars(s.get("busy_hours") or [])
    if bars:
        lines += ["", "🕒 Jam sibuk"]
        lines += bars
        if s.get("peak_hour") is not None:
            lines.append(f"Puncak: {hour_label(s['peak_hour'])}")

    # Menu terlaris
    tops = s.get("top_menus") or []
    if tops:
        lines += ["", "🏆 Menu terlaris"]
        lines += [f"{i}. {m['name']} — {m['qty']}" for i, m in enumerate(tops[:5], 1)]

    # Staff
    staff = s.get("staff") or []
    if staff:
        lines += ["", "👥 Aksi staff"]
        for st in staff[:6]:
            parts = []
            if st.get("accepted"):
                parts.append(f"terima {st['accepted']}")
            if st.get("ready"):
                parts.append(f"siap {st['ready']}")
            if st.get("cancelled"):
                parts.append(f"batal {st['cancelled']}")
            if parts:
                lines.append(f"• {st['actor']}: " + ", ".join(parts))

    # Sisa pekerjaan
    todo = []
    if q.get("awaiting"):
        todo.append(f"{q['awaiting']} menunggu diterima")
    if q.get("late"):
        todo.append(f"{q['late']} telat")
    if q.get("unpaid"):
        extra = f" ({rp(q['unpaid_total'])})" if q.get("unpaid_total") is not None else ""
        todo.append(f"{q['unpaid']} belum dibayar{extra}")
    if q.get("refunds"):
        todo.append(f"{q['refunds']} refund belum diserahkan")
    lines += ["", ("⚠️ Belum beres: " + ", ".join(todo)) if todo else "✅ Tidak ada tagihan atau antrean tertinggal."]
    return "\n".join(lines)
