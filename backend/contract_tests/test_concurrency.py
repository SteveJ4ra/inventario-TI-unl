from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.contrib.auth.models import Group
from django.db import close_old_connections, transaction
from django.test import TransactionTestCase
from inventory.models import Asset
from inventory.retirement_models import DecommissionRequest, ApprovalDecision, DecommissionEvent
from inventory.retirement_store import DjangoRetirementStore
from inventory.retirement_workflow import retire_normal, request_retirement, decide_retirement, cancel_for_recovery
from .test_models import RetirementFixtures
from .providers import RecoveryEvent


class RetirementRaceTests(TransactionTestCase):
    def setUp(self):
        RetirementFixtures.setUp(self)
        self.requester.groups.add(Group.objects.create(name="Gestores"))
        self.reviewer.groups.add(Group.objects.create(name="Revisores"))
        profile=self.reviewer.reviewer_profile;profile.must_change_password=False;profile.save()
    def race(self, actions):
        barrier=Barrier(len(actions))
        def worker(action):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                action(DjangoRetirementStore())
                return "ok"
            except ValueError: return "conflict"
            finally: close_old_connections()
        with ThreadPoolExecutor(max_workers=len(actions)) as pool:
            return list(pool.map(worker,actions))
    def test_double_normal_retirement_only_creates_one_event(self):
        self.asset.lifecycle_status="localizado";self.asset.assignment="disponible";self.asset.save()
        def action(store): return retire_normal(store,asset_id=self.asset.id,actor_id=self.requester.id,expected_revision=0,reason="Obsolescencia")
        self.assertEqual(sorted(self.race([action,action])),["conflict","ok"])
        self.assertEqual(DecommissionEvent.objects.count(),1)
    def test_double_request_only_creates_one_pending(self):
        def action(store): return request_retirement(store,asset_id=self.asset.id,actor_id=self.requester.id,reviewer_id=self.reviewer.id,expected_revision=0,reason="Pérdida")
        self.assertEqual(sorted(self.race([action,action])),["conflict","ok"])
        self.assertEqual(DecommissionRequest.objects.filter(status="pending").count(),1)
    def test_recovery_and_approval_cannot_both_commit(self):
        request=request_retirement(DjangoRetirementStore(),asset_id=self.asset.id,actor_id=self.requester.id,reviewer_id=self.reviewer.id,expected_revision=0,reason="Pérdida")
        def approve(store): return decide_retirement(store,asset_id=self.asset.id,request_id=request.pk,actor_id=self.reviewer.id,expected_revision=1,decision="approve")
        def recover(store):
            with transaction.atomic():
                asset=Asset.objects.select_for_update().get(pk=self.asset.id)
                event=RecoveryEvent.objects.create(asset=asset,incident=self.incident)
                cancel_for_recovery(store,asset_id=asset.id,request_id=request.pk,actor_id=self.requester.id,expected_revision=1,recovery_event_id=event.pk)
                asset.refresh_from_db();asset.lifecycle_status="localizado";asset.assignment="disponible";asset.revision+=1;asset.save()
        self.assertEqual(sorted(self.race([approve,recover])),["conflict","ok"])
        request.refresh_from_db();self.asset.refresh_from_db()
        if request.status=="approved":
            self.assertEqual(self.asset.lifecycle_status,"baja");self.assertEqual(RecoveryEvent.objects.count(),0)
        else:
            self.assertEqual(request.status,"cancelled");self.assertEqual(ApprovalDecision.objects.count(),0)
            self.assertEqual(self.asset.lifecycle_status,"localizado")
