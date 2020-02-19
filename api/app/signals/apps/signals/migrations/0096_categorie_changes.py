"""
Combination of tickets that all include category changes

SIG-2242, SIG-2232, SIG-2231 & SIG-2169
"""

from django.db import migrations

NEW_CATEGORIES = {
    'civiele-constructies': {
            'oevers': {  # noqa SIG-2232: Oevers (stond in: Openbaar Groen en Water) naar Hoofdcategorie Civiele Constructie
                'name': 'Oevers',
                'handling': 'I5DMC',
                'slo': '5W',
                'departments': [
                    'STW',
                ]
            },
    },
    'schoon': {
        'veegzwerfvuil': {  # SIG-2242 Verplaats: Veeg- / zwerfvuil naar Schoon
            'name': 'Veeg- / zwerfvuil',
            'handling': 'A3DEC',
            'slo': '3W',
            'departments': [
                'STW',
            ]
        },
        'prullenbak-vol': {  # SIG-2242 Verplaats: Prullenbak is vol naar Schoon
            'name': 'Prullenbak is vol',
            'handling': 'A3DEC',
            'slo': '3W',
            'departments': [
                'STW',
            ]
        },
        'prullenbak-kapot': {  # noqa SIG-2242 Verplaats: Prullenbak is kapot (was: Afval) naar Wegen, Verkeer en Straatmeubilair
            'name': 'Prullenbak is kapot',
            'handling': 'A3DEC',
            'slo': '3W',
            'departments': [
                'STW',
            ]
        },
    },
}

ML_TRANSLATION = (
    ('oever-kade-steiger', 'oevers'),  # noqa SIG-2232: Oevers (stond in: Openbaar Groen en Water) naar Hoofdcategorie Civiele Constructie
    ('veeg-zwerfvuil', 'veegzwerfvuil'),  # SIG-2242 Verplaats: Veeg- / zwerfvuil naar Schoon
    ('prullenbak-is-vol', 'prullenbak-vol'),  # SIG-2242 Verplaats: Prullenbak is vol naar Schoon
    ('prullenbak-is-kapot', 'prullenbak-kapot'),  # noqa SIG-2242 Verplaats: Prullenbak is kapot (was: Afval) naar Wegen, Verkeer en Straatmeubilair
)

DEACTIVATE_CATEGORIES = [
    'verzakking-kades',  # noqa SIG-2231 VERWIJDER: Verzakking van kades (is dubbel). Overzetten naar Kademuren (die is hernoemd in deze sprint)
    'boom-spiegel',  # SIG-2169 Verwijder: Boom – spiegel (meldingen naar Boom - overig)
    'oever-kade-steiger',  # noqa SIG-2232: Oevers (stond in: Openbaar Groen en Water) naar Hoofdcategorie Civiele Constructie
    'veeg-zwerfvuil',  # SIG-2242 Verplaats: Veeg- / zwerfvuil naar Schoon
    'prullenbak-is-vol',  # SIG-2242 Verplaats: Prullenbak is vol naar Schoon
    'prullenbak-is-kapot',  # noqa SIG-2242 Verplaats: Prullenbak is kapot (was: Afval) naar Wegen, Verkeer en Straatmeubilair
]


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


def _ml_translations(apps, schema_editor):
    Category = apps.get_model('signals', 'Category')
    CategoryTranslation = apps.get_model('signals', 'CategoryTranslation')

    for from_slug, to_slug in ML_TRANSLATION:
        from_category = Category.objects.get(slug=from_slug, parent__isnull=False)
        to_category = Category.objects.get(slug=to_slug, parent__isnull=False)

        CategoryTranslation.objects.create(
            created_by=None,
            text='Omdat er nieuwe categorieën zijn ingevoerd in SIA is er voor de ML tool een tijdelijke vertaling toegevoegd',  # noqa
            old_category=from_category,
            new_category=to_category,
        )


def _deactivate_categories(apps, schema_editor):
    Category = apps.get_model('signals', 'Category')

    qs = Category.objects.filter(slug__in=DEACTIVATE_CATEGORIES, parent__isnull=False)
    qs.update(is_active=False)


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0095_SIG-2224_SIG-2234_new_categories'),
    ]

    operations = [
        migrations.RunPython(_new_categories, None),  # No reverse possible
        migrations.RunPython(_ml_translations, None),  # No reverse possible
        migrations.RunPython(_deactivate_categories, None),  # No reverse possible
    ]
