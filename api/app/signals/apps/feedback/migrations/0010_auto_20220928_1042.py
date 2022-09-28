# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam

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
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=255, unique=True)),
                ('text', models.TextField(max_length=1000)),
                ('order', models.IntegerField(blank=True, default=0,
                    help_text='De volgorde van de antwoorden onderwerpen voor het KTP proces.',  # noqa
                    null=True)), # noqa
            ],
            options={
                'verbose_name': 'Standaard antwoord onderwerp',
                'verbose_name_plural': 'Standaard antwoorden onderwerpen',
            },
        ),
        migrations.AddField(
            model_name='standardanswer',
            name='order',
            field=models.IntegerField(blank=True, default=0,
                help_text='De volgorde van de antwoorden tijdens het KTO proces. ' # noqa
                          'Bij een selectie van een onderwerp is de volgorde van het ' # noqa
                          'antwoord binnen het geselecteerde onderwerp.',  # noqa
                null=True), # noqa
        ),
        migrations.AddField(
            model_name='standardanswer',
            name='topic',
            field=models.ForeignKey(blank=True, null=True,
                                    on_delete=django.db.models.deletion.SET_NULL,
                                    to='feedback.standardanswertopic'),
        ),
    ]
