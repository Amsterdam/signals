from django.db import migrations
from django.utils.text import slugify


def create_new_categories(apps, schema_editor):
    main_category_model = apps.get_model('signals', 'MainCategory')
    main_category = main_category_model.objects.get(
        slug='overlast-in-de-openbare-ruimte',
    )

    sub_category_model = apps.get_model('signals', 'SubCategory')
    sub_category, sub_category_created = sub_category_model.objects.get_or_create(
        main_category=main_category,
        slug=slugify('Wegsleep'),
        name='Wegsleep',
        handling='A3DMC',
        is_active=True,
    )

    departments_model = apps.get_model('signals', 'Department')
    departments = departments_model.objects.filter(pk__in=[2, 6, 12])
    if departments.count():
        for department in departments:
            sub_category.departments.add(department)
        sub_category.save()


def remove_new_categories(apps, schema_editor):
    sub_category_model = apps.get_model('signals', 'SubCategory')

    try:
        sub_category = sub_category_model.objects.get(slug='wegsleep')

        # Delete the category
        sub_category.delete()
    except sub_category_model.DoesNotExist:
        # The main category does not exists so no need to delete it
        pass


class Migration(migrations.Migration):
    """
    SIG-858 [BE] Nieuwe (sub)categorieen; Wegsleep

    This migration will add the new sub category "Wegsleep"

    Main category:
     - overlast-in-de-openbare-ruimte

    Sub category:
     - Wegsleep
    """
    dependencies = [
        ('signals', '0026_history'),
    ]

    operations = [
        migrations.RunPython(create_new_categories, remove_new_categories),
    ]
