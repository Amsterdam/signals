# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Delta10 B.V.
# Generated by Django 3.2.15 on 2022-10-24 21:35
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('signals', '0162_signal_user_HISTORY'),
    ]

    operations = [
        migrations.CreateModel(
            name='Case',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_id', models.CharField(db_index=True, max_length=100)),
                ('_signal', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='zgw_case',
                    to='signals.signal'
                )),
            ],
        ),
    ]