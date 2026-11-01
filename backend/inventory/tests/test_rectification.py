from inventory.models import Movement
from .base import InventoryCase, manager


class RectificationTests(InventoryCase):
    def test_delivery_reversal_and_new_correct_operation(self):
        original = self.new_asset()
        person = self.person()
        delivery = self.deliver(original, person)
        self.client.force_authenticate(manager("otro"))
        response = self.operation(
            delivery["asset"],
            "rectify",
            {
                "movement_id": delivery["movement"]["id"],
                "reason": "Custodio seleccionado por error",
            },
        )
        self.assertEqual(response.status_code, 201, response.content)
        restored = response.json()["asset"]
        self.assertEqual(
            (
                restored["assignment"],
                restored["current_custodian"],
                restored["location"],
            ),
            ("disponible", None, original["location"]),
        )
        self.assertIsNone(restored["rectifiable_movement_id"])
        self.assertEqual(Movement.objects.count(), 2)
        self.deliver(restored, person)

    def test_return_reversal_does_not_enable_old_movement(self):
        original = self.new_asset()
        delivery = self.deliver(original, self.person())
        returned = self.operation(
            delivery["asset"],
            "return",
            {"condition": "averiado", "reception_location": "Bodega"},
        ).json()
        response = self.operation(
            returned["asset"],
            "rectify",
            {
                "movement_id": returned["movement"]["id"],
                "reason": "Condición incorrecta",
            },
        )
        self.assertEqual(response.status_code, 201, response.content)
        restored = response.json()["asset"]
        self.assertEqual(
            (restored["assignment"], restored["condition"], restored["location"]),
            ("asignado", "operativo", "Aula"),
        )
        self.assertEqual(
            restored["current_custodian"]["id"],
            delivery["asset"]["current_custodian"]["id"],
        )
        for target in [
            delivery["movement"]["id"],
            returned["movement"]["id"],
            response.json()["movement"]["id"],
            999999,
        ]:
            self.assertEqual(
                self.operation(
                    restored, "rectify", {"movement_id": target, "reason": "Error"}
                ).status_code,
                409,
            )
        self.assertEqual(Movement.objects.count(), 3)

    def test_reason_required_and_other_asset_rejected(self):
        first = self.deliver(self.new_asset(), self.person())
        second = self.new_asset(serial_number="SECOND")
        self.assertEqual(
            self.operation(
                first["asset"],
                "rectify",
                {"movement_id": first["movement"]["id"], "reason": " "},
            ).status_code,
            400,
        )
        self.assertEqual(
            self.operation(
                second,
                "rectify",
                {"movement_id": first["movement"]["id"], "reason": "Error"},
            ).status_code,
            409,
        )
