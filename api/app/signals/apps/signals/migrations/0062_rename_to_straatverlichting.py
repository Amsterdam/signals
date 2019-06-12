from django.db import migrations

# Requested extra name changes:
# Lantaarnpaal / straatverlichting -> Straatverlichting

REQUESTED_CHANGES = [
    ('Lantaarnpaal / straatverlichting', 'lantaarnpaal-straatverlichting', 'Straatverlichting',),
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
        ('signals', '0061_auto_20190607_1423'),
    ]

    operations = [
        migrations.RunPython(migrate_category_names)
    ]
