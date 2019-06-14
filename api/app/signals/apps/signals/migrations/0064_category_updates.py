"""
Disable 4 categories see SIG-1279 and SIG-1280.
"""
from django.db import migrations

# Disable categories
REMOVE = {
    'wegen-verkeer-straatmeubilair': [
        'lichthinder',
        'verdeelkasten-bekabeling',
        'verlichting-netstoring',
    ],
    'overlast-op-het-water': [
        'overlast-vanaf-het-water',
    ],
}


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


# Activate the automatic category translation
TO_TRANSLATE = [
    ('lichthinder', 'lantaarnpaal-straatverlichting'),
    ('verdeelkasten-bekabeling', 'lantaarnpaal-straatverlichting'),
    ('verlichting-netstoring', 'lantaarnpaal-straatverlichting'),
    ('overlast-vanaf-het-water', 'overig-boten'),
]
MESSAGE = 'Omdat er nieuwe categorieën zijn ingevoerd in SIA is deze melding overnieuw ingedeeld.'


def add_category_translations(apps, schema_editor):
    Category = apps.get_model('signals', 'Category')
    CategoryTranslation = apps.get_model('signals', 'CategoryTranslation')

    for from_slug, to_slug in TO_TRANSLATE:
        from_cat = Category.objects.get(slug=from_slug)
        to_cat = Category.objects.get(slug=to_slug)

        CategoryTranslation.objects.create(
            created_by=None,
            text=MESSAGE,
            old_category=from_cat,
            new_category=to_cat,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0063_auto_20190613_1437'),
    ]

    operations = [
        migrations.RunPython(remove_categories),
        migrations.RunPython(add_category_translations),
    ]
