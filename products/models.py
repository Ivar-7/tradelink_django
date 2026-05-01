import uuid
from django.conf import settings
from django.db import models
from decimal import Decimal


class Product(models.Model):
    """Product in the marketplace."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[])
    stock_quantity = models.PositiveIntegerField(default=0)
    image_url = models.URLField(blank=True)
    category = models.ForeignKey(
        'product_categories.ProductCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='products',
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)  # Vendor can deactivate, suspended vendors products hidden
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['vendor']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    @property
    def category_id(self):
        return str(self.category.id) if self.category else None

    @property
    def vendor_id(self):
        return str(self.vendor.id) if self.vendor else None

    @property
    def vendor_name(self):
        return self.vendor.username if self.vendor else None

    @property
    def average_rating(self):
        """Calculate average rating from reviews."""
        reviews = self.reviews.all()
        if not reviews:
            return None
        total = sum(r.rating_value for r in reviews)
        return round(total / len(reviews), 2)

    @property
    def review_count(self):
        """Number of reviews."""
        return self.reviews.count()


class Stock(models.Model):
    """Inventory stock for a product by vendor."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_entries'
    )
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stock_items'
    )
    quantity = models.PositiveIntegerField(default=0)
    reserved_quantity = models.PositiveIntegerField(default=0)  # Quantity in pending orders
    price = models.DecimalField(max_digits=12, decimal_places=2)
    is_flash_sale = models.BooleanField(default=False)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'vendor')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vendor']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f'Stock: {self.product.name} ({self.quantity} units)'

    @property
    def available_quantity(self):
        """Available for sale (not reserved)."""
        return self.quantity - self.reserved_quantity

    @property
    def discounted_price(self):
        """Price after discount."""
        if self.discount_percentage == 0:
            return self.price
        discount = self.price * (self.discount_percentage / Decimal('100'))
        return self.price - discount


class InventoryMovement(models.Model):
    """Audit trail for inventory changes."""
    MOVEMENT_TYPES = [
        ('sale', 'Sale'),
        ('return', 'Return'),
        ('restock', 'Restock'),
        ('adjustment', 'Adjustment'),
        ('cancellation', 'Order Cancellation'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='movements'
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity_change = models.IntegerField()  # Positive or negative
    previous_quantity = models.PositiveIntegerField()
    new_quantity = models.PositiveIntegerField()
    reference_id = models.UUIDField()  # order_id, return_id, etc.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stock']),
            models.Index(fields=['reference_id']),
        ]

    def __str__(self):
        return f'{self.movement_type}: {self.quantity_change} units'

