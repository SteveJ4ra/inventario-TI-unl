from rest_framework.permissions import BasePermission
from .retirement_permissions import reviewer_has_account


def is_manager(user):
    profile = getattr(user, "reviewer_profile", None)
    if profile is not None and getattr(profile, "must_change_password", None) is not False:
        return False
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
    if getattr(getattr(user, "reviewer_profile", None), "must_change_password", False):
        return False
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
    reviewer = reviewer_has_account(user)
    temporary = reviewer and user.reviewer_profile.must_change_password
    if reviewer and not temporary:
        permissions.append("retirement.review")
    return {"id": user.pk, "username": user.username,
            "permissions": permissions, "must_change_password": temporary}
