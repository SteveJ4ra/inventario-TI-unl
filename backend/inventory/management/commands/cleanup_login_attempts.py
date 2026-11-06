from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from inventory.models import LoginAttempt


class Command(BaseCommand):
    help = 'Elimina contadores de acceso cuya ventana temporal ha finalizado.'

    def handle(self, *args, **options):
        cutoff=timezone.now()-timedelta(seconds=settings.LOGIN_FAILURE_WINDOW_SECONDS)
        count,_=LoginAttempt.objects.filter(window_started__lte=cutoff).delete()
        self.stdout.write(f'Contadores expirados eliminados: {count}')
