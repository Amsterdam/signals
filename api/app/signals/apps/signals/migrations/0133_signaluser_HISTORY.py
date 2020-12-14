from django.db import migrations

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
            CONCAT('UPDATE_SLA_', CAST("ca1"."id" AS VARCHAR(255))) AS "identifier",
            "ca1"."_signal_id" AS "_signal_id",
            "ca1"."created_at" AS "when",
            'UPDATE_SLA' AS "what",
            NULL AS "who",
            NULL AS "extra",
            "sc1"."handling_message" AS "description"
        FROM
            "public"."signals_categoryassignment" AS "ca1",
            "public"."signals_category" AS "sc1"
        WHERE
            "ca1"."category_id" = "sc1"."id"
            AND "ca1"."id" = (
                SELECT MIN("sca1"."id")
                FROM "public"."signals_categoryassignment" AS "sca1"
                WHERE "sca1"."_signal_id" = "ca1"."_signal_id"
            )
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
            CASE
                WHEN "dd"."relation_type" = 'routing' THEN CONCAT('UPDATE_ROUTING_ASSIGNMENT_', CAST("dd"."id" AS VARCHAR(255)))
                WHEN "dd"."relation_type" = 'directing' THEN CONCAT('UPDATE_DIRECTING_DEPARTMENTS_ASSIGNMENT_', CAST("dd"."id" AS VARCHAR(255)))
                ELSE 'UNKNOWN'
            END as "identifier",
            "dd"."_signal_id" AS "_signal_id",
            "dd"."created_at" AS "when",
            CASE
                WHEN "dd"."relation_type" = 'routing' THEN 'UPDATE_ROUTING_ASSIGNMENT'
                WHEN "dd"."relation_type" = 'directing' THEN 'UPDATE_DIRECTING_DEPARTMENTS_ASSIGNMENT'
                ELSE 'UNKNOWN'
            END as "what",
            "created_by" AS "who",
            array_to_string(array(
                SELECT "sd"."code"
                FROM "signals_department" AS "sd"
                JOIN "signals_signaldepartments_departments" AS "ssd" ON "sd"."id" = "ssd"."department_id"
                WHERE "ssd"."signaldepartments_id" = "dd"."id"
                ORDER BY "sd"."code"
                ), ', ') AS "extra",
               null AS "description"
        FROM
            "public"."signals_signaldepartments" AS "dd"
        UNION SELECT
            CONCAT('UPDATE_USER_ASSIGNMENT_', CAST("us"."id" AS VARCHAR(255))) AS "identifier",
            "us"."_signal_id" AS "_signal_id",
            "us"."created_at" AS "when",
            'UPDATE_USER_ASSIGNMENT' AS "what",
            "created_by" AS "who",
            CAST("user"."email" AS VARCHAR(255)) AS "extra",
            null AS "description"
        FROM
            "public"."signals_signaluser" AS "us", "public"."auth_user" AS "user"
        WHERE
            "us"."user_id" = "user"."id" 
        UNION SELECT
            CONCAT('CHILD_SIGNAL_CREATED_', "cs"."id") AS "identifier",
            "cs"."parent_id" AS "_signal_id",
            "cs"."created_at" AS "when",
            'CHILD_SIGNAL_CREATED' AS "what",
            null AS "who",
            CAST("cs"."id" AS varchar) AS "extra",
            '_signal_id contains the parent Signal ID, extra contains the child Signal ID' AS "description"
        FROM signals_signal AS "cs"
        INNER JOIN signals_signal AS "ps" ON "ps"."id" = "cs"."parent_id"
        INNER JOIN signals_status AS "pss" ON "pss"."id" = "ps"."status_id" AND "pss"."state" != 's'

    ) AS "subselect"
    ORDER BY
        "when"
    DESC;
""" # noqa


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0132_migrate_users_signaluser_data'),
    ]

    operations = [
        migrations.RunSQL(history_view),
    ]
