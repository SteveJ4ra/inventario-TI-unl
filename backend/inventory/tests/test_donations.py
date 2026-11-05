"""T011–T013: donaciones reales; datos ficticios solo en PostgreSQL temporal."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError, close_old_connections
from django.test import TransactionTestCase, override_settings
from rest_framework.test import APIClient

from inventory import acquisition_services as domain
from inventory.models import AcquisitionDocument, AcquisitionLine, Asset, AssetChange, Faculty, Movement
from inventory.services import create_asset, record_operation
from .base import InventoryCase, asset_data, manager


def donation(**changes):
    return {"source": "DONATION", "reference": "TEST-DON-ACTA", "support_type": "Acta ficticia", **changes}


class DonationFlowTests(InventoryCase):
    def setUp(self):
        super().setUp()
        self.faculty = Faculty.objects.create(name="Facultad ficticia de donación")

    def document(self):
        response = self.client.post("/api/acquisitions/", donation(), format="json")
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()

    def register(self, doc, **changes):
        return self.client.post("/api/assets/", asset_data(**{
            "faculty_id": self.faculty.pk, "acquisition_document_id": doc["id"],
            "item_value": "35.25", "acquired_on": "2026-01-15", **changes}), format="json")

    def test_shared_support_one_and_several_assets_preserve_individual_estimates(self):
        doc = self.document()
        self.assertEqual(doc["items"], [])
        self.assertEqual(Asset.objects.count(), 0)
        first = self.register(doc)
        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(first.json()["acquisition"]["source"], "DONATION")
        second = self.register(doc, serial_number="DON-SECOND", item_value="80.50",
                               acquired_on=None, date_unknown_reason="No consta en el acta")
        self.assertEqual(second.status_code, 201, second.content)
        detail = self.client.get(f'/api/acquisitions/{doc["id"]}/').json()
        self.assertEqual((detail["support_type"], detail["reference"]), ("Acta ficticia", "TEST-DON-ACTA"))
        self.assertIsNone(detail["invoice_total"])
        self.assertEqual(detail["supplier"], "")
        self.assertEqual({i["asset_id"]: i["item_value"] for i in detail["items"]},
                         {first.json()["id"]: "35.25", second.json()["id"]: "80.50"})
        self.assertEqual(AcquisitionDocument.objects.count(), 1)
        self.assertEqual(AcquisitionLine.objects.count(), 2)
        self.assertEqual(AssetChange.objects.count(), 0)  # Alta, sin edición ficticia.
        with override_settings(ASSET_CURRENCY_CODE="EUR"):
            asset = Asset.objects.get(pk=first.json()["id"])
            self.assertEqual(domain.acquisition_snapshot(asset)["currency"], "USD")

    def test_strict_document_fields_reject_without_writes(self):
        for data in [
            donation(reference="   "), donation(support_type="  "),
            donation(supplier="Proveedor"), donation(supplier=""),
            donation(invoice_total="10.00"), donation(invoice_total=None),
            donation(currency="EUR"), donation(created_by=self.actor.pk),
            donation(support_description="No inferir tipo"), donation(file="foto.png"),
        ]:
            with self.subTest(data=data):
                result = self.client.post("/api/acquisitions/", data, format="json")
                self.assertEqual(result.status_code, 400, result.content)
                self.assertEqual(AcquisitionDocument.objects.count(), 0)

    def test_pending_decisions_remain_explicit_no_writes(self):
        result = self.client.post("/api/acquisitions/", donation(document_date="2026-01-15"), format="json")
        self.assertEqual(result.status_code, 409)
        self.assertEqual(result.json()["code"], "pending_decision")
        self.assertEqual(AcquisitionDocument.objects.count(), 0)
        doc = self.document()
        for amount in ["0.00", "-1.00"]:
            result = self.register(doc, item_value=amount)
            self.assertEqual(result.status_code, 409, result.content)
            self.assertEqual(result.json()["code"], "pending_decision")
            self.assertEqual(Asset.objects.count(), 0)

    def test_invalid_dates_values_reserved_fields_and_references_never_write(self):
        doc = self.document()
        for changes in [
            {"acquired_on": None}, {"acquired_on": None, "date_unknown_reason": " "},
            {"date_unknown_reason": "Motivo"}, {"acquired_on": "invalida"},
            {"item_value": "1.001"}, {"item_value": "NaN"},
            {"faculty_id": 999999}, {"acquisition_document_id": 999999},
            {"estimated_value": "45.00"}, {"revision": 99}, {"source": "PURCHASE"},
        ]:
            with self.subTest(changes=changes):
                result = self.register(doc, **changes)
                self.assertEqual(result.status_code, 400, result.content)
                self.assertEqual((Asset.objects.count(), AcquisitionLine.objects.count(), AssetChange.objects.count()), (0, 0, 0))
                self.assertEqual(AcquisitionDocument.objects.count(), 1)

    def test_duplicate_identity_does_not_leave_partial_line(self):
        doc = self.document()
        first = self.register(doc)
        self.assertEqual(first.status_code, 201)
        result = self.register(doc)
        self.assertEqual(result.status_code, 409, result.content)
        self.assertEqual((Asset.objects.count(), AcquisitionLine.objects.count()), (1, 1))

    def test_real_line_constraint_failure_rolls_back_asset_but_keeps_support(self):
        doc = self.document()
        original = AcquisitionLine.objects.create
        def violate(**kwargs):
            kwargs["acquired_on"] = None
            kwargs["date_unknown_reason"] = ""
            return original(**kwargs)
        with patch.object(AcquisitionLine.objects, "create", side_effect=violate):
            with self.assertRaises(IntegrityError):
                self.register(doc)
        self.assertEqual((Asset.objects.count(), AcquisitionLine.objects.count()), (0, 0))
        self.assertEqual(AcquisitionDocument.objects.count(), 1)

    def test_donation_mutations_require_manager_and_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertEqual(client.post("/api/acquisitions/", donation(), format="json").status_code, 403)
        operator = get_user_model().objects.create_user("operador-donacion")
        operator.groups.add(Group.objects.get_or_create(name="Operadores")[0])
        for user in [operator, get_user_model().objects.create_user("sin-rol-donacion")]:
            client.force_authenticate(user)
            self.assertEqual(client.post("/api/acquisitions/", donation(), format="json").status_code, 403)
        client.force_authenticate(None)
        client.force_login(self.actor)
        self.assertEqual(client.post("/api/acquisitions/", donation(), format="json").status_code, 403)
        self.assertEqual(AcquisitionDocument.objects.count(), 0)
        token = client.get("/api/auth/csrf/").json()["csrfToken"]
        result = client.post("/api/acquisitions/", donation(), format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(result.status_code, 201, result.content)
        data = asset_data(faculty_id=self.faculty.pk, acquisition_document_id=result.json()["id"],
                          item_value="45.00", acquired_on="2026-01-15")
        self.assertEqual(client.post("/api/assets/", data, format="json").status_code, 403)
        self.assertEqual(Asset.objects.count(), 0)
        self.assertEqual(client.post("/api/assets/", data, format="json", HTTP_X_CSRFTOKEN=token).status_code, 201)


class DonationConcurrencyTests(TransactionTestCase):
    def test_simultaneous_registration_same_identity_creates_one_asset_and_line(self):
        actor = manager("gestor-donacion-race")
        faculty = Faculty.objects.create(name="Facultad ficticia concurrente")
        doc = domain.create_document(actor=actor, data=donation())
        barrier = Barrier(2)
        def worker(_):
            close_old_connections()
            try:
                client = APIClient()
                client.force_authenticate(actor)
                barrier.wait(timeout=10)
                return client.post("/api/assets/", asset_data(
                    faculty_id=faculty.pk, acquisition_document_id=doc.pk,
                    item_value="45.50", date_unknown_reason="No consta"), format="json").status_code
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(worker, [1, 2]))
        self.assertCountEqual(results, [201, 409])
        self.assertEqual((Asset.objects.count(), AcquisitionLine.objects.count()), (1, 1))


    def test_concurrent_initial_associations_in_reverse_order_commit_one_document(self):
        actor = manager("gestor-donation-items")
        first = create_asset(actor=actor, data=asset_data(serial_number="DON-RACE-A"))
        second = create_asset(actor=actor, data=asset_data(serial_number="DON-RACE-B"))
        barrier = Barrier(2)
        def worker(reverse):
            close_old_connections()
            try:
                client = APIClient()
                client.force_authenticate(actor)
                ids = [first.pk, second.pk]
                if reverse:
                    ids.reverse()
                items = [{"asset_id": pk, "estimated_value": "55.50", "expected_revision": 0,
                          "reason": "Acta verificada", "acquired_on": "2026-01-15"} for pk in ids]
                barrier.wait(timeout=10)
                result = client.post("/api/acquisitions/", donation(reference="DON-RACE-" + str(reverse), items=items), format="json")
                return result.status_code
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(worker, [True, False]))
        self.assertCountEqual(results, [201, 409])
        self.assertEqual((AcquisitionDocument.objects.count(), AcquisitionLine.objects.count(), AssetChange.objects.count()), (1, 2, 2))
        self.assertEqual(list(Asset.objects.order_by("id").values_list("revision", flat=True)), [1, 1])


class DonationExistingItemsTests(InventoryCase):
    def setUp(self):
        super().setUp()
        self.first = create_asset(actor=self.actor, data=asset_data(serial_number="DON-EXIST-A"))
        self.second = create_asset(actor=self.actor, data=asset_data(serial_number="DON-EXIST-B"))

    def item(self, asset, **changes):
        return {"asset_id": asset.pk, "estimated_value": "45.00", "expected_revision": asset.revision,
                "reason": "Acta verificada", "acquired_on": "2026-01-15", **changes}

    def post(self, items):
        return self.client.post("/api/acquisitions/", donation(items=items), format="json")

    def assert_empty(self):
        self.assertEqual((AcquisitionDocument.objects.count(), AcquisitionLine.objects.count(), AssetChange.objects.count()), (0, 0, 0))
        self.assertEqual(list(Asset.objects.order_by("id").values_list("revision", flat=True)), [0, 0])

    def test_grouped_association_audits_and_preserves_previous_movement(self):
        self.first, movement = record_operation(actor=self.actor, asset_id=self.first.pk, operation=Movement.Type.CONDITION,
            data={"expected_revision": 0, "condition": "averiado", "reason": "Fixture histórica"})
        before = Movement.objects.filter(pk=movement.pk).values().get()
        result = self.post([self.item(self.first), self.item(self.second, estimated_value="90.50",
                           acquired_on=None, date_unknown_reason="No consta")])
        self.assertEqual(result.status_code, 201, result.content)
        doc = result.json()
        self.assertEqual({i["asset_id"]: i["item_value"] for i in doc["items"]}, {self.first.pk: "45.00", self.second.pk: "90.50"})
        self.assertEqual(Asset.objects.count(), 2)
        self.assertEqual(AcquisitionDocument.objects.count(), 1)
        for asset in [self.first, self.second]:
            event = AssetChange.objects.get(asset=asset)
            self.assertIsNone(event.before_json["acquisition"])
            self.assertEqual(event.after_json["acquisition"]["source"], "DONATION")
            self.assertEqual(event.after_json["acquisition"]["support_type"], "Acta ficticia")
            self.assertEqual(event.after_json["acquisition"]["currency"], "USD")
            self.assertEqual(event.actor_id, self.actor.pk)
            asset.refresh_from_db()
            self.assertEqual(event.resulting_revision, asset.revision)
            self.assertIsNone(asset.faculty_id)
        self.assertEqual(Movement.objects.filter(pk=movement.pk).values().get(), before)
        self.assertIsNone(self.client.get(f"/api/assets/{self.first.pk}/").json()["rectifiable_movement_id"])

    def test_strict_items_reject_missing_fields_reserved_fields_and_duplicates(self):
        for field in ["expected_revision", "reason", "acquired_on", "estimated_value"]:
            item = self.item(self.first)
            del item[field]
            result = self.post([item])
            self.assertEqual(result.status_code, 400, result.content)
            self.assert_empty()
        for items in [
            [self.item(self.first), self.item(self.first)],
            [self.item(self.first, item_value="50.00")],
            [self.item(self.first, date_unknown_reason="No consta")],
            [self.item(self.first, before_json={})],
        ]:
            result = self.post(items)
            self.assertEqual(result.status_code, 400, result.content)
            self.assert_empty()

    def test_stale_revision_and_missing_asset_roll_back_all_items(self):
        for changes, status in [({"expected_revision": 99}, 409), ({"asset_id": 999999}, 404)]:
            result = self.post([self.item(self.first), self.item(self.second, **changes)])
            self.assertEqual(result.status_code, status, result.content)
            if status == 409:
                self.assertEqual(result.json()["code"], "stale_revision")
            self.assert_empty()

    def test_existing_line_is_not_replaced(self):
        old_doc = domain.create_document(actor=self.actor, data=donation(reference="OLD-DON"))
        domain.associate_asset(actor=self.actor, document_id=old_doc.pk, asset_id=self.second.pk,
            data={"item_value": "25.00", "expected_revision": 0, "reason": "Verificado", "acquired_on": "2026-01-15"})
        self.second.refresh_from_db()
        old_line = AcquisitionLine.objects.filter(asset=self.second).values().get()
        result = self.post([self.item(self.first), self.item(self.second)])
        self.assertEqual(result.status_code, 409, result.content)
        self.assertEqual(result.json()["code"], "acquisition_exists")
        self.assertEqual((AcquisitionDocument.objects.count(), AcquisitionLine.objects.count(), AssetChange.objects.count()), (1, 1, 1))
        self.first.refresh_from_db()
        self.assertEqual(self.first.revision, 0)
        self.assertEqual(AcquisitionLine.objects.filter(asset=self.second).values().get(), old_line)

    def test_real_audit_sql_failure_reverts_document_lines_revisions_and_audits(self):
        original = AssetChange.objects.create
        count = 0
        def duplicate_second(**kwargs):
            nonlocal count
            count += 1
            event = original(**kwargs)
            return original(**kwargs) if count == 2 else event
        with patch.object(AssetChange.objects, "create", side_effect=duplicate_second):
            with self.assertRaises(IntegrityError) as error:
                self.post([self.item(self.first), self.item(self.second)])
        self.assertEqual(error.exception.__cause__.sqlstate, "23505")
        self.assert_empty()

    def test_nonpositive_initial_estimate_stays_pending_and_does_not_write(self):
        for amount in ["0.00", "-10.00"]:
            result = self.post([self.item(self.first), self.item(self.second, estimated_value=amount)])
            self.assertEqual(result.status_code, 409, result.content)
            self.assertEqual(result.json()["code"], "pending_decision")
            self.assert_empty()
