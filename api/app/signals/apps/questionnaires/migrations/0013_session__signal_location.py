# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0165_add_status_forward_to_external'),
        ('questionnaires', '0012_forward_to_external_flow_changes'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='_signal_location',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to='signals.location'
            ),
        ),
    ]
