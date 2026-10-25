from django.utils import timezone
import math
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
import cloudinary.uploader
from cloudinary.models import CloudinaryField


class Category(models.Model):
    GROUP_CHOICES = [
        ("makanan", "Makanan"),
        ("snack", "Snack"),
        ("minuman", "Minuman"),
    ]

    name = models.CharField(max_length=50, unique=True)
    group = models.CharField(
        max_length=20,
        choices=GROUP_CHOICES,
        default="makanan"
    )

    def __str__(self):
        return self.name


class Menu(models.Model):
    name        = models.CharField(max_length=100)
    category    = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    price       = models.DecimalField(
        max_digits=10, decimal_places=0,
        validators=[MinValueValidator(1)],
    )
    price_web   = models.DecimalField(max_digits=10, decimal_places=0, editable=False, default=0)
    description = models.TextField(blank=True, null=True)
    is_available = models.BooleanField(default=True)
    is_active    = models.BooleanField(default=True)
    image        = CloudinaryField('image', folder='menus/', null=True, blank=True)

    # Badge jempol di halaman Menu. Diatur manual owner (beda dari "Terlaris" yang otomatis).
    is_recommended = models.BooleanField(default=False)

    # Waktu menu dibuat, buat badge "Baru". Kosong untuk menu lama (sebelum field ini ada),
    # supaya semua menu lama tidak mendadak dianggap baru.
    created_at = models.DateTimeField(null=True, blank=True, editable=False)

    # Secret menu: hanya muncul di POS (New Order), TIDAK dikirim ke publik
    # dan TIDAK bisa dipesan lewat web. Filternya di views + create_order.
    is_secret = models.BooleanField(default=False)

    # Opsi pilihan per menu (pedas, suhu, add-on, dll). Struktur & validasi: menu/options.py
    # [{"name": "Level Pedas", "required": true, "multiple": false,
    #   "choices": [{"label": "Sedeng", "price": 0}, ...]}]
    options = models.JSONField(default=list, blank=True)

    def save(self, *args, **kwargs):
        if self._state.adding and not self.created_at:
            self.created_at = timezone.now()
        self.price_web = math.ceil((float(self.price) * 1.01) / 500) * 500
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


@receiver(post_delete, sender=Menu)
def delete_cloudinary_image_on_delete(sender, instance, **kwargs):
    if instance.image:
        try:
            cloudinary.uploader.destroy(instance.image.public_id)
        except Exception as e:
            print(f"[Cloudinary] Gagal hapus gambar Menu id={instance.pk}: {e}")


# ─────────────────────────────────────────────
# MENU PAKET (BUNDLING)
# ─────────────────────────────────────────────
# Admin hanya mengisi HARGA PAKET. Harga normal & potongan dihitung sistem dari harga
# menu saat ini (jadi ikut berubah kalau harga menu berubah). Saat dipesan, paket
# "dipecah" jadi OrderItem biasa (lihat menu/bundles.py), jadi riwayat order tidak
# bergantung pada paket ini dan paket aman dihapus kapan saja.
class MenuBundle(models.Model):
    name        = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    price       = models.DecimalField(
        max_digits=10, decimal_places=0, validators=[MinValueValidator(1)],
        help_text="Harga paket di POS. Harga web mengikuti aturan markup yang sama dengan menu.",
    )
    is_available = models.BooleanField(default=True, help_text="Saklar manual tersedia/habis")
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class MenuBundleItem(models.Model):
    bundle   = models.ForeignKey(MenuBundle, on_delete=models.CASCADE, related_name="items")
    # PROTECT: menu yang masih ada di paket tidak boleh terhapus diam-diam.
    menu     = models.ForeignKey(Menu, on_delete=models.PROTECT, related_name="bundle_items")
    quantity = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(fields=["bundle", "menu"], name="uniq_bundle_menu"),
        ]

    def __str__(self):
        return f"{self.bundle.name}: {self.menu.name} x{self.quantity}"
