"""
Fix SIG-1525
"""
from django.db import migrations

from signals.apps.signals.workflow import VERZENDEN_MISLUKT

PROBLEMATIC_SIA_IDS = [
    250201,
    236810,
    239108,
    240470,
    240487,
    241029,
    241655,
    208934,
    245009,
    245556,
    245455,
    245487,
    245613,
    250333,
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
        ('signals', '0069_stored_signal_filters'),
    ]

    operations = [
        migrations.RunPython(_set_state_send_failed),
    ]
