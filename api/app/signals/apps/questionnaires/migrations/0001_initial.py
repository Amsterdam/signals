# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('field_type', models.CharField(
                    choices=[('integer', 'Integer'), ('plain_text', 'PlainText')], max_length=255)),
                ('payload', models.JSONField(blank=True, null=True)),
                ('required', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Questionnaire',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('first_question', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.CASCADE, to='questionnaires.question')),
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
                ('ttl_seconds', models.IntegerField(default=7200)),
                ('frozen', models.BooleanField(default=False)),
                ('questionnaire', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.CASCADE, to='questionnaires.questionnaire')),
            ],
        ),
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('answer', models.JSONField(blank=True)),
                ('question', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.CASCADE, to='questionnaires.question')),
                ('session', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.CASCADE, to='questionnaires.session')),
            ],
        ),
    ]
