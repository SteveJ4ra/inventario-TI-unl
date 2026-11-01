from inventory.models import Asset
from inventory.services import create_asset
from .base import InventoryCase, asset_data


class QueryTests(InventoryCase):
    def test_empty_missing_and_pagination(self):
        self.assertEqual(self.client.get("/api/assets/").json()["results"], [])
        self.assertEqual(self.client.get("/api/assets/999999/").status_code, 404)
        for n in range(51):
            create_asset(actor=self.actor, data=asset_data(serial_number=str(n)))
        response = self.client.get("/api/assets/").json()
        self.assertEqual((response["count"], len(response["results"])), (51, 50))
        self.assertGreater(response["results"][0]["id"], response["results"][-1]["id"])
        self.assertTrue(response["next"])
        self.assertEqual(
            len(self.client.get("/api/assets/?page=2").json()["results"]), 1
        )
        for page in ["0", "abc", "3"]:
            self.assertEqual(
                self.client.get("/api/assets/", {"page": page}).status_code, 400
            )

    def test_history_links_and_reloads(self):
        asset = self.new_asset()
        delivery = self.deliver(asset, self.person())
        self.operation(
            delivery["asset"],
            "rectify",
            {"movement_id": delivery["movement"]["id"], "reason": "Error"},
        )
        events = self.client.get(f"/api/assets/{asset['id']}/movements/").json()
        self.assertEqual(len(events), 2)
        self.assertEqual(events[1]["rectified_by_id"], events[0]["id"])
        self.assertEqual(events[0]["rectifies_id"], events[1]["id"])
        self.assertEqual(
            self.client.get(f"/api/assets/{asset['id']}/").json()["code"], asset["code"]
        )
