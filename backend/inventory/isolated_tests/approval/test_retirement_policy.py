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


if __name__ == "__main__":
    unittest.main()
