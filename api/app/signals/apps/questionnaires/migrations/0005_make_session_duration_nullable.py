# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaires', '0004_alter_questiongraph_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='session',
            name='duration',
            field=models.DurationField(blank=True, default=datetime.timedelta(seconds=7200), null=True),
        ),
    ]
