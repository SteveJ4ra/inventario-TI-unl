import csv
import io
from datetime import timedelta
from unittest.mock import Mock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from inventory.imports.exceptions import ImportDomainConflict
from inventory.imports.schemas import ASSET_FIELDS, LICENSE_LOT_FIELDS, template_bytes
from inventory.models import Asset, Custodian, ImportBatch, ImportBatchRow

from .base import InventoryCase, manager


def csv_bytes(fields, rows):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return output.getvalue().encode("utf-8")


def asset_row(**changes):
    row = {
        "name": "Portátil",
        "description": "Equipo de práctica",
        "category": "portatil",
        "brand": "Marca",
        "model": "M1",
        "serial_number": "S-001",
        "location": "Laboratorio",
        "condition": "operativo",
        "faculty_id": "1",
        "acquisition_document_id": "",
        "document_key": "doc-1",
        "acquisition_source": "purchase",
        "document_reference": "FAC-001",
        "document_date": "2026-01-01",
        "supplier": "Proveedor",
        "invoice_total": "100.00",
        "donation_support_type": "",
        "acquired_on": "2026-01-02",
        "date_unknown_reason": "",
        "item_value": "50.00",
    }
    row.update(changes)
    return row


def license_row(**changes):
    row = {
        "product_name": "Producto",
        "vendor": "Proveedor",
        "license_model": "USER_SEAT",
        "purchased_quantity": "10",
        "in_use_quantity": "4",
        "starts_on": "2026-01-01",
        "ends_on": "2026-12-31",
    }
    row.update(changes)
    return row


class ImportApiTests(InventoryCase):
    def upload(self, kind="assets", rows=None, fields=None, filename="import.csv"):
        if fields is None:
            fields = ASSET_FIELDS if kind == "assets" else LICENSE_LOT_FIELDS
        if rows is None:
            rows = [asset_row()] if kind == "assets" else [license_row()]
        content = csv_bytes(fields, rows)
        return self.client.post(
            "/api/imports/previews",
            {
                "kind": kind,
                "schema_version": "v1",
                "file": SimpleUploadedFile(filename, content, content_type="text/csv"),
            },
            format="multipart",
        )

    def test_valid_asset_preview_returns_complete_batch_without_writing(self):
        response = self.upload(
            rows=[asset_row(), asset_row(serial_number="S-002")]
        )
        self.assertEqual(response.status_code, 201, response.content)
        data = response.json()
        self.assertEqual(data["state"], ImportBatch.State.PREVIEW_READY)
        self.assertEqual(data["summary"]["valid_rows"], 2)
        self.assertEqual(data["rows_count"], 2)
        self.assertTrue(data["batch_id"])
        self.assertEqual(ImportBatch.objects.count(), 1)
        self.assertEqual(ImportBatchRow.objects.count(), 2)
        self.assertEqual(Asset.objects.count(), 0)

        detail = self.client.get(f"/api/imports/{data['batch_id']}")
        self.assertEqual(detail.status_code, 200, detail.content)
        self.assertEqual(detail.json()["rows"]["count"], 2)

    def test_invalid_preview_returns_400_with_all_errors_and_batch_id(self):
        response = self.upload(
            rows=[asset_row(acquisition_document_id="7")]
        )
        self.assertEqual(response.status_code, 400, response.content)
        data = response.json()
        self.assertEqual(data["state"], ImportBatch.State.INVALID)
        self.assertTrue(data["batch_id"])
        self.assertTrue(data["errors"])
        self.assertEqual(ImportBatchRow.objects.count(), 1)

    def test_bad_header_and_empty_file_are_invalid(self):
        response = self.client.post(
            "/api/imports/previews",
            {
                "kind": "assets",
                "schema_version": "v1",
                "file": SimpleUploadedFile(
                    "bad.csv", b"name,description\nPC,Equipo\n", content_type="text/csv"
                ),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(response.json()["errors"][0]["field"], "header")
        response = self.client.post(
            "/api/imports/previews",
            {
                "kind": "assets",
                "file": SimpleUploadedFile(
                    "empty.csv", b"", content_type="text/csv"
                ),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["errors"][0]["field"], "file")

    def test_upload_limits_return_413(self):
        with override_settings(IMPORT_MAX_BYTES=10):
            response = self.upload()
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()["code"], "import_limit_exceeded")
        with override_settings(IMPORT_MAX_ROWS=1):
            response = self.upload(
                rows=[asset_row(), asset_row(serial_number="S-002")]
            )
        self.assertEqual(response.status_code, 413)

    def test_confirm_apply_and_idempotent_retry(self):
        response = self.upload()
        batch = response.json()
        fake = Mock()
        fake.apply.return_value = {"created": 1, "kind": "assets"}
        with patch("inventory.imports.service._adapter", return_value=fake):
            confirmed = self.client.post(
                f"/api/imports/{batch['batch_id']}/confirm",
                {"content_hash": batch["content_hash"]},
                format="json",
            )
            self.assertEqual(confirmed.status_code, 200, confirmed.content)
            self.assertEqual(
                confirmed.json()["state"], ImportBatch.State.CONFIRMED_ONCE
            )
            applied = self.client.post(
                f"/api/imports/{batch['batch_id']}/apply",
                {"content_hash": batch["content_hash"]},
                format="json",
            )
            self.assertEqual(applied.status_code, 201, applied.content)
            data = applied.json()
            self.assertTrue(data["created"])
            self.assertEqual(data["state"], ImportBatch.State.APPLIED)
            self.assertEqual(data["applied_result"], {"created": 1, "kind": "assets"})
            self.assertEqual(data["rows_count"], 0)
            self.assertEqual(ImportBatchRow.objects.count(), 0)
            self.assertEqual(fake.apply.call_count, 1)

            retry = self.client.post(
                f"/api/imports/{batch['batch_id']}/apply",
                {"content_hash": batch["content_hash"]},
                format="json",
            )
            self.assertEqual(retry.status_code, 200, retry.content)
            self.assertFalse(retry.json()["created"])
            self.assertEqual(fake.apply.call_count, 1)

    def test_hash_and_state_conflicts(self):
        batch = self.upload().json()
        wrong = "0" * 64
        response = self.client.post(
            f"/api/imports/{batch['batch_id']}/confirm",
            {"content_hash": wrong},
            format="json",
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "preview_changed")
        response = self.client.post(
            f"/api/imports/{batch['batch_id']}/apply",
            {"content_hash": batch["content_hash"]},
            format="json",
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "invalid_import_state")

    def test_invalid_preview_cannot_be_confirmed(self):
        batch = self.upload(rows=[asset_row(acquisition_document_id="7")]).json()
        response = self.client.post(
            f"/api/imports/{batch['batch_id']}/confirm",
            {"content_hash": batch["content_hash"]},
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_production_adapter_reports_missing_dependency(self):
        batch = self.upload().json()
        self.client.post(
            f"/api/imports/{batch['batch_id']}/confirm",
            {"content_hash": batch["content_hash"]},
            format="json",
        )
        response = self.client.post(
            f"/api/imports/{batch['batch_id']}/apply",
            {"content_hash": batch["content_hash"]},
            format="json",
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "dependency_not_integrated")

    def test_adapter_failure_rolls_back_all_writes_and_keeps_preview(self):
        batch = self.upload().json()
        self.client.post(
            f"/api/imports/{batch['batch_id']}/confirm",
            {"content_hash": batch["content_hash"]},
            format="json",
        )

        class FailingAdapter:
            def apply(self, rows, *, actor):
                Custodian.objects.create(
                    full_name="Escritura parcial",
                    email="parcial@example.org",
                )
                raise ImportDomainConflict("Fallo simulado del dominio.")

        with patch(
            "inventory.imports.service._adapter",
            return_value=FailingAdapter(),
        ):
            response = self.client.post(
                f"/api/imports/{batch['batch_id']}/apply",
                {"content_hash": batch["content_hash"]},
                format="json",
            )
        self.assertEqual(response.status_code, 409, response.content)
        self.assertEqual(response.json()["code"], "import_domain_conflict")
        self.assertEqual(Custodian.objects.count(), 0)
        record = ImportBatch.objects.get(pk=batch["batch_id"])
        self.assertEqual(record.state, ImportBatch.State.CONFIRMED_ONCE)
        self.assertEqual(ImportBatchRow.objects.count(), 1)

    def test_license_lot_preview_and_template(self):
        response = self.upload(
            kind="license_lots",
            rows=[license_row(), license_row(product_name="Otro")],
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["summary"]["purchased_quantity"], 20)
        template = self.client.get("/api/imports/templates/license_lots/")
        self.assertEqual(template.status_code, 200)
        self.assertEqual(
            template.content.decode("utf-8").strip().split(","),
            list(LICENSE_LOT_FIELDS),
        )
        self.assertEqual(
            self.client.get("/api/imports/templates/otro/").status_code, 404
        )

    def test_cancel_clears_rows_and_cannot_cancel_applied(self):
        batch = self.upload().json()
        cancelled = self.client.post(f"/api/imports/{batch['batch_id']}/cancel")
        self.assertEqual(cancelled.status_code, 200, cancelled.content)
        self.assertEqual(cancelled.json()["state"], ImportBatch.State.CANCELLED)
        self.assertEqual(ImportBatchRow.objects.count(), 0)
        detail = self.client.get(f"/api/imports/{batch['batch_id']}").json()
        self.assertEqual(detail["rows"]["count"], 0)

    def test_expired_preview_is_hidden_and_cannot_confirm(self):
        batch = self.upload().json()
        record = ImportBatch.objects.get(pk=batch["batch_id"])
        record.expires_at = timezone.now() - timedelta(seconds=1)
        record.save(update_fields=["expires_at"])
        detail = self.client.get(f"/api/imports/{batch['batch_id']}")
        self.assertEqual(detail.status_code, 200, detail.content)
        self.assertEqual(detail.json()["state"], ImportBatch.State.EXPIRED)
        self.assertEqual(detail.json()["rows"]["count"], 0)
        self.assertEqual(ImportBatchRow.objects.count(), 0)
        response = self.client.post(
            f"/api/imports/{batch['batch_id']}/confirm",
            {"content_hash": batch["content_hash"]},
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_owner_and_manager_permissions(self):
        batch = self.upload().json()
        other = manager("otro")
        self.client.force_authenticate(other)
        self.assertEqual(
            self.client.get(f"/api/imports/{batch['batch_id']}").status_code, 403
        )
        self.assertEqual(
            self.client.post(f"/api/imports/{batch['batch_id']}/cancel").status_code,
            403,
        )
        plain = manager("sin-grupo")
        plain.groups.clear()
        self.client.force_authenticate(plain)
        self.assertEqual(self.upload().status_code, 403)
        self.client.force_authenticate(user=None)
        self.assertEqual(
            self.client.get("/api/imports/templates/assets/").status_code, 403
        )

    def test_get_rows_are_paginated(self):
        response = self.upload(
            rows=[
                asset_row(serial_number="S-1"),
                asset_row(serial_number="S-2"),
                asset_row(serial_number="S-3"),
            ]
        )
        batch_id = response.json()["batch_id"]
        with patch("inventory.imports.views.PAGE_SIZE", 2):
            page = self.client.get(f"/api/imports/{batch_id}?page=1").json()
            self.assertEqual(page["rows"]["count"], 3)
            self.assertEqual(len(page["rows"]["results"]), 2)
            self.assertTrue(page["rows"]["next"])
            second = self.client.get(f"/api/imports/{batch_id}?page=2").json()
            self.assertEqual(len(second["rows"]["results"]), 1)
            self.assertFalse(second["rows"]["next"])
            self.assertTrue(second["rows"]["previous"])
            self.assertEqual(
                self.client.get(f"/api/imports/{batch_id}?page=9").status_code, 400
            )

    def test_session_writes_require_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.actor)
        content = csv_bytes(ASSET_FIELDS, [asset_row()])
        payload = {
            "kind": "assets",
            "schema_version": "v1",
            "file": SimpleUploadedFile("import.csv", content, content_type="text/csv"),
        }
        self.assertEqual(
            client.post("/api/imports/previews", payload, format="multipart").status_code,
            403,
        )
        token = client.get("/api/auth/csrf/").json()["csrfToken"]
        payload["file"] = SimpleUploadedFile(
            "import.csv", content, content_type="text/csv"
        )
        response = client.post(
            "/api/imports/previews",
            payload,
            format="multipart",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 201, response.content)
