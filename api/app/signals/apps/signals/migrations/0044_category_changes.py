"""Category changes see SIG-1139."""
from django.db import migrations, models
from django.utils.text import slugify

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
            'departments': [
                'STW',
            ]
        },
        {
            'name': 'Verkeersoverlast',
            'handling': 'I5DMC',
            'departments': [
                'THO',
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
    'overig': {
        'overig': {
            'handling': 'I5DMC',
        },
        'overige-dienstverlening': {
            'departments': [
                'ASC',
            ]
        }
    },
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
        'overig-wegen-verkeer-straatmeubilair': {
            'handling': 'REST',
        },
    },
}


def remove_cca_from_departments(apps, schema_editor):
    Category = apps.get_model('signals', 'Category')
    Department = apps.get_model('signals', 'Department')

    cca = Department.objects.get(code='CCA')
    for category in list(Category.objects.filter(departments__in=[cca])):
        category.departments.remove(cca)
        category.save()


def add_categories(apps, schema_editor):
    Category = apps.get_model('signals', 'Category')
    Department = apps.get_model('signals', 'Department')

    for main_slug, data in ADD.items():
        if not data:
            continue

        main_category = Category.objects.get(slug=main_slug, parent__isnull=True)
        for new_sub_category_data in data:
            departments = Department.objects.filter(
                code__in=new_sub_category_data['departments']
            )

            cat_qs = Category.objects.filter(
                parent=main_category,
                name=new_sub_category_data['name'],
            )

            assert not cat_qs.exists()
            assert new_sub_category_data['name']
            assert slugify(new_sub_category_data['name'])

            new_category = Category(
                parent=main_category,
                handling=new_sub_category_data['handling'],
                name=new_sub_category_data['name'],
                slug=slugify(new_sub_category_data['name']),
                is_active=True,
            )
            new_category.save()  # crash here
            new_category.departments.set(departments)
            new_category.save()


def remove_categories(apps, schema_editor):
    Category = apps.get_model('signals', 'Category')
    for main_slug, to_remove in REMOVE.items():
        if not to_remove:
            continue

        main_category = Category.objects.get(slug=main_slug, parent__isnull=True)
        for sub_slug in to_remove:
            sub_category = Category.objects.get(slug=sub_slug, parent=main_category)
            sub_category.is_active = False
            sub_category.save()


def change_categories(apps, schema_editor):
    Category = apps.get_model('signals', 'Category')
    for main_slug, data in CHANGE.items():
        if not data:
            continue

        main_category = Category.objects.get(slug=main_slug, parent__isnull=True)
        for sub_slug, sub_data in data.items():
            sub_category = Category.objects.get(slug=sub_slug, parent=main_category)

            # mutate here
            if 'handling' in sub_data:
                sub_category.handling = sub_data['handling']

            sub_category.save()


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0043_merge_20190404_0927'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='handling',
            field=models.CharField(
                choices=[('A3DMC', 'A3DMC'), ('A3DEC', 'A3DEC'), ('A3WMC', 'A3WMC'),
                         ('A3WEC', 'A3WEC'), ('I5DMC', 'I5DMC'), ('STOPEC', 'STOPEC'),
                         ('KLOKLICHTZC', 'KLOKLICHTZC'), ('GLADZC', 'GLADZC'),
                         ('A3DEVOMC', 'A3DEVOMC'), ('WS1EC', 'WS1EC'), ('WS2EC', 'WS2EC'),
                         ('REST', 'REST'), ('ONDERMIJNING', 'ONDERMIJNING'),
                         ('WS3EC', 'WS3EC'), ('EMPTY', 'EMPTY')], default='REST',
                max_length=20),
        ),
        migrations.RunPython(remove_cca_from_departments),
        migrations.RunPython(remove_categories),
        migrations.RunPython(change_categories),
        migrations.RunPython(add_categories),
    ]
