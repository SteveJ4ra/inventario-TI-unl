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
        return SoftwareLicenseLot.objects.create(created_by=self.actor, **lot_data(**changes))

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
            {"purchased_quantity": -1}, {"in_use_quantity": -1},
            {"in_use_quantity": 11}, {"starts_on": None},
            {"ends_on": date(2025, 12, 31)}, {"license_model": "UNLIMITED"},
        ]:
            with self.subTest(changes=changes):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    self.lot(**changes)
        self.assertEqual(SoftwareLicenseLot.objects.count(), 0)

    def test_audit_is_immutable_in_orm_bulk_sql_and_unique_per_revision(self):
        lot = self.lot()
        event = LicenseLotAudit.objects.create(
            lot=lot, actor=self.actor, actor_label=self.actor.username,
            before_json={}, after_json={"product_name": lot.product_name},
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
                cursor.execute("DELETE FROM inventory_licenselotaudit WHERE id = %s", [event.pk])
        with self.assertRaises(IntegrityError), transaction.atomic():
            LicenseLotAudit.objects.create(
                lot=lot, actor=self.actor, actor_label="Duplicado",
                before_json={}, after_json={}, resulting_revision=0,
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
            product_name="Nuevo", vendor="Otro proveedor", license_model="DEVICE_SEAT",
            purchased_quantity=12, in_use_quantity=3,
            starts_on=date(2026, 2, 1), ends_on=date(2026, 12, 31),
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
            {"purchased_quantity": True}, {"in_use_quantity": 1.2},
            {"purchased_quantity": "10"}, {"in_use_quantity": 2147483648},
            {"product_name": "   "}, {"vendor": "x" * 161},
            {"remaining_quantity": 6}, {"created_by": self.actor.pk},
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
            {"purchased_quantity": 3}, {"in_use_quantity": 11},
            {"starts_on": "2027-01-01", "ends_on": "2026-01-01"},
            {"starts_on": None}, {}, {"vendor": lot.vendor},
        ]:
            with self.subTest(change=change), self.assertRaises(ValidationError):
                update_license_lot(
                    lot_id=lot.pk, actor=self.actor, data={"expected_revision": 0, **change}
                )
        with self.assertRaises(Conflict):
            update_license_lot(
                lot_id=lot.pk, actor=self.actor, data={"vendor": "Cambio", "expected_revision": 9}
            )
        lot.refresh_from_db()
        self.assertEqual((lot.revision, lot.in_use_quantity, lot.purchased_quantity), (0, 4, 10))
        self.assertEqual(lot.audits.count(), 1)

    def test_audit_failure_rolls_back_create_and_edit(self):
        from unittest.mock import patch
        from inventory.services import create_license_lot, update_license_lot

        with patch("inventory.services._audit_license_lot", side_effect=RuntimeError("fallo")):
            with self.assertRaises(RuntimeError):
                create_license_lot(actor=self.actor, data=lot_data())
        self.assertEqual(SoftwareLicenseLot.objects.count(), 0)
        lot = create_license_lot(actor=self.actor, data=lot_data())
        with patch("inventory.services._audit_license_lot", side_effect=RuntimeError("fallo")):
            with self.assertRaises(RuntimeError):
                update_license_lot(
                    actor=self.actor, lot_id=lot.pk,
                    data={"vendor": "Cambio", "expected_revision": 0},
                )
        lot.refresh_from_db()
        self.assertEqual((lot.vendor, lot.revision, lot.audits.count()), ("Proveedor de prueba", 0, 1))

    def test_import_provider_is_atomic_and_checks_authorization(self):
        from django.contrib.auth import get_user_model
        from rest_framework.exceptions import PermissionDenied, ValidationError
        from inventory.license_services import import_license_lots

        with self.assertRaises(ValidationError):
            import_license_lots(actor=self.actor, rows=[lot_data(), lot_data(in_use_quantity=11)])
        self.assertEqual(SoftwareLicenseLot.objects.count(), 0)
        outsider = get_user_model().objects.create_user("externo")
        with self.assertRaises(PermissionDenied):
            import_license_lots(actor=outsider, rows=[lot_data()])
        self.assertEqual(import_license_lots(actor=self.actor, rows=[lot_data(), lot_data()])["created"], 2)
        self.assertEqual(LicenseLotAudit.objects.count(), 2)
