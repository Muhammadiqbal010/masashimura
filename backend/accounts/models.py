from django.db import models
from django.contrib.auth.models import User

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