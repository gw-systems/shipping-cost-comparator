"""
Custom authentication for admin endpoints using X-Admin-Token header.
Uses Django's password hashing for security.
"""
import secrets
from rest_framework import authentication
from rest_framework import exceptions
from django.conf import settings
from django.contrib.auth.hashers import check_password
import logging

logger = logging.getLogger('courier')


class AdminTokenAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication class that validates X-Admin-Token header.
    Used for admin-only endpoints requiring password protection.
    """

    def authenticate(self, request):
        """
        Authenticate admin users via X-Admin-Token header.
        Returns None to allow DRF to fall through to permission classes.
        """
        # Check if this is an admin endpoint
        path = request.path
        if '/admin/' in path:
            token = request.META.get('HTTP_X_ADMIN_TOKEN')

            if not token:
                logger.warning(
                    f"UNAUTHORIZED_ACCESS_ATTEMPT: Missing admin token from {request.META.get('REMOTE_ADDR')} "
                    f"to {path}"
                )
                return None

            # Verify token against hashed password
            if not check_password(token, settings.ADMIN_PASSWORD_HASH):
                logger.warning(
                    f"UNAUTHORIZED_ACCESS_ATTEMPT: Invalid admin token from {request.META.get('REMOTE_ADDR')} "
                    f"to {path}"
                )
                return None

            # Token is valid - create a pseudo-user for admin
            from django.contrib.auth.models import AnonymousUser
            class AdminUser(AnonymousUser):
                @property
                def is_authenticated(self):
                    return True

                @property
                def is_admin(self):
                    return True

            return (AdminUser(), token)

        # Non-admin endpoints don't require authentication here
        return None

    def authenticate_header(self, request):
        return 'X-Admin-Token'


def verify_admin_token(request):
    """
    Helper function to verify admin token from request headers.
    Raises PermissionDenied if token is invalid or missing.

    DEPRECATED: Use AdminTokenAuthentication class instead.
    Kept for backward compatibility.
    """
    token = request.META.get('HTTP_X_ADMIN_TOKEN')

    if not token:
        logger.warning(
            f"UNAUTHORIZED_ACCESS_ATTEMPT: Missing admin token from {request.META.get('REMOTE_ADDR')}"
        )
        raise exceptions.PermissionDenied("Missing Admin Token")

    if not check_password(token, settings.ADMIN_PASSWORD_HASH):
        logger.warning(
            f"UNAUTHORIZED_ACCESS_ATTEMPT: Invalid admin token from {request.META.get('REMOTE_ADDR')}"
        )
        raise exceptions.PermissionDenied("Invalid Admin Token")

    return True
