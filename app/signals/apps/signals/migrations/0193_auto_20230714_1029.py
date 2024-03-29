# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
# Generated by Django 3.2.20 on 2023-07-14 08:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0192_auto_20230626_1312'),
    ]

    operations = [
        migrations.AddField(
            model_name='reporter',
            name='email_verification_token',
            field=models.CharField(db_index=True, max_length=120, null=True),
        ),
        migrations.AddField(
            model_name='reporter',
            name='email_verification_token_expires',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='reporter',
            name='email_verified',
            field=models.BooleanField(default=False),
        ),
    ]
