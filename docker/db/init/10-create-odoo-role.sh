#!/bin/bash
# Runs once, when the PostgreSQL data volume is initialized for the first time.
# Creates the role Odoo connects with: it may log in and create databases, but it
# is not a superuser and cannot create other roles.
if [ -z "${ODOO_DB_USER:-}" ] || [ -z "${ODOO_DB_PASSWORD:-}" ]; then
    echo "ODOO_DB_USER and ODOO_DB_PASSWORD must be set" >&2
    exit 1
fi

psql --variable=ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
    --set=role_name="$ODOO_DB_USER" --set=role_password="$ODOO_DB_PASSWORD" <<'SQL'
CREATE ROLE :"role_name" LOGIN CREATEDB NOSUPERUSER NOCREATEROLE PASSWORD :'role_password';
SQL
