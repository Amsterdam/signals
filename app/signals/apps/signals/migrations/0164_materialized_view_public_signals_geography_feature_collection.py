# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam

import django.contrib.gis.db.models.fields
from django.db import migrations, models

create_materialized_view = '''
CREATE MATERIALIZED VIEW "public_signals_geography_feature_collection" AS
  SELECT
    "signals_signal"."id",
    "signals_signal"."uuid",
    "signals_location"."geometrie" AS geometry,
    "signals_status"."state" AS state,
    scp."id" as parent_category_id,
    "signals_category"."id" as child_category_id,
    "signals_category"."is_public_accessible" as child_category_is_public_accessible,
    "signals_signal"."created_at",
    JSONB_BUILD_OBJECT(
      'type', 'Feature',
      'geometry', st_asgeojson("signals_location"."geometrie")::jsonb,
      'properties', JSONB_BUILD_OBJECT(
      'category', JSONB_BUILD_OBJECT(
        'name', CASE WHEN "signals_category"."public_name" = '' THEN "signals_category"."name" WHEN "signals_category"."public_name" IS NULL THEN "signals_category"."name" ELSE "signals_category"."public_name" END,
        'slug', "signals_category"."slug",
        'parent', JSONB_BUILD_OBJECT(
          'name', CASE WHEN scp."public_name" = ''  THEN scp."name" WHEN scp."public_name" IS NULL THEN scp."name" ELSE scp."public_name" END,
          'slug', scp."slug"
        )
      ),
      'created_at', "signals_signal"."created_at"
    )
    ) AS "feature"
  FROM "signals_signal"
    lEFT OUTER JOIN "signals_status" ON ("signals_signal"."status_id" = "signals_status"."id")
    LEFT OUTER JOIN "signals_categoryassignment" ON ("signals_signal"."category_assignment_id" = "signals_categoryassignment"."id")
    LEFT OUTER JOIN "signals_category" ON ("signals_categoryassignment"."category_id" = "signals_category"."id")
    INNER JOIN "signals_location" ON ("signals_signal"."location_id" = "signals_location"."id")
    LEFT OUTER JOIN "signals_category" scp ON ("signals_category"."parent_id" = scp."id")
  WHERE NOT ("signals_status"."state" IN ('o', 'done external', 'a', 'reopen requested'));

  CREATE UNIQUE INDEX psgfc_id_uniq ON "public_signals_geography_feature_collection" ("id");
  CREATE INDEX psgfc_geometry_id ON "public_signals_geography_feature_collection" USING GIST ("geometry");
  CREATE INDEX psgfc_state_key ON "public_signals_geography_feature_collection" ("state");
'''  # noqa

drop_materialized_view = '''
DROP MATERIALIZED VIEW IF EXISTS "public_signals_geography_feature_collection";
'''


def create_default_periodic_task_to_refresh_the_materialized_view(apps, schema_editor):
    """
    Create a periodic task to refresh the materialized view
    """
    CrontabSchedule = apps.get_model('django_celery_beat', 'CrontabSchedule')
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')

    # Every 30 minutes past every hour
    crontab, _ = CrontabSchedule.objects.get_or_create(minute='*/30', hour='*/1')

    # Create periodic task only if it does not exist already
    periodic_task, created = PeriodicTask.objects.get_or_create(
        task='signals.apps.signals.tasks.refresh_materialized_view_public_signals_geography_feature_collection',
        defaults={
            'name': 'Refresh materialized view "public_signals_geography_feature_collection"',
            'crontab': crontab
        }
    )

    if not created and not periodic_task.enabled:
        periodic_task.enabled = True
        periodic_task.save()


def rollback_default_periodic_task_to_refresh_the_materialized_view(apps, schema_editor):
    """
    Remove all periodic tasks that are present for the task that refreshed the materialized view
    """
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')
    periodic_task_queryset = PeriodicTask.objects.filter(
        task='signals.apps.signals.tasks.refresh_materialized_view_public_signals_geography_feature_collection'
    )
    periodic_task_queryset.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0163_category_icon'),
    ]

    operations = [
        migrations.CreateModel(
            name='PublicSignalGeographyFeature',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('uuid', models.UUIDField()),
                ('geometry', django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ('state', models.CharField(max_length=36)),
                ('child_category_id', models.BigIntegerField()),
                ('child_category_is_public_accessible', models.BooleanField()),
                ('parent_category_id', models.BigIntegerField()),
                ('created_at', models.DateTimeField()),
                ('feature', models.JSONField()),
            ],
            options={
                'db_table': 'public_signals_geography_feature_collection',
                'managed': False,
            },
        ),

        # Create the view, and a rollback option
        migrations.RunSQL(create_materialized_view,
                          reverse_sql=drop_materialized_view),
        # Create the periodic task, and a rollback option
        migrations.RunPython(create_default_periodic_task_to_refresh_the_materialized_view,
                             reverse_code=rollback_default_periodic_task_to_refresh_the_materialized_view)
    ]
