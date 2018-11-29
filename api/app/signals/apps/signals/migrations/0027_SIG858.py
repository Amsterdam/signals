from django.db import migrations
from django.utils.text import slugify


def create_new_categories(apps, schema_editor):
    main_category_model = apps.get_model('signals', 'MainCategory')

    main_category, main_category_created = main_category_model.objects.get_or_create(
        name='Wegsleep',
        slug='wegsleep',
    )

    departments_model = apps.get_model('signals', 'Department')
    departments = departments_model.objects.filter(pk__in=[4, 6, 12])

    sub_category_model = apps.get_model('signals', 'SubCategory')

    new_sub_categories = ['TVM', 'Invalidenparkeerplaats', 'Laad- en losplaatsen',
                          'Overig wegsleep', ]

    for new_sub_category in new_sub_categories:
        sub_category, sub_category_created = sub_category_model.objects.get_or_create(
            main_category=main_category,
            slug=slugify(new_sub_category),
            name=new_sub_category,
            handling='I5DMC',
            is_active=True,
        )

        if departments.count():
            for department in departments:
                sub_category.departments.add(department)
            sub_category.save()


def remove_new_categories(apps, schema_editor):
    main_category_model = apps.get_model('signals', 'MainCategory')

    try:
        main_category = main_category_model.objects.get(slug='wegsleep')

        # Delete all sub categories for the main category
        main_category.sub_categories.all().delete()

        # Delete the main category
        main_category.delete()
    except main_category_model.DoesNotExist:
        # The main category does not exists so no need to delete it
        pass


class Migration(migrations.Migration):
    """
    SIG-858 [BE] Nieuwe (sub)categorieen; Wegsleep

    This migration will add the new categories for Wegsleep

    Main category:
     - Wegsleep

    Sub categories:
     - TVM
     - Invalidenparkeerplaats
     - Laad- en losplaatsen
     - Overig wegsleep
    """
    dependencies = [
        ('signals', '0026_history'),
    ]

    operations = [
        migrations.RunPython(create_new_categories, remove_new_categories),
    ]
