"""
OpenAPI schema definitions for the users app.
Import the composed decorators into views.py — do NOT define @extend_schema there.
"""

import rest_framework.serializers as s
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)

from .serializers import (
    AdminUserSerializer,
    AdminUserUpdateSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    VendorRegisterSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    VerifyEmailSerializer,
    VendorProfileSerializer,
    AdminVendorListSerializer,
    AdminVendorDetailSerializer,
)

_AUTH_TAG = ['Auth']
_USERS_TAG = ['Users']
_ADMIN_USERS_TAG = ['Admin / Users']

# ── Auth ─────────────────────────────────────────────────────────────────────

register_schema = extend_schema(
    summary='Register a new user',
    description=(
        'Create a new buyer or vendor account. '
        'Returns the created user profile and a JWT token pair.'
    ),
    request=RegisterSerializer,
    responses={
        201: inline_serializer(
            name='RegisterResponse',
            fields={
                'user': UserProfileSerializer(),
                'tokens': inline_serializer(
                    name='RegisterTokenPair',
                    fields={
                        'access': s.CharField(),
                        'refresh': s.CharField(),
                    },
                ),
            },
        ),
        400: OpenApiResponse(description='Validation errors'),
    },
    tags=_AUTH_TAG,
)

login_schema = extend_schema(
    summary='Login',
    description='Authenticate with email and password. Returns JWT access and refresh tokens.',
    request=LoginSerializer,
    responses={
        200: inline_serializer(
            name='LoginResponse',
            fields={
                'user': UserProfileSerializer(),
                'tokens': inline_serializer(
                    name='LoginTokenPair',
                    fields={
                        'access': s.CharField(),
                        'refresh': s.CharField(),
                    },
                ),
            },
        ),
        400: OpenApiResponse(description='Invalid credentials or inactive account'),
    },
    tags=_AUTH_TAG,
)

logout_schema = extend_schema(
    summary='Logout',
    description='Blacklist the provided refresh token, effectively terminating the session.',
    request=LogoutSerializer,
    responses={
        200: OpenApiResponse(description='Successfully logged out'),
        400: OpenApiResponse(description='Token invalid or already expired'),
        401: OpenApiResponse(description='Authentication credentials not provided'),
    },
    tags=_AUTH_TAG,
)

# ── User profile ──────────────────────────────────────────────────────────────

me_retrieve_schema = extend_schema(
    summary='Get current user profile',
    description='Returns the full profile of the currently authenticated user.',
    responses={200: UserProfileSerializer},
    tags=_USERS_TAG,
)

me_update_schema = extend_schema(
    summary='Update current user profile',
    description='Partially update editable profile fields (username, name, phone, gender, DOB).',
    request=UserProfileUpdateSerializer,
    responses={
        200: UserProfileSerializer,
        400: OpenApiResponse(description='Validation errors'),
    },
    tags=_USERS_TAG,
)

change_password_schema = extend_schema(
    summary='Change password',
    description='Verify the current password and replace it with a new one.',
    request=ChangePasswordSerializer,
    responses={
        200: OpenApiResponse(description='Password changed successfully'),
        400: OpenApiResponse(description='Incorrect current password or validation failure'),
    },
    tags=_USERS_TAG,
)

# ── Admin / Users ─────────────────────────────────────────────────────────────

admin_users_schema = extend_schema_view(
    list=extend_schema(
        summary='[Admin] List all users',
        description='Paginated list of all users. Supports search and role/active-status filtering.',
        parameters=[
            OpenApiParameter(
                name='role',
                description='Filter by role: buyer | vendor | admin',
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name='is_active',
                description='Filter by active status: true | false',
                required=False,
                type=bool,
            ),
            OpenApiParameter(
                name='search',
                description='Search across email, username, first/last name',
                required=False,
                type=str,
            ),
        ],
        tags=_ADMIN_USERS_TAG,
    ),
    retrieve=extend_schema(
        summary='[Admin] Retrieve a user',
        tags=_ADMIN_USERS_TAG,
    ),
    partial_update=extend_schema(
        summary='[Admin] Update a user',
        request=AdminUserUpdateSerializer,
        responses={200: AdminUserSerializer},
        tags=_ADMIN_USERS_TAG,
    ),
    destroy=extend_schema(
        summary='[Admin] Delete a user',
        tags=_ADMIN_USERS_TAG,
    ),
    activate=extend_schema(
        summary='[Admin] Activate a user account',
        request=None,
        responses={200: OpenApiResponse(description='User activated')},
        tags=_ADMIN_USERS_TAG,
    ),
    deactivate=extend_schema(
        summary='[Admin] Deactivate a user account',
        request=None,
        responses={200: OpenApiResponse(description='User deactivated')},
        tags=_ADMIN_USERS_TAG,
    ),
)


# ── Vendor Registration ─────────────────────────────────────────────────────

vendor_register_schema = extend_schema(
    summary='Register a new vendor account',
    description=(
        'Create a new vendor account with business details. '
        'Vendors must be verified by admin before accessing vendor features. '
        'Returns vendor profile and JWT token pair.'
    ),
    request=VendorRegisterSerializer,
    responses={
        201: inline_serializer(
            name='VendorRegisterResponse',
            fields={
                'user': UserProfileSerializer(),
                'vendor_profile': VendorProfileSerializer(),
                'tokens': inline_serializer(
                    name='VendorRegisterTokenPair',
                    fields={
                        'access': s.CharField(),
                        'refresh': s.CharField(),
                    },
                ),
                'message': s.CharField(),
            },
        ),
        400: OpenApiResponse(description='Validation errors'),
    },
    tags=_AUTH_TAG,
)

# ── Email Verification ──────────────────────────────────────────────────────

verify_email_schema = extend_schema(
    summary='Verify email address',
    description='Verify user email using the token sent via email. Use as GET endpoint with token parameter.',
    parameters=[
        OpenApiParameter(
            name='token',
            description='Email verification token',
            required=True,
            type=str,
        ),
    ],
    responses={
        200: OpenApiResponse(description='Email verified successfully'),
        400: OpenApiResponse(description='Invalid or expired verification token'),
    },
    tags=_AUTH_TAG,
)

# ── Password Reset ──────────────────────────────────────────────────────────

forgot_password_schema = extend_schema(
    summary='Request password reset',
    description='Send password reset link to registered email. Returns reset token (remove from production).',
    request=ForgotPasswordSerializer,
    responses={
        200: inline_serializer(
            name='ForgotPasswordResponse',
            fields={
                'detail': s.CharField(),
                'reset_link': s.CharField(),  # Remove in production
            },
        ),
        400: OpenApiResponse(description='Email not found or validation error'),
    },
    tags=_AUTH_TAG,
)

reset_password_schema = extend_schema(
    summary='Reset password using token',
    description='Reset password using the token received via email.',
    request=ResetPasswordSerializer,
    responses={
        200: OpenApiResponse(description='Password reset successfully'),
        400: OpenApiResponse(description='Invalid, expired token or validation error'),
    },
    tags=_AUTH_TAG,
)

# ── Admin / Vendor Verification ─────────────────────────────────────────────

admin_vendor_verify_schema = extend_schema(
    summary='[Admin] Verify or reject vendor application',
    description='Admin endpoint to approve or reject pending vendor registrations.',
    request=inline_serializer(
        name='AdminVendorVerifyRequest',
        fields={
            'status': s.ChoiceField(choices=['approved', 'rejected']),
            'notes': s.CharField(required=False),
        },
    ),
    responses={
        200: inline_serializer(
            name='AdminVendorVerifyResponse',
            fields={
                'detail': s.CharField(),
                'vendor_profile': VendorProfileSerializer(),
            },
        ),
        400: OpenApiResponse(description='Invalid status or validation error'),
        404: OpenApiResponse(description='Vendor profile not found'),
    },
    tags=['Admin / Vendors'],
)


# ── Admin / Vendor Management ───────────────────────────────────────────────

admin_vendors_list_schema = extend_schema(
    summary='[Admin] List all vendors',
    description='List all vendors with filtering by status, type, and search.',
    parameters=[
        OpenApiParameter(
            name='status',
            description='Filter by status: verified | pending | suspended',
            required=False,
            type=str,
        ),
        OpenApiParameter(
            name='vendor_type',
            description='Filter by type: individual | business',
            required=False,
            type=str,
        ),
        OpenApiParameter(
            name='search',
            description='Search by email or business name',
            required=False,
            type=str,
        ),
    ],
    responses={
        200: inline_serializer(
            name='AdminVendorsListResponse',
            fields={
                'total': s.IntegerField(),
                'vendors': s.ListField(child=s.DictField()),
            },
        ),
    },
    tags=['Admin / Vendors'],
)

admin_vendor_detail_schema = extend_schema(
    summary='[Admin] Get vendor details',
    description='Get complete vendor profile with all details.',
    responses={200: s.DictField()},
    tags=['Admin / Vendors'],
)

admin_vendor_suspend_schema = extend_schema(
    summary='[Admin] Suspend vendor',
    description='Suspend a vendor account for a specified duration.',
    request=inline_serializer(
        name='AdminVendorSuspendRequest',
        fields={
            'reason': s.CharField(max_length=500),
            'suspend_duration_days': s.IntegerField(
                min_value=1, max_value=365, default=30
            ),
        },
    ),
    responses={
        200: inline_serializer(
            name='AdminVendorSuspendResponse',
            fields={
                'detail': s.CharField(),
                'vendor': VendorProfileSerializer(),
            },
        ),
        404: OpenApiResponse(description='Vendor not found'),
    },
    tags=['Admin / Vendors'],
)

admin_vendor_activate_schema = extend_schema(
    summary='[Admin] Reactivate vendor',
    description='Reactivate a suspended vendor account.',
    request=None,
    responses={
        200: inline_serializer(
            name='AdminVendorActivateResponse',
            fields={
                'detail': s.CharField(),
                'vendor': VendorProfileSerializer(),
            },
        ),
        400: OpenApiResponse(description='Vendor is not suspended'),
        404: OpenApiResponse(description='Vendor not found'),
    },
    tags=['Admin / Vendors'],
)

admin_vendor_assign_station_schema = extend_schema(
    summary='[Admin] Assign pickup station',
    description='Assign a pickup station as the vendor\'s default dropoff location.',
    request=inline_serializer(
        name='AdminVendorAssignStationRequest',
        fields={
            'station_id': s.UUIDField(),
            'reason': s.CharField(max_length=500, required=False),
        },
    ),
    responses={
        200: inline_serializer(
            name='AdminVendorAssignStationResponse',
            fields={
                'detail': s.CharField(),
                'vendor': VendorProfileSerializer(),
            },
        ),
        404: OpenApiResponse(description='Vendor not found'),
    },
    tags=['Admin / Vendors'],
)
