import json
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from inventory.legacy_preflight import acquisition_preflight


class Command(BaseCommand):
    help = "Diagnóstico 003 de solo lectura; no migra ni asigna facultades."

    def handle(self, *args, **options):
        required = {"inventory_asset", "inventory_faculty", "inventory_acquisitionline"}
        if not required.issubset(set(connection.introspection.table_names())):
            raise CommandError("Falta el esquema de expansión revisado. No se modificó la base.")
        self.stdout.write(json.dumps(acquisition_preflight(), ensure_ascii=False, sort_keys=True))
