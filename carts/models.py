import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models


class Cart(models.Model):
    """Shopping cart for a user."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    date_created = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'Cart for {self.user.email}'

    @property
    def total_price(self):
        """Calculate cart total from items."""
        return sum(
            Decimal(item.subtotal) for item in self.items.all()
        ) or Decimal('0.00')

    @property
    def products(self):
        """Return list of cart items formatted for API response."""
        return list(self.items.all())


class CartItem(models.Model):
    """Item in a shopping cart."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')
        ordering = ['-added_at']

    def __str__(self):
        return f'{self.product.name} (qty: {self.quantity})'

    @property
    def subtotal(self):
        """Total for this line item."""
        return self.quantity * self.unit_price

    @property
    def product_id(self):
        return str(self.product.id)

    @property
    def product_name(self):
        return self.product.name

    @property
    def product_image(self):
        return getattr(self.product, 'image_url', '')
