# Generated by Django 2.2.13 on 2020-07-14 12:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0114_category_changes_SIG-2872'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='area_code',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='location',
            name='area_type',
            field=models.CharField(max_length=256, null=True),
        ),
    ]
