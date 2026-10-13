import re
import cloudinary.uploader
from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from cloudinary.exceptions import Error as CloudinaryError


# ==================================================================
# PILIHAN UNTUK PROMO & EVENT
# ==================================================================
PROMO_RATIO_CHOICES = [
    ("16:9", "16:9 Landscape"),
    ("21:9", "21:9 Ultrawide"),
    ("4:3",  "4:3 Klasik"),
    ("1:1",  "1:1 Kotak"),
    ("4:5",  "4:5 Portrait"),
    ("3:4",  "3:4 Portrait"),
    ("9:16", "9:16 Story"),
]
PROMO_LAYOUT_CHOICES = [
    ("split",   "Gambar + Teks berdampingan"),
    ("overlay", "Teks di atas Gambar"),
    ("poster",  "Poster (gambar utuh, teks di bawah)"),
]
PROMO_SIDE_CHOICES = [("left", "Gambar di kiri"), ("right", "Gambar di kanan")]
PROMO_FOCUS_CHOICES = [
    ("top-left", "Kiri atas"), ("top", "Atas"), ("top-right", "Kanan atas"),
    ("left", "Kiri"), ("center", "Tengah"), ("right", "Kanan"),
    ("bottom-left", "Kiri bawah"), ("bottom", "Bawah"), ("bottom-right", "Kanan bawah"),
]
PROMO_THEME_CHOICES = [
    ("red", "Merah"), ("amber", "Kuning"), ("emerald", "Hijau"),
    ("sky", "Biru"), ("violet", "Ungu"), ("pink", "Pink"),
]
PROMO_ALIGN_CHOICES = [("left", "Rata kiri"), ("center", "Tengah")]


# 1. TABEL UTAMA KONFIGURASI HOMEPAGE
class HomepageConfig(models.Model):
    # Hero Section
    hero_headline = models.CharField(max_length=255, default="Warkop Level Up Masashimura", blank=True, null=True)
    hero_subheadline = models.TextField(default="Tempat nongkrong kasual modern di Bekasi dengan cita rasa nikmat.", blank=True, null=True)
    hero_food_image = models.URLField(max_length=500, blank=True, null=True)
    hero_bg_image = models.URLField(max_length=500, blank=True, null=True, help_text="Foto background parallax hero (16:9)")

    # Marquee Text
    marquee_text = models.TextField(default="MASA SIH MURAH? • WARKOP EVOLUTION • GOOD FOOD • GOOD VIBES", blank=True, null=True)

    # Tentang / About
    about_text = models.TextField(default="Masashimura adalah sebuah usaha kuliner personal asal Bekasi...", blank=True, null=True)
    about_image = models.URLField(max_length=500, blank=True, null=True)

    # Metrics Data
    metric_1 = models.CharField(max_length=50, default="2024", blank=True, null=True)
    metric_2 = models.CharField(max_length=50, default="50+", blank=True, null=True)
    metric_3 = models.CharField(max_length=50, default="★★★★★", blank=True, null=True)

    # ── Promo & Event ───────────────────────────────────────────────
    # Judul, keterangan, DAN gambar kosong = banner promo tidak tampil.
    promo_badge = models.CharField(max_length=30, blank=True, default="", help_text="Label kecil di atas judul, contoh: Promo, Event, Baru")
    promo_title = models.CharField(max_length=120, blank=True, default="")
    promo_text = models.CharField(max_length=255, blank=True, default="")
    promo_link = models.CharField(max_length=300, blank=True, default="", help_text="'/menu' (halaman sendiri) atau 'https://...' (link luar)")
    promo_link_label = models.CharField(max_length=40, blank=True, default="")

    # Gambar & tampilan
    promo_image = models.URLField(max_length=500, blank=True, null=True)
    promo_image_alt = models.CharField(max_length=150, blank=True, default="")
    promo_image_ratio = models.CharField(max_length=5, choices=PROMO_RATIO_CHOICES, default="16:9")
    promo_layout = models.CharField(max_length=10, choices=PROMO_LAYOUT_CHOICES, default="split")
    promo_image_side = models.CharField(max_length=5, choices=PROMO_SIDE_CHOICES, default="left")
    promo_focus = models.CharField(max_length=15, choices=PROMO_FOCUS_CHOICES, default="center")
    promo_theme = models.CharField(max_length=10, choices=PROMO_THEME_CHOICES, default="red")
    promo_align = models.CharField(max_length=6, choices=PROMO_ALIGN_CHOICES, default="left")
    promo_overlay = models.PositiveSmallIntegerField(default=55, validators=[MaxValueValidator(90)], help_text="Gelap overlay 0-90 (layout 'overlay')")

    # Jadwal & perilaku
    promo_from = models.DateField(null=True, blank=True, help_text="Mulai tayang (opsional)")
    promo_until = models.DateField(null=True, blank=True, help_text="Tayang sampai akhir hari ini WIB (opsional)")
    promo_countdown = models.BooleanField(default=False, help_text="Tampilkan hitung mundur sisa waktu")
    promo_dismissible = models.BooleanField(default=False, help_text="Pengunjung boleh menutup banner")

    class Meta:
        verbose_name = "Homepage Configuration"

    def __str__(self):
        return "Konfigurasi Halaman Depan Masashimura"


# 1b. PROMO & EVENT (maksimal PROMO_MAX_ITEMS, diurutkan lewat field `order`)
PROMO_MAX_ITEMS = 5


class PromoItem(models.Model):
    # Isi
    badge = models.CharField(max_length=30, blank=True, default="", help_text="Label kecil di atas judul, contoh: Promo, Event, Baru")
    title = models.CharField(max_length=120, blank=True, default="")
    text = models.CharField(max_length=255, blank=True, default="")
    link = models.CharField(max_length=300, blank=True, default="", help_text="'/menu' (halaman sendiri) atau 'https://...' (link luar)")
    link_label = models.CharField(max_length=40, blank=True, default="")

    # Gambar & tampilan
    image = models.URLField(max_length=500, blank=True, null=True)
    image_alt = models.CharField(max_length=150, blank=True, default="")
    image_ratio = models.CharField(max_length=5, choices=PROMO_RATIO_CHOICES, default="16:9")
    layout = models.CharField(max_length=10, choices=PROMO_LAYOUT_CHOICES, default="split")
    image_side = models.CharField(max_length=5, choices=PROMO_SIDE_CHOICES, default="left")
    focus = models.CharField(max_length=15, choices=PROMO_FOCUS_CHOICES, default="center")
    theme = models.CharField(max_length=10, choices=PROMO_THEME_CHOICES, default="red")
    align = models.CharField(max_length=6, choices=PROMO_ALIGN_CHOICES, default="left")
    overlay = models.PositiveSmallIntegerField(default=55, validators=[MaxValueValidator(90)])

    # Jadwal & perilaku
    show_from = models.DateField(null=True, blank=True, help_text="Mulai tayang (opsional)")
    show_until = models.DateField(null=True, blank=True, help_text="Tayang sampai akhir hari WIB (opsional)")
    countdown = models.BooleanField(default=False)
    dismissible = models.BooleanField(default=False)

    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Promo & Event"
        verbose_name_plural = "Promo & Event"

    def __str__(self):
        return self.title or f"Promo #{self.pk}"


# 2. TABEL BENTO GRID FASILITAS
class BentoFacility(models.Model):
    SIZE_CHOICES = [
        ('normal', 'Standard Card (1x1)'),
        ('large', 'Large Card (2x2)'),
    ]

    title = models.CharField(max_length=100)
    icon_name = models.CharField(max_length=50, default="Wifi", help_text="Nama icon Lucide (contoh: Wifi, Coffee, Zap, Utensils, DollarSign, Moon)")
    size = models.CharField(max_length=10, choices=SIZE_CHOICES, default='normal', help_text="Mengatur tata ruang kotak di frontend")
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']


# 3. TABEL GALERI / LOOKBOOK
class GalleryLookbook(models.Model):
    title = models.CharField(max_length=100, blank=True, null=True, help_text="Nama produk pakaian atau judul foto suasana")
    image_url = models.URLField(max_length=500, help_text="Link URL gambar secure dari Cloudinary")
    category = models.CharField(max_length=50, default="General", help_text="Kategori (misal: 'Suasana Kedai', 'Lookbook Kalren', 'Best Seller')")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Gallery Lookbook"
        verbose_name_plural = "Gallery Lookbooks"

    def __str__(self):
        return self.title if self.title else f"Foto Galeri #{self.id}"


# ==================================================================
# 🛠️ UTILITY HELPER FOR CLOUDINARY CLEANUP
# ==================================================================
def get_cloudinary_public_id(url):
    if not url:
        return None
    match = re.search(r'/upload/(?:v\d+/)?([^.]+)', url)
    if match:
        return match.group(1)
    return None


def destroy_cloudinary_asset(url):
    """Hapus aset di Cloudinary. Kegagalan di sini TIDAK boleh membatalkan proses simpan di DB."""
    pid = get_cloudinary_public_id(url)
    if not pid:
        return
    try:
        cloudinary.uploader.destroy(pid)
    except CloudinaryError as e:
        print(f"[Cloudinary] Gagal menghapus aset di cloud ({pid}): {e}")
    except Exception as e:
        print(f"[System] Error tak terduga saat menghapus aset ({pid}): {e}")


# ==================================================================
# 🔥 DJANGO SIGNALS (PEMBERSIH SAMPAH CLOUDINARY OTOMATIS)
# ==================================================================
HOMEPAGE_IMAGE_FIELDS = ("hero_food_image", "hero_bg_image", "about_image", "promo_image")


# A. Gambar HomepageConfig yang diganti/dikosongkan ikut dihapus dari Cloudinary,
#    kecuali URL-nya masih dipakai di kolom gambar lain pada record yang sama.
@receiver(pre_save, sender=HomepageConfig)
def clean_old_homepage_images(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = HomepageConfig.objects.get(pk=instance.pk)
    except HomepageConfig.DoesNotExist:
        return

    still_used = {getattr(instance, f) for f in HOMEPAGE_IMAGE_FIELDS}
    for field in HOMEPAGE_IMAGE_FIELDS:
        old_url = getattr(old, field)
        if old_url and old_url not in still_used:
            destroy_cloudinary_asset(old_url)


# B. Gambar galeri yang diganti
@receiver(pre_save, sender=GalleryLookbook)
def clean_old_gallery_images(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = GalleryLookbook.objects.get(pk=instance.pk)
    except GalleryLookbook.DoesNotExist:
        return
    if old.image_url and old.image_url != instance.image_url:
        destroy_cloudinary_asset(old.image_url)


# C. Record galeri dihapus total
@receiver(post_delete, sender=GalleryLookbook)
def delete_cloudinary_image_on_record_delete(sender, instance, **kwargs):
    if instance.image_url:
        print(f"[Cloudinary] Menghapus aset karena record dihapus: {get_cloudinary_public_id(instance.image_url)}")
        destroy_cloudinary_asset(instance.image_url)


# D. Gambar promo diganti / promo dihapus -> hapus aset lama di Cloudinary
@receiver(pre_save, sender=PromoItem)
def clean_old_promo_image(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = PromoItem.objects.get(pk=instance.pk)
    except PromoItem.DoesNotExist:
        return
    if old.image and old.image != instance.image:
        destroy_cloudinary_asset(old.image)


@receiver(post_delete, sender=PromoItem)
def delete_promo_image_on_record_delete(sender, instance, **kwargs):
    if instance.image:
        destroy_cloudinary_asset(instance.image)