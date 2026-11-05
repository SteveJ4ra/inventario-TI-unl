from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

from inventory.tests.base import asset_data


class LifecycleMigrationTests(TransactionTestCase):
    previous = ("inventory", "0003_importbatch")
    target = ("inventory", "0004_asset_lifecycle_events")

    def test_existing_assets_and_movement_history_survive_upgrade(self):
        executor = MigrationExecutor(connection)
        self.addCleanup(self.restore_schema)
        executor.migrate([self.previous])
        old = executor.loader.project_state([self.previous]).apps
        actor = old.get_model("auth", "User").objects.create(username="gestor-anterior")
        custodian = old.get_model("inventory", "Custodian").objects.create(
            full_name="Custodio anterior", email="anterior@example.org"
        )
        assets = old.get_model("inventory", "Asset").objects
        available = assets.create(
            code="TI-000001", created_by=actor, **asset_data()
        )
        assigned = assets.create(
            code="TI-000002", created_by=actor, assignment="asignado",
            current_custodian=custodian, revision=1,
            **asset_data(serial_number="LAB-002", location="Aula"),
        )
        before = {
            "condition": "operativo", "assignment": "disponible",
            "custodian_id": None, "location": "Laboratorio",
        }
        after = {
            **before, "assignment": "asignado", "custodian_id": custodian.pk,
            "location": "Aula",
        }
        movement = old.get_model("inventory", "Movement").objects.create(
            asset=assigned, actor=actor, actor_label=actor.username,
            type="entrega", custodian=custodian, before=before, after=after,
            resulting_revision=1,
        )

        executor = MigrationExecutor(connection)
        executor.migrate([self.target])
        new = executor.loader.project_state([self.target]).apps
        current_assets = new.get_model("inventory", "Asset").objects
        migrated_available = current_assets.get(pk=available.pk)
        migrated_assigned = current_assets.get(pk=assigned.pk)
        self.assertEqual(migrated_available.lifecycle_status, "localizado")
        self.assertEqual(migrated_available.assignment, "disponible")
        self.assertIsNone(migrated_available.current_custodian_id)
        self.assertEqual(migrated_assigned.lifecycle_status, "localizado")
        self.assertEqual(migrated_assigned.assignment, "asignado")
        self.assertEqual(migrated_assigned.current_custodian_id, custodian.pk)
        self.assertEqual(migrated_assigned.code, assigned.code)
        self.assertEqual(migrated_assigned.revision, 1)
        self.assertEqual(migrated_assigned.condition, "operativo")
        self.assertEqual(migrated_assigned.location, "Aula")
        original = new.get_model("inventory", "Movement").objects.get(pk=movement.pk)
        self.assertEqual(original.before, before)
        self.assertEqual(original.after, after)

    def restore_schema(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
