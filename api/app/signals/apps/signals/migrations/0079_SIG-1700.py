"""
Fix SIG-1700
"""
from django.db import migrations


def _migrate(apps, schema_editor):
    Department = apps.get_model('signals', 'Department')

    department_asc = Department.objects.get(code='ASC')

    Category = apps.get_model('signals', 'Category')

    # overig-openbare-ruimte
    # Remove: STW, THO, VTH
    # Add: ASC
    category_overig = Category.objects.filter(slug='overig-openbare-ruimte',
                                              parent__isnull=False).first()
    category_overig.departments.clear()
    category_overig.departments.add(department_asc)


def _rollback(apps, schema_editor):
    Department = apps.get_model('signals', 'Department')

    department_stw = Department.objects.get(code='STW')
    department_tho = Department.objects.get(code='THO')
    department_vth = Department.objects.get(code='VTH')

    Category = apps.get_model('signals', 'Category')

    # overig-openbare-ruimte
    # Add: STW, THO, VTH
    # Remove: ASC
    category_overig = Category.objects.filter(slug='overig-openbare-ruimte',
                                              parent__isnull=False).first()
    category_overig.departments.clear()
    category_overig.departments.add(department_stw)
    category_overig.departments.add(department_tho)
    category_overig.departments.add(department_vth)


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0078_merge_20191023_0857'),
    ]

    operations = [
        migrations.RunPython(_migrate, _rollback),
    ]
