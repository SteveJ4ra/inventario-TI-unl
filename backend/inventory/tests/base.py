from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase


def manager(name="gestor"):
    user = get_user_model().objects.create_user(name)
    group, _ = Group.objects.get_or_create(name="Gestores")
    user.groups.add(group)
    return user


def asset_data(**changes):
    return (
        dict(
            name="Portátil",
            description="Equipo de práctica",
            category="portatil",
            brand="Ejemplo",
            model="A1",
            serial_number="LAB-001",
            location="Laboratorio",
            condition="operativo",
            **changes,
        )
        if not changes
        else {**asset_data(), **changes}
    )


class InventoryCase(APITestCase):
    def setUp(self):
        self.actor = manager()
        self.client.force_authenticate(self.actor)

    def new_asset(self, **changes):
        response = self.client.post(
            "/api/assets/", asset_data(**changes), format="json"
        )
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()

    def person(self, **changes):
        data = {
            "full_name": "Docente de prueba",
            "email": "docente@example.org",
            **changes,
        }
        response = self.client.post("/api/custodians/", data, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()

    def operation(self, asset, route, data):
        return self.client.post(
            f"/api/assets/{asset['id']}/{route}/",
            {"expected_revision": asset["revision"], **data},
            format="json",
        )

    def deliver(self, asset, person):
        response = self.operation(
            asset, "deliver", {"custodian_id": person["id"], "destination": "Aula"}
        )
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()
