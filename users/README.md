# Users App

Handles registration, JWT authentication, and user profile management for Tradelink.

## Quickstart

```bash
source venv/bin/activate
python manage.py migrate
python manage.py seed_users
python manage.py runserver
```

Swagger docs: **http://localhost:8000/api/docs/**

## Seed

```bash
python manage.py seed_users
```

Demo accounts — password for all: `TradelinkDemo123!`

| Email | Role |
|---|---|
| `buyer@tradelink.dev` | Buyer |
| `vendor@tradelink.dev` | Vendor |
| `admin@tradelink.dev` | Admin (staff) |

## Tests

```bash
python manage.py test users
```

## Endpoints summary

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | `/api/v1/auth/register/` | Public | Register |
| POST | `/api/v1/auth/login/` | Public | Login |
| POST | `/api/v1/auth/logout/` | Bearer | Logout |
| POST | `/api/v1/auth/token/refresh/` | — | Refresh token |
| GET | `/api/v1/users/me/` | Bearer | Get profile |
| PATCH | `/api/v1/users/me/` | Bearer | Update profile |
| POST | `/api/v1/users/me/change-password/` | Bearer | Change password |
| GET | `/api/v1/admin/users/` | Admin | List users |
| GET | `/api/v1/admin/users/{id}/` | Admin | Get user |
| PATCH | `/api/v1/admin/users/{id}/` | Admin | Update user |
| DELETE | `/api/v1/admin/users/{id}/` | Admin | Delete user |
| POST | `/api/v1/admin/users/{id}/activate/` | Admin | Activate user |
| POST | `/api/v1/admin/users/{id}/deactivate/` | Admin | Deactivate user |
