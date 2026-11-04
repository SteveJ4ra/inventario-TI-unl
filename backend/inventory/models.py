import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower, Trim


class Condition(models.TextChoices):
    OPERATIONAL = "operativo", "Operativo"
    BROKEN = "averiado", "Averiado"
    REPAIR = "en_reparacion", "En reparación"


class Assignment(models.TextChoices):
    AVAILABLE = "disponible", "Disponible"
    ASSIGNED = "asignado", "Asignado"


class LifecycleStatus(models.TextChoices):
    LOCATED = "localizado", "Localizado"
    UNLOCATED = "no_localizado", "No localizado"
    RETIRED = "baja", "Baja"


class Category(models.TextChoices):
    DESKTOP = "computadora_escritorio", "Computadora de escritorio"
    LAPTOP = "portatil", "Portátil"
    MONITOR = "monitor", "Monitor"
    PRINTER = "impresora", "Impresora"
    NETWORK = "equipo_red", "Equipo de red"
    PERIPHERAL = "periferico", "Periférico"


class Custodian(models.Model):
    full_name = models.CharField(max_length=160)
    email = models.EmailField(max_length=254)
    department = models.CharField(max_length=160, blank=True)

    class Meta:
        ordering = ["full_name", "id"]
        constraints = [
            models.UniqueConstraint(Lower(Trim("email")), name="custodian_email_unique")
        ]


class Asset(models.Model):
    code = models.CharField(max_length=32, unique=True, editable=False)
    name = models.CharField(max_length=160)
    description = models.CharField(max_length=2000)
    category = models.CharField(max_length=24, choices=Category.choices)
    brand = models.CharField(max_length=120)
    model = models.CharField(max_length=120)
    serial_number = models.CharField(max_length=160)
    location = models.CharField(max_length=240)
    condition = models.CharField(max_length=16, choices=Condition.choices)
    assignment = models.CharField(
        max_length=16,
        choices=Assignment.choices,
        default=Assignment.AVAILABLE,
        null=True,
        blank=True,
    )
    lifecycle_status = models.CharField(
        max_length=16, choices=LifecycleStatus.choices, default=LifecycleStatus.LOCATED
    )
    current_custodian = models.ForeignKey(
        Custodian, null=True, blank=True, on_delete=models.PROTECT
    )
    revision = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(
                Lower(Trim("brand")),
                Lower(Trim("model")),
                Lower(Trim("serial_number")),
                name="asset_identity_unique",
            ),
            models.CheckConstraint(
                condition=Q(category__in=Category.values), name="asset_category_valid"
            ),
            models.CheckConstraint(
                condition=Q(condition__in=Condition.values),
                name="asset_condition_valid",
            ),
            models.CheckConstraint(
                condition=(
                    (
                        Q(
                            lifecycle_status=LifecycleStatus.LOCATED,
                            assignment__isnull=False,
                        )
                        & (
                            Q(
                                assignment=Assignment.AVAILABLE,
                                current_custodian__isnull=True,
                            )
                            | Q(
                                assignment=Assignment.ASSIGNED,
                                current_custodian__isnull=False,
                            )
                        )
                    )
                    | Q(
                        lifecycle_status__in=[
                            LifecycleStatus.UNLOCATED, LifecycleStatus.RETIRED
                        ],
                        assignment__isnull=True,
                        current_custodian__isnull=True,
                    )
                ),
                name="asset_custody_consistent",
            ),
        ]


class Movement(models.Model):
    class Type(models.TextChoices):
        DELIVERY = "entrega", "Entrega"
        RETURN = "devolucion", "Devolución"
        CONDITION = "cambio_condicion", "Cambio de condición"
        RECTIFICATION = "rectificacion", "Rectificación"

    asset = models.ForeignKey(Asset, related_name="movements", on_delete=models.PROTECT)
    type = models.CharField(max_length=20, choices=Type.choices)
    occurred_at = models.DateTimeField(auto_now_add=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    actor_label = models.CharField(max_length=150)
    custodian = models.ForeignKey(
        Custodian, null=True, blank=True, on_delete=models.PROTECT
    )
    custodian_snapshot = models.JSONField(null=True, blank=True)
    before = models.JSONField()
    after = models.JSONField()
    note = models.CharField(max_length=2000, blank=True)
    reason = models.CharField(max_length=2000, blank=True)
    rectifies = models.OneToOneField(
        "self",
        null=True,
        blank=True,
        related_name="rectified_by",
        on_delete=models.PROTECT,
    )
    resulting_revision = models.PositiveBigIntegerField()

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["asset", "resulting_revision"], name="movement_revision_unique"
            ),
            models.CheckConstraint(
                condition=Q(
                    type__in=[
                        "entrega",
                        "devolucion",
                        "cambio_condicion",
                        "rectificacion",
                    ]
                ),
                name="movement_type_valid",
            ),
            models.CheckConstraint(
                condition=(
                    Q(type="rectificacion", rectifies__isnull=False)
                    | (~Q(type="rectificacion") & Q(rectifies__isnull=True))
                ),
                name="movement_rectifies_consistent",
            ),
            models.CheckConstraint(
                condition=(
                    ~Q(type__in=["rectificacion", "cambio_condicion"]) | ~Q(reason="")
                ),
                name="movement_reason_required",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(
                "El historial no puede modificarse; registra una rectificación."
            )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("El historial debe conservarse.")


class Incident(models.Model):
    class Type(models.TextChoices):
        DAMAGE = "damage", "Daño"
        OBSERVATION = "observation", "Observación"
        LOST = "lost", "Pérdida"
        STOLEN = "stolen", "Robo"

    DAMAGE_OBSERVATION_TYPES = (Type.DAMAGE, Type.OBSERVATION)
    LOSS_TYPES = (Type.LOST, Type.STOLEN)

    class Status(models.TextChoices):
        OPEN = "open", "Abierto"
        RESOLVED = "resolved", "Resuelto"
        RECOVERED = "recovered", "Recuperado"
        CLOSED_BY_RETIREMENT = "closed_by_retirement", "Cerrado por baja"

    asset = models.ForeignKey(Asset, related_name="incidents", on_delete=models.PROTECT)
    type = models.CharField(max_length=16, choices=Type.choices)
    description = models.CharField(max_length=2000)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.OPEN)
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="+", on_delete=models.PROTECT
    )
    reported_at = models.DateTimeField(auto_now_add=True)
    last_lifecycle_status = models.CharField(
        max_length=16, choices=LifecycleStatus.choices, blank=True
    )
    last_condition = models.CharField(max_length=16, choices=Condition.choices, blank=True)
    last_assignment = models.CharField(
        max_length=16, choices=Assignment.choices, null=True, blank=True
    )
    last_custodian_snapshot = models.JSONField(null=True, blank=True)
    last_location = models.CharField(max_length=240, blank=True)
    active_maintenance_snapshot = models.JSONField(null=True, blank=True)
    resolution_note = models.CharField(max_length=2000, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="+",
        on_delete=models.PROTECT,
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(type__in=["damage", "observation"], status__in=["open", "resolved"])
                    | Q(
                        type__in=["lost", "stolen"],
                        status__in=["open", "recovered", "closed_by_retirement"],
                    )
                ),
                name="incident_type_status_valid",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        status="resolved",
                        resolved_by__isnull=False,
                        resolved_at__isnull=False,
                        resolution_note__regex=r"\S",
                    )
                    | (
                        ~Q(status="resolved")
                        & Q(
                            resolved_by__isnull=True,
                            resolved_at__isnull=True,
                            resolution_note="",
                        )
                    )
                ),
                name="incident_resolution_consistent",
            ),
        ]


class MaintenanceEvent(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "En curso"
        COMPLETED = "completed", "Completado"
        INTERRUPTED_UNLOCATED = "interrupted_unlocated", "Interrumpido por No localizado"

    asset = models.ForeignKey(
        Asset, related_name="maintenance_events", on_delete=models.PROTECT
    )
    description = models.CharField(max_length=2000)
    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.IN_PROGRESS
    )
    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="+", on_delete=models.PROTECT
    )
    started_at = models.DateTimeField(auto_now_add=True)
    workshop_location = models.CharField(max_length=240)
    previous_location = models.CharField(max_length=240)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="+",
        on_delete=models.PROTECT,
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    result = models.CharField(max_length=2000, blank=True)
    receiving_location = models.CharField(max_length=240, blank=True)
    location_confirmed = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["asset"],
                condition=Q(status="in_progress"),
                name="maintenance_one_active_per_asset",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        status="in_progress",
                        closed_by__isnull=True,
                        closed_at__isnull=True,
                        result="",
                        receiving_location="",
                        location_confirmed=False,
                    )
                    | Q(
                        status="completed",
                        closed_by__isnull=False,
                        closed_at__isnull=False,
                        result__regex=r"\S",
                        receiving_location__regex=r"\S",
                        location_confirmed=True,
                    )
                    | Q(
                        status="interrupted_unlocated",
                        closed_by__isnull=False,
                        closed_at__isnull=False,
                        result="",
                        receiving_location="",
                        location_confirmed=False,
                    )
                ),
                name="maintenance_closure_consistent",
            ),
        ]


class RecoveryEvent(models.Model):
    incident = models.OneToOneField(
        Incident, related_name="recovery", on_delete=models.PROTECT
    )
    asset = models.ForeignKey(Asset, related_name="recoveries", on_delete=models.PROTECT)
    found_at = models.DateTimeField(auto_now_add=True)
    found_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    inspected_condition = models.CharField(max_length=16, choices=Condition.choices)
    recovered_location = models.CharField(max_length=240)
    note = models.CharField(max_length=2000, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(
                    inspected_condition__in=Condition.values,
                    recovered_location__regex=r"\S",
                ),
                name="recovery_inspection_required",
            ),
        ]


class AssetTransition(models.Model):
    """Evidencia de una transición de 004, separada de la proyección editable."""

    class Type(models.TextChoices):
        INCIDENT = "incident", "Novedad"
        MAINTENANCE = "maintenance", "Mantenimiento"
        RECOVERY = "recovery", "Recuperación"

    asset = models.ForeignKey(
        Asset, related_name="transitions", on_delete=models.PROTECT
    )
    event_type = models.CharField(max_length=16, choices=Type.choices)
    event_id = models.PositiveBigIntegerField()
    occurred_at = models.DateTimeField(auto_now_add=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    actor_label = models.CharField(max_length=150)
    resulting_revision = models.PositiveBigIntegerField()
    before = models.JSONField(encoder=DjangoJSONEncoder)
    after = models.JSONField(encoder=DjangoJSONEncoder)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["asset", "resulting_revision"],
                name="asset_transition_revision_unique",
            ),
        ]


class ImportBatch(models.Model):
    """Lote técnico de importación CSV (008).

    No es fuente de verdad de activos ni licencias: conserva las filas
    normalizadas y el hash que ligan las dos confirmaciones mientras el lote
    es confirmable. Al aplicar o vencer se elimina el contenido temporal y se
    mantiene un resultado mínimo para responder reintentos idempotentes.
    """

    class Kind(models.TextChoices):
        ASSETS = "assets", "Activos"
        LICENSE_LOTS = "license_lots", "Lotes de licencias"

    class State(models.TextChoices):
        INVALID = "INVALID", "Inválido"
        PREVIEW_READY = "PREVIEW_READY", "Vista previa lista"
        CONFIRMED_ONCE = "CONFIRMED_ONCE", "Confirmado una vez"
        APPLIED = "APPLIED", "Aplicado"
        EXPIRED = "EXPIRED", "Vencido"
        CANCELLED = "CANCELLED", "Cancelado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="import_batches"
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    schema_version = models.CharField(max_length=32)
    state = models.CharField(
        max_length=16, choices=State.choices, default=State.INVALID
    )
    content_hash = models.CharField(max_length=64)
    preview_summary = models.JSONField(default=dict)
    errors = models.JSONField(default=list)
    rows = models.JSONField(null=True, blank=True, default=list)
    confirmed_hash = models.CharField(max_length=64, blank=True, default="")
    applied_hash = models.CharField(max_length=64, blank=True, default="")
    applied_result = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "state"], name="import_owner_state_idx"),
        ]
