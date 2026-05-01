from decimal import Decimal

from django.conf import settings
from django.db import models
import uuid


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


class VendorWallet(models.Model):
    """Wallet for vendor earnings."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vendor_wallet'
    )
    available_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    pending_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_withdrawn = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    last_payout_date = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['vendor']),
        ]

    def __str__(self):
        return f'Wallet: {self.vendor.email} - Available: {self.available_balance}'


class VendorPayout(models.Model):
    """Payout history for vendors."""
    PAYOUT_STATUS = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payouts'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYOUT_STATUS, default='pending')
    payout_method = models.CharField(max_length=50)  # 'mpesa', 'bank_transfer', etc.
    transaction_reference = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vendor', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'Payout {self.id} - {self.vendor.email} - {self.amount}'

