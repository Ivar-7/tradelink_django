import logging
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import User, UserRole

logger = logging.getLogger(__name__)
UserModel = get_user_model()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(
        max_length=150
    )
    password = serializers.CharField(write_only=True, min_length=8, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    phone_number = serializers.CharField(max_length=20, required=False)
    gender = serializers.ChoiceField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], required=False)
    # date_of_birth = serializers.DateField(required=False)
    role = serializers.ChoiceField(choices=[('buyer', 'Buyer'), ('vendor', 'Vendor'), ('user', 'User')], default='buyer')

    def validate_role(self, value):
        # Public registration cannot self-assign admin role
        if value == 'admin':
            raise serializers.ValidationError('Cannot self-assign admin role.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        return User.objects.create_user(password=password, **validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False, allow_blank=False)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = attrs.get('email') or attrs.get('username')
        if not identifier:
            raise serializers.ValidationError({'email': 'Email or username is required.'})

        lookup_field = 'email' if attrs.get('email') else 'username'
        try:
            user_obj = UserModel.objects.get(**{lookup_field: identifier})
        except UserModel.DoesNotExist:
            raise serializers.ValidationError('Invalid email or password.')

        user = authenticate(
            request=self.context.get('request'),
            username=user_obj.email,
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
