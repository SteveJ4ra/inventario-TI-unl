"""Adaptador ORM 005; requiere modelos proveedores 003/004 registrados."""
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import Asset, Movement
from .retirement_models import ReviewerProfile, DecommissionRequest, ApprovalDecision, DecommissionEvent, RetirementAudit
from .retirement_policy import RetirementRequestState
from .retirement_workflow import AssetState, ReviewerState, RequestRecord
from .services import snapshot


class DjangoRetirementStore:
    def atomic(self): return transaction.atomic()

    def has_role(self, user_id, role):
        user = get_user_model().objects.filter(pk=user_id, is_active=True).first()
        if user is None: return False
        profile = ReviewerProfile.objects.filter(user_id=user_id).first()
        if profile and profile.must_change_password: return False
        groups = {"manager": "Gestores", "operator": "Operadores", "reviewer": "Revisores"}
        if not user.groups.filter(name=groups[role]).exists(): return False
        return role != "reviewer" or profile is not None

    def lock_asset(self, asset_id):
        asset = get_object_or_404(Asset.objects.select_for_update(), pk=asset_id)
        maintenance = apps.get_model("inventory", "MaintenanceEvent")
        return AssetState(asset.pk, asset.lifecycle_status, asset.assignment, asset.current_custodian_id, asset.faculty_id, asset.revision, maintenance.objects.filter(asset_id=asset_id, status="in_progress").exists())

    def lock_request(self, request_id):
        request = get_object_or_404(DecommissionRequest.objects.select_for_update(), pk=request_id)
        return RequestRecord(request.pk, request.asset_id, RetirementRequestState(request.requester_id, request.assigned_reviewer_id, request.asset_faculty_id, request.reason, request.status))

    def reviewer(self, user_id):
        user = get_object_or_404(get_user_model().objects.select_for_update(), pk=user_id)
        profile = get_object_or_404(ReviewerProfile.objects.select_for_update(), user_id=user_id)
        allowed = user.is_active and user.groups.filter(name="Revisores").exists()
        return ReviewerState(user.pk, profile.faculty_id, bool(allowed))

    def has_pending_request(self, asset_id):
        return DecommissionRequest.objects.filter(asset_id=asset_id, status="pending").exists()

    def recovery_event_belongs_to_asset(self, recovery_event_id, asset_id, request_id):
        model = apps.get_model("inventory", "RecoveryEvent")
        request = DecommissionRequest.objects.get(pk=request_id, asset_id=asset_id)
        incident_id = request.context_snapshot.get("incident_id")
        if incident_id is None:
            return False
        return model.objects.filter(pk=recovery_event_id, asset_id=asset_id, incident_id=incident_id).exists()

    def _reviewer_snapshot(self, user_id):
        profile = ReviewerProfile.objects.select_related("user", "faculty").get(user_id=user_id)
        return {"reviewer_id": user_id, "reviewer_label": profile.user.username, "reviewer_faculty_id": profile.faculty_id, "reviewer_faculty_label": profile.faculty.name}

    def _snapshot(self, asset):
        return snapshot(asset) | {"lifecycle_status": asset.lifecycle_status, "faculty_id": asset.faculty_id}

    def _audit(self, asset, actor_id, event_type, before, after, request=None, recovery_event_id=None):
        asset.revision += 1
        asset.save(update_fields=["revision", "lifecycle_status", "assignment", "current_custodian"])
        actor = get_user_model().objects.get(pk=actor_id)
        return RetirementAudit.objects.create(asset=asset, request=request, recovery_event_id=recovery_event_id, actor_id=actor_id, event_type=event_type, before=before, after=after | {"actor_label": actor.username}, resulting_revision=asset.revision)

    def _retire(self, asset_id, actor_id, reason, request=None):
        asset = Asset.objects.get(pk=asset_id)
        before = self._snapshot(asset)
        asset.lifecycle_status = "baja"
        asset.assignment = None
        asset.current_custodian_id = None
        after = self._snapshot(asset)
        if request is not None:
            after = after | self._reviewer_snapshot(actor_id) | {"request_id": request.pk}
        self._audit(asset, actor_id, "retirement", before, after, request)
        movement = Movement.objects.create(asset=asset, type="baja", actor_id=actor_id, actor_label=get_user_model().objects.get(pk=actor_id).username, before=before, after=after, reason=reason, resulting_revision=asset.revision)
        return DecommissionEvent.objects.create(asset=asset, movement=movement, request=request, actor_id=actor_id, reason=reason)

    def save_normal_retirement(self, asset, actor_id, reason):
        return self._retire(asset.id, actor_id, reason)

    def save_request(self, asset, state, reviewer):
        obj = Asset.objects.get(pk=asset.id)
        incident = apps.get_model("inventory", "Incident").objects.filter(asset_id=obj.pk, type__in=["lost", "stolen"], status="open").order_by("-reported_at", "-id").first()
        if incident is None:
            from .errors import Conflict
            raise Conflict("Se requiere el reporte de pérdida o robo del activo.")
        context = {"incident_id": incident.pk, "condition": obj.condition, "location": obj.location, "last_custodian": incident.last_custodian_snapshot if incident else None}
        request = DecommissionRequest.objects.create(context_snapshot=context, asset=obj, requester_id=state.requester_id, assigned_reviewer_id=state.reviewer_id, asset_faculty_id=state.asset_faculty_id, reason=state.reason)
        self._audit(obj, state.requester_id, "retirement_requested", {}, {"context": context, "reason": state.reason, "asset_faculty_id": state.asset_faculty_id, "asset_faculty_label": obj.faculty.name} | self._reviewer_snapshot(reviewer.id), request)
        return request

    def save_decision(self, asset, request, actor_id, state, reason, reviewer):
        record = DecommissionRequest.objects.get(pk=request.id)
        record.status = state.status
        record.save(update_fields=["status"])
        decision = ApprovalDecision.objects.create(request=record, reviewer_id=actor_id, outcome="approve" if state.status == "approved" else "reject", reason=reason)
        if state.status == "approved":
            self._retire(asset.id, actor_id, record.reason, record)
        else:
            self._audit(Asset.objects.get(pk=asset.id), actor_id, "retirement_rejected", {"status": "pending"}, {"status": state.status, "reason": reason} | self._reviewer_snapshot(reviewer.id), record)
        return decision

    def save_reassignment(self, asset, request, actor_id, state, reviewer):
        record = DecommissionRequest.objects.get(pk=request.id)
        previous = record.assigned_reviewer_id
        record.assigned_reviewer_id = reviewer.id
        record.save(update_fields=["assigned_reviewer"])
        self._audit(Asset.objects.get(pk=asset.id), actor_id, "retirement_reassigned", {"reviewer_id": previous}, self._reviewer_snapshot(reviewer.id), record)
        return record

    def save_recovery_cancellation(self, asset, request, actor_id, state, cause, recovery_event_id):
        record = DecommissionRequest.objects.get(pk=request.id)
        record.status = state.status
        record.save(update_fields=["status"])
        self._audit(Asset.objects.get(pk=asset.id), actor_id, "retirement_cancelled", {"status": "pending"}, {"status": state.status, "cause": cause, "recovery_event_id": recovery_event_id}, record, recovery_event_id=recovery_event_id)
        return record


def assert_faculty_change_allowed(asset_id):
    """Invocar dentro de la transacción de cambio de facultad de 003."""
    from django.db import connection
    from .errors import Conflict
    if not connection.in_atomic_block:
        raise RuntimeError("La comprobación requiere la transacción de cambio de facultad.")
    get_object_or_404(Asset.objects.select_for_update(), pk=asset_id)
    if DecommissionRequest.objects.filter(asset_id=asset_id, status="pending").exists():
        raise Conflict("No se cambia la facultad mientras exista una solicitud pendiente.")
