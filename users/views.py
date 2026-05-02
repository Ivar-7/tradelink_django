import logging
import secrets
from datetime import timedelta
from typing import Any, Dict, Optional

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsAdminUser
from .schemas import (
    admin_users_schema,
    change_password_schema,
    login_schema,
    logout_schema,
    me_retrieve_schema,
    me_update_schema,
    register_schema,
    vendor_register_schema,
    forgot_password_schema,
    reset_password_schema,
    verify_email_schema,
    admin_vendor_verify_schema,
    admin_vendors_list_schema,
    admin_vendor_detail_schema,
    admin_vendor_suspend_schema,
    admin_vendor_activate_schema,
    admin_vendor_assign_station_schema,
)
from .serializers import (
    AdminUserSerializer,
    AdminUserUpdateSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    RegisterSerializer,
    VendorRegisterSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    VerifyEmailSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    VendorProfileSerializer,
    AdminVendorListSerializer,
    AdminVendorDetailSerializer,
    AdminVendorSuspendSerializer,
    AdminVendorAssignStationSerializer,
    AdminVendorVerifySerializer,
)
from .services import (
    AdminVendorService,
    AuthService,
    SupabaseUserService,
    SupabaseVendorService,
    UserService,
)

logger = logging.getLogger(__name__)


def _vendor_status(vendor_row: Dict[str, Any], user_row: Optional[Dict[str, Any]] = None) -> str:
    # Supabase schema doesn't have vendor suspension fields on vendor_profile.
    # Model suspension via the underlying user's `is_active` flag.
    if user_row is not None and user_row.get("is_active") is False:
        return "suspended"
    if vendor_row.get("is_verified"):
        return "verified"
    return "pending"


# ─────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @register_schema
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_row = serializer.save()

        # Generate and persist email verification token
        verification_token = secrets.token_urlsafe(32)
        token_persisted = False
        try:
            user_row = SupabaseUserService.update_user(
                str(user_row["user_id"]),
                {"email_verification_token": verification_token},
            )
            token_persisted = user_row.get("email_verification_token") == verification_token
        except Exception:
            logger.exception("Failed to persist email verification token")

        if token_persisted:
            verify_link = f"{request.scheme}://{request.get_host()}/api/v1/auth/verify-email/?token={verification_token}"
            subject = "Verify your Tradelink account"
            message = (
                f"Hi {user_row.get('first_name') or user_row.get('username')},\n\n"
                f"Please verify your email address by visiting the following link:\n{verify_link}\n\n"
                "If you did not create an account, please ignore this message.\n"
            )
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_row["email"]], fail_silently=False)
            except Exception:
                logger.exception("Failed to send verification email")
        else:
            logger.warning(
                "Email verification token was not persisted (schema likely lacks email_verification_token). "
                "Skipping verification email."
            )

        tokens = AuthService.get_tokens_for_user(user_row)
        return Response(
            {
                "user": UserProfileSerializer(user_row).data,
                "tokens": tokens,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    @login_schema
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_row = serializer.validated_data["user"]
        tokens = AuthService.get_tokens_for_user(user_row)
        return Response(
            {"user": UserProfileSerializer(user_row).data, "tokens": tokens},
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @logout_schema
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        AuthService.logout(serializer.validated_data["refresh"])
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────
# USER PROFILE
# ─────────────────────────────────────────────────────────────


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @me_retrieve_schema
    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)

    @me_update_schema
    def patch(self, request):
        serializer = UserProfileUpdateSerializer(data=request.data, partial=True, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_row = UserService.update_profile(request.user, serializer.validated_data)
        return Response(UserProfileSerializer(user_row).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @change_password_schema
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        UserService.change_password(request.user, serializer.validated_data["new_password"])
        return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────
# ADMIN USERS
# ─────────────────────────────────────────────────────────────


@admin_users_schema
class AdminUserViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAdminUser]
    http_method_names = ["get", "patch", "delete", "head", "options", "post"]

    def get_serializer_class(self):
        return AdminUserUpdateSerializer if self.action == "partial_update" else AdminUserSerializer

    def list(self, request):
        role = request.query_params.get("role")
        is_active = request.query_params.get("is_active")
        search = request.query_params.get("search")
        ordering = request.query_params.get("ordering")

        client = SupabaseUserService.get_client()
        query = client.table(SupabaseUserService.table).select("*")

        if role:
            query = query.eq("role", role)

        if is_active is not None:
            query = query.eq("is_active", is_active.lower() in ("true", "1", "yes"))

        if search:
            term = f"*{search}*"
            query = query.or_(
                f"email.ilike.{term},username.ilike.{term},first_name.ilike.{term},last_name.ilike.{term}"
            )

        if ordering:
            desc = ordering.startswith("-")
            field = ordering.lstrip("-")
            if field == "date_joined":
                field = "created_at"
            query = query.order(field, desc=desc)
        else:
            query = query.order("created_at", desc=True)

        data = query.execute().data
        return Response(AdminUserSerializer(data, many=True).data)

    def retrieve(self, request, pk=None):
        user_row = SupabaseUserService.get_user_by_id(pk)
        if not user_row:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(AdminUserSerializer(user_row).data)

    def partial_update(self, request, pk=None):
        serializer = AdminUserUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            updated = SupabaseUserService.update_user(pk, serializer.validated_data)
        except Exception:
            logger.exception("Failed to update user")
            return Response({"detail": "Failed to update user."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AdminUserSerializer(updated).data)

    def destroy(self, request, pk=None):
        try:
            ok = SupabaseUserService.delete_user(pk)
        except Exception:
            logger.exception("Failed to delete user")
            ok = False
        if not ok:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        SupabaseUserService.update_user(pk, {"is_active": True})
        return Response({"detail": f"User {pk} activated."})

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        SupabaseUserService.update_user(pk, {"is_active": False})
        return Response({"detail": f"User {pk} deactivated."})


# ─────────────────────────────────────────────────────────────
# VENDOR REGISTRATION
# ─────────────────────────────────────────────────────────────


class VendorRegisterView(APIView):
    permission_classes = [AllowAny]

    @vendor_register_schema
    def post(self, request):
        serializer = VendorRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        result = serializer.save()
        user_row = result["user"]

        # Create vendor profile row (best-effort; table/columns must exist in Supabase).
        try:
            vendor_row = SupabaseVendorService.create_vendor_profile(
                user_id=str(user_row["user_id"]),
                vendor_type=result.get("vendor_type", "individual"),
                business_name=result.get("business_name", ""),
                verification_doc_url=result.get("verification_doc_url", ""),
            )
        except Exception:
            logger.exception("Failed to create vendor_profile row")
            vendor_row = {}

        tokens = AuthService.get_tokens_for_user(user_row)
        return Response(
            {
                "user": UserProfileSerializer(user_row).data,
                "vendor_profile": VendorProfileSerializer(vendor_row).data,
                "tokens": tokens,
                "message": "Vendor account created. Awaiting admin verification.",
            },
            status=status.HTTP_201_CREATED,
        )


# ─────────────────────────────────────────────────────────────
# EMAIL VERIFICATION
# ─────────────────────────────────────────────────────────────


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    @verify_email_schema
    def get(self, request):
        token = request.query_params.get("token")
        if not token:
            return Response({"detail": "Verification token is required."}, status=status.HTTP_400_BAD_REQUEST)

        user_row = SupabaseUserService.get_user_by_verification_token(token)
        if not user_row:
            return Response({"detail": "Invalid verification token."}, status=status.HTTP_400_BAD_REQUEST)

        if user_row.get("is_email_verified"):
            return Response({"detail": "Email already verified."}, status=status.HTTP_200_OK)

        SupabaseUserService.update_user(
            str(user_row["user_id"]),
            {"is_email_verified": True, "email_verification_token": None},
        )
        return Response({"detail": "Email verified successfully."}, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────
# PASSWORD RESET
# ─────────────────────────────────────────────────────────────


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    @forgot_password_schema
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_row = SupabaseUserService.get_user_by_email(serializer.validated_data["email"])
        if not user_row:
            return Response({"detail": "Email not found."}, status=status.HTTP_400_BAD_REQUEST)

        reset_token = secrets.token_urlsafe(32)
        expiry = timezone.now() + timedelta(hours=24)

        updated_row = SupabaseUserService.update_user(
            str(user_row["user_id"]),
            {
                "password_reset_token": reset_token,
                "password_reset_token_expiry": expiry.isoformat(),
            },
        )
        token_persisted = updated_row.get("password_reset_token") == reset_token
        if not token_persisted:
            logger.warning(
                "Password reset token was not persisted (schema likely lacks password_reset_token columns)."
            )
            return Response(
                {
                    "detail": "Password reset is not configured for the current database schema. "
                    "Add password_reset_token and password_reset_token_expiry columns (or implement a token table)."
                },
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        reset_link = f"{request.scheme}://{request.get_host()}/api/v1/auth/reset-password/?token={reset_token}"
        subject = "Tradelink password reset request"
        message = (
            f"Hi {user_row.get('first_name') or user_row.get('username')},\n\n"
            f"You requested a password reset. Use the link below to set a new password (valid for 24 hours):\n{reset_link}\n\n"
            "If you did not request this, please ignore this email.\n"
        )
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_row["email"]], fail_silently=False)
        except Exception:
            logger.exception("Failed to send password reset email")

        return Response(
            {"detail": "Password reset link sent to email.", "reset_link": reset_link},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @reset_password_schema
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        user_row = SupabaseUserService.get_user_by_reset_token(token)
        if not user_row:
            return Response({"detail": "Invalid password reset token."}, status=status.HTTP_400_BAD_REQUEST)

        expiry_raw = user_row.get("password_reset_token_expiry")
        expiry_dt = parse_datetime(expiry_raw) if isinstance(expiry_raw, str) else None
        if not expiry_dt or timezone.now() > expiry_dt:
            return Response({"detail": "Password reset token has expired."}, status=status.HTTP_400_BAD_REQUEST)

        # Use service helper to hash
        SupabaseUserService.set_password(str(user_row["user_id"]), new_password)
        SupabaseUserService.update_user(
            str(user_row["user_id"]),
            {"password_reset_token": None, "password_reset_token_expiry": None},
        )

        return Response(
            {"detail": "Password reset successfully. Please login with your new password."},
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────
# ADMIN VENDOR MANAGEMENT
# ─────────────────────────────────────────────────────────────


class AdminVendorVerifyView(APIView):
    permission_classes = [IsAdminUser]

    @admin_vendor_verify_schema
    def put(self, request, vendor_id):
        vendor_row = SupabaseVendorService.get_vendor_profile(str(vendor_id))
        if not vendor_row:
            return Response({"detail": "Vendor profile not found."}, status=status.HTTP_404_NOT_FOUND)

        action_status = request.data.get("status")
        notes = request.data.get("notes", "")

        if action_status == "approved":
            vendor_row = AdminVendorService.verify_vendor(vendor_row, True, request.user, notes=notes)
        elif action_status == "rejected":
            vendor_row = AdminVendorService.verify_vendor(vendor_row, False, request.user, notes=notes)
        else:
            return Response(
                {"detail": 'Invalid status. Use "approved" or "rejected".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": f"Vendor {action_status}.",
                "vendor_profile": VendorProfileSerializer(vendor_row).data,
            },
            status=status.HTTP_200_OK,
        )


class AdminVendorsListView(APIView):
    permission_classes = [IsAdminUser]

    @admin_vendors_list_schema
    def get(self, request):
        status_filter = request.query_params.get("status")
        vendors = SupabaseVendorService.list_vendor_profiles()

        enriched = []
        for v in vendors:
            user_row = None
            if v.get("user_id"):
                user_row = SupabaseUserService.get_user_by_id(str(v["user_id"]))
            v = dict(v)
            v["status"] = _vendor_status(v, user_row)
            if status_filter in {"verified", "pending", "suspended"} and v["status"] != status_filter:
                continue
            enriched.append(v)

        return Response(AdminVendorListSerializer(enriched, many=True).data)


class AdminVendorDetailView(APIView):
    permission_classes = [IsAdminUser]

    @admin_vendor_detail_schema
    def get(self, request, vendor_id):
        vendor_row = SupabaseVendorService.get_vendor_profile(str(vendor_id))
        if not vendor_row:
            return Response({"detail": "Vendor profile not found."}, status=status.HTTP_404_NOT_FOUND)

        user_row = None
        user_id = vendor_row.get("user_id")
        if user_id:
            user_row = SupabaseUserService.get_user_by_id(str(user_id))

        vendor_row = dict(vendor_row)
        vendor_row["status"] = _vendor_status(vendor_row, user_row)

        payload = {**vendor_row, "user": user_row or {}}
        return Response(AdminVendorDetailSerializer(payload).data)


class AdminVendorSuspendView(APIView):
    permission_classes = [IsAdminUser]

    @admin_vendor_suspend_schema
    def post(self, request, vendor_id):
        serializer = AdminVendorSuspendSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        vendor_row = SupabaseVendorService.get_vendor_profile(str(vendor_id))
        if not vendor_row:
            return Response({"detail": "Vendor profile not found."}, status=status.HTTP_404_NOT_FOUND)

        vendor_row = AdminVendorService.suspend_vendor(
            vendor_row,
            serializer.validated_data["reason"],
            serializer.validated_data["suspend_duration_days"],
            request.user,
        )

        return Response({"vendor_profile": VendorProfileSerializer(vendor_row).data})


class AdminVendorActivateView(APIView):
    permission_classes = [IsAdminUser]

    @admin_vendor_activate_schema
    def post(self, request, vendor_id):
        vendor_row = SupabaseVendorService.get_vendor_profile(str(vendor_id))
        if not vendor_row:
            return Response({"detail": "Vendor profile not found."}, status=status.HTTP_404_NOT_FOUND)

        vendor_row = AdminVendorService.activate_vendor(vendor_row, request.user)
        return Response({"vendor_profile": VendorProfileSerializer(vendor_row).data})


class AdminVendorAssignStationView(APIView):
    permission_classes = [IsAdminUser]

    @admin_vendor_assign_station_schema
    def post(self, request, vendor_id):
        serializer = AdminVendorAssignStationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        vendor_row = SupabaseVendorService.get_vendor_profile(str(vendor_id))
        if not vendor_row:
            return Response({"detail": "Vendor profile not found."}, status=status.HTTP_404_NOT_FOUND)

        vendor_row = AdminVendorService.assign_dropoff_station(
            vendor_row,
            station_id=str(serializer.validated_data["station_id"]),
            admin_user=request.user,
            reason=serializer.validated_data.get("reason", ""),
        )

        return Response({"vendor_profile": VendorProfileSerializer(vendor_row).data})
