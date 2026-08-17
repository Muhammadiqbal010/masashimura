"""
finance_pdf.py  —  v2.0
=======================
Ekspor laporan keuangan Masashimura ke PDF.

REVISI v2.0
-----------
1. Cover  : layout kotak fitur diperbaiki, tidak tumpang-tindih
2. Detail : bulanan → total pendapatan per HARI | tahunan → per BULAN
3. Pengeluaran : bulanan → total pengeluaran per HARI | tahunan → per BULAN
4. Kategori : auto-detect dari kata kunci deskripsi
5. Rekap per kategori : menggunakan hasil auto-detect kategori
6. Catatan & Keterangan : diganti "KETERANGAN PERFORMA" — diisi otomatis
   dengan narasi + bullet-point berdasarkan data real.

Halaman:
  Hal 1  — Cover
  Hal 2  — Ringkasan KPI + Tabel Target vs Aktual
  Hal 3  — Rekap Pendapatan (per hari / per bulan)
  Hal 4  — Rekap Pengeluaran (per hari / per bulan)
  Hal 5  — Top Menu Terlaris
  Hal 6  — Rekap Pengeluaran per Kategori + Keterangan Performa + TTD
"""

import calendar
import io
import os
from collections import defaultdict
from datetime import date

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.http import HttpResponse
from django.utils import timezone

from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from finance.models import Expense
from .models import Order, OrderItem

# ─────────────────────────────────────────────────────────────────────────────
# PATH LOGO
# ─────────────────────────────────────────────────────────────────────────────
try:
    from django.conf import settings
    LOGO_PATH = getattr(
        settings,
        "EXCEL_LOGO_PATH",
        os.path.join(settings.BASE_DIR, "assets", "masashimura-logo.png"),
    )
except Exception:
    LOGO_PATH = "assets/masashimura-logo.png"

# ─────────────────────────────────────────────────────────────────────────────
# WARNA BRAND
# ─────────────────────────────────────────────────────────────────────────────
C_RED    = HexColor("#CC0000")
C_YELLOW = HexColor("#FFD700")
C_DARK   = HexColor("#1A1A1A")
C_WHITE  = white
C_GRAY   = HexColor("#F5F5F5")
C_GRAY2  = HexColor("#E8E8E8")
C_FOOT   = HexColor("#888888")
C_GREEN  = HexColor("#16A34A")
C_ORANGE = HexColor("#D97706")
C_BLUE   = HexColor("#2563EB")
C_PURPLE = HexColor("#7C3AED")
C_ROWTOP = HexColor("#1F2937")

C_LUNAS   = HexColor("#DCFCE7")
C_PENDING = HexColor("#FEF9C3")
C_BATAL   = HexColor("#FEE2E2")

# ─────────────────────────────────────────────────────────────────────────────
# UKURAN HALAMAN
# ─────────────────────────────────────────────────────────────────────────────
W, H   = A4
MARGIN  = 1.2 * cm
TOP_BAR = 32
BOT_BAR = 22

# ─────────────────────────────────────────────────────────────────────────────
# NAMA BULAN
# ─────────────────────────────────────────────────────────────────────────────
BULAN_ID = {
    1: "Januari",  2: "Februari", 3: "Maret",     4: "April",
    5: "Mei",      6: "Juni",     7: "Juli",       8: "Agustus",
    9: "September",10: "Oktober", 11: "November",  12: "Desember",
}

# ─────────────────────────────────────────────────────────────────────────────
# AUTO-DETECT KATEGORI DARI KATA KUNCI
# ─────────────────────────────────────────────────────────────────────────────
CATEGORY_KEYWORDS = {
    "Bahan Baku": [
        "bahan", "baku", "belanja", "pasar", "sayur", "daging", "ayam",
        "ikan", "telur", "bumbu", "minyak", "tepung", "gula", "garam",
        "beras", "tahu", "tempe", "santan", "susu", "keju",
    ],
    "Karyawan": [
        "gaji", "karyawan", "upah", "thr", "bonus", "honor", "lembur",
        "salary", "pegawai", "staf", "staff",
    ],
    "Marketing": [
        "marketing", "iklan", "promosi", "spanduk", "banner", "sosmed",
        "ads", "endorse", "foto", "konten", "flyer", "brosur",
    ],
    "Operasional": [
        "listrik", "air", "pam", "gas", "sewa", "rent", "internet",
        "wifi", "telpon", "telepon", "perbaikan", "servis", "cuci",
        "sabun", "detergen", "tisu", "plastik", "kemasan", "packaging",
        "bensin", "bbm", "parkir", "transportasi", "ojek", "ekspedisi",
        "pajak", "iuran", "kebersihan", "sampah",
    ],
}


def _auto_category(description: str) -> str:
    """Deteksi kategori dari deskripsi; fallback ke 'Lainnya'."""
    if not description:
        return "Lainnya"
    desc_lower = description.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            return cat
    return "Lainnya"


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _rp(value) -> str:
    return f"Rp {int(value or 0):,}".replace(",", ".")


def _fmt_tanggal_id(dt) -> str:
    return f"{dt.day} {BULAN_ID[dt.month]} {dt.year}"


def _build_filename(mode: str, month, year: int) -> str:
    if mode == "monthly" and month:
        return f"Rekap Finance Masashimura {BULAN_ID[month]} {year}.pdf"
    return f"Rekap Finance Masashimura Tahun {year}.pdf"


def _load_logo(target_w_pt: int) -> ImageReader | None:
    if not os.path.isfile(LOGO_PATH):
        return None
    try:
        from PIL import Image as PILImage
        pil = PILImage.open(LOGO_PATH).convert("RGBA")
        w0, h0 = pil.size
        target_h = max(1, int(h0 * target_w_pt / w0))
        pil = pil.resize((target_w_pt, target_h), PILImage.LANCZOS)
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        buf.seek(0)
        return ImageReader(buf)
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────────────────────────────────────

def _build_styles():
    base = getSampleStyleSheet()
    return {
        "section_title": ParagraphStyle(
            "SectionTitle", fontSize=12, fontName="Helvetica-Bold",
            textColor=C_WHITE, leading=16),
        "section_sub": ParagraphStyle(
            "SectionSub", fontSize=8, fontName="Helvetica",
            textColor=C_YELLOW, leading=12),
        "kpi_label": ParagraphStyle(
            "KPILabel", fontSize=8, fontName="Helvetica",
            textColor=HexColor("#555555"), leading=11),
        "kpi_value": ParagraphStyle(
            "KPIValue", fontSize=16, fontName="Helvetica-Bold",
            textColor=C_DARK, leading=20),
        "table_header": ParagraphStyle(
            "TableHeader", fontSize=8, fontName="Helvetica-Bold",
            textColor=C_YELLOW, leading=10, alignment=TA_CENTER),
        "table_cell": ParagraphStyle(
            "TableCell", fontSize=7.5, fontName="Helvetica",
            textColor=C_DARK, leading=10),
        "table_cell_r": ParagraphStyle(
            "TableCellR", fontSize=7.5, fontName="Helvetica",
            textColor=C_DARK, leading=10, alignment=TA_RIGHT),
        "table_total": ParagraphStyle(
            "TableTotal", fontSize=8, fontName="Helvetica-Bold",
            textColor=C_WHITE, leading=10, alignment=TA_RIGHT),
        "cat_label": ParagraphStyle(
            "CatLabel", fontSize=8, fontName="Helvetica-Bold",
            textColor=C_DARK, leading=11),
        "note_text": ParagraphStyle(
            "NoteText", fontSize=8.5, fontName="Helvetica-Oblique",
            textColor=HexColor("#999999"), leading=13),
        "sign_label": ParagraphStyle(
            "SignLabel", fontSize=8, fontName="Helvetica-Bold",
            textColor=C_DARK, leading=11),
        "sign_sub": ParagraphStyle(
            "SignSub", fontSize=7.5, fontName="Helvetica",
            textColor=HexColor("#777777"), leading=10),
        "sign_name": ParagraphStyle(
            "SignName", fontSize=8, fontName="Helvetica",
            textColor=C_DARK, leading=11, alignment=TA_CENTER),
        "normal": base["Normal"],
        "narasi": ParagraphStyle(
            "Narasi", fontSize=8.5, fontName="Helvetica",
            textColor=C_DARK, leading=14),
        "narasi_bold": ParagraphStyle(
            "NarasiBold", fontSize=8.5, fontName="Helvetica-Bold",
            textColor=C_DARK, leading=14),
        "bullet": ParagraphStyle(
            "Bullet", fontSize=8, fontName="Helvetica",
            textColor=C_DARK, leading=13, leftIndent=10),
    }


# ─────────────────────────────────────────────────────────────────────────────
# HEADER & FOOTER
# ─────────────────────────────────────────────────────────────────────────────

class _PageFrame:
    def __init__(self, logo_ir, period_label, generated_at):
        self.logo_ir      = logo_ir
        self.period_label = period_label
        self.generated_at = generated_at

    def __call__(self, canv, doc):
        canv.saveState()

        canv.setFillColor(C_RED)
        canv.rect(0, H - TOP_BAR, W, TOP_BAR, fill=1, stroke=0)
        canv.setFillColor(C_YELLOW)
        canv.rect(0, H - TOP_BAR - 4, W, 4, fill=1, stroke=0)

        if self.logo_ir:
            canv.drawImage(self.logo_ir, MARGIN, H - TOP_BAR + 4,
                           width=80, height=22, mask="auto")
        else:
            canv.setFillColor(C_YELLOW)
            canv.setFont("Helvetica-Bold", 9)
            canv.drawString(MARGIN, H - TOP_BAR + 10, "MASASHIMURA")

        canv.setFillColor(C_YELLOW)
        canv.setFont("Helvetica-Bold", 7.5)
        canv.drawRightString(W - MARGIN, H - TOP_BAR + 10,
                             f"LAPORAN KEUANGAN  ·  TEMPLATE OPERASIONAL")

        canv.setFillColor(C_GRAY)
        canv.rect(0, 0, W, BOT_BAR, fill=1, stroke=0)
        canv.setFillColor(C_FOOT)
        canv.setFont("Helvetica", 7)
        canv.drawString(MARGIN, 7, "© 2026 Masashimura — Laporan Keuangan")
        canv.drawRightString(W - MARGIN, 7, f"Halaman {canv.getPageNumber()}")

        canv.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# SECTION HEADER
# ─────────────────────────────────────────────────────────────────────────────

def _section_header(title, subtitle, styles):
    cell_title    = Paragraph(f"<b>■  {title}</b>", styles["section_title"])
    cell_subtitle = Paragraph(subtitle, styles["section_sub"])
    t = Table([[cell_title, cell_subtitle]], colWidths=[None, 6 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_RED),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (0, 0),   8),
        ("RIGHTPADDING",  (1, 0), (1, 0),   8),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (1, 0), (1, 0),   "RIGHT"),
    ]))
    return t


def _yellow_rule():
    t = Table([[""]], colWidths=[W - 2 * MARGIN], rowHeights=[4])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_YELLOW),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _apply_table_style(tbl, n_rows):
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), C_ROWTOP),
        ("GRID",          (0, 0), (-1, -1), 0.3, HexColor("#CCCCCC")),
        ("LINEBELOW",     (0, 0), (-1, 0), 0.8, C_YELLOW),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_WHITE, C_GRAY2]),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))


# ─────────────────────────────────────────────────────────────────────────────
# HAL 1 — COVER  (FIX: layout 4 fitur tidak tumpang tindih)
# ─────────────────────────────────────────────────────────────────────────────

def _build_cover_page(canv, period_label, generated_at, logo_ir):
    canv.saveState()

    # Background
    canv.setFillColor(C_DARK)
    canv.rect(0, 0, W, H, fill=1, stroke=0)

    # Top bar
    canv.setFillColor(C_RED)
    canv.rect(0, H - TOP_BAR, W, TOP_BAR, fill=1, stroke=0)
    canv.setFillColor(C_YELLOW)
    canv.rect(0, H - TOP_BAR - 4, W, 4, fill=1, stroke=0)
    canv.setFillColor(C_YELLOW)
    canv.setFont("Helvetica-Bold", 9)
    canv.drawCentredString(W / 2, H - TOP_BAR + 10, "MASASHIMURA  ·  BEKASI")

    # Logo
    logo_w = 380
    if logo_ir:
        logo_h = int(logo_w / 4)
        canv.drawImage(logo_ir, (W - logo_w) / 2, H * 0.56,
                       width=logo_w, height=logo_h, mask="auto")
    else:
        canv.setFillColor(C_YELLOW)
        canv.setFont("Helvetica-Bold", 52)
        canv.drawCentredString(W / 2, H * 0.58, "MASASHIMURA")

    # Garis pemisah
    sep_y = H * 0.52
    canv.setStrokeColor(C_YELLOW)
    canv.setLineWidth(1.5)
    canv.line(MARGIN, sep_y, W - MARGIN, sep_y)

    # Judul
    canv.setFillColor(C_WHITE)
    canv.setFont("Helvetica-Bold", 26)
    canv.drawCentredString(W / 2, H * 0.465, "LAPORAN KEUANGAN")

    canv.setFillColor(C_YELLOW)
    canv.setFont("Helvetica-Bold", 13)
    canv.drawCentredString(W / 2, H * 0.425, period_label.upper())

    canv.setFillColor(HexColor("#AAAAAA"))
    canv.setFont("Helvetica", 9)
    canv.drawCentredString(W / 2, H * 0.395, f"Digenerate: {generated_at}")

    # ── Kotak fitur — FIX: 4 icon di baris atas, label di bawahnya ──────────
    feat_y = H * 0.255
    feat_h = 100
    feat_x = MARGIN
    feat_w = W - 2 * MARGIN

    canv.setStrokeColor(HexColor("#FFD70066"))
    canv.setLineWidth(1)
    canv.roundRect(feat_x, feat_y, feat_w, feat_h, 6, fill=0, stroke=1)

    # 4 fitur icon (baris atas kotak)
    labels = ["Ringkasan KPI", "Detail Transaksi", "Top Menu", "Pengeluaran"]
    col_w  = feat_w / 4
    icon_y  = feat_y + feat_h - 24
    label_y = icon_y - 14

    for i, label in enumerate(labels):
        cx = feat_x + col_w * i + col_w / 2
        canv.setFont("Helvetica-Bold", 14)
        canv.setFillColor(C_YELLOW)
        canv.drawCentredString(cx, icon_y, "■")
        canv.setFont("Helvetica-Bold", 7.5)
        canv.setFillColor(C_WHITE)
        canv.drawCentredString(cx, label_y, label)

    # Garis pemisah dalam kotak
    div_y = feat_y + feat_h - 52
    canv.setStrokeColor(HexColor("#FFD70033"))
    canv.setLineWidth(0.5)
    canv.line(feat_x + 8, div_y, feat_x + feat_w - 8, div_y)

    # 3 bullet info (baris bawah kotak)
    bullets = [
        ("■ Filter Periode",  "Bulanan  ·  Tahunan  ·  Custom Range"),
        ("■ Auto-Hitung",     "Pendapatan  ·  Diskon  ·  Laba  ·  KPI"),
        ("■ Color-Coded",     "Lunas = Hijau  ·  Pending = Kuning  ·  Batal = Merah"),
    ]
    by = div_y - 10
    for key, val in bullets:
        canv.setFont("Helvetica-Bold", 7)
        canv.setFillColor(C_YELLOW)
        canv.drawString(feat_x + 12, by, key)
        canv.setFont("Helvetica", 7)
        canv.setFillColor(HexColor("#CCCCCC"))
        canv.drawString(feat_x + 115, by, val)
        by -= 13

    # Footer
    canv.setFillColor(C_YELLOW)
    canv.rect(0, 0, W, 28, fill=1, stroke=0)
    canv.setFillColor(C_DARK)
    canv.setFont("Helvetica-Bold", 8)
    canv.drawCentredString(W / 2, 10,
                           "v2.0  ·  © 2026 Masashimura  ·  Laporan Keuangan")

    canv.restoreState()
    canv.showPage()


# ─────────────────────────────────────────────────────────────────────────────
# HAL 2 — RINGKASAN KPI
# ─────────────────────────────────────────────────────────────────────────────

def _page_ringkasan(story, orders_qs, expenses_qs, period_label, styles):
    total_revenue  = float(orders_qs.filter(payment_status="paid")
                           .aggregate(t=Sum("total_price"))["t"] or 0)
    total_discount = float(orders_qs.aggregate(t=Sum("discount_amount"))["t"] or 0)
    total_expense  = float(expenses_qs.aggregate(t=Sum("amount"))["t"] or 0)
    total_trx      = orders_qs.count()
    avg_trx        = total_revenue / total_trx if total_trx else 0
    net_profit     = total_revenue - total_expense

    story.append(_section_header("RINGKASAN KPI", f"Periode: {period_label}", styles))
    story.append(_yellow_rule())
    story.append(Spacer(1, 10))

    kpis = [
        ("■  Total Pendapatan (Lunas)", _rp(total_revenue),  C_RED),
        ("■■  Total Diskon Diberikan",  _rp(total_discount), C_ORANGE),
        ("■  Total Pengeluaran",        _rp(total_expense),  C_RED),
        ("■  Laba Bersih",              _rp(net_profit),     C_GREEN),
        ("■  Jumlah Transaksi",         f"{total_trx} transaksi", C_BLUE),
        ("■  Rata-rata per Transaksi",  _rp(avg_trx),        C_PURPLE),
    ]

    usable_w = W - 2 * MARGIN
    card_w   = (usable_w - 8) / 3

    for row_kpis in [kpis[0:3], kpis[3:6]]:
        cells = []
        for label, value, accent_color in row_kpis:
            lbl = Paragraph(label, styles["kpi_label"])
            val = Paragraph(f"<b>{value}</b>", styles["kpi_value"])
            inner = Table([[lbl], [val]], colWidths=[card_w - 24])
            inner.setStyle(TableStyle([
                ("TOPPADDING",    (0,0),(-1,-1), 4),
                ("BOTTOMPADDING", (0,0),(-1,-1), 4),
                ("LEFTPADDING",   (0,0),(-1,-1), 0),
                ("RIGHTPADDING",  (0,0),(-1,-1), 0),
            ]))
            wrapper = Table([[inner]], colWidths=[card_w])
            wrapper.setStyle(TableStyle([
                ("BOX",           (0,0),(-1,-1), 0.5, HexColor("#DDDDDD")),
                ("BACKGROUND",    (0,0),(-1,-1), C_GRAY),
                ("LINEAFTER",     (0,0),(0,0), 4, accent_color),
                ("TOPPADDING",    (0,0),(-1,-1), 8),
                ("BOTTOMPADDING", (0,0),(-1,-1), 8),
                ("LEFTPADDING",   (0,0),(-1,-1), 10),
                ("RIGHTPADDING",  (0,0),(-1,-1), 8),
            ]))
            cells.append(wrapper)

        row_tbl = Table([cells], colWidths=[card_w]*3, hAlign="LEFT")
        row_tbl.setStyle(TableStyle([
            ("LEFTPADDING",   (0,0),(-1,-1), 0),
            ("RIGHTPADDING",  (0,0),(-1,-1), 2),
            ("TOPPADDING",    (0,0),(-1,-1), 0),
            ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ]))
        story.append(row_tbl)

    story.append(Spacer(1, 12))

    # Tabel Target vs Aktual
    story.append(_section_header("TABEL TARGET VS AKTUAL",
                                 "Isi kolom Target sesuai rencana", styles))
    story.append(_yellow_rule())
    story.append(Spacer(1, 6))

    HR = ParagraphStyle("HR", fontSize=8, fontName="Helvetica-Bold",
                        textColor=C_YELLOW, alignment=TA_CENTER)
    CC = styles["table_cell"]
    CR = styles["table_cell_r"]

    tdata = [[Paragraph(h, HR) for h in
              ["METRIK", "NILAI AKTUAL (Rp)", "TARGET (Rp)", "vs TARGET", "STATUS"]]]
    metrics = [
        ("■  Total Pendapatan (Lunas)", _rp(total_revenue)),
        ("■■  Total Diskon",            _rp(total_discount)),
        ("■  Total Pengeluaran",        _rp(total_expense)),
        ("■  Laba Bersih",              _rp(net_profit)),
        ("■  Jumlah Transaksi",         str(total_trx)),
        ("■  Rata-rata per Transaksi",  _rp(avg_trx)),
    ]
    for lbl, val in metrics:
        tdata.append([Paragraph(lbl, CC), Paragraph(val, CR),
                      Paragraph("", CC), Paragraph("", CC), Paragraph("", CC)])

    cw = usable_w
    tbl = Table(tdata,
                colWidths=[cw*0.35, cw*0.18, cw*0.18, cw*0.14, cw*0.15],
                repeatRows=1)
    _apply_table_style(tbl, len(tdata))
    story.append(tbl)
    story.append(PageBreak())


# ─────────────────────────────────────────────────────────────────────────────
# HAL 3 — REKAP PENDAPATAN PER HARI / PER BULAN  (REVISI: tidak per transaksi)
# ─────────────────────────────────────────────────────────────────────────────

def _page_rekap_pendapatan(story, orders_qs, styles, mode, month, year):
    """
    Bulanan  → total pendapatan per hari (31 baris maks)
    Tahunan  → total pendapatan per bulan (12 baris)
    """
    if mode == "monthly":
        subtitle = f"Total Pendapatan per Hari — {BULAN_ID[month]} {year}"
    else:
        subtitle = f"Total Pendapatan per Bulan — Tahun {year}"

    story.append(_section_header("REKAP PENDAPATAN", subtitle, styles))
    story.append(_yellow_rule())
    story.append(Spacer(1, 6))

    usable_w = W - 2 * MARGIN
    HR = ParagraphStyle("PH", fontSize=8, fontName="Helvetica-Bold",
                        textColor=C_YELLOW, alignment=TA_CENTER)
    CC = styles["table_cell"]
    CR = styles["table_cell_r"]

    if mode == "monthly":
        days_in_month = calendar.monthrange(year, month)[1]

        # Aggregate per hari
        paid_orders = orders_qs.filter(payment_status="paid")
        daily_rev   = defaultdict(float)
        daily_trx   = defaultdict(int)
        for o in paid_orders:
            d = o.created_at.day
            daily_rev[d]  += float(o.total_price or 0)
            daily_trx[d]  += 1

        all_orders   = orders_qs
        daily_all    = defaultdict(int)
        for o in all_orders:
            daily_all[o.created_at.day] += 1

        col_widths = [usable_w*0.08, usable_w*0.22, usable_w*0.20,
                      usable_w*0.20, usable_w*0.15, usable_w*0.15]
        data = [[
            Paragraph("Hari", HR),
            Paragraph("Tanggal", HR),
            Paragraph("Total Pendapatan (Rp)", HR),
            Paragraph("Jumlah Transaksi Lunas", HR),
            Paragraph("Total Transaksi", HR),
            Paragraph("Ket", HR),
        ]]

        total_rev = 0.0
        total_lunas = 0
        total_all_trx = 0
        for day in range(1, days_in_month + 1):
            rev  = daily_rev.get(day, 0.0)
            lunas = daily_trx.get(day, 0)
            all_t = daily_all.get(day, 0)
            total_rev      += rev
            total_lunas    += lunas
            total_all_trx  += all_t

            tanggal_str = f"{day:02d} {BULAN_ID[month]} {year}"
            hari_name   = date(year, month, day).strftime("%A")
            hari_id     = {
                "Monday":"Senin","Tuesday":"Selasa","Wednesday":"Rabu",
                "Thursday":"Kamis","Friday":"Jumat","Saturday":"Sabtu",
                "Sunday":"Minggu"
            }.get(hari_name, hari_name)

            ket = "Ramai" if rev >= 500_000 else ("Sepi" if rev == 0 else "Normal")

            data.append([
                Paragraph(hari_id, CC),
                Paragraph(tanggal_str, CC),
                Paragraph(_rp(rev), CR),
                Paragraph(str(lunas), CR),
                Paragraph(str(all_t), CR),
                Paragraph(ket, CC),
            ])

        # Baris total
        ti = len(data)
        data.append([
            Paragraph("", CC),
            Paragraph("<b>TOTAL</b>",
                      ParagraphStyle("Tot", fontSize=8, fontName="Helvetica-Bold",
                                     textColor=C_YELLOW)),
            Paragraph(f"<b>{_rp(total_rev)}</b>",
                      ParagraphStyle("TotV", fontSize=8, fontName="Helvetica-Bold",
                                     textColor=C_YELLOW, alignment=TA_RIGHT)),
            Paragraph(f"<b>{total_lunas}</b>",
                      ParagraphStyle("TotL", fontSize=8, fontName="Helvetica-Bold",
                                     textColor=C_YELLOW, alignment=TA_RIGHT)),
            Paragraph(f"<b>{total_all_trx}</b>",
                      ParagraphStyle("TotA", fontSize=8, fontName="Helvetica-Bold",
                                     textColor=C_YELLOW, alignment=TA_RIGHT)),
            Paragraph("", CC),
        ])

    else:  # yearly
        monthly_rev = defaultdict(float)
        monthly_trx = defaultdict(int)
        for o in orders_qs.filter(payment_status="paid"):
            m = o.created_at.month
            monthly_rev[m] += float(o.total_price or 0)
            monthly_trx[m] += 1

        monthly_all = defaultdict(int)
        for o in orders_qs:
            monthly_all[o.created_at.month] += 1

        col_widths = [usable_w*0.06, usable_w*0.22, usable_w*0.22,
                      usable_w*0.18, usable_w*0.16, usable_w*0.16]
        data = [[
            Paragraph("No", HR),
            Paragraph("Bulan", HR),
            Paragraph("Total Pendapatan (Rp)", HR),
            Paragraph("Transaksi Lunas", HR),
            Paragraph("Total Transaksi", HR),
            Paragraph("Pertumbuhan", HR),
        ]]

        total_rev = 0.0
        prev_rev  = 0.0
        for m in range(1, 13):
            rev   = monthly_rev.get(m, 0.0)
            lunas = monthly_trx.get(m, 0)
            all_t = monthly_all.get(m, 0)
            total_rev += rev
            growth = ""
            if prev_rev > 0:
                pct = (rev - prev_rev) / prev_rev * 100
                growth = f"{'▲' if pct >= 0 else '▼'} {abs(pct):.1f}%"
            prev_rev = rev

            data.append([
                Paragraph(str(m), CC),
                Paragraph(BULAN_ID[m], CC),
                Paragraph(_rp(rev), CR),
                Paragraph(str(lunas), CR),
                Paragraph(str(all_t), CR),
                Paragraph(growth, CC),
            ])

        ti = len(data)
        data.append([
            Paragraph("", CC),
            Paragraph("<b>TOTAL</b>",
                      ParagraphStyle("Tot2", fontSize=8, fontName="Helvetica-Bold",
                                     textColor=C_YELLOW)),
            Paragraph(f"<b>{_rp(total_rev)}</b>",
                      ParagraphStyle("TotV2", fontSize=8, fontName="Helvetica-Bold",
                                     textColor=C_YELLOW, alignment=TA_RIGHT)),
            Paragraph("", CC), Paragraph("", CC), Paragraph("", CC),
        ])

    style_cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0), C_ROWTOP),
        ("GRID",          (0, 0), (-1, -1), 0.3, HexColor("#CCCCCC")),
        ("LINEBELOW",     (0, 0), (-1, 0), 0.8, C_YELLOW),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_WHITE, C_GRAY2]),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND",    (0, ti), (-1, ti), C_ROWTOP),
    ]

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle(style_cmds))
    story.append(tbl)
    story.append(PageBreak())


# ─────────────────────────────────────────────────────────────────────────────
# HAL 4 — REKAP PENGELUARAN PER HARI / PER BULAN  (REVISI)
# ─────────────────────────────────────────────────────────────────────────────

def _page_rekap_pengeluaran(story, expenses_qs, styles, mode, month, year):
    """
    Bulanan  → total pengeluaran per hari
    Tahunan  → total pengeluaran per bulan
    Setiap expense di-auto-detect kategorinya.
    """
    if mode == "monthly":
        subtitle = f"Total Pengeluaran per Hari — {BULAN_ID[month]} {year}"
    else:
        subtitle = f"Total Pengeluaran per Bulan — Tahun {year}"

    story.append(_section_header("REKAP PENGELUARAN", subtitle, styles))
    story.append(_yellow_rule())
    story.append(Spacer(1, 6))

    usable_w = W - 2 * MARGIN
    HR = ParagraphStyle("EH", fontSize=8, fontName="Helvetica-Bold",
                        textColor=C_YELLOW, alignment=TA_CENTER)
    CC = styles["table_cell"]
    CR = styles["table_cell_r"]

    expenses_list = list(expenses_qs)

    if mode == "monthly":
        days_in_month = calendar.monthrange(year, month)[1]

        daily_exp = defaultdict(float)
        for e in expenses_list:
            daily_exp[e.date.day] += float(e.amount or 0)

        col_widths = [usable_w*0.08, usable_w*0.24, usable_w*0.22,
                      usable_w*0.22, usable_w*0.24]
        data = [[
            Paragraph("Hari", HR),
            Paragraph("Tanggal", HR),
            Paragraph("Total Pengeluaran (Rp)", HR),
            Paragraph("Jumlah Item", HR),
            Paragraph("Ket", HR),
        ]]

        daily_count = defaultdict(int)
        for e in expenses_list:
            daily_count[e.date.day] += 1

        grand_total = 0.0
        for day in range(1, days_in_month + 1):
            exp   = daily_exp.get(day, 0.0)
            cnt   = daily_count.get(day, 0)
            grand_total += exp

            tanggal_str = f"{day:02d} {BULAN_ID[month]} {year}"
            hari_name   = date(year, month, day).strftime("%A")
            hari_id     = {
                "Monday":"Senin","Tuesday":"Selasa","Wednesday":"Rabu",
                "Thursday":"Kamis","Friday":"Jumat","Saturday":"Sabtu",
                "Sunday":"Minggu"
            }.get(hari_name, hari_name)

            ket = "Tinggi" if exp >= 1_000_000 else ("—" if exp == 0 else "Normal")

            data.append([
                Paragraph(hari_id, CC),
                Paragraph(tanggal_str, CC),
                Paragraph(_rp(exp), CR),
                Paragraph(str(cnt) if cnt else "—", CR),
                Paragraph(ket, CC),
            ])

        ti = len(data)
        data.append([
            Paragraph("", CC),
            Paragraph("<b>TOTAL</b>",
                      ParagraphStyle("TE", fontSize=8, fontName="Helvetica-Bold",
                                     textColor=C_YELLOW)),
            Paragraph(f"<b>{_rp(grand_total)}</b>",
                      ParagraphStyle("TEV", fontSize=8, fontName="Helvetica-Bold",
                                     textColor=C_YELLOW, alignment=TA_RIGHT)),
            Paragraph("", CC), Paragraph("", CC),
        ])

    else:  # yearly
        monthly_exp   = defaultdict(float)
        monthly_count = defaultdict(int)
        for e in expenses_list:
            m = e.date.month
            monthly_exp[m]   += float(e.amount or 0)
            monthly_count[m] += 1

        col_widths = [usable_w*0.06, usable_w*0.22, usable_w*0.24,
                      usable_w*0.18, usable_w*0.30]
        data = [[
            Paragraph("No", HR),
            Paragraph("Bulan", HR),
            Paragraph("Total Pengeluaran (Rp)", HR),
            Paragraph("Jumlah Item", HR),
            Paragraph("Pertumbuhan", HR),
        ]]

        grand_total = 0.0
        prev_exp    = 0.0
        for m in range(1, 13):
            exp   = monthly_exp.get(m, 0.0)
            cnt   = monthly_count.get(m, 0)
            grand_total += exp
            growth = ""
            if prev_exp > 0:
                pct = (exp - prev_exp) / prev_exp * 100
                growth = f"{'▲' if pct >= 0 else '▼'} {abs(pct):.1f}%"
            prev_exp = exp

            data.append([
                Paragraph(str(m), CC),
                Paragraph(BULAN_ID[m], CC),
                Paragraph(_rp(exp), CR),
                Paragraph(str(cnt) if cnt else "—", CR),
                Paragraph(growth, CC),
            ])

        ti = len(data)
        data.append([
            Paragraph("", CC),
            Paragraph("<b>TOTAL</b>",
                      ParagraphStyle("TE2", fontSize=8, fontName="Helvetica-Bold",
                                     textColor=C_YELLOW)),
            Paragraph(f"<b>{_rp(grand_total)}</b>",
                      ParagraphStyle("TEV2", fontSize=8, fontName="Helvetica-Bold",
                                     textColor=C_YELLOW, alignment=TA_RIGHT)),
            Paragraph("", CC), Paragraph("", CC),
        ])

    style_cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0), C_ROWTOP),
        ("GRID",          (0, 0), (-1, -1), 0.3, HexColor("#CCCCCC")),
        ("LINEBELOW",     (0, 0), (-1, 0), 0.8, C_YELLOW),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_WHITE, C_GRAY2]),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND",    (0, ti), (-1, ti), C_ROWTOP),
    ]

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle(style_cmds))
    story.append(tbl)
    story.append(PageBreak())


# ─────────────────────────────────────────────────────────────────────────────
# HAL 5 — TOP MENU TERLARIS
# ─────────────────────────────────────────────────────────────────────────────

def _page_top_menu(story, orders_qs, days_in_period, styles):
    story.append(_section_header(
        "TOP MENU TERLARIS", "Berdasarkan Qty & Omzet", styles))
    story.append(_yellow_rule())
    story.append(Spacer(1, 6))

    menus = (
        OrderItem.objects.filter(order__in=orders_qs)
        .values("menu__name")
        .annotate(
            qty=Sum("quantity"),
            omzet=Sum(ExpressionWrapper(
                F("price") * F("quantity"), output_field=DecimalField())),
        )
        .order_by("-qty")
    )
    menus_list  = list(menus)
    total_omzet = sum(float(m["omzet"] or 0) for m in menus_list)

    usable_w = W - 2 * MARGIN
    HR = ParagraphStyle("TMH", fontSize=7.5, fontName="Helvetica-Bold",
                        textColor=C_YELLOW, alignment=TA_CENTER)
    CC = styles["table_cell"]
    CR = styles["table_cell_r"]
    CL = ParagraphStyle("TMCL", fontSize=7.5, fontName="Helvetica",
                        textColor=C_DARK, alignment=TA_LEFT)

    col_widths = [usable_w*0.28, usable_w*0.10, usable_w*0.14,
                  usable_w*0.10, usable_w*0.16, usable_w*0.12, usable_w*0.10]

    data = [[Paragraph(h, HR) for h in
             ["Nama Menu","Kategori","Harga Satuan (Rp)","Qty Terjual",
              "Total Omzet (Rp)","% Kontribusi","Rata-rata/Hari"]]]

    RANK_ICONS  = ["🥇", "🥈", "🥉"]
    ROW_COLORS  = [HexColor("#FFFBEB"), HexColor("#F0F9FF"), HexColor("#FFF1F2")]
    style_cmds  = [
        ("BACKGROUND",    (0,0),(-1,0), C_ROWTOP),
        ("GRID",          (0,0),(-1,-1), 0.3, HexColor("#CCCCCC")),
        ("LINEBELOW",     (0,0),(-1,0), 0.8, C_YELLOW),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 5),
        ("RIGHTPADDING",  (0,0),(-1,-1), 5),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_WHITE, C_GRAY2]),
    ]

    for i, item in enumerate(menus_list):
        idx   = i + 1
        omzet = float(item["omzet"] or 0)
        pct   = (omzet / total_omzet * 100) if total_omzet else 0
        avg   = round(item["qty"] / days_in_period, 1) if days_in_period else 0
        icon  = RANK_ICONS[i] if i < 3 else str(idx)

        data.append([
            Paragraph(f"{icon}  {item['menu__name']}", CL),
            Paragraph("—", CC),
            Paragraph("—", CR),
            Paragraph(str(item["qty"]), CR),
            Paragraph(_rp(omzet), CR),
            Paragraph(f"{pct:.1f}%", CR),
            Paragraph(str(avg), CR),
        ])
        if i < 3:
            style_cmds.append(("BACKGROUND", (0, idx), (-1, idx), ROW_COLORS[i]))

    ti = len(data)
    data.append([
        Paragraph("<b>TOTAL</b>", ParagraphStyle("Tot", fontSize=8,
            fontName="Helvetica-Bold", textColor=C_YELLOW)),
        Paragraph("", CC), Paragraph("", CC),
        Paragraph(f"<b>{sum(int(m['qty']) for m in menus_list)}</b>",
                  ParagraphStyle("TotQ", fontSize=8, fontName="Helvetica-Bold",
                                 textColor=C_YELLOW, alignment=TA_RIGHT)),
        Paragraph(f"<b>{_rp(total_omzet)}</b>",
                  ParagraphStyle("TotO", fontSize=8, fontName="Helvetica-Bold",
                                 textColor=C_YELLOW, alignment=TA_RIGHT)),
        Paragraph("<b>100%</b>", ParagraphStyle("TotP", fontSize=8,
            fontName="Helvetica-Bold", textColor=C_YELLOW, alignment=TA_RIGHT)),
        Paragraph("", CC),
    ])
    style_cmds.append(("BACKGROUND", (0, ti), (-1, ti), C_ROWTOP))

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle(style_cmds))
    story.append(tbl)
    story.append(PageBreak())


# ─────────────────────────────────────────────────────────────────────────────
# HAL 6 — REKAP KATEGORI + KETERANGAN PERFORMA + TTD
# ─────────────────────────────────────────────────────────────────────────────

def _build_auto_narasi(orders_qs, expenses_qs, period_label, mode, month, year) -> list[str]:
    """
    Bangun narasi otomatis + bullet point berdasarkan data real.
    Return list of Paragraph objects.
    """
    total_rev     = float(orders_qs.filter(payment_status="paid")
                          .aggregate(t=Sum("total_price"))["t"] or 0)
    total_exp     = float(expenses_qs.aggregate(t=Sum("amount"))["t"] or 0)
    net_profit    = total_rev - total_exp
    total_trx     = orders_qs.count()
    lunas_trx     = orders_qs.filter(payment_status="paid").count()
    pending_trx   = orders_qs.filter(payment_status__in=["pending","unpaid"]).count()

    performa_label = "sangat baik" if net_profit > 0 else "perlu perhatian"

    # Hari terbaik (bulanan) / bulan terbaik (tahunan)
    hari_terbaik_str = ""
    peak_rev         = 0.0

    if mode == "monthly":
        daily_rev = defaultdict(float)
        for o in orders_qs.filter(payment_status="paid"):
            daily_rev[o.created_at.day] += float(o.total_price or 0)

        if daily_rev:
            best_day = max(daily_rev, key=daily_rev.get)
            peak_rev = daily_rev[best_day]
            hari_name = date(year, month, best_day).strftime("%A")
            hari_id   = {
                "Monday":"Senin","Tuesday":"Selasa","Wednesday":"Rabu",
                "Thursday":"Kamis","Friday":"Jumat","Saturday":"Sabtu",
                "Sunday":"Minggu"
            }.get(hari_name, hari_name)
            hari_terbaik_str = (
                f"Hari dengan pendapatan tertinggi jatuh pada "
                f"<b>{hari_id}, {best_day:02d} {BULAN_ID[month]} {year}</b> "
                f"dengan total <b>{_rp(peak_rev)}</b>."
            )
        # Rata-rata harian
        days_in_m  = calendar.monthrange(year, month)[1]
        avg_daily  = total_rev / days_in_m if days_in_m else 0
        avg_daily_str = f"Rata-rata pendapatan harian bulan ini sebesar <b>{_rp(avg_daily)}</b>."

        # Hari sepi
        sepi_days = [d for d, v in daily_rev.items() if v < avg_daily * 0.5 and v > 0]
        sepi_str  = (f"Terdapat <b>{len(sepi_days)} hari</b> dengan pendapatan di bawah rata-rata."
                     if sepi_days else "Tidak ada hari dengan pendapatan di bawah rata-rata.")

        opening = (
            f"Laporan keuangan <b>{BULAN_ID[month]} {year}</b> menunjukkan performa toko "
            f"secara keseluruhan <b>{performa_label}</b>. "
            f"Total pendapatan bulan ini mencapai <b>{_rp(total_rev)}</b> "
            f"dari <b>{lunas_trx} transaksi lunas</b> (total {total_trx} transaksi masuk), "
            f"dengan pengeluaran operasional sebesar <b>{_rp(total_exp)}</b>, "
            f"sehingga laba bersih yang diperoleh adalah <b>{_rp(net_profit)}</b>."
        )

        bullets = [
            f"● {hari_terbaik_str}" if hari_terbaik_str else "",
            f"● {avg_daily_str}",
            f"● {sepi_str}",
            f"● Terdapat <b>{pending_trx} transaksi pending/belum lunas</b> yang perlu ditindaklanjuti.",
            f"● Rasio laba terhadap pendapatan: <b>{(net_profit/total_rev*100):.1f}%</b>." if total_rev else "",
        ]

    else:  # yearly
        monthly_rev = defaultdict(float)
        for o in orders_qs.filter(payment_status="paid"):
            monthly_rev[o.created_at.month] += float(o.total_price or 0)

        if monthly_rev:
            best_month = max(monthly_rev, key=monthly_rev.get)
            peak_rev   = monthly_rev[best_month]
            hari_terbaik_str = (
                f"Bulan dengan pendapatan tertinggi adalah "
                f"<b>{BULAN_ID[best_month]} {year}</b> "
                f"dengan total <b>{_rp(peak_rev)}</b>."
            )

        avg_monthly = total_rev / 12
        avg_monthly_str = f"Rata-rata pendapatan bulanan tahun ini sebesar <b>{_rp(avg_monthly)}</b>."

        opening = (
            f"Laporan keuangan tahunan <b>Tahun {year}</b> menunjukkan performa toko "
            f"secara keseluruhan <b>{performa_label}</b>. "
            f"Total pendapatan sepanjang tahun ini mencapai <b>{_rp(total_rev)}</b> "
            f"dari <b>{lunas_trx} transaksi lunas</b> (total {total_trx} transaksi masuk), "
            f"dengan total pengeluaran operasional <b>{_rp(total_exp)}</b>, "
            f"sehingga laba bersih tahunan adalah <b>{_rp(net_profit)}</b>."
        )

        bullets = [
            f"● {hari_terbaik_str}" if hari_terbaik_str else "",
            f"● {avg_monthly_str}",
            f"● Terdapat <b>{pending_trx} transaksi pending/belum lunas</b> sepanjang tahun.",
            f"● Rasio laba terhadap pendapatan: <b>{(net_profit/total_rev*100):.1f}%</b>." if total_rev else "",
        ]

    return opening, [b for b in bullets if b]


def _page_rekap_catatan(story, orders_qs, expenses_qs, generated_at,
                        period_label, styles, mode, month, year):

    usable_w = W - 2 * MARGIN
    HR = ParagraphStyle("RKH", fontSize=8, fontName="Helvetica-Bold",
                        textColor=C_YELLOW, alignment=TA_CENTER)
    CC = styles["table_cell"]
    CR = styles["table_cell_r"]

    # ── Rekap per Kategori (dengan auto-detect) ──────────────────────────────
    story.append(_section_header("REKAP PENGELUARAN PER KATEGORI", "", styles))
    story.append(_yellow_rule())
    story.append(Spacer(1, 6))

    CATEGORIES   = ["Bahan Baku", "Operasional", "Karyawan", "Marketing", "Lainnya"]
    CAT_COLORS_BG = {
        "Bahan Baku":  HexColor("#DBEAFE"),
        "Operasional": HexColor("#FEF3C7"),
        "Karyawan":    HexColor("#DCFCE7"),
        "Marketing":   HexColor("#FEE2E2"),
        "Lainnya":     HexColor("#F3E8FF"),
    }

    # Hitung total per kategori via auto-detect
    cat_totals = defaultdict(float)
    for e in expenses_qs:
        cat = _auto_category(e.description)
        cat_totals[cat] += float(e.amount or 0)

    total_exp = sum(cat_totals.values())

    col_widths = [usable_w*0.30, usable_w*0.25, usable_w*0.20, usable_w*0.25]
    data = [[Paragraph(h, HR) for h in
             ["Kategori", "Total (Rp)", "% dari Total", "Keterangan"]]]

    style_cmds = [
        ("BACKGROUND",    (0,0),(-1,0), C_ROWTOP),
        ("GRID",          (0,0),(-1,-1), 0.3, HexColor("#CCCCCC")),
        ("LINEBELOW",     (0,0),(-1,0), 0.8, C_YELLOW),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("RIGHTPADDING",  (0,0),(-1,-1), 8),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ]

    for i, cat in enumerate(CATEGORIES):
        ri      = i + 1
        cat_tot = cat_totals.get(cat, 0.0)
        pct     = (cat_tot / total_exp * 100) if total_exp else 0
        data.append([
            Paragraph(f"<b>{cat}</b>", styles["cat_label"]),
            Paragraph(_rp(cat_tot), CR),
            Paragraph(f"{pct:.1f}%", CR),
            Paragraph("", CC),
        ])
        style_cmds.append(("BACKGROUND", (0,ri),(0,ri), CAT_COLORS_BG.get(cat, C_GRAY)))

    gt_i = len(data)
    data.append([
        Paragraph("<b>GRAND TOTAL</b>",
                  ParagraphStyle("GT", fontSize=8.5, fontName="Helvetica-Bold",
                                 textColor=C_YELLOW)),
        Paragraph(f"<b>{_rp(total_exp)}</b>",
                  ParagraphStyle("GTV", fontSize=8.5, fontName="Helvetica-Bold",
                                 textColor=C_YELLOW, alignment=TA_RIGHT)),
        Paragraph("<b>100%</b>",
                  ParagraphStyle("GTP", fontSize=8.5, fontName="Helvetica-Bold",
                                 textColor=C_YELLOW, alignment=TA_RIGHT)),
        Paragraph("", CC),
    ])
    style_cmds.append(("BACKGROUND", (0,gt_i),(-1,gt_i), C_ROWTOP))

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle(style_cmds))
    story.append(tbl)
    story.append(Spacer(1, 18))

    # ── KETERANGAN PERFORMA (REVISI: auto-generated narasi) ──────────────────
    story.append(_section_header("KETERANGAN PERFORMA", "", styles))
    story.append(_yellow_rule())
    story.append(Spacer(1, 8))

    opening, bullets = _build_auto_narasi(
        orders_qs, expenses_qs, period_label, mode, month, year)

    # Kotak narasi
    narasi_style = ParagraphStyle(
        "NarasiBox", fontSize=8.5, fontName="Helvetica",
        textColor=C_DARK, leading=14)
    bullet_style = ParagraphStyle(
        "BulletBox", fontSize=8, fontName="Helvetica",
        textColor=C_DARK, leading=13, leftIndent=6, spaceAfter=3)

    narasi_content = [Paragraph(opening, narasi_style), Spacer(1, 8)]
    for b in bullets:
        narasi_content.append(Paragraph(b, bullet_style))

    # Wrap dalam tabel bergaris
    from reportlab.platypus import KeepInFrame
    narasi_box = Table(
        [[narasi_content]],
        colWidths=[usable_w],
    )
    narasi_box.setStyle(TableStyle([
        ("BOX",           (0,0),(-1,-1), 0.8, C_YELLOW),
        ("BACKGROUND",    (0,0),(-1,-1), HexColor("#FFFDF0")),
        ("TOPPADDING",    (0,0),(-1,-1), 14),
        ("BOTTOMPADDING", (0,0),(-1,-1), 14),
        ("LEFTPADDING",   (0,0),(-1,-1), 14),
        ("RIGHTPADDING",  (0,0),(-1,-1), 14),
    ]))
    story.append(narasi_box)
    story.append(Spacer(1, 18))

    # ── TANDA TANGAN ─────────────────────────────────────────────────────────
    story.append(_section_header("TANDA TANGAN & PERSETUJUAN", "", styles))
    story.append(_yellow_rule())
    story.append(Spacer(1, 14))

    half_w = (usable_w - 20) / 2
    sign_box_style = TableStyle([
        ("BOX",           (0,0),(-1,-1), 0.5, HexColor("#CCCCCC")),
        ("TOPPADDING",    (0,0),(-1,-1), 50),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("RIGHTPADDING",  (0,0),(-1,-1), 8),
    ])

    left_sign  = Table([[Paragraph("", styles["normal"])]], colWidths=[half_w])
    left_sign.setStyle(sign_box_style)
    right_sign = Table([[Paragraph("", styles["normal"])]], colWidths=[half_w])
    right_sign.setStyle(sign_box_style)

    sign_tbl = Table([
        [Paragraph("<b>Dibuat oleh:</b>", styles["sign_label"]),
         Paragraph("", styles["normal"]),
         Paragraph("<b>Diperiksa oleh:</b>", styles["sign_label"])],
        [Paragraph("(Kasir / Operator)", styles["sign_sub"]),
         Paragraph("", styles["normal"]),
         Paragraph("(Manajer / Pemilik)", styles["sign_sub"])],
        [left_sign, Paragraph("", styles["normal"]), right_sign],
        [Paragraph("Nama &amp; Jabatan", styles["sign_name"]),
         Paragraph("", styles["normal"]),
         Paragraph("Nama &amp; Jabatan", styles["sign_name"])],
    ], colWidths=[half_w, 20, half_w])
    sign_tbl.setStyle(TableStyle([
        ("TOPPADDING",    (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3),
        ("LEFTPADDING",   (0,0),(-1,-1), 0),
        ("RIGHTPADDING",  (0,0),(-1,-1), 0),
        ("LINEABOVE",     (0,3),(-1,3), 0.5, HexColor("#999999")),
        ("ALIGN",         (0,3),(0,3), "CENTER"),
        ("ALIGN",         (2,3),(2,3), "CENTER"),
    ]))
    story.append(sign_tbl)

    story.append(Spacer(1, 12))
    story.append(Paragraph(
        f"<i>Laporan digenerate otomatis pada: <b>{generated_at}</b> "
        f"— Periode: <b>{period_label}</b></i>",
        ParagraphStyle("GenInfo", fontSize=7.5, fontName="Helvetica-Oblique",
                       textColor=C_FOOT, alignment=TA_CENTER),
    ))


# ─────────────────────────────────────────────────────────────────────────────
# FUNGSI UTAMA
# ─────────────────────────────────────────────────────────────────────────────

def export_finance_pdf(
    request,
    orders_qs,
    expenses_qs,
    period_label: str,
    mode: str = "monthly",
    month: int | None = None,
    year: int | None = None,
):
    now = timezone.now()
    if year is None:
        year = now.year
    if mode == "monthly" and month is None:
        month = now.month

    generated_at   = _fmt_tanggal_id(now)
    filename       = _build_filename(mode, month, year)
    days_in_period = calendar.monthrange(year, month)[1] if mode == "monthly" else 365
    styles         = _build_styles()

    logo_cover  = _load_logo(380)
    logo_header = _load_logo(90)

    # Cover
    cover_buf = io.BytesIO()
    from reportlab.pdfgen import canvas as rl_canvas
    cv = rl_canvas.Canvas(cover_buf, pagesize=A4)
    _build_cover_page(cv, period_label, generated_at, logo_cover)
    cv.save()
    cover_buf.seek(0)

    # Inner pages
    inner_buf = io.BytesIO()
    doc = SimpleDocTemplate(
        inner_buf, pagesize=A4,
        rightMargin=MARGIN, leftMargin=MARGIN,
        topMargin=TOP_BAR + 12, bottomMargin=BOT_BAR + 8,
    )

    frame_cb = _PageFrame(logo_header, period_label, generated_at)

    story = []
    _page_ringkasan(story, orders_qs, expenses_qs, period_label, styles)
    _page_rekap_pendapatan(story, orders_qs, styles, mode, month, year)
    _page_rekap_pengeluaran(story, expenses_qs, styles, mode, month, year)
    _page_top_menu(story, orders_qs, days_in_period, styles)
    _page_rekap_catatan(story, orders_qs, expenses_qs, generated_at,
                        period_label, styles, mode, month, year)

    doc.build(story, onFirstPage=frame_cb, onLaterPages=frame_cb)
    inner_buf.seek(0)

    # Gabungkan
    from pypdf import PdfReader, PdfWriter
    writer = PdfWriter()
    for reader in [PdfReader(cover_buf), PdfReader(inner_buf)]:
        for page in reader.pages:
            writer.add_page(page)

    writer.add_metadata({
        "/Title":    f"Laporan Keuangan Masashimura — {period_label}",
        "/Author":   "Masashimura System",
        "/Subject":  f"Laporan Keuangan {period_label}",
        "/Creator":  "finance_pdf.py v2.0",
        "/Producer": "ReportLab + pypdf",
    })

    final_buf = io.BytesIO()
    writer.write(final_buf)
    final_buf.seek(0)

    response = HttpResponse(content_type="application/pdf")
    encoded  = filename.encode("utf-8").decode("latin-1", errors="replace")
    response["Content-Disposition"] = (
        f'attachment; filename="{encoded}"; '
        f"filename*=UTF-8''{filename.replace(' ', '%20')}"
    )
    response.write(final_buf.read())
    return response


# ─────────────────────────────────────────────────────────────────────────────
# VIEW HELPER
# ─────────────────────────────────────────────────────────────────────────────

def export_finance_pdf_view(request):
    """
    GET /api/orders/export/finance-pdf/?mode=monthly&month=7&year=2026
    GET /api/orders/export/finance-pdf/?mode=yearly&year=2026
    """
    mode  = request.GET.get("mode", "monthly")
    year  = int(request.GET.get("year",  timezone.now().year))
    month = int(request.GET.get("month", timezone.now().month)) if mode == "monthly" else None

    if mode == "monthly":
        orders_qs   = Order.objects.filter(
            created_at__year=year, created_at__month=month,
        ).prefetch_related("items__menu")
        expenses_qs  = Expense.objects.filter(date__year=year, date__month=month)
        period_label = f"{BULAN_ID[month]} {year}"
    else:
        orders_qs   = Order.objects.filter(
            created_at__year=year,
        ).prefetch_related("items__menu")
        expenses_qs  = Expense.objects.filter(date__year=year)
        period_label = f"Tahun {year}"

    return export_finance_pdf(
        request=request,
        orders_qs=orders_qs,
        expenses_qs=expenses_qs,
        period_label=period_label,
        mode=mode,
        month=month,
        year=year,
    )