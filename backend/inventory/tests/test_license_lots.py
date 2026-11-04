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
