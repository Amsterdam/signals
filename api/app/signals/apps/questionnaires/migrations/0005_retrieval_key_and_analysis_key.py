# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaires', '0004_alter_questiongraph_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='question',
            old_name='key',
            new_name='retrieval_key',
        ),
        migrations.AddField(
            model_name='question',
            name='analysis_key',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
