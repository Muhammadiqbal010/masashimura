from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('kasir', 'Kasir'),
        ('pelanggan', 'Pelanggan'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='pelanggan')
    phone = models.CharField(max_length=15, blank=True, null=True)

    # PIN keamanan — dipakai staff buat reset password sendiri tanpa
    # perlu owner. Disimpan HASHED, bukan plain text — sama prinsipnya
    # kaya password. Cuma diisi buat staff (owner/admin/kasir), pelanggan
    # gak perlu ini.
    security_pin = models.CharField(max_length=128, blank=True, default="")

    def set_pin(self, raw_pin):
        self.security_pin = make_password(raw_pin)

    def check_pin(self, raw_pin):
        if not self.security_pin:
            return False
        return check_password(raw_pin, self.security_pin)

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def is_owner(self): return self.role == 'owner'
    @property
    def is_admin(self): return self.role == 'admin'
    @property
    def is_kasir(self): return self.role == 'kasir'
    @property
    def is_pelanggan(self): return self.role == 'pelanggan'

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"