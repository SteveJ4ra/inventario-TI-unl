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

    def recovery_event_belongs_to_asset(self, recovery_event_id, asset_id):
        model = apps.get_model("inventory", "RecoveryEvent")
        return model.objects.filter(pk=recovery_event_id, asset_id=asset_id).exists()

    def _snapshot(self, asset):
        return snapshot(asset) | {"lifecycle_status": asset.lifecycle_status, "faculty_id": asset.faculty_id}

    def _audit(self, asset, actor_id, event_type, before, after, request=None):
        asset.revision += 1
        asset.save(update_fields=["revision", "lifecycle_status", "assignment", "current_custodian"])
        actor = get_user_model().objects.get(pk=actor_id)
        return RetirementAudit.objects.create(asset=asset, request=request, actor_id=actor_id, event_type=event_type, before=before, after=after | {"actor_label": actor.username}, resulting_revision=asset.revision)

    def _retire(self, asset_id, actor_id, reason, request=None):
        asset = Asset.objects.get(pk=asset_id)
        before = self._snapshot(asset)
        asset.lifecycle_status = "baja"
        asset.assignment = None
        asset.current_custodian_id = None
        after = self._snapshot(asset)
        self._audit(asset, actor_id, "retirement", before, after, request)
        movement = Movement.objects.create(asset=asset, type="baja", actor_id=actor_id, actor_label=get_user_model().objects.get(pk=actor_id).username, before=before, after=after, reason=reason, resulting_revision=asset.revision)
        return DecommissionEvent.objects.create(asset=asset, movement=movement, request=request, actor_id=actor_id, reason=reason)

    def save_normal_retirement(self, asset, actor_id, reason):
        return self._retire(asset.id, actor_id, reason)

    def save_request(self, asset, state, reviewer):
        obj = Asset.objects.get(pk=asset.id)
        request = DecommissionRequest.objects.create(asset=obj, requester_id=state.requester_id, assigned_reviewer_id=state.reviewer_id, asset_faculty_id=state.asset_faculty_id, reason=state.reason)
        self._audit(obj, state.requester_id, "retirement_requested", {}, {"reason": state.reason, "reviewer_id": reviewer.id, "reviewer_faculty_id": reviewer.faculty_id, "asset_faculty_id": state.asset_faculty_id}, request)
        return request

    def save_decision(self, asset, request, actor_id, state, reason, reviewer):
        record = DecommissionRequest.objects.get(pk=request.id)
        record.status = state.status
        record.save(update_fields=["status"])
        decision = ApprovalDecision.objects.create(request=record, reviewer_id=actor_id, outcome="approve" if state.status == "approved" else "reject", reason=reason)
        if state.status == "approved":
            self._retire(asset.id, actor_id, record.reason, record)
        else:
            self._audit(Asset.objects.get(pk=asset.id), actor_id, "retirement_rejected", {"status": "pending"}, {"status": state.status, "reason": reason, "reviewer_faculty_id": reviewer.faculty_id}, record)
        return decision

    def save_reassignment(self, asset, request, actor_id, state, reviewer):
        record = DecommissionRequest.objects.get(pk=request.id)
        previous = record.assigned_reviewer_id
        record.assigned_reviewer_id = reviewer.id
        record.save(update_fields=["assigned_reviewer"])
        self._audit(Asset.objects.get(pk=asset.id), actor_id, "retirement_reassigned", {"reviewer_id": previous}, {"reviewer_id": reviewer.id, "reviewer_faculty_id": reviewer.faculty_id}, record)
        return record

    def save_recovery_cancellation(self, asset, request, actor_id, state, cause, recovery_event_id):
        record = DecommissionRequest.objects.get(pk=request.id)
        record.status = state.status
        record.save(update_fields=["status"])
        self._audit(Asset.objects.get(pk=asset.id), actor_id, "retirement_cancelled", {"status": "pending"}, {"status": state.status, "cause": cause, "recovery_event_id": recovery_event_id}, record)
        return record
