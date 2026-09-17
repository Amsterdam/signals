# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam

# Django 5.2 includes through_fields when deconstructing a ManyToManyField; earlier
# versions left it out, so it was never recorded in the migration state. Both fields
# already declared through_fields on the model, which makes this a state-only change:
# through_fields only affects how Django resolves the join columns on the through
# model, so no table is altered.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0203_signal_source_index'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='departments',
            field=models.ManyToManyField(
                through='signals.CategoryDepartment',
                through_fields=('category', 'department'),
                to='signals.department',
            ),
        ),
        migrations.AlterField(
            model_name='category',
            name='questions',
            field=models.ManyToManyField(
                through='signals.CategoryQuestion',
                through_fields=('category', 'question'),
                to='signals.question',
            ),
        ),
    ]
