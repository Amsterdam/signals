# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0165_add_status_forward_to_external'),
        ('questionnaires', '0012_text_and_images_as_explanation'),
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
        migrations.AddField(
            model_name='session',
            name='_signal_status',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to='signals.status'
            ),
        ),
        migrations.AddField(
            model_name='session',
            name='invalidated',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='questionnaire',
            name='flow',
            field=models.CharField(
                choices=[
                    ('EXTRA_PROPERTIES', 'Uitvraag'),
                    ('REACTION_REQUEST', 'Reactie gevraagd'),
                    ('FEEDBACK_REQUEST', 'Klanttevredenheidsonderzoek'),
                    ('FORWARD_TO_EXTERNAL', 'Doorzetten naar externe')
                ],
                default='EXTRA_PROPERTIES',
                max_length=255
            ),
        ),
    ]
