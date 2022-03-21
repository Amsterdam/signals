# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0154_statusmessagetemplate_is_active'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='attachment',
            options={
                'ordering': ('created_at',),
                'permissions': [
                    ('delete_attachment_of_normal_signal', 'Can delete attachment on normal signal.'),
                    ('delete_attachment_of_parent_signal', 'Can delete attachment on parent signal.'),
                    ('delete_attachment_of_child_signal', 'Can delete attachment on child signal.'),
                    ('delete_attachment_of_other_user', 'Can delete attachment uploaded by another user.')
                ]
            },
        ),
    ]
