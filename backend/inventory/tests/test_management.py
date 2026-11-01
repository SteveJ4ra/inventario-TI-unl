from io import StringIO
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class ManagerCommandTests(TestCase):
    def test_interactive_command_creates_only_inventory_manager(self):
        with patch("builtins.input", return_value="nuevo"), patch(
            "inventory.management.commands.create_gestor.getpass",
            return_value="OnlyCLI-Test-!2026",
        ):
            call_command("create_gestor", stdout=StringIO())
        user = get_user_model().objects.get(username="nuevo")
        self.assertTrue(user.check_password("OnlyCLI-Test-!2026"))
        self.assertTrue(user.groups.filter(name="Gestores").exists())
        self.assertFalse(user.is_staff or user.is_superuser)

    def test_mismatch_leaves_no_account(self):
        with patch("builtins.input", return_value="nuevo"), patch(
            "inventory.management.commands.create_gestor.getpass",
            side_effect=["One-Password-2026!", "Other-Password-2026!"],
        ):
            with self.assertRaises(CommandError):
                call_command("create_gestor", stdout=StringIO())
        self.assertFalse(get_user_model().objects.exists())
