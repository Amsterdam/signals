# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.db import migrations

drop_signal_filter_view_sql = 'DROP VIEW IF EXISTS "signals_filter_view";'


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0152_auto_20220221_0848'),
    ]

    operations = [
        migrations.RunSQL(sql=drop_signal_filter_view_sql),
    ]
