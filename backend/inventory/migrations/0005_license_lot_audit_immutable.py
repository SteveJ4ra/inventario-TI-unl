from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("inventory", "0004_license_lots")]
    operations = [
        migrations.RunSQL(
            sql="""
                CREATE FUNCTION inventory_license_audit_immutable() RETURNS trigger AS $$
                BEGIN
                    RAISE EXCEPTION 'El historial de licencias es inmutable'
                        USING ERRCODE = '55000';
                END;
                $$ LANGUAGE plpgsql;
                CREATE TRIGGER inventory_license_audit_no_change
                    BEFORE UPDATE OR DELETE ON inventory_licenselotaudit
                    FOR EACH ROW EXECUTE FUNCTION inventory_license_audit_immutable();
            """,
            reverse_sql="""
                DROP TRIGGER inventory_license_audit_no_change ON inventory_licenselotaudit;
                DROP FUNCTION inventory_license_audit_immutable();
            """,
        ),
    ]
