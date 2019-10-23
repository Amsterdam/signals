from django.db import migrations

WORK_DAY = False

# No update to historic `straatverlichting-openbare-klok` sub-category.
SERVICE_LEVEL_OBJECTIVES = {
    'klok': [21, WORK_DAY],  # is active
    'lantaarnpaal-straatverlichting': [21, WORK_DAY],  # is active
}


def _set_service_level(apps, schema_editor):
    """
    Set a service level objective for each sub category.
    """
    ServiceLevelObjective = apps.get_model('signals', 'ServiceLevelObjective')
    Category = apps.get_model('signals', 'Category')

    for sub_slug, entry in SERVICE_LEVEL_OBJECTIVES.items():
        n_days, use_calendar_days = entry
        sub_cat = Category.objects.get(parent__isnull=False, slug=sub_slug)
        ServiceLevelObjective.objects.create(
            category=sub_cat, n_days=n_days, use_calendar_days=use_calendar_days)

    sub_slugs = SERVICE_LEVEL_OBJECTIVES.keys()
    assert Category.objects.filter(parent__isnull=False, slug__in=[sub_slugs]).count() == 0


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0079_SIG-1700'),
    ]
    operations = [
        migrations.RunPython(_set_service_level),
    ]
