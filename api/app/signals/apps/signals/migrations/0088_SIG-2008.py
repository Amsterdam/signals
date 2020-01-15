from django.db import migrations


def SIG_2008(apps, schema_editor):
    """
    SIG-2008 [BE] Aanpassen verantwoordelijke afdeling

    Asbest / Accu > Was (ASC, THOR), wordt (THOR)
    Handhaving op afval > Was (ASC, THOR) wordt (THOR)
    Boom - illegale kap > Was (ASC, THOR), wordt (THOR)
    Geluidsoverlast installaties > Was (VTH), wordt (ASC, VTH)
    Geluidsoverlast muziek > Was (VTH), wordt (ASC, VTH)
    Overige bedrijven / horeca > Was (VTH), wordt (ASC, VTH)
    Overlast terrassen > Was (VTH), wordt (ASC, VTH)
    Stankoverlast > Was (VTH), wordt (ASC, VTH)
    Hinderlijk geplaatst object > Was (ASC, THOR), wordt (ASC, VTH)
    Stank- / geluidoverlast > Was (THOR, VTH), wordt (ASC, THOR, VTH)
    Verkeerssituaties > Was (STW, V&OR), wordt (STW)

    :param apps:
    :param schema_editor:
    :return:
    """
    Category = apps.get_model('signals', 'Category')
    Department = apps.get_model('signals', 'Department')

    asc = Department.objects.get(code='ASC')
    thor = Department.objects.get(code='THO')
    vth = Department.objects.get(code='VTH')
    stw = Department.objects.get(code='STW')

    # Asbest / Accu > Was (ASC, THOR), wordt (THOR)
    category = Category.objects.get(slug='asbest-accu', parent__isnull=False)
    category.departments.clear()
    category.departments.add(thor)

    # Handhaving op afval > Was (ASC, THOR) wordt (THOR)
    category = Category.objects.get(slug='handhaving-op-afval', parent__isnull=False)
    category.departments.clear()
    category.departments.add(thor)

    # Boom - illegale kap > Was (ASC, THOR), wordt (THOR)
    category = Category.objects.get(slug='boom-illegale-kap', parent__isnull=False)
    category.departments.clear()
    category.departments.add(thor)

    # Geluidsoverlast installaties > Was (VTH), wordt (ASC, VTH)
    category = Category.objects.get(slug='geluidsoverlast-installaties', parent__isnull=False)
    category.departments.clear()
    category.departments.add(asc)
    category.departments.add(vth)

    # Geluidsoverlast muziek > Was (VTH), wordt (ASC, VTH)
    category = Category.objects.get(slug='geluidsoverlast-muziek', parent__isnull=False)
    category.departments.clear()
    category.departments.add(asc)
    category.departments.add(vth)

    # Overige bedrijven / horeca > Was (VTH), wordt (ASC, VTH)
    category = Category.objects.get(slug='overig-horecabedrijven', parent__isnull=False)
    category.departments.clear()
    category.departments.add(asc)
    category.departments.add(vth)

    # Overlast terrassen > Was (VTH), wordt (ASC, VTH)
    category = Category.objects.get(slug='overlast-terrassen', parent__isnull=False)
    category.departments.clear()
    category.departments.add(asc)
    category.departments.add(vth)

    # Stankoverlast > Was (VTH), wordt (ASC, VTH)
    category = Category.objects.get(slug='stankoverlast', parent__isnull=False)
    category.departments.clear()
    category.departments.add(asc)
    category.departments.add(vth)

    # Hinderlijk geplaatst object > Was (ASC, THOR), wordt (ASC, VTH)
    category = Category.objects.get(slug='hinderlijk-geplaatst-object', parent__isnull=False)
    category.departments.clear()
    category.departments.add(asc)
    category.departments.add(vth)

    # Stank - / geluidoverlast > Was(THOR, VTH), wordt(ASC, THOR, VTH)
    category = Category.objects.get(slug='stank-geluidsoverlast', parent__isnull=False)
    category.departments.clear()
    category.departments.add(asc)
    category.departments.add(thor)
    category.departments.add(vth)

    # Verkeerssituaties > Was (STW, V&OR), wordt (STW)
    category = Category.objects.get(slug='verkeerssituaties', parent__isnull=False)
    category.departments.clear()
    category.departments.add(stw)


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0087_SIG-1987_SIG-1830_wonen'),
    ]

    operations = [
        migrations.RunPython(SIG_2008, None),  # Rollback not supported
    ]
