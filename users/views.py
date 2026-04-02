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


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterView(APIView):
    """Public endpoint to create a new user account."""

    permission_classes = [AllowAny]

    @register_schema
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = AuthService.get_tokens_for_user(user)

        # Also save to Supabase
        validated_data = serializer.validated_data
        user_data = {
            'username': validated_data['username'],
            'fname': validated_data.get('first_name', ''),
            'lname': validated_data.get('last_name', ''),
            'email_address': validated_data['email'],
            'password_hash': make_password(validated_data['password']),
            'gender': validated_data.get('gender'),
            # 'date_of_birth': validated_data.get('date_of_birth'),
            'role': validated_data['role']
        }
        supabase_user = SupabaseService.create_user(user_data)
        # logger.info('User registered: %s', user.email)
        return Response(
            {
                'user': UserProfileSerializer(user).data,
                'tokens': tokens,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Authenticate a user and return JWT tokens."""

    permission_classes = [AllowAny]

    @login_schema
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        tokens = AuthService.get_tokens_for_user(user)
        logger.info('User logged in: %s', user.email)
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
        serializer.is_valid(raise_exception=True)
        try:
            AuthService.logout(serializer.validated_data['refresh'])
        except TokenError:
            return Response(
                {'detail': 'Token is invalid or already expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)


# ── User profile ──────────────────────────────────────────────────────────────

class MeView(APIView):
    """Retrieve or update the authenticated user's own profile."""

    permission_classes = [IsAuthenticated]

    @me_retrieve_schema
    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)

    @me_update_schema
    def patch(self, request):
        serializer = UserProfileUpdateSerializer(
            request.user, data=request.data, partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = UserService.update_profile(request.user, serializer.validated_data)
        return Response(UserProfileSerializer(user).data)


class ChangePasswordView(APIView):
    """Change the authenticated user's password."""

    permission_classes = [IsAuthenticated]

    @change_password_schema
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        UserService.change_password(request.user, serializer.validated_data['new_password'])
        return Response({'detail': 'Password changed successfully.'}, status=status.HTTP_200_OK)


# ── Admin / Users ─────────────────────────────────────────────────────────────

@admin_users_schema
class AdminUserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Admin-only ViewSet for managing all user accounts.
    Supports search, role/active-status filtering, and activate/deactivate actions.
    """

    queryset = User.objects.all().order_by('-date_joined')
    permission_classes = [IsAdminUser]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'email', 'username']
    http_method_names = ['get', 'patch', 'delete', 'head', 'options', 'post']

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return AdminUserUpdateSerializer
        return AdminUserSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        role = self.request.query_params.get('role')
        is_active = self.request.query_params.get('is_active')
        if role:
            qs = qs.filter(role=role)
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ('true', '1', 'yes'))
        return qs

    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        user = self.get_object()
        UserService.set_active(user, True)
        return Response({'detail': f'User {user.email} has been activated.'})

    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        user = self.get_object()
        UserService.set_active(user, False)
        return Response({'detail': f'User {user.email} has been deactivated.'})
