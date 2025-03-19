# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Gemeente Amsterdam
# Generated by Django 4.2.20 on 2025-03-19 10:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0200_alter_areatype_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='area',
            options={
                'ordering': ['_type', 'code'],
                'permissions': (('sia_area_write', 'Kan gebieden schrijven.'),),
                'verbose_name': 'Gebied',
                'verbose_name_plural': 'Gebieden'
            },
        ),
    ]
