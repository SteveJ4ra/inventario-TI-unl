from django.db import IntegrityError, connection, transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from .errors import Conflict
from .models import Asset, Assignment, Condition, Custodian, Movement
from .permissions import is_manager


def require_manager(actor):
    if not is_manager(actor):
        raise PermissionDenied("Se requiere acceso de gestor autorizado.")


def create_asset(*, actor, data):
    require_manager(actor)
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT nextval('inventory_asset_code_seq')")
                number = cursor.fetchone()[0]
            return Asset.objects.create(
                code=f"TI-{number:06d}", created_by=actor, **data
            )
    except IntegrityError as exc:
        if (
            getattr(exc.__cause__, "diag", None)
            and exc.__cause__.diag.constraint_name == "asset_identity_unique"
        ):
            raise Conflict(
                "Ya existe un activo con esa marca, modelo y serie.", "duplicate_asset"
            ) from exc
        raise


def create_custodian(*, actor, data):
    require_manager(actor)
    try:
        with transaction.atomic():
            return Custodian.objects.create(**data)
    except IntegrityError as exc:
        if (
            getattr(exc.__cause__, "diag", None)
            and exc.__cause__.diag.constraint_name == "custodian_email_unique"
        ):
            raise Conflict(
                "Ya existe un custodio con ese correo.", "duplicate_custodian"
            ) from exc
        raise


def snapshot(asset):
    result = {
        "condition": asset.condition,
        "assignment": asset.assignment,
        "custodian_id": asset.current_custodian_id,
        "location": asset.location,
    }

    if hasattr(asset, "lifecycle_status"):
        result["lifecycle_status"] = asset.lifecycle_status
    return result


def record_operation(*, asset_id, actor, operation, data):
    """Bloquea la ficha antes de validar; ficha y evento se confirman juntos."""
    require_manager(actor)
    with transaction.atomic():
        asset = get_object_or_404(Asset.objects.select_for_update(), pk=asset_id)
        if asset.revision != data["expected_revision"]:
            raise Conflict(
                "La ficha cambió. Recárgala y revisa antes de repetir.",
                "stale_revision",
            )
        if operation != Movement.Type.RECTIFICATION and getattr(asset, "lifecycle_status", "localizado") != "localizado":
            raise Conflict("La operación requiere un activo localizado.")
        before = snapshot(asset)
        person = None
        target = None
        if operation == Movement.Type.DELIVERY:
            if (
                asset.assignment != Assignment.AVAILABLE
                or asset.condition != Condition.OPERATIONAL
            ):
                raise Conflict("Solo se entregan activos Disponibles y Operativos.")
            try:
                person = Custodian.objects.get(pk=data["custodian_id"])
            except Custodian.DoesNotExist:
                raise ValidationError({"custodian_id": ["El custodio no existe."]})
            asset.assignment = Assignment.ASSIGNED
            asset.current_custodian = person
            asset.location = data["destination"]
        elif operation == Movement.Type.RETURN:
            if (
                asset.assignment != Assignment.ASSIGNED
                or not asset.current_custodian_id
            ):
                raise Conflict("El activo no tiene una entrega activa.")
            person = asset.current_custodian
            asset.assignment = Assignment.AVAILABLE
            asset.current_custodian = None
            asset.condition = data["condition"]
            asset.location = data["reception_location"]
        elif operation == Movement.Type.CONDITION:
            if asset.assignment != Assignment.AVAILABLE:
                raise Conflict("Solo se cambia la condición de activos Disponibles.")
            if asset.condition == data["condition"]:
                raise ValidationError({"condition": ["Elige una condición diferente."]})
            asset.condition = data["condition"]
        elif operation == Movement.Type.RECTIFICATION:
            target = asset.movements.order_by("-id").first()
            if (
                not target
                or target.pk != data["movement_id"]
                or target.resulting_revision != asset.revision
                or target.type == Movement.Type.RECTIFICATION
                or Movement.objects.filter(rectifies=target).exists()
            ):
                raise Conflict(
                    "Solo se rectifica el último movimiento vigente, sin operaciones posteriores.",
                    "ineligible_rectification",
                )
            previous = target.before
            asset.condition = previous["condition"]
            asset.assignment = previous["assignment"]
            asset.current_custodian_id = previous["custodian_id"]
            asset.location = previous["location"]
            if "lifecycle_status" in previous and hasattr(asset, "lifecycle_status"):
                asset.lifecycle_status = previous["lifecycle_status"]
            person = target.custodian
        else:
            raise ValueError("Operación no soportada")
        asset.revision += 1
        extra_fields = ["lifecycle_status"] if hasattr(asset, "lifecycle_status") else []
        asset.save(
            update_fields=[
                "condition",
                "assignment",
                "current_custodian",
                "location",
                "revision",
            ] + extra_fields
        )
        person_snapshot = (
            {
                "id": person.pk,
                "full_name": person.full_name,
                "email": person.email,
                "department": person.department,
            }
            if person
            else None
        )
        movement = Movement.objects.create(
            asset=asset,
            type=operation,
            actor=actor,
            actor_label=actor.username,
            custodian=person,
            custodian_snapshot=person_snapshot,
            before=before,
            after=snapshot(asset),
            note=data.get("note", ""),
            reason=data.get("reason", ""),
            rectifies=target,
            resulting_revision=asset.revision,
        )
        return asset, movement
