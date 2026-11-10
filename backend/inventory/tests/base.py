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

    def api_asset_data(self, **changes):
        """Alta API 003 completa; conserva asset_data para probar servicios/legado 002."""
        if not hasattr(self, "_registration_data"):
            from datetime import date
            from inventory.models import Faculty, AcquisitionDocument
            faculty = Faculty.objects.create(name="Facultad ficticia de regresión")
            document = AcquisitionDocument.objects.create(source="PURCHASE", reference="TEST-REGRESSION",
                document_date=date(2026, 1, 15), supplier="Proveedor ficticio", invoice_total="1000.00",
                created_by=self.actor)
            self._registration_data = dict(faculty_id=faculty.pk, acquisition_document_id=document.pk,
                                           item_value="300.00", acquired_on="2026-01-15")
        return asset_data(**{**self._registration_data, **changes})

    def new_asset(self, **changes):
        response = self.client.post(
            "/api/assets/", self.api_asset_data(**changes), format="json"
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


class AcquisitionFixtures:
    """Fixtures completas 003; no cambia el alta histórica utilizada por tests 002."""

    def require_acquisition_schema(self):
        from django.db import connection
        from inventory.models import Faculty, AcquisitionDocument, AcquisitionLine

        required = {m._meta.db_table for m in [Faculty, AcquisitionDocument, AcquisitionLine]}
        missing = required - set(connection.introspection.table_names())
        if missing:
            self.fail("BLOQUEO_ESQUEMA_T004: faltan " + ", ".join(sorted(missing)))

    def acquisition_asset(self, actor):
        from datetime import date
        from decimal import Decimal
        from inventory.models import Asset, Faculty, AcquisitionDocument, AcquisitionLine

        self.require_acquisition_schema()
        if not any(field.name == "faculty" for field in Asset._meta.fields):
            self.fail("BLOQUEO_MODELO_T003_T004: falta Asset.faculty")
        faculty = Faculty.objects.create(name="Facultad ficticia de pruebas")
        document = AcquisitionDocument.objects.create(
            source="PURCHASE", reference="TEST-FIXTURE", document_date=date(2026, 1, 15),
            supplier="Proveedor ficticio", invoice_total=Decimal("1000.00"), created_by=actor)
        asset = Asset.objects.create(
            code="TI-TEST-FIXTURE", created_by=actor, faculty=faculty, **asset_data())
        AcquisitionLine.objects.create(document=document, asset=asset, item_value=Decimal("300.00"),
                                       acquired_on=date(2026, 1, 15))
        return asset, faculty, document
