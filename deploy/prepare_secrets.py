"""Preparación local idempotente: nunca reemplaza secretos existentes."""
from pathlib import Path
import os
import secrets

root = Path(__file__).resolve().parent / ".secrets"
root.mkdir(mode=0o700, exist_ok=True)
for name in ("django_secret_key", "db_password", "db_admin_password", "test_db_password"):
    target = root / name
    try:
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        if not target.read_text(encoding="utf-8").strip():
            raise SystemExit(f"Archivo vacío: {name}; revisarlo antes de continuar")
    else:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(secrets.token_urlsafe(64) + "\n")
print("Cuatro secretos locales preparados; valores no mostrados. No se sobrescribieron archivos.")
