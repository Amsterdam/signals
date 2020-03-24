from textwrap import dedent

from django.db import migrations, models

from signals.apps.email_integrations.core.messages import ALL_AFHANDELING_TEXT


def _add_handling_message(apps, schema_editor):
    # SIG-2402
    # Adds the correct text from the ALL_AFHANDELING_TEXT based on the current category.handling
    Category = apps.get_model('signals', 'Category')

    for category in Category.objects.all():
        if category.handling in ALL_AFHANDELING_TEXT:
            category.handling_message = dedent(ALL_AFHANDELING_TEXT[category.handling])
            category.save()


def _set_handling_message_to_none(apps, schema_editor):
    Category = apps.get_model('signals', 'Category')
    Category.objects.update(handling_message=None)


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0101_default_type_and_history_view'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='handling_message',
            field=models.TextField(blank=True, null=True),
        ),

        # SIG-2402 Adds the correct text from the ALL_AFHANDELING_TEXT based on the current category.handling
        migrations.RunPython(_add_handling_message, _set_handling_message_to_none),
    ]
