# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaires', '0003_add_triggers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questiongraph',
            name='name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
