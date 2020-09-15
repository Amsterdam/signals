from django.db import migrations


def _rename_eigen_organisatie_to_interne_melding(apps, schema_editor):
    Signal = apps.get_model('signals', 'Signal')
    queryset = Signal.objects.filter(source__iexact='Eigen organisatie')
    queryset.update(source='Interne melding')


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0118_DEELMELDINGEN_HISTORY'),
    ]

    operations = [
        migrations.RunPython(_rename_eigen_organisatie_to_interne_melding, None),  # No reverse possible
    ]
