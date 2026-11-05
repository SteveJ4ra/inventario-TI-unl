"""T007: sesión real/CSRF, separación de roles y endpoints aprobados."""
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from inventory.models import Asset, Faculty, AcquisitionDocument, AcquisitionLine, AssetChange, AssetFacultyChange
from .base import AcquisitionFixtures, asset_data, manager
from .test_acquisitions import purchase


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class OperatorApiTests(AcquisitionFixtures, TestCase):
    def setUp(self):
        self.gestor = manager()
        self.operator = get_user_model().objects.create_user("operator", password="Fixture-only-42!")
        self.operator.groups.add(Group.objects.get_or_create(name="Operadores")[0])
        self.client = APIClient(enforce_csrf_checks=True)

    def session(self, user):
        self.client.force_login(user)
        return {"HTTP_X_CSRFTOKEN": self.client.get("/api/auth/csrf/").json()["csrfToken"]}

    def test_operator_session_permissions_and_csrf(self):
        token = self.client.get("/api/auth/csrf/").json()["csrfToken"]
        response = self.client.post("/api/auth/login/", {"username": "operator", "password": "Fixture-only-42!"},
                                    format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["permissions"], ["faculties.manage"])
        self.assertFalse(response.json()["must_change_password"])
        for route in ["/api/assets/", "/api/custodians/", "/api/options/", "/api/imports/templates/assets/"]:
            self.assertEqual(self.client.get(route).status_code, 403, route)
        self.assertEqual(self.client.post("/api/operator/faculties/", {"name": "Ficticia"}, format="json").status_code, 403)
        self.assertEqual(Faculty.objects.count(), 0)
        token = self.client.get("/api/auth/csrf/").json()["csrfToken"]
        self.assertEqual(self.client.post("/api/auth/logout/", {}, format="json", HTTP_X_CSRFTOKEN=token).status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 403)

    def test_catalog_normalized_unique_and_references_preserved(self):
        headers = self.session(self.operator)
        response = self.client.post("/api/operator/faculties/", {"name": " Ficticia A "}, format="json", **headers)
        self.assertEqual(response.status_code, 201, response.content)
        faculty_id = response.json()["id"]
        response = self.client.post("/api/operator/faculties/", {"name": "ficticia a"}, format="json", **headers)
        self.assertEqual(response.status_code, 409, response.content)
        self.assertEqual(Faculty.objects.count(), 1)
        for data in [{"name": "   "}, {"created_by": 1}, {"id": 100}]:
            self.assertEqual(self.client.patch(f"/api/operator/faculties/{faculty_id}/", data, format="json", **headers).status_code, 400)
        asset, faculty, _doc = self.acquisition_asset(self.gestor)
        response = self.client.patch(f"/api/operator/faculties/{faculty.pk}/", {"name": "Nombre corregido", "active": False},
                                     format="json", **headers)
        self.assertEqual(response.status_code, 200)
        asset.refresh_from_db()
        self.assertEqual(asset.faculty_id, faculty.pk)
        self.assertNotIn(faculty.pk, [row["id"] for row in self.client.get("/api/faculties/").json()])
        self.assertEqual(self.client.delete(f"/api/operator/faculties/{faculty.pk}/", **headers).status_code, 405)

    def test_operator_changes_faculty_when_no_request_is_pending(self):
        asset, faculty, _doc = self.acquisition_asset(self.gestor)
        other = Faculty.objects.create(name="Otra facultad ficticia")
        headers = self.session(self.operator)
        response = self.client.patch(f"/api/operator/assets/{asset.pk}/faculty/",
            {"faculty_id": other.pk, "reason": "Cambio solicitado", "expected_revision": asset.revision}, format="json", **headers)
        self.assertEqual(response.status_code, 200, response.content)
        asset.refresh_from_db()
        self.assertEqual((asset.faculty_id, asset.revision), (other.pk, 1))
        self.assertEqual(AssetFacultyChange.objects.count(), 1)

    def test_rejected_login_removes_previous_authorized_session(self):
        self.session(self.operator)
        token = self.client.get("/api/auth/csrf/").json()["csrfToken"]
        response = self.client.post("/api/auth/login/", {"username": "operator", "password": "wrong"},
                                    format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 403)

    def test_anonymous_inactive_and_unassigned_roles_are_denied(self):
        for route in ["/api/faculties/", "/api/acquisitions/1/", "/api/assets/1/history/"]:
            self.assertEqual(self.client.get(route).status_code, 403)
        user = get_user_model().objects.create_superuser("admin_fixture", password="Fixture-only-42!")
        self.session(user)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 403)
        self.operator.is_active = False
        self.operator.save()
        self.session(self.operator)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 403)
        self.assertEqual(self.client.get("/api/faculties/").status_code, 403)

    def test_operator_provision_rejects_existing_username_without_changing_account(self):
        before = self.operator.password
        with patch("builtins.input", return_value="operator"), patch(
            "inventory.management.commands.create_operator.getpass", return_value="OnlyCLI-Test-!2026"):
            with self.assertRaises(CommandError):
                call_command("create_operator", stdout=StringIO())
        self.operator.refresh_from_db()
        self.assertEqual(self.operator.password, before)
        self.assertFalse(self.operator.groups.filter(name="Gestores").exists())

    def test_acquisition_asset_edit_history_and_pending_routes(self):
        headers = self.session(self.gestor)
        self.assertEqual(self.client.get("/api/auth/me/").json()["permissions"], ["inventory.manage"])
        response = self.client.post("/api/acquisitions/", purchase(), format="json", **headers)
        self.assertEqual(response.status_code, 201, response.content)
        doc_id = response.json()["id"]
        faculty = Faculty.objects.create(name="Facultad ficticia")
        payload = asset_data(faculty_id=faculty.pk, acquisition_document_id=doc_id,
                             item_value="300.00", acquired_on="2026-01-15")
        response = self.client.post("/api/assets/", payload, format="json", **headers)
        self.assertEqual(response.status_code, 201, response.content)
        asset_id = response.json()["id"]
        self.assertEqual(response.json()["faculty_id"], faculty.pk)
        self.assertEqual(response.json()["acquisition"]["currency"], "USD")
        response = self.client.patch(f"/api/assets/{asset_id}/", {"expected_revision": 0, "reason": "Verificado", "name": "Corregido"},
                                     format="json", **headers)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["revision"], 1)
        history = self.client.get(f"/api/assets/{asset_id}/history/")
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.json()[0]["event_type"], "asset_change")
        self.assertEqual(history.json()[0]["resulting_revision"], 1)
        response = self.client.patch(f"/api/acquisitions/{doc_id}/", {"reason": "Cambio", "reference": "OTRA"}, format="json", **headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(AcquisitionDocument.objects.get(pk=doc_id).reference, "TEST-FACT-1")
        for data in [asset_data(), {**payload, "currency": "EUR"}, {**payload, "acquired_on": None, "date_unknown_reason": ""}]:
            self.assertEqual(self.client.post("/api/assets/", data, format="json", **headers).status_code, 400)
        self.assertEqual((Asset.objects.count(), AcquisitionLine.objects.count()), (1, 1))
        self.assertEqual(self.client.get("/api/acquisitions/999999/").status_code, 404)

    def test_new_mutations_enforce_csrf_and_never_write_on_rejection(self):
        asset, faculty, doc = self.acquisition_asset(self.gestor)
        self.session(self.gestor)
        for method, route, data in [
            ("post", "/api/acquisitions/", purchase()),
            ("patch", f"/api/assets/{asset.pk}/", {"expected_revision": 0, "reason": "Intento", "name": "Otro"}),
        ]:
            self.assertEqual(getattr(self.client, method)(route, data, format="json").status_code, 403)
        self.assertEqual((AcquisitionDocument.objects.count(), AssetChange.objects.count()), (1, 0))
        self.session(self.operator)
        self.assertEqual(self.client.patch(f"/api/operator/faculties/{faculty.pk}/", {"name": "Otro"}, format="json").status_code, 403)
        faculty.refresh_from_db()
        self.assertEqual(faculty.name, "Facultad ficticia de pruebas")

    def test_catalog_patch_duplicate_keeps_original_name_and_inactive_state(self):
        first = Faculty.objects.create(name="Facultad A", active=False)
        second = Faculty.objects.create(name="Facultad B")
        headers = self.session(self.operator)
        response = self.client.patch(f"/api/operator/faculties/{first.pk}/", {"name": " facultad b "}, format="json", **headers)
        self.assertEqual(response.status_code, 409, response.content)
        first.refresh_from_db()
        self.assertEqual((first.name, first.active), ("Facultad A", False))
        response = self.client.patch(f"/api/operator/faculties/{first.pk}/", {"name": "Facultad A corregida"}, format="json", **headers)
        self.assertEqual(response.status_code, 200)
        first.refresh_from_db()
        self.assertFalse(first.active)
        self.assertEqual(Faculty.objects.get(pk=second.pk).name, "Facultad B")

    def test_inactive_login_and_manager_login_have_explicit_separate_permissions(self):
        self.operator.is_active = False
        self.operator.save()
        token = self.client.get("/api/auth/csrf/").json()["csrfToken"]
        response = self.client.post("/api/auth/login/", {"username": "operator", "password": "Fixture-only-42!"},
                                    format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 403)
        self.gestor.set_password("Fixture-only-42!")
        self.gestor.save()
        token = self.client.get("/api/auth/csrf/").json()["csrfToken"]
        response = self.client.post("/api/auth/login/", {"username": self.gestor.username, "password": "Fixture-only-42!"},
                                    format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["permissions"], ["inventory.manage"])
        self.assertEqual(self.client.post("/api/operator/faculties/", {"name": "No autorizada"}, format="json",
            HTTP_X_CSRFTOKEN=self.client.get("/api/auth/csrf/").json()["csrfToken"]).status_code, 403)
        self.assertEqual(Faculty.objects.count(), 0)

    def test_pending_operations_have_no_writes_and_no_fake_success(self):
        asset, _faculty, doc = self.acquisition_asset(self.gestor)
        person_response = None
        headers = self.session(self.gestor)
        person_response = self.client.post("/api/custodians/", {"full_name": "Persona ficticia", "email": "person@example.org"},
                                           format="json", **headers)
        self.assertEqual(person_response.status_code, 201)
        person_id = person_response.json()["id"]
        response = self.client.patch(f"/api/custodians/{person_id}/", {"full_name": "Otro"}, format="json", **headers)
        self.assertEqual(response.status_code, 400)
        from inventory.models import Custodian, CustodianChange
        self.assertEqual(Custodian.objects.get(pk=person_id).full_name, "Persona ficticia")
        self.assertEqual(CustodianChange.objects.count(), 0)
        response = self.client.post("/api/acquisitions/", {**purchase(), "items": [{"asset_id": asset.pk, "item_value": "20.00"}]},
                                    format="json", **headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(AcquisitionDocument.objects.count(), 1)
        for data in [purchase(invoice_total="0.00"), {"source": "DONATION", "reference": "TEST",
            "support_type": "Acta", "document_date": "2026-01-15"}]:
            response = self.client.post("/api/acquisitions/", data, format="json", **headers)
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.json()["code"], "pending_decision")
        self.assertEqual(AcquisitionDocument.objects.count(), 1)

    def test_history_combines_movement_and_audit_and_stale_edit_has_no_writes(self):
        asset, _faculty, _doc = self.acquisition_asset(self.gestor)
        headers = self.session(self.gestor)
        response = self.client.post(f"/api/assets/{asset.pk}/condition/", {"expected_revision": 0,
            "condition": "averiado", "reason": "Falla observada"}, format="json", **headers)
        self.assertEqual(response.status_code, 201)
        response = self.client.patch(f"/api/assets/{asset.pk}/", {"expected_revision": 1,
            "reason": "Nombre verificado", "name": "Corregido"}, format="json", **headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["rectifiable_movement_id"])
        response = self.client.patch(f"/api/assets/{asset.pk}/", {"expected_revision": 1,
            "reason": "Obsoleto", "name": "No debe escribirse"}, format="json", **headers)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "stale_revision")
        history = self.client.get(f"/api/assets/{asset.pk}/history/").json()
        self.assertEqual([event["event_type"] for event in history], ["asset_change", "movement"])
        self.assertEqual([event["resulting_revision"] for event in history], [2, 1])
        self.assertEqual(len(self.client.get(f"/api/assets/{asset.pk}/movements/").json()), 1)
        self.assertEqual(AssetChange.objects.count(), 1)

    def test_provision_rejects_weak_password_and_does_not_create_user(self):
        with patch("builtins.input", return_value="weak_fixture"), patch(
            "inventory.management.commands.create_operator.getpass", return_value="123"):
            with self.assertRaises(CommandError):
                call_command("create_operator", stdout=StringIO())
        self.assertFalse(get_user_model().objects.filter(username="weak_fixture").exists())
