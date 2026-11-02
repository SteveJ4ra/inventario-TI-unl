import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from inventory.retirement_policy import create_request, decide_request, reassign_request, cancel_on_recovery


class RequestPolicyTests(unittest.TestCase):
    def setUp(self):
        self.args = dict(unlocated=True, has_pending_request=False, requester_id=1, reviewer_id=2, asset_faculty_id=10, reviewer_faculty_id=20, reviewer_active=True, reason=" pérdida ")
        self.request = create_request(**self.args)

    def test_request_requires_unlocated_and_no_pending(self):
        self.assertEqual(self.request.reason, "pérdida")
        for change in (dict(unlocated=False), dict(has_pending_request=True), dict(reason=" ")):
            with self.subTest(change=change), self.assertRaises(ValueError):
                create_request(**(self.args | change))

    def test_rejection_requires_reason_and_preserves_original(self):
        args = dict(actor_id=2, reviewer_faculty_id=20, reviewer_active=True, unlocated=True, decision="reject")
        with self.assertRaises(ValueError):
            decide_request(self.request, **args)
        result, note = decide_request(self.request, **args, reason=" faltan datos ")
        self.assertEqual((result.status, note, self.request.status), ("rejected", "faltan datos", "pending"))

    def test_approval_rechecks_assignment_faculty_and_recovery(self):
        args = dict(actor_id=2, reviewer_faculty_id=20, reviewer_active=True, unlocated=True, decision="approve")
        for change in (dict(actor_id=3), dict(reviewer_faculty_id=10), dict(reviewer_active=False), dict(unlocated=False)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                decide_request(self.request, **(args | change))
        result, _ = decide_request(self.request, **args)
        self.assertEqual(result.status, "approved")
        with self.assertRaises(ValueError):
            decide_request(result, **args)

    def test_only_operator_reassigns_and_old_reviewer_cannot_decide(self):
        args = dict(reviewer_id=3, reviewer_faculty_id=30, reviewer_active=True)
        with self.assertRaises(ValueError):
            reassign_request(self.request, is_operator=False, **args)
        changed = reassign_request(self.request, is_operator=True, **args)
        with self.assertRaises(ValueError):
            decide_request(changed, actor_id=2, reviewer_faculty_id=20, reviewer_active=True, unlocated=True, decision="approve")
        self.assertEqual((self.request.reviewer_id, changed.reviewer_id), (2, 3))

    def test_recovery_cancels_and_prevents_later_approval(self):
        cancelled, cause = cancel_on_recovery(self.request)
        self.assertEqual((cancelled.status, cause), ("cancelled", "ASSET_RECOVERED"))
        with self.assertRaises(ValueError):
            decide_request(cancelled, actor_id=2, reviewer_faculty_id=20, reviewer_active=True, unlocated=True, decision="approve")
