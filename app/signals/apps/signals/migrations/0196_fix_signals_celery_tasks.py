# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations import RunPython

FORWARD_MAPPING = {
    'signals.apps.signals.tasks.anonymize_reporter': 'signals.apps.signals.tasks.anonymize_reporter.anonymize_reporter',
    'signals.apps.signals.tasks.anonymize_reporters': 'signals.apps.signals.tasks.anonymize_reporter.anonymize_reporters',
    'signals.apps.signals.tasks.apply_auto_create_children': 'signals.apps.signals.tasks.child_signals.apply_auto_create_children',
    'signals.apps.signals.tasks.update_status_children_based_on_parent': 'signals.apps.signals.tasks.child_signals.update_status_children_based_on_parent',
    'signals.apps.signals.tasks.clearsessions': 'signals.apps.signals.tasks.clear_sessions.clearsessions',
    'signals.apps.signals.tasks.refresh_materialized_view_public_signals_geography_feature_collection': 'signals.apps.signals.tasks.refresh_database_view.refresh_materialized_view_public_signals_geography_feature_collection',
    'signals.apps.signals.tasks.apply_routing': 'signals.apps.signals.tasks.signal_routing.apply_routing',
}  # noqa

REVERSED_MAPPING = {
    'signals.apps.signals.tasks.anonymize_reporter.anonymize_reporter': 'signals.apps.signals.tasks.anonymize_reporter',
    'signals.apps.signals.tasks.anonymize_reporter.anonymize_reporters': 'signals.apps.signals.tasks.anonymize_reporters',
    'signals.apps.signals.tasks.child_signals.apply_auto_create_children': 'signals.apps.signals.tasks.apply_auto_create_children',
    'signals.apps.signals.tasks.child_signals.update_status_children_based_on_parent': 'signals.apps.signals.tasks.update_status_children_based_on_parent',
    'signals.apps.signals.tasks.clear_sessions.clearsessions': 'signals.apps.signals.tasks.clearsessions',
    'signals.apps.signals.tasks.refresh_database_view.refresh_materialized_view_public_signals_geography_feature_collection': 'signals.apps.signals.tasks.refresh_materialized_view_public_signals_geography_feature_collection',
    'signals.apps.signals.tasks.signal_routing.apply_routing': 'signals.apps.signals.tasks.apply_routing',
}  # noqa

def _fix_celery_tasks(
        apps: Apps,
        schema_editor: BaseDatabaseSchemaEditor
) -> None:
    PeriodicTask = apps.get_model(
        app_label='django_celery_beat',
        model_name='PeriodicTask'
    )

    # Loop through the keys in the FORWARD_MAPPING dictionary
    for key, value in FORWARD_MAPPING.items():
        PeriodicTask.objects.filter(task=key).update(task=value)

def _reverse_fix_celery_tasks(
        apps: Apps,
        schema_editor: BaseDatabaseSchemaEditor
) -> None:
    PeriodicTask = apps.get_model(
        app_label='django_celery_beat',
        model_name='PeriodicTask'
    )

    # Loop through the keys in the REVERSED_MAPPING dictionary
    for key, value in REVERSED_MAPPING.items():
        PeriodicTask.objects.filter(task=key).update(task=value)


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0195_auto_20230821_1059'),
    ]

    operations = [
        RunPython(
            code=_fix_celery_tasks,
            reverse_code=_reverse_fix_celery_tasks
        )
    ]
