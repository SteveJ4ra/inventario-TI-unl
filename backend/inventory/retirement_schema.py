"""Guardas PostgreSQL; invocar desde migración tras crear tablas 005."""


def install_retirement_guards(connection):
    tables = ("inventory_approvaldecision", "inventory_decommissionevent", "inventory_retirementaudit")
    with connection.cursor() as cursor:
        cursor.execute("""CREATE OR REPLACE FUNCTION inventory_retirement_immutable() RETURNS trigger AS $$
        BEGIN RAISE EXCEPTION 'El historial de bajas es inmutable' USING ERRCODE = '55000'; END;
        $$ LANGUAGE plpgsql""")
        for table in tables:
            name = connection.ops.quote_name(table)
            trigger = connection.ops.quote_name(table + "_immutable")
            cursor.execute(f"DROP TRIGGER IF EXISTS {trigger} ON {name}")
            cursor.execute(f"CREATE TRIGGER {trigger} BEFORE UPDATE OR DELETE ON {name} FOR EACH ROW EXECUTE FUNCTION inventory_retirement_immutable()")
