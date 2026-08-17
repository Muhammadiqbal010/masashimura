from django.db import models
from django.conf import settings
from django.utils import timezone


class Promo(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Persentase'),
        ('fixed', 'Nominal Tetap'),
    ]

    code = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=255, blank=True)

    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Cap maksimal diskon (khusus tipe persentase)"
    )
    min_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    max_usage = models.PositiveIntegerField(null=True, blank=True, help_text="Kosongkan = tanpa batas")
    used_count = models.PositiveIntegerField(default=0)

    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    def check_valid(self, subtotal=0):
        """Return (is_valid: bool, message: str)"""
        now = timezone.now()
        if not self.is_active:
            return False, "Kode promo tidak aktif"
        if now < self.valid_from:
            return False, "Promo belum mulai berlaku"
        if now > self.valid_until:
            return False, "Kode promo sudah kedaluwarsa"
        if self.max_usage is not None and self.used_count >= self.max_usage:
            return False, "Kuota promo sudah habis"
        if subtotal < self.min_purchase:
            return False, f"Minimal belanja Rp{self.min_purchase:,.0f}".replace(",", ".")
        return True, ""

    def calculate_discount(self, subtotal):
        if self.discount_type == 'percentage':
            discount = float(subtotal) * (float(self.discount_value) / 100)
            if self.max_discount_amount:
                discount = min(discount, float(self.max_discount_amount))
        else:
            discount = float(self.discount_value)
        return round(min(discount, float(subtotal)), 2)