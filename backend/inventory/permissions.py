from rest_framework.permissions import BasePermission


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
