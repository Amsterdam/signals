# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam
from django.db import migrations

import signals.apps.services.domain.checker_factories
import signals.apps.services.domain.mimetypes
import signals.apps.services.validator.file
import signals.apps.signals.models.attachment


class Migration(migrations.Migration):
    dependencies = [
        ('signals', '0203_signal_source_index'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='file',
            field=signals.apps.signals.models.attachment.SignalAttachmentFileField(
                max_length=255, upload_to='attachments/%Y/%m/%d/', validators=[
                    signals.apps.services.validator.file.MimeTypeAllowedValidator(
                        signals.apps.services.domain.mimetypes.MimeTypeFromContentResolverFactory(),
                        ('image/jpeg', 'image/png', 'image/gif', 'application/pdf')
                    ),
                    signals.apps.services.validator.file.MimeTypeIntegrityValidator(
                        signals.apps.services.domain.mimetypes.MimeTypeFromContentResolverFactory(),
                        signals.apps.services.domain.mimetypes.MimeTypeFromFilenameResolverFactory()
                    ),
                    signals.apps.services.validator.file.ContentIntegrityValidator(
                        signals.apps.services.domain.mimetypes.MimeTypeFromContentResolverFactory(),
                        signals.apps.services.domain.checker_factories.ContentCheckerFactory()
                    ),
                    signals.apps.services.validator.file.FileSizeValidator(20971520)
                ]
            ),
        ),
    ]
