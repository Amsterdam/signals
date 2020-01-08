"""
Fix SIG-2069
"""
from django.db import migrations

from signals.apps.signals.workflow import AFGEHANDELD_EXTERN

PROBLEMATIC_SIA_IDS = [
    344461,
    361100
]


def _set_state_afgehandeld_extern(apps, schema_editor):
    """
    Move a Signal to state geannuleerd (code "a") regardless of workflow checks.
    """
    Signal = apps.get_model('signals', 'Signal')
    Status = apps.get_model('signals', 'Status')

    for signal in Signal.objects.filter(id__in=PROBLEMATIC_SIA_IDS):
        new_status = Status(
            _signal=signal,
            state=AFGEHANDELD_EXTERN,
            text='Vastgelopen melding vrijgegeven zonder tussenkomst CityControl.'
        )
        new_status.save()  # no full_clean, bypass workflow checks
        signal.status = new_status
        signal.save()


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0085_auto_20191216_1251'),
    ]

    operations = [
        migrations.RunPython(_set_state_afgehandeld_extern),
    ]
