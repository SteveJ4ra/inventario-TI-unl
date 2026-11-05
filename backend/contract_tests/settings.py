"""Solo tests de contrato 005, nunca configuración productiva."""
from config.settings import *
INSTALLED_APPS = ["contract_tests.apps.ContractInventoryConfig" if entry == "inventory.apps.InventoryConfig" else entry for entry in INSTALLED_APPS]
MIGRATION_MODULES = {"inventory": None, "auth": None, "admin": None, "contenttypes": None, "sessions": None}

ROOT_URLCONF = "contract_tests.urls"
