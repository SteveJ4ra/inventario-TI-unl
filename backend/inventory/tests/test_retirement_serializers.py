from django.test import SimpleTestCase
from inventory.retirement_serializers import (NormalRetirementInput, RetirementRequestInput, RetirementDecisionInput, RetirementReassignmentInput, ReviewerCreateInput, ReviewerDeactivateInput, ReviewerPasswordChangeInput)


class RetirementInputTests(SimpleTestCase):
    def test_retirement_requires_revision_reason_and_rejects_reserved_author(self):
        for data in ({"reason": "  ", "expected_revision": 0}, {"reason": "Baja"}, {"reason": "Baja", "expected_revision": -1}, {"reason": "Baja", "expected_revision": 0, "actor": 1}):
            with self.subTest(data=data):
                self.assertFalse(NormalRetirementInput(data=data).is_valid())
        self.assertTrue(NormalRetirementInput(data={"reason": "Baja", "expected_revision": 0}).is_valid())

    def test_request_and_reassignment_require_positive_reviewer(self):
        for cls, payload in ((RetirementRequestInput, {"reason": "Pérdida", "expected_revision": 2, "reviewer_id": 0}), (RetirementReassignmentInput, {"expected_revision": 2, "reviewer_id": 0})):
            self.assertFalse(cls(data=payload).is_valid())
            payload["reviewer_id"] = 2
            self.assertTrue(cls(data=payload).is_valid())

    def test_rejection_requires_reason_and_approval_validates_choice(self):
        self.assertFalse(RetirementDecisionInput(data={"decision": "reject", "reason": "  ", "expected_revision": 1}).is_valid())
        self.assertFalse(RetirementDecisionInput(data={"decision": "invented", "expected_revision": 1}).is_valid())
        self.assertTrue(RetirementDecisionInput(data={"decision": "approve", "expected_revision": 1}).is_valid())
        self.assertTrue(RetirementDecisionInput(data={"decision": "reject", "reason": "Falta evidencia", "expected_revision": 1}).is_valid())

    def test_password_fields_preserve_spaces_and_are_write_only(self):
        create = ReviewerCreateInput(data={"username": "r", "faculty_id": 1, "password": " x "})
        self.assertTrue(create.is_valid(), create.errors)
        self.assertEqual(create.validated_data["password"], " x ")
        self.assertNotIn("password", create.data)
        change = ReviewerPasswordChangeInput(data={"current_password": " a ", "new_password": " b "})
        self.assertTrue(change.is_valid(), change.errors)
        self.assertEqual(change.validated_data["new_password"], " b ")
        self.assertNotIn("new_password", change.data)

    def test_deactivate_cannot_activate_or_accept_extra_fields(self):
        self.assertTrue(ReviewerDeactivateInput(data={"active": False}).is_valid())
        self.assertFalse(ReviewerDeactivateInput(data={"active": True}).is_valid())
        self.assertFalse(ReviewerDeactivateInput(data={"active": False, "actor": 1}).is_valid())
