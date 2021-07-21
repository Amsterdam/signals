# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.db import migrations, models


def migrate_submit_question(apps, schema_editor):
    """
    Set label and short_label of submit question to None.
    """
    # SIG-3911
    Question = apps.get_model('questionnaires', 'Question')
    try:
        q = Question.objects.get(key='submit')
    except Question.DoesNotExist:
        Question.objects.create(
            key='submit',
            field_type='submit',
            label=None,
            short_label=None,
            required=True
        )
    else:
        q.field_type = 'submit'
        q.label = None
        q.short_label = None
        q.required = True
        q.save()


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaires', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='label',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='short_label',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.RunPython(migrate_submit_question),
    ]
