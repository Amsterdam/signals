# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam

import django_fsm
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0191_alter_statusmessagecategory_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='reporter',
            name='state',
            field=django_fsm.FSMField(default='new', max_length=50, protected=True),
        ),
    ]
