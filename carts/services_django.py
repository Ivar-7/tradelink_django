from decimal import Decimal
from django.db import transaction
from products.models import Stock, Product
from .models import Cart, CartItem


class CartService:
    """Service for cart management operations."""
    
    @staticmethod
    def get_or_create_cart(user):
        """Get or create cart for user."""
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart
    
    @staticmethod
    @transaction.atomic
    def add_to_cart(user, product_id, stock_id, quantity):
        """
        Add product to cart.
        
        Args:
            user: Current user
            product_id: UUID of product
            stock_id: UUID of stock entry
            quantity: Quantity to add
            
        Returns:
            CartItem instance
            
        Raises:
            Product.DoesNotExist
            Stock.DoesNotExist
            ValueError: If insufficient stock
        """
        cart = CartService.get_or_create_cart(user)
        product = Product.objects.get(id=product_id)
        stock = Stock.objects.get(id=stock_id)
        
        # Validate stock availability
        if stock.available_quantity < quantity:
            raise ValueError(
                f'Insufficient stock. Available: {stock.available_quantity}, '
                f'Requested: {quantity}'
            )
        
        # Get or create cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'unit_price': stock.price, 'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return cart_item
    
    @staticmethod
    def remove_from_cart(user, product_id):
        """Remove product from cart."""
        try:
            cart = user.cart
            CartItem.objects.filter(cart=cart, product_id=product_id).delete()
            return True
        except Cart.DoesNotExist:
            return False
    
    @staticmethod
    def update_cart_item_quantity(user, product_id, quantity):
        """Update quantity for cart item."""
        try:
            cart = user.cart
            item = CartItem.objects.get(cart=cart, product_id=product_id)
            
            if quantity <= 0:
                item.delete()
                return None
            
            item.quantity = quantity
            item.save()
            return item
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            return None
    
    @staticmethod
    def clear_cart(user):
        """Clear all items from user's cart."""
        try:
            cart = user.cart
            cart.items.all().delete()
            return True
        except Cart.DoesNotExist:
            return False
