"""Respaldo/restauración verificable de la demostración aislada, sin sobrescribir datos.
Ejecutar en el host, sin escrituras concurrentes: python deploy/backup_roundtrip.py
Se restringe al proyecto de validación final. Los respaldos no se versionan.
"""
import hashlib
import json
import re
import subprocess
import uuid
from pathlib import Path

PROJECT = "inventario-ti-u1-final"
BASE = ["docker", "compose", "-p", PROJECT]
ROOT = Path(__file__).resolve().parent.parent
TOKEN = uuid.uuid4().hex
RESTORE_DB = "restorecheck_" + TOKEN
DUMP = "/tmp/" + RESTORE_DB + ".dump"


def run(args):
    result = subprocess.run(BASE + args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise RuntimeError("Falló " + args[0] + ": " + result.stderr[-1200:])
    return result.stdout


def sql(database, query):
    return run(["exec", "-T", "db", "psql", "-U", "inventario_admin", "-d", database, "-X", "-A", "-t", "-v", "ON_ERROR_STOP=1", "-c", query]).strip()


def fingerprint(database):
    tables = sql(database, "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename").splitlines()
    result = {}
    for table in tables:
        if not re.fullmatch(r"[a-z_][a-z_0-9]*", table):
            raise RuntimeError("Nombre de tabla no permitido")
        rows = sql(database, f'SELECT row_to_json(t)::text FROM "{table}" t ORDER BY row_to_json(t)::text')
        count = int(sql(database, f'SELECT count(*) FROM "{table}"'))
        result[table] = {"rows": count, "sha256": hashlib.sha256(rows.encode("utf-8")).hexdigest()}
    return result


def main():
    output = ROOT / "deploy" / "results"
    output.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        before = fingerprint("inventario_ti")
        run(["exec", "-T", "db", "pg_dump", "-U", "inventario_admin", "-d", "inventario_ti", "-Fc", "-f", DUMP])
        run(["exec", "-T", "db", "createdb", "-U", "inventario_admin", "--template=template0", RESTORE_DB])
        created = True
        run(["exec", "-T", "db", "pg_restore", "-U", "inventario_admin", "--no-owner", "--no-privileges", "--exit-on-error", "-d", RESTORE_DB, DUMP])
        restored = fingerprint(RESTORE_DB)
        if restored != before:
            raise RuntimeError("El contenido restaurado difiere; comprobar escrituras concurrentes")
        run(["cp", "db:" + DUMP, str(output / (RESTORE_DB + ".dump"))])
        result = {"project": PROJECT, "source_database": "inventario_ti", "isolated_restore_database": RESTORE_DB,
                  "tables_verified": len(before), "rows_verified": sum(t["rows"] for t in before.values()),
                  "content_sha256_equal": True, "source_overwritten": False}
        (output / "backup-validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
    finally:
        if created:
            run(["exec", "-T", "db", "dropdb", "-U", "inventario_admin", RESTORE_DB])
        run(["exec", "-T", "db", "rm", "-f", "--", DUMP])


if __name__ == "__main__":
    main()
