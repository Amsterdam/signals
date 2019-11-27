from django.db import migrations


def _SIG_1900(apps, schema_editor):
    """
    SIG-1900 [BE] Nieuwe subcategorie 'Parkeerautomaten'

    · Nieuwe subcategorie “Parkeerautomaten” in de hoofdcategorie “Wegen, verkeer, straatmeubilair”
    · Eigenaar: “V&OR”
    · Afhandeltermijn: 5 dagen
    · Servicebelofte: “Uw melding wordt ingepland: wij laten u binnen 5 werkdagen weten hoe en
      wanneer uw melding wordt afgehandeld. Dat doen we via e-mail.”

    :param apps:
    :param schema_editor:
    :return:
    """
    Category = apps.get_model('signals', 'Category')
    Department = apps.get_model('signals', 'Department')

    main_category = Category.objects.get(name='Wegen, verkeer, straatmeubilair',
                                         parent__isnull=True)

    if not Category.objects.filter(parent=main_category, name='Parkeerautomaten').exists():
        # Category does not exist
        department = Department.objects.get(code='VOR')

        sub_category = Category.objects.create(parent=main_category,
                                               name='Parkeerautomaten',
                                               handling='I5DMC')

        sub_category.departments.add(department)

        ServiceLevelObjective = apps.get_model('signals', 'ServiceLevelObjective')
        ServiceLevelObjective.objects.create(category=sub_category,
                                             n_days=5,
                                             use_calendar_days=False)


def _SIG_1913(apps, schema_editor):
    """
    SIG-1913 [BE] De verantwoordelijke partij voor de SIA-categorie “Drijfvuil in bevaarbaar water”
             moet aangepast worden naar “WAT”

    :param apps:
    :param schema_editor:
    :return:
    """
    Category = apps.get_model('signals', 'Category')
    Department = apps.get_model('signals', 'Department')

    department = Department.objects.get(code='WAT')

    sub_category = Category.objects.get(slug='drijfvuil', parent__isnull=False)
    sub_category.departments.clear()
    sub_category.departments.add(department)


def _SIG_1913_rollback(apps, schema_editor):
    """
    Rollback functionality for:

    SIG-1913 [BE] De verantwoordelijke partij voor de SIA-categorie “Drijfvuil in bevaarbaar water”
             moet aangepast worden naar “WAT”

    :param apps:
    :param schema_editor:
    :return:
    """
    Category = apps.get_model('signals', 'Category')
    Department = apps.get_model('signals', 'Department')

    department = Department.objects.get(code='STW')

    sub_category = Category.objects.get(slug='drijfvuil', parent__isnull=False)
    sub_category.departments.add(department)


def _SIG_1874(apps, schema_editor):
    """
    SIG-1874 [BE] Aanpassen afhandeltermijn voor de subcategorie “Overig dieren”
             (onderdeel van Overlast van dieren) naar vijf dagen.

    In SIA staat de afhandeltermijn voor de subcategorie “Overig dieren”
    (onderdeel van Overlast van dieren) op drie (3) dagen. Dit moet vijf (5) dagen zijn.
    Kunnen jullie dit aub in SIA aanpassen?

    :param apps:
    :param schema_editor:
    :return:
    """
    Category = apps.get_model('signals', 'Category')

    sub_category = Category.objects.get(slug='overig-dieren', parent__isnull=False)
    sub_category.handling = 'I5DMC'  # HANDLING_I5DMC instead of HANDLING_REST
    sub_category.save()

    ServiceLevelObjective = apps.get_model('signals', 'ServiceLevelObjective')
    slo = ServiceLevelObjective.objects.get(category_id=sub_category.pk)
    slo.n_days = 5  # 5 working days instead of 3
    slo.save()


def _SIG_1874_rollback(apps, schema_editor):
    """
    Rollback functionality for:

    SIG-1874 [BE] Aanpassen afhandeltermijn voor de subcategorie “Overig dieren”
             (onderdeel van Overlast van dieren) naar vijf dagen.

    In SIA staat de afhandeltermijn voor de subcategorie “Overig dieren”
    (onderdeel van Overlast van dieren) op drie (3) dagen. Dit moet vijf (5) dagen zijn.
    Kunnen jullie dit aub in SIA aanpassen?

    :param apps:
    :param schema_editor:
    :return:
    """
    Category = apps.get_model('signals', 'Category')

    sub_category = Category.objects.get(slug='overig-dieren', parent__isnull=False)
    sub_category.handling = 'REST'  # Rollback to the original value HANDLING_REST
    sub_category.save()

    ServiceLevelObjective = apps.get_model('signals', 'ServiceLevelObjective')
    slo = ServiceLevelObjective.objects.get(category_id=sub_category.pk)
    slo.n_days = 3  # Rollback to the original value of 3 working days
    slo.save()


def _SIG_1831(apps, schema_editor):
    """
    SIG-1831 [BE] de subcategorie “Put/ riolering verstopt” aan STW (Stadswerken)

    De subcategorie “Put/ riolering verstopt” moet toegewezen worden aan STW (Stadswerken)
    ipv WAT (Waternet).

    :param apps:
    :param schema_editor:
    :return:
    """
    Category = apps.get_model('signals', 'Category')
    Department = apps.get_model('signals', 'Department')

    department = Department.objects.get(code='STW')

    sub_category = Category.objects.get(slug='put-riolering-verstopt', parent__isnull=False)
    sub_category.departments.clear()
    sub_category.departments.add(department)


def _SIG_1831_rollback(apps, schema_editor):
    """
    Rollback functionality for:

    SIG-1831 [BE] de subcategorie “Put/ riolering verstopt” aan STW (Stadswerken)

    De subcategorie “Put/ riolering verstopt” moet toegewezen worden aan STW (Stadswerken)
    ipv WAT (Waternet).

    :param apps:
    :param schema_editor:
    :return:
    """
    Category = apps.get_model('signals', 'Category')
    Department = apps.get_model('signals', 'Department')

    department = Department.objects.get(code='WAT')

    sub_category = Category.objects.get(slug='put-riolering-verstopt', parent__isnull=False)
    sub_category.departments.clear()
    sub_category.departments.add(department)


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0082_auto_20191113_1544'),
    ]

    operations = [
        migrations.RunPython(_SIG_1900, None),  # Adding a category cannot be reversed
        migrations.RunPython(_SIG_1913, _SIG_1913_rollback),
        migrations.RunPython(_SIG_1874, _SIG_1874_rollback),
        migrations.RunPython(_SIG_1831, _SIG_1831_rollback),
    ]
