"""Inicialización explícita y anterior al servidor; no crea usuarios por defecto."""
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings_deploy")
import django
django.setup()
from django.core.management import call_command
from inventory.qr_urls import build_asset_qr_url
build_asset_qr_url("TI-CHECK")
call_command("check")
call_command("migrate", interactive=False)
call_command("expire_legacy_sessions")
