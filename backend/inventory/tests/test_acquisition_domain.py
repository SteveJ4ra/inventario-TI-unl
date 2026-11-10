"""T005/T006: servicios reales sin endpoints T007, PostgreSQL temporal."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from threading import Barrier
from unittest.mock import patch

from django.db import close_old_connections, IntegrityError
from django.test import TestCase, TransactionTestCase, override_settings
from rest_framework.exceptions import ValidationError, PermissionDenied

from inventory import acquisition_services as domain
from inventory.errors import Conflict
from inventory.models import Asset, AcquisitionDocument, AcquisitionLine, AssetChange, Faculty, Movement
from inventory.services import create_asset, record_operation
from .base import asset_data, manager
from .test_acquisitions import purchase


class AcquisitionDomainTests(TestCase):
    def setUp(self):
        self.actor = manager()
        self.faculty = Faculty.objects.create(name="Facultad ficticia")

    def document(self, **changes):
        return domain.create_document(actor=self.actor, data=purchase(**changes))

    def new_asset(self, document, **changes):
        return create_asset(actor=self.actor, data=asset_data(faculty_id=self.faculty.pk,
            acquisition_document_id=document.pk, **{"item_value": "300.00", "acquired_on": "2026-01-15", **changes}))

    def test_document_first_shared_purchase_and_historical_currency(self):
        doc = self.document()
        self.assertEqual(Asset.objects.count(), 0)
        first = self.new_asset(doc)
        second = self.new_asset(doc, serial_number="TEST-SECOND")
        with override_settings(ASSET_CURRENCY_CODE="EUR"):
            self.assertEqual(domain.acquisition_snapshot(first)["currency"], "USD")
        self.assertEqual(set(doc.items.values_list("asset_id", flat=True)), {first.pk, second.pk})
        self.assertEqual(doc.invoice_total, Decimal("1000.00"))
        self.assertEqual(first.revision, 0)

    def test_donation_and_unknown_date(self):
        doc = domain.create_document(actor=self.actor, data={"source": "DONATION",
            "reference": "TEST-ACTA", "support_type": "Acta"})
        data = asset_data(faculty_id=self.faculty.pk, acquisition_document_id=doc.pk,
                          item_value="25.00", date_unknown_reason="No consta en respaldo ficticio")
        asset = create_asset(actor=self.actor, data=data)
        line = asset.acquisition_line
        self.assertIsNone(line.acquired_on)
        self.assertEqual(line.item_value, Decimal("25.00"))

    def test_invalid_metadata_dates_reserved_fields_never_write(self):
        for field in ["reference", "document_date", "supplier", "invoice_total"]:
            data = purchase()
            del data[field]
            with self.assertRaises(ValidationError):
                domain.create_document(actor=self.actor, data=data)
        with self.assertRaises(ValidationError):
            domain.create_document(actor=self.actor, data=purchase(currency="EUR"))
        self.assertEqual(AcquisitionDocument.objects.count(), 0)
        doc = self.document()
        for extra in [{}, {"acquired_on": "2026-01-15", "date_unknown_reason": "Motivo"},
                      {"acquired_on": "fecha-inválida"}, {"date_unknown_reason": "   "}]:
            with self.subTest(extra=extra), self.assertRaises(ValidationError):
                create_asset(actor=self.actor, data=asset_data(faculty_id=self.faculty.pk,
                    acquisition_document_id=doc.pk, item_value="20.00", **extra))
        for field, value in [("created_by", self.actor.pk), ("revision", 99), ("code", "TI-FORGED")]:
            with self.assertRaises(ValidationError):
                create_asset(actor=self.actor, data=asset_data(faculty_id=self.faculty.pk,
                    acquisition_document_id=doc.pk, item_value="20.00", acquired_on="2026-01-15", **{field: value}))
        self.assertEqual((Asset.objects.count(), AcquisitionLine.objects.count()), (0, 0))

    def test_reference_and_decimal_validation_and_duplicate_rollback(self):
        doc = self.document()
        for changes in [{"faculty_id": 999999}, {"acquisition_document_id": 999999}, {"item_value": "1.001"}]:
            data = asset_data(faculty_id=self.faculty.pk, acquisition_document_id=doc.pk,
                              item_value="20.00", acquired_on="2026-01-15")
            data.update(changes)
            with self.assertRaises(ValidationError):
                create_asset(actor=self.actor, data=data)
        first = self.new_asset(doc)
        with self.assertRaises(Conflict):
            self.new_asset(doc)
        self.assertEqual((Asset.objects.count(), AcquisitionLine.objects.count()), (1, 1))
        self.assertEqual(AcquisitionLine.objects.get().asset_id, first.pk)

    def test_actual_line_failure_rolls_back_asset(self):
        doc = self.document()
        original = AcquisitionLine.objects.create
        def fail_after_insert(**kwargs):
            original(**kwargs)
            return original(**kwargs)  # Violación UNIQUE real en PostgreSQL.
        with patch.object(AcquisitionLine.objects, "create", side_effect=fail_after_insert):
            with self.assertRaises(IntegrityError):
                self.new_asset(doc)
        self.assertEqual((Asset.objects.count(), AcquisitionLine.objects.count()), (0, 0))
        self.assertEqual(AcquisitionDocument.objects.count(), 1)

    def test_associate_existing_asset_requires_revision_and_audits(self):
        asset = create_asset(actor=self.actor, data=asset_data())
        doc = self.document()
        payload = {"expected_revision": 0, "reason": "Documentación verificada",
                   "item_value": "300.00", "acquired_on": "2026-01-15"}
        line = domain.associate_asset(actor=self.actor, document_id=doc.pk, asset_id=asset.pk, data=payload)
        self.assertEqual(line.asset_id, asset.pk)
        asset.refresh_from_db()
        self.assertEqual(asset.revision, 1)
        event = AssetChange.objects.get(asset=asset)
        self.assertIsNone(event.before_json["acquisition"])
        self.assertEqual(event.after_json["acquisition"]["currency"], "USD")
        with self.assertRaises(Conflict):
            domain.associate_asset(actor=self.actor, document_id=doc.pk, asset_id=asset.pk, data=payload)
        self.assertEqual(AssetChange.objects.count(), 1)

    def test_audited_update_disables_rectification_without_rewriting_movement(self):
        asset = self.new_asset(self.document())
        asset, movement = record_operation(actor=self.actor, asset_id=asset.pk,
            operation=Movement.Type.CONDITION,
            data={"expected_revision": 0, "condition": "averiado", "reason": "Falla observada"})
        before = Movement.objects.filter(pk=movement.pk).values().get()
        updated = domain.update_asset(actor=self.actor, asset_id=asset.pk,
            data={"expected_revision": 1, "reason": "Dato verificado", "name": "Nombre corregido"})
        self.assertEqual(updated.revision, 2)
        self.assertEqual(AssetChange.objects.get().actor_id, self.actor.pk)
        self.assertEqual(Movement.objects.filter(pk=movement.pk).values().get(), before)
        from inventory.views import assets
        self.assertIsNone(assets().get(pk=asset.pk).latest_rectifiable_id)
        with self.assertRaises(Conflict):
            record_operation(actor=self.actor, asset_id=asset.pk, operation=Movement.Type.RECTIFICATION,
                data={"expected_revision": 2, "movement_id": movement.pk, "reason": "Intento"})
        self.assertEqual(Movement.objects.count(), 1)

    def test_audit_failure_rolls_back_update_and_reserved_fields_are_rejected(self):
        asset = self.new_asset(self.document())
        original = AssetChange.objects.create
        def fail_after_insert(**kwargs):
            original(**kwargs)
            return original(**kwargs)  # Misma revisión: UNIQUE real, no excepción ficticia.
        with patch.object(AssetChange.objects, "create", side_effect=fail_after_insert):
            with self.assertRaises(IntegrityError):
                domain.update_asset(actor=self.actor, asset_id=asset.pk,
                    data={"expected_revision": 0, "reason": "Corrección", "name": "Otro"})
        asset.refresh_from_db()
        self.assertEqual((asset.name, asset.revision, AssetChange.objects.count()), ("Portátil", 0, 0))
        for field, value in [("faculty_id", self.faculty.pk), ("location", "Otra"),
                             ("condition", "averiado"), ("current_custodian", None), ("revision", 99)]:
            with self.assertRaises(ValidationError):
                domain.update_asset(actor=self.actor, asset_id=asset.pk,
                    data={"expected_revision": 0, "reason": "Corrección", field: value})

    def test_duplicate_identity_on_edit_and_stale_revision_leave_no_writes(self):
        doc = self.document()
        first = self.new_asset(doc)
        second = self.new_asset(doc, serial_number="TEST-OTHER")
        for data in [
            {"expected_revision": 0, "reason": "Prueba", "serial_number": first.serial_number},
            {"expected_revision": 99, "reason": "Prueba", "name": "Otro nombre"},
        ]:
            with self.assertRaises(Conflict):
                domain.update_asset(actor=self.actor, asset_id=second.pk, data=data)
        second.refresh_from_db()
        self.assertEqual((second.serial_number, second.revision), ("TEST-OTHER", 0))
        self.assertEqual(AssetChange.objects.count(), 0)

    def test_line_edits_preserve_shared_document_and_currency_snapshots(self):
        doc = self.document()
        first = self.new_asset(doc)
        second = self.new_asset(doc, serial_number="TEST-OTHER", item_value="400.00")
        with override_settings(ASSET_CURRENCY_CODE="EUR"):
            domain.update_asset(actor=self.actor, asset_id=first.pk, data={
                "expected_revision": 0, "reason": "Valor comprobado", "item_value": "350.00",
                "date_unknown_reason": "No consta fecha en respaldo ficticio"})
        event = AssetChange.objects.get(asset=first)
        self.assertEqual(event.before_json["acquisition"]["currency"], "USD")
        self.assertEqual(event.after_json["acquisition"]["currency"], "USD")
        self.assertEqual(event.before_json["acquisition"]["acquired_on"], "2026-01-15")
        self.assertIsNone(event.after_json["acquisition"]["acquired_on"])
        self.assertEqual(event.after_json["acquisition"]["item_value"], "350.00")
        self.assertEqual(second.acquisition_line.item_value, Decimal("400.00"))
        doc.refresh_from_db()
        self.assertEqual((doc.invoice_total, doc.currency), (Decimal("1000.00"), "USD"))

    def test_document_non_applicable_reserved_and_non_finite_inputs_never_write(self):
        for data in [
            {"source": "DONATION", "reference": "TEST", "support_type": "Acta", "supplier": "Proveedor"},
            {"source": "DONATION", "reference": "TEST", "support_type": "Acta", "invoice_total": "10.00"},
            {"source": "DONATION", "reference": "TEST"},
            purchase(created_by=self.actor.pk), purchase(invoice_total="NaN"),
            purchase(invoice_total="Infinity"), purchase(invoice_total="1.001"),
            purchase(reference="   "), purchase(source="OTHER"), purchase(items=[{"asset_id": 1}]),
        ]:
            with self.subTest(data=data), self.assertRaises(ValidationError):
                domain.create_document(actor=self.actor, data=data)
        self.assertEqual(AcquisitionDocument.objects.count(), 0)
        doc = domain.create_document(actor=self.actor, data=purchase(items=[]))
        self.assertEqual(doc.items.count(), 0)

    def test_service_permissions_do_not_grant_operator_manager_access(self):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group
        actor = get_user_model().objects.create_user("operator_fixture")
        actor.groups.add(Group.objects.get_or_create(name="Operadores")[0])
        doc = self.document()
        asset = self.new_asset(doc)
        with self.assertRaises(PermissionDenied):
            domain.create_document(actor=actor, data=purchase())
        with self.assertRaises(PermissionDenied):
            create_asset(actor=actor, data=asset_data())
        with self.assertRaises(PermissionDenied):
            domain.update_asset(actor=actor, asset_id=asset.pk,
                data={"expected_revision": 0, "reason": "Intento", "name": "Otro"})
        self.assertEqual(AssetChange.objects.count(), 0)

    def test_asset_metadata_edit_preserves_custodian_snapshot(self):
        from inventory.services import create_custodian
        person = create_custodian(actor=self.actor, data={"full_name": "Persona ficticia", "email": "fixture@example.org"})
        asset = self.new_asset(self.document())
        asset, movement = record_operation(actor=self.actor, asset_id=asset.pk, operation=Movement.Type.DELIVERY,
            data={"expected_revision": 0, "custodian_id": person.pk, "destination": "Aula ficticia"})
        snapshot = dict(movement.custodian_snapshot)
        domain.update_asset(actor=self.actor, asset_id=asset.pk,
            data={"expected_revision": 1, "reason": "Nombre comprobado", "name": "Nombre correcto"})
        movement.refresh_from_db()
        self.assertEqual(movement.custodian_snapshot, snapshot)


    def test_unapproved_cases_are_explicitly_pending_and_never_written(self):
        for value in ["0.00", "-1.00"]:
            with self.assertRaises(Conflict) as caught:
                domain.create_document(actor=self.actor, data=purchase(invoice_total=value))
            self.assertEqual(caught.exception.error_code, "pending_decision")
        with self.assertRaises(Conflict) as caught:
            domain.create_document(actor=self.actor, data={"source": "DONATION", "reference": "TEST",
                "support_type": "Acta", "document_date": "2026-01-15"})
        self.assertEqual(caught.exception.error_code, "pending_decision")
        self.assertEqual(AcquisitionDocument.objects.count(), 0)
        doc = self.document()
        for value in ["0.00", "-1.00"]:
            with self.assertRaises(Conflict) as caught:
                self.new_asset(doc, item_value=value)
            self.assertEqual(caught.exception.error_code, "pending_decision")
        self.assertEqual((Asset.objects.count(), AcquisitionLine.objects.count()), (0, 0))

    def test_existing_association_rejects_invalid_date_and_preserves_current_line(self):
        existing = create_asset(actor=self.actor, data=asset_data())
        doc = self.document()
        data = {"expected_revision": 0, "reason": "Respaldo verificado", "item_value": "45.00"}
        before = Asset.objects.filter(pk=existing.pk).values().get()
        for date_data in [{}, {"date_unknown_reason": "   "},
                          {"acquired_on": "2026-01-15", "date_unknown_reason": "No consta"}]:
            with self.assertRaises(ValidationError):
                domain.associate_asset(actor=self.actor, document_id=doc.pk, asset_id=existing.pk, data={**data, **date_data})
        self.assertEqual(Asset.objects.filter(pk=existing.pk).values().get(), before)
        self.assertEqual((AcquisitionLine.objects.count(), AssetChange.objects.count()), (0, 0))
        line = domain.associate_asset(actor=self.actor, document_id=doc.pk, asset_id=existing.pk,
            data={**data, "date_unknown_reason": "No consta en respaldo ficticio"})
        other = self.document(reference="OTRA-FACTURA")
        with self.assertRaises(Conflict) as caught:
            domain.associate_asset(actor=self.actor, document_id=other.pk, asset_id=existing.pk,
                data={**data, "expected_revision": 1, "acquired_on": "2026-01-15"})
        self.assertEqual(caught.exception.error_code, "acquisition_exists")
        line.refresh_from_db()
        self.assertEqual((line.document_id, line.item_value, line.acquired_on), (doc.pk, Decimal("45.00"), None))
        existing.refresh_from_db()
        self.assertEqual((existing.revision, existing.faculty_id), (1, before["faculty_id"]))
        self.assertEqual((AcquisitionLine.objects.count(), AssetChange.objects.count()), (1, 1))

    def test_association_audit_sql_failure_rolls_back_line_and_asset_revision(self):
        existing = create_asset(actor=self.actor, data=asset_data())
        before = Asset.objects.filter(pk=existing.pk).values().get()
        doc = self.document()
        original = AssetChange.objects.create
        def duplicate_audit(**kwargs):
            original(**kwargs)
            return original(**kwargs)
        with patch.object(AssetChange.objects, "create", side_effect=duplicate_audit):
            with self.assertRaises(IntegrityError) as caught:
                domain.associate_asset(actor=self.actor, document_id=doc.pk, asset_id=existing.pk,
                    data={"expected_revision": 0, "reason": "Respaldo verificado", "item_value": "45.00", "acquired_on": "2026-01-15"})
        self.assertEqual(caught.exception.__cause__.sqlstate, "23505")
        self.assertEqual(Asset.objects.filter(pk=existing.pk).values().get(), before)
        self.assertEqual((AcquisitionLine.objects.count(), AssetChange.objects.count()), (0, 0))
        self.assertEqual(AcquisitionDocument.objects.count(), 1)


class AcquisitionConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.actor = manager()
        self.faculty = Faculty.objects.create(name="Facultad ficticia")
        self.doc = domain.create_document(actor=self.actor, data=purchase())
        self.asset = create_asset(actor=self.actor, data=asset_data(faculty_id=self.faculty.pk,
            acquisition_document_id=self.doc.pk, item_value="300.00", acquired_on="2026-01-15"))

    def test_two_edits_with_same_revision_commit_only_once(self):
        barrier = Barrier(2)
        def worker(name):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    domain.update_asset(actor=self.actor, asset_id=self.asset.pk,
                        data={"expected_revision": 0, "reason": "Verificación", "name": name})
                    return "ok"
                except Conflict:
                    return "conflict"
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(worker, ["Nombre A", "Nombre B"]))
        self.assertCountEqual(result, ["ok", "conflict"])
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.revision, 1)
        self.assertEqual(AssetChange.objects.count(), 1)

    def test_duplicate_registration_in_same_document_has_one_asset_and_line(self):
        # Usar identidad nueva para que dos sesiones compitan por el mismo alta.
        barrier = Barrier(2)
        def worker(_):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    create_asset(actor=self.actor, data=asset_data(serial_number="RACE-NEW",
                        faculty_id=self.faculty.pk, acquisition_document_id=self.doc.pk,
                        item_value="20.00", acquired_on="2026-01-15"))
                    return "ok"
                except Conflict:
                    return "conflict"
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(worker, [1, 2]))
        self.assertCountEqual(result, ["ok", "conflict"])
        self.assertEqual(Asset.objects.filter(serial_number="RACE-NEW").count(), 1)
        self.assertEqual(AcquisitionLine.objects.filter(asset__serial_number="RACE-NEW").count(), 1)

    def test_two_documents_compete_for_existing_asset_without_duplicate_lines(self):
        existing = create_asset(actor=self.actor, data=asset_data(serial_number="ASSOCIATION-RACE"))
        other = domain.create_document(actor=self.actor, data=purchase(reference="OTHER-DOCUMENT"))
        barrier = Barrier(2)
        def worker(document_id):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    domain.associate_asset(actor=self.actor, document_id=document_id, asset_id=existing.pk,
                        data={"expected_revision": 0, "reason": "Respaldo verificado", "item_value": "45.00", "acquired_on": "2026-01-15"})
                    return "ok"
                except Conflict:
                    return "conflict"
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(worker, [self.doc.pk, other.pk]))
        self.assertCountEqual(result, ["ok", "conflict"])
        existing.refresh_from_db()
        self.assertEqual(existing.revision, 1)
        self.assertEqual(AcquisitionLine.objects.filter(asset=existing).count(), 1)
        self.assertEqual(AssetChange.objects.filter(asset=existing).count(), 1)

    def test_concurrent_document_creation_with_reversed_items_has_one_winner(self):
        from rest_framework.test import APIClient
        first = create_asset(actor=self.actor, data=asset_data(serial_number="BATCH-A"))
        second = create_asset(actor=self.actor, data=asset_data(serial_number="BATCH-B"))
        barrier = Barrier(2)
        def worker(reverse):
            close_old_connections()
            try:
                client = APIClient()
                client.force_authenticate(self.actor)
                ids = [first.pk, second.pk]
                if reverse:
                    ids.reverse()
                items = [{"asset_id": pk, "item_value": "45.00", "expected_revision": 0,
                          "reason": "Respaldo verificado", "acquired_on": "2026-01-15"} for pk in ids]
                barrier.wait(timeout=10)
                return client.post("/api/acquisitions/", purchase(reference="BATCH-" + str(reverse), items=items), format="json").status_code
            finally:
                close_old_connections()
        before = AcquisitionDocument.objects.count()
        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(worker, [False, True]))
        self.assertCountEqual(result, [201, 409])
        self.assertEqual(AcquisitionDocument.objects.count(), before + 1)
        self.assertEqual(AcquisitionLine.objects.filter(asset_id__in=[first.pk, second.pk]).count(), 2)
        self.assertEqual(AssetChange.objects.filter(asset_id__in=[first.pk, second.pk]).count(), 2)
