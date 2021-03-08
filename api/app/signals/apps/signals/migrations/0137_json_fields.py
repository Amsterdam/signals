from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0136_categoryassignment_stored_handling_message_and_HISTORY'),
    ]

    operations = [
        migrations.AlterField(
            model_name='categoryassignment',
            name='extra_properties',
            field=models.JSONField(null=True),
        ),
        migrations.AlterField(
            model_name='location',
            name='address',
            field=models.JSONField(null=True),
        ),
        migrations.AlterField(
            model_name='location',
            name='extra_properties',
            field=models.JSONField(null=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='meta',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='signal',
            name='extra_properties',
            field=models.JSONField(null=True),
        ),
        migrations.AlterField(
            model_name='status',
            name='extra_properties',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='storedsignalfilter',
            name='options',
            field=models.JSONField(default=dict),
        ),
    ]
