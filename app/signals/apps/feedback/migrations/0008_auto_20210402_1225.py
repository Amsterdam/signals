# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0007_auto_20190611_1126'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='feedback',
            options={'ordering': ('_signal', '-created_at')},
        ),
    ]
