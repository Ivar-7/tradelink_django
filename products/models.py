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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['vendor']),
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

