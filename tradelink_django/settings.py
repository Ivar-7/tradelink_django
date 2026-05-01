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
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*', cast=Csv())


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'corsheaders',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    # Local apps
    'users',
    'addresses',
    'products',
    'orders',
    'reviews',
    'payments',
    'carts',
    'feedback',
    'product_categories',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
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
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'tradelink_django.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

SUPABASE_DB_URL = config('SUPABASE_DB_URL', default='')
if SUPABASE_DB_URL:
    DATABASES['default'] = dj_database_url.parse(
        SUPABASE_DB_URL,
        conn_max_age=600,
        ssl_require=True,
    )


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


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

# Custom user model
AUTH_USER_MODEL = 'users.User'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
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
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('JWT_ACCESS_TOKEN_MINUTES', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('JWT_REFRESH_TOKEN_DAYS', default=7, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
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
    'ENUM_NAME_OVERRIDES': {
        'UserRoleEnum': 'users.models.UserRole.choices',
    },
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
