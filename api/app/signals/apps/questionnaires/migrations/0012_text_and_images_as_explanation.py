# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaires', '0011_question_multiple_answer'),
    ]

    operations = [
        migrations.CreateModel(
            name='IllustratedText',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('title', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='StoredFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'file',
                    models.FileField(
                        max_length=255,
                        upload_to='attachments/questionnaires/stored_files/%Y/%m/%d/'
                    )
                ),
            ],
        ),
        migrations.CreateModel(
            name='AttachedSection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('header', models.CharField(blank=True, max_length=255, null=True)),
                ('text', models.TextField(blank=True, null=True)),
                (
                    'illustrated_text',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='sections',
                        to='questionnaires.illustratedtext'
                    )
                ),
            ],
            options={
                'order_with_respect_to': 'illustrated_text',
            },
        ),
        migrations.CreateModel(
            name='AttachedFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('description', models.CharField(blank=True, max_length=255, null=True)),
                (
                    'section',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='files',
                        to='questionnaires.attachedsection'
                    )
                ),
                (
                    'stored_file',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='attached_files',
                        to='questionnaires.storedfile'
                    )
                ),
            ],
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='explanation',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to='questionnaires.illustratedtext'
            ),
        ),
        migrations.AlterField(
            model_name='questionnaire',
            name='flow',
            field=models.CharField(
                choices=[
                    ('EXTRA_PROPERTIES', 'Uitvraag'),
                    ('REACTION_REQUEST', 'Reactie gevraagd'),
                    ('FEEDBACK_REQUEST', 'Klanttevredenheidsonderzoek'),
                    ('FORWARD_TO_EXTERNAL', 'Doorzetten naar externe')
                ],
                default='EXTRA_PROPERTIES',
                max_length=255
            ),
        ),
        migrations.AddField(
            model_name='session',
            name='status',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to='signals.status'
            ),
        ),
        migrations.AddField(
            model_name='session',
            name='invalidated',
            field=models.BooleanField(default=False),
        ),
    ]
