from django.conf import settings
from django.db import migrations


def initial_data_contrib_site(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.update_or_create(
        id=settings.SITE_ID,
        defaults={
            'domain': settings.SITE_DOMAIN,
            'name': settings.SITE_NAME,
        })


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0018_auto_20181003_1206'),
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.RunPython(initial_data_contrib_site),
    ]
