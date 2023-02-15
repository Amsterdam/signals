# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
"""
Category changes SIG-4387

New subcategories for:
    - Container bijplaatsing
    - Rolcontainer is kapot
    - Rolcontainer is vol
"""
from django.db import migrations

# SIG-4387
NEW_CATEGORIES = {
    'afval': {
        'container-bijplaatsing': {
            'name': 'Container bijplaatsing',
            'description': 'Meldingen bijplaatsing naast container',
            'handling': 'A3DMC',
            'handling_message':
                'Wij gaan aan het werk met uw melding. '
                'Als het dringend is komen we direct in actie. '
                'U hoort binnen 3 werkdagen wat wij hebben gedaan.',
            'departments': ['AEG'],
            'slo': '3W',
        },
        'rolcontainer-is-kapot': {
            'name': 'Rolcontainer is kapot',
            'description': 'Aanvragen rolcontainer(s) bewoners, defecte rolcontainer(s) bewoners, wisselen '
                           'rolcontainer(s) bewoners',
            'handling': 'EMPTY',
            'handling_message':
                'Wij gaan aan het werk met uw melding. '
                'Als het dringend is komen we direct in actie. '
                'U hoort binnen 10 werkdagen wat wij hebben gedaan.',
            'departments': ['AEG'],
            'slo': '10W',
        },
        'rolcontainer-is-vol': {
            'name': 'Rolcontainer is vol',
            'description': 'Meldingen rolcontainer(s) bewoners  vol/niet geleegd.',
            'handling': 'A3DMC',
            'handling_message':
                'Wij gaan aan het werk met uw melding. '
                'Als het dringend is komen we direct in actie. '
                'U hoort binnen 3 werkdagen wat wij hebben gedaan.',
            'departments': ['AEG'],
            'slo': '3W',
        }
    }
}


def _new_categories(apps, schema_editor):
    Category = apps.get_model('signals', 'Category')
    Department = apps.get_model('signals', 'Department')
    ServiceLevelObjective = apps.get_model('signals', 'ServiceLevelObjective')

    for main_category_slug, data in NEW_CATEGORIES.items():
        try:
            main_category = Category.objects.get(slug=main_category_slug, parent__isnull=True)

            for category_slug, category_data in data.items():
                category = Category.objects.create(name=category_slug, parent=main_category, is_active=False)  # noqa Using the slug as name to ensure the slug is correctly created

                category.name = category_data['name']
                category.description = category_data['description']
                category.handling = category_data['handling']
                category.handling_message = category_data['handling_message']

                responsible_deps = Department.objects.filter(code__in=category_data['departments'])
                category.departments.add(*responsible_deps, through_defaults={'is_responsible': True, 'can_view': True})
                # all departments have visibility on these categories, hence:
                can_view_deps = Department.objects.exclude(code__in=category_data['departments'])
                category.departments.add(*can_view_deps, through_defaults={'is_responsible': False, 'can_view': True})

                n_days = int(category_data['slo'][:-1])
                use_calendar_days = True if category_data['slo'][-1] == 'K' else False

                ServiceLevelObjective.objects.create(category=category, n_days=n_days,
                                                     use_calendar_days=use_calendar_days)

                category.save()
        except Category.DoesNotExist:
            # don't fail if category does not exists
            pass


class Migration(migrations.Migration):
    dependencies = [
        ('signals', '0150_category_questionnaire'),
    ]

    operations = [
        migrations.RunPython(_new_categories, None),  # No reverse possible
    ]
