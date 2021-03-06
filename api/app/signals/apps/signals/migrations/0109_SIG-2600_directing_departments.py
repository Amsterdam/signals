# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
import django.db.models.deletion
from django.db import migrations, models

history_view = """
DROP VIEW IF EXISTS "signals_history_view";
CREATE VIEW "signals_history_view" AS
    SELECT
        CAST("identifier" AS varchar(255)),
        _signal_id,
        CAST("when" AS timestamptz),
        CAST("what" AS varchar(255)),
        CAST("who" AS varchar(255)),
        CAST("extra" AS varchar(255)),
        CAST("description" AS varchar(3000))  /* Most extreme case; the Note model's text field. */
    FROM (
        SELECT
            CONCAT('UPDATE_STATUS_', CAST("s"."id" AS VARCHAR(255))) AS "identifier",
            "s"."_signal_id" AS "_signal_id",
            "s"."created_at" AS "when",
            'UPDATE_STATUS' As "what",
            "s"."user" AS "who",
            "s"."state" AS "extra",
            "s"."text" AS "description"
        FROM
            "public"."signals_status" AS "s"
        UNION SELECT
            CONCAT('UPDATE_PRIORITY_', CAST("p"."id" AS VARCHAR(255))) AS "identifier",
            "p"."_signal_id" AS "_signal_id",
            "p"."created_at" AS "when",
            'UPDATE_PRIORITY' AS "what",
            "p"."created_by" AS "who",
            "p"."priority" AS "extra",
            null AS "description"
        FROM
            "public"."signals_priority" AS "p"
        UNION SELECT
            CONCAT('UPDATE_CATEGORY_ASSIGNMENT_', CAST("ca"."id" AS VARCHAR(255))) AS "identifier",
            "ca"."_signal_id" AS "_signal_id",
            "ca"."created_at" AS "when",
            'UPDATE_CATEGORY_ASSIGNMENT' AS "what",
            "created_by" AS "who",
            "sc"."name" AS "extra",
            "ca"."text" AS "description"
        FROM
            "public"."signals_categoryassignment" AS "ca",
            "public"."signals_category" AS "sc"
        WHERE
            "ca"."category_id" = "sc"."id"
        UNION SELECT
            CONCAT('CREATE_NOTE_', CAST("n"."id" AS VARCHAR(255))) AS "identifier",
            "n"."_signal_id" as "_signal_id",
            "n"."created_at" as "when",
            'CREATE_NOTE' as "what",
            "n"."created_by" as "who",
            'Notitie toegevoegd' AS "extra",
            "n"."text" AS "description"
        FROM
            "public"."signals_note" AS "n"
        UNION SELECT
            CONCAT('UPDATE_LOCATION_', CAST("l"."id" AS VARCHAR(255))) AS "identifier",
            "l"."_signal_id" AS "_signal_id",
            "l"."created_at" AS "when",
            'UPDATE_LOCATION' AS "what",
            "created_by" AS "who",
            'Locatie gewijzigd' AS "extra",
            null AS "description"
        FROM
            "public"."signals_location" AS "l"
        UNION SELECT
            /* token is not numerical id, inconsistent */
            CONCAT('RECEIVE_FEEDBACK_', "f"."token") AS "identifier",
            "f"."_signal_id" AS "_signal_id",
            "f".submitted_at AS "when",
            'RECEIVE_FEEDBACK' AS "what",
            null AS "who",
            'Feedback ontvangen' AS "extra",
            null AS "description"
        FROM
            "public"."feedback_feedback" AS "f"
        WHERE
            "f"."submitted_at" IS NOT null
         UNION SELECT
            CONCAT('UPDATE_TYPE_ASSIGNMENT_', "st"."id") AS "identifier",
            "st"."_signal_id" AS "_signal_id",
            "st"."created_at" AS "when",
            'UPDATE_TYPE_ASSIGNMENT' AS "what",
            "st"."created_by" AS "who",
            "st"."name" AS "extra",
            null AS "description"
        FROM
            "public"."signals_type" AS "st"
        UNION SELECT
                    CONCAT('UPDATE_DIRECTING_DEPARTMENTS_ASSIGNMENT_', CAST("dd"."id" AS VARCHAR(255))) AS "identifier",
                    "dd"."_signal_id" AS "_signal_id",
                    "dd"."created_at" AS "when",
                    'UPDATE_DIRECTING_DEPARTMENTS_ASSIGNMENT' AS "what",
                    "created_by" AS "who",
                    array_to_string(array(
                        SELECT "sd"."code"
                        FROM "signals_department" AS "sd"
                        JOIN "signals_directingdepartments_departments" AS "ssd" ON "sd"."id" = "ssd"."department_id"
                        WHERE "ssd"."directingdepartments_id" = "dd"."id"
                        ORDER BY "sd"."code"
                        ), ', ') AS "extra",
                       null AS "description"
                FROM
                    "public"."signals_directingdepartments" AS "dd"
    ) AS "subselect"
    ORDER BY
        "when"
    DESC;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0108_area_uniqueness_constraints'),
    ]

    operations = [
        migrations.CreateModel(
            name='DirectingDepartments',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.EmailField(blank=True, max_length=254, null=True)),
                ('_signal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              related_name='directing_departments', to='signals.Signal')),
                ('departments', models.ManyToManyField(related_name='_directingdepartments_departments_+',
                                                       to='signals.Department')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='signal',
            name='directing_departments_assignment',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='signal',
                                       to='signals.DirectingDepartments'),
        ),
        migrations.RunSQL(history_view),
    ]
