# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('questionnaires', '0011_question_multiple_answer'),
    ]

    operations = [
        migrations.CreateModel(
            name='StoredFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(max_length=255, upload_to='questionnaires/%Y/%m/%d/')),
            ],
        ),
        migrations.CreateModel(
            name='AttachedSection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('text', models.TextField()),
                ('object_id', models.PositiveIntegerField()),
                (
                    'content_type', models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='contenttypes.contenttype')
                ),
            ],
        ),
        migrations.CreateModel(
            name='AttachedFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(blank=True, max_length=255, null=True)),
                (
                    'section', models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='attached_files',
                        to='questionnaires.attachedsection'
                    )
                ),
                (
                    'stored_file',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='questionnaires.storedfile'
                    )
                ),
            ],
        ),
        migrations.AddIndex(
            model_name='attachedsection',
            index=models.Index(fields=['content_type', 'object_id'], name='questionnai_content_d90586_idx'),
        ),
    ]
