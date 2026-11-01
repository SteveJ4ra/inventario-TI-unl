from .base import InventoryCase


class SearchTests(InventoryCase):
    def test_search_each_field_and_filters_and_current_custodian(self):
        asset = self.new_asset()
        person = self.person()
        current = self.deliver(asset, person)["asset"]
        self.new_asset(serial_number="other", category="monitor", location="Bodega")
        for term in [
            asset["code"].lower(),
            "PORTÁ",
            "ejEMP",
            "a1",
            "lab-0",
            "docente",
            "EXAMPLE.ORG",
        ]:
            result = self.client.get("/api/assets/", {"search": term}).json()
            self.assertIn(asset["id"], [a["id"] for a in result["results"]], term)
        filters = {
            "category": "portatil",
            "condition": "operativo",
            "assignment": "asignado",
            "location": "Aula",
            "custodian": person["id"],
            "search": "lab-",
        }
        self.assertEqual(self.client.get("/api/assets/", filters).json()["count"], 1)
        self.assertEqual(
            self.client.get("/api/assets/", {**filters, "location": "Bodega"}).json()[
                "count"
            ],
            0,
        )
        self.operation(
            current,
            "return",
            {"condition": "operativo", "reception_location": "Laboratorio"},
        )
        self.assertEqual(
            self.client.get("/api/assets/", {"search": person["email"]}).json()[
                "count"
            ],
            0,
        )
        for key, value in [
            ("category", "FPGA"),
            ("condition", "malo"),
            ("assignment", "otro"),
            ("custodian", "abc"),
        ]:
            self.assertEqual(
                self.client.get("/api/assets/", {key: value}).status_code, 400
            )
