from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from inventory.imports import schemas, services
from inventory.models import Asset, ImportBatch
from .base import manager
from .fake_import_gateway import FakeGateway

GATEWAY = "inventory.tests.fake_import_gateway.FakeGateway"


def csv_file(kind, rows, name="import.csv"):
    header = ",".join(schemas.columns(kind))
    body = "\n".join([header, *[",".join(row) for row in rows]]) + "\n"
    return SimpleUploadedFile(
        name, body.encode("utf-8"), content_type="text/csv"
    )


def asset_row(**changes):
    row = {
        "name": "Portátil",
        "description": "Equipo de práctica",
        "category": "portatil",
        "brand": "Marca",
        "model": "Modelo A",
        "serial_number": "SER-1",
        "location": "Laboratorio",
        "condition": "operativo",
        "faculty_id": "1",
        "acquisition_document_id": "",
        "document_key": "FACT-1",
        "document_source": "compra",
        "document_reference": "FAC-1",
        "document_date": "2026-01-15",
        "supplier": "Proveedor",
        "invoice_total": "1000.00",
        "support_description": "",
        "item_value": "500.00",
        "acquired_on": "2026-01-20",
        "date_unknown_reason": "",
    }
    row.update(changes)
    return [row[name] for name in schemas.ASSET_COLUMNS]


def license_row(**changes):
    row = {
        "product_name": "Suite",
        "vendor": "Proveedor",
        "license_model": "USER_SEAT",
        "purchased_quantity": "10",
        "in_use_quantity": "2",
        "starts_on": "2026-01-01",
        "ends_on": "",
    }
    row.update(changes)
    return [row[name] for name in schemas.LICENSE_LOT_COLUMNS]


@override_settings(IMPORT_GATEWAY=GATEWAY)
class ImportApiTests(APITestCase):
    def setUp(self):
        FakeGateway.reset()
        FakeGateway.faculty_ids = {1}
        FakeGateway.document_ids = {10}
        self.actor = manager("gestor")
        self.client.force_authenticate(self.actor)

    def preview(self, kind, rows, **extra):
        data = {
            "kind": kind,
            "schema_version": schemas.default_version(kind),
            "file": csv_file(kind, rows),
            **extra,
        }
        return self.client.post("/api/imports/previews/", data, format="multipart")

    def valid_preview(self, kind=schemas.ASSETS, rows=None):
        response = self.preview(kind, rows or [asset_row()])
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()

    def confirm(self, batch, digest=None):
        return self.client.post(
            f"/api/imports/{batch['batch_id']}/confirm/",
            {"content_hash": digest or batch["content_hash"]},
            format="json",
        )

    def apply(self, batch, digest=None):
        return self.client.post(
            f"/api/imports/{batch['batch_id']}/apply/",
            {"content_hash": digest or batch["content_hash"]},
            format="json",
        )

    def test_plantilla_descargable(self):
        response = self.client.get("/api/imports/templates/assets/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"\xef\xbb\xbf"))
        self.assertIn(b"document_key", response.content)
        self.assertIn("assets-v1.csv", response["Content-Disposition"])
        self.assertEqual(
            self.client.get("/api/imports/templates/otro/").status_code, 404
        )

    def test_preview_valido_no_escribe_dominio(self):
        batch = self.valid_preview()
        self.assertEqual(batch["state"], "PREVIEW_READY")
        self.assertEqual(batch["summary"]["record_count"], 1)
        self.assertEqual(len(batch["content_hash"]), 64)
        self.assertEqual(batch["rows"][0]["values"]["item_value"], "500.00")
        self.assertEqual(Asset.objects.count(), 0)
        self.assertEqual(ImportBatch.objects.count(), 1)
        stored = ImportBatch.objects.get()
        self.assertEqual(stored.owner, self.actor)
        self.assertEqual(len(stored.rows), 1)

    def test_preview_invalido_lista_errores_y_no_habilita_confirmacion(self):
        response = self.preview(
            schemas.ASSETS,
            [
                asset_row(serial_number=""),
                asset_row(serial_number="SER-2", category="otra"),
            ],
        )
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["state"], "INVALID")
        fields = {(error["row"], error["field"]) for error in body["errors"]}
        self.assertIn((2, "serial_number"), fields)
        self.assertIn((3, "category"), fields)
        self.assertEqual(Asset.objects.count(), 0)
        confirm = self.confirm(body)
        self.assertEqual(confirm.status_code, 409)
        self.assertEqual(confirm.json()["code"], "invalid_batch")

    def test_ciclo_doble_confirmacion_y_reintento_idempotente(self):
        batch = self.valid_preview()
        first = self.confirm(batch)
        self.assertEqual(first.status_code, 200, first.content)
        self.assertEqual(first.json()["state"], "CONFIRMED_ONCE")
        again = self.confirm(batch)
        self.assertEqual(again.status_code, 200)
        self.assertEqual(FakeGateway.apply_calls, [])
        applied = self.apply(batch)
        self.assertEqual(applied.status_code, 201, applied.content)
        body = applied.json()
        self.assertEqual(body["state"], "APPLIED")
        self.assertEqual(body["applied_result"]["created"], 1)
        retry = self.apply(batch)
        self.assertEqual(retry.status_code, 200, retry.content)
        self.assertEqual(retry.json()["applied_result"], body["applied_result"])
        self.assertEqual(len(FakeGateway.apply_calls), 1)
        stored = ImportBatch.objects.get()
        self.assertEqual(stored.state, "APPLIED")
        self.assertIsNone(stored.rows)
        self.assertEqual(stored.applied_result["created"], 1)

    def test_apply_requiere_confirmacion_y_hash_vigente(self):
        batch = self.valid_preview()
        early = self.apply(batch)
        self.assertEqual(early.status_code, 409)
        self.assertEqual(early.json()["code"], "confirmation_required")
        self.confirm(batch)
        stale = self.apply(batch, "0" * 64)
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(stale.json()["code"], "stale_preview")
        self.assertEqual(FakeGateway.apply_calls, [])

    def test_otro_gestor_no_consulta_ni_confirma(self):
        batch = self.valid_preview()
        other = manager("otro")
        self.client.force_authenticate(other)
        self.assertEqual(
            self.client.get(f"/api/imports/{batch['batch_id']}/").status_code, 403
        )
        self.assertEqual(self.confirm(batch).status_code, 403)
        self.assertEqual(self.apply(batch).status_code, 403)

    def test_cancelacion_impide_confirmar_y_aplicar(self):
        batch = self.valid_preview()
        response = self.client.post(
            f"/api/imports/{batch['batch_id']}/cancel/", {}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["state"], "CANCELLED")
        self.assertEqual(self.confirm(batch).status_code, 409)
        self.assertEqual(self.apply(batch).status_code, 409)
        stored = ImportBatch.objects.get()
        self.assertIsNone(stored.rows)

    def test_expiracion_elimina_contenido_temporal(self):
        batch = self.valid_preview()
        stored = ImportBatch.objects.get()
        stored.expires_at = timezone.now() - timedelta(seconds=1)
        stored.save(update_fields=["expires_at"])
        response = self.confirm(batch)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "expired_batch")
        stored.refresh_from_db()
        self.assertEqual(stored.state, "EXPIRED")
        self.assertIsNone(stored.rows)
        self.assertFalse(stored.errors)

    def test_licencias_validas_e_invalidas(self):
        batch = self.valid_preview(schemas.LICENSE_LOTS, [license_row()])
        self.assertEqual(batch["summary"]["purchased_total"], 10)
        response = self.preview(
            schemas.LICENSE_LOTS,
            [license_row(in_use_quantity="11")],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("no puede superar", str(response.json()["errors"]))

    def test_documentos_compartidos_y_referencias(self):
        mismatch = self.preview(
            schemas.ASSETS,
            [
                asset_row(),
                asset_row(serial_number="SER-2", supplier="Otro"),
            ],
        )
        self.assertEqual(mismatch.status_code, 400)
        self.assertIn("no coinciden", str(mismatch.json()["errors"]))

        existing = self.preview(
            schemas.ASSETS,
            [
                asset_row(
                    acquisition_document_id="10",
                    document_key="",
                    document_source="",
                    document_reference="",
                    document_date="",
                    supplier="",
                    invoice_total="",
                    support_description="",
                )
            ],
        )
        self.assertEqual(existing.status_code, 201, existing.content)

        missing = self.preview(
            schemas.ASSETS,
            [
                asset_row(
                    acquisition_document_id="99",
                    document_key="",
                    document_source="",
                    document_reference="",
                    document_date="",
                    supplier="",
                    invoice_total="",
                    support_description="",
                )
            ],
        )
        self.assertEqual(missing.status_code, 400)
        self.assertIn("no existe", str(missing.json()["errors"]))

        FakeGateway.existing_identities = {("marca", "modelo a", "ser-1")}
        duplicate_db = self.preview(schemas.ASSETS, [asset_row()])
        self.assertEqual(duplicate_db.status_code, 400)
        self.assertIn("Ya existe", str(duplicate_db.json()["errors"]))

    def test_revalidacion_al_aplicar_rechaza_todo(self):
        batch = self.valid_preview()
        self.confirm(batch)
        FakeGateway.faculty_ids = set()
        response = self.apply(batch)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "import_conflict")
        self.assertEqual(response.json()["errors"][0]["field"], "faculty_id")
        self.assertEqual(FakeGateway.apply_calls, [])
        stored = ImportBatch.objects.get()
        self.assertEqual(stored.state, "CONFIRMED_ONCE")
        self.assertIsNotNone(stored.rows)

    def test_fallo_del_proveedor_revierte_y_permite_reintentar(self):
        batch = self.valid_preview()
        self.confirm(batch)
        FakeGateway.fail_integrity = True
        response = self.apply(batch)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "import_conflict")
        stored = ImportBatch.objects.get()
        self.assertEqual(stored.state, "CONFIRMED_ONCE")
        self.assertIsNotNone(stored.rows)
        FakeGateway.fail_integrity = False
        retry = self.apply(batch)
        self.assertEqual(retry.status_code, 201, retry.content)
        self.assertEqual(len(FakeGateway.apply_calls), 1)

    @override_settings(IMPORT_MAX_ROWS=1)
    def test_limite_de_filas(self):
        response = self.preview(
            schemas.ASSETS, [asset_row(), asset_row(serial_number="SER-2")]
        )
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()["code"], "limit_exceeded")
        self.assertEqual(ImportBatch.objects.count(), 0)

    @override_settings(IMPORT_MAX_BYTES=20)
    def test_limite_de_bytes(self):
        response = self.preview(schemas.ASSETS, [asset_row()])
        self.assertEqual(response.status_code, 413)
        self.assertEqual(ImportBatch.objects.count(), 0)

    def test_get_pagina_todas_las_filas(self):
        rows = [
            license_row(product_name=f"Producto {number}")
            for number in range(55)
        ]
        batch = self.valid_preview(schemas.LICENSE_LOTS, rows)
        first = self.client.get(f"/api/imports/{batch['batch_id']}/?page=1")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(len(first.json()["rows"]), 50)
        self.assertIsNotNone(first.json()["next"])
        second = self.client.get(f"/api/imports/{batch['batch_id']}/?page=2")
        self.assertEqual(len(second.json()["rows"]), 5)
        self.assertIsNotNone(second.json()["previous"])
        self.assertEqual(
            self.client.get(f"/api/imports/{batch['batch_id']}/?page=3").status_code,
            400,
        )


@override_settings(IMPORT_GATEWAY=GATEWAY)
class ImportCsrfTests(TestCase):
    def setUp(self):
        FakeGateway.reset()
        FakeGateway.faculty_ids = {1}
        self.actor = manager("gestor")
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_login(self.actor)

    def test_carga_multipart_exige_csrf(self):
        data = {
            "kind": schemas.ASSETS,
            "schema_version": "assets-v1",
            "file": csv_file(schemas.ASSETS, [asset_row()]),
        }
        denied = self.client.post("/api/imports/previews/", data, format="multipart")
        self.assertEqual(denied.status_code, 403)
        token = self.client.get("/api/auth/csrf/").json()["csrfToken"]
        data = {
            "kind": schemas.ASSETS,
            "schema_version": "assets-v1",
            "file": csv_file(schemas.ASSETS, [asset_row()]),
        }
        allowed = self.client.post(
            "/api/imports/previews/",
            data,
            format="multipart",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(allowed.status_code, 201, allowed.content)


@override_settings(IMPORT_GATEWAY=GATEWAY)
class ImportConcurrencyTests(TransactionTestCase):
    def setUp(self):
        FakeGateway.reset()
        FakeGateway.faculty_ids = {1}
        self.actor = manager("gestor")
        self.batch = services.preview(
            actor=self.actor,
            kind=schemas.ASSETS,
            schema_version="assets-v1",
            raw=csv_file(schemas.ASSETS, [asset_row()]).read(),
        )
        services.confirm(
            actor=self.actor,
            batch_id=self.batch.pk,
            content_hash=self.batch.content_hash,
        )

    def test_dos_aplicaciones_simultaneas_crean_una_vez(self):
        barrier = Barrier(2)

        def worker():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                batch, changed = services.apply(
                    actor=self.actor,
                    batch_id=self.batch.pk,
                    content_hash=self.batch.content_hash,
                )
                return changed
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: worker(), range(2)))
        self.assertEqual(results.count(True), 1)
        self.assertEqual(results.count(False), 1)
        self.assertEqual(len(FakeGateway.apply_calls), 1)
        stored = ImportBatch.objects.get(pk=self.batch.pk)
        self.assertEqual(stored.state, "APPLIED")
