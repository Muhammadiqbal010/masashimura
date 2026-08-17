import math
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
    price       = models.DecimalField(max_digits=10, decimal_places=0)
    price_web   = models.DecimalField(max_digits=10, decimal_places=0, editable=False, default=0)
    description = models.TextField(blank=True, null=True)
    is_available = models.BooleanField(default=True)
    is_active    = models.BooleanField(default=True)
    image        = CloudinaryField('image', folder='menus/', null=True, blank=True)

    def save(self, *args, **kwargs):
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