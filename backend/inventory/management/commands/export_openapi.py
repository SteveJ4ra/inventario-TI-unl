import json
from django.core.management.base import BaseCommand
from inventory.openapi_v1 import SCHEMA

class Command(BaseCommand):
    help = "Exporta a stdout el contrato OpenAPI vigente, sin consultar la base."
    def handle(self, *args, **options):
        self.stdout.write(json.dumps(SCHEMA,ensure_ascii=False,indent=2))
