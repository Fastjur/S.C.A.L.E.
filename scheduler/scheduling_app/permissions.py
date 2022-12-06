from typing import Iterable

from rest_framework.permissions import BasePermission


class ResourcePermission(BasePermission):
    message = "Accessing resource not allowed."

    def get_permissions(self, request, view) -> Iterable:
        return getattr(view, f"{request.method.lower()}_permission", ())

    def has_permission(self, request, view):
        for permission in self.get_permissions(request=request, view=view):
            if request.user.has_perm(permission) is False:
                return False

        return True
