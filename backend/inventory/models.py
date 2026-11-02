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
        RETIREMENT = "baja", "Baja"
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
                        "baja",
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
                    ~Q(type__in=["rectificacion", "cambio_condicion", "baja"]) | ~Q(reason="")
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
