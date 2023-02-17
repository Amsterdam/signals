# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0141_workflow_additions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='status',
            name='state',
            field=models.CharField(
                blank=True,
                choices=[
                    ('m', 'Gemeld'),
                    ('i', 'In afwachting van behandeling'),
                    ('b', 'In behandeling'),
                    ('h', 'On hold'),
                    ('ingepland', 'Ingepland'),
                    ('ready to send', 'Extern: te verzenden'),
                    ('o', 'Afgehandeld'),
                    ('a', 'Geannuleerd'),
                    ('reopened', 'Heropend'),
                    ('s', 'Gesplitst'),
                    ('closure requested', 'Extern: verzoek tot afhandeling'),
                    ('reaction requested', 'Reactie gevraagd'),
                    ('reaction received', 'Reactie ontvangen'),
                    ('sent', 'Extern: verzonden'),
                    ('send failed', 'Extern: mislukt'),
                    ('done external', 'Extern: afgehandeld'),
                    ('reopen requested', 'Verzoek tot heropenen')
                ],
                default='m',
                help_text='Melding status',
                max_length=20
            ),
        ),
        migrations.AlterField(
            model_name='statusmessagetemplate',
            name='state',
            field=models.CharField(
                choices=[
                    ('m', 'Gemeld'),
                    ('i', 'In afwachting van behandeling'),
                    ('b', 'In behandeling'),
                    ('h', 'On hold'),
                    ('ingepland', 'Ingepland'),
                    ('ready to send', 'Extern: te verzenden'),
                    ('o', 'Afgehandeld'),
                    ('a', 'Geannuleerd'),
                    ('reopened', 'Heropend'),
                    ('s', 'Gesplitst'),
                    ('closure requested', 'Extern: verzoek tot afhandeling'),
                    ('reaction requested', 'Reactie gevraagd'),
                    ('reaction received', 'Reactie ontvangen'),
                    ('sent', 'Extern: verzonden'),
                    ('send failed', 'Extern: mislukt'),
                    ('done external', 'Extern: afgehandeld'),
                    ('reopen requested', 'Verzoek tot heropenen')
                ],
                max_length=20
            ),
        ),
    ]
