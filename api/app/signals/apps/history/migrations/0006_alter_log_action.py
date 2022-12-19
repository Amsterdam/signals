# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0005_alter_log__signal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='log',
            name='action',
            field=models.CharField(
                choices=[
                    ('UNKNOWN', 'Unknown'),
                    ('CREATE', 'Created'),
                    ('UPDATE', 'Updated'),
                    ('DELETE', 'Deleted'),
                    ('RECEIVE', 'Received'),
                    ('ACTION_NOT_RECEIVED', 'Not received')
                ],
                default='UNKNOWN',
                editable=False, max_length=20
            ),
        ),
    ]
