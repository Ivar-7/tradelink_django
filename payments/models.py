from decimal import Decimal

from django.conf import settings
from django.db import models


class PaymentStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'


class Payment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments'
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        db_column='order_id',
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    payment_provider = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        order_id = self.order_id if self.order_id else 'none'
        return f'{self.pk} - order:{order_id} - {self.payment_provider} - {self.amount}'

