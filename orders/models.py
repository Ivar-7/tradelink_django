import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models


class OrderStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    CONFIRMED = 'confirmed', 'Confirmed'
    SHIPPED = 'shipped', 'Shipped'
    OUT_FOR_DELIVERY = 'out_for_delivery', 'Out for Delivery'
    DELIVERED = 'delivered', 'Delivered'
    CANCELLED = 'cancelled', 'Cancelled'


class ShippingMethod(models.TextChoices):
    PICKUP = 'pickup', 'Pickup'
    DELIVERY = 'delivery', 'Delivery'


class ReturnStatus(models.TextChoices):
    REQUESTED = 'requested', 'Requested'
    APPROVED = 'approved', 'Approved'
    SHIPPED_BACK = 'shipped_back', 'Shipped Back'
    REFUNDED = 'refunded', 'Refunded'


class Order(models.Model):
    """Customer order."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    order_date = models.DateTimeField(auto_now_add=True)
    order_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )
    shipping_method = models.CharField(
        max_length=20,
        choices=ShippingMethod.choices
    )
    tracking_number = models.CharField(max_length=100, null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-order_date']

    def __str__(self):
        return f'Order {self.id} - {self.user.email}'

    @property
    def products(self):
        """Return list of order items formatted for API response."""
        return list(self.items.all())


class OrderItem(models.Model):
    """Item in an order."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items'
    )
    product_name = models.CharField(max_length=255)
    product_image = models.URLField(blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    # CRITICAL: Links this item to the vendor who sold it
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='sold_items',
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['id']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['vendor']),
        ]

    def __str__(self):
        return f'{self.product_name} (qty: {self.quantity})'

    @property
    def product_id(self):
        return str(self.product.id) if self.product else None

    @property
    def vendor_id(self):
        return str(self.vendor.id) if self.vendor else None

    @property
    def subtotal(self):
        return self.quantity * self.unit_price


class OrderSuborder(models.Model):
    """Suborder for each vendor in a multi-vendor order."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='suborders'
    )
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='vendor_suborders'
    )
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('order', 'vendor')
        indexes = [
            models.Index(fields=['vendor', '-created_at']),
        ]

    def __str__(self):
        return f'Suborder {self.id} - Vendor {self.vendor.email}'


class Shipment(models.Model):
    """Shipment tracking for an order."""
    SHIPMENT_STATUS = [
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='shipment'
    )
    external_package_id = models.CharField(max_length=255, blank=True)
    tracking_number = models.CharField(max_length=255, unique=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=SHIPMENT_STATUS, default='pending')
    pickup_time = models.DateTimeField(null=True, blank=True)
    last_update_time = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tracking_number']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'Shipment {self.tracking_number} - {self.status}'


class OrderStatusHistory(models.Model):
    """Audit trail for order and suborder status transitions."""
    ROLE_CHOICES = [
        ('buyer', 'Buyer'),
        ('vendor', 'Vendor'),
        ('admin', 'Admin'),
        ('system', 'System'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    suborder = models.ForeignKey(
        OrderSuborder,
        on_delete=models.CASCADE,
        related_name='status_history',
        null=True,
        blank=True
    )
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='order_status_changes'
    )
    changed_by_role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    notes = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', '-created_at']),
            models.Index(fields=['suborder', '-created_at']),
            models.Index(fields=['changed_by_role']),
        ]

    def __str__(self):
        return f'{self.order_id}: {self.old_status} -> {self.new_status}'


class DeliveryAddress(models.Model):
    """Shipping address for an order."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='delivery_address'
    )
    county = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    postal_address = models.CharField(max_length=255)
    user_contact = models.CharField(max_length=20)

    def __str__(self):
        return f'{self.city}, {self.county}'


class OrderIssueReport(models.Model):
    """Issue report for an order."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='issue_report'
    )
    type = models.CharField(max_length=100)
    details = models.TextField()
    reported_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Issue: {self.type} - Order {self.order.id}'


class ReturnRequest(models.Model):
    """Return request for an order."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='return_request'
    )
    status = models.CharField(
        max_length=20,
        choices=ReturnStatus.choices,
        default=ReturnStatus.REQUESTED
    )
    reason = models.TextField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    requested_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    shipped_back_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Return: {self.status} - Order {self.order.id}'

    @property
    def timeline(self):
        return {
            'requested_at': self.requested_at,
            'approved_at': self.approved_at,
            'shipped_back_at': self.shipped_back_at,
            'refunded_at': self.refunded_at,
        }

