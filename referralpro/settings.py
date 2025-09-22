"""
Django settings for referralpro project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------
# Core Security
# -------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-placeholder")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = ['*']

# -------------------------
# Installed Apps
# -------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'storages',
    # 'drf_yasg',

    # Local apps
    'accounts',
    'referr',
    'rewards'
]

# -------------------------
# Middleware
# -------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',   # <-- must be high in stack
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'referralpro.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'referralpro.wsgi.application'
ASGI_APPLICATION = 'referralpro.asgi.application'  # for channels later

# -------------------------
# Database (MySQL)
# -------------------------
DATABASES = {
    'default': {
        'ENGINE': 'mysql.connector.django',
        'NAME': os.getenv('DB_NAME', 'referpro_db'),
        'USER': os.getenv('DB_USER', 'root'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {'autocommit': True}
    }
}

# -------------------------
# Custom User
# -------------------------
AUTH_USER_MODEL = "accounts.User"

# -------------------------
# REST Framework & JWT
# -------------------------

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}
from datetime import timedelta
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=600),   # 🔹 1 hour
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),      # 🔹 7 days
    "ROTATE_REFRESH_TOKENS": True,                    # issue new refresh token on each use
    "BLACKLIST_AFTER_ROTATION": True,                 # old refresh tokens become invalid
    "AUTH_HEADER_TYPES": ("Bearer",),                 # for Authorization: Bearer <token>
    "AUTH_COOKIE": "access_token",                    # optional, if you want DRF cookies
    "AUTH_COOKIE_SECURE": True,                       # secure cookies for HTTPS
    "AUTH_COOKIE_HTTP_ONLY": True,
    "AUTH_COOKIE_SAMESITE": "Lax",
}
# -------------------------
# Redis & Celery
# -------------------------
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB = os.getenv("REDIS_DB", "0")

CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

# -------------------------
# AWS S3 Configuration - CORRECTED
# -------------------------
# AWS credentials
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME", "referal-pro-bucket")
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "us-east-1")

# Disable ACLs (modern S3 default)
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}



if all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME]):
    # Use AWS S3
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3StaticStorage"
    STATIC_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/static/"

    DEFAULT_FILE_STORAGE = "utils.storage_backends.MediaStorage"
    MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/media/"

else:
    # Fallback to local storage
    STATIC_URL = "/static/"
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
    MEDIA_URL = "/media/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# -------------------------
# Email
# -------------------------
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)

# -------------------------
# Twilio
# -------------------------
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# -------------------------
# Stripe / PayPal
# -------------------------
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")


# -------------------------
# Social Authentication
# -------------------------
# Google OAuth2
GOOGLE_OAUTH2_CLIENT_ID = os.getenv('GOOGLE_OAUTH2_CLIENT_ID')

# Facebook
FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID')
FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET')

# Apple Sign In
APPLE_BUNDLE_ID = os.getenv('APPLE_BUNDLE_ID')
APPLE_SERVICES_ID = os.getenv('APPLE_SERVICES_ID')
APPLE_TEAM_ID = os.getenv('APPLE_TEAM_ID')
APPLE_KEY_ID = os.getenv('APPLE_KEY_ID')
APPLE_PRIVATE_KEY = os.getenv('APPLE_PRIVATE_KEY')  # Base64 encoded private key

# OAuth2 Settings
OAUTH2_STATE_TIMEOUT = 300  # 5 minutes timeout for OAuth state
SOCIAL_AUTH_ALLOWED_REDIRECT_URIS = os.getenv('SOCIAL_AUTH_ALLOWED_REDIRECT_URIS', '').split(',')

# -------------------------
# Security / CORS
# -------------------------
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "True").lower() == "true"

# SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False").lower() == "true"
# SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"
# CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "False").lower() == "true"

# -------------------------
# Internationalization
# -------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
