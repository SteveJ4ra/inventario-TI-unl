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

    def test_situation_filter_distinguishes_lifecycle_and_available(self):
        from inventory.models import Asset
        available = self.new_asset(serial_number="SITUATION-A")
        lost = self.new_asset(serial_number="SITUATION-B")
        retired = self.new_asset(serial_number="SITUATION-C")
        assigned = self.new_asset(serial_number="SITUATION-D")
        self.deliver(assigned, self.person())
        maintenance = self.new_asset(serial_number="SITUATION-E")
        response = self.operation(maintenance, "maintenance", {
            "description": "Revisión", "workshop_location": "Taller",
        })
        self.assertEqual(response.status_code, 201, response.content)
        Asset.objects.filter(pk=lost["id"]).update(lifecycle_status="no_localizado", assignment=None)
        Asset.objects.filter(pk=retired["id"]).update(lifecycle_status="baja", assignment=None)
        for situation, expected in (("disponible", available["id"]), ("asignado", assigned["id"]), ("no_localizado", lost["id"]), ("baja", retired["id"])):
            response = self.client.get("/api/assets/", {"situation": situation})
            self.assertEqual(response.status_code, 200, response.content)
            self.assertEqual([item["id"] for item in response.json()["results"]], [expected])
        self.assertEqual(self.client.get("/api/assets/", {"situation": "invalido"}).status_code, 400)
        response = self.client.get("/api/assets/", {
            "situation": "asignado", "search": "SITUATION-D", "category": "portatil",
        })
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(self.client.get("/api/assets/", {
            "situation": "asignado", "category": "monitor",
        }).json()["count"], 0)
        self.assertEqual(self.client.get("/api/assets/").json()["count"], 5)
