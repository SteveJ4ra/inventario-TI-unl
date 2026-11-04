r"""Pruebas focalizadas del paquete 007: QR y resolución exacta por código TI.

Ejecución recomendada desde la raíz del repositorio (PowerShell):
& .\backend\.venv\Scripts\python.exe backend/tools/test_postgres.py inventory.test_qr_assets --verbosity 2
"""

from unittest.mock import patch

import segno
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from inventory.models import Asset, Assignment, Category, Condition, Movement
from inventory.qr_urls import build_asset_qr_url


@override_settings(PUBLIC_APP_URL="https://inventario.example.test", DEBUG=False)
class QrActivosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.manager = users.objects.create_user(
            username="gestor_qr_prueba", password="Clave-Prueba-Segura-12345"
        )
        managers, _ = Group.objects.get_or_create(name="Gestores")
        cls.manager.groups.add(managers)
        cls.other_user = users.objects.create_user(
            username="usuario_sin_permiso_qr", password="Otra-Clave-Prueba-12345"
        )
        cls.asset = Asset.objects.create(
            code="TI-123456",
            name="Equipo de prueba QR",
            description="Activo de prueba sin datos privados",
            category=Category.DESKTOP,
            brand="Marca QR",
            model="Modelo QR",
            serial_number="QR-TEST-UNICO-123456",
            location="Laboratorio de pruebas",
            condition=Condition.OPERATIONAL,
            assignment=Assignment.AVAILABLE,
            created_by=cls.manager,
        )

    def test_sin_sesion_no_puede_descargar_ni_consultar(self):
        self.assertEqual(
            self.client.get(f"/api/assets/{self.asset.pk}/qr.svg").status_code,
            403,
        )
        self.assertEqual(
            self.client.get(f"/api/assets/by-code/{self.asset.code}/").status_code,
            403,
        )

    def test_usuario_sin_rol_gestor_no_puede_descargar_ni_consultar(self):
        self.client.force_login(self.other_user)
        self.assertEqual(
            self.client.get(f"/api/assets/{self.asset.pk}/qr.svg").status_code,
            403,
        )
        self.assertEqual(
            self.client.get(f"/api/assets/by-code/{self.asset.code}/").status_code,
            403,
        )

    def test_gestor_descarga_svg_bajo_demanda(self):
        self.client.force_login(self.manager)
        before_count = Asset.objects.count()
        before_movements = Movement.objects.count()
        response = self.client.get(f"/api/assets/{self.asset.pk}/qr.svg")
        self.assertEqual(response.status_code, 200)
        self.assertIn("image/svg+xml", response["Content-Type"])
        self.assertIn(b"<svg", response.content)
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(Asset.objects.count(), before_count)
        self.assertEqual(Movement.objects.count(), before_movements)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.revision, 0)

    def test_qr_contiene_url_canonica_sin_datos_privados(self):
        self.client.force_login(self.manager)
        # Espiamos Segno sin sustituir su generador real.
        with patch("inventory.views.segno.make_qr", wraps=segno.make_qr) as generator:
            response = self.client.get(
                f"/api/assets/{self.asset.pk}/qr.svg"
            )
        self.assertEqual(response.status_code, 200)
        generator.assert_called_once()
        encoded_url = generator.call_args.args[0]
        self.assertEqual(
            encoded_url,
            "https://inventario.example.test/assets/code/TI-123456",
        )
        self.assertNotIn("evil.example.test", encoded_url)
        self.assertNotIn(self.asset.serial_number, encoded_url)
        self.assertNotIn(self.manager.username, encoded_url)

    @override_settings(ALLOWED_HOSTS=["testserver", "evil.example.test"])
    def test_host_alternativo_no_define_destino_qr(self):
        self.client.force_login(self.manager)
        with patch("inventory.views.segno.make_qr", wraps=segno.make_qr) as generator:
            response = self.client.get(
                f"/api/assets/{self.asset.pk}/qr.svg", HTTP_HOST="evil.example.test"
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            generator.call_args.args[0],
            "https://inventario.example.test/assets/code/TI-123456",
        )

    def test_resolucion_exacta_por_codigo(self):
        self.client.force_login(self.manager)
        response = self.client.get(f"/api/assets/by-code/{self.asset.code}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.asset.pk)
        self.assertEqual(response.json()["code"], self.asset.code)

    def test_codigo_inexistente_o_parcial_no_coincide(self):
        self.client.force_login(self.manager)
        for code in ("TI-999999", "TI-123", "TI-1234567"):
            with self.subTest(code=code):
                response = self.client.get(f"/api/assets/by-code/{code}/")
                self.assertEqual(response.status_code, 404)

    def test_id_inexistente_no_produce_qr(self):
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get("/api/assets/987654321/qr.svg").status_code, 404)

    def test_una_url_publica_insegura_se_rechaza(self):
        with override_settings(PUBLIC_APP_URL="javascript:alert(1)"):
            with self.assertRaises(ImproperlyConfigured):
                build_asset_qr_url(self.asset.code)
        with override_settings(PUBLIC_APP_URL="http://inventario.example.test"):
            with self.assertRaises(ImproperlyConfigured):
                build_asset_qr_url(self.asset.code)

    def test_url_canonica_no_usa_id_numerico(self):
        self.assertEqual(
            build_asset_qr_url(self.asset.code),
            "https://inventario.example.test/assets/code/TI-123456",
        )
