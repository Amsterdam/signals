# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Vereniging van Nederlandse Gemeenten

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0166_rename_status_forward_to_external'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='signal',
            options={
                'ordering': ('created_at',),
                'permissions': (
                    ('sia_read', 'Leesrechten algemeen'),
                    ('sia_write', 'Schrijfrechten algemeen'),
                    ('sia_split', 'Splitsen van een melding'),
                    ('sia_signal_create_initial', 'Melding aanmaken'),
                    ('sia_signal_create_note', 'Notitie toevoegen bij een melding'),
                    ('sia_signal_change_status', 'Wijzigen van status van een melding'),
                    ('sia_signal_change_category', 'Wijzigen van categorie van een melding'),
                    ('sia_signal_export', 'Meldingen exporteren'), ('sia_signal_report', 'Rapportage beheren'),
                    ('perform_sigmax_updates', 'Updates door CityControl uitvoeren')
                )
            },
        ),
    ]
