import datetime

from django.db import migrations

fe_uitvraag_mapping = [
    {
        'id': 'extra_personen_overig',
        'label': 'Om hoe veel personen gaat het (ongeveer)?',
        'category_url': '/signals/v1/public/terms/categories/overlast-van-en-door-personen-of-groepen',  # noqa
    },
    {
        'id': 'extra_personen_overig_vaker',
        'label': 'Gebeurt het vaker?',
        'category_url': '/signals/v1/public/terms/categories/overlast-van-en-door-personen-of-groepen',  # noqa
    },
    {
        'id': 'extra_personen_overig_vaker_momenten',
        'label': 'Geef aan op welke momenten het gebeurt',
        'category_url': '/signals/v1/public/terms/categories/overlast-van-en-door-personen-of-groepen',  # noqa
    },
    {
        'id': 'extra_bedrijven_overig',
        'label': 'Uw melding gaat over:',
        'category_url': '/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca',
    },
    {
        'id': 'extra_bedrijven_adres',
        'label': 'Bedrijfsnaam / Evenementnaam van vermoedelijke veroorzaker',
        'category_url': '/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca',
    },
    {
        'id': 'extra_bedrijven_naam',
        'label': 'Op welke locatie ervaart u de overlast',
        'category_url': '/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca',
    },
    {
        'id': 'extra_bedrijven_vaker',
        'label': 'Gebeurt het vaker?',
        'category_url': '/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca',
    },
    {
        'id': 'extra_bedrijven_momenten',
        'label': 'Geef aan op welke momenten het gebeurt',
        'category_url': '/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca',
    },
    {
        'id': 'extra_boten_snelheid_rondvaartboot',
        'label': 'Gaat de melding over een rondvaartboot?',
        'category_url': '/signals/v1/public/terms/categories/overlast-op-het-water/sub_categories/overlast-op-het-water-snel-varen',  # noqa
    },
    {
        'id': 'extra_boten_snelheid_rederij',
        'label': 'Wat is de naam van de rederij?',
        'category_url': '/signals/v1/public/terms/categories/overlast-op-het-water/sub_categories/overlast-op-het-water-snel-varen',  # noqa
    },
    {
        'id': 'extra_boten_snelheid_naamboot',
        'label': 'Wat is de naam van de boot?',
        'category_url': '/signals/v1/public/terms/categories/overlast-op-het-water/sub_categories/overlast-op-het-water-snel-varen',  # noqa
    },
    {
        'id': 'extra_boten_snelheid_meer',
        'label': 'Zijn er nog dingen die u ons nog meer kunt vertellen?',
        'category_url': '/signals/v1/public/terms/categories/overlast-op-het-water/sub_categories/overlast-op-het-water-snel-varen',  # noqa
    },
    {
        'id': 'extra_boten_geluid_meer',
        'label': 'Zijn er nog dingen die u ons nog meer kunt vertellen?',
        'category_url': '/signals/v1/public/terms/categories/overlast-op-het-water/sub_categories/overlast-op-het-water-geluid',  # noqa
    },
    {
        'id': 'extra_boten_gezonken_meer',
        'label': 'Zijn er nog dingen die u ons nog meer kunt vertellen?',
        'category_url': '/signals/v1/public/terms/categories/overlast-op-het-water/sub_categories/overlast-op-het-water-gezonken-boot',  # noqa
    }
]


PARENT_CATEGORY_URL_PATTERN = '/signals/v1/public/terms/categories/{category_slug}'
CHILD_CATEGORY_URL_PATTERN = '{parent_category_url_pattern}/sub_categories/{category_slug}'


def _migrated(extra_properties):
    return not isinstance(extra_properties, dict)


def _create_answer(answer, label=None):
    if isinstance(answer, bool):
        return {
            'label': label,
            'value': answer,
        }
    return answer


def _create_question(_id, question, answer, category_url):
    return {
        'id': _id,
        'label': question,
        'answer': _create_answer(answer),
        'category_url': category_url,
    }


def _migrate_extra_property(question, answer, signal):
    category_assignment = signal.category_assignment
    if not category_assignment:
        return

    current_category = category_assignment.category
    if current_category.parent:
        category_url = CHILD_CATEGORY_URL_PATTERN.format(
            parent_category_url_pattern=PARENT_CATEGORY_URL_PATTERN.format(
                category_slug=current_category.parent.slug
            ),
            category_slug=current_category.slug
        )
    else:
        category_url = PARENT_CATEGORY_URL_PATTERN.format(
            category_slug=current_category.slug
        )

    mapping = list(filter(lambda o: o['label'] == question, fe_uitvraag_mapping))
    if not mapping:
        return

    return _create_question(
        mapping[0]['id'],
        question,
        answer,
        mapping[0]['category_url'] if len(mapping) == 1 else category_url
    )


def _migrate(signal):
    new_extra_properties = []
    for question, answer in signal.extra_properties.items():
        new_extra_property = _migrate_extra_property(question, answer, signal)
        if new_extra_property:
            new_extra_properties.append(new_extra_property)
    return new_extra_properties


def forward_func(apps, schema_editor):
    signal_model = apps.get_model('signals', 'Signal')
    qs = signal_model.objects.filter(extra_properties__isnull=False)
    for signal in qs:
        if not _migrated(signal.extra_properties):
            signal.extra_properties = _migrate(signal)
            signal.save()


now = datetime.datetime.utcnow()
backup_extra_properties = "CREATE TABLE signals_extra_properties_{} " \
                          "AS SELECT id, signal_id, extra_properties " \
                          "FROM signals_signal".format(now.strftime("%Y%m%d"))


class Migration(migrations.Migration):
    """
    SIG-1203 - [BE] Migreer oude uitvraag data naar nieuw ontwerp

    Migratie naar nieuwe structuur voor extra_properties + rollback
    """
    dependencies = [
        ('signals', '0048_merge_20190503_1542'),
    ]

    operations = [
        migrations.RunSQL(backup_extra_properties),  # Create the backup table
        migrations.RunPython(forward_func),
    ]
