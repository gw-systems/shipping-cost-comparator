"""
Custom authentication for admin endpoints using X-Admin-Token header.
Maintains compatibility with the FastAPI implementation.
"""
from rest_framework import authentication
from rest_framework import exceptions
from django.conf import settings
import logging

logger = logging.getLogger('courier')


class AdminTokenAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication class that validates X-Admin-Token header.
    Used for admin-only endpoints requiring password protection.
    """

    def authenticate(self, request):
        # This authentication is only required for admin endpoints
        # Non-admin endpoints will pass through
        return None

    def authenticate_header(self, request):
        return 'X-Admin-Token'


def verify_admin_token(request):
    """
    Helper function to verify admin token from request headers.
    Raises PermissionDenied if token is invalid or missing.
    """
    token = request.META.get('HTTP_X_ADMIN_TOKEN')

    if token != settings.ADMIN_PASSWORD:
        logger.warning(f"UNAUTHORIZED_ACCESS_ATTEMPT: Invalid token provided from {request.META.get('REMOTE_ADDR')}")
        raise exceptions.PermissionDenied("Invalid or missing Admin Token")

    return True
