from django.db import models
from django.utils import timezone


class Expense(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'Tunai'
        QRIS = 'qris', 'QRIS'

    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    payment_method = models.CharField(
        max_length=10,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
    )
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.date} - {self.description} ({self.get_payment_method_display()}): {self.amount}"