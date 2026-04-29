import logging

from django.contrib.auth.hashers import make_password
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError

from .models import User
from .permissions import IsAdminUser
from .schemas import (
    admin_users_schema,
    change_password_schema,
    login_schema,
    logout_schema,
    me_retrieve_schema,
    me_update_schema,
    register_schema,
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