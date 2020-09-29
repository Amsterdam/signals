from django.db import migrations

view_sql = """
DROP VIEW IF EXISTS "signals_ext_tdo";
CREATE VIEW "signals_ext_tdo" AS
    SELECT
        sig.id,
        sig.created_at,
        sig.updated_at,
        loc.geometrie AS geometry,
        stat.state AS status,
        maincat.slug AS main_slug,
        subcat.slug AS sub_slug
    FROM signals_signal AS sig
        INNER JOIN signals_location AS loc
            ON sig.location_id = loc.id
        INNER JOIN signals_status AS stat
            ON sig.status_id = stat.id
        INNER JOIN signals_categoryassignment AS cas
            ON sig.category_assignment_id = cas.id
        INNER JOIN signals_category AS subcat
            ON subcat.id = cas.category_id
        INNER JOIN signals_category AS maincat
            ON maincat.id = subcat.parent_id;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('reporting', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(view_sql),
    ]
