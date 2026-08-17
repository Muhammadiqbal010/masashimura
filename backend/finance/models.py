from django.db import models
from django.utils import timezone

class Expense(models.Model):
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.date} - {self.description}: {self.amount}"