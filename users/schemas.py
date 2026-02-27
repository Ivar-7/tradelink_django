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
