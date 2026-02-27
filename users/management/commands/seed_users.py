"""
Seed demo user data.  Safe to run multiple times (idempotent).

Usage:
    python manage.py seed_users
"""

from django.core.management.base import BaseCommand

from users.models import User, UserRole

DEMO_USERS = [
    {
        'email': 'buyer@tradelink.dev',
        'username': 'demo_buyer',
        'first_name': 'Alice',
        'last_name': 'Buyer',
        'role': UserRole.BUYER,
        'is_staff': False,
        'is_superuser': False,
        'password': 'TradelinkDemo123!',
    },
    {
        'email': 'vendor@tradelink.dev',
        'username': 'demo_vendor',
        'first_name': 'Bob',
        'last_name': 'Vendor',
        'role': UserRole.VENDOR,
        'is_staff': False,
        'is_superuser': False,
        'password': 'TradelinkDemo123!',
    },
    {
        'email': 'admin@tradelink.dev',
        'username': 'demo_admin',
        'first_name': 'Charlie',
        'last_name': 'Admin',
        'role': UserRole.ADMIN,
        'is_staff': True,
        'is_superuser': True,
        'password': 'TradelinkDemo123!',
    },
]


class Command(BaseCommand):
    help = 'Seed demo user data (idempotent)'

    def handle(self, *args, **options):
        self.stdout.write('Seeding users...')
        for data in DEMO_USERS:
            password = data.pop('password')
            user, created = User.objects.get_or_create(
                email=data['email'],
                defaults=data,
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'  Created: {user.email}  [{user.get_role_display()}]')
                )
            else:
                self.stdout.write(f'  Already exists: {user.email}')
        self.stdout.write(self.style.SUCCESS('Done.'))
