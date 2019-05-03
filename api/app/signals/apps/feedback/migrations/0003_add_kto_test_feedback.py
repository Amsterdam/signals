"""
For testing purposes we add a few Feedback instances to the database.

Note: we re-use the Signal entries 1000 up to 1005.
"""

import datetime

from django.db import migrations


def add_test_feedback(apps, schema_editor):
    Feedback = apps.get_model('feedback', 'Feedback')
    Signal = apps.get_model('signals', 'Signal')

    # Grab Signal instances 1000 up to 1005, re-use them for test.
    signal_qs = Signal.objects.filter(id__gte=1000, id__lt=1005)

    for i, signal in enumerate(signal_qs):
        test_feedback = Feedback(
            _signal=signal,
            is_satisfied=(i % 2 == 0),
            allows_contact=(i % 2 != 0),
            text='Tevreden want dit is een TEST.',
            text_extra='Extra uitleg.\n\nKan heel lang zijn en newlines bevatten.',
            submitted_at=datetime.datetime(2019, 4, 29, 18, 0, 0),
        )
        test_feedback.save()


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0002_auto_20190409_1517'),
    ]

    operations = [
        migrations.RunPython(add_test_feedback),
    ]
