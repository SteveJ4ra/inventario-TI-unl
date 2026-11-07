#!/bin/sh
set -eu
APP_DB_PASSWORD="$(cat /run/secrets/db_password)"
export APP_DB_PASSWORD
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<'SQL'
\getenv app_password APP_DB_PASSWORD
CREATE ROLE inventario_app WITH LOGIN PASSWORD :'app_password' NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE DATABASE inventario_ti OWNER inventario_app TEMPLATE template0 ENCODING 'UTF8' LOCALE_PROVIDER icu ICU_LOCALE 'und';
SQL
unset APP_DB_PASSWORD
