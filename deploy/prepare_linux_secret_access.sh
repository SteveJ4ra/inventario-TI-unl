#!/bin/sh
# ACL de lectura por UID para secretos de Compose en Linux; no cambia propietario.
set -eu
if [ "$(uname -s)" != "Linux" ]; then
    echo "Este ajuste solo corresponde a anfitriones Linux."
    exit 1
fi
command -v setfacl >/dev/null || { echo "Instala el paquete acl y vuelve a ejecutar."; exit 1; }
secret_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/.secrets"
postgres_image='postgres:17-bookworm@sha256:665dc7b37ac52a17e298511414c21d23ffa4e6a6ef6225b3e5d59c7afb35e994'
pg_uid="${POSTGRES_RUNTIME_UID:-$(docker run --rm --entrypoint id "$postgres_image" -u postgres)}"
case "$pg_uid" in ''|*[!0-9]*|0) echo "UID de PostgreSQL inválido."; exit 1;; esac
for name in django_secret_key db_password db_admin_password test_db_password; do
    [ -f "$secret_dir/$name" ] || { echo "Ejecuta primero prepare_secrets.py."; exit 1; }
done
setfacl -m u:10001:r-- "$secret_dir/django_secret_key"
setfacl -m "u:10001:r--,u:$pg_uid:r--" "$secret_dir/db_password" "$secret_dir/test_db_password"
setfacl -m "u:$pg_uid:r--" "$secret_dir/db_admin_password"
echo "Lectura de secretos limitada a los UID de aplicación y PostgreSQL; valores no mostrados."
