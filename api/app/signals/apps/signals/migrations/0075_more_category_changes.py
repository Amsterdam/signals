"""
SIG-1705 new main categories
SIG-1706 new sub categories
SIG-1707 rename sub categories
"""
from django.db import migrations, models

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

        return self

    def new_sub(self, mutation):
        self._mutation = mutation
        self._type = CategoryMutation.NEW_SUB

        return self

    def change_sub(self, mutation):
        self._mutation = mutation
        self._type = CategoryMutation.CHANGE_SUB

        return self

    def _parse_slo_code(self, slo_code):
        """Parse e.g. 21K to mean 21 calendar days or 3W three work days"""
        n_days = int(slo_code[:-1])
        assert slo_code[-1] in 'WK'  # work or calendar day
        use_calendar_days = True if slo_code[-1] == 'K' else False

        return n_days, use_calendar_days

    def _add_main_category(self, apps, schema_editor):
        Category = apps.get_model('signals', 'Category')

        # Check that the slugs are unique across sub and main category
        slugs = set(Category.objects.values_list('slug', flat=True))
        new_slugs = set(self._mutation)
        assert not (slugs & new_slugs)

        for main_slug, main_data in self._mutation.items():
            new_main = Category.objects.create(name=main_slug)  # control slug derivation
            new_main.name = main_data['name']  # set actual desired name
            new_main.save()

    def _add_sub_category(self, apps, schema_editor):
        """Add sub category (use with self._change_sub_category below)"""
        Category = apps.get_model('signals', 'Category')

        # Check that the slugs are unique across sub and main category
        slugs = set(Category.objects.values_list('slug', flat=True))
        all_new_slugs = [slug for value in self._mutation.values() for slug in value]
        new_slugs = set(all_new_slugs)

        assert len(new_slugs) == len(all_new_slugs)  # no double slugs in new data
        assert not (slugs & new_slugs)  # slugs globally unique

        for main_slug, main_data in self._mutation.items():
            main_cat = Category.objects.get(slug=main_slug)

            for sub_slug, sub_data in main_data.items():
                assert 'name' in sub_data  # create sub category with slug, but need name later on

                Category.objects.create(name=sub_slug, parent=main_cat)

    def _change_sub_category(self, apps, schema_editor):
        Category = apps.get_model('signals', 'Category')
        Department = apps.get_model('signals', 'Department')
        ServiceLevelObjective = apps.get_model('signals', 'ServiceLevelObjective')

        for main_slug, main_data in self._mutation.items():
            main_cat = Category.objects.get(slug=main_slug)

            for sub_slug, sub_data in main_data.items():
                sub_cat = Category.objects.get(slug=sub_slug, parent=main_cat)

                if 'handling' in sub_data:
                    sub_cat.handling = sub_data['handling']
                if 'departments' in sub_data:
                    new_departments = Department.objects.filter(code__in=sub_data['departments'])
                    sub_cat.departments.clear()
                    for dep in new_departments:
                        sub_cat.departments.add(dep)
                if 'name' in sub_data:
                    sub_cat.name = sub_data['name']
                if 'slo' in sub_data:
                    n_days, use_calendar_days = self._parse_slo_code(sub_data['slo'])

                    ServiceLevelObjective.objects.create(
                        category=sub_cat,
                        n_days=n_days,
                        use_calendar_days=use_calendar_days
                    )

                sub_cat.save()

    def run(self, apps, schema_editor):
        assert self._mutation is not None
        assert self._type is not None

        if self._type == CategoryMutation.NEW_MAIN:
            self._add_main_category(apps, schema_editor)
        elif self._type == CategoryMutation.NEW_SUB:
            self._add_sub_category(apps, schema_editor)
            self._change_sub_category(apps, schema_editor)
        elif self._type == CategoryMutation.CHANGE_SUB:
            self._change_sub_category(apps, schema_editor)


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0074_auto_20191001_0945'),
    ]

    operations = [
        # migrate category model to add new handling message choices
        migrations.AlterField(
            model_name='category',
            name='handling',
            field=models.CharField(
                choices=[
                    ('A3DMC', 'A3DMC'),
                    ('A3DEC', 'A3DEC'),
                    ('A3WMC', 'A3WMC'),
                    ('A3WEC', 'A3WEC'),
                    ('I5DMC', 'I5DMC'),
                    ('STOPEC', 'STOPEC'),
                    ('KLOKLICHTZC', 'KLOKLICHTZC'),
                    ('GLADZC', 'GLADZC'),
                    ('A3DEVOMC', 'A3DEVOMC'),
                    ('WS1EC', 'WS1EC'),
                    ('WS2EC', 'WS2EC'),
                    ('WS3EC', 'WS3EC'),
                    ('REST', 'REST'),
                    ('ONDERMIJNING', 'ONDERMIJNING'),
                    ('EMPTY', 'EMPTY'),
                    ('LIGHTING', 'LIGHTING'),
                    ('GLAD_OLIE', 'GLAD_OLIE')
                ],
                default='REST',
                max_length=20
            ),
        ),
        migrations.RunPython(CategoryMutation().new_main(NEW_SIG_1705).run),
        migrations.RunPython(CategoryMutation().new_sub(NEW_SIG_1706).run),
        migrations.RunPython(CategoryMutation().change_sub(CHANGES_SIG_1707).run),
    ]
