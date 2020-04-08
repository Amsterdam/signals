"""
Category changes.

SIG-2456, SIG-2458, SIG-2457, and SIG-2508.
"""
from django.db import migrations

# SIG-2457 and SIG-2508
NEW_CATEGORIES = {
    'openbaar-groen-en-water': {
        'beplanting': {
            'name': 'Beplanting',  # SIG-2457
            'handling': 'I5DMC',
            'handling_message':
                "Uw melding wordt ingepland: wij laten u binnen 5 werkdagen "
                "weten hoe en wanneer uw melding wordt afgehandeld. Dat doen "
                "we via e-mail.",
            'departments': ['V&OR'],
            'slo': '5W',
        },
        'japanse-duizendknoop': {
            'name': 'Japanse duizendknoop',  # SIG-2457
            'handling': 'I5DMC',
            'handling_message':
                "Uw melding wordt ingepland: wij laten u binnen 5 werkdagen "
                "weten hoe en wanneer uw melding wordt afgehandeld. Dat doen "
                "we via e-mail.",
            'departments': ['V&OR'],
            'slo': '5W',
        },
        'boomziekten-en-plagen': {
            'name': 'Boom - ziekten en plagen',  # SIG-2457
            'handling': 'I5DMC',
            'handling_message':
                "Uw melding wordt ingepland: wij laten u binnen 5 werkdagen "
                "weten hoe en wanneer uw melding wordt afgehandeld. Dat doen "
                "we via e-mail.",
            'departments': ['V&OR'],
            'slo': '5W',
        },
        'boom-verzoek-inspectie': {
            'name': 'Boom - verzoek inspectie',  # SIG-2457
            'handling': 'I5DMC',
            'handling_message':
                "Uw melding wordt ingepland: wij laten u binnen 5 werkdagen "
                "weten hoe en wanneer uw melding wordt afgehandeld. Dat doen "
                "we via e-mail.",
            'departments': ['V&OR'],
            'slo': '5W',
        },
        'boom-stormschade': {
            'name': 'Boom - stormschade',  # SIG-2457
            'handling': 'I5DMC',
            'handling_message':
                "Uw melding wordt ingepland: wij laten u binnen 5 werkdagen "
                "weten hoe en wanneer uw melding wordt afgehandeld. Dat doen "
                "we via e-mail.",
            'departments': ['STW'],
            'slo': '5W',
        },
    },
    'overlast-in-de-openbare-ruimte': {
        'markten': {
            'name': 'Markten',  # SIG-2508
            'handling': 'HANDLING_MARKTEN',
            'handling_message':
                "Wij beoordelen uw melding. Urgente meldingen pakken we zo "
                "snel mogelijk op. Overige meldingen handelen we binnen drie "
                "dagen af. Als u een mailadres hebt opgegeven, zullen we u op "
                "de hoogte houden.",
            'departments': ['ASC'],
            'slo': '3W',
        }
    }
}

# SIG-2458
DEACTIVATE_CATEGORIES = [
    'riolering-verstopte-kolk',
    'boom-boomstob',
]

ML_TRANSLATION = (
    ('riolering-verstopte-kolk', 'put-riolering-verstopt'),
    ('boom-boomstob', 'boom-aanvraag-plaatsing'),
)


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
        ('signals', '0102_auto_20200323_1513'),
    ]

    operations = [
        migrations.RunPython(_new_categories, None),  # No reverse possible
        migrations.RunPython(_ml_translations, None),  # No reverse possible
        migrations.RunPython(_deactivate_categories, None),  # No reverse possible
    ]
