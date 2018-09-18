from django.db import migrations


def create_initial_data_departments(apps, schema_editor):
    """Creating initial data for all departments."""
    departments = {
        # code, name,                    intern/extern
        'POA': ('Port of Amsterdam',     'E'),
        'THO': ('THOR',                  'I'),
        'WAT': ('Waternet',              'E'),
        'STW': ('Stadswerken',           'I'),
        'AEG': ('Afval en Grondstoffen', 'I'),
        'ASC': ('Actie Service Centrum', 'I'),
        'POL': ('Politie',               'E'),
        'GGD': ('GGD',                   'E'),
        'VOR': ('V&OR',                  'I'),  # Onderscheid V&OR OVL en V&OR VRI ???
        'OVL': ('V&OR OVL',              'I'),  # Onderscheid V&OR OVL en V&OR VRI ???
        'VRI': ('V&OR VRI',              'I'),  # Onderscheid V&OR OVL en V&OR VRI ???
        'CCA': ('CCA',                   'I'),
        'STL': ('Stadsloket',            'I'),
        'OMG': ('Omgevingsdienst',       'I'),  # Intern/extern ???
        'VTH': ('VTH',                   'I'),  # Wat is VTH ? Intern/Extern ?
        'FB':  ('FB',                    'I'),  # ?? what is FB
    }

    Department = apps.get_model('signals', 'Department')
    for department_code, department_values in departments.items():
        name = department_values[0]
        is_intern = department_values[1] == 'I'
        Department.objects.create(code=department_code, name=name, is_intern=is_intern)


def create_initial_data_categories(apps, schema_editor):
    """Creating initial data for all categories."""
    categories = (
        # code,  main_categorie,                             sub_categorie,                                handling,      departments              # noqa
        ('F01',  'Afval',                                    'Veeg- / zwerfvuil',                          'A3DEC',       'CCA,ASC,STW'),          # noqa
        ('F02',  'Afval',                                    'Grofvuil',                                   'A3DEVOMC',    'CCA,ASC,AEG'),          # noqa
        ('F03',  'Afval',                                    'Huisafval',                                  'A3DMC',       'CCA,ASC,AEG'),          # noqa
        ('F04',  'Afval',                                    'Bedrijfsafval',                              'A3DMC',       'CCA,ASC,AEG'),          # noqa
        ('F05',  'Afval',                                    'Puin / sloopafval',                          'A3DMC',       'CCA,ASC,AEG'),          # noqa
        ('F06',  'Afval',                                    'Container is vol',                           'A3DMC',       'CCA,ASC,AEG'),          # noqa
        ('F07',  'Afval',                                    'Prullenbak is vol',                          'A3DEC',       'CCA,ASC,STW'),          # noqa
        ('F08',  'Afval',                                    'Container is kapot',                         'A3DMC',       'CCA,ASC,AEG'),          # noqa
        ('F09',  'Afval',                                    'Prullenbak is kapot',                        'A3DMC',       'CCA,ASC,STW'),          # noqa
        ('F10',  'Afval',                                    'Asbest / accu',                              'A3DMC',       'CCA,ASC,AEG'),          # noqa
        ('F11',  'Afval',                                    'Overig afval',                               'I5DMC',       'CCA,ASC,STW,AEG'),      # noqa
        ('F12',  'Afval',                                    'Container voor plastic afval is vol',        'A3DMC',       'CCA,ASC,AEG'),          # noqa
        ('F13',  'Afval',                                    'Container voor plastic afval is kapot',      'A3DMC',       'CCA,ASC,AEG'),          # noqa
        ('F14',  'Wegen, verkeer, straatmeubilair',          'Onderhoud stoep, straat en fietspad',        'A3DEC',       'CCA,ASC,STW'),          # noqa
        ('F15',  'Wegen, verkeer, straatmeubilair',          'Verkeersbord, verkeersafzetting',            'A3DEC',       'CCA,ASC,STW'),          # noqa
        ('F16',  'Wegen, verkeer, straatmeubilair',          'Gladheid',                                   'GLADZC',      'CCA,ASC,STW'),          # noqa
        ('F17',  'Wegen, verkeer, straatmeubilair',          'Omleiding / belijning verkeer',              'A3WEC',       'CCA,ASC,STW'),          # noqa
        ('F18',  'Wegen, verkeer, straatmeubilair',          'Brug',                                       'A3WEC',       'CCA,ASC,STW'),          # noqa
        ('F19',  'Wegen, verkeer, straatmeubilair',          'Straatmeubilair',                            'I5DMC',       'CCA,ASC,STW'),          # noqa
        ('F20',  'Wegen, verkeer, straatmeubilair',          'Fietsrek / nietje',                          'I5DMC',       'CCA,ASC,STW'),          # noqa
        ('F21',  'Wegen, verkeer, straatmeubilair',          'Put / riolering verstopt',                   'I5DMC',       'CCA,ASC,STW'),          # noqa
        ('F22',  'Wegen, verkeer, straatmeubilair',          'Speelplaats',                                'I5DMC',       'CCA,ASC,STW'),          # noqa
        ('F23',  'Wegen, verkeer, straatmeubilair',          'Sportvoorziening',                           'I5DMC',       'CCA,ASC,STW'),          # noqa
        ('F24a', 'Wegen, verkeer, straatmeubilair',          'Straatverlichting / openbare klok',          'KLOKLICHTZC', 'CCA,ASC'),              # noqa
        ('F24b', 'Wegen, verkeer, straatmeubilair',          'Klok',                                       'KLOKLICHTZC', 'CCA,ASC,OVL'),          # noqa
        ('F25',  'Wegen, verkeer, straatmeubilair',          'Verkeerslicht',                              'STOPEC',      'CCA,ASC,VRI'),          # noqa
        ('F26',  'Wegen, verkeer, straatmeubilair',          'Overig Wegen, verkeer, straatmeubilair',     'I5DMC',       'CCA,ASC,STW'),          # noqa
        ('F27',  'Wegen, verkeer, straatmeubilair',          'Verkeersoverlast / Verkeerssituaties',       'I5DMC',       'CCA,ASC,THO'),          # noqa
        ('F28',  'Overlast in de openbare ruimte',           'Lozing / dumping / bodemverontreiniging',    'A3DMC',       'CCA,ASC,OMG'),          # noqa
        ('F29',  'Overlast in de openbare ruimte',           'Parkeeroverlast',                            'A3DMC',       'CCA,ASC,THO'),          # noqa
        ('F30',  'Overlast in de openbare ruimte',           'Fietswrak',                                  'A3WMC',       'CCA,ASC,STW,THO'),      # noqa
        ('F31',  'Overlast in de openbare ruimte',           'Stank- / geluidsoverlast',                   'A3WMC',       'CCA,ASC,THO,VTH'),      # noqa
        ('F32',  'Overlast in de openbare ruimte',           'Bouw- / sloopoverlast',                      'A3WMC',       'CCA,ASC,VTH'),          # noqa
        ('F33',  'Overlast in de openbare ruimte',           'Auto- / scooter- / bromfiets(wrak)',         'A3WMC',       'CCA,ASC,VTH'),          # noqa
        ('F34',  'Overlast in de openbare ruimte',           'Graffiti / wildplak',                        'I5DMC',       'CCA,ASC,STW'),          # noqa
        ('F35',  'Overlast in de openbare ruimte',           'Honden(poep)',                               'A3WMC',       'CCA,ASC,STW'),          # noqa
        ('F36',  'Overlast in de openbare ruimte',           'Hinderlijk geplaatst object',                'I5DMC',       'CCA,ASC,THO'),          # noqa
        ('F39',  'Overlast in de openbare ruimte',           'Deelfiets',                                  'A3WMC',       'CCA,ASC,STW'),          # noqa
        ('F40',  'Overlast in de openbare ruimte',           'Overig openbare ruimte',                     'I5DMC',       'CCA,ASC,STW,THO,VTH'),  # noqa
        ('F41',  'Openbaar groen en water',                  'Boom',                                       'I5DMC',       'CCA,ASC,STW'),          # noqa
        ('F42',  'Openbaar groen en water',                  'Maaien / snoeien',                           'I5DMC',       'CCA,ASC,STW'),          # noqa
        ('F43',  'Openbaar groen en water',                  'Onkruid',                                    'I5DMC',       'CCA,ASC,STW'),          # noqa
        ('F44',  'Openbaar groen en water',                  'Drijfvuil',                                  'I5DMC',       'CCA,ASC,STW'),          # noqa
        ('F45',  'Openbaar groen en water',                  'Oever / kade / steiger',                     'I5DMC',       'CCA,ASC,STW'),          # noqa
        ('F46',  'Openbaar groen en water',                  'Overig groen en water',                      'I5DMC',       'CCA,ASC,STW'),          # noqa
        ('F48',  'Overlast van dieren',                      'Ratten',                                     'I5DMC',       'CCA,ASC,GGD'),          # noqa
        ('F49',  'Overlast van dieren',                      'Ganzen',                                     'I5DMC',       'CCA,ASC,GGD'),          # noqa
        ('F50',  'Overlast van dieren',                      'Duiven',                                     'I5DMC',       'CCA,ASC,GGD'),          # noqa
        ('F51',  'Overlast van dieren',                      'Meeuwen',                                    'I5DMC',       'CCA,ASC,GGD'),          # noqa
        ('F52',  'Overlast van dieren',                      'Wespen',                                     'I5DMC',       'CCA,ASC,GGD'),          # noqa
        ('F53',  'Overlast van dieren',                      'Dode dieren',                                'A3DMC',       'CCA,ASC,GGD'),          # noqa
        ('F54',  'Overlast van dieren',                      'Overig dieren',                              'I5DMC',       'CCA,ASC,GGD'),          # noqa
        ('F55a', 'Overlast van en door personen of groepen', 'Vuurwerkoverlast',                           'A3DMC',       'CCA,ASC,THO'),          # noqa
        ('F55b', 'Overlast van en door personen of groepen', 'Overlast door afsteken vuurwerk',            'A3DMC',       'CCA,ASC,THO'),          # noqa
        ('F56',  'Overlast van en door personen of groepen', 'Overige overlast door personen',             'A3DMC',       'CCA,ASC,THO'),          # noqa
        ('F57',  'Overlast van en door personen of groepen', 'Personen op het water',                      'A3DMC',       'CCA,ASC,THO'),          # noqa
        ('F58',  'Overlast van en door personen of groepen', "Overlast van taxi's, bussen en fietstaxi's", 'A3DMC',       'CCA,ASC,THO'),          # noqa
        ('F59',  'Overlast van en door personen of groepen', 'Jongerenoverlast',                           'A3DMC',       'CCA,ASC,THO'),          # noqa
        ('F60',  'Overlast van en door personen of groepen', 'Daklozen / bedelen',                         'A3DMC',       'CCA,ASC,THO'),          # noqa
        ('F61',  'Overlast van en door personen of groepen', 'Wildplassen / poepen / overgeven',           'A3DMC',       'CCA,ASC,THO'),          # noqa
        ('F62',  'Overlast van en door personen of groepen', 'Drank- en drugsoverlast',                    'A3DMC',       'CCA,ASC,THO'),          # noqa
        ('F63',  'Overlast Bedrijven en Horeca',             'Geluidsoverlast muziek',                     'I5DMC',       'CCA,ASC,VTH'),          # noqa
        ('F64',  'Overlast Bedrijven en Horeca',             'Geluidsoverlast installaties',               'I5DMC',       'CCA,ASC,VTH'),          # noqa
        ('F65',  'Overlast Bedrijven en Horeca',             'Overlast terrassen',                         'I5DMC',       'CCA,ASC,VTH'),          # noqa
        ('F66a', 'Overlast Bedrijven en Horeca',             'Stank horeca/bedrijven',                     'I5DMC',       'CCA,ASC,VTH'),          # noqa
        ('F66b', 'Overlast Bedrijven en Horeca',             'Stankoverlast',                              'I5DMC',       'CCA,ASC,VTH'),          # noqa
        ('F67',  'Overlast Bedrijven en Horeca',             'Overlast door bezoekers (niet op terras)',   'I5DMC',       'CCA,ASC,THO'),          # noqa
        ('F68',  'Overlast Bedrijven en Horeca',             'Overig horeca/bedrijven',                    'I5DMC',       'CCA,ASC,THO,VTH'),      # noqa
        ('F69a', 'Overlast op het water',                    'Overlast op het water - snel varen',         'WS1EC',       'CCA,ASC,WAT'),          # noqa
        ('F69b', 'Overlast op het water',                    'Overlast op het water - Vaargedrag',         'WS1EC',       'CCA,ASC,WAT'),          # noqa
        ('F70',  'Overlast op het water',                    'Overlast op het water - geluid',             'WS1EC',       'CCA,ASC,WAT'),          # noqa
        ('F71',  'Overlast op het water',                    'Overlast op het water - Gezonken boot',      'WS2EC',       'CCA,ASC,WAT'),          # noqa
        ('F72a', 'Overlast op het water',                    'Scheepvaart nautisch toezicht',              'WS1EC',       'CCA,ASC,WAT'),          # noqa
        ('F72b', 'Overlast op het water',                    'Overlast vanaf het water',                   'WS1EC',       'CCA,ASC,WAT'),          # noqa
        ('F72c', 'Overlast op het water',                    'Overig boten',                               'WS1EC',       'CCA,ASC,WAT'),          # noqa
        ('F73',  'Overig',                                   'Overig',                                     'REST',        'CCA,ASC'),              # noqa
    )

    MainCategory = apps.get_model('signals', 'MainCategory')
    SubCategory = apps.get_model('signals', 'SubCategory')
    Department = apps.get_model('signals', 'Department')
    for category in categories:
        code = category[0]
        main_category_name = category[1]
        sub_category_name = category[2]
        handling = category[3]
        departments = category[4].split(',')

        # Creating (or get if already exist) `MainCategory` object.
        main_category, _ = MainCategory.objects.get_or_create(name=main_category_name)

        # Creating `SubCategory` object.
        sub_category = SubCategory.objects.create(main_category=main_category,
                                                  code=code,
                                                  name=sub_category_name,
                                                  handling=handling)

        # Creating relations between `SubCategory` and `Department` objects.
        for department_code in departments:
            department = Department.objects.get(code=department_code)
            sub_category.departments.add(department)


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0008_department_maincategory_subcategory'),
    ]

    operations = [
        migrations.RunPython(create_initial_data_departments),
        migrations.RunPython(create_initial_data_categories),
    ]
