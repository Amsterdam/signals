# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0088_SIG-2008'),
    ]

    operations = [
        migrations.AlterField(
            model_name='priority',
            name='priority',
            field=models.CharField(
                choices=[
                    ('low', 'Low'),
                    ('normal', 'Normal'),
                    ('high', 'High')
                ],
                default='normal',
                max_length=10
            ),
        ),
    ]
