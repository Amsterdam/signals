"""
Category changes SIG-2627.
"""
from django.db import migrations

# SIG-2555
NEW_CATEGORIES = {
    'overlast-van-dieren': {
        'ratten-in-en-rond-woning': {
            'name': 'Ratten – in en rond een woning',
            'handling': 'I5DMC',
            'handling_message':
                'Wij laten u binnen 5 werkdagen weten wat wij met uw melding gaan doen. '
                'Wij melden u ook wanneer we dat gaan doen. Dit doen we via e-mail, '
                'als u een mailadres hebt opgegeven.',
            'departments': ['GGD'],
            'slo': '5W',
        }
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


class Migration(migrations.Migration):
    dependencies = [
        ('signals', '0106_auto_20200422_2337'),
    ]

    operations = [
        migrations.RunPython(_new_categories, None),  # No reverse possible
    ]
