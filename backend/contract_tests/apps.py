from inventory.apps import InventoryConfig


class ContractInventoryConfig(InventoryConfig):
    def import_models(self):
        super().import_models()
        from . import providers
        from inventory import retirement_models

    def ready(self):
        from django.db.models.signals import post_migrate
        def install(sender, using, **kwargs):
            if sender.label == "inventory":
                from django.db import connections
                from inventory.retirement_schema import install_retirement_guards
                install_retirement_guards(connections[using])
        post_migrate.connect(install, weak=False, dispatch_uid="contract_retirement_guards")
