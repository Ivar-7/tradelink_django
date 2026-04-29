import logging
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import User, UserRole

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