# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from django.db import migrations, models

import signals.apps.signals.models.utils


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0163_category_icon'),
    ]

    operations = [
        migrations.AddField(
            model_name='status',
            name='email_override',
            field=models.EmailField(blank=True, default=None, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='icon',
            field=models.FileField(
                blank=True,
                max_length=255,
                null=True,
                upload_to=signals.apps.signals.models.utils.upload_category_icon_to,
                validators=[signals.apps.signals.models.utils.validate_category_icon]
            ),
        ),
        migrations.AlterField(
            model_name='deletedsignal',
            name='signal_state',
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
                    ('foward to external', 'Doorzetten naar extern'),
                    ('sent', 'Extern: verzonden'),
                    ('send failed', 'Extern: mislukt'),
                    ('done external', 'Extern: afgehandeld'),
                    ('reopen requested', 'Verzoek tot heropenen')
                ],
                editable=False,
                max_length=20
            ),
        ),
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
                    ('foward to external', 'Doorzetten naar extern'),
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
                    ('o', 'Afgehandeld'), ('a', 'Geannuleerd'),
                    ('reopened', 'Heropend'),
                    ('s', 'Gesplitst'),
                    ('closure requested', 'Extern: verzoek tot afhandeling'),
                    ('reaction requested', 'Reactie gevraagd'),
                    ('reaction received', 'Reactie ontvangen'),
                    ('foward to external', 'Doorzetten naar extern'),
                    ('sent', 'Extern: verzonden'),
                    ('send failed', 'Extern: mislukt'),
                    ('done external', 'Extern: afgehandeld'),
                    ('reopen requested', 'Verzoek tot heropenen')
                ],
                max_length=20
            ),
        ),
    ]
