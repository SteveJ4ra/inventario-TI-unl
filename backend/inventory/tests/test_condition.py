from .base import InventoryCase


class ConditionTests(InventoryCase):
    def test_real_changes_and_reversal(self):
        asset = self.new_asset(condition="averiado")
        for condition in ["en_reparacion", "operativo"]:
            response = self.operation(
                asset,
                "condition",
                {"condition": condition, "reason": "Revisión del equipo"},
            )
            self.assertEqual(response.status_code, 201, response.content)
            asset = response.json()["asset"]
        event = response.json()["movement"]
        reversed = self.operation(
            asset,
            "rectify",
            {"movement_id": event["id"], "reason": "Registro por error"},
        )
        self.assertEqual(reversed.status_code, 201)
        self.assertEqual(reversed.json()["asset"]["condition"], "en_reparacion")

    def test_requires_available_different_condition_and_reason(self):
        asset = self.new_asset()
        self.assertEqual(
            self.operation(
                asset, "condition", {"condition": "averiado", "reason": " "}
            ).status_code,
            400,
        )
        self.assertEqual(
            self.operation(
                asset, "condition", {"condition": "operativo", "reason": "R"}
            ).status_code,
            400,
        )
        assigned = self.deliver(asset, self.person())["asset"]
        self.assertEqual(
            self.operation(
                assigned, "condition", {"condition": "averiado", "reason": "R"}
            ).status_code,
            409,
        )
