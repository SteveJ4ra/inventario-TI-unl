import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from inventory.retirement_policy import validate_normal_retirement, validate_reviewer


class RetirementPolicyTests(unittest.TestCase):
    def test_normal_retirement_requires_eligible_state_and_reason(self):
        valid = dict(located=True, available=True, has_custodian=False, maintenance_active=False, reason="obsolescencia")
        validate_normal_retirement(**valid)
        for change in (dict(located=False), dict(available=False), dict(has_custodian=True), dict(maintenance_active=True), dict(reason="  ")):
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_normal_retirement(**(valid | change))

    def test_reviewer_requires_independent_active_other_faculty(self):
        valid = dict(requester_id=1, reviewer_id=2, asset_faculty_id=10, reviewer_faculty_id=20, reviewer_active=True)
        validate_reviewer(**valid)
        for change in (dict(reviewer_active=False), dict(reviewer_id=1), dict(reviewer_faculty_id=10), dict(asset_faculty_id=None), dict(reviewer_id=None)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_reviewer(**(valid | change))

    def test_reviewer_identifiers_and_active_flag_must_be_explicit(self):
        valid = dict(requester_id=1, reviewer_id=2, asset_faculty_id=10, reviewer_faculty_id=20, reviewer_active=True)
        for change in ({"reviewer_id": -1}, {"requester_id": True}, {"asset_faculty_id": 0}, {"reviewer_active": "false"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_reviewer(**(valid | change))

    def test_unknown_normal_retirement_flags_are_rejected(self):
        for value in (None, "false", 0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_normal_retirement(located=True, available=True, has_custodian=value, maintenance_active=False, reason="Baja")

    def test_reason_is_limited_at_domain_boundary(self):
        validate_normal_retirement(located=True, available=True, has_custodian=False, maintenance_active=False, reason=" " * 2000 + "Baja" + " " * 2000)
        with self.assertRaises(ValueError):
            validate_normal_retirement(located=True, available=True, has_custodian=False, maintenance_active=False, reason="x" * 2001)


if __name__ == "__main__":
    unittest.main()
