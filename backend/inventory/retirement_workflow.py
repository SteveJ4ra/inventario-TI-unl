"""Orquestación 005 sobre un puerto transaccional; aún sin adaptador ORM.

El adaptador real deberá implementar bloqueos, persistencia inmutable y
revisiones conforme a contratos-transversales.md. No instalar rutas hasta
que las features 003/004 y el adaptador estén integrados y probados.
"""

from dataclasses import dataclass
from typing import ContextManager, Protocol

from .retirement_policy import (
    RetirementRequestState, create_request, decide_request,
    reassign_request, validate_normal_retirement, require_id,
)


@dataclass(frozen=True)
class AssetState:
    id: int
    lifecycle: str
    assignment: str | None
    custodian_id: int | None
    faculty_id: int | None
    revision: int
    maintenance_active: bool


@dataclass(frozen=True)
class ReviewerState:
    id: int
    faculty_id: int | None
    active: bool


@dataclass(frozen=True)
class RequestRecord:
    id: int
    asset_id: int
    state: RetirementRequestState


class RetirementStore(Protocol):
    """Puerto: métodos de escritura deben crear eventos y aumentar revisión.

    atomic debe revertir todas las escrituras ante cualquier excepción;
    lock_asset y lock_request deben bloquear filas hasta salir de atomic.
    Las comprobaciones de roles incluyen cuenta activa y cambio inicial de
    contraseña completado cuando corresponda. No hay implementación falsa
    de este protocolo en producción.
    """
    def atomic(self) -> ContextManager: ...
    def has_role(self, user_id: int, role: str) -> bool: ...
    def lock_asset(self, asset_id: int) -> AssetState: ...
    def lock_request(self, request_id: int) -> RequestRecord: ...
    def reviewer(self, user_id: int) -> ReviewerState:
        """Retorna el revisor solicitado y protege sus datos vigentes ante cambios concurrentes."""
        ...
    def has_pending_request(self, asset_id: int) -> bool: ...
    def save_normal_retirement(self, asset: AssetState, actor_id: int, reason: str): ...
    def save_request(self, asset: AssetState, state: RetirementRequestState, reviewer: ReviewerState): ...
    def save_decision(self, asset: AssetState, request: RequestRecord, actor_id: int, state: RetirementRequestState, reason: str, reviewer: ReviewerState): ...
    def save_reassignment(self, asset: AssetState, request: RequestRecord, actor_id: int, state: RetirementRequestState, reviewer: ReviewerState): ...


def _authorize(store: RetirementStore, user_id: int, role: str) -> None:
    require_id(user_id)
    if store.has_role(user_id, role) is not True:
        raise PermissionError("forbidden")


def _asset(store: RetirementStore, asset_id: int, expected_revision: int) -> AssetState:
    require_id(asset_id)
    if type(expected_revision) is not int or expected_revision < 0:
        raise ValueError("invalid_revision")
    asset = store.lock_asset(asset_id)
    if type(asset.id) is not int or asset.id != asset_id:
        raise ValueError("asset_identity_mismatch")
    if type(asset.revision) is not int or asset.revision != expected_revision:
        raise ValueError("stale_revision")
    return asset


def _request_for_asset(store: RetirementStore, request_id: int, asset: AssetState) -> RequestRecord:
    require_id(request_id)
    request = store.lock_request(request_id)
    if type(request.id) is not int or request.id != request_id:
        raise ValueError("request_identity_mismatch")
    if request.asset_id != asset.id:
        raise ValueError("request_asset_mismatch")
    if request.state.asset_faculty_id != asset.faculty_id:
        raise ValueError("asset_faculty_changed")
    return request


def _require_unlocated(asset: AssetState) -> None:
    if (
        asset.lifecycle != "no_localizado"
        or asset.assignment is not None
        or asset.custodian_id is not None
        or asset.maintenance_active is not False
    ):
        raise ValueError("inconsistent_unlocated_state")
    require_id(asset.faculty_id, "faculty_required")


def retire_normal(store: RetirementStore, *, asset_id: int, actor_id: int, expected_revision: int, reason: str):
    with store.atomic():
        _authorize(store, actor_id, "manager")
        asset = _asset(store, asset_id, expected_revision)
        validate_normal_retirement(located=asset.lifecycle == "localizado", available=asset.assignment == "disponible", has_custodian=asset.custodian_id is not None, maintenance_active=asset.maintenance_active, reason=reason)
        return store.save_normal_retirement(asset, actor_id, reason.strip())


def request_retirement(store: RetirementStore, *, asset_id: int, actor_id: int, reviewer_id: int, expected_revision: int, reason: str):
    with store.atomic():
        _authorize(store, actor_id, "manager")
        asset = _asset(store, asset_id, expected_revision)
        require_id(reviewer_id)
        reviewer = store.reviewer(reviewer_id)
        if type(reviewer.id) is not int or reviewer.id != reviewer_id:
            raise ValueError("reviewer_identity_mismatch")
        _require_unlocated(asset)
        state = create_request(unlocated=asset.lifecycle == "no_localizado", has_pending_request=store.has_pending_request(asset.id), requester_id=actor_id, reviewer_id=reviewer.id, asset_faculty_id=asset.faculty_id, reviewer_faculty_id=reviewer.faculty_id, reviewer_active=reviewer.active, reason=reason)
        return store.save_request(asset, state, reviewer)


def decide_retirement(store: RetirementStore, *, asset_id: int, request_id: int, actor_id: int, expected_revision: int, decision: str, reason: str = ""):
    with store.atomic():
        _authorize(store, actor_id, "reviewer")
        asset = _asset(store, asset_id, expected_revision)
        request = _request_for_asset(store, request_id, asset)
        reviewer = store.reviewer(actor_id)
        if type(reviewer.id) is not int or reviewer.id != actor_id:
            raise ValueError("reviewer_identity_mismatch")
        _require_unlocated(asset)
        state, note = decide_request(request.state, actor_id=actor_id, reviewer_faculty_id=reviewer.faculty_id, reviewer_active=reviewer.active, unlocated=asset.lifecycle == "no_localizado", decision=decision, reason=reason)
        return store.save_decision(asset, request, actor_id, state, note, reviewer)


def reassign_retirement(store: RetirementStore, *, asset_id: int, request_id: int, actor_id: int, reviewer_id: int, expected_revision: int):
    with store.atomic():
        _authorize(store, actor_id, "operator")
        asset = _asset(store, asset_id, expected_revision)
        request = _request_for_asset(store, request_id, asset)
        _require_unlocated(asset)
        require_id(reviewer_id)
        reviewer = store.reviewer(reviewer_id)
        if type(reviewer.id) is not int or reviewer.id != reviewer_id:
            raise ValueError("reviewer_identity_mismatch")
        state = reassign_request(request.state, is_operator=True, reviewer_id=reviewer.id, reviewer_faculty_id=reviewer.faculty_id, reviewer_active=reviewer.active)
        return store.save_reassignment(asset, request, actor_id, state, reviewer)
