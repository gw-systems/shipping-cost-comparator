"""
Production settings for Courier Module.
"""

from .base import *

# SECURITY: Debug must be False in production
DEBUG = False

# SECURITY: Restrict allowed hosts
ALLOWED_HOSTS_STR = os.getenv('ALLOWED_HOSTS')
if not ALLOWED_HOSTS_STR:
    raise RuntimeError(
        "CRITICAL: ALLOWED_HOSTS not set in .env file. "
        "Set to your domain(s), e.g., ALLOWED_HOSTS=example.com,www.example.com"
    )
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_STR.split(',')]

# Database - PostgreSQL for production
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv('DB_NAME'),
        "USER": os.getenv('DB_USER'),
        "PASSWORD": os.getenv('DB_PASSWORD'),
        "HOST": os.getenv('DB_HOST', 'localhost'),
        "PORT": os.getenv('DB_PORT', '5432'),
        "CONN_MAX_AGE": 600,  # Connection pooling - keep connections open for 10 minutes
    }
}

# Validate database credentials
if not all([os.getenv('DB_NAME'), os.getenv('DB_USER'), os.getenv('DB_PASSWORD')]):
    raise RuntimeError(
        "CRITICAL: Database credentials not set. "
        "Required: DB_NAME, DB_USER, DB_PASSWORD"
    )

# CORS - Restrict origins in production
CORS_ALLOWED_ORIGINS_STR = os.getenv('CORS_ALLOWED_ORIGINS')
if not CORS_ALLOWED_ORIGINS_STR:
    raise RuntimeError(
        "CRITICAL: CORS_ALLOWED_ORIGINS not set in .env file. "
        "Set to your frontend domain(s), e.g., CORS_ALLOWED_ORIGINS=https://example.com,https://www.example.com"
    )
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ALLOWED_ORIGINS_STR.split(',')]
CORS_ALLOW_ALL_ORIGINS = False

# Security Headers
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:")
CSP_FONT_SRC = ("'self'",)

# File-based caching for production (free alternative to Redis)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Production logging - more strict
LOGGING['handlers']['file']['level'] = 'WARNING'
LOGGING['loggers']['django']['level'] = 'WARNING'
LOGGING['loggers']['courier']['level'] = 'INFO'
