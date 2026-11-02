from django.contrib.auth.models import Group
from django.db import transaction
from inventory.models import Movement
from inventory.retirement_models import DecommissionRequest, ApprovalDecision, RetirementAudit
from inventory.retirement_store import DjangoRetirementStore
from inventory.retirement_workflow import retire_normal, request_retirement, decide_retirement, cancel_for_recovery
from .test_models import RetirementFixtures
from .providers import RecoveryEvent


class RetirementStoreTests(RetirementFixtures):
    def setUp(self):
        super().setUp()
        self.requester.groups.add(Group.objects.create(name="Gestores"))
        self.reviewer.groups.add(Group.objects.create(name="Revisores"))
        profile=self.reviewer.reviewer_profile
        profile.must_change_password=False
        profile.save()
        self.store=DjangoRetirementStore()
    def test_normal_retirement_records_state_movement_and_audit(self):
        self.asset.lifecycle_status="localizado";self.asset.assignment="disponible";self.asset.save()
        event=retire_normal(self.store, asset_id=self.asset.id, actor_id=self.requester.id, expected_revision=0, reason="Obsolescencia")
        self.asset.refresh_from_db()
        self.assertEqual((self.asset.lifecycle_status,self.asset.revision), ("baja",1))
        self.assertEqual(event.movement.type,"baja")
        self.assertEqual(RetirementAudit.objects.get(asset=self.asset).resulting_revision,1)
    def test_request_approval_persists_and_is_not_repeatable(self):
        request=request_retirement(self.store,asset_id=self.asset.id,actor_id=self.requester.id,reviewer_id=self.reviewer.id,expected_revision=0,reason="Pérdida")
        decision=decide_retirement(self.store,asset_id=self.asset.id,request_id=request.id,actor_id=self.reviewer.id,expected_revision=1,decision="approve")
        self.assertEqual(decision.outcome,"approve")
        self.asset.refresh_from_db();self.assertEqual(self.asset.lifecycle_status,"baja")
        with self.assertRaises(ValueError): decide_retirement(self.store,asset_id=self.asset.id,request_id=request.id,actor_id=self.reviewer.id,expected_revision=2,decision="approve")
        self.assertEqual(ApprovalDecision.objects.count(),1)
    def test_outer_rollback_reverts_event_state_and_revision(self):
        self.asset.lifecycle_status="localizado";self.asset.assignment="disponible";self.asset.save()
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                retire_normal(self.store,asset_id=self.asset.id,actor_id=self.requester.id,expected_revision=0,reason="Prueba")
                raise RuntimeError("rollback exterior")
        self.asset.refresh_from_db();self.assertEqual(self.asset.revision,0)
        self.assertEqual(Movement.objects.count(),0);self.assertEqual(RetirementAudit.objects.count(),0)
    def test_recovery_cancellation_has_link_and_rolls_back_with_recovery(self):
        request=request_retirement(self.store,asset_id=self.asset.id,actor_id=self.requester.id,reviewer_id=self.reviewer.id,expected_revision=0,reason="Pérdida")
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                recovery=RecoveryEvent.objects.create(asset=self.asset)
                cancel_for_recovery(self.store,asset_id=self.asset.id,request_id=request.id,actor_id=self.requester.id,expected_revision=1,recovery_event_id=recovery.id)
                raise RuntimeError("fallo recuperación")
        request.refresh_from_db();self.assertEqual(request.status,"pending")
        self.assertEqual(RecoveryEvent.objects.count(),0)
