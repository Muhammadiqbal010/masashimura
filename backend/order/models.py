from django.db import models, transaction
from django.db.models.signals import pre_save, post_save
from dateutil.relativedelta import relativedelta
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
import random
import string

from menu.models import Menu

# Zona waktu operasional toko (WIB, UTC+7, tanpa DST). Dipakai untuk "hari" order
# dan tanggal di nomor order, supaya tidak bergantung ke setting TIME_ZONE server.
WIB = timezone.get_fixed_timezone(7 * 60)


# ─────────────────────────────────────────────
# CHOICES
# ─────────────────────────────────────────────

ORDER_SERVICE_TYPE_CHOICES = (
    ('dine_in', 'Makan di Tempat'),
    ('takeaway', 'Dibungkus'),
)

ORDER_SOURCE_CHOICES = (
    ('web', 'Web'),
    ('pos', 'POS'),
)

ORDER_STATUS_CHOICES = (
    ('pending',    'Pending'),
    ('processing', 'Processing'),
    ('completed',  'Completed'),
    ('cancelled',  'Cancelled'),
)

CANCEL_REASON_CHOICES = (
    ('wrong_input',     'Salah input'),
    ('customer_cancel', 'Pelanggan batal'),
    ('out_of_stock',    'Stok habis'),
    ('other',           'Lainnya'),
)

PAYMENT_STATUS_CHOICES = (
    ('unpaid',                'Unpaid'),
    ('paid',                  'Paid'),
    ('pending',                'Pending'),
    ('void',                  'Batal'),
)

PAYMENT_METHOD_CHOICES = (
    ('cash',        'Cash'),
    ('qris',        'QRIS'),
    ('qris_manual', 'QRIS Manual'),
    ('gateway',     'Payment Gateway'),
    ('mixed',       'Campuran (Split Bayar)'),
)


# ─────────────────────────────────────────────
# ORDER
# ─────────────────────────────────────────────

# Aturan "siap diambil" (HANYA order dari web):
#  - ditekan manual (ready_at), ATAU
#  - sudah dilunasi di kasir (bukan gateway online -- itu dibayar di muka, dapur belum masak), ATAU
#  - tombol Siap tidak disentuh sampai AUTO_READY_HOURS jam sejak order masuk / tambahan menu terakhir.
# Order POS tidak punya status siap sama sekali: pelanggannya sudah ada di warung.
AUTO_READY_HOURS = 2


def kitchen_open_q(now=None):
    """
    Q untuk order yang masih "berjalan" di dapur / belum diserahkan.
    Web : belum siap manual, belum lunas di kasir, belum lewat AUTO_READY_HOURS.
    POS : belum lunas, ATAU sudah lunas tapi barusan (dalam AUTO_READY_HOURS) -- POS tidak punya
          tombol siap, jadi pesanan yang dibayar di muka dianggap masih disiapkan selama jendela itu.
    """
    from django.db.models import Q
    now = now or timezone.now()
    cutoff = now - timedelta(hours=AUTO_READY_HOURS)
    paid_at_counter = Q(payment_status='paid') & ~Q(payment_method='gateway')
    web = Q(source='web', ready_at__isnull=True, created_at__gt=cutoff) & ~paid_at_counter
    pos = Q(source='pos') & (~Q(payment_status='paid') | Q(created_at__gt=cutoff))
    return web | pos


class Order(models.Model):
    order_number = models.CharField(max_length=30, unique=True, editable=False, blank=True)

    source         = models.CharField(max_length=10, choices=ORDER_SOURCE_CHOICES, default='web')
    status         = models.CharField(max_length=15, choices=ORDER_STATUS_CHOICES, default='pending')

    payment_status = models.CharField(max_length=25, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    is_deferred_payment = models.BooleanField(
        default=False,
        help_text='POS: pelanggan makan dulu, bayar nanti',
    )

    # Makan di tempat atau dibungkus. Terpisah dari is_deferred_payment (itu soal
    # KAPAN bayar, ini soal DI MANA makannya). Order lama otomatis 'dine_in'.
    service_type = models.CharField(
        max_length=10, choices=ORDER_SERVICE_TYPE_CHOICES, default='dine_in',
    )

    customer_name  = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True, db_index=True)
    table_number   = models.CharField(max_length=10, blank=True, null=True)

    subtotal        = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    total_price     = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    promo = models.ForeignKey('promotions.Promo', on_delete=models.SET_NULL, null=True, blank=True)
    promo_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    notes = models.TextField(blank=True, null=True)

    # PENTING: pakai default=timezone.now, BUKAN auto_now_add=True.
    # auto_now_add memaksa Django selalu overwrite created_at ke waktu
    # sekarang setiap kali objek dibuat -- termasuk saat kita eksplisit
    # set created_at manual lewat bulk_create() (contoh: generate_dummy.py).
    # default=timezone.now tetap otomatis keisi waktu sekarang untuk order
    # asli (checkout/POS) selama field-nya gak diisi manual, tapi TIDAK
    # akan override kalau kita eksplisit kasih nilai lain.
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # Waktu ASLI order ini diketik ke sistem. HANYA diisi kalau admin menginput
    # order untuk waktu lain (created_at diatur manual di POS — mis. salah input
    # yang baru ketahuan besok). Kosong = order dibuat saat itu juga.
    # Dipakai buat audit & badge "Input susulan" di Active Orders.
    entered_at = models.DateTimeField(null=True, blank=True)

    amount_paid = models.DecimalField(
    max_digits=12,
    decimal_places=0,
    default=0
    )

    change_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0
    )

    kasir_name = models.CharField(
        max_length=100,
        blank=True,
        default=""
    )

    # Snap token Midtrans. Disimpan supaya kalau customer menutup popup lalu
    # klik bayar lagi, token yang sama dipakai ulang (tidak ada transaksi
    # Midtrans kedua → tidak ada risiko bayar dobel). Bukti bayar tidak
    # disimpan di sini: status lunas datang dari webhook Midtrans.
    midtrans_snap_token = models.CharField(
        max_length=100, blank=True, default="", editable=False,
    )

    # QRIS dinamis Midtrans untuk order POS (Core API). Disimpan supaya QR yang masih
    # berlaku ditampilkan lagi, bukan bikin transaksi kedua.
    midtrans_qr_url = models.TextField(blank=True, default="", editable=False)
    # ID transaksi Midtrans untuk QR "bayar nanti" (nota yang sudah ada). Dibuat unik per QR
    # (NOMOR-Q1, NOMOR-Q2, ...) supaya QR kedaluwarsa tidak ikut membatalkan nota & bisa dibuat ulang.
    # Kosong untuk order QRIS "bayar sekarang" (pakai order_number langsung).
    midtrans_qr_ref = models.CharField(max_length=60, blank=True, default="", editable=False)
    midtrans_qr_expires_at = models.DateTimeField(null=True, blank=True, editable=False)

    # Order web bayar-di-toko harus DITERIMA kasir dulu (anti-iseng). True = menunggu diterima; kalau lewat
    # CONFIRM_TIMEOUT_MINUTES (lihat guards.py) order dibatalkan otomatis. Order lama & POS selalu False.
    awaiting_confirmation = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)

    # ── Audit trail pembatalan (void) ──────────────────────────────
    # Order yang dibatalkan TIDAK dihapus dari database — cuma diubah
    # statusnya jadi 'cancelled' + dicatat alasannya di sini, biar tetap
    # kelacak buat laporan/audit (gak ada transaksi yang "hilang" gitu saja).
    cancel_reason = models.CharField(
        max_length=20, choices=CANCEL_REASON_CHOICES, blank=True, null=True,
        help_text="Alasan order dibatalkan",
    )
    cancel_note = models.CharField(
        max_length=255, blank=True, default="",
        help_text="Catatan tambahan opsional saat membatalkan order",
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.CharField(
        max_length=100, blank=True, default="",
        help_text="Nama kasir/admin yang membatalkan order",
    )

    # ── Dipakai buat reversal akurat kalau order ini dihapus permanen ──
    # (lihat OrderDeletionLog / views._delete_order_permanently). Disimpan
    # di sini (bukan dihitung ulang saat delete) karena rupiah_per_point
    # di LoyaltySettings bisa saja sudah berubah sejak order ini completed
    # — kalau dihitung ulang pakai rate SEKARANG, angkanya bisa salah.
    loyalty_applied = models.BooleanField(
        default=False,
        help_text="True kalau order ini sudah pernah trigger penambahan poin ke customer",
    )
    loyalty_points_earned = models.PositiveIntegerField(
        default=0,
        help_text="Poin yang di-earn dari order ini saat completed — disimpan biar reversal saat delete akurat, tidak bergantung rupiah_per_point yang mungkin sudah berubah",
    )

    # ── Status dapur & menu habis ─────────────────────────────────
    # "completed" di sistem ini artinya LUNAS, bukan "makanan sudah jadi", jadi
    # kesiapan dicatat terpisah. Kosong = belum ditandai siap diambil.
    ready_at = models.DateTimeField(null=True, blank=True)

    # Menu yang batal dibuat karena habis SETELAH order dibuat:
    # [{"name": "Kukubima", "quantity": 1, "price": 7500, "at": "2026-10-23T10:00:00+07:00"}]
    # Item-nya sendiri dihapus dari nota (total ikut turun); catatannya disimpan di sini.
    unavailable_items = models.JSONField(default=list, blank=True)

    # Uang yang harus DIKEMBALIKAN ke pelanggan karena menu habis di order yang
    # sudah lunas (QRIS/gateway/cash di muka). 0 = tidak ada utang kembalian.
    refund_due = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    refunded_at = models.DateTimeField(null=True, blank=True)
    refunded_by = models.CharField(max_length=100, blank=True, default="")

    # ── Jejak asal pemesan (hanya order web; untuk melacak scam) ──────────────
    # IP dipisah ke kolom sendiri supaya bisa dicari/diindeks ("semua order dari IP ini").
    # client_info = {country, region, city, lat, lng, tz, device, ua, bot} — PERKIRAAN dari header
    # Vercel (lihat client_info.py). Sengaja TIDAK masuk OrderSerializer agar tidak sampai ke pelanggan.
    client_ip = models.GenericIPAddressField(null=True, blank=True, db_index=True, editable=False)
    client_info = models.JSONField(default=dict, blank=True, editable=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_number} [{self.get_source_display()}]"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Tanggal di nomor order mengikuti created_at (bukan jam saat ini),
            # supaya order input susulan tetap bernomor sesuai harinya.
            self.order_number = generate_order_number(self.created_at)
        super().save(*args, **kwargs)

    # ── Status siap (lihat AUTO_READY_HOURS di atas) ─────────────────
    @property
    def tracks_readiness(self):
        return self.source == 'web'

    def kitchen_clock_start(self):
        """Titik mulai hitungan menit: order masuk, atau tambahan menu terakhir kalau ada."""
        starts = [self.created_at] + [i.added_at for i in self.items.all() if i.added_at]
        return max(starts)

    def ready_source(self, now=None):
        """'manual' | 'paid' | 'auto' | None (belum siap / tidak dilacak)."""
        if not self.tracks_readiness or self.status == 'cancelled' or self.payment_status == 'void':
            return None
        if self.ready_at is not None:
            return 'manual'
        if self.payment_status == 'paid' and self.payment_method != 'gateway':
            return 'paid'
        now = now or timezone.now()
        if now - self.kitchen_clock_start() >= timedelta(hours=AUTO_READY_HOURS):
            return 'auto'
        return None

    def recalculate_totals(self):
        subtotal      = sum((item.subtotal for item in self.items.all()), Decimal('0'))
        self.subtotal = subtotal
        # Diskon tier loyalty otomatis SUDAH DIHAPUS — satu-satunya jalur
        # reward customer sekarang cuma poin (tukar menu gratis, dicatat
        # sebagai OrderItem is_point_redemption). discount_amount dibiarkan
        # ada di kolom (buat kompatibilitas data lama) tapi ngga pernah lagi
        # diisi otomatis di sini — cuma promo_discount_amount yang aktif motong harga.
        total = subtotal - self.discount_amount - self.promo_discount_amount
        self.total_price = total if total > 0 else Decimal('0')
        self.save(update_fields=['subtotal', 'total_price'])


# ─────────────────────────────────────────────
# ORDER ITEM
# ─────────────────────────────────────────────

class OrderItem(models.Model):
    order    = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu = models.ForeignKey(Menu, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    # Harga SATUAN, sudah termasuk add-on berbayar (kalau ada).
    price = models.DecimalField(max_digits=10, decimal_places=0)

    # Teks yang tampil di struk/drawer: gabungan pilihan opsi + catatan bebas,
    # contoh "Pedas · Extra keju · tanpa sayur". Dirakit server.
    notes = models.CharField(max_length=255, blank=True, default='')

    # Pilihan terstruktur (snapshot saat order dibuat, tidak ikut berubah kalau opsi menu diedit):
    # [{"group": "Level Pedas", "choices": [{"label": "Pedas", "price": 0}]}]
    selected_options = models.JSONField(default=list, blank=True)

    # True kalau item ini didapat dari tukar poin loyalty (harga selalu 0),
    # dipakai buat nampilin badge "Reward" di struk/admin, bukan cuma nebak dari price=0.
    is_point_redemption = models.BooleanField(default=False)

    # Nama paket kalau baris ini berasal dari Menu Paket (snapshot teks, bukan FK:
    # paket boleh dihapus tanpa mengubah riwayat). Kosong = item biasa.
    bundle_name = models.CharField(max_length=100, blank=True, default='')

    # Penanda "ditambahkan setelah order dibuat" (dari Active Orders). added_at =
    # kapan terakhir ditambah, added_qty = berapa porsi yang ditambahkan belakangan.
    # Item bawaan order awal: added_at kosong dan added_qty 0.
    added_at  = models.DateTimeField(null=True, blank=True)
    added_qty = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.menu.name} x{self.quantity}"

    @property
    def subtotal(self):
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        # price=0 itu SAH (item tukar poin) — jangan ditimpa harga menu.
        # Cuma isi otomatis kalau price benar-benar belum diset.
        if self.price is None and self.menu:
            self.price = self.menu.price
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────
# ORDER PAYMENT (split bill / multi-payment)
# ─────────────────────────────────────────────
# Satu Order bisa punya lebih dari satu baris pembayaran — misal
# sebagian cash + sebagian QRIS, atau dibagi rata ke beberapa orang
# (tiap orang jadi satu baris). Total seluruh baris ini yang menentukan
# apakah order sudah lunas atau belum, bukan satu nilai amount_paid saja.
class OrderPayment(models.Model):
    order  = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    method = models.CharField(max_length=15, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.order.order_number} — {self.get_method_display()} Rp{self.amount}"


# ─────────────────────────────────────────────
# ORDER DELETION LOG (audit trail buat hapus permanen)
# ─────────────────────────────────────────────
# Beda dari cancel_order (void) yang cuma ubah status & row Order-nya
# tetap ada di DB — delete permanen beneran ngilangin row Order (+
# OrderItem/OrderPayment via CASCADE). Snapshot di sini disimpan SEBELUM
# Order-nya benar-benar di-.delete(), jadi tetap ada jejak kalau nanti
# dipertanyakan: kapan, siapa yang hapus, isinya apa, dan efek balik
# (poin/promo) apa aja yang sudah di-reverse.
class OrderDeletionLog(models.Model):
    order_number   = models.CharField(max_length=30)
    order_source   = models.CharField(max_length=10)
    order_status   = models.CharField(max_length=15)
    payment_status = models.CharField(max_length=25)
    payment_method = models.CharField(max_length=15, blank=True, null=True)

    customer_name  = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)

    total_price = models.DecimalField(max_digits=12, decimal_places=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=0, default=0)

    original_created_at = models.DateTimeField()

    items_snapshot    = models.JSONField(default=list)
    payments_snapshot = models.JSONField(default=list)

    loyalty_points_reverted = models.IntegerField(
        default=0,
        help_text="Poin yang ditarik balik dari CustomerLoyalty (0 kalau order ini memang tidak pernah menyumbang poin)",
    )
    loyalty_points_refunded = models.IntegerField(
        default=0,
        help_text="Poin tukar reward yang DIKEMBALIKAN ke customer karena order ini dihapus (poin yang dulu terpotong saat order dibuat)",
    )
    loyalty_clamped = models.BooleanField(
        default=False,
        help_text="True kalau saldo poin customer sudah lebih kecil dari yang seharusnya di-reverse (kemungkinan poinnya sudah kepakai buat redeem reward lain) — dikliping ke 0, bukan dipaksa minus",
    )
    promo_code_reverted = models.CharField(max_length=50, blank=True, default="")

    deleted_by = models.CharField(max_length=100, blank=True, default="")
    deleted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-deleted_at"]
        verbose_name = "Order Deletion Log"
        verbose_name_plural = "Order Deletion Logs"

    def __str__(self):
        return f"[DELETED] {self.order_number} oleh {self.deleted_by or '—'} pada {self.deleted_at:%d %b %Y %H:%M}"


# ─────────────────────────────────────────────
# LOYALTY SETTINGS  (singleton)
# ─────────────────────────────────────────────

POINTS_EXPIRY_CHOICES = (
    (0,  'Nonaktif (poin tidak pernah hangus)'),
    (3,  '3 bulan'),
    (6,  '6 bulan'),
    (12, '12 bulan'),
)


class LoyaltySettings(models.Model):
    # Rate poin masuk (BUKAN rate redeem — redeem-nya diatur per-menu di PointReward).
    # Default 10.000 artinya tiap belanja Rp10.000 = 1 poin.
    rupiah_per_point = models.PositiveIntegerField(
        default=10000,
        help_text="Nominal belanja (Rp) yang setara dengan 1 poin loyalty",
    )

    # 0 = nonaktif (poin ngga pernah hangus). Dihitung per-customer dari
    # order TERAKHIR masing-masing (rolling), bukan tanggal serentak buat semua.
    points_expiry_months = models.PositiveSmallIntegerField(
        default=0,
        choices=POINTS_EXPIRY_CHOICES,
        help_text="Poin hangus kalau customer ngga order selama sekian bulan. 0 = nonaktif.",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Loyalty Settings"
        verbose_name_plural = "Loyalty Settings"

    def __str__(self):
        expiry = "nonaktif" if not self.points_expiry_months else f"{self.points_expiry_months} bulan"
        return f"Rp{self.rupiah_per_point}/poin, hangus: {expiry}"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# ─────────────────────────────────────────────
# CUSTOMER LOYALTY
# ─────────────────────────────────────────────

class CustomerLoyalty(models.Model):
    phone = models.CharField(max_length=20, unique=True)
    name  = models.CharField(max_length=100, blank=True)

    points      = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    total_orders = models.PositiveIntegerField(
        default=0,
        help_text="Statistik lifetime, TIDAK ikut hangus (beda dari poin).",
    )

    # Dasar hitung kedaluwarsa poin — rolling per-customer, bukan tanggal
    # serentak buat semua orang. Diupdate tiap kali order customer ini completed.
    last_order_at = models.DateTimeField(null=True, blank=True)

    # PIN member (lihat order/member_pin.py). Hash saja, PIN asli tidak pernah disimpan.
    pin_hash            = models.CharField(max_length=128, blank=True, default='')
    pin_set_at          = models.DateTimeField(null=True, blank=True)
    pin_failed_attempts = models.PositiveSmallIntegerField(default=0)
    pin_locked_until    = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering        = ['-total_spent']
        verbose_name    = "Customer Loyalty"
        verbose_name_plural = "Customer Loyalties"

    def __str__(self):
        return f"{self.name or 'Unknown'} ({self.phone})"

    @property
    def has_pin(self):
        return bool(self.pin_hash)

    def expiry_months_setting(self):
        return LoyaltySettings.get_settings().points_expiry_months

    def points_expired(self):
        """True kalau poin customer ini harusnya udah hangus berdasarkan
        pengaturan points_expiry_months & order terakhirnya."""
        months = self.expiry_months_setting()
        if not months or not self.last_order_at:
            return False
        cutoff = timezone.now() - relativedelta(months=months)
        return self.last_order_at < cutoff

    def expiry_estimate_date(self):
        """Estimasi kapan poin bakal hangus KALAU customer ngga order lagi."""
        months = self.expiry_months_setting()
        if not months or not self.last_order_at:
            return None
        return self.last_order_at + relativedelta(months=months)

    def check_and_expire_points(self):
        """Pengecekan LAZY — dipanggil pas ada order baru dari customer ini,
        atau pas customer masukin nomor HP di checkout/kasir. Kalau poin
        emang harus hangus, di-nolkan & dicatat sebagai PointAdjustment
        (biar ada jejak, bukan cuma ilang diam-diam)."""
        if self.points > 0 and self.points_expired():
            hangus = self.points
            self.points = 0
            self.save(update_fields=['points'])
            PointAdjustment.objects.create(
                customer=self,
                amount=-hangus,
                reason='expired',
                note=f"Poin hangus otomatis (tidak order sejak {self.last_order_at:%d %b %Y})" if self.last_order_at else "Poin hangus otomatis",
                admin_name='system',
            )
            return True
        return False


# ─────────────────────────────────────────────
# POINT REWARD  (tukar poin loyalty → menu gratis)
# ─────────────────────────────────────────────
# point_cost diatur MANUAL oleh admin per menu (bukan rumus otomatis),
# karena cuma admin yang tau HPP tiap menu. Menu HPP kecil → point_cost
# rendah, menu HPP mahal → point_cost tinggi atau ngga usah dimasukin sama sekali.
class PointReward(models.Model):
    menu = models.ForeignKey(
        Menu, on_delete=models.CASCADE, related_name='point_rewards',
    )
    point_cost = models.PositiveIntegerField(
        help_text="Jumlah poin yang dibutuhkan buat nuker 1 menu ini",
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['point_cost']
        verbose_name = "Point Reward"
        verbose_name_plural = "Point Rewards"

    def __str__(self):
        return f"{self.menu.name} — {self.point_cost} poin"


# ─────────────────────────────────────────────
# POINT ADJUSTMENT  (log audit — otomatis maupun manual admin)
# ─────────────────────────────────────────────
# Setiap perubahan poin di luar transaksi normal (hangus otomatis, atau
# admin nambah/kurangin manual) dicatat di sini — biar ada jejak jelas
# "kenapa" saldo poin seorang customer berubah, bukan cuma angka yang
# tiba-tiba beda tanpa penjelasan.
POINT_ADJUSTMENT_REASON_CHOICES = (
    ('manual',  'Adjust Manual Admin'),
    ('expired', 'Hangus Otomatis'),
)


class PointAdjustment(models.Model):
    customer = models.ForeignKey(
        CustomerLoyalty, on_delete=models.CASCADE, related_name='adjustments',
    )
    amount = models.IntegerField(
        help_text="Positif = nambah poin, negatif = mengurangi/menghanguskan poin",
    )
    reason = models.CharField(max_length=20, choices=POINT_ADJUSTMENT_REASON_CHOICES, default='manual')
    note = models.CharField(max_length=255, blank=True, default='')
    admin_name = models.CharField(
        max_length=100, blank=True, default='',
        help_text="Nama admin yang melakukan adjust, atau 'system' kalau otomatis",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Point Adjustment"
        verbose_name_plural = "Point Adjustments"

    def __str__(self):
        sign = "+" if self.amount >= 0 else ""
        return f"{self.customer.phone} {sign}{self.amount} poin ({self.get_reason_display()})"


# ─────────────────────────────────────────────
# ORDER EVENT (riwayat aksi staff / sistem per order)
# ─────────────────────────────────────────────
# Satu baris = satu kejadian penting pada order: diterima, dibatalkan, siap, pengingat, dst.
# Dipakai untuk (1) timeline di struk Active Orders, (2) mencegah pengingat dobel,
# (3) audit "siapa menekan apa, dari mana" (admin web atau Telegram),
# (4) hitungan kinerja di ringkasan staff (waktu respons terima/siap).

ORDER_EVENT_ACTION_CHOICES = (
    ('accepted',       'Diterima'),
    ('paid',           'Dilunasi'),
    ('cancelled',      'Dibatalkan'),
    ('auto_cancelled', 'Dibatalkan otomatis'),
    ('ready',          'Siap diambil'),
    ('unready',        'Tanda siap dicabut'),
    ('reminded',       'Pengingat dikirim'),
    ('refunded',       'Refund diserahkan'),
    ('blocked',        'Nomor diblokir'),
    ('unblocked',      'Blokir dibuka'),
)

ORDER_EVENT_CHANNEL_CHOICES = (
    ('staff',    'Aplikasi admin'),
    ('telegram', 'Telegram'),
    ('system',   'Sistem'),
)


class OrderEvent(models.Model):
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='events')
    action     = models.CharField(max_length=20, choices=ORDER_EVENT_ACTION_CHOICES)
    actor      = models.CharField(max_length=100, blank=True, default='')
    channel    = models.CharField(max_length=10, choices=ORDER_EVENT_CHANNEL_CHOICES, default='staff')
    note       = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at', 'id']
        indexes = [
            models.Index(fields=['order', 'action'], name='orderevent_order_action_idx'),
            models.Index(fields=['created_at'], name='orderevent_created_idx'),
        ]

    def __str__(self):
        return f"{self.order_id} {self.action} oleh {self.actor or '-'} ({self.channel})"


# ─────────────────────────────────────────────
# DAFTAR BLOKIR (anti-scam)
# ─────────────────────────────────────────────
# Diisi lewat tombol "🚫 Blokir" / perintah /blokir di Telegram (lihat blocklist.py).
#   phone → pesanan web dari nomor ini DITOLAK total.
#   ip    → pesanan cash dari IP ini dipaksa QRIS (tidak ditolak: IP bisa dipakai bersama banyak orang).
# Blokir IP kedaluwarsa otomatis (blocklist.IP_BLOCK_DAYS) karena IP sering berganti pemilik.
class BlockedContact(models.Model):
    KIND_CHOICES = (('phone', 'Nomor WA'), ('ip', 'IP'))

    kind       = models.CharField(max_length=5, choices=KIND_CHOICES)
    value      = models.CharField(max_length=64, db_index=True)
    is_active  = models.BooleanField(default=True)
    reason     = models.CharField(max_length=255, blank=True, default='')
    blocked_by = models.CharField(max_length=100, blank=True, default='')
    order_number = models.CharField(max_length=40, blank=True, default='')   # order yang memicu blokir
    blocked_at = models.DateTimeField(default=timezone.now)
    unblocked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [('kind', 'value')]
        ordering = ['-blocked_at']

    def __str__(self):
        return f"{self.kind}:{self.value} ({'aktif' if self.is_active else 'dibuka'})"


# ─────────────────────────────────────────────
# SIGNALS
# ─────────────────────────────────────────────

@receiver(pre_save, sender=Order)
def _track_previous_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._previous_status = Order.objects.get(pk=instance.pk).status
        except Order.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Order)
def _update_loyalty_on_complete(sender, instance, created, **kwargs):
    previous_status = getattr(instance, '_previous_status', None)

    if not (
        instance.status == 'completed'
        and previous_status != 'completed'
        and instance.customer_phone
    ):
        return

    with transaction.atomic():
        # "Klaim" order ini secara atomik: cuma satu proses yang bisa ngubah
        # loyalty_applied False -> True. Kalau sudah pernah di-apply (mis.
        # status bolak-balik atau signal kepanggil dua kali), poin TIDAK
        # ditambah lagi. update() juga gak retrigger post_save.
        claimed = Order.objects.filter(pk=instance.pk, loyalty_applied=False).update(loyalty_applied=True)
        if not claimed:
            return

        CustomerLoyalty.objects.get_or_create(
            phone=instance.customer_phone,
            defaults={'name': instance.customer_name},
        )
        # Lock row biar dua order customer yang sama selesai barengan gak saling timpa saldo.
        loyalty = CustomerLoyalty.objects.select_for_update().get(phone=instance.customer_phone)

        # Cek kedaluwarsa poin LAMA dulu (berdasarkan last_order_at SEBELUM
        # order ini) sebelum poin baru ditambahkan.
        loyalty.check_and_expire_points()

        rupiah_per_point = LoyaltySettings.get_settings().rupiah_per_point or 10000
        earned_points         = int(instance.total_price // rupiah_per_point)
        loyalty.points       += earned_points
        loyalty.total_spent  += instance.total_price
        loyalty.total_orders += 1
        # Jangan mundurkan last_order_at: order input susulan (created_at lebih
        # lama dari order terakhir customer) tidak boleh memajukan masa hangus poin.
        if not loyalty.last_order_at or instance.created_at > loyalty.last_order_at:
            loyalty.last_order_at = instance.created_at

        if instance.customer_name and not loyalty.name:
            loyalty.name = instance.customer_name

        loyalty.save()

        Order.objects.filter(pk=instance.pk).update(loyalty_points_earned=earned_points)


def generate_order_number(for_dt=None):
    # Tanggal diambil dari waktu WIB milik for_dt; default: sekarang.
    dt = for_dt or timezone.now()
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt, WIB)
    date_part = dt.strftime("%y%m%d")

    while True:
        random_part = "".join(
            random.choices(
                string.ascii_uppercase + string.digits,
                k=4
            )
        )

        code = f"MSM-{date_part}-{random_part}"

        if not Order.objects.filter(order_number=code).exists():
            return code

class StoreSettings(models.Model):
    """
    Singleton — selalu pakai pk=1.
    Simpan semua konfigurasi toko: WA admin, jam operasional, override manual.
    """
 
    admin_whatsapp = models.CharField(
        max_length=20, blank=True, default="",
        help_text="Nomor WA admin format internasional tanpa +, cth: 628xxx"
    )
 
    # null = ikut jadwal | True = paksa buka | False = paksa tutup
    is_open_override = models.BooleanField(
        null=True, blank=True, default=None,
        help_text="null=jadwal, True=paksa buka, False=paksa tutup"
    )
 
    closed_message = models.TextField(
        default="Maaf, kami sedang tidak beroperasi. Silakan kembali sesuai jam operasional kami.",
        help_text="Pesan yang ditampilkan saat toko tutup"
    )
 
    # Format JSON:
    # {
    #   "0": {"open": "08:00", "close": "22:00"},   ← Senin
    #   "1": {"open": "08:00", "close": "22:00"},   ← Selasa
    #   ...
    #   "6": null                                    ← Minggu libur (atau tidak ada key-nya)
    # }
    # Key: 0=Senin, 1=Selasa, ..., 6=Minggu
    operating_hours = models.JSONField(
        default=dict, blank=True,
        help_text="Jadwal per hari. Key 0-6 (0=Senin), value: {open, close} atau null"
    )
 
    # ── Indikator keramaian (badge Santai / Sedang / Ramai di halaman Menu) ──
    # Saklar utama: False = badge disembunyikan total, apa pun mode-nya.
    crowd_indicator_enabled = models.BooleanField(
        default=True,
        help_text="False = badge keramaian tidak ditampilkan ke pelanggan",
    )
    # Mode manual: level yang dipilih kasir/owner + batas waktunya. Masa berlaku
    # disimpan sebagai "berlaku sampai jam X" dan dicek saat dibaca (tanpa cron,
    # cocok untuk serverless). Lewat waktunya -> otomatis kembali ke mode otomatis.
    crowd_manual_level = models.CharField(
        max_length=10, blank=True, default="",
        choices=(("santai", "Santai"), ("sedang", "Sedang"), ("ramai", "Ramai")),
        help_text="Kosong = mode otomatis",
    )
    crowd_manual_until = models.DateTimeField(
        null=True, blank=True,
        help_text="Level manual berlaku sampai waktu ini",
    )

    # ── Target omzet bulanan (Strip Briefing & Target vs Realisasi di Dashboard) ──
    # Kosong/0 = belum ada target. Rupiah utuh, tanpa desimal.
    monthly_revenue_target = models.PositiveBigIntegerField(
        null=True, blank=True,
        help_text="Target omzet per bulan (Rp). Kosong = belum diatur",
    )

    # Batas "telat": order yang belum ditandai siap lebih lama dari ini dianggap telat.
    order_late_minutes = models.PositiveSmallIntegerField(
        default=20,
        help_text="Menit sejak order masuk sampai dianggap telat kalau belum siap diambil",
    )

    updated_at = models.DateTimeField(auto_now=True)
 
    class Meta:
        verbose_name        = "Store Settings"
        verbose_name_plural = "Store Settings"
 
    def __str__(self):
        return "Store Settings"
 
    def save(self, *args, **kwargs):
        self.pk = 1   # Singleton
        super().save(*args, **kwargs)
 
    def delete(self, *args, **kwargs):
        pass  # Jangan hapus row ini
 
    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj