# Generated by Django 3.2.5 on 2021-07-27 12:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0142_auto_20210727_1406'),
    ]

    operations = [
        migrations.RenameField(
            model_name='routingexpression',
            old_name='_user',
            new_name='employee',
        ),
    ]
