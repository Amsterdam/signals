"""
Fix SIG-1771
"""
from django.db import migrations

from signals.apps.signals.workflow import GESPLITST

PROBLEMATIC_SIA_IDS = [
    225231,
    223988,
]


def _set_state_geannuleerd(apps, schema_editor):
    """
    Move a Signal to state geannuleerd (code "a") regardless of workflow checks.
    """
    Signal = apps.get_model('signals', 'Signal')
    Status = apps.get_model('signals', 'Status')

    for signal in Signal.objects.filter(id__in=PROBLEMATIC_SIA_IDS):
        new_status = Status(
            _signal=signal,
            state=GESPLITST,
            text='Vastgelopen melding alsnog naar status gesplitst.'
        )
        new_status.save()  # no full_clean, bypass workflow checks
        signal.status = new_status
        signal.save()


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0076_unstick_signals'),
    ]

    operations = [
        migrations.RunPython(_set_state_geannuleerd),
    ]
