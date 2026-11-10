"""Recolecta estáticos y reemplaza el proceso por Gunicorn; sin migraciones en workers."""
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings_deploy")
import django
django.setup()
from django.core.management import call_command
call_command("collectstatic", interactive=False, verbosity=0)
os.execvp("gunicorn", ["gunicorn", "config.wsgi:application", "--bind=0.0.0.0:8000", "--workers=2", "--timeout=60", "--error-logfile=-"])
