"""Category changes see SIG-1139."""
from django.db import migrations

# TODO: finish Excel file, currently at row 89
# TODO: implement add_categories
# TODO: communicate that we do bulk re-assign after acceptation of categories
# TODO: add new re-assigns to bulk script

ADD = {
    'afval': [],
    'ondermijning': [],
    'openbaar-groen-en-water': [],
    'overig': [],
    'overlast-bedrijven-en-horeca': [],
    'overlast-in-de-openbare-ruimte': [],
    'overlast-op-het-water': [],
    'overlast-van-dieren': [],
    'overlast-van-en-door-personen-of-groepen': [],
    'wegen-verkeer-straatmeubilair': [
        {
            'name': 'Verkeerssituaties',
            'handling': 'I5DMC',
            'departments': []
        },
        {
            'name': 'Verkeersoverlast',
            'handling': 'I5DMC',
            'departments': [
                'THOR',
            ]
        }
    ],
}

REMOVE = {
    'afval': ['bedrijfsafval'],
    'ondermijning': [],
    'openbaar-groen-en-water': [],
    'overig': [],
    'overlast-bedrijven-en-horeca': [],
    'overlast-in-de-openbare-ruimte': [],
    'overlast-op-het-water': [
        'overlast-op-het-water-vaargedrag',
    ],
    'overlast-van-dieren': [],
    'overlast-van-en-door-personen-of-groepen': [
        'vuurwerkoverlast',
        'personen-op-het-water',
    ],
    'wegen-verkeer-straatmeubilair': [
        'verkeersoverlast-verkeerssituaties',
    ],
}

CHANGE = {
    'afval': {
        'overig-afval': {
            'handling': 'REST',
        }
    },
    'ondermijning': {},
    'openbaar-groen-en-water': {
        'overig-groen-en-water': {
            'handling': 'REST',
        }
    },
    'overig': {},
    'overlast-bedrijven-en-horeca': {
        'overig-horecabedrijven': {
            'handling': 'REST',
        }
    },
    'overlast-in-de-openbare-ruimte': {
        'wegsleep': {
            'handling': 'EMPTY',
        },
        'overig-openbare-ruimte': {
            'handling': 'EMPTY',
        },
    },
    'overlast-op-het-water': {
        'scheepvaart-nautisch-toezicht': {
            'handling': 'WS3EC',
        },
        'overig-boten': {
            'handling': 'WS3EC',
        },
    },
    'overlast-van-dieren': {
        'overig-dieren': {
            'handling': 'REST',
        },
    },
    'overlast-van-en-door-personen-of-groepen': {
        'overige-overlast-door-personen': {
            'handling': 'REST',
        }
    },
    'wegen-verkeer-straatmeubilair': {
        'autom-verzinkbare-palen': {
            'handling': 'A3WEC',
        },
    },
}


def add_categories(apps, schema_editor):
    Category = apps.get_model('signals', 'Category')
    for main_slug, data in ADD.items():
        if not data:
            continue

        main_category = Category.get(slug=main_slug, parent__is_null=True)
        for new_sub_category_data in data:
            pass  # TODO: implement


def remove_categories(apps, schema_editor):
    Category = apps.get_model('signals', 'Category')
    for main_slug, to_remove in REMOVE.items():
        if not to_remove:
            continue

        main_category = Category.get(slug=main_slug, parent__is_null=True)
        for sub_slug in to_remove:
            sub_category = Category.get(slug=sub_slug, parent=main_category)
            sub_category.is_active = False
            sub_category.save()


def change_categories(apps, schema_editor):
    Category = apps.get_model('signals', 'Category')
    for main_slug, data in CHANGE.items():
        if not data:
            continue

        main_category = Category.get(slug=main_slug, parent__is_null=True)
        for sub_slug, sub_data in data.items():
            sub_category = Category.get(slug=sub_slug, parent=main_category)

            # mutate here
            if 'handling' in sub_data:
                sub_category.handling = sub_data['handling']
            
            sub_category.save()

class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0043_merge_20190404_0927'),
    ]

    operations = [
    ]
