from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.db import close_old_connections
from django.test import TransactionTestCase
from rest_framework.exceptions import APIException
from inventory.models import Asset, AssetTransition, Incident, Movement
from inventory.services import (
    create_asset,
    create_custodian,
    record_event_transition,
    record_operation,
    report_incident,
    recover_asset,
    resolve_incident,
    start_maintenance,
)
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

    def test_incident_and_movement_share_asset_revision_lock(self):
        asset = create_asset(actor=self.actor, data=asset_data())

        def prepare(locked, incident):
            incident.type = Incident.Type.OBSERVATION
            incident.description = "Observación ficticia"
            incident.reported_by = self.actor

        def add_incident():
            return record_event_transition(
                asset_id=asset.pk, actor=self.actor, expected_revision=0,
                event_model=Incident, apply=prepare,
            )

        def deliver():
            return record_operation(
                asset_id=asset.pk, actor=self.actor, operation=Movement.Type.DELIVERY,
                data={
                    "expected_revision": 0, "custodian_id": self.person.pk,
                    "destination": "Aula",
                },
            )

        results = self.race([add_incident, deliver])
        self.assertEqual([result[0] for result in results].count("ok"), 1)
        self.assertIn(("error", 409), results)
        asset.refresh_from_db()
        self.assertEqual(asset.revision, 1)
        self.assertEqual(Incident.objects.count(), AssetTransition.objects.count())
        self.assertEqual(Movement.objects.count() + AssetTransition.objects.count(), 1)

    def test_two_resolutions_with_same_revision_keep_one_note_and_one_audit(self):
        asset = create_asset(actor=self.actor, data=asset_data())
        incident = report_incident(
            asset_id=asset.pk, actor=self.actor,
            data={"expected_revision": 0, "type": "damage", "description": "Bisagra"},
        )

        def resolve(note):
            return resolve_incident(
                incident_id=incident.pk, actor=self.actor,
                data={"expected_revision": 1, "resolution_note": note},
            )

        results = self.race([lambda: resolve("Nota A"), lambda: resolve("Nota B")])
        self.assertEqual([result[0] for result in results].count("ok"), 1)
        self.assertIn(("error", 409), results)
        asset.refresh_from_db()
        incident.refresh_from_db()
        self.assertEqual(asset.revision, 2)
        self.assertEqual(incident.status, "resolved")
        self.assertEqual(AssetTransition.objects.filter(asset=asset).count(), 2)
        closure = AssetTransition.objects.get(asset=asset, resulting_revision=2)
        self.assertEqual(closure.after["event"]["resolution_note"], incident.resolution_note)

    def test_maintenance_and_delivery_cannot_both_win(self):
        asset = create_asset(actor=self.actor, data=asset_data())

        def start():
            return start_maintenance(
                asset_id=asset.pk, actor=self.actor,
                data={
                    "expected_revision": 0, "description": "Revisión",
                    "workshop_location": "Taller",
                },
            )

        def deliver():
            return record_operation(
                asset_id=asset.pk, actor=self.actor, operation=Movement.Type.DELIVERY,
                data={
                    "expected_revision": 0, "custodian_id": self.person.pk,
                    "destination": "Aula",
                },
            )

        results = self.race([start, deliver])
        self.assertEqual([result[0] for result in results].count("ok"), 1)
        self.assertIn(("error", 409), results)
        asset.refresh_from_db()
        self.assertEqual(asset.revision, 1)
        self.assertEqual(asset.maintenance_events.count(), AssetTransition.objects.count())
        self.assertEqual(Movement.objects.count() + AssetTransition.objects.count(), 1)
        if asset.maintenance_events.exists():
            self.assertEqual((asset.location, asset.current_custodian_id), ("Taller", None))
        else:
            self.assertEqual(asset.current_custodian_id, self.person.pk)

    def test_simultaneous_recovery_records_only_one_event(self):
        asset = create_asset(actor=self.actor, data=asset_data())
        incident = report_incident(
            asset_id=asset.pk, actor=self.actor,
            data={"expected_revision": 0, "type": "lost", "description": "Extraviado"},
        )

        def recover(location):
            return recover_asset(
                asset_id=asset.pk, actor=self.actor,
                data={
                    "expected_revision": 1, "inspection_confirmed": True,
                    "inspected_condition": "operativo", "recovered_location": location,
                },
            )

        results = self.race([lambda: recover("Aula"), lambda: recover("Bodega")])
        self.assertEqual([result[0] for result in results].count("ok"), 1)
        self.assertIn(("error", 409), results)
        asset.refresh_from_db()
        incident.refresh_from_db()
        self.assertEqual((asset.revision, incident.status), (2, "recovered"))
        self.assertEqual(asset.recoveries.count(), 1)
        self.assertEqual(asset.location, asset.recoveries.get().recovered_location)
        self.assertEqual(AssetTransition.objects.filter(asset=asset).count(), 2)
