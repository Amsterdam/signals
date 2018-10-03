# Generated by Django 2.1 on 2018-09-18 13:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0011b_rerun_data_migration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='sub_category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                    related_name='category_assignments',
                                    to='signals.SubCategory',
                                    default=76),
        ),
    ]
