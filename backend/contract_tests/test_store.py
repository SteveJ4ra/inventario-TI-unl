from django.contrib.auth.models import Group
from django.db import transaction
from inventory.models import Movement
from inventory.errors import Conflict
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
                recovery=RecoveryEvent.objects.create(asset=self.asset,incident=self.incident)
                cancel_for_recovery(self.store,asset_id=self.asset.id,request_id=request.id,actor_id=self.requester.id,expected_revision=1,recovery_event_id=recovery.id)
                raise RuntimeError("fallo recuperación")
        request.refresh_from_db();self.assertEqual(request.status,"pending")
        self.assertEqual(RecoveryEvent.objects.count(),0)

    def test_rectify_latest_retirement_restores_snapshot_without_erasing_event(self):
        from inventory.services import record_operation
        from inventory.retirement_models import DecommissionEvent
        self.asset.lifecycle_status="localizado";self.asset.assignment="disponible";self.asset.save()
        event=retire_normal(self.store,asset_id=self.asset.id,actor_id=self.requester.id,expected_revision=0,reason="Error de registro")
        asset, correction=record_operation(asset_id=self.asset.id,actor=self.requester,operation="rectificacion",data={"expected_revision":1,"movement_id":event.movement_id,"reason":"Activo equivocado"})
        self.assertEqual((asset.lifecycle_status,asset.assignment,asset.revision),("localizado","disponible",2))
        self.assertEqual(correction.rectifies_id,event.movement_id)
        self.assertTrue(DecommissionEvent.objects.filter(pk=event.pk).exists())
        with self.assertRaises(Conflict):
            record_operation(asset_id=asset.id,actor=self.requester,operation="rectificacion",data={"expected_revision":2,"movement_id":event.movement_id,"reason":"Repetir"})

    def test_rectify_approved_retirement_keeps_approval_and_unlocated(self):
        from inventory.services import record_operation
        request=request_retirement(self.store,asset_id=self.asset.id,actor_id=self.requester.id,reviewer_id=self.reviewer.id,expected_revision=0,reason="Pérdida")
        decide_retirement(self.store,asset_id=self.asset.id,request_id=request.id,actor_id=self.reviewer.id,expected_revision=1,decision="approve")
        movement=Movement.objects.get(asset=self.asset,type="baja")
        asset,_=record_operation(asset_id=self.asset.id,actor=self.requester,operation="rectificacion",data={"expected_revision":2,"movement_id":movement.pk,"reason":"Registro equivocado"})
        self.assertEqual((asset.lifecycle_status,asset.assignment,asset.current_custodian_id),("no_localizado",None,None))
        request.refresh_from_db();self.assertEqual(request.status,"approved")
        self.assertTrue(ApprovalDecision.objects.filter(request=request).exists())

    def test_pending_request_blocks_faculty_change_guard(self):
        from inventory.retirement_store import assert_faculty_change_allowed
        request_retirement(self.store,asset_id=self.asset.id,actor_id=self.requester.id,reviewer_id=self.reviewer.id,expected_revision=0,reason="Pérdida")
        with self.assertRaises(Conflict): assert_faculty_change_allowed(self.asset.id)

    def test_request_faculty_and_reviewer_labels_are_snapshots(self):
        request=request_retirement(self.store,asset_id=self.asset.id,actor_id=self.requester.id,reviewer_id=self.reviewer.id,expected_revision=0,reason="Pérdida")
        audit=RetirementAudit.objects.get(request=request)
        previous=audit.after["reviewer_faculty_label"]
        self.other.name="Renombrada";self.other.save()
        audit.refresh_from_db();self.assertEqual(audit.after["reviewer_faculty_label"],previous)

    def test_active_maintenance_blocks_normal_retirement_in_database_service(self):
        from .providers import MaintenanceEvent
        self.asset.lifecycle_status="localizado";self.asset.assignment="disponible";self.asset.save()
        MaintenanceEvent.objects.create(asset=self.asset,status="in_progress")
        with self.assertRaises(ValueError):
            retire_normal(self.store,asset_id=self.asset.id,actor_id=self.requester.id,expected_revision=0,reason="Daño")
        self.asset.refresh_from_db();self.assertEqual(self.asset.lifecycle_status,"localizado")
        self.assertEqual(Movement.objects.count(),0)

    def test_previous_recovery_cannot_cancel_new_incident_request(self):
        from .providers import Incident
        old=RecoveryEvent.objects.create(asset=self.asset,incident=self.incident)
        new_loss=Incident.objects.create(asset=self.asset,type="lost",last_custodian_snapshot=None)
        request=request_retirement(self.store,asset_id=self.asset.id,actor_id=self.requester.id,reviewer_id=self.reviewer.id,expected_revision=0,reason="Nueva pérdida")
        with self.assertRaises(ValueError):
            cancel_for_recovery(self.store,asset_id=self.asset.id,request_id=request.id,actor_id=self.requester.id,expected_revision=1,recovery_event_id=old.pk)
        request.refresh_from_db();self.assertEqual(request.status,"pending")
        event=RecoveryEvent.objects.create(asset=self.asset,incident=new_loss)
        cancel_for_recovery(self.store,asset_id=self.asset.id,request_id=request.id,actor_id=self.requester.id,expected_revision=1,recovery_event_id=event.pk)
        from django.db.models.deletion import ProtectedError
        with self.assertRaises(ProtectedError): event.delete()

    def test_no_request_without_loss_report_and_no_partial_writes(self):
        self.incident.delete()
        with self.assertRaises(Conflict):
            request_retirement(self.store,asset_id=self.asset.id,actor_id=self.requester.id,reviewer_id=self.reviewer.id,expected_revision=0,reason="Sin reporte")
        self.asset.refresh_from_db();self.assertEqual(self.asset.revision,0)
        self.assertEqual(DecommissionRequest.objects.count(),0)
        self.assertEqual(RetirementAudit.objects.count(),0)
