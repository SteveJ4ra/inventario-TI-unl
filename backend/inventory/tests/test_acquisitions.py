"""T001: aceptación 003; fallos rojos se mantienen visibles hasta T005–T007.

Las fixtures son ficticias. No se consulta la base local ni se inventa legado.
"""
from decimal import Decimal

from django.apps import apps
from inventory.models import Asset
from .base import AcquisitionFixtures, InventoryCase, asset_data


def purchase(**changes):
    return {"source": "PURCHASE", "reference": "TEST-FACT-1",
            "document_date": "2026-01-15", "supplier": "Proveedor ficticio",
            "invoice_total": "1000.00", **changes}


class AcquisitionApiTests(AcquisitionFixtures, InventoryCase):
    def document(self, **changes):
        response = self.client.post("/api/acquisitions/", purchase(**changes), format="json")
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()

    def faculty(self):
        self.require_acquisition_schema()
        return apps.get_model("inventory", "Faculty").objects.create(name="Facultad ficticia")

    def register(self, document, faculty, **changes):
        return self.client.post("/api/assets/", asset_data(
            faculty_id=faculty.pk, acquisition_document_id=document["id"],
            **{"item_value": "300.00", "acquired_on": "2026-01-15", **changes}), format="json")

    def test_metadata_document_without_assets_and_shared_purchase(self):
        document = self.document()
        self.assertEqual(Asset.objects.count(), 0)
        faculty = self.faculty()
        for serial, value in [("TEST-A", "300.00"), ("TEST-B", "400.00")]:
            response = self.register(document, faculty, serial_number=serial, item_value=value)
            self.assertEqual(response.status_code, 201, response.content)
        detail = self.client.get(f"/api/acquisitions/{document['id']}/")
        self.assertEqual(detail.status_code, 200)
        data = detail.json()
        self.assertEqual(Decimal(data["invoice_total"]), Decimal("1000.00"))
        self.assertEqual(data["currency"], "USD")
        self.assertEqual(len(data["items"]), 2)
        # El total no está obligado a igualar la suma (impuestos/envío).
        self.assertCountEqual([Decimal(i["item_value"]) for i in data["items"]],
                         [Decimal("300.00"), Decimal("400.00")])

    def test_purchase_required_fields_and_no_partial_document(self):
        for field in ["reference", "document_date", "supplier", "invoice_total"]:
            with self.subTest(field=field):
                data = purchase()
                del data[field]
                response = self.client.post("/api/acquisitions/", data, format="json")
                self.assertEqual(response.status_code, 400, response.content)
                self.assertIn(field, response.json()["fields"])
                self.require_acquisition_schema()
                Document = apps.get_model("inventory", "AcquisitionDocument")
                self.assertEqual(Document.objects.count(), 0)

    def test_donation_metadata_without_invoice(self):
        response = self.client.post("/api/acquisitions/", {
            "source": "DONATION", "reference": "TEST-ACTA", "support_type": "Acta"
        }, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["source"], "DONATION")
        self.assertEqual(response.json()["currency"], "USD")

    def test_shared_donation_retains_individual_estimates(self):
        response = self.client.post("/api/acquisitions/", {
            "source": "DONATION", "reference": "TEST-ACTA", "support_type": "Acta"
        }, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        document = response.json()
        faculty = self.faculty()
        for serial, value in [("DON-A", "25.00"), ("DON-B", "60.00")]:
            result = self.register(document, faculty, serial_number=serial, item_value=value)
            self.assertEqual(result.status_code, 201, result.content)
        Line = apps.get_model("inventory", "AcquisitionLine")
        self.assertEqual(list(Line.objects.filter(document_id=document["id"])
                              .order_by("id").values_list("item_value", flat=True)),
                         [Decimal("25.00"), Decimal("60.00")])

    def test_unknown_acquisition_date_requires_reason_and_rejects_both(self):
        document = self.document()
        faculty = self.faculty()
        for extra in [{}, {"acquired_on": "2026-01-15", "date_unknown_reason": "Sin respaldo"}]:
            data = asset_data(faculty_id=faculty.pk, acquisition_document_id=document["id"],
                              item_value="20.00", **extra)
            response = self.client.post("/api/assets/", data, format="json")
            self.assertEqual(response.status_code, 400, response.content)
            self.assertEqual(Asset.objects.count(), 0)
        response = self.client.post("/api/assets/", asset_data(
            faculty_id=faculty.pk, acquisition_document_id=document["id"], item_value="20.00",
            date_unknown_reason="No consta en el respaldo ficticio"), format="json")
        self.assertEqual(response.status_code, 201, response.content)
        line = apps.get_model("inventory", "AcquisitionLine").objects.get(asset_id=response.json()["id"])
        self.assertIsNone(line.acquired_on)
        self.assertTrue(line.date_unknown_reason)

    def test_general_edit_requires_reason_and_rejects_reserved_state(self):
        asset, faculty, _document = self.acquisition_asset(self.actor)
        before = {field.attname: getattr(asset, field.attname) for field in asset._meta.fields}
        audit_model = apps.get_model("inventory", "AssetChange")
        for changes in [{"name": "Corregido"}, {"reason": "Corrección", "location": "Otra"},
                        {"reason": "Corrección", "condition": "averiado"},
                        {"reason": "Corrección", "assignment": "asignado"},
                        {"reason": "Corrección", "current_custodian": None},
                        {"reason": "Corrección", "faculty_id": faculty.pk}]:
            response = self.client.patch(f"/api/assets/{asset.pk}/",
                {"expected_revision": asset.revision, **changes}, format="json")
            self.assertEqual(response.status_code, 400, response.content)
            asset.refresh_from_db()
            self.assertEqual({field.attname: getattr(asset, field.attname) for field in asset._meta.fields}, before)
            self.assertEqual(audit_model.objects.filter(asset=asset).count(), 0)


class AcquisitionServiceTests(AcquisitionFixtures, InventoryCase):
    def test_service_validates_document_and_rolls_back_duplicate_asset_line(self):
        self.require_acquisition_schema()
        # Mismo punto de entrada de 002, ampliado en T006; sin fake de producción.
        from inventory.services import create_asset
        try:
            Document = apps.get_model("inventory", "AcquisitionDocument")
            Faculty = apps.get_model("inventory", "Faculty")
            Line = apps.get_model("inventory", "AcquisitionLine")
        except LookupError as exc:
            self.fail(f"T003 pendiente: {exc}")
        faculty = Faculty.objects.create(name="Facultad ficticia")
        document = Document.objects.create(created_by=self.actor, **purchase())
        data = asset_data(faculty_id=faculty.pk, acquisition_document_id=document.pk,
                          item_value="300.00", acquired_on="2026-01-15")
        first = create_asset(actor=self.actor, data=data)
        from inventory.errors import Conflict
        with self.assertRaises(Conflict):
            create_asset(actor=self.actor, data=data)
        self.assertEqual(Asset.objects.count(), 1)
        self.assertEqual(Line.objects.count(), 1)
        self.assertEqual(Line.objects.get().asset_id, first.pk)


class PurchaseFlowTests(InventoryCase):
    """T008–T010: factura primero, cada activo/línea atómicos; no lote ficticio."""
    def setUp(self):
        super().setUp()
        self.faculty_row = apps.get_model("inventory", "Faculty").objects.create(name="Facultad ficticia de compra")

    def invoice(self):
        response = self.client.post("/api/acquisitions/", purchase(), format="json")
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()

    def register_purchase(self, doc, **changes):
        data = asset_data(**{"faculty_id": self.faculty_row.pk, "acquisition_document_id": doc["id"],
            "item_value": "300.00", "acquired_on": "2026-01-15", **changes})
        return self.client.post("/api/assets/", data, format="json")

    def test_one_purchase_has_one_document_and_atomic_line(self):
        doc = self.invoice()
        self.assertEqual(doc["items"], [])
        response = self.register_purchase(doc)
        self.assertEqual(response.status_code, 201, response.content)
        data = response.json()
        detail = self.client.get(f"/api/acquisitions/{doc['id']}/").json()
        self.assertEqual(len(detail["items"]), 1)
        self.assertEqual(detail["items"][0]["asset_id"], data["id"])
        self.assertEqual(detail["items"][0]["asset_code"], data["code"])
        self.assertNotIn("invoice_total", detail["items"][0])
        self.assertEqual((data["revision"], detail["currency"]), (0, "USD"))

    def test_several_assets_reuse_invoice_and_keep_exact_individual_values(self):
        doc = self.invoice()
        expected = {}
        for serial, value in [("BUY-A", "300.25"), ("BUY-B", "400.50")]:
            response = self.register_purchase(doc, serial_number=serial, item_value=value)
            self.assertEqual(response.status_code, 201, response.content)
            expected[response.json()["id"]] = value
        detail = self.client.get(f"/api/acquisitions/{doc['id']}/").json()
        self.assertEqual({item["asset_id"]: item["item_value"] for item in detail["items"]}, expected)
        self.assertEqual(detail["invoice_total"], "1000.00")
        self.assertEqual(apps.get_model("inventory", "AcquisitionDocument").objects.count(), 1)
        self.assertEqual(apps.get_model("inventory", "AcquisitionLine").objects.count(), 2)

    def test_invalid_asset_does_not_write_but_keeps_previously_created_invoice(self):
        doc = self.invoice()
        for changes in [{"item_value": "1.001"}, {"faculty_id": 999999},
                        {"acquired_on": None, "date_unknown_reason": "   "}, {"code": "FORGED"}]:
            response = self.register_purchase(doc, **changes)
            self.assertEqual(response.status_code, 400, response.content)
            self.assertEqual(Asset.objects.count(), 0)
            self.assertEqual(apps.get_model("inventory", "AcquisitionLine").objects.count(), 0)
        self.assertEqual(apps.get_model("inventory", "AcquisitionDocument").objects.count(), 1)

    def test_database_failure_after_line_insert_rolls_back_asset_and_line(self):
        from unittest.mock import patch
        from django.db import IntegrityError
        Line = apps.get_model("inventory", "AcquisitionLine")
        doc = self.invoice()
        original = Line.objects.create
        def duplicate(**kwargs):
            original(**kwargs)
            return original(**kwargs)  # UNIQUE PostgreSQL real tras INSERT del activo y línea.
        with patch.object(Line.objects, "create", side_effect=duplicate):
            with self.assertRaises(IntegrityError) as caught:
                self.register_purchase(doc)
        self.assertEqual(caught.exception.__cause__.sqlstate, "23505")
        self.assertEqual((Asset.objects.count(), Line.objects.count()), (0, 0))
        self.assertEqual(apps.get_model("inventory", "AcquisitionDocument").objects.count(), 1)

    def test_failed_second_asset_preserves_first_without_creating_another_invoice(self):
        doc = self.invoice()
        first = self.register_purchase(doc)
        self.assertEqual(first.status_code, 201)
        rejected = self.register_purchase(doc)
        self.assertEqual(rejected.status_code, 409)
        self.assertEqual(Asset.objects.count(), 1)
        self.assertEqual(apps.get_model("inventory", "AcquisitionLine").objects.count(), 1)
        self.assertEqual(apps.get_model("inventory", "AcquisitionDocument").objects.count(), 1)
        self.assertEqual(self.client.get(f"/api/acquisitions/{doc['id']}/").json()["items"][0]["asset_id"], first.json()["id"])

    def test_invoice_read_does_not_change_revision_or_audit(self):
        doc = self.invoice()
        created = self.register_purchase(doc).json()
        before = Asset.objects.filter(pk=created["id"]).values().get()
        for _ in range(2):
            self.assertEqual(self.client.get(f"/api/acquisitions/{doc['id']}/").status_code, 200)
        self.assertEqual(Asset.objects.filter(pk=created["id"]).values().get(), before)
        self.assertEqual(apps.get_model("inventory", "AssetChange").objects.count(), 0)


class PurchaseExistingItemsTests(InventoryCase):
    def setUp(self):
        super().setUp()
        from inventory.services import create_asset
        self.first = create_asset(actor=self.actor, data=asset_data(serial_number="EXISTING-A"))
        self.second = create_asset(actor=self.actor, data=asset_data(serial_number="EXISTING-B"))

    def item(self, asset, **changes):
        return {"asset_id": asset.pk, "item_value": "45.00", "expected_revision": asset.revision,
                "reason": "Respaldo verificado", "acquired_on": "2026-01-15", **changes}

    def counts(self):
        return tuple(apps.get_model("inventory", name).objects.count()
                     for name in ["AcquisitionDocument", "AcquisitionLine", "AssetChange"])

    def test_document_and_existing_items_commit_together_with_audit(self):
        from inventory.services import record_operation
        from inventory.models import Movement
        self.first, movement = record_operation(actor=self.actor, asset_id=self.first.pk, operation=Movement.Type.CONDITION,
            data={"expected_revision": 0, "condition": "averiado", "reason": "Fixture histórica"})
        before_movement = Movement.objects.filter(pk=movement.pk).values().get()
        before = Asset.objects.filter(pk=self.second.pk).values().get()
        unknown = self.item(self.second)
        unknown.pop("acquired_on")
        unknown.update(date_unknown_reason="No consta en respaldo ficticio", item_value="80.25")
        response = self.client.post("/api/acquisitions/", purchase(items=[unknown, self.item(self.first)]), format="json")
        self.assertEqual(response.status_code, 201, response.content)
        doc = response.json()
        self.assertEqual(Asset.objects.count(), 2)
        self.assertEqual(self.counts(), (1, 2, 2))
        self.assertEqual({i["asset_id"]: i["item_value"] for i in doc["items"]}, {self.first.pk: "45.00", self.second.pk: "80.25"})
        after = Asset.objects.filter(pk=self.second.pk).values().get()
        self.assertEqual(after.pop("revision"), before.pop("revision") + 1)
        self.assertEqual(after, before)
        event = apps.get_model("inventory", "AssetChange").objects.get(asset_id=self.second.pk)
        self.assertIsNone(event.before_json["acquisition"])
        self.assertEqual(event.after_json["acquisition"]["document_id"], doc["id"])
        self.assertEqual(event.after_json["acquisition"]["currency"], "USD")
        self.assertEqual(event.actor_id, self.actor.pk)
        self.assertEqual(Movement.objects.filter(pk=movement.pk).values().get(), before_movement)
        self.assertIsNone(self.client.get(f"/api/assets/{self.first.pk}/").json()["rectifiable_movement_id"])

    def test_invalid_item_fields_and_duplicate_ids_leave_no_writes(self):
        for field in ["expected_revision", "reason", "acquired_on"]:
            item = self.item(self.first)
            del item[field]
            response = self.client.post("/api/acquisitions/", purchase(items=[item]), format="json")
            self.assertEqual(response.status_code, 400, response.content)
            self.assertEqual(self.counts(), (0, 0, 0))
        for items in [[self.item(self.first), self.item(self.first)],
                      [self.item(self.first, before_json={})],
                      [self.item(self.first, date_unknown_reason="No consta")]]:
            response = self.client.post("/api/acquisitions/", purchase(items=items), format="json")
            self.assertEqual(response.status_code, 400, response.content)
            self.assertEqual(self.counts(), (0, 0, 0))
        self.first.refresh_from_db()
        self.assertEqual(self.first.revision, 0)

    def test_stale_second_item_rolls_back_document_and_first_item(self):
        response = self.client.post("/api/acquisitions/", purchase(items=[self.item(self.first), self.item(self.second, expected_revision=99)]), format="json")
        self.assertEqual(response.status_code, 409, response.content)
        self.assertEqual(response.json()["code"], "stale_revision")
        self.assertEqual(self.counts(), (0, 0, 0))
        self.first.refresh_from_db(); self.second.refresh_from_db()
        self.assertEqual((self.first.revision, self.second.revision), (0, 0))

    def test_existing_line_is_never_replaced_and_all_new_associations_roll_back(self):
        from inventory import acquisition_services as domain
        old_doc = domain.create_document(actor=self.actor, data=purchase(reference="OLD"))
        domain.associate_asset(actor=self.actor, document_id=old_doc.pk, asset_id=self.second.pk,
            data={key: value for key, value in self.item(self.second).items() if key != "asset_id"})
        self.second.refresh_from_db()
        response = self.client.post("/api/acquisitions/", purchase(items=[self.item(self.first), self.item(self.second)]), format="json")
        self.assertEqual(response.status_code, 409, response.content)
        self.assertEqual(response.json()["code"], "acquisition_exists")
        self.assertEqual(self.counts(), (1, 1, 1))
        self.first.refresh_from_db()
        self.assertEqual(self.first.revision, 0)
        self.assertEqual(apps.get_model("inventory", "AcquisitionLine").objects.get().document_id, old_doc.pk)

    def test_missing_asset_rolls_back_the_entire_post(self):
        response = self.client.post("/api/acquisitions/", purchase(items=[self.item(self.first), self.item(self.second, asset_id=999999)]), format="json")
        self.assertEqual(response.status_code, 404, response.content)
        self.assertEqual(self.counts(), (0, 0, 0))
        self.first.refresh_from_db()
        self.assertEqual(self.first.revision, 0)

    def test_real_sql_failure_on_second_audit_rolls_back_everything(self):
        from unittest.mock import patch
        from django.db import IntegrityError
        Audit = apps.get_model("inventory", "AssetChange")
        original = Audit.objects.create
        calls = 0
        def fail_second(**kwargs):
            nonlocal calls
            calls += 1
            event = original(**kwargs)
            if calls == 2:
                return original(**kwargs)
            return event
        with patch.object(Audit.objects, "create", side_effect=fail_second):
            with self.assertRaises(IntegrityError) as caught:
                self.client.post("/api/acquisitions/", purchase(items=[self.item(self.first), self.item(self.second)]), format="json")
        self.assertEqual(caught.exception.__cause__.sqlstate, "23505")
        self.assertEqual(self.counts(), (0, 0, 0))
        self.assertEqual(list(Asset.objects.order_by("id").values_list("revision", flat=True)), [0, 0])
