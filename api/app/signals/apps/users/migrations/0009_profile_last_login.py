# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
# Generated by Django 3.2.10 on 2021-12-20 12:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_delete_signaluser'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='last_authentication',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
