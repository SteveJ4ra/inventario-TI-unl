"""Proveedores mínimos SOLO de tests: no implementan 003/004 productivos."""
from django.db import models
from django.db.models import Q
from inventory.models import Asset, Movement


class Faculty(models.Model):
    name = models.CharField(max_length=160, unique=True)
    active = models.BooleanField(default=True)
    class Meta:
        app_label = "inventory"


class MaintenanceEvent(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT)
    status = models.CharField(max_length=32)
    class Meta:
        app_label = "inventory"


class RecoveryEvent(models.Model):
    incident = models.ForeignKey("inventory.Incident", on_delete=models.PROTECT)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT)
    class Meta:
        app_label = "inventory"


Asset.add_to_class("faculty", models.ForeignKey(Faculty, null=True, on_delete=models.PROTECT))
Asset.add_to_class("lifecycle_status", models.CharField(max_length=16, default="localizado"))
Asset._meta.get_field("assignment").null = True
Asset._meta.constraints = [constraint for constraint in Asset._meta.constraints if constraint.name != "asset_custody_consistent"]
Asset._meta.constraints.append(models.CheckConstraint(condition=(Q(lifecycle_status="localizado", assignment="disponible", current_custodian__isnull=True) | Q(lifecycle_status="localizado", assignment="asignado", current_custodian__isnull=False) | Q(lifecycle_status__in=["no_localizado", "baja"], assignment__isnull=True, current_custodian__isnull=True)), name="asset_custody_consistent"))

Movement._meta.constraints = [constraint for constraint in Movement._meta.constraints if constraint.name != "movement_type_valid"]
Movement._meta.constraints.append(models.CheckConstraint(condition=Q(type__in=["entrega", "devolucion", "cambio_condicion", "rectificacion", "baja"]), name="movement_type_valid"))


class Incident(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT)
    type = models.CharField(max_length=32)
    last_custodian_snapshot = models.JSONField(null=True)
    class Meta:
        app_label = "inventory"
