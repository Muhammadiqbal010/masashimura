import re
import cloudinary.uploader
from django.db import models
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from cloudinary.exceptions import Error as CloudinaryError

# 1. TABEL UTAMA KONFIGURASI HOMEPAGE
class HomepageConfig(models.Model):
    # Hero Section
    hero_headline = models.CharField(max_length=255, default="Warkop Level Up Masashimura", blank=True, null=True)
    hero_subheadline = models.TextField(default="Tempat nongkrong kasual modern di Bekasi dengan cita rasa nikmat.", blank=True, null=True)
    hero_food_image = models.URLField(max_length=500, blank=True, null=True)
    hero_bg_image = models.URLField(blank=True, null=True, help_text="Foto background parallax hero (16:9)")
    
    # Marquee Text
    marquee_text = models.TextField(default="MASA SIH MURAH? • WARKOP EVOLUTION • GOOD FOOD • GOOD VIBES", blank=True, null=True)
    
    # Tentang / About
    about_text = models.TextField(default="Masashimura adalah sebuah usaha kuliner personal asal Bekasi...", blank=True, null=True)
    about_image = models.URLField(max_length=500, blank=True, null=True)
    
    # Metrics Data
    metric_1 = models.CharField(max_length=50, default="2024", blank=True, null=True)
    metric_2 = models.CharField(max_length=50, default="50+", blank=True, null=True)
    metric_3 = models.CharField(max_length=50, default="★★★★★", blank=True, null=True)

    class Meta:
        verbose_name = "Homepage Configuration"

    def __str__(self):
        return "Konfigurasi Halaman Depan Masashimura"


# 2. TABEL BARU: BENTO GRID FASILITAS (Dinamis: Bisa Tambah / Kurang / Ganti Icon)
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


# 3. TABEL BARU: GALERI / LOOKBOOK (Dinamis: Bisa Upload Banyak Foto, Masashimura / KALREN Style)
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


# ==================================================================
# 🔥 DJANGO SIGNALS (PEMBERSIH SAMPAH CLOUDINARY OTOMATIS)
# ==================================================================

# A. Pembersihan Gambar Di HomepageConfig saat Diupdate
@receiver(pre_save, sender=HomepageConfig)
def clean_old_homepage_images(sender, instance, **kwargs):
    if not instance.pk: return
    try:
        old = HomepageConfig.objects.get(pk=instance.pk)
        if old.hero_food_image and old.hero_food_image != instance.hero_food_image:
            pid = get_cloudinary_public_id(old.hero_food_image)
            if pid: cloudinary.uploader.destroy(pid)
        if old.about_image and old.about_image != instance.about_image:
            pid = get_cloudinary_public_id(old.about_image)
            if pid: cloudinary.uploader.destroy(pid)
    except HomepageConfig.DoesNotExist: pass

# B. Pembersihan Gambar Galeri saat Diupdate/Diganti gambarnya
@receiver(pre_save, sender=GalleryLookbook)
def clean_old_gallery_images(sender, instance, **kwargs):
    if not instance.pk: return
    try:
        old = GalleryLookbook.objects.get(pk=instance.pk)
        if old.image_url and old.image_url != instance.image_url:
            pid = get_cloudinary_public_id(old.image_url)
            if pid: cloudinary.uploader.destroy(pid)
    except GalleryLookbook.DoesNotExist: pass

# C. Pembersihan Gambar Galeri dari Cloudinary jika data/fotonya DIHAPUS TOTAL oleh admin
@receiver(post_delete, sender=GalleryLookbook)
def delete_cloudinary_image_on_record_delete(sender, instance, **kwargs):
    if instance.image_url:
        pid = get_cloudinary_public_id(instance.image_url)
        if pid:
            try:
                print(f"[Cloudinary] Menghapus aset dari Cloud karena data record dihapus: {pid}")
                # Melakukan penghapusan
                cloudinary.uploader.destroy(pid)
            except CloudinaryError as e:
                # Menangkap error Cloudinary tanpa membatalkan proses hapus record di DB
                print(f"[Cloudinary] Gagal menghapus aset di cloud: {e}")
            except Exception as e:
                # Menangkap error lain yang tidak terduga
                print(f"[System] Error tak terduga saat menghapus aset: {e}")