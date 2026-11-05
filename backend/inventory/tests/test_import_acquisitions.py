"""Integración 003/008 real: gateway de producción y PostgreSQL temporal."""
from unittest.mock import patch
from django.db import IntegrityError
from django.test import override_settings
from inventory import acquisition_services as domain
from inventory.models import AcquisitionDocument, AcquisitionLine, Asset, Faculty, ImportBatch
from .base import InventoryCase, asset_data
from .test_imports import asset_row, csv_file


@override_settings(IMPORT_GATEWAY="inventory.imports.gateways.DjangoProviderGateway")
class RealAcquisitionImportTests(InventoryCase):
    def setUp(self):
        super().setUp()
        self.faculty = Faculty.objects.create(name="Facultad ficticia CSV")

    def preview_confirm(self, rows):
        response = self.client.post("/api/imports/previews/", {"kind": "assets", "schema_version": "assets-v1",
            "file": csv_file("assets", rows)}, format="multipart")
        self.assertEqual(response.status_code, 201, response.content)
        batch = response.json()
        self.assertEqual(batch["errors"], [])
        result = self.client.post(f'/api/imports/{batch["batch_id"]}/confirm/', {"content_hash": batch["content_hash"]}, format="json")
        self.assertEqual(result.status_code, 200, result.content)
        return batch

    def apply(self, batch):
        return self.client.post(f'/api/imports/{batch["batch_id"]}/apply/', {"content_hash": batch["content_hash"]}, format="json")

    def row(self, **changes):
        return asset_row(**{"faculty_id": str(self.faculty.pk), **changes})

    def test_real_csv_shared_purchase_and_batch_idempotence(self):
        batch = self.preview_confirm([self.row(serial_number="CSV-A", item_value="35.25"),
                                      self.row(serial_number="CSV-B", item_value="80.50")])
        self.assertEqual((Asset.objects.count(), AcquisitionDocument.objects.count()), (0, 0))
        result = self.apply(batch)
        self.assertEqual(result.status_code, 201, result.content)
        self.assertEqual(result.json()["applied_result"]["created"], 2)
        self.assertEqual((Asset.objects.count(), AcquisitionDocument.objects.count(), AcquisitionLine.objects.count()), (2, 1, 2))
        self.assertCountEqual([str(value) for value in AcquisitionLine.objects.values_list("item_value", flat=True)], ["35.25", "80.50"])
        doc = AcquisitionDocument.objects.get()
        self.assertEqual((str(doc.invoice_total), doc.currency), ("1000.00", "USD"))
        self.assertEqual(self.apply(batch).status_code, 200)
        self.assertEqual(Asset.objects.count(), 2)

    def test_existing_donation_document_needs_no_support_adapter(self):
        doc = domain.create_document(actor=self.actor, data={"source": "DONATION", "reference": "CSV-ACTA", "support_type": "Acta"})
        batch = self.preview_confirm([self.row(acquisition_document_id=str(doc.pk), document_key="", document_source="",
            document_reference="", document_date="", supplier="", invoice_total="", serial_number="CSV-DON")])
        result = self.apply(batch)
        self.assertEqual(result.status_code, 201, result.content)
        self.assertEqual(AcquisitionDocument.objects.count(), 1)
        self.assertEqual(AcquisitionLine.objects.get().document_id, doc.pk)

    def test_actual_second_line_sql_failure_reverts_entire_batch_and_document(self):
        batch = self.preview_confirm([self.row(serial_number="ROLLBACK-A"), self.row(serial_number="ROLLBACK-B")])
        original = AcquisitionLine.objects.create
        count = 0
        def invalid_second(**kwargs):
            nonlocal count
            count += 1
            if count == 2:
                kwargs.update(acquired_on=None, date_unknown_reason="")
            return original(**kwargs)
        with patch.object(AcquisitionLine.objects, "create", side_effect=invalid_second):
            result = self.apply(batch)
        self.assertEqual(result.status_code, 409, result.content)
        self.assertEqual((Asset.objects.count(), AcquisitionDocument.objects.count(), AcquisitionLine.objects.count()), (0, 0, 0))
        stored = ImportBatch.objects.get(pk=batch["batch_id"])
        self.assertNotEqual(stored.state, ImportBatch.State.APPLIED)
        self.assertIsNone(stored.applied_result)

    def test_nonpositive_amount_is_pending_not_applied(self):
        batch = self.preview_confirm([self.row(item_value="0.00")])
        result = self.apply(batch)
        self.assertEqual(result.status_code, 409, result.content)
        self.assertEqual(result.json()["code"], "pending_decision")
        self.assertEqual((Asset.objects.count(), AcquisitionDocument.objects.count()), (0, 0))

    def test_direct_import_rejects_reserved_fields_and_bad_grouping_before_writes(self):
        from rest_framework.exceptions import ValidationError
        from inventory.imports.domain import parse_csv
        from inventory.imports import schemas
        raw = csv_file("assets", [self.row()]).read()
        parsed = parse_csv("assets", schemas.default_version("assets"), raw, max_bytes=2000000, max_rows=2000)
        values = parsed.rows[0]["values"]
        with self.assertRaises(ValidationError):
            domain.import_assets(actor=self.actor, rows=[{**values, "code": "FORGED"}])
        with self.assertRaises(ValidationError):
            domain.import_assets(actor=self.actor, rows=[values, {**values, "serial_number": "OTHER", "document_reference": "DIFFERENT"}])
        self.assertEqual((Asset.objects.count(), AcquisitionDocument.objects.count()), (0, 0))


    def test_new_donation_csv_remains_explicitly_blocked_by_human_decision(self):
        batch = self.preview_confirm([self.row(document_source="donacion", supplier="", invoice_total="",
            document_date="", support_description="Acta descrita")])
        result = self.apply(batch)
        self.assertEqual(result.status_code, 409, result.content)
        self.assertEqual(result.json()["code"], "pending_decision")
        self.assertEqual((Asset.objects.count(), AcquisitionDocument.objects.count()), (0, 0))

    def test_real_revalidation_detects_new_identity_without_partial_document(self):
        from inventory.services import create_asset
        batch = self.preview_confirm([self.row()])
        create_asset(actor=self.actor, data=asset_data(brand="Marca", model="Modelo A", serial_number="SER-1"))
        result = self.apply(batch)
        self.assertEqual(result.status_code, 409, result.content)
        self.assertEqual((Asset.objects.count(), AcquisitionDocument.objects.count(), AcquisitionLine.objects.count()), (1, 0, 0))


from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.db import close_old_connections
from django.test import TransactionTestCase
from rest_framework.test import APIClient
from .base import manager


@override_settings(IMPORT_GATEWAY="inventory.imports.gateways.DjangoProviderGateway")
class RealImportConcurrencyTests(TransactionTestCase):
    row = RealAcquisitionImportTests.row
    preview_confirm = RealAcquisitionImportTests.preview_confirm

    def test_simultaneous_real_apply_is_idempotent_with_one_shared_document(self):
        self.actor = manager("csv-real-race")
        self.faculty = Faculty.objects.create(name="Facultad CSV race")
        self.client = APIClient(); self.client.force_authenticate(self.actor)
        batch = self.preview_confirm([self.row(serial_number="RACE-CSV-A"), self.row(serial_number="RACE-CSV-B")])
        barrier = Barrier(2)
        def worker(_):
            close_old_connections()
            try:
                client = APIClient(); client.force_authenticate(self.actor)
                barrier.wait(timeout=10)
                result = client.post(f'/api/imports/{batch["batch_id"]}/apply/',
                    {"content_hash": batch["content_hash"]}, format="json")
                return result.status_code, result.json()["applied_result"]
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(worker, [1, 2]))
        self.assertCountEqual([status for status, _ in results], [201, 200])
        self.assertEqual(results[0][1], results[1][1])
        self.assertEqual((Asset.objects.count(), AcquisitionDocument.objects.count(), AcquisitionLine.objects.count()), (2, 1, 2))
