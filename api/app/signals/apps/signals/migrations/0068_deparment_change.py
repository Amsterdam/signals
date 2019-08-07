"""SIG-1468 chance category-departments association"""
from django.db import migrations

CHANGE = {
    'afval': {
        'asbest-accu': {
            'departments': ['ASC', 'THO'],
        },
        'container-is-kapot': {
            'departments': ['AEG'],
        },
        'container-is-vol': {
            'departments': ['AEG'],
        },
        'container-voor-papier-is-stuk': {
            'departments': ['AEG'],
        },
        'container-voor-papier-is-vol': {
            'departments': ['AEG'],
        },
        'container-voor-plastic-afval-is-vol': {
            'departments': ['AEG'],
        },
        'container-voor-plastic-afval-is-kapot': {
            'departments': ['AEG'],
        },
        'grofvuil': {
            'departments': ['AEG'],
        },
        'handhaving-op-afval': {
            'departments': ['ASC', 'THO']
        },
        'huisafval': {
            'departments': ['AEG'],
        },
        'overig-afval': {
            'departments': ['AEG', 'STW'],
        },
        'prullenbak-is-kapot': {
            'departments': ['STW'],
        },
        'prullenbak-is-vol': {
            'departments': ['STW'],
        },
        'puin-sloopafval': {
            'departments': ['AEG'],
        },
        'veeg-zwerfvuil': {
            'departments': ['STW'],
        },
    },
    'openbaar-groen-en-water': {
        'boom': {
            'departments': ['STW'],
        },
        'drijfvuil': {
            'departments': ['STW', 'WAT'],
        },
        'maaien-snoeien': {
            'departments': ['STW'],
        },
        'oever-kade-steiger': {
            'departments': ['STW'],
        },
        'onkruid': {
            'departments': ['STW'],
        },
        'overig-groen-en-water': {
            'departments': ['STW'],
        },
    },
    'overig': {
        'overige-dienstverlening': {
            'departments': ['ASC'],
        },
    },
    'overlast-bedrijven-en-horeca': {
        'geluidsoverlast-installaties': {
            'departments': ['VTH'],
        },
        'geluidsoverlast-muziek': {
            'departments': ['VTH'],
        },
        'overig-horecabedrijven': {
            'departments': ['VTH'],
        },
        'overlast-terrassen': {
            'departments': ['VTH'],
        },
        'stankoverlast': {
            'departments': ['VTH'],
        },
    },
    'overlast-in-de-openbare-ruimte': {
        'auto-scooter-bromfietswrak': {
            'departments': ['ASC', 'THO'],
        },
        'bouw-sloopoverlast': {
            'departments': ['VTH'],
        },
        'fietswrak': {
            'departments': ['THO'],
        },
        'graffiti-wildplak': {
            'departments': ['STW'],
        },
        'lozing-dumping-bodemverontreiniging': {
            'departments': ['OMG'],
        },
        'stank-geluidsoverlast': {
            'departments': ['VTH', 'THO'],
        },
        'hondenpoep': {
            'departments': ['STW', 'THO'],
        },
        'wegsleep': {
            'departments': ['THO'],
        },
    },
    'overlast-van-dieren': {
        'dode-dieren': {
            'departments': ['GGD'],
        },
        'duiven': {
            'departments': ['GGD'],
        },
        'ganzen': {
            'departments': ['GGD'],
        },
        'meeuwen': {
            'departments': ['GGD'],
        },
        'overig-dieren': {
            'departments': ['GGD'],
        },
        'ratten': {
            'departments': ['GGD'],
        },
        'wespen': {
            'departments': ['GGD'],
        },
    },
    'wegen-verkeer-straatmeubilair': {
        'autom-verzinkbare-palen': {
            'departments': ['VOR'],
        },
        'bewegwijzering': {
            'departments': ['VOR'],
        },
        'brug': {
            'departments': ['STW', 'WAT'],
        },
        'camerasystemen': {
            'departments': ['VOR'],
        },
        'fietsrek-nietje': {
            'departments': ['STW'],
        },
        'gladheid': {
            'departments': ['STW'],
        },
        'klok': {
            'departments': ['VOR'],
        },
        'omleiding-belijning-verkeer': {
            'departments': ['STW'],
        },
        'onderhoud-stoep-straat-en-fietspad': {
            'departments': ['STW'],
        },
        'overig-wegen-verkeer-straatmeubilair': {
            'departments': ['STW'],
        },
        'parkeer-verwijssysteem': {
            'departments': ['VOR'],
        },
        'put-riolering-verstopt': {
            'departments': ['WAT'],
        },
        'speelplaats': {
            'departments': ['STW'],
        },
        'sportvoorziening': {
            'departments': ['STW'],
        },
        'stadsplattegronden': {
            'departments': ['VOR'],
        },
        'straatmeubilair': {
            'departments': ['STW'],
        },
        'lantaarnpaal-straatverlichting': {
            'departments': ['VOR'],
        },
        'verkeersbord-verkeersafzetting': {
            'departments': ['STW'],
        },
        'verkeerslicht': {
            'departments': ['VOR'],
        },
        'verkeersoverlast': {
            'departments': ['ASC', 'THO'],
        },
        'verkeerssituaties': {
            'departments': ['STW', 'VOR'],
        },
    },
}


def change_categories(apps, schema_editor):
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

            sub_category.save()


class Migration(migrations.Migration):
    dependencies = [
        ('signals', '0067_unstick_signals'),
    ]

    operations = [
        migrations.RunPython(change_categories),
    ]
