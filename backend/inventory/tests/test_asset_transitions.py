from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import DatabaseError, IntegrityError, transaction
from django.http import Http404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from inventory.models import Asset, AssetTransition, Incident, MaintenanceEvent, Movement
from inventory.services import record_event_transition

from .base import InventoryCase


class AssetTransitionTests(InventoryCase):
    def transition(self, asset, apply, *, model=Incident, event_id=None, actor=None):
        return record_event_transition(
            asset_id=asset["id"], actor=actor or self.actor,
            expected_revision=asset["revision"], event_model=model,
            event_id=event_id, apply=apply,
        )

    def prepare_incident(self, asset, incident):
        incident.type = Incident.Type.OBSERVATION
        incident.description = "Observación ficticia"
        incident.reported_by = self.actor

    def test_event_blocks_rectification_and_preserves_legacy_history(self):
        asset = self.new_asset()
        delivery = self.deliver(asset, self.person())
        asset = delivery["asset"]
        legacy_url = f"/api/assets/{asset['id']}/movements/"
        legacy = self.client.get(legacy_url).json()
        _, incident = self.transition(asset, self.prepare_incident)

        detail = self.client.get(f"/api/assets/{asset['id']}/").json()
        self.assertEqual(detail["revision"], asset["revision"] + 1)
        self.assertIsNone(detail["rectifiable_movement_id"])
        response = self.operation(detail, "rectify", {
            "movement_id": delivery["movement"]["id"], "reason": "Intento obsoleto",
        })
        self.assertEqual((response.status_code, response.json()["code"]), (409, "ineligible_rectification"))
        self.assertEqual(self.client.get(legacy_url).json(), legacy)

        history = self.client.get(f"/api/assets/{asset['id']}/history/").json()
        self.assertEqual([event["event_type"] for event in history], ["incident", "movement"])
        self.assertEqual([event["resulting_revision"] for event in history], [2, 1])
        self.assertEqual(history[0]["actor"]["username"], self.actor.username)
        self.assertEqual(history[0]["data"]["projection_id"], incident.pk)
        self.assertIsNone(history[0]["data"]["before"]["event"])
        self.assertEqual(history[0]["data"]["after"]["event"]["description"], incident.description)

    def test_maintenance_detail_and_projection_changes_keep_original_evidence(self):
        asset = self.new_asset()

        def prepare(locked, maintenance):
            maintenance.started_by = self.actor
            maintenance.description = "Revisión ficticia"
            maintenance.previous_location = locked.location
            maintenance.workshop_location = "Taller"

        _, event = self.transition(asset, prepare, model=MaintenanceEvent)
        url = f"/api/maintenance/{event.pk}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual((response.json()["previous_location"], response.json()["revision"]), ("Laboratorio", 1))
        self.assertEqual(self.client.get("/api/maintenance/0/").status_code, 404)

        def update_projection(locked, maintenance):
            maintenance.status = MaintenanceEvent.Status.COMPLETED
            maintenance.closed_by = self.actor
            maintenance.closed_at = timezone.now()
            maintenance.result = "Revisado"
            maintenance.receiving_location = locked.location
            maintenance.location_confirmed = True

        self.transition(
            {**asset, "revision": 1}, update_projection, model=MaintenanceEvent,
            event_id=event.pk,
        )
        original, newer = AssetTransition.objects.order_by("resulting_revision")
        self.assertEqual(original.after["event"]["status"], "in_progress")
        self.assertEqual(newer.before["event"]["status"], "in_progress")
        self.assertEqual(newer.after["event"]["status"], "completed")
        self.assertEqual(self.client.get(url).json()["revision"], 2)
        for mutate in (
            lambda: AssetTransition.objects.filter(pk=original.pk).update(actor_label="alterado"),
            lambda: AssetTransition.objects.filter(pk=original.pk).delete(),
        ):
            with self.assertRaises(DatabaseError), transaction.atomic():
                mutate()
        self.assertEqual(AssetTransition.objects.count(), 2)

    def test_projection_from_another_asset_is_rejected(self):
        asset = self.new_asset()
        other = self.new_asset(serial_number="LAB-002")
        _, incident = self.transition(other, self.prepare_incident)
        with self.assertRaises(Http404):
            self.transition(asset, self.prepare_incident, event_id=incident.pk)
        self.assertEqual(Asset.objects.get(pk=asset["id"]).revision, 0)

    def test_audit_failure_rolls_back_asset_and_projection(self):
        asset = self.new_asset()

        def apply(locked, incident):
            self.prepare_incident(locked, incident)
            locked.location = "Cambio ficticio"

        with patch("inventory.services.AssetTransition.objects.create", side_effect=IntegrityError):
            with self.assertRaises(IntegrityError):
                self.transition(asset, apply)
        current = Asset.objects.get(pk=asset["id"])
        self.assertEqual((current.revision, current.location), (0, asset["location"]))
        self.assertFalse(Incident.objects.exists())
        self.assertFalse(AssetTransition.objects.exists())

    def test_existing_writes_reject_nonlocated_assets_without_partial_changes(self):
        asset = self.new_asset()
        Asset.objects.filter(pk=asset["id"]).update(
            lifecycle_status="no_localizado", assignment=None,
        )
        cases = {
            "deliver": {"custodian_id": self.person()["id"], "destination": "Aula"},
            "return": {"condition": "operativo", "reception_location": "Aula"},
            "condition": {"condition": "averiado", "reason": "Prueba"},
            "rectify": {"movement_id": 1, "reason": "Prueba"},
        }
        for route, payload in cases.items():
            with self.subTest(route=route):
                response = self.operation(asset, route, payload)
                self.assertEqual((response.status_code, response.json()["code"]), (409, "asset_not_located"))
        response = self.client.get(f"/api/assets/{asset['id']}/").json()
        self.assertEqual(response["lifecycle_status"], "no_localizado")
        self.assertIsNone(response["assignment"])
        self.assertIsNone(response["rectifiable_movement_id"])
        self.assertEqual(response["revision"], 0)
        self.assertFalse(Movement.objects.exists())

    def test_operator_and_reviewer_groups_do_not_grant_access(self):
        asset = self.new_asset()
        for name in ("Operadores", "Revisores"):
            with self.subTest(group=name):
                user = get_user_model().objects.create_user(name)
                user.groups.add(Group.objects.create(name=name))
                self.client.force_authenticate(user)
                self.assertEqual(self.client.get(f"/api/assets/{asset['id']}/history/").status_code, 403)
                self.assertEqual(self.client.get("/api/maintenance/1/").status_code, 403)
                self.assertEqual(self.operation(asset, "condition", {
                    "condition": "averiado", "reason": "Sin permiso",
                }).status_code, 403)
                with self.assertRaises(PermissionDenied):
                    self.transition(asset, self.prepare_incident, actor=user)
        self.assertEqual(Asset.objects.get(pk=asset["id"]).revision, 0)
        self.assertFalse(AssetTransition.objects.exists())
