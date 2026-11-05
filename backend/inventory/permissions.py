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


def is_operator(user):
    return bool(user.is_authenticated and user.is_active and user.groups.filter(name="Operadores").exists())


class IsOperator(BasePermission):
    message = "Se requiere acceso de operador autorizado."

    def has_permission(self, request, view):
        return is_operator(request.user)


class IsManagerOrOperator(BasePermission):
    message = "Se requiere una sesión de inventario autorizada."

    def has_permission(self, request, view):
        return is_manager(request.user) or is_operator(request.user)


def session_payload(user):
    permissions = []
    if is_manager(user):
        permissions.append("inventory.manage")
    if is_operator(user):
        permissions.append("faculties.manage")
    return {"id": user.pk, "username": user.username,
            "permissions": permissions, "must_change_password": False}
