import logging
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import User, UserRole, VendorProfile

logger = logging.getLogger(__name__)
UserModel = get_user_model()


# ─────────────────────────────────────────────
# REGISTER
# ─────────────────────────────────────────────

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all(), message="Email already exists.")]
    )

    username = serializers.CharField(
        max_length=150,
        validators=[UniqueValidator(queryset=User.objects.all(), message="Username already taken.")]
    )

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password]
    )

    # ✅ FIX 1: OPTIONAL NOW
    password_confirm = serializers.CharField(write_only=True, required=False)

    # ✅ FIX 2: ALLOW BLANK
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)

    gender = serializers.ChoiceField(
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        required=False
    )

    role = serializers.ChoiceField(
        choices=[('buyer', 'Buyer'), ('vendor', 'Vendor'), ('user', 'User')],
        default='buyer'
    )

    # ─────────────────────────────
    # VALIDATIONc
    # ─────────────────────────────

    def validate_role(self, value):
        if value == 'admin':
            raise serializers.ValidationError('Cannot self-assign admin role.')
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        # ✅ FIX 3: Only check IF provided
        if password_confirm is not None and password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })

        return attrs

    # ─────────────────────────────
    # CREATE USER
    # ─────────────────────────────

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)

        password = validated_data.pop('password')

        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        return user


# ─────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = attrs.get('email') or attrs.get('username')

        if not identifier:
            raise serializers.ValidationError({'detail': 'Email or username is required.'})

        lookup_field = 'email' if attrs.get('email') else 'username'

        try:
            user_obj = UserModel.objects.get(**{lookup_field: identifier})
        except UserModel.DoesNotExist:
            raise serializers.ValidationError({'detail': 'Invalid credentials.'})

        user = authenticate(
            request=self.context.get('request'),
            username=user_obj.email,
            password=attrs['password'],
        )

        if not user:
            raise serializers.ValidationError({'detail': 'Invalid credentials.'})

        if not user.is_active:
            raise serializers.ValidationError({'detail': 'Account is deactivated.'})

        attrs['user'] = user
        return attrs


# ─────────────────────────────────────────────
# PROFILE
# ─────────────────────────────────────────────

class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'phone_number', 'gender', 'date_of_birth', 'role', 'date_joined',
        ]
        read_only_fields = ['id', 'email', 'role', 'date_joined']


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=150,
        validators=[UniqueValidator(queryset=User.objects.all(), message='Username already taken.')]
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'phone_number', 'gender', 'date_of_birth']


# ─────────────────────────────────────────────
# PASSWORD
# ─────────────────────────────────────────────

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)

    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password]
    )

    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Passwords do not match.'
            })
        return attrs

    def validate_current_password(self, value):
        user = self.context['request'].user

        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')

        return value


# ─────────────────────────────────────────────
# ADMIN
# ─────────────────────────────────────────────

class AdminUserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'phone_number', 'gender', 'date_of_birth', 'role', 'is_active',
            'is_staff', 'date_joined',
        ]
        read_only_fields = ['id', 'date_joined']


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number',
            'gender', 'date_of_birth', 'role',
            'is_active', 'is_staff'
        ]


# ─────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


# ─────────────────────────────────────────────
# VENDOR REGISTRATION
# ─────────────────────────────────────────────

class VendorRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all(), message="Email already exists.")]
    )

    username = serializers.CharField(
        max_length=150,
        validators=[UniqueValidator(queryset=User.objects.all(), message="Username already taken.")]
    )

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password]
    )

    password_confirm = serializers.CharField(write_only=True, required=False)

    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)

    gender = serializers.ChoiceField(
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        required=False
    )

    vendor_type = serializers.ChoiceField(
        choices=[('individual', 'Individual'), ('business', 'Business')],
        default='individual'
    )

    business_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    verification_doc_url = serializers.URLField(required=False, allow_blank=True)

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        if password_confirm is not None and password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })

        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password')
        
        vendor_type = validated_data.pop('vendor_type', 'individual')
        business_name = validated_data.pop('business_name', '')
        verification_doc_url = validated_data.pop('verification_doc_url', '')

        user = User.objects.create_user(
            password=password,
            role='vendor',
            **validated_data
        )

        VendorProfile.objects.create(
            user=user,
            vendor_type=vendor_type,
            business_name=business_name,
            verification_doc_url=verification_doc_url,
            is_verified=False
        )

        return user


# ─────────────────────────────────────────────
# PASSWORD RESET
# ─────────────────────────────────────────────

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('User with this email does not exist.')
        return value


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Passwords do not match.'
            })
        return attrs


# ─────────────────────────────────────────────
# EMAIL VERIFICATION
# ─────────────────────────────────────────────

class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField()


# ─────────────────────────────────────────────
# VENDOR PROFILE
# ─────────────────────────────────────────────

class VendorProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = VendorProfile
        fields = [
            'id', 'user_email', 'user_username', 'vendor_type', 'business_name',
            'verification_doc_url', 'is_verified', 'verified_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'verified_at', 'created_at', 'updated_at', 'is_verified']


# ─────────────────────────────────────────────
# ADMIN VENDOR MANAGEMENT
# ─────────────────────────────────────────────

class AdminVendorListSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = VendorProfile
        fields = [
            'id', 'user_email', 'user_name', 'vendor_type', 'business_name',
            'is_verified', 'is_suspended', 'status', 'created_at'
        ]
        read_only_fields = fields


class AdminVendorDetailSerializer(serializers.ModelSerializer):
    user = AdminUserSerializer(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = VendorProfile
        fields = [
            'id', 'user', 'vendor_type', 'business_name', 'verification_doc_url',
            'is_verified', 'verified_at', 'is_suspended', 'suspension_reason',
            'suspended_at', 'suspension_expires_at', 'default_dropoff_station_id',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = fields


class AdminVendorVerifySerializer(serializers.Serializer):
    is_verified = serializers.BooleanField()
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)


class AdminVendorSuspendSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500)
    suspend_duration_days = serializers.IntegerField(
        min_value=1,
        max_value=365,
        default=30
    )


class AdminVendorActivateSerializer(serializers.Serializer):
    pass


class AdminVendorAssignStationSerializer(serializers.Serializer):
    station_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


class AdminAuditLogSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    admin_email = serializers.CharField(source='admin.email', read_only=True)
    action = serializers.CharField(read_only=True)
    target_type = serializers.CharField(read_only=True)
    target_id = serializers.UUIDField(read_only=True)
    details = serializers.CharField(read_only=True)
    ip_address = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)