"""
PART 1 of the SIG-1708 New categories

In overleg met Arvid is besloten om dit in 2 delen op te pakken. Er worden 5 nieuwe categorieen toegevoegd en hiervoor
zal de bulk actie voor hercategorisering plaatsvinden.

Het eerste deel bevat de volgende categorieën:
    * Drijfvuil bevaarbaar water
    * Uitwerpselen
    * Gladheid winterdienst
    * Graffiti / wildplak
    * Brug
"""

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
}

SIG_1708_ML_TRANSLATION = (
    ('brug',                'bruggen'),
    ('drijfvuil',           'drijfvuil-bevaarbaar-water'),
    ('gladheid',            'gladheid-winterdienst'),
    ('graffiti-wildplak',   'graffitiwildplak'),
    ('hondenpoep',          'uitwerpselen'),
)

SIG_1708_DEACTIVATE_CATEGORIES = [
    'brug', 'drijfvuil', 'gladheid', 'graffiti-wildplak', 'hondenpoep',
]


def _SIG_1708_new_categories(apps, schema_editor):
    Category = apps.get_model('signals', 'Category')
    Department = apps.get_model('signals', 'Department')
    ServiceLevelObjective = apps.get_model('signals', 'ServiceLevelObjective')

    for main_category_slug, data in SIG_1708_NEW_CATEGORIES.items():
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
        ('signals', '0094_SIG-2170_new_categories'),
    ]

    operations = [
        migrations.RunPython(_SIG_1708_new_categories, None),  # No reverse possible
        migrations.RunPython(_SIG_1708_ml_translations, None),  # No reverse possible
        migrations.RunPython(_SIG_1708_deactivate_categories, None),  # No reverse possible
    ]
