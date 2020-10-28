from django.db import migrations


def _migrate_directing_departments_to_generic_relation(apps, schema_editor):
    DirectingDepartments = apps.get_model('signals', 'DirectingDepartments')
    SignalDepartments = apps.get_model('signals', 'SignalDepartments')

    # duplicate directing department relation to generic relation (in preperation for deletion)
    for dp in DirectingDepartments.objects.all().order_by('created_by'):
        sp = SignalDepartments.objects.create(**{
            '_signal': dp._signal,
            'relation_type': SignalDepartments.REL_DIRECTING,
            'created_by': dp.created_by
        })
        sp.departments.set(dp.departments.all())
        sp.save()
        sp._signal.directing_departments_assignment = sp
        sp._signal.save()


def _reverse_migrate_directing_departments_to_generic_relation(apps, schema_editor):
    SignalDepartments = apps.get_model('signals', 'SignalDepartments')
    SignalDepartments.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('signals', '0123_auto_20200908_0945'),
    ]

    operations = [
        migrations.RunPython(
            _migrate_directing_departments_to_generic_relation,
            _reverse_migrate_directing_departments_to_generic_relation
        ),
    ]
