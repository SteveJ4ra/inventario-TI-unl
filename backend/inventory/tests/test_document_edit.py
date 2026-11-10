"""Contrato documental confirmado: snapshots y revisiones de todos los afectados."""
from unittest.mock import patch
from django.db import IntegrityError
from inventory import acquisition_services as domain
from inventory.models import Asset, AssetChange, AcquisitionDocumentChange
from .base import InventoryCase, AcquisitionFixtures


def snapshot(doc):
    return {field: (getattr(doc, field).isoformat() if field == "document_date" and getattr(doc, field)
                    else str(getattr(doc, field)) if field == "invoice_total" and getattr(doc, field) is not None
                    else getattr(doc, field))
            for field in ["source", "reference", "document_date", "supplier", "invoice_total", "support_type", "currency"]}


class DocumentEditTests(AcquisitionFixtures, InventoryCase):
    def setUp(self):
        super().setUp()
        self.asset, self.faculty, self.doc = self.acquisition_asset(self.actor)

    def payload(self, **changes):
        return {"reason": "Documento cotejado", "expected_document": snapshot(self.doc),
                "expected_revisions": {str(self.asset.pk): 0}, "reference": "CORREGIDA", **changes}

    def test_shared_document_event_and_asset_changes_commit_with_revisions(self):
        from inventory.services import create_asset
        from .base import asset_data
        other = create_asset(actor=self.actor, data=asset_data(faculty_id=self.faculty.pk, acquisition_document_id=self.doc.pk,
            item_value="80.25", acquired_on="2026-01-15", serial_number="DOC-OTHER"))
        payload = self.payload()
        payload["expected_revisions"][str(other.pk)] = 0
        result = self.client.patch(f"/api/acquisitions/{self.doc.pk}/", payload, format="json")
        self.assertEqual(result.status_code, 200, result.content)
        self.assertEqual(result.json()["reference"], "CORREGIDA")
        self.assertEqual(AcquisitionDocumentChange.objects.count(), 1)
        self.assertEqual(AssetChange.objects.count(), 2)
        self.assertCountEqual([item["item_value"] for item in result.json()["items"]], ["300.00", "80.25"])
        for asset in [self.asset, other]:
            asset.refresh_from_db()
            self.assertEqual(asset.revision, 1)
            event = AssetChange.objects.get(asset=asset)
            self.assertEqual(event.before_json["acquisition"]["reference"], self.doc.reference)
            self.assertEqual(event.after_json["acquisition"]["reference"], "CORREGIDA")
            self.assertEqual(event.resulting_revision, 1)

    def test_stale_snapshot_missing_members_and_revisions_never_write(self):
        for extra in [
            {"expected_document": {**snapshot(self.doc), "reference": "STALE"}},
            {"expected_revisions": {}},
            {"expected_revisions": {str(self.asset.pk): 99}},
        ]:
            result = self.client.patch(f"/api/acquisitions/{self.doc.pk}/", self.payload(**extra), format="json")
            self.assertEqual(result.status_code, 409, result.content)
            self.doc.refresh_from_db()
            self.assertNotEqual(self.doc.reference, "CORREGIDA")
            self.assertEqual((AssetChange.objects.count(), AcquisitionDocumentChange.objects.count()), (0, 0))

    def test_reserved_invalid_and_pending_money_reject_without_writes(self):
        for extra, status in [
            ({"source": "DONATION"}, 400), ({"currency": "EUR"}, 400),
            ({"invoice_total": "0.00"}, 409), ({"reference": " "}, 400),
            ({"support_type": "Acta"}, 400), ({"expected_revisions": {"fake": 0}}, 400),
        ]:
            result = self.client.patch(f"/api/acquisitions/{self.doc.pk}/", self.payload(**extra), format="json")
            self.assertEqual(result.status_code, status, result.content)
            self.assertEqual((AssetChange.objects.count(), AcquisitionDocumentChange.objects.count()), (0, 0))

    def test_sql_failure_in_document_audit_reverts_document_and_all_assets(self):
        original = AcquisitionDocumentChange.objects.create
        def invalid(**kwargs):
            kwargs.pop("actor"); kwargs["actor_id"] = None
            return original(**kwargs)
        with patch.object(AcquisitionDocumentChange.objects, "create", side_effect=invalid):
            with self.assertRaises(IntegrityError):
                self.client.patch(f"/api/acquisitions/{self.doc.pk}/", self.payload(), format="json")
        self.asset.refresh_from_db(); self.doc.refresh_from_db()
        self.assertEqual(self.asset.revision, 0)
        self.assertNotEqual(self.doc.reference, "CORREGIDA")
        self.assertEqual((AssetChange.objects.count(), AcquisitionDocumentChange.objects.count()), (0, 0))

    def test_empty_document_still_requires_snapshot_and_records_event(self):
        empty = domain.create_document(actor=self.actor, data={"source": "DONATION", "reference": "EMPTY", "support_type": "Acta"})
        payload = {"expected_document": snapshot(empty), "expected_revisions": {}, "reason": "Acta verificada", "support_type": "Convenio"}
        result = self.client.patch(f"/api/acquisitions/{empty.pk}/", payload, format="json")
        self.assertEqual(result.status_code, 200, result.content)
        self.assertEqual(result.json()["support_type"], "Convenio")
        self.assertEqual(AcquisitionDocumentChange.objects.get().before_json["support_type"], "Acta")
        self.assertEqual(AssetChange.objects.count(), 0)
        stale = self.client.patch(f"/api/acquisitions/{empty.pk}/", payload, format="json")
        self.assertEqual(stale.status_code, 409)

    def test_document_patch_roles_csrf_and_missing_reference(self):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group
        from rest_framework.test import APIClient
        client = APIClient(enforce_csrf_checks=True)
        path = f"/api/acquisitions/{self.doc.pk}/"
        self.assertEqual(client.patch(path, self.payload(), format="json").status_code, 403)
        operator = get_user_model().objects.create_user("doc-operator")
        operator.groups.add(Group.objects.get_or_create(name="Operadores")[0])
        client.force_authenticate(operator)
        self.assertEqual(client.patch(path, self.payload(), format="json").status_code, 403)
        client.force_authenticate(None); client.force_login(self.actor)
        self.assertEqual(client.patch(path, self.payload(), format="json").status_code, 403)
        self.assertEqual(AcquisitionDocumentChange.objects.count(), 0)
        token = client.get("/api/auth/csrf/").json()["csrfToken"]
        self.assertEqual(client.patch("/api/acquisitions/999999/", self.payload(), format="json", HTTP_X_CSRFTOKEN=token).status_code, 404)
        result = client.patch(path, self.payload(), format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(result.status_code, 200, result.content)


from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.db import close_old_connections
from django.test import TransactionTestCase
from rest_framework.test import APIClient
from .base import manager, asset_data
from .test_acquisitions import purchase


class DocumentConcurrencyTests(TransactionTestCase):
    def test_two_edits_of_empty_document_compare_snapshot_under_lock(self):
        actor = manager("doc-empty-race")
        doc = domain.create_document(actor=actor, data=purchase())
        barrier = Barrier(2)
        def worker(reference):
            close_old_connections()
            try:
                client = APIClient(); client.force_authenticate(actor)
                barrier.wait(timeout=10)
                return client.patch(f"/api/acquisitions/{doc.pk}/", {"expected_document": snapshot(doc),
                    "expected_revisions": {}, "reason": "Verificado", "reference": reference}, format="json").status_code
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(worker, ["EMPTY-A", "EMPTY-B"]))
        self.assertCountEqual(results, [200, 409])
        self.assertEqual(AcquisitionDocumentChange.objects.count(), 1)

    def test_document_edit_and_line_association_share_document_lock(self):
        from inventory.models import Faculty
        from inventory.services import create_asset
        actor = manager("doc-association-race")
        faculty = Faculty.objects.create(name="Facultad race documental")
        doc = domain.create_document(actor=actor, data=purchase())
        first = create_asset(actor=actor, data=asset_data(faculty_id=faculty.pk, acquisition_document_id=doc.pk,
            item_value="35.00", acquired_on="2026-01-15"))
        legacy = create_asset(actor=actor, data=asset_data(serial_number="DOC-LEGACY"))
        barrier = Barrier(2)
        def worker(operation):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                if operation == "edit":
                    client = APIClient(); client.force_authenticate(actor)
                    return client.patch(f"/api/acquisitions/{doc.pk}/", {"expected_document": snapshot(doc),
                        "expected_revisions": {str(first.pk): 0}, "reason": "Cotejado", "reference": "EDITADA"},
                        format="json").status_code
                domain.associate_asset(actor=actor, document_id=doc.pk, asset_id=legacy.pk,
                    data={"expected_revision": 0, "reason": "Acta verificada", "item_value": "45.00", "acquired_on": "2026-01-15"})
                return "associated"
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(worker, ["edit", "associate"]))
        self.assertIn(result[0], [200, 409])
        self.assertEqual(result[1], "associated")
        self.assertEqual(AcquisitionDocumentChange.objects.count(), int(result[0] == 200))
        legacy.refresh_from_db()
        self.assertEqual(legacy.revision, 1)
