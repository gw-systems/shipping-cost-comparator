"""
Development settings for Courier Module.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# Database - SQLite for development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "logistics.db",
    }
}

# CORS - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Disable security features in development for easier testing
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Development-specific logging
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['courier']['level'] = 'DEBUG'
LOGGING['handlers']['console']['level'] = 'DEBUG'
