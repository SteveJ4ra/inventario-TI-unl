import sys
import unittest
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from inventory.retirement_policy import RetirementRequestState
from inventory.retirement_workflow import AssetState, ReviewerState, RequestRecord, retire_normal, request_retirement, decide_retirement, reassign_retirement


class Store:
    """Doble de puerto solo de prueba; no sustituye PostgreSQL."""
    def __init__(self):
        self.asset = AssetState(1, "no_localizado", None, None, 10, 3, False)
        self.request = RequestRecord(7, 1, RetirementRequestState(1, 2, 10, "pérdida"))
        self.reviewers = {2: ReviewerState(2, 20, True), 3: ReviewerState(3, 30, True)}
        self.roles = {(1, "manager"), (2, "reviewer"), (9, "operator")}
        self.pending = False
        self.writes = []
        self.locks = []
    @contextmanager
    def atomic(self):
        yield
    def has_role(self, user_id, role): return (user_id, role) in self.roles
    def lock_asset(self, asset_id):
        self.locks.append("asset")
        if asset_id != self.asset.id: raise LookupError("asset")
        return self.asset
    def lock_request(self, request_id):
        self.locks.append("request")
        if request_id != self.request.id: raise LookupError("request")
        return self.request
    def reviewer(self, user_id): return self.reviewers[user_id]
    def has_pending_request(self, asset_id): return self.pending
    def save_normal_retirement(self, asset, actor_id, reason): self.writes.append(("retire", reason)); return "ok"
    def save_request(self, asset, state, reviewer): self.writes.append(("request", state)); return state
    def save_decision(self, asset, request, actor_id, state, reason, reviewer): self.writes.append(("decision", state.status)); return state
    def save_reassignment(self, asset, request, actor_id, state, reviewer): self.writes.append(("reassign", state.reviewer_id)); return state


class WorkflowTests(unittest.TestCase):
    def setUp(self): self.store = Store()
    def test_normal_retirement_requires_manager_and_eligible_state(self):
        self.store.asset = replace(self.store.asset, lifecycle="localizado", assignment="disponible")
        self.assertEqual(retire_normal(self.store, asset_id=1, actor_id=1, expected_revision=3, reason="obsolescencia"), "ok")
        self.store.writes.clear()
        with self.assertRaises(PermissionError): retire_normal(self.store, asset_id=1, actor_id=2, expected_revision=3, reason="x")
        self.assertEqual(self.store.writes, [])
    def test_request_rejects_stale_revision_and_duplicate(self):
        args = dict(asset_id=1, actor_id=1, reviewer_id=2, expected_revision=3, reason="pérdida")
        with self.assertRaises(ValueError): request_retirement(self.store, **(args | {"expected_revision": 2}))
        self.store.pending = True
        with self.assertRaises(ValueError): request_retirement(self.store, **args)
        self.assertEqual(self.store.writes, [])
        self.store.pending = False
        self.assertEqual(request_retirement(self.store, **args).reviewer_id, 2)
    def test_decision_locks_asset_first_and_checks_current_faculty(self):
        args = dict(asset_id=1, request_id=7, actor_id=2, expected_revision=3, decision="approve")
        self.store.reviewers[2] = ReviewerState(2, 10, True)
        with self.assertRaises(ValueError): decide_retirement(self.store, **args)
        self.assertEqual(self.store.writes, [])
        self.store.reviewers[2] = ReviewerState(2, 20, True)
        self.store.locks.clear()
        self.assertEqual(decide_retirement(self.store, **args).status, "approved")
        self.assertEqual(self.store.locks, ["asset", "request"])
    def test_decision_rejects_changed_faculty_and_recovered_asset(self):
        args = dict(asset_id=1, request_id=7, actor_id=2, expected_revision=3, decision="approve")
        for change in (dict(faculty_id=11), dict(lifecycle="localizado", assignment="disponible")):
            original=self.store.asset; self.store.asset=replace(original, **change)
            with self.subTest(change=change), self.assertRaises(ValueError): decide_retirement(self.store, **args)
            self.store.asset=original
        self.assertEqual(self.store.writes, [])
    def test_reassign_requires_operator_and_eligible_reviewer(self):
        args = dict(asset_id=1, request_id=7, actor_id=9, reviewer_id=3, expected_revision=3)
        with self.assertRaises(PermissionError): reassign_retirement(self.store, **(args | {"actor_id": 1}))
        self.assertEqual(reassign_retirement(self.store, **args).reviewer_id, 3)
    def test_reviewer_identity_mismatch_never_writes(self):
        self.store.reviewers[2] = ReviewerState(3, 20, True)
        with self.assertRaises(ValueError):
            request_retirement(self.store, asset_id=1, actor_id=1, reviewer_id=2, expected_revision=3, reason="pérdida")
        self.assertEqual(self.store.writes, [])

    def test_wrong_asset_and_request_returned_by_adapter_never_write(self):
        original_asset = self.store.asset
        self.store.lock_asset = lambda asset_id: replace(original_asset, id=99)
        with self.assertRaises(ValueError):
            request_retirement(self.store, asset_id=1, actor_id=1, reviewer_id=2, expected_revision=3, reason="pérdida")
        self.store.lock_asset = lambda asset_id: original_asset
        self.store.lock_request = lambda request_id: replace(self.store.request, id=99)
        with self.assertRaises(ValueError):
            decide_retirement(self.store, asset_id=1, request_id=7, actor_id=2, expected_revision=3, decision="approve")
        self.assertEqual(self.store.writes, [])

    def test_boolean_revision_and_actor_id_are_not_integers(self):
        for change in ({"expected_revision": True}, {"actor_id": True}):
            args = dict(asset_id=1, actor_id=1, reviewer_id=2, expected_revision=3, reason="pérdida") | change
            with self.subTest(change=change), self.assertRaises(ValueError):
                request_retirement(self.store, **args)
        self.assertEqual(self.store.writes, [])

    def test_unlocated_snapshot_cannot_keep_current_assignment_or_maintenance(self):
        for change in ({"assignment": "asignado", "custodian_id": 5}, {"maintenance_active": True}, {"faculty_id": None}):
            store = Store()
            store.asset = replace(store.asset, **change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                request_retirement(store, asset_id=1, actor_id=1, reviewer_id=2, expected_revision=3, reason="Pérdida")
            self.assertEqual(store.writes, [])
