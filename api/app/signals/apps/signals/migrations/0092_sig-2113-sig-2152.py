"""
Fix SIG-2113 and SIG-2152
"""
from django.db import migrations

from signals.apps.signals.workflow import AFGEHANDELD_EXTERN

PROBLEMATIC_SIA_IDS = [
    361100,
]


def _set_state_afgehandeld_extern(apps, schema_editor):
    """
    Move a Signal to state AFGEHANDELD_EXTERN regardless of workflow checks.
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


def _remove_stw_from_verkeerssituaties(apps, schema_editor):
    """
    Change responsible department voor de "Verkeerssituaties" category.
    """
    Category = apps.get_model('signals', 'Category')
    Department = apps.get_model('signals', 'Department')
    CategoryDepartment = apps.get_model('signals', 'CategoryDepartment')

    v_or = Department.objects.get(code='VOR')
    parent = Category.objects.get(slug='wegen-verkeer-straatmeubilair', parent__isnull=True)
    verkeerssituaties = Category.objects.get(slug='verkeerssituaties', parent=parent)

    # clear previous associations, set new one
    verkeerssituaties.departments.clear()
    CategoryDepartment.objects.create(
        category=verkeerssituaties,
        department=v_or,
        is_responsible=True,
        can_view=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0091_unstick_signals'),
    ]

    operations = [
        migrations.RunPython(_set_state_afgehandeld_extern),
        migrations.RunPython(_remove_stw_from_verkeerssituaties)
    ]
