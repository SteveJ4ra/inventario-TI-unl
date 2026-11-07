"""Pruebas en testdb aislado. Nunca utiliza el rol/base operativa de la aplicación."""
import os
import sys
from config.runtime_secrets import load_runtime_secrets
load_runtime_secrets()
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
os.execv(sys.executable, [sys.executable, "manage.py", *sys.argv[1:]])
