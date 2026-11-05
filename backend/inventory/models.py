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
            models.UniqueConstraint(Lower(Trim("email")), name="custodian_email_unique"),
            models.CheckConstraint(condition=Q(full_name__regex=r"\S"), name="custodian_name_required"),
            models.CheckConstraint(condition=Q(email__regex=r"\S"), name="custodian_email_required"),
        ]


class ConservedQuerySet(models.QuerySet):
    def delete(self):
        raise ValidationError("Los registros de inventario deben conservarse.")


class AppendOnlyQuerySet(ConservedQuerySet):
    def update(self, **kwargs):
        raise ValidationError("La auditoría no puede modificarse.")

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError("La auditoría no puede modificarse.")

    def bulk_create(self, objs, **kwargs):
        if kwargs.get("update_conflicts"):
            raise ValidationError("La auditoría no puede sobrescribirse.")
        return super().bulk_create(objs, **kwargs)


class Asset(models.Model):
    objects = ConservedQuerySet.as_manager()

    def delete(self, *args, **kwargs):
        raise ValidationError("Los activos deben conservarse.")

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
    faculty = models.ForeignKey(
        "Faculty", null=True, blank=True, on_delete=models.PROTECT, related_name="assets"
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
        ] + [
            models.CheckConstraint(
                condition=Q(**{field + "__regex": r"\S"}),
                name=f"asset_{field}_required",
            )
            for field in ["code", "name", "description", "brand", "model", "serial_number", "location"]
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


class Faculty(models.Model):
    """Identidad estable; el catálogo lo mantiene el Operador (T007)."""

    name = models.CharField(max_length=160)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(Lower(Trim("name")), name="faculty_name_unique"),
            models.CheckConstraint(condition=Q(name__regex=r"\S"), name="faculty_name_required"),
        ]

    def clean(self):
        self.name = self.name.strip()
        if not self.name:
            raise ValidationError({"name": "El nombre es obligatorio."})


def acquisition_currency():
    # Callable serializable por Django; el valor se persiste en cada documento.
    return settings.ASSET_CURRENCY_CODE


class AcquisitionDocument(models.Model):
    objects = ConservedQuerySet.as_manager()

    class Source(models.TextChoices):
        PURCHASE = "PURCHASE", "Compra"
        DONATION = "DONATION", "Donación"

    source = models.CharField(max_length=8, choices=Source.choices)
    reference = models.CharField(max_length=160)
    document_date = models.DateField(null=True, blank=True)
    supplier = models.CharField(max_length=160, blank=True)
    invoice_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    support_type = models.CharField(max_length=160, blank=True)
    currency = models.CharField(max_length=3, default=acquisition_currency, editable=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(condition=Q(reference__regex=r"\S"), name="acquisition_reference_required"),
            models.CheckConstraint(
                condition=(
                    Q(source="PURCHASE", document_date__isnull=False,
                      invoice_total__isnull=False, support_type="") & Q(supplier__regex=r"\S")
                    | Q(source="DONATION", invoice_total__isnull=True, supplier="") & Q(support_type__regex=r"\S")
                ), name="acquisition_source_fields_valid"),
        ]

    def clean(self):
        errors = {}
        self.reference = self.reference.strip()
        self.supplier = self.supplier.strip()
        self.support_type = self.support_type.strip()
        if not self.reference:
            errors["reference"] = "La referencia es obligatoria."
        if self.source == self.Source.PURCHASE:
            for field in ["document_date", "supplier", "invoice_total"]:
                if getattr(self, field) in (None, ""):
                    errors[field] = "Obligatorio para compra."
            if self.support_type:
                errors["support_type"] = "No corresponde a una compra."
        elif self.source == self.Source.DONATION:
            if not self.support_type:
                errors["support_type"] = "El tipo de respaldo es obligatorio."
            if self.supplier or self.invoice_total is not None:
                errors["source"] = "Una donación no admite proveedor ni total de factura."
        else:
            errors["source"] = "Origen inválido."
        if errors:
            raise ValidationError(errors)

    def delete(self, *args, **kwargs):
        raise ValidationError("Los documentos de adquisición deben conservarse.")


class AcquisitionLine(models.Model):
    objects = ConservedQuerySet.as_manager()

    document = models.ForeignKey(AcquisitionDocument, related_name="items", on_delete=models.PROTECT)
    asset = models.OneToOneField(Asset, related_name="acquisition_line", on_delete=models.PROTECT)
    item_value = models.DecimalField(max_digits=12, decimal_places=2)
    acquired_on = models.DateField(null=True, blank=True)
    date_unknown_reason = models.CharField(max_length=2000, blank=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(condition=(
                Q(acquired_on__isnull=False, date_unknown_reason="")
                | Q(acquired_on__isnull=True, date_unknown_reason__regex=r"\S")
            ), name="acquisition_date_alternative"),
        ]

    def clean(self):
        self.date_unknown_reason = self.date_unknown_reason.strip()
        if bool(self.acquired_on) == bool(self.date_unknown_reason):
            raise ValidationError({"acquired_on": "Indica fecha o motivo de desconocimiento, exclusivamente."})

    def delete(self, *args, **kwargs):
        raise ValidationError("Los registros de adquisición deben conservarse.")


class AuditEvidence(models.Model):
    """Protección ORM; T004 debe añadir triggers PostgreSQL contra SQL directo."""

    objects = AppendOnlyQuerySet.as_manager()

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    before_json = models.JSONField()
    after_json = models.JSONField()

    class Meta:
        abstract = True
        ordering = ["-id"]

    def clean(self):
        if hasattr(self, "reason") and not self.reason.strip():
            raise ValidationError({"reason": "El motivo es obligatorio."})

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("La auditoría no puede modificarse.")
        if kwargs.get("force_update"):
            raise ValidationError("La auditoría solo admite inserciones.")
        kwargs["force_insert"] = True
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("La auditoría debe conservarse.")


class AssetChange(AuditEvidence):
    asset = models.ForeignKey(Asset, related_name="metadata_changes", on_delete=models.PROTECT)
    reason = models.CharField(max_length=2000)
    resulting_revision = models.PositiveBigIntegerField()

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(condition=Q(reason__regex=r"\S"), name="asset_change_reason_required"),
            models.CheckConstraint(condition=Q(resulting_revision__gt=0), name="asset_change_revision_positive"),
            models.UniqueConstraint(fields=["asset", "resulting_revision"], name="asset_change_revision_unique"),
        ]


class CustodianChange(AuditEvidence):
    custodian = models.ForeignKey(Custodian, related_name="profile_changes", on_delete=models.PROTECT)


class AssetFacultyChange(AuditEvidence):
    asset = models.ForeignKey(Asset, related_name="faculty_changes", on_delete=models.PROTECT)
    previous_faculty = models.ForeignKey(Faculty, related_name="changes_from", on_delete=models.PROTECT)
    new_faculty = models.ForeignKey(Faculty, related_name="changes_to", on_delete=models.PROTECT)
    reason = models.CharField(max_length=2000)
    resulting_revision = models.PositiveBigIntegerField()

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(condition=Q(reason__regex=r"\S"), name="faculty_change_reason_required"),
            models.CheckConstraint(condition=Q(resulting_revision__gt=0), name="faculty_change_revision_positive"),
            models.UniqueConstraint(fields=["asset", "resulting_revision"], name="faculty_change_revision_unique"),
        ]


class AcquisitionDocumentChange(AuditEvidence):
    document = models.ForeignKey(AcquisitionDocument, related_name="changes", on_delete=models.PROTECT)
    reason = models.CharField(max_length=2000)
    # T006 crea este evento y un AssetChange por cada activo, en la misma transacción.

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(condition=Q(reason__regex=r"\S"), name="document_change_reason_required"),
        ]
