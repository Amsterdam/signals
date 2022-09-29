# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaires', '0012_auto_20220928_2110'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='attachedsection',
            options={'ordering': ['order', 'id']},
        ),
        migrations.AddField(
            model_name='attachedsection',
            name='order',
            field=models.IntegerField(default=0),
        ),
    ]
