# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Vereniging van Nederlandse Gemeenten
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0160_deletedsignal'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='attachment',
            options={
                'ordering': ('created_at',),
                'permissions': [
                    ('sia_delete_attachment_of_normal_signal', 'Kan bijlage bij standaard melding verwijderen.'),
                    ('sia_delete_attachment_of_parent_signal', 'Kan bijlage bij hoofdmelding verwijderen.'),
                    ('sia_delete_attachment_of_child_signal', 'Kan bijlage bij deelmelding verwijderen.'),
                    ('sia_delete_attachment_of_other_user',
                        'Kan bijlage bij melding van andere gebruiker verwijderen.'),
                    ('sia_delete_attachment_of_anonymous_user', 'Kan bijlage toegevoegd door melder verwijderen.')
                ]
            },
        ),
    ]
