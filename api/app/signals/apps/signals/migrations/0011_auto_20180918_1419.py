from django.db import migrations
from django.utils.text import slugify


def populate_sub_category_field(apps, schema_editor):
    """Populate `sub_category` field on `Category` model based on current category string."""
    Category = apps.get_model('signals', 'Category')
    SubCategory = apps.get_model('signals', 'SubCategory')

    # Getting default/fallback sub category "Overig".
    sub_category_overig = SubCategory.objects.get(code='F73')

    for category in Category.objects.all():
        # Fixing "alias" for specific sub category.
        if category.sub == 'Auto- /scooter- / bromfiets(wrak)':
            category.sub = 'Auto- / scooter- / bromfiets(wrak)'

        # Getting the related sub category object.
        try:
            sub_category = SubCategory.objects.get(name__iexact=category.sub)
        except SubCategory.DoesNotExist:
            # No existing sub category found. Set sub category to "overig" and continue.
            category.sub_category = sub_category_overig
        else:
            category.sub_category = sub_category

        category.save()


def populate_slug_fields(apps, schema_editor):
    """Populate `slug` fields on category models."""
    MainCategory = apps.get_model('signals', 'MainCategory')
    SubCategory = apps.get_model('signals', 'SubCategory')

    for main_category in MainCategory.objects.all():
        main_category.slug = slugify(main_category.name)
        main_category.save()

    for sub_category in SubCategory.objects.all():
        sub_category.slug = slugify(sub_category.name)
        sub_category.save()


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0010_auto_20180918_1416'),
    ]

    operations = [
        migrations.RunPython(populate_sub_category_field),
        migrations.RunPython(populate_slug_fields),
    ]
