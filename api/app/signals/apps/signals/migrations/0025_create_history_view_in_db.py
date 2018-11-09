from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('signals', '0024_create_history_view_in_db'),
    ]

    operations = [
        migrations.RunSQL(
"""
DROP VIEW IF EXISTS "signals_history_view";
CREATE VIEW "signals_history_view" AS
	SELECT
		_signal_id,
		CAST("when" AS timestamptz),
		CAST("what" AS varchar(255)),
		CAST("who" AS varchar(255)),
		CAST("extra" AS varchar(255)),
		CAST("description" AS varchar(3000)) /* Most extreme case is the Note model's text field. */
	FROM (
		SELECT
			"s"."_signal_id" AS "_signal_id",
			"s"."created_at" AS "when",
			'UPDATE_STATUS' As "what",
			"s"."user" AS "who",
			"s"."state" AS "extra",
			"s"."text" AS "description"
		FROM
			"public"."signals_status" AS "s"
		UNION SELECT
			"p"."_signal_id" AS "_signal_id",
			"p"."created_at" AS "when",
			'UPDATE_PRIORITY' AS "what",
			"p"."created_by" AS "who",
			"p"."priority" AS "extra",
			null AS "description"
		FROM
			"public"."signals_priority" AS "p"
		UNION SELECT
			"ca"."_signal_id" AS "_signal_id",
			"ca"."created_at" AS "when",
			'UPDATE_CATEGORY_ASSIGNMENT' AS "what",
			"created_by" AS "who",
			"sc"."name" AS "extra",
			null AS "description"
		FROM
			"public"."signals_categoryassignment" AS "ca",
			"public"."signals_subcategory" AS "sc"
		WHERE
			"ca"."sub_category_id" = "sc"."id"
		UNION SELECT
			"n"."_signal_id" as "_signal_id",
			"n"."created_at" as "when",
			'CREATE_NOTE' as "what",
			"n"."created_by" as "who",
			'Notitie toegevoegd' as "extra",
			"n"."text" as "description"
		FROM
			"public"."signals_note" AS "n"
		UNION SELECT
			"l"."_signal_id" AS "_signal_id",
			"l"."created_at" AS "when",
			'UPDATE_LOCATION' AS "what",
			"created_by" AS "who",
			'Locatie gewijzigd' AS "extra",
			null AS "description"
		FROM 
			"public"."signals_location" AS "l"
	) AS "subselect"
	ORDER BY
		"when"
	DESC;
"""
        ),
    ]
