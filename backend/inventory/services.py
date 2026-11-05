from contextlib import contextmanager
from copy import deepcopy

from django.db import IntegrityError, connection, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from .errors import Conflict
from .models import (
    Asset,
    AssetTransition,
    Assignment,
    Condition,
    Custodian,
    Incident,
    LifecycleStatus,
    MaintenanceEvent,
    Movement,
    RecoveryEvent,
)
from .permissions import is_manager


def require_manager(actor):
    if not is_manager(actor):
        raise PermissionDenied("Se requiere acceso de gestor autorizado.")


def create_asset(*, actor, data):
    require_manager(actor)
    # Transición explícita: 002 sigue vigente hasta la activación API de T007.
    acquisition_fields = {"faculty_id", "acquisition_document_id", "item_value", "acquired_on", "date_unknown_reason"}
    if isinstance(data, dict) and acquisition_fields.intersection(data):
        from .acquisition_services import create_asset_with_acquisition
        return create_asset_with_acquisition(actor=actor, data=data)
    from .serializers import AssetInput
    serializer = AssetInput(data=data)
    serializer.is_valid(raise_exception=True)
    return _create_base_asset(actor=actor, data=serializer.validated_data)


def _create_base_asset(*, actor, data):
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
    return {
        "condition": asset.condition,
        "assignment": asset.assignment,
        "custodian_id": asset.current_custodian_id,
        "location": asset.location,
    }


def custodian_snapshot(person):
    if person is None:
        return None
    return {
        "id": person.pk,
        "full_name": person.full_name,
        "email": person.email,
        "department": person.department,
    }


@contextmanager
def locked_asset(*, asset_id, actor, expected_revision):
    """Serializa escrituras de 002 y 004 con el mismo bloqueo de ficha."""
    with transaction.atomic():
        require_manager(actor)
        asset = get_object_or_404(Asset.objects.select_for_update(), pk=asset_id)
        if asset.revision != expected_revision:
            raise Conflict(
                "La ficha cambió. Recárgala y revisa antes de repetir.",
                "stale_revision",
            )
        yield asset


def transition_snapshot(asset, event):
    return {
        "asset": {**snapshot(asset), "lifecycle_status": asset.lifecycle_status},
        "event": (
            {
                field.attname: deepcopy(getattr(event, field.attname))
                for field in event._meta.concrete_fields
            }
            if event is not None
            else None
        ),
    }


def record_event_transition(
    *, asset_id, actor, expected_revision, event_model, apply, event_id=None
):
    """Ejecuta una transición interna y registra evidencia en la misma transacción.

    La operación de dominio valida el estado y prepara las instancias recibidas.
    Si necesita bloquear otra proyección, lo hace después de bloquear el activo.
    """
    event_type = {
        Incident: AssetTransition.Type.INCIDENT,
        MaintenanceEvent: AssetTransition.Type.MAINTENANCE,
        RecoveryEvent: AssetTransition.Type.RECOVERY,
    }[event_model]
    with locked_asset(
        asset_id=asset_id, actor=actor, expected_revision=expected_revision
    ) as asset:
        if event_id is None:
            event = event_model(asset=asset)
            before = transition_snapshot(asset, None)
        else:
            event = get_object_or_404(
                event_model.objects.select_for_update(), pk=event_id, asset_id=asset.pk
            )
            before = transition_snapshot(asset, event)

        apply(asset, event)
        if event.asset_id != asset.pk:
            raise ValueError("La proyección debe permanecer asociada al activo bloqueado.")
        event.save()
        asset.revision = expected_revision + 1
        asset.save(
            update_fields=[
                "condition", "assignment", "current_custodian", "location",
                "lifecycle_status", "revision",
            ]
        )
        AssetTransition.objects.create(
            asset=asset,
            event_type=event_type,
            event_id=event.pk,
            actor=actor,
            actor_label=actor.username,
            resulting_revision=asset.revision,
            before=before,
            after=transition_snapshot(asset, event),
        )
        return asset, event


@transaction.atomic
def report_incident(*, asset_id, actor, data):
    def apply(asset, incident):
        if asset.lifecycle_status != LifecycleStatus.LOCATED:
            raise Conflict("La novedad requiere un activo localizado.", "asset_not_located")
        if data["type"] not in Incident.Type.values:
            raise ValidationError({"type": ["Elige un tipo de novedad válido."]})
        incident.type = data["type"]
        incident.description = data["description"]
        incident.reported_by = actor
        if incident.type in Incident.LOSS_TYPES:
            maintenance = active_maintenance(asset).select_for_update().first()
            if maintenance is not None:
                incident.active_maintenance_snapshot = {
                    "id": maintenance.pk,
                    "status": maintenance.status,
                    "description": maintenance.description,
                    "workshop_location": maintenance.workshop_location,
                    "previous_location": maintenance.previous_location,
                    "started_by_id": maintenance.started_by_id,
                    "started_at": maintenance.started_at.isoformat(),
                }
            incident.last_lifecycle_status = asset.lifecycle_status
            incident.last_condition = asset.condition
            incident.last_assignment = asset.assignment
            incident.last_location = asset.location
            incident.last_custodian_snapshot = custodian_snapshot(asset.current_custodian)
            asset.lifecycle_status = LifecycleStatus.UNLOCATED
            asset.assignment = None
            asset.current_custodian = None

    asset, incident = record_event_transition(
        asset_id=asset_id,
        actor=actor,
        expected_revision=data["expected_revision"],
        event_model=Incident,
        apply=apply,
    )
    if incident.active_maintenance_snapshot is not None:
        interrupt_maintenance(
            maintenance_id=incident.active_maintenance_snapshot["id"],
            actor=actor,
            expected_revision=asset.revision,
        )
    return incident


def recover_asset(*, asset_id, actor, data):
    def apply(asset, recovery):
        if asset.lifecycle_status != LifecycleStatus.UNLOCATED:
            raise Conflict("Solo se recuperan activos no localizados.")
        if data["inspection_confirmed"] is not True:
            raise ValidationError({"inspection_confirmed": ["Confirma la inspección del activo."]})
        incident = (
            asset.incidents.select_for_update()
            .filter(type__in=Incident.LOSS_TYPES, status=Incident.Status.OPEN)
            .order_by("-reported_at", "-pk")
            .first()
        )
        if incident is None:
            raise Conflict("El activo no tiene un reporte de pérdida o robo pendiente.")

        # Punto de integración de 005: cancelar una solicitud pendiente aquí,
        # con el activo bloqueado y dentro de la transacción de recuperación.
        recovery.incident = incident
        recovery.found_by = actor
        recovery.inspected_condition = data["inspected_condition"]
        recovery.recovered_location = data["recovered_location"]
        recovery.note = data.get("note", "")
        incident.status = Incident.Status.RECOVERED
        incident.save(update_fields=["status"])
        asset.lifecycle_status = LifecycleStatus.LOCATED
        asset.assignment = Assignment.AVAILABLE
        asset.current_custodian = None
        asset.condition = recovery.inspected_condition
        asset.location = recovery.recovered_location

    return record_event_transition(
        asset_id=asset_id, actor=actor, expected_revision=data["expected_revision"],
        event_model=RecoveryEvent, apply=apply,
    )


def resolve_incident(*, incident_id, actor, data):
    require_manager(actor)
    asset_id = get_object_or_404(Incident.objects.only("asset_id"), pk=incident_id).asset_id

    def apply(asset, incident):
        if (
            incident.type not in Incident.DAMAGE_OBSERVATION_TYPES
            or incident.status != Incident.Status.OPEN
        ):
            raise Conflict("Solo se resuelven daños u observaciones pendientes.")
        incident.status = Incident.Status.RESOLVED
        incident.resolution_note = data["resolution_note"]
        incident.resolved_by = actor
        incident.resolved_at = timezone.now()

    _, incident = record_event_transition(
        asset_id=asset_id,
        actor=actor,
        expected_revision=data["expected_revision"],
        event_model=Incident,
        event_id=incident_id,
        apply=apply,
    )
    return incident


def active_maintenance(asset):
    return asset.maintenance_events.filter(status=MaintenanceEvent.Status.IN_PROGRESS)


def require_available_for_maintenance(asset):
    if (
        asset.lifecycle_status != LifecycleStatus.LOCATED
        or asset.assignment != Assignment.AVAILABLE
        or asset.current_custodian_id is not None
    ):
        raise Conflict("El mantenimiento requiere un activo localizado, disponible y sin custodio.")


def start_maintenance(*, asset_id, actor, data):
    def apply(asset, event):
        require_available_for_maintenance(asset)
        if active_maintenance(asset).exists():
            raise Conflict("El activo ya tiene un mantenimiento en curso.", "maintenance_in_progress")
        event.description = data["description"]
        event.started_by = actor
        event.previous_location = asset.location
        event.workshop_location = data["workshop_location"]
        asset.location = event.workshop_location

    return record_event_transition(
        asset_id=asset_id, actor=actor, expected_revision=data["expected_revision"],
        event_model=MaintenanceEvent, apply=apply,
    )


def _finish_maintenance(*, maintenance_id, actor, expected_revision, apply):
    require_manager(actor)
    asset_id = get_object_or_404(
        MaintenanceEvent.objects.only("asset_id"), pk=maintenance_id
    ).asset_id

    def finish(asset, event):
        if event.status != MaintenanceEvent.Status.IN_PROGRESS:
            raise Conflict("El mantenimiento ya no está en curso.")
        apply(asset, event)
        event.closed_by = actor
        event.closed_at = timezone.now()

    return record_event_transition(
        asset_id=asset_id, actor=actor, expected_revision=expected_revision,
        event_model=MaintenanceEvent, event_id=maintenance_id, apply=finish,
    )


def close_maintenance(*, maintenance_id, actor, data):
    def apply(asset, event):
        require_available_for_maintenance(asset)
        if data["location_confirmed"] is not True:
            raise ValidationError({"location_confirmed": ["Confirma la ubicación de recepción."]})
        event.status = MaintenanceEvent.Status.COMPLETED
        event.result = data["result"]
        event.receiving_location = data["receiving_location"]
        event.location_confirmed = True
        asset.location = event.receiving_location

    return _finish_maintenance(
        maintenance_id=maintenance_id, actor=actor,
        expected_revision=data["expected_revision"], apply=apply,
    )


def interrupt_maintenance(*, maintenance_id, actor, expected_revision):
    """Interrumpe el mantenimiento sin registrar resultado de reparación."""
    def apply(asset, event):
        if asset.lifecycle_status != LifecycleStatus.UNLOCATED:
            raise Conflict("La interrupción requiere un activo no localizado.")
        event.status = MaintenanceEvent.Status.INTERRUPTED_UNLOCATED

    return _finish_maintenance(
        maintenance_id=maintenance_id, actor=actor,
        expected_revision=expected_revision, apply=apply,
    )


def record_operation(*, asset_id, actor, operation, data):
    """Conserva el formato histórico de Movement y comparte el bloqueo de 004."""
    with locked_asset(
        asset_id=asset_id, actor=actor, expected_revision=data["expected_revision"]
    ) as asset:
        if asset.lifecycle_status != LifecycleStatus.LOCATED:
            raise Conflict("La operación requiere un activo localizado.", "asset_not_located")
        before = snapshot(asset)
        person = None
        target = None
        if operation == Movement.Type.DELIVERY:
            if active_maintenance(asset).exists():
                raise Conflict("No se puede entregar un activo en mantenimiento.", "maintenance_in_progress")
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
                or target.resulting_revision != asset.revision
                or target.pk != data["movement_id"]
                or target.type == Movement.Type.RECTIFICATION
                or target.resulting_revision != asset.revision
                or Movement.objects.filter(rectifies=target).exists()
            ):
                raise Conflict(
                    "Solo se rectifica el último movimiento vigente, sin operaciones posteriores.",
                    "ineligible_rectification",
                )
            previous = target.before
            if (
                target.type != Movement.Type.CONDITION
                and active_maintenance(asset).exists()
            ):
                raise Conflict("La rectificación es incompatible con el mantenimiento en curso.", "maintenance_in_progress")
            asset.condition = previous["condition"]
            asset.assignment = previous["assignment"]
            asset.current_custodian_id = previous["custodian_id"]
            asset.location = previous["location"]
            person = target.custodian
        else:
            raise ValueError("Operación no soportada")
        asset.revision += 1
        asset.save(
            update_fields=[
                "condition",
                "assignment",
                "current_custodian",
                "location",
                "revision",
            ]
        )
        movement = Movement.objects.create(
            asset=asset,
            type=operation,
            actor=actor,
            actor_label=actor.username,
            custodian=person,
            custodian_snapshot=custodian_snapshot(person),
            before=before,
            after=snapshot(asset),
            note=data.get("note", ""),
            reason=data.get("reason", ""),
            rectifies=target,
            resulting_revision=asset.revision,
        )
        return asset, movement
