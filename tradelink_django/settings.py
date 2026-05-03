"""
Django settings for tradelink_django project.
"""

from pathlib import Path
import os
try:
    import certifi
    # Ensure OpenSSL in this Python process uses certifi's CA bundle for verification
    os.environ.setdefault('SSL_CERT_FILE', certifi.where())
except Exception:
    # certifi may not be installed; fall back to system defaults
    pass
from datetime import timedelta
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*', cast=Csv())


# Application definition

INSTALLED_APPS = [
    # Minimal Django internals required by DRF/SimpleJWT at import-time.
    'django.contrib.auth',
    'django.contrib.contenttypes',
    # Third-party
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    # Local apps
    'users',
    'addresses',
    'products',
    'orders',
    'reviews',
    'payments',
    'carts',
    'reports',
    'feedback',
    'product_categories',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tradelink_django.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'tradelink_django.wsgi.application'


# Database
# This project treats Django as an API client only; all persistence must go through Supabase
# PostgREST HTTP calls.
# Django still requires a DATABASES setting, but it must not be used for application data.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}


# Migrations
# This codebase uses Supabase as the system of record. Django migrations must not be
# used to manage schema, and we don't want `runserver` to warn about unapplied
# migrations for apps that are installed only to satisfy import-time dependencies.
DJANGO_DISABLE_MIGRATIONS = config('DJANGO_DISABLE_MIGRATIONS', default=True, cast=bool)
if DJANGO_DISABLE_MIGRATIONS:
    MIGRATION_MODULES = {
        # Built-in apps required by DRF/SimpleJWT import-time behavior
        'auth': None,
        'contenttypes': None,
        # Local apps
        'users': None,
        'addresses': None,
        'products': None,
        'orders': None,
        'reviews': None,
        'payments': None,
        'carts': None,
        'feedback': None,
        'product_categories': None,
    }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = []


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'users.authentication.SupabaseJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# Simple JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=config('JWT_ACCESS_TOKEN_DAYS', default=7, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('JWT_REFRESH_TOKEN_DAYS', default=7, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# drf-spectacular (Swagger)
SPECTACULAR_SETTINGS = {
    'TITLE': 'Tradelink API Documentation',
    'DESCRIPTION': 'Organized API docs for user website flows, catalog, admin dashboard, and vendor operations.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
    'TAGS': [
        {
            'name': '1. User Website Endpoints',
            'description': 'Public and authenticated endpoints used by the customer-facing website.',
        },
        {
            'name': '2. Categories & Catalog',
            'description': 'Catalog taxonomy endpoints for category browsing and management.',
        },
        {
            'name': '3. Admin Dashboard Endpoints',
            'description': 'Admin-only endpoints for platform management and dashboard operations.',
        },
        {
            'name': '4. Vendor Endpoints',
            'description': 'Vendor onboarding, store setup, inventory, payouts, reports, and vendor tools.',
        },
    ],
    'POSTPROCESSING_HOOKS': [
        'tradelink_django.swagger_hooks.organize_endpoint_tags',
    ],
}

# CORS
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://localhost:3000,http://127.0.0.1:3000', cast=Csv())
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGIN_REGEXES = [
    r'^http://localhost(:[0-9]+)?$',
    r'^http://127\.0\.0\.1(:[0-9]+)?$',
]

# Email (SMTP) settings - read from environment (.env)
EMAIL_ALLOW_INSECURE_CERTS = config('EMAIL_ALLOW_INSECURE_CERTS', default=False, cast=bool)
EMAIL_BACKEND = (
    'tradelink_django.email_backends.InsecureTLSEmailBackend'
    if EMAIL_ALLOW_INSECURE_CERTS
    else config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
)
EMAIL_HOST = config('SMTP_HOST', default='localhost')
EMAIL_PORT = config('SMTP_PORT', default=25, cast=int)
EMAIL_HOST_USER = config('SMTP_USER', default='')
EMAIL_HOST_PASSWORD = config('SMTP_PASS', default='')
DEFAULT_FROM_EMAIL = config('EMAIL_FROM', default='webmaster@localhost')
# Use TLS for port 587 by default
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
