# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaires', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='next_rules',
        ),
        migrations.RemoveField(
            model_name='questionnaire',
            name='first_question',
        ),
        migrations.AlterField(
            model_name='questionnaire',
            name='name',
            field=models.CharField(max_length=255),
        ),
        migrations.CreateModel(
            name='QuestionGraph',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('first_question', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='+',
                    to='questionnaires.question'
                )),
            ],
        ),
        migrations.CreateModel(
            name='Edge',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField(default=0)),
                ('payload', models.JSONField(blank=True, null=True)),
                ('graph', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='edges',
                    to='questionnaires.questiongraph'
                )),
                ('next_question', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='+',
                    to='questionnaires.question'
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
        migrations.AddField(
            model_name='questionnaire',
            name='graph',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='questionnaire',
                to='questionnaires.questiongraph'
            ),
        ),
    ]
