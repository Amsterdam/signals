"""Category changes see SIG-1255."""
from django.db import migrations

CHANGE = {
    'overlast-in-de-openbare-ruimte': {
        'wegsleep': {
            'handling': 'A3WMC',
        },
        'overig-openbare-ruimte': {
            'handling': 'A3WMC',
        },
    },
}


def change_categories(apps, schema_editor):
    Category = apps.get_model('signals', 'Category')
    for main_slug, data in CHANGE.items():
        if not data:
            continue

        main_category = Category.objects.get(slug=main_slug, parent__isnull=True)
        for sub_slug, sub_data in data.items():
            sub_category = Category.objects.get(slug=sub_slug, parent=main_category)

            # mutate here
            if 'handling' in sub_data:
                sub_category.handling = sub_data['handling']

            sub_category.save()


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0054_extra_category_name_changes'),
    ]

    operations = [
        migrations.RunPython(change_categories),
    ]
