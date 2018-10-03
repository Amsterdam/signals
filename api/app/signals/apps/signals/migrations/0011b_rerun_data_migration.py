from django.db import migrations


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


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0011_auto_20180918_1419'),
    ]

    operations = [
        migrations.RunPython(populate_sub_category_field),
    ]
