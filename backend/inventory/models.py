import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
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
        max_length=16, choices=Assignment.choices, default=Assignment.AVAILABLE
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
                    Q(assignment=Assignment.AVAILABLE, current_custodian__isnull=True)
                    | Q(assignment=Assignment.ASSIGNED, current_custodian__isnull=False)
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


class SoftwareLicenseLot(models.Model):
    class LicenseModel(models.TextChoices):
        USER_SEAT = "USER_SEAT", "Por usuario"
        DEVICE_SEAT = "DEVICE_SEAT", "Por dispositivo"

    class TemporalStatus(models.TextChoices):
        NOT_STARTED = "NOT_STARTED", "Por iniciar"
        CURRENT = "CURRENT", "Vigente"
        EXPIRED = "EXPIRED", "Vencido"

    product_name = models.CharField(max_length=160)
    vendor = models.CharField(max_length=160)
    license_model = models.CharField(max_length=16, choices=LicenseModel.choices)
    purchased_quantity = models.PositiveIntegerField()
    in_use_quantity = models.PositiveIntegerField()
    starts_on = models.DateField()
    ends_on = models.DateField(null=True, blank=True)
    revision = models.PositiveBigIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_license_lots",
    )

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(license_model__in=["USER_SEAT", "DEVICE_SEAT"]),
                name="license_lot_model_valid",
            ),
            models.CheckConstraint(
                condition=Q(in_use_quantity__lte=models.F("purchased_quantity")),
                name="license_lot_use_within_purchased",
            ),
            models.CheckConstraint(
                condition=Q(ends_on__isnull=True)
                | Q(ends_on__gte=models.F("starts_on")),
                name="license_lot_dates_ordered",
            ),
        ]

    @property
    def remaining_quantity(self):
        return self.purchased_quantity - self.in_use_quantity

    def status_on(self, today=None):
        from django.utils import timezone

        today = today if today is not None else timezone.localdate()
        if self.starts_on > today:
            return self.TemporalStatus.NOT_STARTED
        if self.ends_on is not None and self.ends_on < today:
            return self.TemporalStatus.EXPIRED
        return self.TemporalStatus.CURRENT

    @property
    def temporal_status(self):
        return self.status_on()


class LicenseLotAudit(models.Model):
    lot = models.ForeignKey(
        SoftwareLicenseLot, related_name="audits", on_delete=models.PROTECT
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    actor_label = models.CharField(max_length=150)
    timestamp = models.DateTimeField(auto_now_add=True)
    before_json = models.JSONField()
    after_json = models.JSONField()
    resulting_revision = models.PositiveBigIntegerField()

    class Meta:
        ordering = ["-resulting_revision", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["lot", "resulting_revision"],
                name="license_lot_audit_revision_unique",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("El historial de licencias no puede modificarse.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("El historial de licencias debe conservarse.")
