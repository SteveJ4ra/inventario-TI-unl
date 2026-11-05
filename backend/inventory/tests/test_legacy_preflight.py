import json
from io import StringIO
from django.core.management import call_command
from inventory.legacy_preflight import acquisition_preflight
from inventory.models import Asset, Faculty
from inventory.services import create_asset
from .base import InventoryCase, asset_data

class LegacyPreflightTests(InventoryCase):
    def test_empty_database_reports_readiness_without_creating_rows(self):
        result = acquisition_preflight()
        self.assertEqual((result["asset_count"], result["unmapped_assets"]), (0, []))
        self.assertTrue(result["faculty_data_ready"])
        self.assertTrue(result["requires_release_review"])
        self.assertFalse(result["writes_performed"])
        self.assertEqual(Faculty.objects.count(), 0)

    def test_historical_assets_require_explicit_mapping_and_never_get_acquisition_invented(self):
        asset = create_asset(actor=self.actor, data=asset_data())
        result = acquisition_preflight()
        self.assertFalse(result["faculty_data_ready"])
        self.assertEqual(result["unmapped_assets"], [{"id": asset.pk, "code": asset.code}])
        self.assertEqual(result["missing_acquisition_count"], 1)
        asset.refresh_from_db()
        self.assertIsNone(asset.faculty_id)
        faculty = Faculty.objects.create(name="Facultad verificada solo en test")
        Asset.objects.filter(pk=asset.pk).update(faculty=faculty)
        output = StringIO()
        call_command("acquisition_preflight", stdout=output)
        report = json.loads(output.getvalue())
        self.assertTrue(report["faculty_data_ready"])
        self.assertEqual(report["missing_acquisition_count"], 1)

    def contract_migration(self):
        from pathlib import Path
        from importlib.machinery import SourceFileLoader
        from importlib.util import spec_from_loader, module_from_spec
        path = Path(__file__).resolve().parents[3] / "specs/003-fichas-adquisiciones/migration-notes/faculty_contract.py.txt"
        loader = SourceFileLoader("reviewed_faculty_contract", str(path))
        module = module_from_spec(spec_from_loader(loader.name, loader))
        loader.exec_module(module)
        return module.Migration("reviewed_faculty_contract", "inventory")

    def test_contract_template_aborts_on_unmapped_historical_asset(self):
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor
        create_asset(actor=self.actor, data=asset_data())
        state = MigrationExecutor(connection).loader.project_state()
        with self.assertRaises(RuntimeError):
            with connection.schema_editor() as editor:
                self.contract_migration().apply(state, editor)
        self.assertIsNone(Asset.objects.get().faculty_id)

    def test_contract_template_preserves_verified_asset_and_rejects_new_null(self):
        from django.db import connection, transaction, IntegrityError
        from django.db.migrations.executor import MigrationExecutor
        asset = create_asset(actor=self.actor, data=asset_data())
        faculty = Faculty.objects.create(name="Facultad mapeada en test")
        Asset.objects.filter(pk=asset.pk).update(faculty=faculty)
        before = Asset.objects.filter(pk=asset.pk).values().get()
        # Vaciar eventos FK diferidos de las fixtures antes del DDL, sin desactivar constraints.
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        state = MigrationExecutor(connection).loader.project_state()
        with connection.schema_editor() as editor:
            self.contract_migration().apply(state, editor)
        self.assertEqual(Asset.objects.filter(pk=asset.pk).values().get(), before)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                create_asset(actor=self.actor, data=asset_data(serial_number="NULL-REJECTED"))
