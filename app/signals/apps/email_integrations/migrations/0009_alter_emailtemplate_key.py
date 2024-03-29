# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
# Generated by Django 3.2.18 on 2023-03-23 11:45
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email_integrations', '0008_alter_emailtemplate_key'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailtemplate',
            name='key',
            field=models.CharField(choices=[
                ('signal_created', 'Send mail signal created'),
                ('signal_status_changed_afgehandeld', 'Send mail signal handled'),
                ('signal_status_changed_ingepland', 'Send mail signal scheduled'),
                ('signal_status_changed_heropend', 'Send mail signal reopened'),
                ('signal_status_changed_optional', 'Send mail optional'),
                ('signal_status_changed_reactie_gevraagd', 'Send mail signal reaction requested'),
                ('signal_status_changed_reactie_ontvangen', 'Send mail signal reaction requested received'),
                ('signal_status_changed_afgehandeld_kto_negative_contact', 'Send mail signal negative KTO contact'),
                ('signal_forward_to_external', 'Send mail signal forwarded to external'),
                ('signal_assigned', 'Send mail signal assigned'),
                ('signal_feedback_received', 'Send mail signal feedback received'),
                ('signal_forward_to_external_reaction_received', 'Send mail forwarded to external reaction received'),
                ('my_signal_token', 'Send mail when a My Signals token has been requested')
            ], db_index=True, max_length=100, unique=True),
        ),
    ]
