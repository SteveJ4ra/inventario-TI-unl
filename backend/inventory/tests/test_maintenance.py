from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import DatabaseError, IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from inventory.models import Asset, AssetTransition, Condition, Incident, MaintenanceEvent, Movement
from inventory.services import interrupt_maintenance
from inventory.tests.base import InventoryCase, asset_data, manager


class MaintenanceModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.actor = manager()
        cls.asset = Asset.objects.create(
            code="TI-000001", created_by=cls.actor, **asset_data()
        )

    def maintenance(self):
        return MaintenanceEvent.objects.create(
            asset=self.asset, started_by=self.actor, description="Revisión preventiva",
            workshop_location="Taller", previous_location=self.asset.location,
        )

    def test_only_one_active_maintenance_per_asset(self):
        event = self.maintenance()
        self.assertEqual(event.status, MaintenanceEvent.Status.IN_PROGRESS)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.condition, Condition.OPERATIONAL)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.maintenance()

    def test_completed_maintenance_requires_result_and_confirmed_location(self):
        event = self.maintenance()
        closed = dict(
            status=MaintenanceEvent.Status.COMPLETED, closed_by=self.actor,
            closed_at=timezone.now(), result="Revisado", receiving_location="Laboratorio",
            location_confirmed=True,
        )
        for invalid in ({"location_confirmed": False}, {"result": " "}, {"receiving_location": ""}):
            with self.subTest(invalid=invalid):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    MaintenanceEvent.objects.filter(pk=event.pk).update(**{**closed, **invalid})
        MaintenanceEvent.objects.filter(pk=event.pk).update(**closed)
        self.assertNotEqual(event.pk, self.maintenance().pk)

    def test_stolen_from_workshop_keeps_snapshot_and_interruption_has_no_result(self):
        event = self.maintenance()
        snapshot = {"id": event.pk, "status": event.status, "workshop_location": event.workshop_location}
        incident = Incident.objects.create(
            asset=self.asset, type=Incident.Type.STOLEN, description="Robo en taller",
            reported_by=self.actor, last_lifecycle_status=self.asset.lifecycle_status,
            last_condition=self.asset.condition, last_assignment=self.asset.assignment,
            last_location=event.workshop_location, active_maintenance_snapshot=snapshot,
        )
        interrupted = dict(
            status=MaintenanceEvent.Status.INTERRUPTED_UNLOCATED,
            closed_by=self.actor, closed_at=timezone.now(),
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            MaintenanceEvent.objects.filter(pk=event.pk).update(**interrupted, result="Reparado")
        MaintenanceEvent.objects.filter(pk=event.pk).update(**interrupted)
        event.refresh_from_db()
        incident.refresh_from_db()
        self.assertEqual(event.result, "")
        self.assertEqual(incident.last_location, "Taller")
        self.assertEqual(incident.active_maintenance_snapshot, snapshot)


class MaintenanceApiTests(InventoryCase):
    def start(self, asset, **changes):
        return self.client.post(
            f"/api/assets/{asset['id']}/maintenance/",
            {"description": "Revisión", "workshop_location": "Taller",
             "expected_revision": asset["revision"], **changes},
            format="json",
        )

    def close(self, event_id, revision, **changes):
        return self.client.post(
            f"/api/maintenance/{event_id}/close/",
            {"result": "Revisado", "receiving_location": "Recepción",
             "location_confirmed": True, "expected_revision": revision, **changes},
            format="json",
        )

    def detail(self, asset):
        return self.client.get(f"/api/assets/{asset['id']}/").json()

    def test_preventive_maintenance_blocks_delivery_and_closes_without_changing_condition(self):
        asset = self.new_asset()
        response = self.start(asset)
        self.assertEqual(response.status_code, 201, response.data)
        event = response.json()
        current = self.detail(asset)
        self.assertEqual(current["active_maintenance_id"], event["id"])
        self.assertEqual((current["location"], current["condition"]), ("Taller", "operativo"))
        self.assertEqual(current["assignment"], "disponible")
        self.assertIsNone(current["current_custodian"])
        self.assertEqual(self.client.get("/api/assets/?assignment=disponible").json()["count"], 0)
        detail = self.client.get(f"/api/maintenance/{event['id']}/").json()
        self.assertEqual((detail["previous_location"], detail["revision"]), ("Laboratorio", 1))
        self.assertEqual(detail["started_by_id"], self.actor.pk)
        self.assertTrue(detail["started_at"])
        person = self.person()
        delivery = {"custodian_id": person["id"], "destination": "Aula"}
        blocked = self.operation(current, "deliver", delivery)
        self.assertEqual((blocked.status_code, blocked.json()["code"]), (409, "maintenance_in_progress"))
        self.assertEqual(self.operation(current, "return", {
            "condition": "operativo", "reception_location": "Aula",
        }).status_code, 409)
        self.assertEqual(self.detail(asset)["revision"], 1)
        self.assertFalse(Movement.objects.exists())

        closer = manager("gestor-cierre")
        self.client.force_authenticate(closer)
        closed = self.close(event["id"], detail["revision"])
        self.assertEqual(closed.status_code, 200, closed.data)
        self.assertEqual(closed.json()["closed_by_id"], closer.pk)
        self.assertTrue(closed.json()["closed_at"])
        current = self.detail(asset)
        self.assertEqual((current["location"], current["condition"]), ("Recepción", "operativo"))
        self.assertIsNone(current["active_maintenance_id"])
        self.assertEqual(self.client.get("/api/assets/?assignment=disponible").json()["count"], 1)
        history = self.client.get(f"/api/assets/{asset['id']}/history/").json()
        self.assertEqual([row["resulting_revision"] for row in history], [2, 1])
        self.assertEqual(history[0]["data"]["after"]["event"]["result"], "Revisado")
        self.assertEqual(history[1]["data"]["after"]["event"]["status"], "in_progress")
        self.assertEqual(self.operation(current, "deliver", delivery).status_code, 201)

    def test_ineligible_duplicate_and_stale_start_leave_no_partial_writes(self):
        assigned = self.deliver(self.new_asset(), self.person())["asset"]
        self.assertEqual(self.start(assigned).status_code, 409)
        asset = self.new_asset(serial_number="LAB-002", condition="averiado")
        for fields in ({"description": " "}, {"workshop_location": ""}, {"started_by": 7}):
            self.assertEqual(self.start(asset, **fields).status_code, 400)
        Asset.objects.filter(pk=asset["id"]).update(lifecycle_status="no_localizado", assignment=None)
        self.assertEqual(self.start(asset).status_code, 409)
        self.assertFalse(AssetTransition.objects.exists())
        Asset.objects.filter(pk=asset["id"]).update(lifecycle_status="localizado", assignment="disponible")
        self.assertEqual(self.start(asset).status_code, 201)
        self.assertEqual(self.detail(asset)["condition"], "averiado")
        self.assertEqual(self.start(asset).json()["code"], "stale_revision")
        self.assertEqual(self.start(self.detail(asset)).json()["code"], "maintenance_in_progress")
        self.assertEqual(MaintenanceEvent.objects.count(), 1)
        self.assertEqual(AssetTransition.objects.count(), 1)

    def test_condition_is_a_separate_operation_and_old_movements_cannot_be_rectified(self):
        asset = self.new_asset()
        movement = self.operation(asset, "condition", {"condition": "averiado", "reason": "Daño"}).json()
        asset = movement["asset"]
        self.assertEqual(self.start(asset).status_code, 201)
        asset = self.detail(asset)
        self.assertIsNone(asset["rectifiable_movement_id"])
        self.assertEqual(self.operation(asset, "rectify", {
            "movement_id": movement["movement"]["id"], "reason": "Prueba",
        }).status_code, 409)
        changed = self.operation(asset, "condition", {"condition": "en_reparacion", "reason": "Diagnóstico"})
        self.assertEqual(changed.status_code, 201, changed.data)
        self.assertEqual(changed.json()["asset"]["location"], "Taller")
        self.assertEqual(MaintenanceEvent.objects.get().status, "in_progress")

    def test_corrective_maintenance_still_blocks_delivery_after_condition_change(self):
        asset = self.new_asset(condition="averiado")
        self.assertEqual(self.start(asset).status_code, 201)
        current = self.detail(asset)
        changed = self.operation(current, "condition", {
            "condition": "operativo", "reason": "Verificación técnica",
        })
        self.assertEqual(changed.status_code, 201, changed.data)
        current = changed.json()["asset"]
        response = self.operation(current, "deliver", {
            "custodian_id": self.person()["id"], "destination": "Aula",
        })
        self.assertEqual(
            (response.status_code, response.json()["code"]),
            (409, "maintenance_in_progress"),
        )
        self.assertEqual(self.detail(asset)["revision"], current["revision"])
        self.assertEqual(Movement.objects.count(), 1)

    def test_close_validation_and_evidence_failure_leave_maintenance_active(self):
        asset = self.new_asset()
        event_id = self.start(asset).json()["id"]
        for fields in (
            {"result": " "}, {"receiving_location": ""}, {"location_confirmed": False},
            {"location_confirmed": "true"}, {"closed_by_id": self.actor.pk},
        ):
            self.assertEqual(self.close(event_id, 1, **fields).status_code, 400)
        self.assertEqual(self.close(event_id, 0).json()["code"], "stale_revision")
        with patch("inventory.services.AssetTransition.objects.create", side_effect=IntegrityError):
            with self.assertRaises(IntegrityError):
                self.close(event_id, 1)
        self.assertEqual(MaintenanceEvent.objects.get().status, "in_progress")
        current = self.detail(asset)
        self.assertEqual((current["revision"], current["location"]), (1, "Taller"))
        self.assertEqual(AssetTransition.objects.count(), 1)
        with self.assertRaises(DatabaseError), transaction.atomic():
            AssetTransition.objects.all().update(actor_label="alterado")
        self.assertEqual(self.close(event_id, 1).status_code, 200)
        self.assertEqual(self.close(event_id, 2).status_code, 409)
        self.assertEqual(AssetTransition.objects.count(), 2)

    def test_permissions_and_csrf(self):
        asset = self.new_asset()
        event_id = self.start(asset).json()["id"]
        start_url = f"/api/assets/{asset['id']}/maintenance/"
        close_url = f"/api/maintenance/{event_id}/close/"
        outsider = get_user_model().objects.create_user("sin-gestor")
        for user in (None, outsider):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(f"/api/maintenance/{event_id}/").status_code, 403)
            self.assertEqual(self.start(asset).status_code, 403)
            self.assertEqual(self.close(event_id, 1).status_code, 403)
        session = APIClient(enforce_csrf_checks=True)
        session.force_login(self.actor)
        for url in (start_url, close_url):
            response = session.post(url, {}, format="json")
            self.assertEqual((response.status_code, response.json()["code"]), (403, "csrf_failed"))
        self.assertEqual(AssetTransition.objects.count(), 1)

    def test_internal_interruption_leaves_no_result_and_blocks_normal_close(self):
        asset = self.new_asset()
        event_id = self.start(asset).json()["id"]
        Asset.objects.filter(pk=asset["id"]).update(lifecycle_status="no_localizado", assignment=None)
        self.assertEqual(self.close(event_id, 1).status_code, 409)
        _, interrupted = interrupt_maintenance(
            maintenance_id=event_id, actor=self.actor, expected_revision=1
        )
        self.assertEqual((interrupted.status, interrupted.result), ("interrupted_unlocated", ""))
        self.assertIsNone(self.detail(asset)["active_maintenance_id"])
        self.assertEqual(AssetTransition.objects.count(), 2)
