from django.db import models
from django.db.models.signals import pre_save, post_save
from dateutil.relativedelta import relativedelta
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal
from datetime import datetime
import random
import string

from menu.models import Menu


# ─────────────────────────────────────────────
# CHOICES
# ─────────────────────────────────────────────

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
    ('unpaid',  'Unpaid'),
    ('paid',    'Paid'),
    ('pending', 'Pending'),
    ('void',    'Batal'),
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

class Order(models.Model):
    order_number = models.CharField(max_length=30, unique=True, editable=False, blank=True)

    source         = models.CharField(max_length=10, choices=ORDER_SOURCE_CHOICES, default='web')
    status         = models.CharField(max_length=15, choices=ORDER_STATUS_CHOICES, default='pending')

    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    is_deferred_payment = models.BooleanField(
        default=False,
        help_text='POS: pelanggan makan dulu, bayar nanti',
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

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_number} [{self.get_source_display()}]"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = generate_order_number()
        super().save(*args, **kwargs)

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

    price = models.DecimalField(max_digits=10, decimal_places=0)
    notes = models.CharField(max_length=255, blank=True, default='')

    # True kalau item ini didapat dari tukar poin loyalty (harga selalu 0),
    # dipakai buat nampilin badge "Reward" di struk/admin, bukan cuma nebak dari price=0.
    is_point_redemption = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.menu.name} x{self.quantity}"

    @property
    def subtotal(self):
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        if not self.price:
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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering        = ['-total_spent']
        verbose_name    = "Customer Loyalty"
        verbose_name_plural = "Customer Loyalties"

    def __str__(self):
        return f"{self.name or 'Unknown'} ({self.phone})"

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

    if (
        instance.status == 'completed'
        and previous_status != 'completed'
        and instance.customer_phone
    ):
        loyalty, _ = CustomerLoyalty.objects.get_or_create(
            phone=instance.customer_phone,
            defaults={'name': instance.customer_name},
        )

        # Cek kedaluwarsa poin LAMA dulu (berdasarkan last_order_at SEBELUM
        # order ini) sebelum poin baru ditambahkan — biar poin lama yang
        # emang udah harus hangus ngga ikut "keselamatan" numpang di order baru.
        loyalty.check_and_expire_points()

        rupiah_per_point = LoyaltySettings.get_settings().rupiah_per_point or 10000
        earned_points         = int(instance.total_price // rupiah_per_point)
        loyalty.points       += earned_points
        loyalty.total_spent  += instance.total_price
        loyalty.total_orders += 1
        loyalty.last_order_at = instance.created_at

        if instance.customer_name and not loyalty.name:
            loyalty.name = instance.customer_name

        loyalty.save()


def generate_order_number():
    date_part = datetime.now().strftime("%y%m%d")

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