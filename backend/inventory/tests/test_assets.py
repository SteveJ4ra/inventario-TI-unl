from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from .base import InventoryCase, asset_data


class AssetTests(InventoryCase):
    def test_creation_code_fields_and_stability(self):
        asset = self.new_asset()
        self.assertRegex(asset["code"], r"^TI-\d{6,}$")
        self.assertEqual(
            (asset["assignment"], asset["current_custodian"], asset["revision"]),
            ("disponible", None, 0),
        )
        self.assertNotEqual(asset["name"], asset["description"])
        self.assertEqual(
            self.client.get(f"/api/assets/{asset['id']}/").json()["code"], asset["code"]
        )
        other = self.new_asset(serial_number="LAB-002")
        self.assertGreater(other["code"], asset["code"])

    def test_duplicates_normalized_but_internal_characters_preserved(self):
        self.new_asset()
        response = self.client.post(
            "/api/assets/",
            asset_data(brand=" ejemplo ", model=" a1 ", serial_number=" lab-001 "),
            format="json",
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "duplicate_asset")
        self.new_asset(serial_number="LAB001")

    def test_required_lengths_choices_and_reserved_fields(self):
        for field in asset_data():
            with self.subTest(field=field):
                data = asset_data()
                data[field] = "   "
                self.assertEqual(
                    self.client.post("/api/assets/", data, format="json").status_code,
                    400,
                )
        for field, limit in [
            ("name", 160),
            ("description", 2000),
            ("brand", 120),
            ("model", 120),
            ("serial_number", 160),
            ("location", 240),
        ]:
            self.assertEqual(
                self.client.post(
                    "/api/assets/",
                    asset_data(**{field: "X" * (limit + 1)}),
                    format="json",
                ).status_code,
                400,
            )
        for field, value in [
            ("code", "TI-999999"),
            ("assignment", "asignado"),
            ("current_custodian", 1),
            ("created_by", 1),
            ("revision", 10),
            ("condition", "otro"),
            ("category", "FPGA"),
        ]:
            self.assertEqual(
                self.client.post(
                    "/api/assets/", {**asset_data(), field: value}, format="json"
                ).status_code,
                400,
            )

    def test_custodian_email_unique_without_domain_restriction_no_user(self):
        before = get_user_model().objects.count()
        person = self.person(email=" Docente@otro.edu ")
        self.assertEqual(person["department"], "")
        self.assertEqual(get_user_model().objects.count(), before)
        self.assertEqual(
            self.client.post(
                "/api/custodians/",
                {"full_name": "Otra persona", "email": "docente@OTRO.edu"},
                format="json",
            ).status_code,
            409,
        )
        for email in ["", "no-es-correo"]:
            self.assertEqual(
                self.client.post(
                    "/api/custodians/",
                    {"full_name": "Persona", "email": email},
                    format="json",
                ).status_code,
                400,
            )

    def test_session_writes_require_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.actor)
        self.assertEqual(
            client.post("/api/assets/", asset_data(), format="json").status_code, 403
        )
        token = client.get("/api/auth/csrf/").json()["csrfToken"]
        self.assertEqual(
            client.post(
                "/api/assets/", asset_data(), format="json", HTTP_X_CSRFTOKEN=token
            ).status_code,
            201,
        )

    def test_only_six_categories_and_no_edit_delete(self):
        asset = self.new_asset(condition="averiado")
        self.assertEqual(len(self.client.get("/api/options/").json()["categories"]), 6)
        for method in ["put", "patch", "delete"]:
            self.assertEqual(
                getattr(self.client, method)(
                    f"/api/assets/{asset['id']}/", {}, format="json"
                ).status_code,
                405,
            )

    def test_data_endpoints_require_manager_and_unicode_identity(self):
        asset = self.new_asset(brand="ÁRBOL")
        response = self.client.post(
            "/api/assets/", asset_data(brand=" árbol "), format="json"
        )
        self.assertEqual(response.status_code, 409)
        self.client.force_authenticate(user=None)
        for url in [
            "/api/assets/",
            "/api/custodians/",
            "/api/options/",
            f"/api/assets/{asset['id']}/",
            f"/api/assets/{asset['id']}/movements/",
        ]:
            self.assertEqual(self.client.get(url).status_code, 403, url)
