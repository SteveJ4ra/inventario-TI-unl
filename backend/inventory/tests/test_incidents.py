from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from inventory.models import (
    Asset, AssetTransition, Assignment, Condition, Custodian, Incident,
    LifecycleStatus, MaintenanceEvent, Movement, RecoveryEvent,
)
from inventory.tests.base import InventoryCase, asset_data, manager


class IncidentModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.actor = manager()
        cls.custodian = Custodian.objects.create(
            full_name="Custodia ficticia", email="custodia@example.org"
        )

    def asset(self, **changes):
        return Asset.objects.create(
            code="TI-000001", created_by=self.actor, **asset_data(**changes)
        )

    def test_localized_asset_requires_valid_current_custody(self):
        asset = self.asset()
        self.assertEqual(asset.lifecycle_status, LifecycleStatus.LOCATED)
        for assignment, custodian in (
            (None, None), (None, self.custodian), ("", None),
            (Assignment.ASSIGNED, None), (Assignment.AVAILABLE, self.custodian),
        ):
            with self.subTest(assignment=assignment, custodian=custodian):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    Asset.objects.filter(pk=asset.pk).update(
                        assignment=assignment, current_custodian=custodian
                    )

    def test_nonlocated_states_require_null_assignment_and_custody(self):
        asset = self.asset()
        for status in (LifecycleStatus.UNLOCATED, LifecycleStatus.RETIRED):
            for assignment, custodian in (
                (Assignment.AVAILABLE, None), (None, self.custodian),
            ):
                with self.subTest(status=status, assignment=assignment):
                    with self.assertRaises(IntegrityError), transaction.atomic():
                        Asset.objects.filter(pk=asset.pk).update(
                            lifecycle_status=status, assignment=assignment,
                            current_custodian=custodian,
                        )
            Asset.objects.filter(pk=asset.pk).update(
                lifecycle_status=status, assignment=None, current_custodian=None
            )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Asset.objects.filter(pk=asset.pk).update(lifecycle_status="desconocido")

    def test_damage_and_observation_can_be_stored_without_changing_assignment(self):
        asset = self.asset(assignment=Assignment.ASSIGNED, current_custodian=self.custodian)
        for kind in (Incident.Type.DAMAGE, Incident.Type.OBSERVATION):
            Incident.objects.create(
                asset=asset, type=kind, description="Detalle", reported_by=self.actor
            )
        asset.refresh_from_db()
        self.assertEqual(asset.assignment, Assignment.ASSIGNED)
        self.assertEqual(asset.condition, Condition.OPERATIONAL)
        self.assertEqual(asset.current_custodian_id, self.custodian.pk)

    def test_loss_snapshot_survives_custody_change_and_recovery(self):
        asset = self.asset(assignment=Assignment.ASSIGNED, current_custodian=self.custodian)
        incident = Incident.objects.create(
            asset=asset, type=Incident.Type.LOST, description="Extraviado",
            reported_by=self.actor, last_lifecycle_status=asset.lifecycle_status,
            last_condition=asset.condition, last_assignment=asset.assignment,
            last_location=asset.location,
            last_custodian_snapshot={"id": self.custodian.pk, "full_name": self.custodian.full_name},
        )
        Asset.objects.filter(pk=asset.pk).update(
            lifecycle_status=LifecycleStatus.UNLOCATED, assignment=None, current_custodian=None
        )
        self.custodian.full_name = "Nombre actualizado"
        self.custodian.save(update_fields=["full_name"])
        recovery = RecoveryEvent.objects.create(
            asset=asset, incident=incident, found_by=self.actor,
            inspected_condition=Condition.BROKEN, recovered_location="Recepción",
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            RecoveryEvent.objects.create(
                asset=asset, incident=incident, found_by=self.actor,
                inspected_condition=Condition.OPERATIONAL, recovered_location="Recepción",
            )
        Asset.objects.filter(pk=asset.pk).update(
            lifecycle_status=LifecycleStatus.LOCATED, assignment=Assignment.AVAILABLE,
            condition=recovery.inspected_condition, location=recovery.recovered_location,
        )
        asset.refresh_from_db()
        incident.refresh_from_db()
        self.assertEqual(asset.code, "TI-000001")
        self.assertIsNone(asset.current_custodian_id)
        self.assertEqual(incident.last_assignment, Assignment.ASSIGNED)
        self.assertEqual(incident.last_condition, Condition.OPERATIONAL)
        self.assertEqual(incident.last_location, "Laboratorio")
        self.assertEqual(incident.last_custodian_snapshot["full_name"], "Custodia ficticia")

    def test_resolution_requires_note_and_is_reserved_for_damage_or_observation(self):
        asset = self.asset()
        for kind, note in ((Incident.Type.DAMAGE, " "), (Incident.Type.LOST, "Nota")):
            with self.subTest(kind=kind):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    Incident.objects.create(
                        asset=asset, type=kind, description="Detalle", reported_by=self.actor,
                        status=Incident.Status.RESOLVED, resolved_by=self.actor,
                        resolved_at=timezone.now(), resolution_note=note,
                    )


class IncidentApiTests(InventoryCase):
    def report(self, asset, **changes):
        return self.client.post(
            f"/api/assets/{asset['id']}/incidents/",
            {
                "type": "damage", "description": "Bisagra suelta",
                "expected_revision": asset["revision"], **changes,
            },
            format="json",
        )

    def resolve(self, incident_id, revision, **changes):
        return self.client.post(
            f"/api/incidents/{incident_id}/resolve/",
            {"expected_revision": revision, **changes},
            format="json",
        )

    def test_assigned_asset_report_and_resolution_preserve_custody_and_history(self):
        asset = self.deliver(self.new_asset(), self.person())["asset"]
        response = self.report(asset)
        self.assertEqual(response.status_code, 201, response.data)
        reported = response.json()
        self.assertEqual(reported["status"], "open")
        self.assertEqual(reported["reported_by"]["id"], self.actor.pk)
        self.assertTrue(reported["reported_at"])
        url = f"/api/assets/{asset['id']}/incidents/"
        self.assertEqual(self.client.get(url).json(), [reported])
        resolver = manager("gestor-resuelve")
        self.client.force_authenticate(resolver)
        response = self.resolve(
            reported["id"], asset["revision"] + 1, resolution_note="Se verificó el daño"
        )
        self.assertEqual(response.status_code, 200, response.data)
        resolved = response.json()
        self.assertEqual(resolved["status"], "resolved")
        self.assertEqual(resolved["resolved_by"]["id"], resolver.pk)
        self.assertTrue(resolved["resolved_at"])
        self.assertEqual(resolved["reported_at"], reported["reported_at"])
        self.assertEqual(resolved["reported_by"], reported["reported_by"])
        self.assertEqual(self.client.get(url).json(), [resolved])
        current = self.client.get(f"/api/assets/{asset['id']}/").json()
        for field in ("condition", "assignment", "current_custodian", "location"):
            self.assertEqual(current[field], asset[field])
        self.assertEqual(current["revision"], asset["revision"] + 2)
        history = self.client.get(f"/api/assets/{asset['id']}/history/").json()
        self.assertEqual([entry["event_type"] for entry in history], ["incident", "incident", "movement"])
        self.assertEqual(history[0]["data"]["before"]["event"]["status"], "open")
        self.assertEqual(history[0]["data"]["after"]["event"]["resolution_note"], "Se verificó el daño")
        self.assertEqual(history[1]["data"]["after"]["event"]["status"], "open")

    def test_invalid_input_cannot_create_or_resolve(self):
        asset = self.new_asset()
        for changes in (
            {"description": " "}, {"type": "invalid"}, {"reported_by": 3},
            {"expected_revision": -1}, {"reported_at": "2020-01-01"},
        ):
            with self.subTest(changes=changes):
                self.assertEqual(self.report(asset, **changes).status_code, 400)
        self.assertFalse(Incident.objects.exists())
        response = self.report(asset, type="observation")
        self.assertEqual(response.status_code, 201, response.data)
        incident_id = response.json()["id"]
        for changes in ({}, {"resolution_note": " "}, {"resolution_note": "Nota", "resolved_by": 7}):
            self.assertEqual(self.resolve(incident_id, 1, **changes).status_code, 400)
        self.assertEqual(Asset.objects.get(pk=asset["id"]).revision, 1)
        self.assertEqual(Incident.objects.get().status, "open")
        self.assertEqual(AssetTransition.objects.count(), 1)


    def test_conflicts_do_not_add_evidence(self):
        asset = self.new_asset()
        incident_id = self.report(asset).json()["id"]
        stale = self.report(asset)
        self.assertEqual((stale.status_code, stale.json()["code"]), (409, "stale_revision"))
        self.assertEqual(self.resolve(incident_id, 0, resolution_note="Nota").status_code, 409)
        self.assertEqual(self.resolve(incident_id, 1, resolution_note="Nota").status_code, 200)
        self.assertEqual(self.resolve(incident_id, 2, resolution_note="Otra nota").status_code, 409)
        self.assertEqual(self.resolve(0, 2, resolution_note="Nota").status_code, 404)
        self.assertEqual(Asset.objects.get(pk=asset["id"]).revision, 2)
        self.assertEqual(AssetTransition.objects.count(), 2)

    def test_read_and_write_require_manager_and_session_writes_require_csrf(self):
        asset = self.new_asset()
        incident_id = self.report(asset).json()["id"]
        url = f"/api/assets/{asset['id']}/incidents/"
        outsider = get_user_model().objects.create_user("sin-gestor")
        for user in (None, outsider):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.report(asset).status_code, 403)
            self.assertEqual(self.resolve(incident_id, 1, resolution_note="Nota").status_code, 403)
        session = APIClient(enforce_csrf_checks=True)
        session.force_login(self.actor)
        self.assertEqual(session.post(url, {}, format="json").status_code, 403)
        self.assertEqual(session.post(f"/api/incidents/{incident_id}/resolve/", {}, format="json").status_code, 403)
        self.assertEqual(AssetTransition.objects.count(), 1)

    def test_failed_resolution_audit_rolls_back_note_and_revision(self):
        asset = self.new_asset()
        incident_id = self.report(asset).json()["id"]
        with patch("inventory.services.AssetTransition.objects.create", side_effect=IntegrityError):
            with self.assertRaises(IntegrityError):
                self.resolve(incident_id, 1, resolution_note="Nota")
        incident = Incident.objects.get(pk=incident_id)
        self.assertEqual((incident.status, incident.resolution_note, incident.resolved_at), ("open", "", None))
        self.assertEqual(Asset.objects.get(pk=asset["id"]).revision, 1)
        self.assertEqual(AssetTransition.objects.count(), 1)

class LossRecoveryApiTests(InventoryCase):
    def report_loss(self, asset, kind="lost"):
        return self.client.post(
            f"/api/assets/{asset['id']}/incidents/",
            {"type": kind, "description": "No está en su ubicación",
             "expected_revision": asset["revision"]},
            format="json",
        )

    def recover(self, asset, **changes):
        return self.client.post(
            f"/api/assets/{asset['id']}/recover/",
            {"expected_revision": asset["revision"], "inspection_confirmed": True,
             "inspected_condition": "averiado", "recovered_location": "Recepción",
             "note": "Inspección ficticia", **changes},
            format="json",
        )

    def detail(self, asset):
        return self.client.get(f"/api/assets/{asset['id']}/").json()

    def start(self, asset):
        response = self.client.post(
            f"/api/assets/{asset['id']}/maintenance/",
            {"description": "Revisión", "workshop_location": "Taller",
             "expected_revision": asset["revision"]},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        return response.json()

    def test_loss_from_available_blocks_incompatible_actions(self):
        asset = self.new_asset()
        reported = self.report_loss(asset)
        self.assertEqual(reported.status_code, 201, reported.data)
        current = self.detail(asset)
        self.assertEqual(current["lifecycle_status"], "no_localizado")
        self.assertEqual(current["last_lifecycle_status"], "localizado")
        self.assertEqual(current["last_assignment"], "disponible")
        self.assertEqual(current["last_condition"], "operativo")
        self.assertEqual(current["last_location"], "Laboratorio")
        for key in ("assignment", "current_custodian", "last_custodian"):
            self.assertIsNone(current[key])
        for action, payload in (
            ("deliver", {"custodian_id": 1, "destination": "Aula"}),
            ("return", {"condition": "operativo", "reception_location": "Aula"}),
            ("condition", {"condition": "averiado", "reason": "Prueba"}),
            ("rectify", {"movement_id": 1, "reason": "Prueba"}),
        ):
            self.assertEqual(self.operation(current, action, payload).status_code, 409)
        self.assertEqual(self.report_loss(current).status_code, 409)
        self.assertEqual(self.client.post(
            f"/api/incidents/{reported.json()['id']}/resolve/",
            {"expected_revision": current["revision"], "resolution_note": "Nota"},
            format="json",
        ).status_code, 409)
        self.assertEqual(AssetTransition.objects.count(), 1)
        self.assertFalse(Movement.objects.exists())

    def test_loss_from_assigned_snapshots_custodian_and_preserves_movements(self):
        person = self.person()
        asset = self.deliver(self.new_asset(), person)["asset"]
        url = f"/api/assets/{asset['id']}/movements/"
        before = self.client.get(url).json()
        response = self.report_loss(asset, "stolen")
        self.assertEqual(response.status_code, 201, response.data)
        Custodian.objects.filter(pk=person["id"]).update(full_name="Nombre nuevo")
        current = self.detail(asset)
        self.assertEqual(current["last_assignment"], "asignado")
        self.assertEqual(current["last_custodian"]["full_name"], person["full_name"])
        self.assertEqual(current["last_location"], "Aula")
        self.assertIsNone(current["current_custodian"])
        self.assertIsNone(current["rectifiable_movement_id"])
        self.assertEqual(self.client.get(url).json(), before)
        self.assertEqual(self.client.get("/api/assets/?assignment=asignado").json()["count"], 0)

    def test_loss_during_maintenance_and_recovery_preserve_original_evidence(self):
        asset = self.new_asset()
        maintenance = self.start(asset)
        response = self.report_loss(self.detail(asset), "stolen")
        self.assertEqual(response.status_code, 201, response.data)
        incident = Incident.objects.get()
        self.assertEqual(incident.active_maintenance_snapshot["id"], maintenance["id"])
        self.assertEqual(incident.active_maintenance_snapshot["status"], "in_progress")
        self.assertEqual(incident.last_location, "Taller")
        event = MaintenanceEvent.objects.get()
        self.assertEqual((event.status, event.result), ("interrupted_unlocated", ""))
        current = self.detail(asset)
        self.assertIsNone(current["active_maintenance_id"])
        recovered = self.recover(current)
        self.assertEqual(recovered.status_code, 201, recovered.data)
        self.assertEqual(recovered.json()["found_by_id"], self.actor.pk)
        self.assertTrue(recovered.json()["found_at"])
        current = self.detail(asset)
        self.assertEqual((current["code"], current["condition"], current["location"]),
                         (asset["code"], "averiado", "Recepción"))
        self.assertEqual((current["lifecycle_status"], current["assignment"]), ("localizado", "disponible"))
        self.assertIsNone(current["current_custodian"])
        self.assertIsNone(current["active_maintenance_id"])
        self.assertIsNone(current["last_location"])
        incident.refresh_from_db()
        event.refresh_from_db()
        self.assertEqual(incident.status, "recovered")
        self.assertEqual(event.status, "interrupted_unlocated")
        self.assertEqual(self.recover(current).status_code, 409)
        history = self.client.get(f"/api/assets/{asset['id']}/history/").json()
        self.assertEqual([row["event_type"] for row in history],
                         ["recovery", "maintenance", "incident", "maintenance"])
        self.assertEqual([row["resulting_revision"] for row in history], [4, 3, 2, 1])
        self.assertEqual(history[0]["data"]["before"]["asset"]["lifecycle_status"], "no_localizado")
        self.assertEqual(history[2]["data"]["after"]["event"]["status"], "open")
        self.assertFalse(Movement.objects.exists())

    def test_recovery_validates_inspection_condition_location_and_revision(self):
        asset = self.new_asset()
        self.assertEqual(self.recover(asset).status_code, 409)
        self.assertEqual(self.report_loss(asset).status_code, 201)
        current = self.detail(asset)
        for fields in (
            {"inspection_confirmed": False}, {"inspection_confirmed": "true"},
            {"inspected_condition": ""}, {"recovered_location": " "}, {"found_by_id": self.actor.pk},
        ):
            self.assertEqual(self.recover(current, **fields).status_code, 400)
        self.assertEqual(self.recover(asset).json()["code"], "stale_revision")
        self.assertFalse(RecoveryEvent.objects.exists())
        self.assertEqual(AssetTransition.objects.count(), 1)

    def test_permissions_and_csrf_for_report_and_recovery(self):
        asset = self.new_asset()
        outsider = get_user_model().objects.create_user("sin-permiso-recuperar")
        for user in (None, outsider):
            self.client.force_authenticate(user)
            self.assertEqual(self.report_loss(asset).status_code, 403)
            self.assertEqual(self.recover(asset).status_code, 403)
        session = APIClient(enforce_csrf_checks=True)
        session.force_login(self.actor)
        for path in ("incidents", "recover"):
            response = session.post(f"/api/assets/{asset['id']}/{path}/", {}, format="json")
            self.assertEqual((response.status_code, response.json()["code"]), (403, "csrf_failed"))
        self.assertFalse(AssetTransition.objects.exists())

    def test_failed_interruption_rolls_back_report_and_asset(self):
        asset = self.new_asset()
        self.start(asset)
        create = AssetTransition.objects.create

        def fail_maintenance(**kwargs):
            if kwargs["event_type"] == "maintenance":
                raise IntegrityError
            return create(**kwargs)

        with patch("inventory.services.AssetTransition.objects.create", side_effect=fail_maintenance):
            with self.assertRaises(IntegrityError):
                self.report_loss(self.detail(asset))
        self.assertFalse(Incident.objects.exists())
        self.assertEqual(MaintenanceEvent.objects.get().status, "in_progress")
        current = self.detail(asset)
        self.assertEqual((current["lifecycle_status"], current["revision"]), ("localizado", 1))
        self.assertEqual(AssetTransition.objects.count(), 1)

    def test_failed_recovery_rolls_back_incident_status_and_asset(self):
        asset = self.new_asset()
        self.assertEqual(self.report_loss(asset).status_code, 201)
        with patch("inventory.services.AssetTransition.objects.create", side_effect=IntegrityError):
            with self.assertRaises(IntegrityError):
                self.recover(self.detail(asset))
        self.assertEqual(Incident.objects.get().status, "open")
        self.assertFalse(RecoveryEvent.objects.exists())
        current = self.detail(asset)
        self.assertEqual((current["lifecycle_status"], current["revision"]), ("no_localizado", 1))
        self.assertEqual(AssetTransition.objects.count(), 1)
