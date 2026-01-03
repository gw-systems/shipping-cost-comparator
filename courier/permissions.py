"""
Custom permission classes for API endpoints.
"""
from rest_framework import permissions
from django.conf import settings
from django.contrib.auth.hashers import check_password
import logging

logger = logging.getLogger('courier')


class IsAdminToken(permissions.BasePermission):
    """
    Permission class that checks for valid X-Admin-Token header.
    Used to protect admin-only endpoints.
    Uses hashed password comparison for security.
    """

    def has_permission(self, request, view):
        token = request.META.get('HTTP_X_ADMIN_TOKEN')

        if not token:
            logger.warning(
                f"ADMIN_ACCESS_DENIED: Missing token - "
                f"IP: {request.META.get('REMOTE_ADDR')}, "
                f"Path: {request.path}, "
                f"Method: {request.method}"
            )
            return False

        if not check_password(token, settings.ADMIN_PASSWORD_HASH):
            logger.warning(
                f"ADMIN_ACCESS_DENIED: Invalid token - "
                f"IP: {request.META.get('REMOTE_ADDR')}, "
                f"Path: {request.path}, "
                f"Method: {request.method}"
            )
            return False

        # Log successful admin access for audit trail
        logger.info(
            f"ADMIN_ACCESS_GRANTED: "
            f"IP: {request.META.get('REMOTE_ADDR')}, "
            f"Path: {request.path}, "
            f"Method: {request.method}"
        )

        return True

    def has_object_permission(self, request, view, obj):
        # Same check for object-level permissions
        return self.has_permission(request, view)
