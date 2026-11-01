from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from rest_framework.test import APIClient


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
