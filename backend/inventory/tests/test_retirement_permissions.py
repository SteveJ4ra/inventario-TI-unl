from types import SimpleNamespace
from unittest.mock import MagicMock
from django.test import SimpleTestCase
from inventory.retirement_permissions import IsAssignedReviewer, IsReviewerAccount


def request_for(*, active=True, authenticated=True, member=True, faculty_id=10, must_change=False):
    user = SimpleNamespace(pk=2, is_active=active, is_authenticated=authenticated, reviewer_profile=SimpleNamespace(faculty_id=faculty_id, must_change_password=must_change), groups=MagicMock())
    user.groups.filter.return_value.exists.return_value = member
    return SimpleNamespace(user=user)


class ReviewerPermissionTests(SimpleTestCase):
    def test_temporary_password_allows_account_action_but_not_requests(self):
        request = request_for(must_change=True)
        self.assertTrue(IsReviewerAccount().has_permission(request, None))
        self.assertFalse(IsAssignedReviewer().has_permission(request, None))

    def test_missing_role_inactive_or_missing_faculty_denied(self):
        for args in ({"member": False}, {"active": False}, {"authenticated": False}, {"faculty_id": None}):
            with self.subTest(args=args):
                request = request_for(**args)
                self.assertFalse(IsReviewerAccount().has_permission(request, None))
                self.assertFalse(IsAssignedReviewer().has_permission(request, None))

    def test_only_assigned_reviewer_has_object_access(self):
        request = request_for()
        permission = IsAssignedReviewer()
        self.assertTrue(permission.has_object_permission(request, None, SimpleNamespace(assigned_reviewer_id=2)))
        self.assertFalse(permission.has_object_permission(request, None, SimpleNamespace(assigned_reviewer_id=3)))
        self.assertFalse(permission.has_object_permission(request, None, SimpleNamespace()))

    def test_absent_profile_fails_closed(self):
        request = request_for()
        del request.user.reviewer_profile
        self.assertFalse(IsAssignedReviewer().has_permission(request, None))
