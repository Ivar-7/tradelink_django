"""
Seed local database with vendor dashboard demo data.

Usage:
    python manage.py seed_vendor_dashboard
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from addresses.models import ProfileAddress
from orders.models import Order, OrderItem, OrderStatus, ShippingMethod
from payments.models import Payment, PaymentStatus
from product_categories.models import ProductCategory
from products.models import Product
from reviews.models import Review
from users.management.commands.seed_users import DEMO_USERS
from users.models import User


class Command(BaseCommand):
    help = "Seed vendor dashboard demo data (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding vendor dashboard demo data..."))

        users = self._seed_demo_users()
        categories = self._seed_categories()
        products = self._seed_products(users["vendor"], categories)
        self._seed_addresses(users)
        orders = self._seed_orders(users, products)
        self._seed_payments(users["buyer"], orders)
        self._seed_reviews(users["buyer"], products)

        self.stdout.write(self.style.SUCCESS("Done seeding vendor dashboard data."))
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Frontend login details:"))
        self.stdout.write("  Vendor email: vendor@tradelink.dev")
        self.stdout.write("  Vendor password: TradelinkDemo123!")
        self.stdout.write("  Admin email: admin@tradelink.dev")
        self.stdout.write("  Admin password: TradelinkDemo123!")
        self.stdout.write("  Buyer email: buyer@tradelink.dev")
        self.stdout.write("  Buyer password: TradelinkDemo123!")

    def _seed_demo_users(self):
        mapped = {}
        for row in DEMO_USERS:
            defaults = {
                "username": row["username"],
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "role": row["role"],
                "is_staff": row["is_staff"],
                "is_superuser": row["is_superuser"],
            }
            user, created = User.objects.get_or_create(email=row["email"], defaults=defaults)
            if created:
                user.set_password(row["password"])
                user.save()
                self.stdout.write(self.style.SUCCESS(f"  Created user: {user.email}"))
            else:
                changed = False
                for key, value in defaults.items():
                    if getattr(user, key) != value:
                        setattr(user, key, value)
                        changed = True
                if changed:
                    user.save(update_fields=list(defaults.keys()))
                if not user.check_password(row["password"]):
                    user.set_password(row["password"])
                    user.save(update_fields=["password"])
                self.stdout.write(f"  Reused user: {user.email}")

            if user.email.startswith("vendor"):
                mapped["vendor"] = user
            elif user.email.startswith("admin"):
                mapped["admin"] = user
            elif user.email.startswith("buyer"):
                mapped["buyer"] = user

        return mapped

    def _seed_categories(self):
        seeds = [
            {
                "name": "Electronics",
                "description": "Phones, accessories, and gadgets",
                "image_url": "https://picsum.photos/seed/electronics/480/320",
            },
            {
                "name": "Fashion",
                "description": "Clothing and apparel",
                "image_url": "https://picsum.photos/seed/fashion/480/320",
            },
            {
                "name": "Home",
                "description": "Home and living products",
                "image_url": "https://picsum.photos/seed/home/480/320",
            },
        ]

        categories = {}
        for seed in seeds:
            category, created = ProductCategory.objects.get_or_create(
                name=seed["name"],
                defaults={
                    "description": seed["description"],
                    "image_url": seed["image_url"],
                },
            )
            categories[seed["name"]] = category
            self.stdout.write(("  Created" if created else "  Reused") + f" category: {category.name}")
        return categories

    def _seed_products(self, vendor, categories):
        seeds = [
            {
                "name": "Smartphone X1",
                "description": "Dual-SIM Android phone with 128GB storage",
                "price": Decimal("28999.00"),
                "stock_quantity": 18,
                "category": categories["Electronics"],
            },
            {
                "name": "Wireless Earbuds Pro",
                "description": "Noise-cancelling earbuds with charging case",
                "price": Decimal("7499.00"),
                "stock_quantity": 6,
                "category": categories["Electronics"],
            },
            {
                "name": "Cotton Hoodie",
                "description": "Warm unisex hoodie",
                "price": Decimal("2499.00"),
                "stock_quantity": 25,
                "category": categories["Fashion"],
            },
            {
                "name": "Office Desk Lamp",
                "description": "LED desk lamp with adjustable brightness",
                "price": Decimal("1999.00"),
                "stock_quantity": 4,
                "category": categories["Home"],
            },
            {
                "name": "Stainless Water Bottle",
                "description": "750ml insulated bottle",
                "price": Decimal("1299.00"),
                "stock_quantity": 30,
                "category": categories["Home"],
            },
        ]

        products = []
        for idx, seed in enumerate(seeds, start=1):
            product, created = Product.objects.get_or_create(
                name=seed["name"],
                vendor=vendor,
                defaults={
                    "description": seed["description"],
                    "price": seed["price"],
                    "stock_quantity": seed["stock_quantity"],
                    "category": seed["category"],
                    "image_url": f"https://picsum.photos/seed/product-{idx}/640/480",
                },
            )
            if not created:
                product.description = seed["description"]
                product.price = seed["price"]
                product.stock_quantity = seed["stock_quantity"]
                product.category = seed["category"]
                product.save(update_fields=["description", "price", "stock_quantity", "category", "updated_at"])
            products.append(product)
            self.stdout.write(("  Created" if created else "  Updated") + f" product: {product.name}")
        return products

    def _seed_addresses(self, users):
        entries = [
            {
                "user": users["vendor"],
                "label": "Vendor HQ",
                "county": "Nairobi",
                "city": "Westlands",
                "postal_address": "00100",
                "user_contact": "+254711000001",
            },
            {
                "user": users["buyer"],
                "label": "Home",
                "county": "Nairobi",
                "city": "Kilimani",
                "postal_address": "00100",
                "user_contact": "+254711000002",
            },
        ]

        for entry in entries:
            address, created = ProfileAddress.objects.get_or_create(
                user=entry["user"],
                label=entry["label"],
                defaults={
                    "country": "Kenya",
                    "county": entry["county"],
                    "city": entry["city"],
                    "line1": "Demo street",
                    "postal_address": entry["postal_address"],
                    "user_email": entry["user"].email,
                    "user_contact": entry["user_contact"],
                    "is_default": True,
                },
            )
            self.stdout.write(("  Created" if created else "  Reused") + f" address: {address.label}")

    def _seed_orders(self, users, products):
        buyer = users["buyer"]
        seeds = [
            {
                "order_amount": Decimal("36498.00"),
                "status": OrderStatus.CONFIRMED,
                "shipping_method": ShippingMethod.DELIVERY,
                "tracking_number": "TRK-DEMO-001",
                "items": [(products[0], 1), (products[1], 1)],
            },
            {
                "order_amount": Decimal("2499.00"),
                "status": OrderStatus.PENDING,
                "shipping_method": ShippingMethod.PICKUP,
                "tracking_number": "",
                "items": [(products[2], 1)],
            },
            {
                "order_amount": Decimal("3298.00"),
                "status": OrderStatus.SHIPPED,
                "shipping_method": ShippingMethod.DELIVERY,
                "tracking_number": "TRK-DEMO-003",
                "items": [(products[3], 1), (products[4], 1)],
            },
        ]

        orders = []
        for idx, seed in enumerate(seeds, start=1):
            order, created = Order.objects.get_or_create(
                user=buyer,
                tracking_number=seed["tracking_number"] or f"PICKUP-{idx}",
                defaults={
                    "order_amount": seed["order_amount"],
                    "status": seed["status"],
                    "shipping_method": seed["shipping_method"],
                },
            )
            if not created:
                order.order_amount = seed["order_amount"]
                order.status = seed["status"]
                order.shipping_method = seed["shipping_method"]
                order.save(update_fields=["order_amount", "status", "shipping_method", "updated_at"])

            existing_items = OrderItem.objects.filter(order=order)
            if not existing_items.exists():
                for product, quantity in seed["items"]:
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        product_image=product.image_url,
                        quantity=quantity,
                        unit_price=product.price,
                    )

            orders.append(order)
            self.stdout.write(("  Created" if created else "  Updated") + f" order: {order.id}")
        return orders

    def _seed_payments(self, buyer, orders):
        for idx, order in enumerate(orders, start=1):
            payment, created = Payment.objects.get_or_create(
                user=buyer,
                order_id=idx,
                defaults={
                    "amount": order.order_amount,
                    "payment_provider": "mpesa",
                    "status": PaymentStatus.COMPLETED if idx != 2 else PaymentStatus.PENDING,
                },
            )
            if not created:
                payment.amount = order.order_amount
                payment.payment_provider = "mpesa"
                payment.status = PaymentStatus.COMPLETED if idx != 2 else PaymentStatus.PENDING
                payment.updated_at = timezone.now()
                payment.save(update_fields=["amount", "payment_provider", "status", "updated_at"])
            self.stdout.write(("  Created" if created else "  Updated") + f" payment for order index: {idx}")

    def _seed_reviews(self, buyer, products):
        review_seeds = [
            (products[0], 5, "Excellent phone, fast delivery."),
            (products[1], 4, "Great sound quality."),
            (products[3], 3, "Lamp is good but packaging can improve."),
        ]

        for product, rating, comment in review_seeds:
            review, created = Review.objects.get_or_create(
                user=buyer,
                product=product,
                defaults={
                    "rating_value": rating,
                    "comment": comment,
                    "verified_purchase": True,
                },
            )
            if not created:
                review.rating_value = rating
                review.comment = comment
                review.verified_purchase = True
                review.save(update_fields=["rating_value", "comment", "verified_purchase"])
            self.stdout.write(("  Created" if created else "  Updated") + f" review: {product.name}")