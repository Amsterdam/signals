"""
Fix SIG-1502
"""
from django.db import migrations

from signals.apps.signals.workflow import VERZENDEN_MISLUKT

PROBLEMATIC_SIA_IDS = [
    234158,
    230962,
    230957,
    230946,
    230457,
    230181,
    229952,
    211084,
    114289,
    24478,
    9533,
    8469,
]


def _set_state_send_failed(apps, schema_editor):
    """
    Move a Signal to state "send failed" regardless of workflow checks.
    """
    Signal = apps.get_model('signals', 'Signal')
    Status = apps.get_model('signals', 'Status')

    for signal in Signal.objects.filter(id__in=PROBLEMATIC_SIA_IDS):
        new_status = Status(
            _signal=signal,
            state=VERZENDEN_MISLUKT,
            text='Melding vrijgegeven.'
        )
        new_status.save()  # no full_clean
        signal.status = new_status
        signal.save()


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0066_fix_datamodel_extra_properties'),
    ]

    operations = [
        migrations.RunPython(_set_state_send_failed),
    ]
