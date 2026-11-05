from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone as datetime_timezone
from threading import Barrier
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import close_old_connections
from django.test import TransactionTestCase, override_settings
from rest_framework.exceptions import APIException
from rest_framework.test import APIClient, APITestCase

from inventory.services import create_license_lot, update_license_lot


from datetime import date, timedelta

from django.core.exceptions import ValidationError as ModelValidationError
from django.db import DatabaseError, IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from inventory.models import LicenseLotAudit, SoftwareLicenseLot
from .base import manager


def lot_data(**changes):
    return {
        "product_name": "Suite académica",
        "vendor": "Proveedor de prueba",
        "license_model": "USER_SEAT",
        "purchased_quantity": 10,
        "in_use_quantity": 4,
        "starts_on": date(2026, 1, 1),
        "ends_on": None,
        **changes,
    }


class LicenseLotModelTests(TestCase):
    def setUp(self):
        self.actor = manager()

    def lot(self, **changes):
        return SoftwareLicenseLot.objects.create(
            created_by=self.actor, **lot_data(**changes)
        )

    def test_zero_remaining_and_temporal_boundaries(self):
        today = timezone.localdate()
        lot = self.lot(starts_on=today, ends_on=today)
        self.assertEqual(lot.remaining_quantity, 6)
        self.assertEqual(lot.status_on(today), "CURRENT")
        self.assertEqual(lot.status_on(today + timedelta(days=1)), "EXPIRED")
        self.assertEqual(lot.status_on(today - timedelta(days=1)), "NOT_STARTED")
        self.assertEqual(lot.remaining_quantity, 6)
        zero = self.lot(purchased_quantity=0, in_use_quantity=0)
        self.assertEqual(zero.remaining_quantity, 0)
        self.assertEqual(zero.status_on(date(2099, 1, 1)), "CURRENT")

    def test_database_rejects_invalid_values_even_without_api(self):
        for changes in [
            {"purchased_quantity": -1},
            {"in_use_quantity": -1},
            {"in_use_quantity": 11},
            {"starts_on": None},
            {"ends_on": date(2025, 12, 31)},
            {"license_model": "UNLIMITED"},
        ]:
            with self.subTest(changes=changes):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    self.lot(**changes)
        self.assertEqual(SoftwareLicenseLot.objects.count(), 0)

    def test_audit_is_immutable_in_orm_bulk_sql_and_unique_per_revision(self):
        lot = self.lot()
        event = LicenseLotAudit.objects.create(
            lot=lot,
            actor=self.actor,
            actor_label=self.actor.username,
            before_json={},
            after_json={"product_name": lot.product_name},
            resulting_revision=0,
        )
        with self.assertRaises(ModelValidationError):
            event.save()
        with self.assertRaises(ModelValidationError):
            event.delete()
        with self.assertRaises(DatabaseError), transaction.atomic():
            LicenseLotAudit.objects.filter(pk=event.pk).update(actor_label="Falso")
        with self.assertRaises(DatabaseError), transaction.atomic():
            LicenseLotAudit.objects.filter(pk=event.pk).delete()
        with self.assertRaises(DatabaseError), transaction.atomic():
            with transaction.get_connection().cursor() as cursor:
                cursor.execute(
                    "DELETE FROM inventory_licenselotaudit WHERE id = %s", [event.pk]
                )
        with self.assertRaises(IntegrityError), transaction.atomic():
            LicenseLotAudit.objects.create(
                lot=lot,
                actor=self.actor,
                actor_label="Duplicado",
                before_json={},
                after_json={},
                resulting_revision=0,
            )
        event.refresh_from_db()
        self.assertEqual(event.actor_label, self.actor.username)


class LicenseLotServiceTests(TestCase):
    def setUp(self):
        self.actor = manager()

    def test_create_edit_all_fields_and_preserve_author_snapshot(self):
        from inventory.services import create_license_lot, update_license_lot

        lot = create_license_lot(actor=self.actor, data=lot_data())
        self.assertEqual(lot.audits.count(), 1)
        other = manager("otro")
        changes = lot_data(
            product_name="Nuevo",
            vendor="Otro proveedor",
            license_model="DEVICE_SEAT",
            purchased_quantity=12,
            in_use_quantity=3,
            starts_on=date(2026, 2, 1),
            ends_on=date(2026, 12, 31),
        )
        updated = update_license_lot(
            actor=other, lot_id=lot.pk, data={**changes, "expected_revision": 0}
        )
        self.assertEqual(updated.revision, 1)
        event = updated.audits.first()
        self.assertEqual(event.before_json["in_use_quantity"], 4)
        for key, value in changes.items():
            expected = value.isoformat() if isinstance(value, date) else value
            self.assertEqual(event.after_json[key], expected)
        self.assertEqual(event.actor_id, other.pk)
        other.username = "renombrado"
        other.save()
        event.refresh_from_db()
        self.assertEqual(event.actor_label, "otro")
        self.assertEqual(event.after_json["revision"], 1)

    def test_strict_types_unknown_fields_and_service_permissions(self):
        from django.contrib.auth import get_user_model
        from rest_framework.exceptions import PermissionDenied, ValidationError
        from inventory.services import create_license_lot

        for changes in [
            {"purchased_quantity": True},
            {"in_use_quantity": 1.2},
            {"purchased_quantity": "10"},
            {"in_use_quantity": 2147483648},
            {"product_name": "   "},
            {"vendor": "x" * 161},
            {"remaining_quantity": 6},
            {"created_by": self.actor.pk},
        ]:
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                create_license_lot(actor=self.actor, data=lot_data(**changes))
        outsider = get_user_model().objects.create_user("visitante")
        with self.assertRaises(PermissionDenied):
            create_license_lot(actor=outsider, data=lot_data())
        self.assertEqual(SoftwareLicenseLot.objects.count(), 0)
        self.assertEqual(LicenseLotAudit.objects.count(), 0)

    def test_rejected_updates_leave_projection_and_history_unchanged(self):
        from rest_framework.exceptions import ValidationError
        from inventory.errors import Conflict
        from inventory.services import create_license_lot, update_license_lot

        lot = create_license_lot(actor=self.actor, data=lot_data())
        for change in [
            {"purchased_quantity": 3},
            {"in_use_quantity": 11},
            {"starts_on": "2027-01-01", "ends_on": "2026-01-01"},
            {"starts_on": None},
            {},
            {"vendor": lot.vendor},
        ]:
            with self.subTest(change=change), self.assertRaises(ValidationError):
                update_license_lot(
                    lot_id=lot.pk,
                    actor=self.actor,
                    data={"expected_revision": 0, **change},
                )
        with self.assertRaises(Conflict):
            update_license_lot(
                lot_id=lot.pk,
                actor=self.actor,
                data={"vendor": "Cambio", "expected_revision": 9},
            )
        lot.refresh_from_db()
        self.assertEqual(
            (lot.revision, lot.in_use_quantity, lot.purchased_quantity), (0, 4, 10)
        )
        self.assertEqual(lot.audits.count(), 1)

    def test_audit_failure_rolls_back_create_and_edit(self):
        from unittest.mock import patch
        from inventory.services import create_license_lot, update_license_lot

        with patch(
            "inventory.services._audit_license_lot", side_effect=RuntimeError("fallo")
        ):
            with self.assertRaises(RuntimeError):
                create_license_lot(actor=self.actor, data=lot_data())
        self.assertEqual(SoftwareLicenseLot.objects.count(), 0)
        lot = create_license_lot(actor=self.actor, data=lot_data())
        with patch(
            "inventory.services._audit_license_lot", side_effect=RuntimeError("fallo")
        ):
            with self.assertRaises(RuntimeError):
                update_license_lot(
                    actor=self.actor,
                    lot_id=lot.pk,
                    data={"vendor": "Cambio", "expected_revision": 0},
                )
        lot.refresh_from_db()
        self.assertEqual(
            (lot.vendor, lot.revision, lot.audits.count()),
            ("Proveedor de prueba", 0, 1),
        )

    def test_import_provider_is_atomic_and_checks_authorization(self):
        from django.contrib.auth import get_user_model
        from rest_framework.exceptions import PermissionDenied, ValidationError
        from inventory.license_services import import_license_lots

        with self.assertRaises(ValidationError):
            import_license_lots(
                actor=self.actor, rows=[lot_data(), lot_data(in_use_quantity=11)]
            )
        self.assertEqual(SoftwareLicenseLot.objects.count(), 0)
        outsider = get_user_model().objects.create_user("externo")
        with self.assertRaises(PermissionDenied):
            import_license_lots(actor=outsider, rows=[lot_data()])
        self.assertEqual(
            import_license_lots(actor=self.actor, rows=[lot_data(), lot_data()])[
                "created"
            ],
            2,
        )
        self.assertEqual(LicenseLotAudit.objects.count(), 2)


class LicenseLotApiTests(APITestCase):
    def setUp(self):
        self.actor = manager()
        self.client.force_authenticate(self.actor)

    def create(self, **changes):
        data = lot_data(**changes)
        data["starts_on"] = (
            data["starts_on"].isoformat()
            if isinstance(data["starts_on"], date)
            else data["starts_on"]
        )
        data["ends_on"] = (
            data["ends_on"].isoformat()
            if isinstance(data["ends_on"], date)
            else data["ends_on"]
        )
        return self.client.post("/api/license-lots/", data, format="json")

    def test_create_read_edit_and_history(self):
        response = self.create()
        self.assertEqual(response.status_code, 201, response.content)
        lot = response.json()
        self.assertEqual(lot["remaining_quantity"], 6)
        self.assertEqual(lot["created_by"]["id"], self.actor.pk)
        url = f"/api/license-lots/{lot['id']}/"
        self.assertEqual(self.client.get(url).json(), lot)
        edited = self.client.patch(
            url, {"expected_revision": 0, "in_use_quantity": 3}, format="json"
        )
        self.assertEqual(edited.status_code, 200, edited.content)
        self.assertEqual(
            (edited.json()["remaining_quantity"], edited.json()["revision"]), (7, 1)
        )
        history = self.client.get(url + "history/").json()
        self.assertEqual(history["count"], 2)
        event = history["results"][0]
        self.assertEqual(event["before_json"]["in_use_quantity"], 4)
        self.assertEqual(event["after_json"]["in_use_quantity"], 3)
        self.assertEqual(event["actor"]["recorded_label"], self.actor.username)
        self.assertTrue(event["timestamp"])

    def test_invalid_input_rejected_without_rows_or_audits(self):
        cases = [
            {"purchased_quantity": -1},
            {"in_use_quantity": -1},
            {"in_use_quantity": 11},
            {"purchased_quantity": 0},
            {"purchased_quantity": True},
            {"in_use_quantity": 1.0},
            {"in_use_quantity": "4"},
            {"in_use_quantity": 2147483648},
            {"in_use_quantity": [4]},
            {"in_use_quantity": {"value": 4}},
            {"starts_on": ""},
            {"starts_on": None},
            {"starts_on": "2026-02-30"},
            {"ends_on": "2025-01-01"},
            {"license_model": "UNLIMITED"},
            {"product_name": ""},
            {"vendor": " "},
            {"product_name": "x" * 161},
        ]
        for changes in cases:
            with self.subTest(changes=changes):
                response = self.create(**changes)
                self.assertEqual(response.status_code, 400, response.content)
                self.assertIn("code", response.json())
                self.assertIn("fields", response.json())
        for data in [[], "texto", 10, None, {}, {"vendor": "Proveedor"}]:
            response = self.client.post("/api/license-lots/", data, format="json")
            self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(SoftwareLicenseLot.objects.count(), 0)
        self.assertEqual(LicenseLotAudit.objects.count(), 0)

    def test_zero_quantities_and_optional_end_date(self):
        response = self.create(purchased_quantity=0, in_use_quantity=0)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["remaining_quantity"], 0)
        body = {**lot_data(), "starts_on": "2026-01-01"}
        del body["ends_on"]
        response = self.client.post("/api/license-lots/", body, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        self.assertIsNone(response.json()["ends_on"])

    def test_reserved_fields_are_rejected_on_create_and_patch(self):
        lot = self.create().json()
        reserved = {
            "id": 999,
            "created_by": self.actor.pk,
            "created_at": "2026-01-01",
            "actor": self.actor.pk,
            "timestamp": "2026-01-01",
            "revision": 9,
            "remaining_quantity": 100,
            "temporal_status": "CURRENT",
            "before_json": {},
            "after_json": {},
            "activation_key": "inventada",
            "asset_id": 1,
            "custodian": 1,
            "invoice_id": 1,
            "__proto__": {},
        }
        url = f"/api/license-lots/{lot['id']}/"
        for field, value in reserved.items():
            with self.subTest(field=field):
                self.assertEqual(self.create(**{field: value}).status_code, 400)
                response = self.client.patch(
                    url, {"expected_revision": 0, field: value}, format="json"
                )
                self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(LicenseLotAudit.objects.count(), 1)
        self.assertEqual(SoftwareLicenseLot.objects.get().revision, 0)
        self.assertTrue(
            set(lot).isdisjoint(
                {"activation_key", "asset_id", "custodian", "invoice_id"}
            )
        )

    def test_all_routes_require_active_manager_even_for_superuser(self):
        lot = self.create().json()
        routes = [
            "/api/license-lots/",
            f"/api/license-lots/{lot['id']}/",
            f"/api/license-lots/{lot['id']}/history/",
        ]
        outsider = get_user_model().objects.create_user("externo")
        admin = get_user_model().objects.create_superuser(
            "administrador", "admin@example.org", "test-password"
        )
        inactive = manager("inactivo")
        inactive.is_active = False
        inactive.save()
        operator = get_user_model().objects.create_user("operador")
        operator.groups.add(Group.objects.get_or_create(name="Operadores")[0])
        reviewer = get_user_model().objects.create_user("revisor")
        reviewer.groups.add(Group.objects.get_or_create(name="Revisores")[0])
        for actor in [None, outsider, admin, inactive, operator, reviewer]:
            self.client.force_authenticate(actor)
            for route in routes:
                self.assertEqual(self.client.get(route).status_code, 403)
            self.assertEqual(
                self.client.post(routes[0], {}, format="json").status_code, 403
            )
            self.assertEqual(
                self.client.patch(routes[1], {}, format="json").status_code, 403
            )
        self.assertEqual(LicenseLotAudit.objects.count(), 1)

    def test_other_managers_have_equal_access(self):
        lot = self.create().json()
        self.client.force_authenticate(manager("segundo"))
        url = f"/api/license-lots/{lot['id']}/"
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get(url + "history/").status_code, 200)
        self.assertEqual(
            self.client.patch(
                url, {"expected_revision": 0, "vendor": "Otro"}, format="json"
            ).status_code,
            200,
        )

    def test_real_session_requires_csrf_and_rejects_foreign_origin(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.actor)
        lot = self.create().json()
        url = f"/api/license-lots/{lot['id']}/"
        data = {"expected_revision": 0, "in_use_quantity": 3}
        self.assertEqual(client.patch(url, data, format="json").status_code, 403)
        self.assertEqual(
            client.post("/api/license-lots/", {}, format="json").status_code, 403
        )
        token = client.get("/api/auth/csrf/").json()["csrfToken"]
        response = client.patch(
            url,
            data,
            format="json",
            HTTP_X_CSRFTOKEN=token,
            HTTP_ORIGIN="https://evil.example",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "csrf_failed")
        response = client.patch(url, data, format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(LicenseLotAudit.objects.count(), 2)
        client.logout()
        self.assertEqual(client.get(url).status_code, 403)

    def test_stale_missing_or_invalid_revision_and_merged_constraints(self):
        lot = self.create(ends_on=date(2026, 12, 31)).json()
        url = f"/api/license-lots/{lot['id']}/"
        for data in [
            {"vendor": "Otro"},
            {"vendor": "Otro", "expected_revision": True},
            {"vendor": "Otro", "expected_revision": -1},
            {"expected_revision": 0},
            {"expected_revision": 0, "purchased_quantity": 3},
            {"expected_revision": 0, "starts_on": "2027-01-01"},
            {"expected_revision": 0, "ends_on": "2025-12-31"},
        ]:
            response = self.client.patch(url, data, format="json")
            self.assertEqual(response.status_code, 400, response.content)
        response = self.client.patch(
            url, {"expected_revision": 1, "vendor": "Otro"}, format="json"
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "stale_revision")
        self.assertEqual(LicenseLotAudit.objects.count(), 1)
        response = self.client.patch(
            url, {"expected_revision": 0, "ends_on": None}, format="json"
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertIsNone(response.json()["ends_on"])

    def test_dates_filters_and_output_use_same_local_day(self):
        moment = datetime(2026, 11, 5, 2, tzinfo=datetime_timezone.utc)
        self.create(starts_on=date(2026, 11, 4), ends_on=date(2026, 11, 4))
        with patch("django.utils.timezone.now", return_value=moment):
            with timezone.override(ZoneInfo("America/Guayaquil")):
                page = self.client.get(
                    "/api/license-lots/?temporal_status=CURRENT"
                ).json()
                self.assertEqual(page["count"], 1)
                self.assertEqual(page["results"][0]["temporal_status"], "CURRENT")
            with timezone.override(ZoneInfo("UTC")):
                page = self.client.get(
                    "/api/license-lots/?temporal_status=EXPIRED"
                ).json()
                self.assertEqual(page["count"], 1)
                self.assertEqual(page["results"][0]["remaining_quantity"], 6)

    def test_search_combined_filters_injection_and_query_validation(self):
        today = timezone.localdate()
        self.create(
            product_name="Editor Ágil",
            vendor="Proveedor Ágil",
            license_model="DEVICE_SEAT",
            starts_on=today,
        )
        self.create(product_name="Suite futura", starts_on=today + timedelta(days=1))
        self.create(product_name="Suite pasada", ends_on=today - timedelta(days=1))
        for query in [
            "search=editor",
            "search=ágil&license_model=DEVICE_SEAT&temporal_status=CURRENT",
            "temporal_status=NOT_STARTED",
            "temporal_status=EXPIRED",
        ]:
            response = self.client.get("/api/license-lots/?" + query)
            self.assertEqual(response.status_code, 200, response.content)
            self.assertEqual(response.json()["count"], 1)
        for query in [
            "page=0",
            "page=abc",
            "page=999999999999999999999",
            "other=x",
            "license_model=ALL",
            "temporal_status=VIGENTE",
        ]:
            self.assertEqual(
                self.client.get("/api/license-lots/?" + query).status_code, 400
            )
        response = self.client.get(
            "/api/license-lots/",
            {"search": "' OR 1=1; DROP TABLE inventory_softwarelicenselot; --"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 0)
        self.assertEqual(SoftwareLicenseLot.objects.count(), 3)

    def test_pagination_history_and_read_methods_do_not_write(self):
        for n in range(51):
            create_license_lot(
                actor=self.actor, data=lot_data(product_name=f"Producto {n}")
            )
        page = self.client.get("/api/license-lots/").json()
        self.assertEqual((page["count"], len(page["results"])), (51, 50))
        self.assertTrue(page["next"].endswith("page=2"))
        second = self.client.get("/api/license-lots/?page=2").json()
        self.assertEqual(len(second["results"]), 1)
        self.assertIsNone(second["next"])
        self.assertEqual(self.client.get("/api/license-lots/?page=3").status_code, 400)
        lot_id = page["results"][0]["id"]
        for revision in range(50):
            update_license_lot(
                actor=self.actor,
                lot_id=lot_id,
                data={"expected_revision": revision, "in_use_quantity": revision % 10},
            )
        history_url = f"/api/license-lots/{lot_id}/history/"
        history = self.client.get(history_url).json()
        self.assertEqual((history["count"], len(history["results"])), (51, 50))
        self.assertEqual(
            self.client.get(history_url + "?page=2").json()["results"][0][
                "resulting_revision"
            ],
            0,
        )
        self.assertEqual(self.client.get(history_url + "?page=3").status_code, 400)
        self.assertEqual(self.client.get(history_url + "?other=x").status_code, 400)
        self.assertEqual(LicenseLotAudit.objects.count(), 101)

    def test_missing_ids_unsupported_verbs_and_malformed_json(self):
        for route in ["/api/license-lots/999999/", "/api/license-lots/999999/history/"]:
            self.assertEqual(self.client.get(route).status_code, 404)
        lot = self.create().json()
        url = f"/api/license-lots/{lot['id']}/"
        for method in [self.client.delete, self.client.put, self.client.post]:
            self.assertEqual(method(url, {}, format="json").status_code, 405)
        self.assertEqual(
            self.client.patch(url + "history/", {}, format="json").status_code, 405
        )
        response = self.client.post(
            "/api/license-lots/", "{broken", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(LicenseLotAudit.objects.count(), 1)


class LicenseLotConcurrencyTests(TransactionTestCase):
    def test_two_editors_only_one_commits_and_no_partial_audit(self):
        actor = manager()
        lot = create_license_lot(actor=actor, data=lot_data())
        barrier = Barrier(2)

        def edit(value):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                updated = update_license_lot(
                    actor=actor,
                    lot_id=lot.pk,
                    data={"expected_revision": 0, "in_use_quantity": value},
                )
                return 200, updated.in_use_quantity
            except APIException as exc:
                return exc.status_code, None
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(edit, [2, 3]))
        self.assertEqual(sorted(code for code, _ in results), [200, 409])
        lot.refresh_from_db()
        self.assertEqual(lot.revision, 1)
        self.assertEqual(
            lot.in_use_quantity, next(value for code, value in results if code == 200)
        )
        self.assertEqual(lot.audits.count(), 2)
        self.assertEqual(
            lot.audits.first().after_json["in_use_quantity"], lot.in_use_quantity
        )


@override_settings(IMPORT_GATEWAY="inventory.imports.gateways.DjangoProviderGateway")
class LicenseLotRealImportTests(APITestCase):
    def test_real_csv_provider_double_confirmation_and_idempotency(self):
        from inventory.imports import schemas
        from inventory.models import ImportBatch
        from .test_imports import csv_file, license_row

        actor = manager()
        self.client.force_authenticate(actor)
        preview = self.client.post(
            "/api/imports/previews/",
            {
                "kind": "license_lots",
                "schema_version": "license-lots-v1",
                "file": csv_file(
                    schemas.LICENSE_LOTS,
                    [license_row(), license_row(product_name="Otro")],
                ),
            },
            format="multipart",
        )
        self.assertEqual(preview.status_code, 201, preview.content)
        batch = preview.json()
        self.assertEqual(SoftwareLicenseLot.objects.count(), 0)
        url = f"/api/imports/{batch['batch_id']}/"
        body = {"content_hash": batch["content_hash"]}
        self.assertEqual(
            self.client.post(url + "confirm/", body, format="json").status_code, 200
        )
        applied = self.client.post(url + "apply/", body, format="json")
        self.assertEqual(applied.status_code, 201, applied.content)
        self.assertEqual(SoftwareLicenseLot.objects.count(), 2)
        self.assertEqual(LicenseLotAudit.objects.count(), 2)
        self.assertEqual(
            self.client.post(url + "apply/", body, format="json").status_code, 200
        )
        self.assertEqual(SoftwareLicenseLot.objects.count(), 2)
        self.assertEqual(ImportBatch.objects.get().state, "APPLIED")


class LicenseLotSecurityReviewTests(APITestCase):
    def setUp(self):
        self.actor = manager()
        self.client.force_authenticate(self.actor)

    def test_bounded_json_body_and_no_cache_for_private_responses(self):
        oversized = '{"product_name":"' + "x" * 16384 + '"}'
        response = self.client.post(
            "/api/license-lots/", oversized, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("16 KiB", response.json()["detail"])
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(SoftwareLicenseLot.objects.count(), 0)
        response = self.client.get("/api/license-lots/")
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(
            self.client.post(
                "/api/license-lots/", {"product_name": "texto"}
            ).status_code,
            415,
        )

    @override_settings(
        IMPORT_GATEWAY="inventory.imports.gateways.DjangoProviderGateway"
    )
    def test_real_import_preview_uses_provider_limits_before_confirmation(self):
        from inventory.imports import schemas
        from .test_imports import csv_file, license_row

        response = self.client.post(
            "/api/imports/previews/",
            {
                "kind": "license_lots",
                "schema_version": "license-lots-v1",
                "file": csv_file(
                    schemas.LICENSE_LOTS,
                    [license_row(), license_row(purchased_quantity="2147483648")],
                ),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 400, response.content)
        self.assertTrue(
            any(
                error["field"] == "purchased_quantity"
                for error in response.json()["errors"]
            )
        )
        self.assertEqual(SoftwareLicenseLot.objects.count(), 0)
        self.assertEqual(LicenseLotAudit.objects.count(), 0)


class LicenseLotCharsetTests(APITestCase):
    def test_non_text_or_non_utf8_codecs_are_rejected_without_decoding(self):
        self.client.force_authenticate(manager())
        for charset in ["bz2_codec", "zlib_codec", "base64_codec", "utf-16", "latin1"]:
            with self.subTest(charset=charset):
                response = self.client.post(
                    "/api/license-lots/",
                    b"{}",
                    content_type=f"application/json; charset={charset}",
                )
                self.assertEqual(response.status_code, 400, response.content)
                self.assertIn("UTF-8", response.json()["detail"])
        self.assertEqual(SoftwareLicenseLot.objects.count(), 0)


@override_settings(IMPORT_GATEWAY="inventory.imports.gateways.DjangoProviderGateway")
class LicenseLotAtomicImportReviewTests(APITestCase):
    def test_second_row_failure_rolls_back_real_provider_and_batch_can_retry(self):
        from inventory import services as lot_services
        from inventory.imports import schemas
        from inventory.models import ImportBatch
        from .test_imports import csv_file, license_row

        self.client.force_authenticate(manager())
        batch = self.client.post(
            "/api/imports/previews/",
            {
                "kind": "license_lots",
                "schema_version": "license-lots-v1",
                "file": csv_file(
                    schemas.LICENSE_LOTS,
                    [license_row(), license_row(product_name="Segundo")],
                ),
            },
            format="multipart",
        ).json()
        url = f"/api/imports/{batch['batch_id']}/"
        body = {"content_hash": batch["content_hash"]}
        self.assertEqual(
            self.client.post(url + "confirm/", body, format="json").status_code, 200
        )
        original = lot_services._audit_license_lot
        calls = 0

        def fail_second(lot, actor, before):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("Fallo simulado al auditar segunda fila")
            return original(lot, actor, before)

        with patch("inventory.services._audit_license_lot", side_effect=fail_second):
            with self.assertRaises(RuntimeError):
                self.client.post(url + "apply/", body, format="json")
        self.assertEqual(SoftwareLicenseLot.objects.count(), 0)
        self.assertEqual(LicenseLotAudit.objects.count(), 0)
        self.assertEqual(ImportBatch.objects.get().state, "CONFIRMED_ONCE")
        response = self.client.post(url + "apply/", body, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(
            (SoftwareLicenseLot.objects.count(), LicenseLotAudit.objects.count()),
            (2, 2),
        )


class LicenseLotMalformedJsonReviewTests(APITestCase):
    def test_deep_json_and_invalid_unicode_do_not_raise_server_errors(self):
        self.client.force_authenticate(manager())
        bodies = [
            '{"vendor":' + "[" * 1100 + "0" + "]" * 1100 + "}",
            b'{"vendor":"\xff"}',
            b'{"\\ud800":"valor"}',
            b'{"product_name":"\\ud800"}',
        ]
        for body in bodies:
            with self.subTest(case=str(body)[:35]):
                response = self.client.post(
                    "/api/license-lots/", body, content_type="application/json"
                )
                self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(SoftwareLicenseLot.objects.count(), 0)
        self.assertEqual(LicenseLotAudit.objects.count(), 0)
