# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaires', '0006_retrieval_key_and_analysis_key'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='edge',
            name='payload',
        ),
        migrations.AddField(
            model_name='choice',
            name='display',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='choice',
            name='selected',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='edge',
            name='choice',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to='questionnaires.choice'
            ),
        ),
        migrations.AlterField(
            model_name='question',
            name='analysis_key',
            field=models.CharField(default='PLACEHOLDER', max_length=255),
        ),
        migrations.AlterField(
            model_name='question',
            name='field_type',
            field=models.CharField(
                choices=[
                    ('boolean', 'Boolean'),
                    ('integer', 'Integer'),
                    ('plain_text', 'PlainText')
                ],
                max_length=255
            ),
        ),
    ]
