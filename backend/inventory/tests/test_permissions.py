from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from .base import AcquisitionFixtures


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class PermissionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "gestor", password="Fixture-only-42!"
        )
        self.group = Group.objects.create(name="Gestores")
        self.user.groups.add(self.group)
        self.client = APIClient(enforce_csrf_checks=True)

    def test_anonymous_and_non_manager_denied(self):
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 403)
        self.user.groups.clear()
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 403)

    def test_login_requires_csrf_and_logout_clears_session(self):
        payload = {"username": "gestor", "password": "Fixture-only-42!"}
        self.assertEqual(
            self.client.post("/api/auth/login/", payload, format="json").status_code,
            403,
        )
        token = self.client.get("/api/auth/csrf/").json()["csrfToken"]
        response = self.client.post(
            "/api/auth/login/", payload, format="json", HTTP_X_CSRFTOKEN=token
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.client.get("/api/auth/me/").json()["username"], "gestor")
        fresh = self.client.get("/api/auth/csrf/").json()["csrfToken"]
        self.assertEqual(
            self.client.post(
                "/api/auth/logout/", {}, format="json", HTTP_X_CSRFTOKEN=fresh
            ).status_code,
            200,
        )
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 403)

    def test_inactive_and_superuser_without_group_denied(self):
        self.user.is_active = False
        self.user.save()
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 403)
        admin = get_user_model().objects.create_superuser(
            "admin", password="Fixture-only-42!"
        )
        self.client.force_login(admin)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 403)

    def test_bad_credentials_generic(self):
        token = self.client.get("/api/auth/csrf/").json()["csrfToken"]
        response = self.client.post(
            "/api/auth/login/",
            {"username": "gestor", "password": "wrong"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("password", str(response.json().get("fields", {})))

    def test_login_rejects_non_object_json(self):
        token = self.client.get("/api/auth/csrf/").json()["csrfToken"]
        invalid_payloads = [
            [],
            [{"username": "gestor"}],
            ["username", "password"],
            "not-an-object",
            {"username": "gestor"},
            {"username": [], "password": "fixture"},
            {"username": "gestor", "password": 123},
            {"username": "gestor", "password": "fixture", "extra": True},
        ]
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.post(
                    "/api/auth/login/", payload, format="json", HTTP_X_CSRFTOKEN=token
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["code"], "invalid")
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 403)


# T002: contrato nuevo, deliberadamente rojo hasta T007; no altera PermissionTests.
@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class OperatorContractTests(AcquisitionFixtures, TestCase):
    def setUp(self):
        self.operator = get_user_model().objects.create_user(
            "operador", password="Fixture-only-42!")
        # Nombre técnico propuesto, simétrico a Gestores; no otorga permisos por sí solo.
        self.operator.groups.add(Group.objects.get_or_create(name="Operadores")[0])
        self.client = APIClient(enforce_csrf_checks=True)

    def test_operator_login_me_logout_without_inventory_access(self):
        token = self.client.get("/api/auth/csrf/").json()["csrfToken"]
        response = self.client.post("/api/auth/login/", {
            "username": "operador", "password": "Fixture-only-42!"
        }, format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200, response.content)
        session = self.client.get("/api/auth/me/")
        self.assertEqual(session.status_code, 200)
        self.assertIsInstance(session.json()["permissions"], list)
        self.assertFalse(session.json()["must_change_password"])
        for route in ["/api/assets/", "/api/custodians/", "/api/options/"]:
            self.assertEqual(self.client.get(route).status_code, 403, route)
        fresh = self.client.get("/api/auth/csrf/").json()["csrfToken"]
        self.assertEqual(self.client.post("/api/auth/logout/", {}, format="json",
                         HTTP_X_CSRFTOKEN=fresh).status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 403)

    def test_faculty_administration_requires_operator_and_csrf(self):
        self.client.force_login(self.operator)
        self.assertEqual(self.client.post("/api/operator/faculties/",
            {"name": "Facultad ficticia"}, format="json").status_code, 403)
        token = self.client.get("/api/auth/csrf/").json()["csrfToken"]
        response = self.client.post("/api/operator/faculties/",
            {"name": "Facultad ficticia"}, format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 201, response.content)
        faculty_id = response.json()["id"]
        self.assertEqual(self.client.patch(f"/api/operator/faculties/{faculty_id}/",
            {"name": "Nombre corregido"}, format="json",
            HTTP_X_CSRFTOKEN=token).status_code, 200)
        self.assertFalse(self.operator.groups.filter(name="Gestores").exists())

    def test_manager_cannot_administer_faculties_or_change_asset_faculty(self):
        from .base import manager
        actor = manager("otro_gestor")
        self.client.force_authenticate(actor)
        asset, faculty, _document = self.acquisition_asset(actor)
        before = {field.attname: getattr(asset, field.attname) for field in asset._meta.fields}
        response = self.client.post("/api/operator/faculties/",
                                   {"name": "No autorizada"}, format="json")
        self.assertEqual(response.status_code, 403, response.content)
        self.assertEqual(self.client.patch(f"/api/operator/assets/{asset.pk}/faculty/", {
            "faculty_id": faculty.pk, "reason": "Prueba", "expected_revision": asset.revision
        }, format="json").status_code, 403)
        asset.refresh_from_db()
        self.assertEqual({field.attname: getattr(asset, field.attname) for field in asset._meta.fields}, before)

    def test_operator_cannot_edit_asset_description(self):
        from .base import manager
        asset, _faculty, _document = self.acquisition_asset(manager("fixture_gestor"))
        before = asset.name, asset.revision
        self.client.force_authenticate(self.operator)
        self.assertEqual(self.client.patch(f"/api/assets/{asset.pk}/", {
            "name": "No autorizado", "reason": "Prueba", "expected_revision": 0
        }, format="json").status_code, 403)
        asset.refresh_from_db()
        self.assertEqual((asset.name, asset.revision), before)

    def test_local_provision_creates_only_operator(self):
        from importlib import import_module
        from io import StringIO
        from unittest.mock import patch
        from django.core.management import call_command
        try:
            command = import_module("inventory.management.commands.create_operator")
        except ModuleNotFoundError:
            self.fail("T007 pendiente: no existe create_operator")
        with patch("builtins.input", return_value="nuevo_operador"), patch.object(
            command, "getpass", return_value="OnlyCLI-Test-!2026"):
            call_command("create_operator", stdout=StringIO())
        user = get_user_model().objects.get(username="nuevo_operador")
        self.assertTrue(user.check_password("OnlyCLI-Test-!2026"))
        self.assertTrue(user.groups.filter(name="Operadores").exists())
        self.assertFalse(user.groups.filter(name="Gestores").exists())
        self.assertFalse(user.is_staff or user.is_superuser)

    def test_provision_password_mismatch_leaves_no_account(self):
        from importlib import import_module
        from io import StringIO
        from unittest.mock import patch
        from django.core.management import call_command, CommandError
        try:
            command = import_module("inventory.management.commands.create_operator")
        except ModuleNotFoundError:
            self.fail("T007 pendiente: no existe create_operator")
        with patch("builtins.input", return_value="no_creado"), patch.object(
            command, "getpass", side_effect=["One-Password-2026!", "Other-Password-2026!"]):
            with self.assertRaises(CommandError):
                call_command("create_operator", stdout=StringIO())
        self.assertFalse(get_user_model().objects.filter(username="no_creado").exists())

    def test_anonymous_and_inactive_operator_denied(self):
        self.assertEqual(self.client.get("/api/faculties/").status_code, 403)
        self.operator.is_active = False
        self.operator.save()
        self.client.force_login(self.operator)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 403)
        self.assertEqual(self.client.get("/api/faculties/").status_code, 403)
