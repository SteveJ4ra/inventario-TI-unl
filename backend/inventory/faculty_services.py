"""Catálogo manual 003, solo Operador; sin lógica de baja/revisores 005."""
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from .errors import Conflict
from .models import Faculty
from .permissions import is_operator
from .serializers import FacultyInput


def save_faculty(*, actor, data, faculty_id=None):
    if not is_operator(actor):
        raise PermissionDenied("Se requiere acceso de operador autorizado.")
    serializer = FacultyInput(data=data, partial=faculty_id is not None)
    serializer.is_valid(raise_exception=True)
    try:
        with transaction.atomic():
            if faculty_id is None:
                return Faculty.objects.create(**serializer.validated_data)
            faculty = get_object_or_404(Faculty.objects.select_for_update(), pk=faculty_id)
            for field, value in serializer.validated_data.items():
                setattr(faculty, field, value)
            if serializer.validated_data:
                faculty.save(update_fields=list(serializer.validated_data))
            return faculty
    except IntegrityError as exc:
        if getattr(getattr(exc.__cause__, "diag", None), "constraint_name", None) == "faculty_name_unique":
            raise Conflict("Ya existe una facultad con ese nombre.", "duplicate_faculty") from exc
        raise


def ensure_no_pending_decommission(*, asset):
    from .retirement_store import assert_faculty_change_allowed
    assert_faculty_change_allowed(asset.pk)


def change_asset_faculty(*, actor, asset_id, data):
    from .acquisition_services import validated, check_revision, reference
    from .models import Asset, AssetFacultyChange
    from .serializers import FacultyChangeInput
    from .errors import DependencyUnavailable
    if not is_operator(actor):
        raise PermissionDenied("Se requiere acceso de operador autorizado.")
    values = validated(FacultyChangeInput, data)
    with transaction.atomic():
        asset = get_object_or_404(Asset.objects.select_for_update(), pk=asset_id)
        check_revision(asset, values["expected_revision"])
        ensure_no_pending_decommission(asset=asset)
        target = reference(Faculty, values["faculty_id"], "faculty_id", lock=True)
        if asset.faculty_id is None:
            raise DependencyUnavailable("Falta el mapeo histórico verificado de facultad (T004).")
        before = {"faculty_id": asset.faculty_id, "faculty_name": asset.faculty.name}
        previous = asset.faculty_id
        asset.faculty = target
        asset.revision += 1
        asset.save(update_fields=["faculty", "revision"])
        AssetFacultyChange.objects.create(asset=asset, previous_faculty_id=previous, new_faculty=target,
            actor=actor, reason=values["reason"], resulting_revision=asset.revision,
            before_json=before, after_json={"faculty_id": target.pk, "faculty_name": target.name})
        return asset
