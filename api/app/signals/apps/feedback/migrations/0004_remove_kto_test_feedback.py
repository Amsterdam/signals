"""
For testing purposes we added a few Feedback instances to the database. Now we remove them

Note: we re-use the Signal entries 1000 up to 1005.
"""

from django.db import migrations


def remove_test_feedback(apps, schema_editor):
    Feedback = apps.get_model('feedback', 'Feedback')
    feedback_qs = Feedback.objects.filter(_signal__id__gte=1000, _signal__id__lt=1005)
    feedback_qs.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0003_add_kto_test_feedback'),
    ]

    operations = [
        migrations.RunPython(remove_test_feedback),
    ]
