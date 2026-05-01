import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    BUYER = 'buyer', 'Buyer'
    VENDOR = 'vendor', 'Vendor'
    ADMIN = 'admin', 'Admin'


class Gender(models.TextChoices):
    MALE = 'M', 'Male'
    FEMALE = 'F', 'Female'
    OTHER = 'O', 'Other'


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email address is required.')
        email = self.normalize_email(email)
        extra_fields.setdefault('role', UserRole.BUYER)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.ADMIN)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=10, choices=UserRole.choices, default=UserRole.BUYER)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, blank=True, null=True)
    password_reset_token = models.CharField(max_length=255, blank=True, null=True)
    password_reset_token_expiry = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    class Meta:
        ordering = ['-date_joined']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f'{self.email} ({self.get_role_display()})'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()


class VendorProfile(models.Model):
    """Extended vendor information linked to User with role=vendor."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile')
    vendor_type = models.CharField(
        max_length=20,
        choices=[('individual', 'Individual'), ('business', 'Business')],
        default='individual'
    )
    business_name = models.CharField(max_length=255, blank=True)
    verification_doc_url = models.URLField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Suspension fields
    is_suspended = models.BooleanField(default=False)
    suspension_reason = models.TextField(blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    suspension_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Pickup station assignment
    default_dropoff_station_id = models.UUIDField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Vendor Profile'
        verbose_name_plural = 'Vendor Profiles'

    def __str__(self):
        return f'Vendor: {self.user.email} ({self.get_vendor_type_display()})'

    @property
    def status(self):
        """Return vendor status."""
        if not self.is_verified:
            return 'pending'
        if self.is_suspended:
            return 'suspended'
        return 'active'


class AdminAuditLog(models.Model):
    """Audit trail for all admin actions."""
    
    ACTION_CHOICES = [
        ('vendor_verify', 'Vendor Verified'),
        ('vendor_reject', 'Vendor Rejected'),
        ('vendor_suspend', 'Vendor Suspended'),
        ('vendor_activate', 'Vendor Activated'),
        ('payout_approve', 'Payout Approved'),
        ('payout_reject', 'Payout Rejected'),
        ('product_hide', 'Product Hidden'),
        ('product_show', 'Product Shown'),
        ('user_delete', 'User Deleted'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admin = models.ForeignKey(User, on_delete=models.PROTECT, related_name='admin_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target_type = models.CharField(max_length=50)  # 'vendor', 'product', 'order', etc.
    target_id = models.UUIDField()
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Admin Audit Log'
        verbose_name_plural = 'Admin Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin', '-created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['target_id']),
        ]

    def __str__(self):
        return f'{self.get_action_display()} by {self.admin.email} on {self.created_at}'
