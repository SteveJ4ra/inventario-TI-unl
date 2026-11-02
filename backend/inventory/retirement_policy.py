"""Reglas de baja independientes de persistencia y proveedores 003/004.

El servicio que las invoque debe autenticar, bloquear filas y guardar los
eventos y la proyección dentro de una sola transacción de base de datos.
"""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class RetirementRequestState:
    requester_id: int
    reviewer_id: int
    asset_faculty_id: int
    reason: str
    status: str = "pending"


def require_text(value, code):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(code)
    return value.strip()


def validate_normal_retirement(*, located, available, has_custodian, maintenance_active, reason):
    require_text(reason, "reason_required")
    if not located or not available or has_custodian or maintenance_active:
        raise ValueError("ineligible_asset")


def validate_reviewer(*, requester_id, reviewer_id, asset_faculty_id, reviewer_faculty_id, reviewer_active):
    if not reviewer_active:
        raise ValueError("inactive_reviewer")
    if requester_id is None or reviewer_id is None or requester_id == reviewer_id:
        raise ValueError("independent_reviewer_required")
    if asset_faculty_id is None or reviewer_faculty_id is None:
        raise ValueError("faculty_required")
    if asset_faculty_id == reviewer_faculty_id:
        raise ValueError("different_faculty_required")


def create_request(*, unlocated, has_pending_request, requester_id, reviewer_id, asset_faculty_id, reviewer_faculty_id, reviewer_active, reason):
    reason = require_text(reason, "reason_required")
    if not unlocated or has_pending_request:
        raise ValueError("request_ineligible")
    validate_reviewer(requester_id=requester_id, reviewer_id=reviewer_id, asset_faculty_id=asset_faculty_id, reviewer_faculty_id=reviewer_faculty_id, reviewer_active=reviewer_active)
    return RetirementRequestState(requester_id, reviewer_id, asset_faculty_id, reason)


def decide_request(request, *, actor_id, reviewer_faculty_id, reviewer_active, unlocated, decision, reason=""):
    if request.status != "pending" or not unlocated:
        raise ValueError("request_not_pending")
    if actor_id != request.reviewer_id:
        raise ValueError("not_assigned_reviewer")
    validate_reviewer(requester_id=request.requester_id, reviewer_id=actor_id, asset_faculty_id=request.asset_faculty_id, reviewer_faculty_id=reviewer_faculty_id, reviewer_active=reviewer_active)
    if decision not in ("approve", "reject"):
        raise ValueError("invalid_decision")
    note = require_text(reason, "rejection_reason_required") if decision == "reject" else ""
    return replace(request, status="approved" if decision == "approve" else "rejected"), note


def reassign_request(request, *, is_operator, reviewer_id, reviewer_faculty_id, reviewer_active):
    if not is_operator:
        raise ValueError("operator_required")
    if request.status != "pending":
        raise ValueError("request_not_pending")
    validate_reviewer(requester_id=request.requester_id, reviewer_id=reviewer_id, asset_faculty_id=request.asset_faculty_id, reviewer_faculty_id=reviewer_faculty_id, reviewer_active=reviewer_active)
    return replace(request, reviewer_id=reviewer_id)


def cancel_on_recovery(request):
    if request.status != "pending":
        raise ValueError("request_not_pending")
    return replace(request, status="cancelled"), "ASSET_RECOVERED"
