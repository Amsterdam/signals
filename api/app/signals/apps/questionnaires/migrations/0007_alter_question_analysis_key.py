# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaires', '0006_retrieval_key_and_analysis_key'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='analysis_key',
            field=models.CharField(default='analysis_key_placeholder', max_length=255),
        ),
    ]
