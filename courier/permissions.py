"""
Custom permission classes for API endpoints.
"""
from rest_framework import permissions
from django.conf import settings
import logging

logger = logging.getLogger('courier')


class IsAdminToken(permissions.BasePermission):
    """
    Permission class that checks for valid X-Admin-Token header.
    Used to protect admin-only endpoints.
    """

    def has_permission(self, request, view):
        token = request.META.get('HTTP_X_ADMIN_TOKEN')

        if token != settings.ADMIN_PASSWORD:
            logger.warning(
                f"UNAUTHORIZED_ACCESS_ATTEMPT: Invalid token provided from "
                f"{request.META.get('REMOTE_ADDR')}"
            )
            return False

        return True

    def has_object_permission(self, request, view, obj):
        # Same check for object-level permissions
        return self.has_permission(request, view)
