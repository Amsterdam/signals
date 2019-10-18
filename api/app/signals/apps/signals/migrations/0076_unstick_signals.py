"""
Fix SIG-1728
"""
from django.db import migrations

from signals.apps.signals.workflow import GEANNULEERD

PROBLEMATIC_SIA_IDS = [
    112099,
    228254,
    235242,
    226580,
    63905,

    161155,
    242526,
    63869,
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
            state=GEANNULEERD,
            text='Vastgelopen melding geannuleerd zonder terugkoppeling aan melder.'
        )
        new_status.save()  # no full_clean, bypass workflow checks
        signal.status = new_status
        signal.save()


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0075_more_category_changes'),
    ]

    operations = [
        migrations.RunPython(_set_state_geannuleerd),
    ]
