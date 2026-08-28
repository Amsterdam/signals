# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten

from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('signals', '0202_alter_status_options'),
    ]

    operations = [
        AddIndexConcurrently(
            model_name='signal',
            index=models.Index(fields=['source'], name='signals_sig_source_a75928_idx'),
        ),
    ]
