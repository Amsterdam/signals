# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.db import migrations

forward_sql_migrate = """
INSERT INTO history_log
(content_type_id, object_pk, action, data, created_by, created_at)
    SELECT cl.content_type_id,
           cl.object_id,
           CASE
            WHEN cl.action = 'U' THEN 'UPDATE'
            WHEN cl.action = 'I' THEN 'CREATE'
            ELSE 'UNKNOWN'
           END,
           cl.data::jsonb,
           cl.who as created_by,
           cl."when" as created_at
    FROM change_log AS cl
    LEFT JOIN history_log hl on (
        hl.content_type_id = cl.content_type_id and
        hl.object_pk = CAST(cl.object_id AS TEXT) and
        hl.created_at = cl.when
    )
    WHERE hl.object_pk IS NULL AND hl._signal_id IS NULL;
"""

reverse_sql_migrate = """
INSERT INTO change_log
(content_type_id, object_id, action, data, who, "when")
    SELECT
        hl.content_type_id,
        CAST(hl.object_pk AS INTEGER) as object_id,
        CASE
            WHEN hl.action = 'UPDATE' THEN 'U'
            WHEN hl.action = 'CREATE' THEN 'I'
        END,
        hl.data::text,
        hl.created_by as who,
        hl.created_at as "when"
    FROM history_log AS hl
    LEFT JOIN change_log cl on (
        hl.content_type_id = cl.content_type_id AND
        CAST(hl.object_pk AS INTEGER) = cl.object_id and
        hl.created_at = cl."when"
    )
    WHERE cl.object_id IS NULL AND hl._signal_id IS NULL;
"""


class Migration(migrations.Migration):
    check_exists_query = 'SELECT relname FROM pg_class WHERE relname='

    dependencies = [
        ('history', '0003_log_data'),
    ]

    operations = [
        migrations.RunSQL(forward_sql_migrate, reverse_sql=reverse_sql_migrate),
    ]
