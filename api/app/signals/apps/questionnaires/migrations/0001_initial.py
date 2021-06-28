# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import datetime
import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('signals', '0141_workflow_additions'),
    ]

    operations = [
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('label', models.CharField(max_length=255)),
                ('short_label', models.CharField(max_length=255)),
                ('field_type', models.CharField(
                    choices=[('integer', 'Integer'), ('plain_text', 'PlainText'), ('submit', 'Submit')],
                    max_length=255
                )),
                ('next_rules', models.JSONField(blank=True, null=True)),
                ('required', models.BooleanField(default=False)),
                ('root', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='+',
                    to='questionnaires.question'
                )),
            ],
        ),
        migrations.CreateModel(
            name='Questionnaire',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('flow', models.CharField(
                    choices=[
                        ('EXTRA_PROPERTIES', 'Uitvraag'),
                        ('REACTION_REQUEST', 'Reactie gevraagd'),
                        ('FEEDBACK_REQUEST', 'Klanttevredenheidsonderzoek')
                    ],
                    default='EXTRA_PROPERTIES',
                    max_length=255
                )),
                ('name', models.CharField(
                    help_text='The name of the Questionnaire',
                    max_length=255
                )),
                ('description', models.TextField(blank=True, help_text='Describe the Questionnaire', null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('first_question', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='+',
                    to='questionnaires.question'
                )),
            ],
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('submit_before', models.DateTimeField(blank=True, null=True)),
                ('duration', models.DurationField(default=datetime.timedelta(seconds=7200))),
                ('frozen', models.BooleanField(default=False)),
                ('_signal', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    to='signals.signal'
                )),
                ('questionnaire', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='+',
                    to='questionnaires.questionnaire'
                )),
            ],
        ),
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('payload', models.JSONField(blank=True, null=True)),
                ('question', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='+',
                    to='questionnaires.question'
                )),
                ('session', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='answers',
                    to='questionnaires.session'
                )),
            ],
        ),
    ]
