from django.db import migrations

# Requested extra name changes:
# Lantaarnpaal / Straatverlichting -> Lantaarnpaal / straatverlichting
# Nautisch toezicht / Vaargedrag -> Nautisch toezicht / vaargedrag
# Verkeersbord, verkeersafzetting -> Verkeersbord / verkeersafzetting

# (As of now sub slugs are still unique, hence no main slugs below.)
REQUESTED_CHANGES = [
    ('Lantaarnpaal / Straatverlichting', 'lantaarnpaal-straatverlichting', 'Lantaarnpaal / straatverlichting',),  # noqa: 501
    ('Nautisch toezicht / Vaargedrag',   'scheepvaart-nautisch-toezicht',  'Nautisch toezicht / vaargedrag',  ),  # noqa: 501
    ('Verkeersbord, verkeersafzetting',  'verkeersbord-verkeersafzetting', 'Verkeersbord / verkeersafzetting',),  # noqa: 501
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
        ('signals', '0053_category_name_changes'),
    ]

    operations = [
        migrations.RunPython(migrate_category_names),
    ]
