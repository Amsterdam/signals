# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaires', '0002_auto_20210719_0131'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='enforce_choices',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='question',
            name='field_type',
            field=models.CharField(choices=[('integer', 'Integer'), ('plain_text', 'PlainText')], max_length=255),
        ),
        migrations.CreateModel(
            name='Choice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payload', models.JSONField(blank=True, null=True)),
                ('question', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='choices',
                    to='questionnaires.question'
                )),
            ],
        ),
    ]
