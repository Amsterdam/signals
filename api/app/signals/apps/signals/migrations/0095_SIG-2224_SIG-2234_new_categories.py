"""
Added new categories according to tickets SIG-2224 & SGI-2234
"""

from django.db import migrations

NEW_CATEGORIES = {
    # SIG-2224
    'civiele-constructies': {
        'sluis': {  # SIG-2224
            'name': 'Sluis',
            'handling': 'URGENTE_MELDINGEN',
            'slo': '5W',
            'departments': [
                'STW',
                'VOR',
            ]
        },
        'watergangen': {  # SIG-2224
            'name': 'Watergangen',
            'handling': 'URGENTE_MELDINGEN',
            'slo': '5W',
            'departments': [
                'STW',
                'VOR',
            ]
        },
        'afwatering-brug': {  # SIG-2224
            'name': 'Afwatering brug',
            'handling': 'URGENTE_MELDINGEN',
            'slo': '5W',
            'departments': [
                'STW',
                'VOR',
            ]
        },
    },
    # SIG-2234
    'wegen-verkeer-straatmeubilair': {
        'omleiding': {  # SIG-2234
            'name': 'Omleiding',
            'handling': 'A3WEC',
            'slo': '15K',
            'departments': [
                'STW',
            ]
        },
    }
}


def _new_categories(apps, schema_editor):
    Category = apps.get_model('signals', 'Category')
    Department = apps.get_model('signals', 'Department')
    ServiceLevelObjective = apps.get_model('signals', 'ServiceLevelObjective')

    for main_category_slug, data in NEW_CATEGORIES.items():
        main_category = Category.objects.get(slug=main_category_slug, parent__isnull=True)

        for category_slug, category_data in data.items():
            category = Category.objects.create(name=category_slug, parent=main_category)  # noqa Using the slug as name to ensure the slug is correctly created

            category.name = category_data['name']
            category.handling = category_data['handling']

            departments = Department.objects.filter(code__in=category_data['departments'])
            category.departments.add(*departments, through_defaults={'is_responsible': True, 'can_view': True})

            n_days = int(category_data['slo'][:-1])
            use_calendar_days = True if category_data['slo'][-1] == 'K' else False

            ServiceLevelObjective.objects.create(category=category, n_days=n_days,
                                                 use_calendar_days=use_calendar_days)

            category.save()


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0095_SIG-1708_part-1'),
    ]

    operations = [
        migrations.RunPython(_new_categories, None),  # No reverse possible
    ]
