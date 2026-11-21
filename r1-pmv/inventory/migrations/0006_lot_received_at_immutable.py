from django.db import migrations


def install_guard(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor == "sqlite":
        schema_editor.execute("""
            CREATE TRIGGER inventory_lot_received_at_immutable
            BEFORE UPDATE OF received_at ON inventory_lot
            WHEN NEW.received_at IS NOT OLD.received_at
            BEGIN
                SELECT RAISE(ABORT, 'Lot received_at is immutable');
            END
        """)
    elif vendor == "postgresql":
        schema_editor.execute("""
            CREATE FUNCTION inventory_lot_guard_received_at() RETURNS trigger
            LANGUAGE plpgsql AS $$
            BEGIN
                IF NEW.received_at IS DISTINCT FROM OLD.received_at THEN
                    RAISE EXCEPTION 'Lot received_at is immutable'
                        USING ERRCODE = '23514';
                END IF;
                RETURN NEW;
            END;
            $$
        """)
        schema_editor.execute("""
            CREATE TRIGGER inventory_lot_received_at_immutable
            BEFORE UPDATE OF received_at ON inventory_lot
            FOR EACH ROW EXECUTE FUNCTION inventory_lot_guard_received_at()
        """)
    else:
        raise RuntimeError("Lot receipt-time guard supports SQLite and PostgreSQL.")


def remove_guard(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        schema_editor.execute("DROP TRIGGER inventory_lot_received_at_immutable")
    elif schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("DROP TRIGGER inventory_lot_received_at_immutable ON inventory_lot")
        schema_editor.execute("DROP FUNCTION inventory_lot_guard_received_at()")


class Migration(migrations.Migration):
    dependencies = [("inventory", "0005_lot_responsible")]
    operations = [migrations.RunPython(install_guard, remove_guard)]
