from django.db import migrations


def set_is_active_to_true(apps, schema_editor):
    """Set is_active to True for all existing sub categories."""
    SubCategory = apps.get_model('signals', 'SubCategory')

    for instance in SubCategory.objects.all():
        instance.is_active = True
        instance.save()


class Migration(migrations.Migration):
    dependencies = [
        ('signals', '0023_subcategory_is_active')
    ]

    operations = [
        migrations.RunPython(set_is_active_to_true),
    ]
