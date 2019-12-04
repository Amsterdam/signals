from django.db import migrations

SIG_1708_NEW_CATEGORIES = {
    'schoon': {
        'drijfvuil-bevaarbaar-water': {
            'name': 'Drijfvuil bevaarbaar water',
            'handling': 'I5DMC',
            'slo': '5W',
            'departments': [
                'WAT',
            ]
        },
        'veegzwerfvuil': {
            'name': 'Veeg- / zwerfvuil',
            'handling': 'A3DEC',
            'slo': '3W',
            'departments': [
                'STW',
            ]
        },
        'prullenbak-vol': {
            'name': 'Prullenbak is vol',
            'handling': 'A3DEC',
            'slo': '3W',
            'departments': [
                'STW',
            ]
        },
        'uitwerpselen': {
            'name': 'Uitwerpselen',
            'handling': 'A3WMC',
            'slo': '21K',
            'departments': [
                'THO',
                'STW',
                'ASC',
            ]
        },
        'gladheid-winterdienst': {
            'name': 'Gladheid winterdienst',
            'handling': 'GLADZC',
            'slo': '3W',
            'departments': [
                'STW',
            ]
        },
        'graffitiwildplak': {
            'name': 'Graffiti / wildplak',
            'handling': 'I5DMC',
            'slo': '5W',
            'departments': [
                'STW',
            ]
        },
    },
    'civiele-constructies': {
        'bruggen': {
            'name': 'Brug',
            'handling': 'A3WEC',
            'slo': '21K',
            'departments': [
                'WAT',
                'STW',
            ]
        },
    },
    'wegen-verkeer-straatmeubilair': {
        'prullenbak-kapot': {
            'name': 'Prullenbak is kapot',
            'handling': 'A3DMC',
            'slo': '3W',
            'departments': [
                'STW',
            ]
        },
    }
}

SIG_1708_ML_TRANSLATION = (
    ('brug',                'bruggen'),
    ('drijfvuil',           'drijfvuil-bevaarbaar-water'),
    ('gladheid',            'gladheid-winterdienst'),
    ('graffiti-wildplak',   'graffitiwildplak'),
    ('prullenbak-is-kapot', 'prullenbak-kapot'),
    ('prullenbak-is-vol',   'prullenbak-vol'),
    ('hondenpoep',          'uitwerpselen'),
    ('veeg-zwerfvuil',      'veegzwerfvuil'),
)

SIG_1708_DEACTIVATE_CATEGORIES = [
    'brug', 'drijfvuil', 'gladheid', 'graffiti-wildplak', 'prullenbak-is-kapot',
    'prullenbak-is-vol', 'hondenpoep', 'veeg-zwerfvuil',
]


def _SIG_1708_new_categories(apps, schema_editor):
    Category = apps.get_model('signals', 'Category')
    Department = apps.get_model('signals', 'Department')
    ServiceLevelObjective = apps.get_model('signals', 'ServiceLevelObjective')

    for main_category_slug, data in SIG_1708_NEW_CATEGORIES.items():
        main_category = Category.objects.get(slug=main_category_slug, parent__isnull=True)

        for category_slug, category_data in data.items():
            category = Category.objects.create(name=category_slug, parent=main_category)  # noqa Using the slug as name to ensure the slug is correctly created

            if 'name' in category_data:
                category.name = category_data['name']
            if 'handling' in category_data:
                category.handling = category_data['handling']

            if 'departments' in category_data:
                departments = Department.objects.filter(name__in=category_data['departments'])
                for department in departments:
                    category.departments.add(department)

            if 'slo' in category_data:
                n_days = int(category_data['slo'][:-1])
                use_calendar_days = True if category_data['slo'][-1] == 'K' else False

                ServiceLevelObjective.objects.create(
                    category=category,
                    n_days=n_days,
                    use_calendar_days=use_calendar_days
                )

            category.save()


def _SIG_1708_ml_translations(apps, schema_editor):
    Category = apps.get_model('signals', 'Category')
    CategoryTranslation = apps.get_model('signals', 'CategoryTranslation')

    for from_slug, to_slug in SIG_1708_ML_TRANSLATION:
        from_category = Category.objects.get(slug=from_slug, parent__isnull=False)
        to_category = Category.objects.get(slug=to_slug, parent__isnull=False)

        CategoryTranslation.objects.create(
            created_by=None,
            text='Omdat er nieuwe categorieën zijn ingevoerd in SIA is er voor de ML tool een tijdelijke vertaling toegevoegd',  # noqa
            old_category=from_category,
            new_category=to_category,
        )


def _SIG_1708_deactivate_categories(apps, schema_editor):
    Category = apps.get_model('signals', 'Category')

    qs = Category.objects.filter(slug__in=SIG_1708_DEACTIVATE_CATEGORIES, parent__isnull=False)
    qs.update(is_active=False)


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0084_auto_20191127_1339'),
    ]

    operations = [
        migrations.RunPython(_SIG_1708_new_categories, None),  # No reverse possible
        migrations.RunPython(_SIG_1708_ml_translations, None),  # No reverse possible
        migrations.RunPython(_SIG_1708_deactivate_categories, None),  # No reverse possible
    ]
