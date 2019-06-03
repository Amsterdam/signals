"""Category changes see SIG-1148."""
from django.db import migrations
from django.utils.text import slugify

ADD = {
    'wegen-verkeer-straatmeubilair': [
        {
            'name': 'Lantaarnpaal / Straatverlichting',
            'handling': 'KLOKLICHTZC',
            'departments': ['ASC'],
        },
    ]
}

REMOVE = {
    'overlast-bedrijven-en-horeca': ['stank-horecabedrijven'],
    'wegen-verkeer-straatmeubilair': ['straatverlichting-openbare-klok'],
}


def add_categories(apps, schema_editor):
    Category = apps.get_model('signals', 'Category')
    Department = apps.get_model('signals', 'Department')

    for main_slug, data in ADD.items():
        if not data:
            continue

        main_category = Category.objects.get(slug=main_slug, parent__isnull=True)
        for new_sub_category_data in data:
            departments = Department.objects.filter(
                code__in=new_sub_category_data['departments']
            )

            cat_qs = Category.objects.filter(
                parent=main_category,
                name=new_sub_category_data['name'],
            )

            assert not cat_qs.exists()
            assert new_sub_category_data['name']
            assert slugify(new_sub_category_data['name'])

            new_category = Category(
                parent=main_category,
                handling=new_sub_category_data['handling'],
                name=new_sub_category_data['name'],
                slug=slugify(new_sub_category_data['name']),
                is_active=True,
            )
            new_category.save()
            new_category.departments.set(departments)
            new_category.save()


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


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0044_category_changes'),
    ]

    operations = [
        migrations.RunPython(remove_categories),
        migrations.RunPython(add_categories),
    ]
