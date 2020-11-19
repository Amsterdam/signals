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
        CASE
           WHEN stat.state = 'm' THEN 'Gemeld'
           WHEN stat.state = 'i' THEN 'In afwachting van behandeling'
           WHEN stat.state = 'b' THEN 'In behandeling'
           WHEN stat.state = 'h' THEN 'On hold'
           WHEN stat.state = 'ingepland' THEN 'Ingepland'
           WHEN stat.state = 'ready to send' THEN 'Te verzenden naar extern systeem'
           WHEN stat.state = 'o' THEN 'Afgehandeld'
           WHEN stat.state = 'a' THEN 'Geannuleerd'
           WHEN stat.state = 'reopenend' THEN 'Heropend'
           WHEN stat.state = 'reopened' THEN 'Heropend'
           WHEN stat.state = 's' THEN 'Gesplitst'
           WHEN stat.state = 'closure requested' THEN 'Verzoek tot afhandeling'
           WHEN stat.state = 'sent' THEN 'Verzonden naar extern systeem'
           WHEN stat.state = 'send failed' THEN 'Verzending naar extern systeem mislukt'
           WHEN stat.state = 'done external' THEN 'Melding is afgehandeld in extern systeem'
           WHEN stat.state = 'reopen requested' THEN 'Verzoek tot heropenen'
           WHEN stat.state = '' THEN 'Leeg'
           ELSE NULL END
        AS status_display,
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
        ('reporting', '0002_add_dro_view'),
    ]

    operations = [
        migrations.RunSQL(view_sql),
    ]
