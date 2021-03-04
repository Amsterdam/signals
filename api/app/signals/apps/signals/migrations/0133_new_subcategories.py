# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
"""
Category changes SIG-3491

New subcategories for 'Onderhoud fietspad' and 'Put / Riool kapot'
"""
from django.db import migrations

# SIG-3491
NEW_CATEGORIES = {
    'wegen-verkeer-straatmeubilair': {
        'onderhoud-fietspad': {
            'name': 'Onderhoud fietspad',
            'description': 'Verzakkingen in/van fietspad, missende tegels, wortelopdruk in het fietspad, scheuren in '
                           'fietspad',
            'handling': 'A3DEC',
            'handling_message':
                'Wij handelen uw melding binnen een week af. '
                'Als u een mailadres hebt opgegeven, zullen we u op de hoogte houden.',
            'departments': ['STW'],
            'slo': '5W',
        },
        'put-riool-kapot': {
            'name': 'Put / Riool kapot',
            'description': 'Meldingen die betrekking hebben op een kapotte kolk en riolering.',
            'handling': 'A3DEC',
            'handling_message':
                'Uw melding wordt ingepland: wij laten u binnen 5 werkdagen weten hoe en wanneer uw melding wordt '
                'afgehandeld.  Als u een mailadres hebt opgegeven, zullen we u op de hoogte houden.',
            'departments': ['STW'],
            'slo': '5W',
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
                category = Category.objects.create(name=category_slug, parent=main_category)  # noqa Using the slug as name to ensure the slug is correctly created

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
        ('signals', '0132_signaluser_HISTORY'),
    ]

    operations = [
        migrations.RunPython(_new_categories, None),  # No reverse possible
    ]
