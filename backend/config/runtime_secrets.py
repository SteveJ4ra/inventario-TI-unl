"""Carga secretos de Docker sin guardarlos en la imagen ni mostrarlos."""
import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured


def load_runtime_secrets():
    for name in ("DJANGO_SECRET_KEY", "DB_PASSWORD"):
        path = os.environ.get(name + "_FILE")
        if path:
            try:
                value = Path(path).read_text(encoding="utf-8").strip()
            except OSError as exc:
                raise ImproperlyConfigured(f"No se pudo leer {name}_FILE") from exc
            if not value:
                raise ImproperlyConfigured(f"El archivo {name}_FILE está vacío")
            os.environ[name] = value
        if not os.environ.get(name):
            raise ImproperlyConfigured(f"Falta configurar {name} o {name}_FILE")
