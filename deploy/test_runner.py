"""Pruebas en testdb aislado. Nunca utiliza el rol/base operativa de la aplicación."""
import os
import sys
from config.runtime_secrets import load_runtime_secrets
load_runtime_secrets()
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
os.environ.setdefault("INVENTORY_HTTP_LOG_LEVEL", "WARNING")
if sys.argv[1:2] == ["--pytest"]:
    os.execv(sys.executable, [sys.executable, "-m", "pytest", *sys.argv[2:]])
os.execv(sys.executable, [sys.executable, "manage.py", *sys.argv[1:]])
