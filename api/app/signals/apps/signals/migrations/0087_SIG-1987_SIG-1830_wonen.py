from django.db import migrations


def SIG_1987(apps, schema_editor):
    """
    SIG-1987 [BE] Aanmaken verantwoordelijke afdeling 'Wonen'

    :param apps:
    :param schema_editor:
    :return:
    """
    Department = apps.get_model('signals', 'Department')
    Department.objects.create(code='WON', name='Wonen', is_intern=False)


def SIG_1830(apps, schema_editor):
    """
    SIG-1830 [BE] Nieuwe subcategorien wonen

    Categorie toevoegen:
    * Onderhuur en adreskwaliteit
    * Leegstand
    * Woningdelen/spookburgers

    Service belofte
    Dezelfde als de overige 3:

    “Uw melding wordt ingepland: wij laten u binnen 5 werkdagen weten hoe en wanneer uw melding wordt afgehandeld.
     Dat doen we via e-mail.”

    Woonfraude
    De categorie Woonfraude komt te vervallen. De meldingen die nu onder Woonfraude vallen moeten verplaatst
    worden naar Vakantieverhuur.

    :param apps:
    :param schema_editor:
    :return:
    """
    Category = apps.get_model('signals', 'Category')
    ServiceLevelObjective = apps.get_model('signals', 'ServiceLevelObjective')
    CategoryTranslation = apps.get_model('signals', 'CategoryTranslation')

    main_category = Category.objects.get(slug='wonen', parent__isnull=True)

    sub_category = Category.objects.create(parent=main_category,
                                           name='Onderhuur en adreskwaliteit',
                                           handling='I5DMC')
    ServiceLevelObjective.objects.create(category=sub_category,
                                         n_days=5,
                                         use_calendar_days=False)

    sub_category = Category.objects.create(parent=main_category,
                                           name='Leegstand',
                                           handling='I5DMC')
    ServiceLevelObjective.objects.create(category=sub_category,
                                         n_days=5,
                                         use_calendar_days=False)

    sub_category = Category.objects.create(parent=main_category,
                                           name='Woningdelen / spookburgers',
                                           handling='I5DMC')
    ServiceLevelObjective.objects.create(category=sub_category,
                                         n_days=5,
                                         use_calendar_days=False)

    sub_category_fraude = Category.objects.get(slug='fraude', parent_id=main_category.pk)
    sub_category_fraude.is_active = False
    sub_category_fraude.save()

    sub_category_vakantieverhuur = Category.objects.get(slug='vakantieverhuur', parent_id=main_category.pk)

    CategoryTranslation.objects.create(
        old_category=sub_category_fraude,
        new_category=sub_category_vakantieverhuur,
        text='Omdat er nieuwe categorieën zijn ingevoerd in SIA is deze melding overnieuw ingedeeld.'
    )


def link_categories_to_department(apps, schema_editor):
    """
    Connect all categories that belong to the main category "Wonen" to the department "Wonen

    :param apps:
    :param schema_editor:
    :return:
    """
    Category = apps.get_model('signals', 'Category')
    Department = apps.get_model('signals', 'Department')

    department_wonen = Department.objects.get(code='WON')
    main_category_wonen = Category.objects.get(slug='wonen', parent__isnull=True)
    main_category_wonen.departments.add(department_wonen, through_defaults={'is_responsible': True,
                                                                            'can_view': True})

    for sub_category_wonen in main_category_wonen.children.all():
        sub_category_wonen.departments.add(department_wonen, through_defaults={'is_responsible': True,
                                                                               'can_view': True})


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0086_unstick_signals'),
    ]

    operations = [
        migrations.RunPython(SIG_1987, None),  # Rollback not supported
        migrations.RunPython(SIG_1830, None),  # Rollback not supported
        migrations.RunPython(link_categories_to_department, None),  # Rollback not supported
    ]
