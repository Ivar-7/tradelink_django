import logging
from typing import Any, Dict, Optional

from django.contrib.auth.hashers import check_password, make_password
from rest_framework import serializers

from .services import SupabaseUserService

logger = logging.getLogger(__name__)


def _validate_password_basic(password: str) -> None:
    if len(password) < 8:
        raise serializers.ValidationError("Password must be at least 8 characters long.")
    if password.isdigit():
        raise serializers.ValidationError("Password cannot be entirely numeric.")


def _as_user_dict(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    # SupabaseUser (dataclass) or similar
    return {
        "user_id": getattr(obj, "id", None) or getattr(obj, "user_id", None),
        "email": getattr(obj, "email", ""),
        "username": getattr(obj, "username", ""),
        "first_name": getattr(obj, "first_name", ""),
        "last_name": getattr(obj, "last_name", ""),
        "phone_number": getattr(obj, "phone_number", ""),
        "gender": getattr(obj, "gender", ""),
        "role": getattr(obj, "role", "user"),
        "is_active": getattr(obj, "is_active", True),
        "is_staff": getattr(obj, "is_staff", False),
        "is_email_verified": getattr(obj, "is_email_verified", False),
        "password_hash": getattr(obj, "password_hash", ""),
    }


# ─────────────────────────────────────────────
# REGISTER
# ─────────────────────────────────────────────


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, required=False)

    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    gender = serializers.ChoiceField(choices=[("M", "Male"), ("F", "Female"), ("O", "Other")], required=False)

    role = serializers.ChoiceField(choices=[("buyer", "Buyer"), ("vendor", "Vendor"), ("user", "User")], default="buyer")

    def validate_role(self, value):
        if value == "admin":
            raise serializers.ValidationError("Cannot self-assign admin role.")
        return value

    def validate(self, attrs):
        pw = attrs.get("password")
        pw2 = attrs.get("password_confirm")
        if pw2 is not None and pw != pw2:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})

        _validate_password_basic(pw)

        if SupabaseUserService.get_user_by_email(attrs["email"]):
            raise serializers.ValidationError({"email": "Email already exists."})
        if SupabaseUserService.get_user_by_username(attrs["username"]):
            raise serializers.ValidationError({"username": "Username already taken."})

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm", None)
        raw_password = validated_data.pop("password")

        payload = {
            **validated_data,
            "password_hash": make_password(raw_password),
            "is_active": True,
            "is_staff": False,
            "is_superuser": False,
            "is_email_verified": False,
        }
        return SupabaseUserService.create_user(payload)


# ─────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = attrs.get("email") or attrs.get("username")
        if not identifier:
            raise serializers.ValidationError({"detail": "Email or username is required."})

        if attrs.get("email"):
            user_row = SupabaseUserService.get_user_by_email(attrs["email"])
        else:
            user_row = SupabaseUserService.get_user_by_username(attrs["username"])

        if not user_row:
            raise serializers.ValidationError({"detail": "Invalid credentials."})

        if not SupabaseUserService.verify_password(user_row, attrs["password"]):
            raise serializers.ValidationError({"detail": "Invalid credentials."})

        if not bool(user_row.get("is_active", True)):
            raise serializers.ValidationError({"detail": "Account is deactivated."})

        attrs["user"] = user_row
        return attrs


# ─────────────────────────────────────────────
# PROFILE
# ─────────────────────────────────────────────


class UserProfileSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="user_id", read_only=True)
    email = serializers.EmailField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)

    phone_number = serializers.CharField(read_only=True)
    gender = serializers.CharField(read_only=True)
    date_of_birth = serializers.DateField(read_only=True)
    role = serializers.CharField(read_only=True)
    date_joined = serializers.DateTimeField(source="created_at", read_only=True)

    def to_representation(self, instance):
        d = _as_user_dict(instance)
        first_name = d.get("first_name") or ""
        last_name = d.get("last_name") or ""
        d["full_name"] = (first_name + " " + last_name).strip()
        # normalize id
        if "id" in d and "user_id" not in d:
            d["user_id"] = d["id"]
        return super().to_representation(d)


class UserProfileUpdateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=False)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    gender = serializers.ChoiceField(choices=[("M", "Male"), ("F", "Female"), ("O", "Other")], required=False)
    date_of_birth = serializers.DateField(required=False)

    def validate_username(self, value):
        request = self.context.get("request")
        current_user_id = getattr(getattr(request, "user", None), "id", None)
        existing = SupabaseUserService.get_user_by_username(value)
        if existing and str(existing.get("user_id")) != str(current_user_id):
            raise serializers.ValidationError("Username already taken.")
        return value


# ─────────────────────────────────────────────
# PASSWORD
# ─────────────────────────────────────────────


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        _validate_password_basic(attrs["new_password"])
        return attrs

    def validate_current_password(self, value):
        user = self.context["request"].user
        user_dict = _as_user_dict(user)
        if not user_dict.get("password_hash"):
            raise serializers.ValidationError("Current password is incorrect.")
        if not check_password(value, user_dict["password_hash"]):
            raise serializers.ValidationError("Current password is incorrect.")
        return value


# ─────────────────────────────────────────────
# ADMIN
# ─────────────────────────────────────────────


class AdminUserSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="user_id", read_only=True)
    email = serializers.EmailField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)

    phone_number = serializers.CharField(read_only=True)
    gender = serializers.CharField(read_only=True)
    date_of_birth = serializers.DateField(read_only=True)
    role = serializers.CharField(read_only=True)

    is_active = serializers.BooleanField(read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    date_joined = serializers.DateTimeField(source="created_at", read_only=True)

    def to_representation(self, instance):
        d = _as_user_dict(instance)
        d["full_name"] = ((d.get("first_name") or "") + " " + (d.get("last_name") or "")).strip()
        if "id" in d and "user_id" not in d:
            d["user_id"] = d["id"]
        return super().to_representation(d)


class AdminUserUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    gender = serializers.ChoiceField(choices=[("M", "Male"), ("F", "Female"), ("O", "Other")], required=False)
    date_of_birth = serializers.DateField(required=False)

    role = serializers.CharField(required=False)
    is_active = serializers.BooleanField(required=False)
    is_staff = serializers.BooleanField(required=False)


# ─────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


# ─────────────────────────────────────────────
# VENDOR REGISTRATION
# ─────────────────────────────────────────────


class VendorRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, required=False)

    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    gender = serializers.ChoiceField(choices=[("M", "Male"), ("F", "Female"), ("O", "Other")], required=False)

    vendor_type = serializers.ChoiceField(choices=[("individual", "Individual"), ("business", "Business")], default="individual")
    business_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    verification_doc_url = serializers.URLField(required=False, allow_blank=True)

    def validate(self, attrs):
        pw = attrs.get("password")
        pw2 = attrs.get("password_confirm")
        if pw2 is not None and pw != pw2:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})

        _validate_password_basic(pw)

        if SupabaseUserService.get_user_by_email(attrs["email"]):
            raise serializers.ValidationError({"email": "Email already exists."})
        if SupabaseUserService.get_user_by_username(attrs["username"]):
            raise serializers.ValidationError({"username": "Username already taken."})

        return attrs

    def create(self, validated_data):
        # Vendor profile creation happens in the view/service layer because the Supabase
        # vendor table schema can vary across deployments.
        validated_data.pop("password_confirm", None)
        raw_password = validated_data.pop("password")

        payload = {
            **validated_data,
            "role": "vendor",
            "password_hash": make_password(raw_password),
            "is_active": True,
            "is_staff": False,
            "is_superuser": False,
            "is_email_verified": False,
        }
        return {
            "user": SupabaseUserService.create_user(payload),
            "vendor_type": validated_data.get("vendor_type", "individual"),
            "business_name": validated_data.get("business_name", ""),
            "verification_doc_url": validated_data.get("verification_doc_url", ""),
        }


# ─────────────────────────────────────────────
# PASSWORD RESET
# ─────────────────────────────────────────────


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        user = SupabaseUserService.get_user_by_email(value)
        if not user:
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        _validate_password_basic(attrs["new_password"])
        return attrs


# ─────────────────────────────────────────────
# EMAIL VERIFICATION
# ─────────────────────────────────────────────


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField()


# ─────────────────────────────────────────────
# ADMIN VENDOR MANAGEMENT
# ─────────────────────────────────────────────


class AdminVendorVerifySerializer(serializers.Serializer):
    is_verified = serializers.BooleanField()
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)


class AdminVendorSuspendSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500)
    suspend_duration_days = serializers.IntegerField(min_value=1, max_value=365, default=30)


class AdminVendorActivateSerializer(serializers.Serializer):
    pass


class AdminVendorAssignStationSerializer(serializers.Serializer):
    station_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


class VendorProfileSerializer(serializers.Serializer):
    vendor_id = serializers.UUIDField(read_only=True)
    user_id = serializers.UUIDField(read_only=True)
    vendor_type = serializers.CharField(read_only=True)
    verification_doc_url = serializers.CharField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    default_dropoff_station_id = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class AdminVendorListSerializer(serializers.Serializer):
    vendor_id = serializers.UUIDField(read_only=True)
    user_id = serializers.UUIDField(read_only=True)
    vendor_type = serializers.CharField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class AdminVendorDetailSerializer(serializers.Serializer):
    vendor_id = serializers.UUIDField(read_only=True)
    user = AdminUserSerializer(read_only=True)
    vendor_type = serializers.CharField(read_only=True)
    verification_doc_url = serializers.CharField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    default_dropoff_station_id = serializers.UUIDField(read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
