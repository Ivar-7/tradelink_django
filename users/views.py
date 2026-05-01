import logging

from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import timedelta
import secrets
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError

from .models import User, VendorProfile
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
)
from .services import AuthService, SupabaseService, UserService

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────

class RegisterView(APIView):
    """Public endpoint to create a new user account."""

    permission_classes = [AllowAny]

    @register_schema
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        # ✅ FIX 1: EXPOSE VALIDATION ERRORS (CRITICAL)
        if not serializer.is_valid():
            logger.error("REGISTER VALIDATION ERROR: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = serializer.save()
            tokens = AuthService.get_tokens_for_user(user)

            validated_data = serializer.validated_data

            # ✅ FIX 2: SAFE SUPABASE CALL (DO NOT BREAK MAIN FLOW)
            try:
                user_data = {
                    'username': validated_data['username'],
                    'fname': validated_data.get('first_name', ''),
                    'lname': validated_data.get('last_name', ''),
                    'email_address': validated_data['email'],
                    'password_hash': make_password(validated_data['password']),
                    'gender': validated_data.get('gender'),
                    'role': validated_data['role']
                }

                SupabaseService.create_user(user_data)

            except Exception as supabase_error:
                # ⚠️ Do NOT fail registration if Supabase fails
                logger.warning("Supabase sync failed: %s", str(supabase_error))

            logger.info("User registered successfully: %s", user.email)

            return Response(
                {
                    'user': UserProfileSerializer(user).data,
                    'tokens': tokens,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.exception("REGISTER ERROR: %s", str(e))
            return Response(
                {'detail': 'Registration failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LoginView(APIView):
    """Authenticate a user and return JWT tokens."""

    permission_classes = [AllowAny]

    @login_schema
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})

        # ✅ FIX 3: HANDLE VALIDATION MANUALLY
        if not serializer.is_valid():
            logger.error("LOGIN ERROR: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        tokens = AuthService.get_tokens_for_user(user)

        logger.info("User logged in: %s", user.email)

        return Response(
            {'user': UserProfileSerializer(user).data, 'tokens': tokens},
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """Blacklist the refresh token to invalidate the current session."""

    permission_classes = [IsAuthenticated]

    @logout_schema
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            AuthService.logout(serializer.validated_data['refresh'])
        except TokenError:
            return Response(
                {'detail': 'Token is invalid or already expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)


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
        serializer = UserProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = UserService.update_profile(request.user, serializer.validated_data)
        return Response(UserProfileSerializer(user).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @change_password_schema
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        UserService.change_password(
            request.user,
            serializer.validated_data['new_password']
        )

        return Response(
            {'detail': 'Password changed successfully.'},
            status=status.HTTP_200_OK
        )


# ─────────────────────────────────────────────────────────────
# ADMIN USERS
# ─────────────────────────────────────────────────────────────

@admin_users_schema
class AdminUserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.all().order_by('-date_joined')
    permission_classes = [IsAdminUser]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'email', 'username']
    http_method_names = ['get', 'patch', 'delete', 'head', 'options', 'post']

    def get_serializer_class(self):
        return AdminUserUpdateSerializer if self.action == 'partial_update' else AdminUserSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        role = self.request.query_params.get('role')
        is_active = self.request.query_params.get('is_active')

        if role:
            qs = qs.filter(role=role)

        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ('true', '1', 'yes'))

        return qs

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        user = self.get_object()
        UserService.set_active(user, True)
        return Response({'detail': f'User {user.email} activated.'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        UserService.set_active(user, False)
        return Response({'detail': f'User {user.email} deactivated.'})


# ─────────────────────────────────────────────────────────────
# VENDOR REGISTRATION
# ─────────────────────────────────────────────────────────────

class VendorRegisterView(APIView):
    """Public endpoint to create a new vendor account."""

    permission_classes = [AllowAny]

    @vendor_register_schema
    def post(self, request):
        serializer = VendorRegisterSerializer(data=request.data)

        if not serializer.is_valid():
            logger.error("VENDOR REGISTER VALIDATION ERROR: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = serializer.save()
            tokens = AuthService.get_tokens_for_user(user)

            logger.info("Vendor registered successfully: %s", user.email)

            return Response(
                {
                    'user': UserProfileSerializer(user).data,
                    'vendor_profile': VendorProfileSerializer(user.vendor_profile).data,
                    'tokens': tokens,
                    'message': 'Vendor account created. Awaiting admin verification.',
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.exception("VENDOR REGISTER ERROR: %s", str(e))
            return Response(
                {'detail': 'Vendor registration failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ─────────────────────────────────────────────────────────────
# EMAIL VERIFICATION
# ─────────────────────────────────────────────────────────────

class VerifyEmailView(APIView):
    """Verify user email address using verification token."""

    permission_classes = [AllowAny]

    @verify_email_schema
    def get(self, request):
        token = request.query_params.get('token')
        
        if not token:
            return Response(
                {'detail': 'Verification token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email_verification_token=token)
            
            if user.is_email_verified:
                return Response(
                    {'detail': 'Email already verified.'},
                    status=status.HTTP_200_OK
                )
            
            user.is_email_verified = True
            user.email_verification_token = None
            user.save()

            logger.info("Email verified for user: %s", user.email)

            return Response(
                {'detail': 'Email verified successfully.'},
                status=status.HTTP_200_OK
            )

        except User.DoesNotExist:
            return Response(
                {'detail': 'Invalid verification token.'},
                status=status.HTTP_400_BAD_REQUEST
            )


# ─────────────────────────────────────────────────────────────
# PASSWORD RESET
# ─────────────────────────────────────────────────────────────

class ForgotPasswordView(APIView):
    """Request password reset token via email."""

    permission_classes = [AllowAny]

    @forgot_password_schema
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=serializer.validated_data['email'])
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            user.password_reset_token = reset_token
            user.password_reset_token_expiry = timezone.now() + timedelta(hours=24)
            user.save()

            logger.info("Password reset token generated for user: %s", user.email)

            # TODO: Send email with reset link
            # For now, return token in response (NOT for production!)
            reset_link = f"https://app.tradelink.com/reset-password?token={reset_token}"

            return Response(
                {
                    'detail': 'Password reset link sent to email.',
                    'reset_link': reset_link,  # Remove in production
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.exception("FORGOT PASSWORD ERROR: %s", str(e))
            return Response(
                {'detail': 'Error processing password reset request.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ResetPasswordView(APIView):
    """Reset password using reset token."""

    permission_classes = [AllowAny]

    @reset_password_schema
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']

            user = User.objects.get(password_reset_token=token)

            # Check if token is expired
            if (user.password_reset_token_expiry is None or 
                timezone.now() > user.password_reset_token_expiry):
                return Response(
                    {'detail': 'Password reset token has expired.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.set_password(new_password)
            user.password_reset_token = None
            user.password_reset_token_expiry = None
            user.save()

            logger.info("Password reset successful for user: %s", user.email)

            return Response(
                {'detail': 'Password reset successfully. Please login with your new password.'},
                status=status.HTTP_200_OK
            )

        except User.DoesNotExist:
            return Response(
                {'detail': 'Invalid password reset token.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception("RESET PASSWORD ERROR: %s", str(e))
            return Response(
                {'detail': 'Error resetting password.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ─────────────────────────────────────────────────────────────
# ADMIN VENDOR VERIFICATION
# ─────────────────────────────────────────────────────────────

class AdminVendorVerifyView(APIView):
    """Admin endpoint to verify/reject vendor applications."""

    permission_classes = [IsAdminUser]

    @admin_vendor_verify_schema
    def put(self, request, vendor_id):
        try:
            vendor_profile = VendorProfile.objects.get(id=vendor_id)
            
            action_status = request.data.get('status')  # 'approved' or 'rejected'
            notes = request.data.get('notes', '')

            if action_status == 'approved':
                vendor_profile.is_verified = True
                vendor_profile.verified_at = timezone.now()
                logger.info("Vendor verified: %s", vendor_profile.user.email)

            elif action_status == 'rejected':
                vendor_profile.is_verified = False
                logger.info("Vendor rejected: %s", vendor_profile.user.email)

            else:
                return Response(
                    {'detail': 'Invalid status. Use "approved" or "rejected".'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            vendor_profile.save()

            return Response(
                {
                    'detail': f'Vendor {action_status}.',
                    'vendor_profile': VendorProfileSerializer(vendor_profile).data,
                },
                status=status.HTTP_200_OK
            )

        except VendorProfile.DoesNotExist:
            return Response(
                {'detail': 'Vendor profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception("ADMIN VENDOR VERIFY ERROR: %s", str(e))
            return Response(
                {'detail': 'Error verifying vendor.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ─────────────────────────────────────────────────────────────
# ADMIN VENDOR MANAGEMENT
# ─────────────────────────────────────────────────────────────

class AdminVendorsListView(APIView):
    """Admin endpoint to list all vendors with filtering."""

    permission_classes = [IsAdminUser]

    @admin_vendors_list_schema
    def get(self, request):
        vendors = VendorProfile.objects.select_related('user').all()
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter == 'verified':
            vendors = vendors.filter(is_verified=True, is_suspended=False)
        elif status_filter == 'pending':
            vendors = vendors.filter(is_verified=False)
        elif status_filter == 'suspended':
            vendors = vendors.filter(is_suspended=True)
        
        # Filter by vendor type
        vendor_type = request.query_params.get('vendor_type')
        if vendor_type:
            vendors = vendors.filter(vendor_type=vendor_type)
        
        # Search
        search = request.query_params.get('search')
        if search:
            vendors = vendors.filter(
                user__email__icontains=search
            ) | vendors.filter(
                business_name__icontains=search
            )
        
        serializer = AdminVendorListSerializer(vendors, many=True)
        return Response({
            'total': vendors.count(),
            'vendors': serializer.data
        })


class AdminVendorDetailView(APIView):
    """Admin endpoint to view detailed vendor information."""

    permission_classes = [IsAdminUser]

    @admin_vendor_detail_schema
    def get(self, request, vendor_id):
        try:
            vendor_profile = VendorProfile.objects.select_related('user').get(id=vendor_id)
            serializer = AdminVendorDetailSerializer(vendor_profile)
            return Response(serializer.data)
        except VendorProfile.DoesNotExist:
            return Response(
                {'detail': 'Vendor not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


class AdminVendorSuspendView(APIView):
    """Admin endpoint to suspend a vendor."""

    permission_classes = [IsAdminUser]

    @admin_vendor_suspend_schema
    def put(self, request, vendor_id):
        try:
            vendor_profile = VendorProfile.objects.get(id=vendor_id)
            
            serializer = AdminVendorSuspendSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            reason = serializer.validated_data['reason']
            duration_days = serializer.validated_data.get('suspend_duration_days', 30)
            
            from .services import AdminVendorService
            AdminVendorService.suspend_vendor(
                vendor_profile,
                reason,
                duration_days,
                request.user
            )
            
            return Response({
                'detail': f'Vendor suspended for {duration_days} days.',
                'vendor': VendorProfileSerializer(vendor_profile).data
            })
            
        except VendorProfile.DoesNotExist:
            return Response(
                {'detail': 'Vendor not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception("SUSPEND VENDOR ERROR: %s", str(e))
            return Response(
                {'detail': 'Error suspending vendor.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminVendorActivateView(APIView):
    """Admin endpoint to reactivate a suspended vendor."""

    permission_classes = [IsAdminUser]

    @admin_vendor_activate_schema
    def put(self, request, vendor_id):
        try:
            vendor_profile = VendorProfile.objects.get(id=vendor_id)
            
            if not vendor_profile.is_suspended:
                return Response(
                    {'detail': 'Vendor is not suspended.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            from .services import AdminVendorService
            AdminVendorService.activate_vendor(vendor_profile, request.user)
            
            return Response({
                'detail': 'Vendor activated.',
                'vendor': VendorProfileSerializer(vendor_profile).data
            })
            
        except VendorProfile.DoesNotExist:
            return Response(
                {'detail': 'Vendor not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception("ACTIVATE VENDOR ERROR: %s", str(e))
            return Response(
                {'detail': 'Error activating vendor.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminVendorAssignStationView(APIView):
    """Admin endpoint to assign pickup station to vendor."""

    permission_classes = [IsAdminUser]

    @admin_vendor_assign_station_schema
    def put(self, request, vendor_id):
        try:
            vendor_profile = VendorProfile.objects.get(id=vendor_id)
            
            serializer = AdminVendorAssignStationSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            station_id = serializer.validated_data['station_id']
            reason = serializer.validated_data.get('reason', '')
            
            from .services import AdminVendorService
            AdminVendorService.assign_dropoff_station(
                vendor_profile,
                station_id,
                request.user,
                reason
            )
            
            return Response({
                'detail': 'Pickup station assigned.',
                'vendor': VendorProfileSerializer(vendor_profile).data
            })
            
        except VendorProfile.DoesNotExist:
            return Response(
                {'detail': 'Vendor not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception("ASSIGN STATION ERROR: %s", str(e))
            return Response(
                {'detail': 'Error assigning station.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )