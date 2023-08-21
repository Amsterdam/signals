# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations import RunPython
from django.db.models import OuterRef, Subquery


def _make_attachment_public_when_uploaded_by_reporter(
        apps: Apps,
        schema_editor: BaseDatabaseSchemaEditor
) -> None:
    Reporter = apps.get_model('signals', 'Reporter')
    Attachment = apps.get_model('signals', 'Attachment')
    reporters = Reporter.objects.filter(_signal=OuterRef('_signal'))
    attachments = Attachment.objects.filter(created_by__in=Subquery(reporters.values('email')))
    for attachment in attachments:
        attachment.public = True
        attachment.save()


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0194_auto_20230821_1046'),
    ]

    operations = [
        RunPython(_make_attachment_public_when_uploaded_by_reporter)
    ]
