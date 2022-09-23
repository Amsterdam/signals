# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0009_feedback_text_list'),
    ]

    operations = [
        migrations.CreateModel(
            name='StandardAnswerTopic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('text', models.TextField(max_length=1000)),
                ('order', models.IntegerField(blank=True, default=0, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='standardanswer',
            name='order',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='standardanswer',
            name='topic',
            field=models.ForeignKey(blank=True, null=True,
                                    on_delete=django.db.models.deletion.SET_NULL,
                                    to='feedback.standardanswertopic'),
        ),
    ]
