"""Pruebas del perfil de despliegue sin arrancar servicios ni usar secretos reales."""
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from django.test import SimpleTestCase


class DeploymentProfileTests(SimpleTestCase):
    def profile(self, **changes):
        with TemporaryDirectory() as directory:
            key = Path(directory) / "key"
            password = Path(directory) / "password"
            key.write_text("s" * 64, encoding="utf-8")
            password.write_text("solo-fixture-de-prueba", encoding="utf-8")
            env = os.environ.copy()
            env.update(DJANGO_SECRET_KEY_FILE=str(key), DB_PASSWORD_FILE=str(password),
                DJANGO_DEBUG="false", DJANGO_HTTPS="false", DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1")
            env.update(changes)
            code = (
                "import json; from config import settings_deploy as s; "
                "print(json.dumps(dict(debug=s.DEBUG, hosts=s.ALLOWED_HOSTS, secure=s.SESSION_COOKIE_SECURE, "
                "csrf_secure=s.CSRF_COOKIE_SECURE, redirect=s.SECURE_SSL_REDIRECT, "
                "session_age=s.SESSION_COOKIE_AGE, secrets_read=(s.SECRET_KEY=='s'*64 and s.DATABASES['default']['PASSWORD']=='solo-fixture-de-prueba'))))"
            )
            return subprocess.run([sys.executable, "-c", code], cwd=Path(__file__).resolve().parents[2],
                env=env, capture_output=True, text=True, timeout=15)

    def test_local_profile_reads_files_without_enabling_public_https(self):
        result = self.profile()
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertFalse(data["debug"])
        self.assertFalse(data["secure"])
        self.assertFalse(data["redirect"])
        self.assertEqual(data["hosts"], ["localhost", "127.0.0.1"])
        self.assertEqual(data["session_age"], 1800)
        self.assertTrue(data["secrets_read"])

    def test_https_profile_requires_secure_cookies_and_redirect(self):
        result = self.profile(DJANGO_HTTPS="true")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertTrue(data["secure"] and data["csrf_secure"] and data["redirect"])

    def test_debug_and_wildcard_hosts_are_rejected(self):
        for values in [{"DJANGO_DEBUG":"true"}, {"DJANGO_ALLOWED_HOSTS":"*"}, {"DJANGO_ALLOWED_HOSTS":""}]:
            with self.subTest(values=values):
                result = self.profile(**values)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("ImproperlyConfigured", result.stderr)

    def test_missing_secret_file_fails_closed(self):
        result = self.profile(DB_PASSWORD_FILE="/archivo-inexistente-de-prueba")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No se pudo leer DB_PASSWORD_FILE", result.stderr)


class QrLocalDeploymentTests(SimpleTestCase):
    def test_http_loopback_requires_explicit_permission(self):
        from django.test import override_settings
        from django.core.exceptions import ImproperlyConfigured
        from inventory.qr_urls import build_asset_qr_url
        for host in ["localhost:5173", "127.0.0.1:5173", "[::1]:5173"]:
            with self.subTest(host=host), override_settings(DEBUG=False, PUBLIC_APP_URL="http://"+host, QR_ALLOW_LOCAL_HTTP=False):
                with self.assertRaises(ImproperlyConfigured):
                    build_asset_qr_url("TI-000001")
            with self.subTest(host=host), override_settings(DEBUG=False, PUBLIC_APP_URL="http://"+host, QR_ALLOW_LOCAL_HTTP=True):
                self.assertEqual(build_asset_qr_url("TI-000001"), "http://"+host+"/assets/code/TI-000001")

    def test_http_external_is_rejected_even_with_local_permission(self):
        from django.test import override_settings
        from django.core.exceptions import ImproperlyConfigured
        from inventory.qr_urls import build_asset_qr_url
        with override_settings(DEBUG=False, PUBLIC_APP_URL="http://inventario.example.test", QR_ALLOW_LOCAL_HTTP=True):
            with self.assertRaises(ImproperlyConfigured):
                build_asset_qr_url("TI-000001")
