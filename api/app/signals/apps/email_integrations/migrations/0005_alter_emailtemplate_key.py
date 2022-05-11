# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email_integrations', '0004_alter_emailtemplate_key'),
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
                ('signal_status_changed_reactie_ontvangen', 'Send mail signal reaction requested received'),
                ('signal_status_changed_afgehandeld_kto_negative_contact', 'Send mail signal '),
                ('signal_feedback_received', 'Send mail signal feedback received')], db_index=True, max_length=100),
        ),
    ]
