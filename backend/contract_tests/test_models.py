from django.contrib.auth import get_user_model
from django.db import IntegrityError, DatabaseError, transaction, connection
from django.test import TestCase
from django.core.exceptions import ValidationError
from inventory.models import Asset
from inventory.retirement_models import ReviewerProfile, DecommissionRequest, ApprovalDecision
from .providers import Faculty


class RetirementFixtures(TestCase):
    def setUp(self):
        self.requester = get_user_model().objects.create(username="gestor")
        self.reviewer = get_user_model().objects.create(username="revisor")
        self.faculty = Faculty.objects.create(name="Facultad A")
        self.other = Faculty.objects.create(name="Facultad B")
        ReviewerProfile.objects.create(user=self.reviewer, faculty=self.other)
        self.asset = Asset.objects.create(code="TI-900001", name="Equipo", description="Prueba", category="monitor", brand="Marca", model="M", serial_number="S", location="A", condition="averiado", assignment=None, lifecycle_status="no_localizado", faculty=self.faculty, created_by=self.requester)
    def create_request(self):
        return DecommissionRequest.objects.create(asset=self.asset, requester=self.requester, assigned_reviewer=self.reviewer, asset_faculty=self.faculty, reason="Pérdida")


class RetirementModelTests(RetirementFixtures):
    def test_one_pending_and_no_self_review(self):
        self.create_request()
        with self.assertRaises(IntegrityError), transaction.atomic(): self.create_request()
        with self.assertRaises(IntegrityError), transaction.atomic():
            DecommissionRequest.objects.create(asset=self.asset, requester=self.requester, assigned_reviewer=self.requester, asset_faculty=self.faculty, reason="Pérdida")
    def test_decision_requires_reason_and_is_immutable(self):
        request = self.create_request()
        with self.assertRaises(IntegrityError), transaction.atomic(): ApprovalDecision.objects.create(request=request, reviewer=self.reviewer, outcome="reject", reason="")
        decision = ApprovalDecision.objects.create(request=request, reviewer=self.reviewer, outcome="reject", reason="Falta evidencia")
        with self.assertRaises(ValidationError): decision.save()
        with self.assertRaises(ValidationError): ApprovalDecision.objects.filter(pk=decision.pk).update(reason="otro")
        with self.assertRaises(ValidationError): decision.delete()
    def test_profile_requires_password_change(self):
        self.assertTrue(self.reviewer.reviewer_profile.must_change_password)

    def test_direct_sql_cannot_rewrite_decision(self):
        request = self.create_request()
        decision = ApprovalDecision.objects.create(request=request, reviewer=self.reviewer, outcome="reject", reason="Revisar")
        with self.assertRaises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
            cursor.execute("UPDATE inventory_approvaldecision SET reason=%s WHERE id=%s", ["alterado", decision.id])
        decision.refresh_from_db()
        self.assertEqual(decision.reason, "Revisar")
