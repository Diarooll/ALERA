from rest_framework.permissions import BasePermission


class EhAdministrador(BasePermission):
    """Só conta de administrador (a mesma regra de Usuario.papel)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
