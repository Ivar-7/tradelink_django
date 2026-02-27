"""
Users app test suite.
Run: python manage.py test users
"""

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, UserRole
from .services import AuthService, UserService

# ── Helpers ───────────────────────────────────────────────────────────────────


def make_user(
    email='buyer@example.com',
    username='buyer',
    password='TestPass123!',
    role=UserRole.BUYER,
    **kwargs,
):
    return User.objects.create_user(
        email=email, username=username, password=password, role=role, **kwargs
    )


def make_admin(email='admin@example.com', username='admin', password='AdminPass123!'):
    return User.objects.create_user(
        email=email,
        username=username,
        password=password,
        role=UserRole.ADMIN,
        is_staff=True,
        is_superuser=True,
    )


def bearer(user):
    return {'HTTP_AUTHORIZATION': f'Bearer {RefreshToken.for_user(user).access_token}'}


# ── Service unit tests ────────────────────────────────────────────────────────


class AuthServiceTest(APITestCase):
    def test_get_tokens_returns_access_and_refresh(self):
        user = make_user()
        tokens = AuthService.get_tokens_for_user(user)
        self.assertIn('access', tokens)
        self.assertIn('refresh', tokens)

    def test_logout_blacklists_token(self):
        from rest_framework_simplejwt.exceptions import TokenError

        user = make_user(email='svc@example.com', username='svcuser')
        tokens = AuthService.get_tokens_for_user(user)
        AuthService.logout(tokens['refresh'])
        with self.assertRaises(TokenError):
            AuthService.logout(tokens['refresh'])


class UserServiceTest(APITestCase):
    def setUp(self):
        self.user = make_user()

    def test_update_profile(self):
        updated = UserService.update_profile(self.user, {'first_name': 'Jane'})
        self.assertEqual(updated.first_name, 'Jane')

    def test_change_password(self):
        UserService.change_password(self.user, 'NewSecure456!')
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecure456!'))

    def test_set_active_false(self):
        UserService.set_active(self.user, False)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_set_active_true(self):
        self.user.is_active = False
        self.user.save()
        UserService.set_active(self.user, True)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)


# ── API tests: Register ───────────────────────────────────────────────────────


class RegisterAPITest(APITestCase):
    URL = '/api/v1/auth/register/'

    def _payload(self, **overrides):
        base = {
            'email': 'new@example.com',
            'username': 'newuser',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
        }
        base.update(overrides)
        return base

    def test_register_success(self):
        res = self.client.post(self.URL, self._payload())
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', res.data)
        self.assertIn('user', res.data)
        self.assertEqual(res.data['user']['email'], 'new@example.com')

    def test_register_default_role_is_buyer(self):
        res = self.client.post(self.URL, self._payload())
        self.assertEqual(res.data['user']['role'], UserRole.BUYER)

    def test_register_duplicate_email_rejected(self):
        make_user(email='new@example.com', username='existing')
        res = self.client.post(self.URL, self._payload())
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_mismatch_rejected(self):
        res = self.client.post(self.URL, self._payload(password_confirm='Different1!'))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_cannot_self_assign_admin(self):
        res = self.client.post(self.URL, self._payload(role='admin'))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password_rejected(self):
        res = self.client.post(self.URL, self._payload(password='123', password_confirm='123'))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


# ── API tests: Login ──────────────────────────────────────────────────────────


class LoginAPITest(APITestCase):
    URL = '/api/v1/auth/login/'

    def setUp(self):
        self.user = make_user()

    def test_login_success(self):
        res = self.client.post(self.URL, {'email': 'buyer@example.com', 'password': 'TestPass123!'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', res.data)
        self.assertIn('access', res.data['tokens'])

    def test_login_wrong_password(self):
        res = self.client.post(self.URL, {'email': 'buyer@example.com', 'password': 'Wrong!'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_unknown_email(self):
        res = self.client.post(self.URL, {'email': 'ghost@example.com', 'password': 'pass'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_inactive_account_rejected(self):
        self.user.is_active = False
        self.user.save()
        res = self.client.post(self.URL, {'email': 'buyer@example.com', 'password': 'TestPass123!'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


# ── API tests: Logout ─────────────────────────────────────────────────────────


class LogoutAPITest(APITestCase):
    URL = '/api/v1/auth/logout/'

    def setUp(self):
        self.user = make_user()
        self.refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh.access_token}')

    def test_logout_success(self):
        res = self.client.post(self.URL, {'refresh': str(self.refresh)})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_logout_unauthenticated(self):
        self.client.credentials()
        res = self.client.post(self.URL, {'refresh': str(self.refresh)})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_invalid_token(self):
        res = self.client.post(self.URL, {'refresh': 'notavalidtoken'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


# ── API tests: Token refresh ──────────────────────────────────────────────────


class TokenRefreshAPITest(APITestCase):
    URL = '/api/v1/auth/token/refresh/'

    def test_refresh_success(self):
        user = make_user(email='refresh@example.com', username='refreshuser')
        refresh = RefreshToken.for_user(user)
        res = self.client.post(self.URL, {'refresh': str(refresh)})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)


# ── API tests: Profile ────────────────────────────────────────────────────────


class ProfileAPITest(APITestCase):
    ME_URL = '/api/v1/users/me/'
    PW_URL = '/api/v1/users/me/change-password/'

    def setUp(self):
        self.user = make_user()
        self.client.credentials(**bearer(self.user))

    def test_get_profile(self):
        res = self.client.get(self.ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['email'], self.user.email)

    def test_update_profile_name(self):
        res = self.client.patch(self.ME_URL, {'first_name': 'John', 'last_name': 'Doe'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['first_name'], 'John')
        self.assertEqual(res.data['last_name'], 'Doe')

    def test_cannot_change_email_via_patch(self):
        res = self.client.patch(self.ME_URL, {'email': 'newemail@example.com'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # email is read-only — should remain unchanged
        self.assertEqual(res.data['email'], self.user.email)

    def test_get_profile_unauthenticated(self):
        self.client.credentials()
        res = self.client.get(self.ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_success(self):
        res = self.client.post(self.PW_URL, {
            'current_password': 'TestPass123!',
            'new_password': 'NewSecure456!',
            'new_password_confirm': 'NewSecure456!',
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_change_password_wrong_current(self):
        res = self.client.post(self.PW_URL, {
            'current_password': 'WrongPass!',
            'new_password': 'NewSecure456!',
            'new_password_confirm': 'NewSecure456!',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_mismatch(self):
        res = self.client.post(self.PW_URL, {
            'current_password': 'TestPass123!',
            'new_password': 'NewSecure456!',
            'new_password_confirm': 'MismatchPass!',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


# ── API tests: Admin users ────────────────────────────────────────────────────


class AdminUserAPITest(APITestCase):
    LIST_URL = '/api/v1/admin/users/'

    def setUp(self):
        self.admin = make_admin()
        self.user = make_user(email='buyer2@example.com', username='buyer2')
        self.client.credentials(**bearer(self.admin))

    def _detail(self, pk):
        return f'/api/v1/admin/users/{pk}/'

    def test_list_users(self):
        res = self.client.get(self.LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        emails = [u['email'] for u in res.data['results']]
        self.assertIn('buyer2@example.com', emails)

    def test_retrieve_user(self):
        res = self.client.get(self._detail(self.user.pk))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['email'], self.user.email)

    def test_update_user_role(self):
        res = self.client.patch(self._detail(self.user.pk), {'role': 'vendor'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_deactivate_user(self):
        res = self.client.post(f'/api/v1/admin/users/{self.user.pk}/deactivate/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_activate_user(self):
        self.user.is_active = False
        self.user.save()
        res = self.client.post(f'/api/v1/admin/users/{self.user.pk}/activate/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_delete_user(self):
        res = self.client.delete(self._detail(self.user.pk))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())

    def test_search_by_email(self):
        res = self.client.get(self.LIST_URL + '?search=buyer2')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data['results']), 1)

    def test_filter_by_role(self):
        res = self.client.get(self.LIST_URL + '?role=buyer')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for u in res.data['results']:
            self.assertEqual(u['role'], UserRole.BUYER)

    def test_non_admin_forbidden(self):
        self.client.credentials(**bearer(self.user))
        res = self.client.get(self.LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_forbidden(self):
        self.client.credentials()
        res = self.client.get(self.LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
