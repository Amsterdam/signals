# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Delta10 B.V.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0203_signal_source_index'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expressioncontext',
            name='identifier_type',
            field=models.CharField(
                choices=[
                    ('point', 'point'),
                    ('str', 'str'),
                    ('number', 'number'),
                    ('time', 'time'),
                    ('set', 'set'),
                    ('dict', 'dict'),
                    ('boolean', 'boolean'),
                ],
                default='number',
                max_length=255,
            ),
        ),
    ]
