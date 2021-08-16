# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0142_auto_20210719_0057'),
    ]

    operations = [
        migrations.AddField(
            model_name='storedsignalfilter',
            name='show_on_overview',
            field=models.BooleanField(default=False),
        ),
    ]
