"""T014–T017: edición y frontera 005; solo PostgreSQL temporal."""
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.contrib.auth.models import Group
from django.db import IntegrityError, connection, transaction, close_old_connections
from django.test import TransactionTestCase
from rest_framework.test import APIClient
from inventory import acquisition_services as domain, faculty_services
from inventory.errors import Conflict
from inventory.models import Asset, AssetChange, AssetFacultyChange, Custodian, CustodianChange, Faculty, Movement
from inventory.services import create_asset, create_custodian, record_operation
from .base import AcquisitionFixtures, InventoryCase, manager, asset_data


class MetadataEditTests(AcquisitionFixtures, InventoryCase):
    def setUp(self):
        super().setUp()
        self.asset, self.faculty, self.doc = self.acquisition_asset(self.actor)

    def test_asset_edit_audit_history_and_rectification_guard(self):
        asset, movement = record_operation(actor=self.actor, asset_id=self.asset.pk, operation=Movement.Type.CONDITION,
            data={"expected_revision": 0, "condition": "averiado", "reason": "Prueba histórica"})
        old = Movement.objects.filter(pk=movement.pk).values().get()
        response = self.client.patch(f"/api/assets/{asset.pk}/",
            {"expected_revision": 1, "reason": "Etiqueta verificada", "name": "Nombre corregido"}, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["revision"], 2)
        event = AssetChange.objects.get(asset=asset)
        self.assertEqual((event.before_json["name"], event.after_json["name"]), (asset.name, "Nombre corregido"))
        self.assertEqual((event.actor_id, event.resulting_revision), (self.actor.pk, 2))
        self.assertIsNotNone(event.created_at)
        self.assertEqual(Movement.objects.filter(pk=movement.pk).values().get(), old)
        history = self.client.get(f"/api/assets/{asset.pk}/history/").json()
        self.assertEqual([e["event_type"] for e in history], ["asset_change", "movement"])
        rejected = self.client.post(f"/api/assets/{asset.pk}/rectify/",
            {"expected_revision": 2, "movement_id": movement.pk, "reason": "No debe rectificar"}, format="json")
        self.assertEqual(rejected.status_code, 409)
        self.assertEqual(AssetChange.objects.count(), 1)

    def test_duplicate_identity_and_reserved_fields_do_not_write(self):
        other = create_asset(actor=self.actor, data=asset_data(serial_number="OTHER-EDIT"))
        before = Asset.objects.filter(pk=self.asset.pk).values().get()
        for values, status in [
            ({"brand": other.brand, "model": other.model, "serial_number": other.serial_number}, 409),
            ({"name": " "}, 400), ({"location": "Otra"}, 400), ({"faculty_id": self.faculty.pk}, 400),
            ({"condition": "averiado"}, 400), ({"current_custodian": None}, 400),
            ({"resulting_revision": 7}, 400), ({"source": "DONATION"}, 400),
            ({"acquired_on": None, "date_unknown_reason": ""}, 400),
        ]:
            result = self.client.patch(f"/api/assets/{self.asset.pk}/",
                {"expected_revision": 0, "reason": "Corrección", **values}, format="json")
            self.assertEqual(result.status_code, status, result.content)
            self.assertEqual(Asset.objects.filter(pk=self.asset.pk).values().get(), before)
            self.assertEqual(AssetChange.objects.count(), 0)

    def test_real_audit_failure_rolls_back_metadata_line_and_revision(self):
        original = AssetChange.objects.create
        def duplicate(**kwargs):
            original(**kwargs)
            return original(**kwargs)
        before = domain.acquisition_snapshot(self.asset)
        with patch.object(AssetChange.objects, "create", side_effect=duplicate):
            with self.assertRaises(IntegrityError):
                self.client.patch(f"/api/assets/{self.asset.pk}/", {"expected_revision": 0, "reason": "Corrección",
                    "name": "No persistir", "item_value": "55.50"}, format="json")
        self.asset.refresh_from_db()
        self.assertEqual((self.asset.revision, AssetChange.objects.count()), (0, 0))
        self.assertEqual(domain.acquisition_snapshot(self.asset), before)

    def test_faculty_service_missing_provider_and_permissions_do_not_write(self):
        operator = manager("operator-edit")
        operator.groups.clear()
        operator.groups.add(Group.objects.get_or_create(name="Operadores")[0])
        target = Faculty.objects.create(name="Facultad destino ficticia")
        from inventory.errors import DependencyUnavailable
        with self.assertRaises(DependencyUnavailable):
            faculty_services.change_asset_faculty(actor=operator, asset_id=self.asset.pk,
                data={"faculty_id": target.pk, "reason": "Cambio verificado", "expected_revision": 0})
        self.asset.refresh_from_db()
        self.assertEqual((self.asset.faculty_id, self.asset.revision), (self.faculty.pk, 0))
        self.assertEqual(AssetFacultyChange.objects.count(), 0)

    def test_faculty_guard_pending_allowed_stale_and_sql_rollback(self):
        operator = manager("operator-guard")
        operator.groups.clear()
        operator.groups.add(Group.objects.get_or_create(name="Operadores")[0])
        target = Faculty.objects.create(name="Facultad destino guard ficticia")
        payload = {"faculty_id": target.pk, "reason": "Cambio verificado", "expected_revision": 0}
        # Fakes únicamente en tests: no representan integración real con 005.
        with patch.object(faculty_services, "ensure_no_pending_decommission", side_effect=Conflict("Pendiente", "pending_request")):
            with self.assertRaises(Conflict):
                faculty_services.change_asset_faculty(actor=operator, asset_id=self.asset.pk, data=payload)
        self.assertEqual(AssetFacultyChange.objects.count(), 0)
        original = AssetFacultyChange.objects.create
        def duplicate(**kwargs):
            original(**kwargs)
            return original(**kwargs)
        with patch.object(faculty_services, "ensure_no_pending_decommission"):
            with patch.object(AssetFacultyChange.objects, "create", side_effect=duplicate):
                with self.assertRaises(IntegrityError):
                    faculty_services.change_asset_faculty(actor=operator, asset_id=self.asset.pk, data=payload)
            self.asset.refresh_from_db()
            self.assertEqual((self.asset.faculty_id, self.asset.revision), (self.faculty.pk, 0))
            faculty_services.change_asset_faculty(actor=operator, asset_id=self.asset.pk, data=payload)
            event = AssetFacultyChange.objects.get()
            self.assertEqual((event.previous_faculty_id, event.new_faculty_id, event.resulting_revision), (self.faculty.pk, target.pk, 1))
            with self.assertRaises(Conflict):
                faculty_services.change_asset_faculty(actor=operator, asset_id=self.asset.pk, data=payload)
        self.asset.refresh_from_db()
        self.assertEqual((self.asset.faculty_id, self.asset.revision), (target.pk, 1))


    def test_guard_database_errors_propagate_and_catalog_is_operator_only(self):
        from django.db import OperationalError
        from rest_framework.exceptions import PermissionDenied
        op = manager("operator-database-error")
        op.groups.clear(); op.groups.add(Group.objects.get_or_create(name="Operadores")[0])
        target = Faculty.objects.create(name="Destino error", active=False)
        payload = {"faculty_id": target.pk, "reason": "Verificado", "expected_revision": 0}
        with self.assertRaises(PermissionDenied):
            faculty_services.change_asset_faculty(actor=self.actor, asset_id=self.asset.pk, data=payload)
        with patch.object(faculty_services, "ensure_no_pending_decommission", side_effect=OperationalError("Provider failure")):
            with self.assertRaises(OperationalError):
                faculty_services.change_asset_faculty(actor=op, asset_id=self.asset.pk, data=payload)
        self.asset.refresh_from_db()
        self.assertEqual((self.asset.faculty_id, self.asset.revision, AssetFacultyChange.objects.count()), (self.faculty.pk, 0, 0))
        self.assertEqual(self.client.get("/api/operator/faculties/").status_code, 403)
        self.client.force_authenticate(op)
        result = self.client.get("/api/operator/faculties/")
        self.assertEqual(result.status_code, 200)
        self.assertIn(target.pk, [row["id"] for row in result.json()])


class CustodianEditTests(AcquisitionFixtures, InventoryCase):
    def setUp(self):
        super().setUp()
        self.person = create_custodian(actor=self.actor, data={"full_name": "Persona previa", "email": "previa@example.org", "department": "Área previa"})
        self.profile = {"full_name": self.person.full_name, "email": self.person.email, "department": self.person.department}
        self.asset, self.faculty, self.doc = self.acquisition_asset(self.actor)

    def payload(self, **changes):
        return {"expected_profile": self.profile, "reason": "Datos verificados", "full_name": "Persona corregida", **changes}

    def test_audited_correction_preserves_movement_snapshot_and_asset_revision(self):
        asset, movement = record_operation(actor=self.actor, asset_id=self.asset.pk, operation=Movement.Type.DELIVERY,
            data={"expected_revision": 0, "custodian_id": self.person.pk, "destination": "Aula"})
        old = Movement.objects.filter(pk=movement.pk).values().get()
        result = self.client.patch(f"/api/custodians/{self.person.pk}/", self.payload(), format="json")
        self.assertEqual(result.status_code, 200, result.content)
        self.assertEqual(result.json()["full_name"], "Persona corregida")
        event = CustodianChange.objects.get()
        self.assertEqual(event.before_json, {"profile": self.profile})
        self.assertEqual(event.after_json["profile"]["full_name"], "Persona corregida")
        self.assertEqual(event.after_json["reason"], "Datos verificados")
        self.assertEqual(event.actor_id, self.actor.pk)
        self.assertIsNotNone(event.created_at)
        self.assertEqual(Movement.objects.filter(pk=movement.pk).values().get(), old)
        asset.refresh_from_db()
        self.assertEqual(asset.revision, 1)
        self.assertEqual(asset.current_custodian_id, self.person.pk)
        self.assertEqual(AssetChange.objects.count(), 0)

    def test_stale_profile_validation_reserved_and_duplicates_do_not_write(self):
        create_custodian(actor=self.actor, data={"full_name": "Otra", "email": "other@example.org", "department": ""})
        for changes, status in [
            ({"expected_profile": {**self.profile, "full_name": "Obsoleto"}}, 409),
            ({"reason": ""}, 400), ({"email": "invalido"}, 400), ({"email": "OTHER@example.org"}, 409),
            ({"full_name": " "}, 400), ({"revision": 99}, 400), ({"asset_id": self.asset.pk}, 400),
        ]:
            result = self.client.patch(f"/api/custodians/{self.person.pk}/", self.payload(**changes), format="json")
            self.assertEqual(result.status_code, status, result.content)
            self.person.refresh_from_db()
            self.assertEqual(self.person.full_name, self.profile["full_name"])
            self.assertEqual(CustodianChange.objects.count(), 0)
        missing = self.payload(); del missing["expected_profile"]
        self.assertEqual(self.client.patch(f"/api/custodians/{self.person.pk}/", missing, format="json").status_code, 400)

    def test_sql_failure_rolls_back_profile_and_evidence(self):
        original = CustodianChange.objects.create
        def invalid(**kwargs):
            kwargs["actor_id"] = None
            kwargs.pop("actor")
            return original(**kwargs)
        with patch.object(CustodianChange.objects, "create", side_effect=invalid):
            with self.assertRaises(IntegrityError):
                self.client.patch(f"/api/custodians/{self.person.pk}/", self.payload(), format="json")
        self.person.refresh_from_db()
        self.assertEqual(self.person.full_name, self.profile["full_name"])
        self.assertEqual(CustodianChange.objects.count(), 0)

    def test_permissions_csrf_and_evidence_sql_protection(self):
        from django.contrib.auth import get_user_model
        client = APIClient(enforce_csrf_checks=True)
        path = f"/api/custodians/{self.person.pk}/"
        self.assertEqual(client.patch(path, self.payload(), format="json").status_code, 403)
        op = get_user_model().objects.create_user("custodian-op")
        op.groups.add(Group.objects.get_or_create(name="Operadores")[0])
        client.force_authenticate(op)
        self.assertEqual(client.patch(path, self.payload(), format="json").status_code, 403)
        client.force_authenticate(None); client.force_login(self.actor)
        self.assertEqual(client.patch(path, self.payload(), format="json").status_code, 403)
        token = client.get("/api/auth/csrf/").json()["csrfToken"]
        self.assertEqual(client.patch(path, self.payload(), format="json", HTTP_X_CSRFTOKEN=token).status_code, 200)
        event = CustodianChange.objects.get()
        from django.db import DatabaseError
        for sql in ["UPDATE inventory_custodianchange SET after_json='{}' WHERE id=%s", "DELETE FROM inventory_custodianchange WHERE id=%s"]:
            with self.assertRaises(DatabaseError):
                with transaction.atomic(), connection.cursor() as cursor:
                    cursor.execute(sql, [event.pk])
        self.assertEqual(CustodianChange.objects.get().after_json["reason"], "Datos verificados")


class MetadataConcurrencyTests(TransactionTestCase):
    def run_race(self, actor, payloads):
        barrier = Barrier(2)
        def worker(payload):
            close_old_connections()
            try:
                client = APIClient(); client.force_authenticate(actor)
                barrier.wait(timeout=10)
                return client.patch(payload[0], payload[1], format="json").status_code
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(worker, payloads))

    def test_custodian_two_corrections_on_same_profile_have_one_winner(self):
        actor = manager("custodian-race")
        person = create_custodian(actor=actor, data={"full_name": "Original", "email": "race@example.org", "department": ""})
        profile = {"full_name": person.full_name, "email": person.email, "department": person.department}
        path = f"/api/custodians/{person.pk}/"
        results = self.run_race(actor, [(path, {"expected_profile": profile, "reason": "Verificado", "full_name": name})
                                       for name in ["Corrección A", "Corrección B"]])
        self.assertCountEqual(results, [200, 409])
        self.assertEqual(CustodianChange.objects.count(), 1)

    def test_asset_two_api_edits_share_global_revision(self):
        actor = manager("asset-edit-race")
        asset = create_asset(actor=actor, data=asset_data(serial_number="EDIT-RACE"))
        path = f"/api/assets/{asset.pk}/"
        results = self.run_race(actor, [(path, {"expected_revision": 0, "reason": "Verificado", "name": name})
                                       for name in ["Nombre A", "Nombre B"]])
        self.assertCountEqual(results, [200, 409])
        asset.refresh_from_db()
        self.assertEqual((asset.revision, AssetChange.objects.count()), (1, 1))

    def test_faculty_two_api_changes_one_winner_with_test_only_provider(self):
        operator = manager("faculty-change-race")
        operator.groups.clear(); operator.groups.add(Group.objects.get_or_create(name="Operadores")[0])
        actor = manager("faculty-asset-owner")
        faculty = Faculty.objects.create(name="Facultad inicial race")
        asset = create_asset(actor=actor, data=asset_data(serial_number="FACULTY-RACE"))
        Asset.objects.filter(pk=asset.pk).update(faculty=faculty)  # Fixture verificada, solo test.
        targets = [Faculty.objects.create(name=name) for name in ["Facultad A race", "Facultad B race"]]
        path = f"/api/operator/assets/{asset.pk}/faculty/"
        with patch.object(faculty_services, "ensure_no_pending_decommission"):
            results = self.run_race(operator, [(path, {"expected_revision": 0, "reason": "Verificado", "faculty_id": target.pk}) for target in targets])
        self.assertCountEqual(results, [200, 409])
        asset.refresh_from_db()
        self.assertEqual((asset.revision, AssetFacultyChange.objects.count()), (1, 1))
