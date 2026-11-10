"""Frontera 003/008: introspección simulada; nunca simula un alta de dominio."""
from types import SimpleNamespace
from unittest.mock import patch

from django.db import connection, OperationalError, ProgrammingError
from django.test import SimpleTestCase
from inventory.imports.gateways import DjangoProviderGateway, ProviderUnavailable
from inventory.models import Asset, Faculty, AcquisitionDocument, AcquisitionLine


class AcquisitionGatewayCompatibilityTests(SimpleTestCase):
    models = [Faculty, AcquisitionDocument, AcquisitionLine, Asset]

    def setUp(self):
        self.gateway = DjangoProviderGateway()
        self.tables = [model._meta.db_table for model in self.models]

    def test_exact_missing_table_is_reported(self):
        tables = [table for table in self.tables if table != "inventory_acquisitiondocument"]
        with patch.object(connection.introspection, "table_names", return_value=tables):
            with self.assertRaisesMessage(ProviderUnavailable, "inventory_acquisitiondocument") as caught:
                self.gateway._require_models(self.gateway.ASSET_MODELS)
        self.assertNotIn("inventory_faculty", str(caught.exception))

    def test_complete_table_inventory_returns_actual_models(self):
        with patch.object(connection.introspection, "table_names", return_value=self.tables):
            self.assertEqual(self.gateway._require_models(self.gateway.ASSET_MODELS), self.models)

    def test_introspection_failure_is_not_disguised_as_missing_provider(self):
        with patch.object(connection.introspection, "table_names", side_effect=OperationalError("DB unavailable")):
            with self.assertRaises(OperationalError):
                self.gateway._require_models(self.gateway.ASSET_MODELS)

    def test_query_failure_is_not_disguised_as_missing_provider(self):
        with patch.object(connection.introspection, "table_names", return_value=self.tables), patch.object(
            Faculty.objects, "filter", side_effect=ProgrammingError("incompatible schema")):
            with self.assertRaises(ProgrammingError):
                self.gateway.validate_assets([])

    def test_missing_provider_module_is_explicit(self):
        with patch("inventory.imports.gateways.import_module", side_effect=ModuleNotFoundError(
            "missing provider", name="inventory.acquisition_services")):
            with self.assertRaises(ProviderUnavailable):
                self.gateway._service("inventory.acquisition_services", "import_assets")

    def test_missing_internal_dependency_is_not_hidden(self):
        with patch("inventory.imports.gateways.import_module", side_effect=ModuleNotFoundError(
            "missing internal dependency", name="provider_internal_dependency")):
            with self.assertRaises(ModuleNotFoundError):
                self.gateway._service("inventory.acquisition_services", "import_assets")

    def test_missing_function_is_explicit_and_non_callable_is_an_error(self):
        with patch("inventory.imports.gateways.import_module", return_value=SimpleNamespace()):
            with self.assertRaises(ProviderUnavailable):
                self.gateway._service("inventory.acquisition_services", "import_assets")
        with patch("inventory.imports.gateways.import_module", return_value=SimpleNamespace(import_assets=42)):
            with self.assertRaises(TypeError):
                self.gateway._service("inventory.acquisition_services", "import_assets")
