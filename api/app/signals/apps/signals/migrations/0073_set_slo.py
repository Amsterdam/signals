import django.db.models.deletion
from django.db import migrations, models

NOT_SPECIFIED = 3
WORK_DAY = False
CALENDAR_DAY = True

SERVICE_LEVEL_OBJECTIVES = {
    'asbest-accu': [3, WORK_DAY],
    'bedrijfsafval': [3, WORK_DAY],
    'container-is-kapot': [3, WORK_DAY],
    'container-is-vol': [3, WORK_DAY],
    'container-voor-papier-is-stuk': [3, WORK_DAY],
    'container-voor-papier-is-vol': [3, WORK_DAY],
    'container-voor-plastic-afval-is-vol': [3, WORK_DAY],
    'container-voor-plastic-afval-is-kapot': [3, WORK_DAY],
    'grofvuil': [3, WORK_DAY],
    'handhaving-op-afval': [3, WORK_DAY],
    'huisafval': [3, WORK_DAY],
    'overig-afval': [3, WORK_DAY],
    'prullenbak-is-kapot': [3, WORK_DAY],
    'prullenbak-is-vol': [3, WORK_DAY],
    'puin-sloopafval': [3, WORK_DAY],
    'veeg-zwerfvuil': [3, WORK_DAY],
    'vermoeden': [3, WORK_DAY],
    'boom': [5, WORK_DAY],
    'drijfvuil': [5, WORK_DAY],
    'maaien-snoeien': [5, WORK_DAY],
    'oever-kade-steiger': [5, WORK_DAY],
    'onkruid': [5, WORK_DAY],
    'overig-groen-en-water': [3, WORK_DAY],
    'overig': [5, WORK_DAY],
    'overige-dienstverlening': [3, WORK_DAY],
    'geluidsoverlast-installaties': [5, WORK_DAY],
    'geluidsoverlast-muziek': [5, WORK_DAY],
    'overig-horecabedrijven': [5, WORK_DAY],
    'overlast-door-bezoekers-niet-op-terras': [5, WORK_DAY],
    'overlast-terrassen': [5, WORK_DAY],
    'stank-horecabedrijven': [3, WORK_DAY],
    'stankoverlast': [5, WORK_DAY],
    'auto-scooter-bromfietswrak': [21, CALENDAR_DAY],
    'bouw-sloopoverlast': [21, CALENDAR_DAY],
    'deelfiets': [21, CALENDAR_DAY],
    'fietswrak': [21, CALENDAR_DAY],
    'graffiti-wildplak': [5, WORK_DAY],
    'hinderlijk-geplaatst-object': [5, WORK_DAY],
    'lozing-dumping-bodemverontreiniging': [3, WORK_DAY],
    'overig-openbare-ruimte': [21, CALENDAR_DAY],
    'parkeeroverlast': [3, WORK_DAY],
    'stank-geluidsoverlast': [21, CALENDAR_DAY],
    'hondenpoep': [21, CALENDAR_DAY],
    'wegsleep': [21, CALENDAR_DAY],
    'overlast-op-het-water-geluid': [3, WORK_DAY],
    'scheepvaart-nautisch-toezicht': [3, WORK_DAY],
    'overig-boten': [3, WORK_DAY],
    'overlast-op-het-water-vaargedrag': [3, WORK_DAY],
    'overlast-vanaf-het-water': [3, WORK_DAY],
    'overlast-op-het-water-snel-varen': [3, WORK_DAY],
    'overlast-op-het-water-gezonken-boot': [3, WORK_DAY],
    'dode-dieren': [3, WORK_DAY],
    'duiven': [5, WORK_DAY],
    'ganzen': [5, WORK_DAY],
    'meeuwen': [5, WORK_DAY],
    'overig-dieren': [3, WORK_DAY],
    'ratten': [5, WORK_DAY],
    'wespen': [5, WORK_DAY],
    'daklozen-bedelen': [3, WORK_DAY],
    'drank-en-drugsoverlast': [3, WORK_DAY],
    'jongerenoverlast': [3, WORK_DAY],
    'overige-overlast-door-personen': [3, WORK_DAY],
    'overlast-door-afsteken-vuurwerk': [3, WORK_DAY],
    'overlast-van-taxis-bussen-en-fietstaxis': [3, WORK_DAY],
    'personen-op-het-water': [NOT_SPECIFIED, WORK_DAY],
    'vuurwerkoverlast': [3, WORK_DAY],
    'wildplassen-poepen-overgeven': [3, WORK_DAY],
    'autom-verzinkbare-palen': [21, CALENDAR_DAY],
    'bewegwijzering': [21, CALENDAR_DAY],
    'brug': [21, CALENDAR_DAY],
    'camerasystemen': [21, CALENDAR_DAY],
    'fietsrek-nietje': [5, WORK_DAY],
    'gladheid': [3, WORK_DAY],
    'klok': [21, CALENDAR_DAY],
    'lichthinder': [5, WORK_DAY],
    'omleiding-belijning-verkeer': [21, CALENDAR_DAY],
    'onderhoud-stoep-straat-en-fietspad': [3, WORK_DAY],
    'overig-wegen-verkeer-straatmeubilair': [5, WORK_DAY],
    'parkeer-verwijssysteem': [21, CALENDAR_DAY],
    'put-riolering-verstopt': [5, WORK_DAY],
    'speelplaats': [5, WORK_DAY],
    'sportvoorziening': [5, WORK_DAY],
    'stadsplattegronden': [21, CALENDAR_DAY],
    'straatmeubilair': [5, WORK_DAY],
    'lantaarnpaal-straatverlichting': [21, CALENDAR_DAY],
    'straatverlichting-openbare-klok': [21, CALENDAR_DAY],
    'verdeelkasten-bekabeling': [21, CALENDAR_DAY],
    'verkeersbord-verkeersafzetting': [3, WORK_DAY],
    'verkeerslicht': [5, WORK_DAY],
    'verkeersoverlast': [5, WORK_DAY],
    'verkeersoverlast-verkeerssituaties': [5, WORK_DAY],
    'verkeerssituaties': [5, WORK_DAY],
    'verlichting-netstoring': [5, WORK_DAY],
}


def _set_service_level(apps, schema_editor):
    """
    Set a service level objective for each sub category.
    """
    ServiceLevelObjective = apps.get_model('signals', 'ServiceLevelObjective')
    Category = apps.get_model('signals', 'Category')

    for sub_slug, entry in SERVICE_LEVEL_OBJECTIVES.items():
        n_days, use_calendar_days = entry
        sub_cat = Category.objects.get(parent__isnull=False, slug=sub_slug)
        ServiceLevelObjective.objects.create(
            category=sub_cat, n_days=n_days, use_calendar_days=use_calendar_days)

    sub_slugs = SERVICE_LEVEL_OBJECTIVES.keys()
    assert Category.objects.filter(parent__isnull=False, slug__in=[sub_slugs]).count() == 0


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0072_auto_20190912_1020'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceLevelObjective',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID'
                )),
                ('n_days', models.IntegerField()),
                ('use_calendar_days', models.BooleanField(
                    default=False,
                    choices=[
                        (True, 'Kalender dagen'),
                        (False, 'Werk dagen'),
                    ]
                )),
                ('category', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='signals.Category'
                )),
            ],
        ),
        migrations.RunPython(_set_service_level),
    ]
