# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0154_statusmessagetemplate_is_active'),
        ('questionnaires', '0007_auto_20210830_2156'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='label',
            field=models.CharField(max_length=1000),
        ),
        migrations.AlterField(
            model_name='questionnaire',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='session',
            name='_signal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to='signals.signal'),
        ),
    ]
