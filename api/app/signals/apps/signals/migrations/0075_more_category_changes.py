"""
SIG-1705 new main categories
SIG-1706 new sub categories
SIG-1707 rename sub categories
"""
from django.db import migrations

# Slugs carefully chosen to be unique (globally, across main/sub-categories).
NEW_SIG_1705 = {
    'schoon': {
        'name': 'Schoon',
    },
    'civiele-constructies': {
        'name': 'Civiele Constructies',
    },
    'wonen': {
        'name': 'Wonen',
    }
}

# Slugs carefully chosen to be unique (globally, across main/sub-categories).
# Assumption:
# - missing SLO, means 3 workdays
NEW_SIG_1706 = {
    'schoon': {
        'drijfvuil-niet-bevaarbaar-water': {
            'name': 'Drijfvuil niet-bevaarbaar water',
            'departments': ['STW'],
            'handling': 'I5DMC',
            'slo': '5W',
        },
        'gladheid-bladeren': {
            'name': 'Gladheid door blad',
            'departments': ['STW'],
            'handling': 'GLADZC',
        },
        'gladheid-olie': {
            'name': 'Gladheid door olie op de weg',
            'departments': ['STW'],
            'handling': 'GLAD_OLIE',
            'slo': '3W',
        },
        'onkruid-verharding': {
            'name': 'Onkruid op verharding',
            'departments': ['STW'],
            'handling': 'I5DMC',
            'slo': '5W',
        },
    },
    # Assumptions:
    # - no sub departments WAT (Waternet)
    # - no sub departments STW (Stadswerken)
    'openbaar-groen-en-water': {
        'snoeien': {
            'name': 'Snoeien',
            'departments': ['STW'],
            'handling': 'I5DMC',
            'slo': '5W',
        },
        'boom-aanvraag-plaatsing': {
            'name': 'Boom - aanvraag plaatsing',
            'departments': ['VOR'],
            'handling': 'I5DMC',
            'slo': '5W',
        },
        'boom-noodkap': {
            'name': 'Boom - noodkap',
            'departments': ['STW'],
            'handling': 'I5DMC',            
            'slo': '5W',
        },
        'boom-illegale-kap': {
            'name': 'Boom - illegale kap',
            'departments': ['ASC', 'THO'],
            'handling': 'I5DMC',
            'slo': '5W',
        },
        'boom-spiegel': {
            'name': 'Boom - spiegel',
            'departments': ['STW'],
            'handling': 'I5DMC',
            'slo': '5W',
        },
        'boom-overig': {
            'name': 'Boom - overig',
            'departments': ['STW'],
            'handling': 'I5DMC',
            'slo': '5W',
        },
        'boom-afval': {
            'name': 'Boom - plastic en overig afval',
            'departments': ['STW'],
            'handling': 'I5DMC',
            'slo': '5W',
        }
    },
    'civiele-constructies': {
        'kades': {
            'name': 'Kades',
            'departments': ['STW'],
            'handling': 'I5DMC',
            'slo': '5W',
        },
        'steiger': {
            'name': 'Steiger',
            'departments': ['STW'],
            'handling': 'I5DMC',
            'slo': '5W',
        },
        'verzakking-kades': {
            'name': 'Verzakking van kades',
            'departments': ['STW'],
            'handling': 'I5DMC',
            'slo': '5W',
        },
        'brug-bediening': {
            'name': 'Brug bediening',
            'departments': ['WAT'],
            'handling': 'A3WEC',
            'slo': '21W',  # 3 weeks, assumption: calendar days
        },
        'riolering-verstopte-kolk': {
            'name': 'Riolering - verstopte kolk',
            'departments': ['WAT'],
            'handling': 'I5DMC',
            'slo': '5W',
        }
    },
    # Note:
    # - no associated department as it does not exist yet in signals, SIG-1706
    'wonen': {
        'fraude': {
            'name': 'Woonfraude',
            'handling': 'I5DMC',
            'slo': '5W',
        },
        'vakantieverhuur': {
            'name': 'Vakantieverhuur',
            'handling': 'I5DMC',
            'slo': '5W',
        },
        'woningkwaliteit': {
            'name': 'Woningkwaliteit',
            'handling': 'I5DMC',
            'slo': '5W',
        }
    },
}

CHANGES_SIG_1707 = {
    'openbaar-groen-en-water': {
        'drijfvuil': {
            'name': 'Drijfvuil bevaarbaar water',
        },
        'maaien-snoeien': {
            'name': 'Maaien',
        },
        'oever-kade-steiger': {
            'name': 'Oever',
        },
        'onkruid': {
            'name': 'Onkruid in het groen',
        },
        'boom': {
            'name': 'Boom - dood',
        }
    },
    'wegen-verkeer-straatmeubilair': {
        'gladheid': {
            'name': 'Gladheid winterdienst',
        }
    },
}


def change_categories(apps, schema_editor):
    """
    Optionally change sub-category name, handling code, department association.
    """
    Category = apps.get_model('signals', 'Category')
    Department = apps.get_model('signals', 'Department')
    for main_slug, data in CHANGE.items():
        if not data:
            continue

        main_category = Category.objects.get(slug=main_slug, parent__isnull=True)
        for sub_slug, sub_data in data.items():
            sub_category = Category.objects.get(slug=sub_slug, parent=main_category)

            # mutate here
            if 'handling' in sub_data:
                sub_category.handling = sub_data['handling']
            if 'departments' in sub_data:
                new_departments = Department.objects.filter(code__in=sub_data['departments'])
                sub_category.departments.clear()
                for dep in new_departments:
                    sub_category.departments.add(dep)
            if 'name' in sub_data:
                sub_category.name = sub_data['name']

            sub_category.save()


class CategoryMutation:
    NEW_MAIN = 'NEW_MAIN'
    NEW_SUB = 'NEW_SUB'
    CHANGE_SUB = 'CHANGE_SUB'

    def __init__(self):
        self._mutation = None
        self._type = None

    def new_main(self, mutation):
        self._mutation = mutation
        self._type = CategoryMutation.NEW_MAIN

    def new_sub(self, mutation):
        self._mutation = mutation
        self._type = CategoryMutation.NEW_SUB

    def change_sub(self, mutation):
        self._mutation = mutation
        self._type = CategoryMutation.CHANGE_SUB

    def _add_main_category(self, apps, schema_editor):
        Category = apps.get_model('signals', 'Category')

        for main_slug, main_data in self._mutation.items():
            exists_already = Category.objects.filter(slug=main_slug).exists()
            assert not exists_already

            new_main = Category.create(name=main_slug)  # control slug derivation
            new_main.name = main_data['name']  # set actual desired name
            new_main.save()

    def _add_sub_category(self, apps, schema_editor):
        Category = apps.get_model('signals', 'Category')

        for main_slug, main_data in self._mutation.items():
            main_cat = Category.objects.get(slug=main_slug)

            for sub_slug, sub_data in main_data.items():
                exists_already = Category.objects.filter(slug=sub_slug).exists()
                assert not exists_already

                Category.create(name=sub_slug, parent=main_cat)

    def _change_sub_category(self, apps, schema_editor):
        Category = apps.get_model('signals', 'Category')
        ServiceLevelObjective = apps.get_model('signals', 'ServiceLevelObjective')

        # BUSY

    def run(self, apps, schema_editor):
        assert self._mutatation is not None
        assert self._type is not None

        if self._type == CategoryMutation.NEW_MAIN:
            self._add_main_category(apps, schema_editor) 

        assert False, 'Failing here is ok during development'


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0074_auto_20191001_0945'),
    ]

    operations = [
        # migrate category model to add new handling message choices
        migrations.RunPython(CategoryMutation().new_main(NEW_SIG_1705).run),
        migrations.RunPython(CategoryMutation().new_sub(NEW_SIG_1706).run),
        migrations.RunPython(CategoryMutation().change_sub(CHANGES_SIG_1707).run)
    ]
