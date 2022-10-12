# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaires', '0012_text_and_images_as_explanation'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionnaire',
            name='thank_you_message',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to='questionnaires.illustratedtext'
            ),
        ),
    ]
