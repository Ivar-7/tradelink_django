import logging
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import User, UserRole

logger = logging.getLogger(__name__)


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all(), message='This email is already registered.')]
    )
    username = serializers.CharField(
        max_length=150,
        validators=[UniqueValidator(queryset=User.objects.all(), message='This username is already taken.')]
    )
    password = serializers.CharField(write_only=True, min_length=8, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'password', 'password_confirm',
                  'phone_number', 'gender', 'date_of_birth', 'role']
        extra_kwargs = {
            'role': {'default': UserRole.BUYER},
        }

    def validate_role(self, value):
        # Public registration cannot self-assign admin role
        if value == UserRole.ADMIN:
            raise serializers.ValidationError('Cannot self-assign admin role.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        logger.info('New user registered: %s', user.email)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get('request'),
            username=attrs['email'],
            password=attrs['password'],
        )
        if not user:
            raise serializers.ValidationError('Invalid email or password.')
        if not user.is_active:
            raise serializers.ValidationError('This account has been deactivated.')
        attrs['user'] = user
        return attrs


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
        validators=[UniqueValidator(queryset=User.objects.all(), message='This username is already taken.')]
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'phone_number', 'gender', 'date_of_birth']


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Passwords do not match.'})
        return attrs

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value


class AdminUserSerializer(serializers.ModelSerializer):
    """Full user representation for admin use."""
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
        fields = ['first_name', 'last_name', 'phone_number', 'gender', 'date_of_birth', 'role', 'is_active', 'is_staff']


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
