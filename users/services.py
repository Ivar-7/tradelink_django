import logging

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)


class AuthService:
    """Handles JWT token operations."""

    @staticmethod
    def get_tokens_for_user(user) -> dict:
        """Generate JWT access and refresh tokens for the given user."""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @staticmethod
    def logout(refresh_token: str) -> None:
        """Blacklist the given refresh token to invalidate the session."""
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info('Refresh token blacklisted.')
        except TokenError as exc:
            logger.warning('Logout attempt with invalid token: %s', exc)
            raise


class UserService:
    """Handles user profile and account state operations."""

    @staticmethod
    def update_profile(user, data: dict):
        """Apply validated field updates to the user model and persist."""
        for attr, value in data.items():
            setattr(user, attr, value)
        user.save()
        logger.info('Profile updated: %s', user.email)
        return user

    @staticmethod
    def change_password(user, new_password: str) -> None:
        """Hash and save a new password for the user."""
        user.set_password(new_password)
        user.save(update_fields=['password'])
        logger.info('Password changed: %s', user.email)

    @staticmethod
    def set_active(user, active: bool) -> None:
        """Activate or deactivate a user account."""
        user.is_active = active
        user.save(update_fields=['is_active'])
        state = 'activated' if active else 'deactivated'
        logger.info('User %s %s by admin.', user.email, state)
