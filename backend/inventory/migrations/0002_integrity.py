from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("inventory", "0001_initial")]
    operations = [
        migrations.RunSQL(
            sql="""
        CREATE SEQUENCE inventory_asset_code_seq AS bigint START WITH 1 INCREMENT BY 1 NO CYCLE;
        CREATE FUNCTION inventory_movement_immutable() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'El historial es inmutable; registra una rectificación' USING ERRCODE = '55000';
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER inventory_movement_no_change
            BEFORE UPDATE OR DELETE ON inventory_movement
            FOR EACH ROW EXECUTE FUNCTION inventory_movement_immutable();
        """,
            reverse_sql="""
        DROP TRIGGER inventory_movement_no_change ON inventory_movement;
        DROP FUNCTION inventory_movement_immutable();
        DROP SEQUENCE inventory_asset_code_seq;
        """,
        )
    ]
