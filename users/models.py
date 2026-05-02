"""No-ORM models module.

This project treats Django as an API layer only. Persistence is handled via Supabase
PostgREST HTTP calls, not Django ORM models.

We keep lightweight constants here for backwards-compat with older imports.
"""

from django.db import models


class UserRole(models.TextChoices):
    BUYER = "buyer", "Buyer"
    VENDOR = "vendor", "Vendor"
    ADMIN = "admin", "Admin"


class Gender(models.TextChoices):
    MALE = "M", "Male"
    FEMALE = "F", "Female"
    OTHER = "O", "Other"
