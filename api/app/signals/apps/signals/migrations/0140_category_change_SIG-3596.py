# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.db import migrations


def SIG_3596(apps, schema_editor):
    Category = apps.get_model('signals', 'Category')
    Department = apps.get_model('signals', 'Department')
    ServiceLevelObjective = apps.get_model('signals', 'ServiceLevelObjective')

    try:
        old_main_category = Category.objects.get(slug='wegen-verkeer-straatmeubilair', parent__isnull=True)
        old_category = Category.objects.get(slug='put-riolering-verstopt', parent_id=old_main_category.pk)

        new_main_category = Category.objects.get(slug='schoon', parent__isnull=True)
    except Category.DoesNotExist:
        return

    new_category = Category.objects.create(name='putrioleringverstopt', parent=new_main_category)
    new_category.name = 'Put / riolering verstopt'
    new_category.handling = 'I5DMC'
    new_category.handling_message = 'Uw melding wordt ingepland: wij laten u binnen 5 werkdagen weten hoe en wanneer ' \
                                    'uw melding wordt afgehandeld. Dat doen we via e-mail.'

    responsible_departments = Department.objects.filter(code__in=['ASC', 'CCA', 'STW', ])
    new_category.departments.add(*responsible_departments, through_defaults={'is_responsible': True, 'can_view': True})
    new_category.save()

    ServiceLevelObjective.objects.create(category=new_category, n_days=5, use_calendar_days=False)

    old_category.is_active = False
    old_category.save()


class Migration(migrations.Migration):
    dependencies = [
        ('signals', '0139_json_fields'),
    ]

    operations = [
        migrations.RunPython(SIG_3596, None),  # No reverse possible
    ]
