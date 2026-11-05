from django.contrib.auth.models import Group

from inventory.models import Asset, Faculty, ReviewerProfile, RetirementAudit

from .base import InventoryCase, manager


class RetirementIntegrationTests(InventoryCase):
    def setUp(self):
        super().setUp()
        self.asset = self.new_asset()
        self.path = f"/api/assets/{self.asset['id']}/"
        self.reviewer = manager("reviewer")
        self.reviewer.groups.set([Group.objects.create(name="Revisores")])
        ReviewerProfile.objects.create(
            user=self.reviewer, faculty=Faculty.objects.create(name="Facultad revisora"),
            must_change_password=False,
        )

    def request_retirement(self):
        incident = self.operation(self.asset, "incidents", {"type": "lost", "description": "No está en el aula"})
        self.assertEqual(incident.status_code, 201, incident.content)
        response = self.client.post(self.path + "retirement-requests/", {
            "expected_revision": 1, "reason": "Pérdida confirmada", "reviewer_id": self.reviewer.pk,
        }, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()

    def test_pending_request_blocks_faculty_change_and_cancels_on_recovery(self):
        request = self.request_retirement()
        operator = manager("operator")
        operator.groups.set([Group.objects.create(name="Operadores")])
        self.client.force_authenticate(operator)
        response = self.client.patch(f"/api/operator/assets/{self.asset['id']}/faculty/", {
            "expected_revision": 2, "reason": "Traslado", "faculty_id": self.reviewer.reviewer_profile.faculty_id,
        }, format="json")
        self.assertEqual(response.status_code, 409, response.content)
        self.client.force_authenticate(self.actor)
        response = self.client.post(self.path + "recover/", {
            "expected_revision": 2, "inspection_confirmed": True,
            "inspected_condition": "operativo", "recovered_location": "Recepción",
        }, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        audit = RetirementAudit.objects.get(request_id=request["id"], event_type="retirement_cancelled")
        self.assertEqual(audit.recovery_event.asset_id, self.asset["id"])
        asset = Asset.objects.get(pk=self.asset["id"])
        self.assertEqual((asset.lifecycle_status, asset.assignment, asset.revision), ("localizado", "disponible", 4))
        self.assertEqual(audit.request.status, "cancelled")

    def test_reviewer_approves_and_retirement_can_be_rectified(self):
        request = self.request_retirement()
        self.client.force_authenticate(self.reviewer)
        session = self.client.get("/api/auth/me/")
        self.assertEqual(session.json()["permissions"], ["retirement.review"])
        response = self.client.post(f"/api/retirement-requests/{request['id']}/decision/", {
            "expected_revision": 2, "decision": "approve",
        }, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        self.client.force_authenticate(self.actor)
        asset = self.client.get(self.path).json()
        self.assertEqual(asset["lifecycle_status"], "baja")
        history = self.client.get(self.path + "history/").json()
        response = self.operation(asset, "rectify", {
            "movement_id": history[0]["event_id"], "reason": "Se detectó un error",
        })
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(self.client.get(self.path).json()["lifecycle_status"], "no_localizado")

    def test_active_maintenance_blocks_normal_retirement(self):
        maintenance = self.operation(self.asset, "maintenance", {
            "description": "Revisión", "workshop_location": "Taller",
        })
        self.assertEqual(maintenance.status_code, 201, maintenance.content)
        blocked = self.client.post(self.path + "retire/", {
            "expected_revision": 1, "reason": "Fin de vida útil",
        }, format="json")
        self.assertEqual(blocked.status_code, 409, blocked.content)
        self.assertFalse(RetirementAudit.objects.filter(asset_id=self.asset["id"]).exists())

    def test_normal_retirement_preserves_acquisition(self):
        retired = self.operation(self.asset, "retire", {"reason": "Fin de vida útil"})
        self.assertEqual(retired.status_code, 201, retired.content)
        asset = self.client.get(self.path).json()
        self.assertEqual(asset["lifecycle_status"], "baja")
        self.assertEqual(asset["acquisition"], self.asset["acquisition"])
        self.assertEqual(asset["rectifiable_movement_id"], retired.json()["movement_id"])
