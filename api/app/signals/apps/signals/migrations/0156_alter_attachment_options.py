# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from django.db import migrations


def _change_permission(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')

    permissions_to_change = (
        ('sia_delete_attachment_of_normal_signal', 'Kan bijlage bij standaard melding verwijderen.'),
        ('sia_delete_attachment_of_parent_signal', 'Kan bijlage bij hoofdmelding verwijderen.'),
        ('sia_delete_attachment_of_child_signal', 'Kan bijlage bij deelmelding verwijderen.'),
        ('sia_delete_attachment_of_other_user', 'Kan bijlage bij melding van andere gebruiker verwijderen.')
    )

    for codename, name in permissions_to_change:
        try:
            permission = Permission.objects.get(codename=codename)
            permission.name = name
            permission.save()
        except Permission.DoesNotExist:
            # Test suite fails if we do not catch these exceptions
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0155_alter_attachment_options'),
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
                    ('sia_delete_attachment_of_other_user', 'Kan bijlage bij melding van andere gebruiker verwijderen.')
                ]
            },
        ),
        migrations.RunPython(_change_permission, lambda x, y: True),  # Reverse function does nothing
    ]
