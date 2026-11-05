"""T004 expansión: SQL y migraciones solo en PostgreSQL aislado del runner."""
from datetime import date
from decimal import Decimal
from uuid import uuid4

from django.db import connection, transaction, DatabaseError, IntegrityError
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.exceptions import IrreversibleError
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ProjectState
from django.apps import apps
from django.test import TestCase
from django.utils import timezone

from inventory.models import (
    Asset, Faculty, AcquisitionDocument, AcquisitionLine, AssetChange,
    AssetFacultyChange, AcquisitionDocumentChange, CustodianChange, Custodian,
)
from inventory.services import create_asset
from .base import asset_data, manager


class ExpansionSchemaTests(TestCase):
    def test_empty_installation_and_nullable_faculty_without_database_default(self):
        for model in [Asset, Faculty, AcquisitionDocument, AcquisitionLine, AssetChange,
                      AssetFacultyChange, AcquisitionDocumentChange, CustodianChange]:
            self.assertEqual(model.objects.count(), 0)
        field = Asset._meta.get_field("faculty")
        self.assertTrue(field.null)
        self.assertFalse(field.has_default())
        with connection.cursor() as cursor:
            cursor.execute("""SELECT is_nullable, column_default FROM information_schema.columns
                              WHERE table_schema = current_schema() AND table_name = 'inventory_asset'
                              AND column_name = 'faculty_id'""")
            self.assertEqual(cursor.fetchone(), ("YES", None))
        actor = manager()
        asset = create_asset(actor=actor, data=asset_data())
        self.assertIsNone(asset.faculty_id)
        self.assertEqual(AcquisitionLine.objects.count(), 0)


    def test_migration_state_matches_models_and_reverse_is_blocked(self):
        executor = MigrationExecutor(connection)
        self.assertEqual(executor.loader.graph.leaf_nodes("inventory"),
                         [("inventory", "0007_retirement_workflow")])
        self.assertEqual(MigrationAutodetector(executor.loader.project_state(),
                         ProjectState.from_apps(apps)).changes(graph=executor.loader.graph, trim_to_apps={"inventory"}), {})
        with self.assertRaises(IrreversibleError):
            with transaction.atomic():
                executor.migrate([("inventory", "0003_importbatch")])
        self.assertIn(("inventory", "0004_acquisition_expansion"),
                      executor.recorder.applied_migrations())
        self.assertEqual(Faculty.objects.count(), 0)

    def test_only_legacy_text_checks_are_not_validated_yet(self):
        with connection.cursor() as cursor:
            cursor.execute("""SELECT conname FROM pg_constraint
                              WHERE connamespace = current_schema()::regnamespace
                              AND contype = 'c' AND NOT convalidated ORDER BY conname""")
            names = {row[0] for row in cursor.fetchall()}
        self.assertEqual(names, {"asset_code_required", "asset_name_required", "asset_description_required",
            "asset_brand_required", "asset_model_required", "asset_serial_number_required", "asset_location_required",
            "custodian_name_required", "custodian_email_required"})


class ExpansionIntegrityTests(TestCase):
    def setUp(self):
        self.actor = manager()
        self.asset = create_asset(actor=self.actor, data=asset_data())
        self.person = Custodian.objects.create(full_name="Persona ficticia", email="fixture@example.org")
        self.old_faculty = Faculty.objects.create(name="Facultad ficticia A")
        self.new_faculty = Faculty.objects.create(name="Facultad ficticia B")
        self.document = AcquisitionDocument.objects.create(
            source="PURCHASE", reference="TEST-FACTURA", document_date=date(2026, 1, 15),
            supplier="Proveedor ficticio", invoice_total=Decimal("1000.00"), created_by=self.actor)
        self.line = AcquisitionLine.objects.create(document=self.document, asset=self.asset,
                                                   item_value=Decimal("300.00"), acquired_on=date(2026, 1, 15))

    def assert_sql_rejected(self, sql, params, code):
        with self.assertRaises(DatabaseError) as caught:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(sql, params)
        self.assertEqual(caught.exception.__cause__.sqlstate, code)

    def test_all_new_audits_reject_sql_update_and_delete(self):
        common = dict(actor=self.actor, before_json={"old": "dato"}, after_json={"new": "dato"})
        self.asset.revision = 2
        self.asset.save(update_fields=["revision"])
        audits = [
            AssetChange.objects.create(asset=self.asset, reason="Corrección", resulting_revision=1, **common),
            AssetFacultyChange.objects.create(asset=self.asset, previous_faculty=self.old_faculty,
                new_faculty=self.new_faculty, reason="Corrección", resulting_revision=2, **common),
            CustodianChange.objects.create(custodian=self.person, **common),
            AcquisitionDocumentChange.objects.create(document=self.document, reason="Corrección", **common),
        ]
        for event in audits:
            table = connection.ops.quote_name(event._meta.db_table)
            with self.subTest(table=table):
                self.assert_sql_rejected(f"UPDATE {table} SET after_json = '{{}}' WHERE id = %s", [event.pk], "55000")
                self.assert_sql_rejected(f"DELETE FROM {table} WHERE id = %s", [event.pk], "55000")
                event.refresh_from_db()
                self.assertEqual(event.after_json, {"new": "dato"})

    def test_domain_delete_is_prohibited_even_without_references(self):
        bare_asset = create_asset(actor=self.actor, data=asset_data(serial_number="UNREFERENCED"))
        bare_document = AcquisitionDocument.objects.create(
            source="DONATION", reference="TEST-ACTA", support_type="Acta", created_by=self.actor)
        for instance in [bare_asset, bare_document, self.line]:
            table = connection.ops.quote_name(instance._meta.db_table)
            self.assert_sql_rejected(f"DELETE FROM {table} WHERE id = %s", [instance.pk], "55000")
            self.assertTrue(type(instance).objects.filter(pk=instance.pk).exists())

    def test_catalog_references_and_one_line_per_asset(self):
        self.asset.faculty = self.old_faculty
        self.asset.save(update_fields=["faculty"])
        with self.assertRaises(IntegrityError):
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute("DELETE FROM inventory_faculty WHERE id = %s", [self.old_faculty.pk])
                cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AcquisitionLine.objects.create(document=self.document, asset=self.asset,
                    item_value=Decimal("10.00"), acquired_on=date(2026, 1, 15))
        self.assertEqual(AcquisitionLine.objects.count(), 1)

    def test_sql_text_date_and_revision_constraints(self):
        statements = [
            ("UPDATE inventory_faculty SET name = %s WHERE id = %s", [" \t\n", self.old_faculty.pk]),
            ("UPDATE inventory_acquisitiondocument SET reference = %s WHERE id = %s", ["   ", self.document.pk]),
            ("UPDATE inventory_acquisitiondocument SET supplier = %s WHERE id = %s", ["   ", self.document.pk]),
            ("UPDATE inventory_acquisitionline SET acquired_on = NULL, date_unknown_reason = %s WHERE id = %s", ["   ", self.line.pk]),
            ("UPDATE inventory_asset SET name = %s WHERE id = %s", ["   ", self.asset.pk]),
            ("UPDATE inventory_custodian SET full_name = %s WHERE id = %s", ["   ", self.person.pk]),
        ]
        for sql, params in statements:
            with self.subTest(sql=sql):
                self.assert_sql_rejected(sql, params, "23514")
        for model, extra in [
            (AssetChange, {}),
            (AssetFacultyChange, {"previous_faculty": self.old_faculty, "new_faculty": self.new_faculty}),
        ]:
            data = dict(asset=self.asset, actor=self.actor, reason="Corrección", before_json={}, after_json={}, **extra)
            for invalid in [dict(data, resulting_revision=0), dict(data, resulting_revision=1, reason="   ")]:
                with self.assertRaises(IntegrityError), transaction.atomic():
                    model.objects.create(**invalid)
            model.objects.create(**data, resulting_revision=1)
            with self.assertRaises(IntegrityError), transaction.atomic():
                model.objects.create(**data, resulting_revision=1)
            self.assertEqual(model.objects.count(), 1)

    def test_document_required_metadata_and_unknown_date_constraint_on_insert(self):
        for data in [
            {"source": "PURCHASE", "reference": "TEST", "supplier": "Proveedor"},
            {"source": "DONATION", "reference": "TEST", "support_type": "   "},
        ]:
            with self.assertRaises(IntegrityError), transaction.atomic():
                AcquisitionDocument.objects.create(created_by=self.actor, **data)
        other = create_asset(actor=self.actor, data=asset_data(serial_number="TEST-UNKNOWN"))
        with self.assertRaises(IntegrityError), transaction.atomic():
            AcquisitionLine.objects.create(document=self.document, asset=other, item_value=Decimal("20.00"),
                                            acquired_on=date(2026, 1, 15), date_unknown_reason="No consta")
        line = AcquisitionLine.objects.create(document=self.document, asset=other, item_value=Decimal("20.00"),
                                               date_unknown_reason="No consta en respaldo ficticio")
        self.assertIsNone(line.acquired_on)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Faculty.objects.create(name=" facultad ficticia a ")

    def test_multirow_delete_has_no_partial_effects(self):
        create_asset(actor=self.actor, data=asset_data(serial_number="TEST-SECOND"))
        count = Asset.objects.count()
        self.assert_sql_rejected("DELETE FROM inventory_asset", [], "55000")
        self.assertEqual(Asset.objects.count(), count)



class HistoricalExpansionTests(TestCase):
    def test_0003_records_survive_without_invented_faculty_or_acquisition(self):
        # Schema privado de esta prueba, dentro de transacción rollback. Nunca public/local.
        schema = "test_003_" + uuid4().hex
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_setting('search_path')")
            original = cursor.fetchone()[0]
            cursor.execute('CREATE SCHEMA ' + connection.ops.quote_name(schema))
            cursor.execute("SELECT set_config('search_path', %s, true)", [schema])
        try:
            executor = MigrationExecutor(connection)
            executor.migrate([("inventory", "0003_importbatch")])
            old = executor.loader.project_state([("inventory", "0003_importbatch")]).apps
            User = old.get_model("auth", "User")
            user = User.objects.create(username="legacy_fixture")
            OldAsset = old.get_model("inventory", "Asset")
            asset = OldAsset.objects.create(code="TI-LEGACY", created_by_id=user.pk,
                                           revision=1, **asset_data())
            # Dato histórico defectuoso deliberado: no corregirlo automáticamente.
            dirty = OldAsset.objects.create(code="TI-LEGACY-DIRTY", created_by_id=user.pk,
                                           **asset_data(name="   ", serial_number="LEGACY-DIRTY"))
            movement = old.get_model("inventory", "Movement").objects.create(
                asset_id=asset.pk, actor_id=user.pk, actor_label=user.username, type="cambio_condicion",
                before={"condition": "averiado"}, after={"condition": "operativo"},
                reason="Fixture histórica", resulting_revision=1)
            batch = old.get_model("inventory", "ImportBatch").objects.create(
                owner_id=user.pk, kind="assets", schema_version="assets-v1", content_hash="a" * 64,
                expires_at=timezone.now(), preview_summary={"fixture": True})
            before_asset = OldAsset.objects.filter(pk=asset.pk).values().get()
            before_movement = old.get_model("inventory", "Movement").objects.filter(pk=movement.pk).values().get()
            before_batch = old.get_model("inventory", "ImportBatch").objects.filter(pk=batch.pk).values().get()
            with connection.cursor() as cursor:
                cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            executor = MigrationExecutor(connection)
            executor.migrate([("inventory", "0004_acquisition_expansion")])
            current = executor.loader.project_state([("inventory", "0004_acquisition_expansion")]).apps
            after_asset = current.get_model("inventory", "Asset").objects.filter(pk=asset.pk).values().get()
            self.assertIsNone(after_asset.pop("faculty_id"))
            self.assertEqual(after_asset, before_asset)
            self.assertEqual(current.get_model("inventory", "Asset").objects.get(pk=dirty.pk).name, "   ")
            self.assertEqual(current.get_model("inventory", "Movement").objects.filter(pk=movement.pk).values().get(), before_movement)
            self.assertEqual(current.get_model("inventory", "ImportBatch").objects.filter(pk=batch.pk).values().get(), before_batch)
            for name in ["Faculty", "AcquisitionDocument", "AcquisitionLine", "AssetChange", "AssetFacultyChange", "CustodianChange", "AcquisitionDocumentChange"]:
                self.assertEqual(current.get_model("inventory", name).objects.count(), 0)
        finally:
            with connection.cursor() as cursor:
                cursor.execute("SELECT set_config('search_path', %s, true)", [original])
