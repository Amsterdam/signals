# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0008_auto_20210402_1225'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedback',
            name='text_list',
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.TextField(blank=True, max_length=1000), blank=True, null=True, size=None),
        ),
    ]
