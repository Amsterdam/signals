from django.db import migrations

# Below is the full list of sub categories, their names, slugs and desired new
# names. Some of the categories are already in the desired state. Strictly
# speaking these categories need not be in the list, however they are for
# documentation purposes.

# (As of now sub slugs are still unique, hence no main slugs below.)
REQUESTED_CHANGES = [
    ('Asbest / accu',                              'asbest-accu',                             'Asbest / accu',                             ),  # noqa: 501
    ('Container is kapot',                         'container-is-kapot',                      'Container is kapot',                        ),  # noqa: 501
    ('Container is vol',                           'container-is-vol',                        'Container is vol',                          ),  # noqa: 501
    ('Container voor papier is stuk',              'container-voor-papier-is-stuk',           'Container papier kapot',                    ),  # noqa: 501
    ('Container voor papier is vol',               'container-voor-papier-is-vol',            'Container papier vol',                      ),  # noqa: 501
    ('Container voor plastic afval is kapot',      'container-voor-plastic-afval-is-kapot',   'Container plastic kapot',                   ),  # noqa: 501
    ('Container voor plastic afval is vol',        'container-voor-plastic-afval-is-vol',     'Container plastic afval vol',               ),  # noqa: 501
    ('Grofvuil',                                   'grofvuil',                                'Grofvuil',                                  ),  # noqa: 501
    ('Handhaving op afval',                        'handhaving-op-afval',                     'Handhaving op afval',                       ),  # noqa: 501
    ('Huisafval',                                  'huisafval',                               'Huisafval',                                 ),  # noqa: 501
    ('Overig afval',                               'overig-afval',                            'Overig afval',                              ),  # noqa: 501
    ('Prullenbak is kapot',                        'prullenbak-is-kapot',                     'Prullenbak is kapot',                       ),  # noqa: 501
    ('Prullenbak is vol',                          'prullenbak-is-vol',                       'Prullenbak is vol',                         ),  # noqa: 501
    ('Puin / sloopafval',                          'puin-sloopafval',                         'Puin- / sloopafval',                        ),  # noqa: 501
    ('Veeg- / zwerfvuil',                          'veeg-zwerfvuil',                          'Veeg- / zwerfvuil',                         ),  # noqa: 501
    ('Vermoeden',                                  'vermoeden',                               'Vermoeden',                                 ),  # noqa: 501
    ('Boom',                                       'boom',                                    'Boom',                                      ),  # noqa: 501
    ('Drijfvuil',                                  'drijfvuil',                               'Drijfvuil',                                 ),  # noqa: 501
    ('Maaien / snoeien',                           'maaien-snoeien',                          'Maaien / snoeien',                          ),  # noqa: 501
    ('Oever / kade / steiger',                     'oever-kade-steiger',                      'Oever / kade / steiger',                    ),  # noqa: 501
    ('Onkruid',                                    'onkruid',                                 'Onkruid',                                   ),  # noqa: 501
    ('Overig groen en water',                      'overig-groen-en-water',                   'Overig groen en water',                     ),  # noqa: 501
    ('Overig',                                     'overig',                                  'Overig',                                    ),  # noqa: 501
    ('Overige dienstverlening',                    'overige-dienstverlening',                 'Overige dienstverlening',                   ),  # noqa: 501
    ('Geluidsoverlast installaties',               'geluidsoverlast-installaties',            'Geluidsoverlast installaties',              ),  # noqa: 501
    ('Geluidsoverlast muziek',                     'geluidsoverlast-muziek',                  'Geluidsoverlast muziek',                    ),  # noqa: 501
    ('Overig horeca / bedrijven',                  'overig-horecabedrijven',                  'Overig bedrijven / horeca',                 ),  # noqa: 501
    ('Overlast door bezoekers (niet op terras)',   'overlast-door-bezoekers-niet-op-terras',  'Overlast door bezoekers (niet op terras)',  ),  # noqa: 501
    ('Overlast terrassen',                         'overlast-terrassen',                      'Overlast terrassen',                        ),  # noqa: 501
    ('Stankoverlast',                              'stankoverlast',                           'Stankoverlast',                             ),  # noqa: 501
    ('Auto- / scooter- / bromfiets(wrak)',         'auto-scooter-bromfietswrak',              'Auto- / scooter- / bromfiets(wrak)',        ),  # noqa: 501
    ('Bouw- / sloopoverlast',                      'bouw-sloopoverlast',                      'Bouw- / sloopoverlast',                     ),  # noqa: 501
    ('Fietswrak',                                  'fietswrak',                               'Fietswrak',                                 ),  # noqa: 501
    ('Graffiti / wildplak',                        'graffiti-wildplak',                       'Graffiti / wildplak',                       ),  # noqa: 501
    ('Hinderlijk geplaatst object',                'hinderlijk-geplaatst-object',             'Hinderlijk geplaatst object',               ),  # noqa: 501
    ('Honden(poep)',                               'hondenpoep',                              'Uitwerpselen',                              ),  # noqa: 501
    ('Lozing / dumping / bodemverontreiniging',    'lozing-dumping-bodemverontreiniging',     'Lozing / dumping / bodemverontreiniging',   ),  # noqa: 501
    ('Overig openbare ruimte',                     'overig-openbare-ruimte',                  'Overig openbare ruimte',                    ),  # noqa: 501
    ('Parkeeroverlast',                            'parkeeroverlast',                         'Parkeeroverlast',                           ),  # noqa: 501
    ('Stank- / geluidsoverlast',                   'stank-geluidsoverlast',                   'Stank- / geluidsoverlast',                  ),  # noqa: 501
    ('Wegsleep',                                   'wegsleep',                                'Wegsleep',                                  ),  # noqa: 501
    ('Overig boten',                               'overig-boten',                            'Overige boten',                             ),  # noqa: 501
    ('Overlast op het water - geluid',             'overlast-op-het-water-geluid',            'Geluid op het water',                       ),  # noqa: 501
    ('Overlast op het water - Gezonken boot',      'overlast-op-het-water-gezonken-boot',     'Wrak in het water',                         ),  # noqa: 501
    ('Overlast op het water - snel varen',         'overlast-op-het-water-snel-varen',        'Snel varen',                                ),  # noqa: 501
    ('Overlast vanaf het water',                   'overlast-vanaf-het-water',                'Overlast vanaf het water',                  ),  # noqa: 501
    ('Scheepvaart nautisch toezicht',              'scheepvaart-nautisch-toezicht',           'Nautisch toezicht / Vaargedrag',            ),  # noqa: 501
    ('Dode dieren',                                'dode-dieren',                             'Dode dieren',                               ),  # noqa: 501
    ('Duiven',                                     'duiven',                                  'Duiven',                                    ),  # noqa: 501
    ('Ganzen',                                     'ganzen',                                  'Ganzen',                                    ),  # noqa: 501
    ('Meeuwen',                                    'meeuwen',                                 'Meeuwen',                                   ),  # noqa: 501
    ('Overig dieren',                              'overig-dieren',                           'Overig dieren',                             ),  # noqa: 501
    ('Ratten',                                     'ratten',                                  'Ratten',                                    ),  # noqa: 501
    ('Wespen',                                     'wespen',                                  'Wespen',                                    ),  # noqa: 501
    ('Daklozen / bedelen',                         'daklozen-bedelen',                        'Daklozen / bedelen',                        ),  # noqa: 501
    ('Drank- en drugsoverlast',                    'drank-en-drugsoverlast',                  'Drank- / drugsoverlast',                    ),  # noqa: 501
    ('Jongerenoverlast',                           'jongerenoverlast',                        'Jongerenoverlast',                          ),  # noqa: 501
    ('Overige overlast door personen',             'overige-overlast-door-personen',          'Overige overlast door personen',            ),  # noqa: 501
    ('Overlast door afsteken vuurwerk',            'overlast-door-afsteken-vuurwerk',         'Overlast door afsteken vuurwerk',           ),  # noqa: 501
    ("Overlast van taxi's, bussen en fietstaxi's",  'overlast-van-taxis-bussen-en-fietstaxis',  "Overlast van taxi's, bussen en fietstaxi's", ),  # noqa: 501
    ('Wildplassen / poepen / overgeven',           'wildplassen-poepen-overgeven',            'Wildplassen / poepen / overgeven',          ),  # noqa: 501
    ('Autom. Verzinkbare palen',                   'autom-verzinkbare-palen',                 'Autom. Verzinkbare palen',                  ),  # noqa: 501
    ('Bewegwijzering',                             'bewegwijzering',                          'Bewegwijzering',                            ),  # noqa: 501
    ('Brug',                                       'brug',                                    'Brug',                                      ),  # noqa: 501
    ('Camerasystemen',                             'camerasystemen',                          'Camerasystemen',                            ),  # noqa: 501
    ('Fietsrek / nietje',                          'fietsrek-nietje',                         'Fietsrek / nietje',                         ),  # noqa: 501
    ('Gladheid',                                   'gladheid',                                'Gladheid',                                  ),  # noqa: 501
    ('Klok',                                       'klok',                                    'Klok',                                      ),  # noqa: 501
    ('Lantaarnpaal / Straatverlichting',           'lantaarnpaal-straatverlichting',          'Lantaarnpaal / Straatverlichting',          ),  # noqa: 501
    ('Lichthinder',                                'lichthinder',                             'Lichthinder',                               ),  # noqa: 501
    ('Omleiding / belijning verkeer',              'omleiding-belijning-verkeer',             'Omleiding / belijning verkeer',             ),  # noqa: 501
    ('Onderhoud stoep, straat en fietspad',        'onderhoud-stoep-straat-en-fietspad',      'Onderhoud stoep, straat en fietspad',       ),  # noqa: 501
    ('Overig Wegen, verkeer, straatmeubilair',     'overig-wegen-verkeer-straatmeubilair',    'Overig Wegen, verkeer, straatmeubilair',    ),  # noqa: 501
    ('Parkeer verwijssysteem',                     'parkeer-verwijssysteem',                  'Parkeer verwijssysteem',                    ),  # noqa: 501
    ('Put / riolering verstopt',                   'put-riolering-verstopt',                  'Put / riolering verstopt',                  ),  # noqa: 501
    ('Speelplaats',                                'speelplaats',                             'Speelplaats',                               ),  # noqa: 501
    ('Sportvoorziening',                           'sportvoorziening',                        'Sportvoorziening',                          ),  # noqa: 501
    ('Stadsplattegronden',                         'stadsplattegronden',                      'Stadsplattegronden',                        ),  # noqa: 501
    ('Straatmeubilair',                            'straatmeubilair',                         'Straatmeubilair',                           ),  # noqa: 501
    ('Verdeelkasten / bekabeling',                 'verdeelkasten-bekabeling',                'Verdeelkasten / bekabeling',                ),  # noqa: 501
    ('Verkeersbord, verkeersafzetting',            'verkeersbord-verkeersafzetting',          'Verkeersbord, verkeersafzetting',           ),  # noqa: 501
    ('Verkeerslicht',                              'verkeerslicht',                           'Verkeerslicht',                             ),  # noqa: 501
    ('Verkeersoverlast',                           'verkeersoverlast',                        'Verkeersoverlast',                          ),  # noqa: 501
    ('Verkeerssituaties',                          'verkeerssituaties',                       'Verkeerssituaties',                         ),  # noqa: 501
    ('Verlichting netstoring',                     'verlichting-netstoring',                  'Verlichting netstoring',                    ),  # noqa: 501
]


def migrate_category_names(apps, schema_editor):
    Category = apps.get_model('signals', 'Category')

    for old_name, slug, new_name in REQUESTED_CHANGES:
        if new_name == old_name:
            continue

        category = Category.objects.get(slug=slug)
        if category.name == new_name:
            continue
        category.name = new_name
        category.save()


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0052_merge_20190514_1115'),
    ]

    operations = [
        migrations.RunPython(migrate_category_names),
    ]
