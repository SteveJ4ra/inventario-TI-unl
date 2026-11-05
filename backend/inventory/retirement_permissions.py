"""Permisos para el perfil revisor; no habilita endpoints por sí solo."""

from rest_framework.permissions import BasePermission

REVIEWER_GROUP = "Revisores"


def reviewer_has_account(user):
    if user is None or not (user.is_authenticated and user.is_active):
        return False
    if not user.groups.filter(name=REVIEWER_GROUP).exists():
        return False
    if type(user.pk) is not int or user.pk <= 0:
        return False
    profile = getattr(user, "reviewer_profile", None)
    if profile is None or getattr(profile, "user_id", None) != user.pk:
        return False
    faculty_id = getattr(profile, "faculty_id", None)
    return type(faculty_id) is int and faculty_id > 0


class IsReviewerAccount(BasePermission):
    """Solo sesión/logout/cambio de contraseña, incluido primer acceso."""
    message = "Se requiere una cuenta revisora activa."

    def has_permission(self, request, view):
        return reviewer_has_account(request.user)


class IsAssignedReviewer(BasePermission):
    """Permite decidir solo al revisor asignado y con contraseña actualizada.

    Las vistas de lista deben filtrar también el queryset por el usuario;
    DRF no aplica has_object_permission a cada fila de una lista.
    """
    message = "Se requiere una cuenta revisora habilitada para la solicitud."

    def has_permission(self, request, view):
        user = request.user
        return reviewer_has_account(user) and getattr(user.reviewer_profile, "must_change_password", None) is False

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view) and getattr(obj, "assigned_reviewer_id", None) == request.user.pk
