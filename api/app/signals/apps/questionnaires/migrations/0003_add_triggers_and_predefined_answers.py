# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaires', '0002_rework_using_question_graphs'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='enforce_choices',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='InfoTrigger',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payload', models.JSONField(blank=True, null=True)),
                ('order', models.IntegerField(default=0)),
                ('title', models.CharField(max_length=255)),
                ('information', models.TextField()),
                ('graph', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='info_triggers',
                    to='questionnaires.questiongraph'
                )),
                ('question', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='+',
                    to='questionnaires.question'
                )),
            ],
            options={
                'ordering': ['order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ActionTrigger',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payload', models.JSONField(blank=True, null=True)),
                ('order', models.IntegerField(default=0)),
                ('action', models.CharField(choices=[('reopen signal', 'Melding heropenen')], max_length=255)),
                ('arguments', models.JSONField(blank=True, null=True)),
                ('graph', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='action_triggers',
                    to='questionnaires.questiongraph'
                )),
                ('question', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='+',
                    to='questionnaires.question'
                )),
            ],
            options={
                'ordering': ['order', 'id'],
            },
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
            options={
                'order_with_respect_to': 'question',
            },
        ),
    ]
