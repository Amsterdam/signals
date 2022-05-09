# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0158_alter_question_field_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='area_name',
            field=models.CharField(max_length=256, null=True),
        ),
    ]
