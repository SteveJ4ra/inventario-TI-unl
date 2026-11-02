"""Modelos reales de 005. Registrar tras integrar Faculty/lifecycle de 003/004.

Los proveedores de contract_tests son exclusivamente de prueba. No usar
esa configuración para desarrollo con datos reales ni producción.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class ImmutableQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("El historial es inmutable.")
    def delete(self):
        raise ValidationError("El historial debe conservarse.")
    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError("El historial es inmutable.")


class ImmutableRecord(models.Model):
    objects = ImmutableQuerySet.as_manager()
    class Meta:
        abstract = True
    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("El historial es inmutable.")
        return super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        raise ValidationError("El historial debe conservarse.")


class ReviewerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reviewer_profile")
    faculty = models.ForeignKey("inventory.Faculty", on_delete=models.PROTECT)
    must_change_password = models.BooleanField(default=True)


class DecommissionRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        APPROVED = "approved", "Aprobada"
        REJECTED = "rejected", "Rechazada"
        CANCELLED = "cancelled", "Cancelada"
    asset = models.ForeignKey("inventory.Asset", on_delete=models.PROTECT, related_name="retirement_requests")
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="requested_retirements")
    assigned_reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="assigned_retirements")
    asset_faculty = models.ForeignKey("inventory.Faculty", on_delete=models.PROTECT)
    reason = models.CharField(max_length=2000)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    requested_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["asset"], condition=Q(status="pending"), name="retirement_one_pending"),
            models.CheckConstraint(condition=Q(status__in=["pending", "approved", "rejected", "cancelled"]), name="retirement_status_valid"),
            models.CheckConstraint(condition=~Q(reason=""), name="retirement_reason_required"),
            models.CheckConstraint(condition=~Q(requester=models.F("assigned_reviewer")), name="retirement_no_self_review"),
        ]


class ApprovalDecision(ImmutableRecord):
    request = models.OneToOneField(DecommissionRequest, on_delete=models.PROTECT, related_name="decision")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    outcome = models.CharField(max_length=8, choices=[("approve", "Aprobar"), ("reject", "Rechazar")])
    reason = models.CharField(max_length=2000, blank=True)
    decided_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(outcome__in=["approve", "reject"]), name="retirement_decision_valid"),
            models.CheckConstraint(condition=~Q(outcome="reject") | ~Q(reason=""), name="retirement_reject_reason"),
        ]


class DecommissionEvent(ImmutableRecord):
    asset = models.ForeignKey("inventory.Asset", on_delete=models.PROTECT)
    movement = models.OneToOneField("inventory.Movement", on_delete=models.PROTECT, related_name="retirement_event")
    request = models.OneToOneField(DecommissionRequest, null=True, blank=True, on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reason = models.CharField(max_length=2000)
    occurred_at = models.DateTimeField(auto_now_add=True)


class RetirementAudit(ImmutableRecord):
    asset = models.ForeignKey("inventory.Asset", on_delete=models.PROTECT)
    request = models.ForeignKey(DecommissionRequest, null=True, blank=True, on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    event_type = models.CharField(max_length=32)
    before = models.JSONField()
    after = models.JSONField()
    resulting_revision = models.PositiveBigIntegerField()
    occurred_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["asset", "resulting_revision"], name="retirement_audit_revision_unique")]
