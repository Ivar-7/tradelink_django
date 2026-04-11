"""
Seed product categories for local development.

Usage:
    python manage.py seed_product_categories
"""

from django.core.management.base import BaseCommand

from product_categories.models import ProductCategory


CATEGORY_SEEDS = [
    {
        "name": "Electronics",
        "description": "Phones, accessories, and smart devices",
        "image_url": "https://picsum.photos/seed/electronics/480/320",
    },
    {
        "name": "Fashion",
        "description": "Clothing, shoes, and accessories",
        "image_url": "https://picsum.photos/seed/fashion/480/320",
    },
    {
        "name": "Home & Living",
        "description": "Home decor, furniture, and living essentials",
        "image_url": "https://picsum.photos/seed/home-living/480/320",
    },
    {
        "name": "Beauty & Personal Care",
        "description": "Beauty products and personal care items",
        "image_url": "https://picsum.photos/seed/beauty/480/320",
    },
    {
        "name": "Sports & Outdoors",
        "description": "Fitness gear and outdoor equipment",
        "image_url": "https://picsum.photos/seed/sports/480/320",
    },
    {
        "name": "Books & Stationery",
        "description": "Books, notebooks, and office supplies",
        "image_url": "https://picsum.photos/seed/books/480/320",
    },
    {
        "name": "Automotive",
        "description": "Car accessories and maintenance products",
        "image_url": "https://picsum.photos/seed/automotive/480/320",
    },
    {
        "name": "Health & Wellness",
        "description": "Health, wellness, and self-care products",
        "image_url": "https://picsum.photos/seed/wellness/480/320",
    },
    {
        "name": "Toys & Games",
        "description": "Toys, games, and hobby products",
        "image_url": "https://picsum.photos/seed/toys/480/320",
    },
    {
        "name": "Tools & Hardware",
        "description": "Hand tools, power tools, and hardware",
        "image_url": "https://picsum.photos/seed/tools/480/320",
    },
]


class Command(BaseCommand):
    help = "Seed 10 product categories (idempotent)."

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        self.stdout.write("Seeding product categories...")

        for entry in CATEGORY_SEEDS:
            category, created = ProductCategory.objects.get_or_create(
                name=entry["name"],
                defaults={
                    "description": entry["description"],
                    "image_url": entry["image_url"],
                },
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  Created: {category.name}"))
                continue

            changed = False
            if category.description != entry["description"]:
                category.description = entry["description"]
                changed = True
            if category.image_url != entry["image_url"]:
                category.image_url = entry["image_url"]
                changed = True

            if changed:
                category.save(update_fields=["description", "image_url"])
                updated_count += 1
                self.stdout.write(f"  Updated: {category.name}")
            else:
                self.stdout.write(f"  Unchanged: {category.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Created={created_count}, Updated={updated_count}, Total={ProductCategory.objects.count()}"
            )
        )