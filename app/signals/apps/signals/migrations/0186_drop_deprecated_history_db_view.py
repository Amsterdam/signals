# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0167_alter_signal_options'),
    ]

    operations = [
        migrations.RunSQL("""
DROP VIEW IF EXISTS "signals_history_view";
"""), ]
