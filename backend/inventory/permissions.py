from rest_framework.permissions import BasePermission


def is_manager(user):
    return bool(
        user.is_authenticated
        and user.is_active
        and user.groups.filter(name="Gestores").exists()
    )


class IsManager(BasePermission):
    message = "Se requiere acceso de gestor autorizado."

    def has_permission(self, request, view):
        return is_manager(request.user)
