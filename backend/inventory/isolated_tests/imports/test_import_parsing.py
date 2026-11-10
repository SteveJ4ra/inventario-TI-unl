import csv
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from inventory.imports.parsing import ImportLimitExceeded, parse_import
from inventory.imports.schemas import ASSET_FIELDS, LICENSE_LOT_FIELDS, template_bytes


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


def parse(kind, content, version="v1"):
    return parse_import(
        kind=kind,
        content=content,
        schema_version=version,
        max_bytes=100_000,
        max_rows=100,
    )


class ImportParsingTests(unittest.TestCase):
    def test_asset_preview_is_complete_and_hash_is_stable(self):
        content = csv_bytes(ASSET_FIELDS, [asset_row(), asset_row(serial_number="S-002")])
        first = parse("assets", content)
        second = parse("assets", content)
        self.assertEqual(first.errors, ())
        self.assertEqual(first.summary["valid_rows"], 2)
        self.assertEqual(first.summary["document_count"], 1)
        self.assertEqual(first.content_hash, second.content_hash)
        self.assertEqual(first.rows[0]["item_value"], "50.00")

    def test_changed_content_changes_hash(self):
        one = parse("assets", csv_bytes(ASSET_FIELDS, [asset_row()]))
        two = parse(
            "assets",
            csv_bytes(ASSET_FIELDS, [asset_row(serial_number="S-999")]),
        )
        self.assertNotEqual(one.content_hash, two.content_hash)

    def test_asset_requires_exactly_one_document_source(self):
        row = asset_row(acquisition_document_id="7")
        preview = parse("assets", csv_bytes(ASSET_FIELDS, [row]))
        self.assertTrue(
            any(error.field == "acquisition_document_id" for error in preview.errors)
        )

    def test_asset_rejects_inconsistent_document_metadata(self):
        preview = parse(
            "assets",
            csv_bytes(
                ASSET_FIELDS,
                [
                    asset_row(serial_number="S-1"),
                    asset_row(serial_number="S-2", supplier="Otro proveedor"),
                ],
            ),
        )
        self.assertTrue(any(error.field == "document_key" for error in preview.errors))
        self.assertEqual(preview.summary["valid_rows"], 0)

    def test_asset_rejects_duplicate_identity(self):
        preview = parse(
            "assets",
            csv_bytes(
                ASSET_FIELDS,
                [
                    asset_row(serial_number="S-1"),
                    asset_row(serial_number="S-1"),
                ],
            ),
        )
        self.assertTrue(
            any(error.field == "serial_number" for error in preview.errors)
        )

    def test_asset_requires_one_acquisition_date_alternative(self):
        preview = parse(
            "assets",
            csv_bytes(
                ASSET_FIELDS,
                [
                    asset_row(
                        acquired_on="",
                        date_unknown_reason="No consta en el acta",
                    )
                ],
            ),
        )
        self.assertEqual(preview.errors, ())
        preview = parse(
            "assets",
            csv_bytes(
                ASSET_FIELDS,
                [asset_row(date_unknown_reason="También hay fecha")],
            ),
        )
        self.assertTrue(any(error.field == "acquired_on" for error in preview.errors))

    def test_license_lot_validates_quantities_and_dates(self):
        preview = parse(
            "license_lots",
            csv_bytes(
                LICENSE_LOT_FIELDS,
                [
                    license_row(),
                    license_row(in_use_quantity="11"),
                    license_row(ends_on="2025-12-31"),
                ],
            ),
        )
        fields = {(error.row, error.field) for error in preview.errors}
        self.assertIn((3, "in_use_quantity"), fields)
        self.assertIn((4, "ends_on"), fields)
        self.assertEqual(preview.summary["purchased_quantity"], 10)
        self.assertEqual(preview.summary["in_use_quantity"], 4)

    def test_bad_headers_and_encoding_are_rejected(self):
        bad_header = b"name,description\nPC,Equipo\n"
        preview = parse("assets", bad_header)
        self.assertEqual(preview.rows, ())
        self.assertEqual(preview.errors[0].field, "header")
        preview = parse("assets", b"\xff\xfe")
        self.assertEqual(preview.errors[0].field, "file")

    def test_header_without_data_rows_is_rejected(self):
        preview = parse("assets", csv_bytes(ASSET_FIELDS, []))
        self.assertEqual(preview.errors[0].field, "file")
        self.assertEqual(preview.summary["row_count"], 0)

    def test_unsupported_schema_version_is_reported(self):
        preview = parse("assets", csv_bytes(ASSET_FIELDS, [asset_row()]), version="v9")
        self.assertEqual(preview.errors[0].field, "schema_version")

    def test_unknown_kind_is_rejected(self):
        with self.assertRaises(ValueError):
            parse("otro", b"")

    def test_limits_are_enforced(self):
        with self.assertRaises(ImportLimitExceeded):
            parse_import(
                kind="assets",
                content=b"x" * 20,
                schema_version="v1",
                max_bytes=10,
                max_rows=10,
            )
        with self.assertRaises(ImportLimitExceeded):
            parse_import(
                kind="assets",
                content=csv_bytes(
                    ASSET_FIELDS, [asset_row(), asset_row(serial_number="S-2")]
                ),
                schema_version="v1",
                max_bytes=1000,
                max_rows=1,
            )

    def test_templates_have_the_expected_headers(self):
        assets = template_bytes("assets").decode("utf-8").strip().split(",")
        licenses = template_bytes("license_lots").decode("utf-8").strip().split(",")
        self.assertEqual(tuple(assets), ASSET_FIELDS)
        self.assertEqual(tuple(licenses), LICENSE_LOT_FIELDS)


if __name__ == "__main__":
    unittest.main()
