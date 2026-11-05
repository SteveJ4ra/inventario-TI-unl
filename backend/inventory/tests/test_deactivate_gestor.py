from io import StringIO
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from inventory.models import Asset, Category, Condition, Movement
from inventory.services import record_operation


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class DeactivateGestorTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("gestor_baja", password="Fixture-only-42!")
        self.user.groups.add(Group.objects.create(name="Gestores"))
        self.asset = Asset.objects.create(code="TI-990001", name="Prueba", description="Equipo", category=Category.MONITOR, brand="Prueba", model="M", serial_number="1", location="A", condition=Condition.OPERATIONAL, created_by=self.user)

    def test_deactivate_preserves_author_and_denies_existing_session(self):
        _, movement = record_operation(asset_id=self.asset.id, actor=self.user, operation=Movement.Type.CONDITION, data={"expected_revision": 0, "condition": Condition.BROKEN, "reason": "Revisión"})
        client = APIClient()
        client.force_login(self.user)
        call_command("deactivate_gestor", self.user.username, stdout=StringIO())
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertEqual(Asset.objects.get(pk=self.asset.pk).created_by_id, self.user.pk)
        self.assertEqual(Movement.objects.get(pk=movement.pk).actor_id, self.user.pk)
        self.assertEqual(client.get("/api/auth/me/").status_code, 403)
        self.assertFalse(client.login(username=self.user.username, password="Fixture-only-42!"))

    def test_reject_unknown_non_manager_and_already_inactive(self):
        other = get_user_model().objects.create_user("otro", password="Fixture-only-42!")
        for username in ("no_existe", other.username):
            with self.subTest(username=username), self.assertRaises(CommandError):
                call_command("deactivate_gestor", username, stdout=StringIO())
        other.refresh_from_db()
        self.assertTrue(other.is_active)
        call_command("deactivate_gestor", self.user.username, stdout=StringIO())
        with self.assertRaises(CommandError):
            call_command("deactivate_gestor", self.user.username, stdout=StringIO())
