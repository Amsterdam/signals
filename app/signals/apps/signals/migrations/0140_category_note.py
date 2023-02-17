# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0139_json_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='note',
            field=models.TextField(blank=True, null=True),
        ),
    ]
