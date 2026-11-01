from unittest.mock import patch
from django.db import DatabaseError, connection, transaction
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from inventory.models import Asset, Movement
from .base import InventoryCase, manager


class CustodyTests(InventoryCase):
    def test_cycle_authors_locations_and_history(self):
        asset = self.new_asset()
        person = self.person()
        delivered = self.deliver(asset, person)
        current = delivered["asset"]
        self.assertEqual(
            (
                current["assignment"],
                current["location"],
                current["current_custodian"]["id"],
            ),
            ("asignado", "Aula", person["id"]),
        )
        second = manager("gestor2")
        self.client.force_authenticate(second)
        response = self.operation(
            current, "return", {"condition": "averiado", "reception_location": "Bodega"}
        )
        self.assertEqual(response.status_code, 201, response.content)
        returned = response.json()["asset"]
        self.assertEqual(
            (
                returned["assignment"],
                returned["condition"],
                returned["current_custodian"],
                returned["location"],
            ),
            ("disponible", "averiado", None, "Bodega"),
        )
        events = self.client.get(f"/api/assets/{asset['id']}/movements/").json()
        self.assertEqual([e["actor"]["id"] for e in events], [second.pk, self.actor.pk])
        self.assertEqual(events[0]["custodian"]["id"], person["id"])
        self.assertEqual(events[0]["before"]["condition"], "operativo")
        self.assertTrue(events[0]["occurred_at"])

    def test_invalid_states_stale_revision_and_forged_author(self):
        person = self.person()
        asset = self.new_asset()
        self.assertEqual(
            self.operation(
                asset, "return", {"condition": "operativo", "reception_location": "L"}
            ).status_code,
            409,
        )
        delivered = self.deliver(asset, person)["asset"]
        self.assertEqual(
            self.operation(
                delivered, "deliver", {"custodian_id": person["id"], "destination": "L"}
            ).status_code,
            409,
        )
        self.assertEqual(
            self.operation(
                asset, "return", {"condition": "operativo", "reception_location": "L"}
            ).json()["code"],
            "stale_revision",
        )
        self.assertEqual(
            self.operation(
                delivered,
                "return",
                {"condition": "operativo", "reception_location": "L", "actor": 999},
            ).status_code,
            400,
        )
        self.assertEqual(Movement.objects.count(), 1)
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.actor)
        self.assertEqual(
            client.post(
                f"/api/assets/{asset['id']}/return/",
                {
                    "expected_revision": 1,
                    "condition": "operativo",
                    "reception_location": "L",
                },
                format="json",
            ).status_code,
            403,
        )
        for condition in ["averiado", "en_reparacion"]:
            broken = self.new_asset(serial_number=condition, condition=condition)
            self.assertEqual(
                self.operation(
                    broken,
                    "deliver",
                    {"custodian_id": person["id"], "destination": "L"},
                ).status_code,
                409,
            )

    def test_event_failure_rolls_back_asset(self):
        asset = self.new_asset()
        person = self.person()
        with patch(
            "inventory.services.Movement.objects.create",
            side_effect=RuntimeError("simulated failure"),
        ):
            with self.assertRaises(RuntimeError):
                self.deliver(asset, person)
        row = Asset.objects.get(pk=asset["id"])
        self.assertEqual(
            (row.assignment, row.revision, row.location),
            ("disponible", 0, "Laboratorio"),
        )
        self.assertFalse(Movement.objects.exists())

    def test_original_immutable_in_model_and_database(self):
        asset = self.new_asset()
        self.deliver(asset, self.person())
        event = Movement.objects.get()
        with self.assertRaises(ValidationError):
            event.save()
        with self.assertRaises(ValidationError):
            event.delete()
        for sql in [
            "UPDATE inventory_movement SET note='changed'",
            "DELETE FROM inventory_movement",
        ]:
            with self.assertRaises(DatabaseError):
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute(sql)
