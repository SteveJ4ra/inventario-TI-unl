from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.db import close_old_connections
from django.test import TransactionTestCase
from rest_framework.exceptions import APIException
from inventory.models import Asset, Movement
from inventory.services import create_asset, create_custodian, record_operation
from .base import asset_data, manager


class ConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.actor = manager()
        self.person = create_custodian(
            actor=self.actor, data={"full_name": "Test", "email": "test@example.org"}
        )

    def race(self, operations):
        barrier = Barrier(len(operations))

        def worker(operation):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return ("ok", operation())
            except APIException as exc:
                return ("error", exc.status_code)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=len(operations)) as pool:
            return list(pool.map(worker, operations))

    def test_duplicate_registration_and_unique_codes(self):
        results = self.race(
            [
                lambda: create_asset(actor=self.actor, data=asset_data())
                for _ in range(2)
            ]
        )
        self.assertEqual([x[0] for x in results].count("ok"), 1)
        self.assertEqual(Asset.objects.count(), 1)
        results = self.race(
            [
                lambda n=n: create_asset(
                    actor=self.actor, data=asset_data(serial_number=str(n))
                )
                for n in range(4)
            ]
        )
        self.assertTrue(all(r[0] == "ok" for r in results))
        self.assertEqual(len(set(Asset.objects.values_list("code", flat=True))), 5)

    def test_double_delivery_return_and_rectification(self):
        asset = create_asset(actor=self.actor, data=asset_data())

        def action(kind, data):
            return lambda: record_operation(
                asset_id=asset.pk, actor=self.actor, operation=kind, data=data
            )

        deliver = action(
            Movement.Type.DELIVERY,
            {
                "expected_revision": 0,
                "custodian_id": self.person.pk,
                "destination": "Aula",
            },
        )
        result = self.race([deliver, deliver])
        self.assertEqual(sum(r[0] == "ok" for r in result), 1)
        back = action(
            Movement.Type.RETURN,
            {
                "expected_revision": 1,
                "condition": "averiado",
                "reception_location": "Bodega",
            },
        )
        result = self.race([back, back])
        self.assertEqual(sum(r[0] == "ok" for r in result), 1)
        target = Movement.objects.order_by("-id").first()
        rectify = action(
            Movement.Type.RECTIFICATION,
            {"expected_revision": 2, "movement_id": target.pk, "reason": "Error"},
        )
        result = self.race([rectify, rectify])
        self.assertEqual(sum(r[0] == "ok" for r in result), 1)
        self.assertEqual(Movement.objects.count(), 3)
        asset.refresh_from_db()
        self.assertEqual(
            (asset.revision, asset.assignment, asset.location), (3, "asignado", "Aula")
        )
