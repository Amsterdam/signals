# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam
from django.db import migrations

import signals.apps.services.attachment_files


class Migration(migrations.Migration):
    dependencies = [
        ('questionnaires', '0013_forward_to_external_flow_changes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storedfile',
            name='file',
            field=signals.apps.services.attachment_files.SanitizedAttachmentFileField(
                max_length=255,
                upload_to='attachments/questionnaires/stored_files/%Y/%m/%d/',
            ),
        ),
    ]
