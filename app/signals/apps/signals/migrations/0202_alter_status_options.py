# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0201_alter_area_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='status',
            options={
                'get_latest_by': 'datetime',
                'ordering': ('created_at',),
                'permissions': (
                    ('push_to_sigmax', 'Doorsturen van een melding (THOR)'),
                    ('sia_status_updates_read', 'Statusupdates lezen'),
                ),
                'verbose_name_plural': 'Statuses',
            },
        ),
    ]
