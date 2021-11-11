# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0145_source_is_public'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='can_be_selected',
            field=models.BooleanField(default=True),
        ),
    ]
