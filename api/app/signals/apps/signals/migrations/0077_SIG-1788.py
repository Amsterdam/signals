"""
Fix SIG-1788
"""
from django.db import migrations


def _migrate(apps, schema_editor):
    Department = apps.get_model('signals', 'Department')

    department_asc = Department.objects.get(code='ASC')
    department_stw = Department.objects.get(code='STW')
    department_tho = Department.objects.get(code='THO')

    Category = apps.get_model('signals', 'Category')

    # Uitwerpselen
    # Add: ASC
    category_uitwerpselen = Category.objects.filter(slug='hondenpoep', parent__isnull=False).first()
    category_uitwerpselen.departments.add(department_asc)

    # Lozing / dumping / bodemverontreiniging
    # Add: ASC, STW, THOR
    # Remove: OMG
    category_lozing_dumping_bodemverontreiniging = Category.objects.filter(
        slug='lozing-dumping-bodemverontreiniging', parent__isnull=False
    ).first()
    category_lozing_dumping_bodemverontreiniging.departments.clear()
    category_lozing_dumping_bodemverontreiniging.departments.add(department_asc)
    category_lozing_dumping_bodemverontreiniging.departments.add(department_stw)
    category_lozing_dumping_bodemverontreiniging.departments.add(department_tho)


def _rollback(apps, schema_editor):
    Department = apps.get_model('signals', 'Department')

    department_asc = Department.objects.get(code='ASC')
    department_omg = Department.objects.get(code='OMG')

    Category = apps.get_model('signals', 'Category')

    # Uitwerpselen
    # Remove: ASC
    category_uitwerpselen = Category.objects.filter(slug='hondenpoep', parent__isnull=False).first()
    category_uitwerpselen.departments.remove(department_asc)

    # Lozing / dumping / bodemverontreiniging
    # Remove: ASC, STW, THOR
    # Add: OMG
    category_lozing_dumping_bodemverontreiniging = Category.objects.filter(
        slug='lozing-dumping-bodemverontreiniging', parent__isnull=False
    ).first()
    category_lozing_dumping_bodemverontreiniging.departments.clear()
    category_lozing_dumping_bodemverontreiniging.departments.add(department_omg)


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0076_unstick_signals'),
    ]

    operations = [
        migrations.RunPython(_migrate, _rollback),
    ]
