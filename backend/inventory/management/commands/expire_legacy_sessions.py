from django.contrib.sessions.models import Session
from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime


class Command(BaseCommand):
    help = 'Caduca sesiones anteriores sin un vencimiento absoluto válido dentro del plazo configurado. Ejecutar al desplegar la política nueva.'

    def handle(self, *args, **options):
        now=timezone.now()
        count=0
        for session in Session.objects.filter(expire_date__gt=now).iterator():
            value=session.get_decoded().get('_session_expiry')
            try:
                deadline=parse_datetime(value) if isinstance(value,str) else None
            except ValueError:
                deadline=None
            valid=(deadline is not None and timezone.is_aware(deadline)
                   and now < deadline <= now+timedelta(seconds=settings.INVENTORY_SESSION_LIFETIME_SECONDS))
            if not valid:
                count+=Session.objects.filter(pk=session.pk,session_data=session.session_data).update(expire_date=now)
        self.stdout.write(f'Sesiones anteriores caducadas: {count}')
