# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('signals', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                                   to='contenttypes.contenttype')),
                ('object_pk', models.CharField(db_index=True, max_length=128)),
                ('action', models.CharField(choices=[('UNKNOWN', 'Unknown'),
                                                     ('CREATE', 'Created'),
                                                     ('UPDATE', 'Updated'),
                                                     ('DELETE', 'Deleted'),
                                                     ('RECEIVE', 'Received')],
                                            default='UNKNOWN', editable=False, max_length=16)),
                ('description', models.TextField(blank=True, max_length=3000, null=True)),
                ('extra', models.TextField(blank=True, max_length=255, null=True)),
                ('created_by', models.EmailField(blank=True, max_length=254, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('_signal', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING,
                                              related_name='history_log', to='signals.signal')),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
        migrations.AddIndex(
            model_name='Log',
            index=models.Index(
                fields=[
                    'content_type',
                    'object_pk'
                ],
                name='history_log_content_2ce2f5_idx'
            ),
        ),
    ]
