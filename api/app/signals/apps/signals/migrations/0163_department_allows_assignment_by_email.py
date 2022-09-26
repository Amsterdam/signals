# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Gemeente Amsterdam
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0162_signal_user_HISTORY'),
    ]

    operations = [
        migrations.AddField(
            model_name='department',
            name='allows_assignment_by_email',
            field=models.BooleanField(default=False),
        ),
    ]
