# Generated by Django 2.2.13 on 2020-09-08 16:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0125_update_history_after_directing_dept_remove'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='signal',
            name='department_assignment',
        ),
        migrations.RemoveField(
            model_name='signal',
            name='user_assignment',
        ),
    ]
