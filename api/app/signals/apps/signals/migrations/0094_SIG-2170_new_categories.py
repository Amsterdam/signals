from django.db import migrations, models


def SIG_2170(apps, schema_editor):
    """
    SIG-2170 [BE] 7 nieuwe subcategorien

    NIEUW: Boom - boomstob (Parent
            * Parent category slug -> openbaar-groen-en-water
            * Responsible department codes -> STW
            * Handling -> HANDLING_I5DMC
            * SLA ???
    NIEUW: Container glas kapot
            * Parent category slug -> afval
            * Responsible department codes -> AEG
            * Handling -> HANDLING_A3WMC
            * SLA 3 werkdagen
    NIEUW: Container glas vol
            * Parent category slug -> afval
            * Responsible department codes -> AEG
            * Handling -> HANDLING_A3WMC
            * SLA 3 werkdagen
    NIEUW: Blokkade van de vaarweg
            * Parent category slug -> ???
            * Responsible department codes -> ASC, AEG, WAT
            * Handling -> ???
            * SLA 3 weekdagen
    NIEUW: Olie op het water
            * Parent category slug -> ???
            * Responsible department codes -> ASC, AEG, WAT
            * Handling -> ???
            * SLA 3 weekdagen
    NIEUW: Oplaadpunt
            * Parent category slug -> wegen-verkeer-straatmeubilair
            * Responsible department codes -> VOR
            * Handling -> ???
            * SLA 5 weekdagen
    NIEUW: Tijdelijke Verkeersmaatregelen
            * Parent category slug -> wegen-verkeer-straatmeubilair
            * Responsible department codes -> STW
            * Handling -> HANDLING_A3DEC
            * SLA ???
    """
    ServiceLevelObjective = apps.get_model('signals', 'ServiceLevelObjective')

    Department = apps.get_model('signals', 'Department')
    stw = Department.objects.get(code='STW')
    aeg = Department.objects.get(code='AEG')
    asc = Department.objects.get(code='ASC')
    wat = Department.objects.get(code='WAT')
    vor = Department.objects.get(code='VOR')

    Category = apps.get_model('signals', 'Category')

    # OPENBAAR GROEN EN WATER ------------------------------------------------------------------------------------------

    parent_category = Category.objects.get(slug='openbaar-groen-en-water', parent__isnull=True)

    # Boom - boomstob
    new_category = Category.objects.create(
        parent=parent_category,
        name='Boom - boomstob',
        handling='I5DMC'
    )

    # SLO 5 Werkdagen
    ServiceLevelObjective.objects.create(category=new_category, n_days=5, use_calendar_days=False)

    # All departments can view
    new_category.departments.add(*Department.objects.exclude(code='STW'),
                                 through_defaults={'is_responsible': False, 'can_view': True})
    # STW is responsible
    new_category.departments.add(stw, through_defaults={'is_responsible': True, 'can_view': True})

    # AFVAL ------------------------------------------------------------------------------------------------------------

    parent_category = Category.objects.get(slug='afval', parent__isnull=True)

    # Container glas kapot
    new_category = Category.objects.create(
        parent=parent_category,
        name='Container glas kapot',
        handling='A3WMC'
    )

    # SLO 3 weekdays
    ServiceLevelObjective.objects.create(category=new_category, n_days=3, use_calendar_days=False)

    # All departments can view
    new_category.departments.add(*Department.objects.exclude(code='AEG'),
                                 through_defaults={'is_responsible': False, 'can_view': True})
    # AEG is responsible
    new_category.departments.add(aeg, through_defaults={'is_responsible': True, 'can_view': True})

    # Container glas vol
    new_category = Category.objects.create(
        parent=parent_category,
        name='Container glas vol',
        handling='A3WMC'
    )

    # SLO 3 weekdays
    ServiceLevelObjective.objects.create(category=new_category, n_days=3, use_calendar_days=False)

    # All departments can view
    new_category.departments.add(*Department.objects.exclude(code='AEG'),
                                 through_defaults={'is_responsible': False, 'can_view': True})
    # AEG is responsible
    new_category.departments.add(aeg, through_defaults={'is_responsible': True, 'can_view': True})

    # Overlast op het water --------------------------------------------------------------------------------------------

    parent_category = Category.objects.get(slug='overlast-op-het-water', parent__isnull=True)

    # Blokkade van de vaarweg
    new_category = Category.objects.create(
        parent=parent_category,
        name='Blokkade van de vaarweg',
        handling='STOPEC3'
    )

    # SLO 3 weekdays
    ServiceLevelObjective.objects.create(category=new_category, n_days=3, use_calendar_days=True)

    # All departments can view
    new_category.departments.add(*Department.objects.exclude(code__in=['ASC', 'AEG', 'WAT']),
                                 through_defaults={'is_responsible': False, 'can_view': True})
    # ASC, AEG, WAT is responsible
    new_category.departments.add(aeg, through_defaults={'is_responsible': True, 'can_view': True})
    new_category.departments.add(asc, through_defaults={'is_responsible': True, 'can_view': True})
    new_category.departments.add(wat, through_defaults={'is_responsible': True, 'can_view': True})

    # Olie op het water
    new_category = Category.objects.create(
        parent=parent_category,
        name='Olie op het water',
        handling='STOPEC3'
    )

    # SLO 3 weekdays
    ServiceLevelObjective.objects.create(category=new_category, n_days=3, use_calendar_days=True)

    # All departments can view
    new_category.departments.add(*Department.objects.all().exclude(code__in=['ASC', 'AEG', 'WAT']),
                                 through_defaults={'is_responsible': False, 'can_view': True})
    # ASC, AEG, WAT is responsible
    new_category.departments.add(aeg, through_defaults={'is_responsible': True, 'can_view': True})
    new_category.departments.add(asc, through_defaults={'is_responsible': True, 'can_view': True})
    new_category.departments.add(wat, through_defaults={'is_responsible': True, 'can_view': True})

    # WEGEN VERKEER STRAATMEUBILAIR ------------------------------------------------------------------------------------

    parent_category = Category.objects.get(slug='wegen-verkeer-straatmeubilair', parent__isnull=True)

    # Oplaadpunt
    new_category = Category.objects.create(
        parent=parent_category,
        name='Oplaadpunt',
        handling='TECHNISCHE_STORING'
    )

    # SLO 5 weekdays
    ServiceLevelObjective.objects.create(category=new_category, n_days=5, use_calendar_days=True)

    # All departments can view
    new_category.departments.add(*Department.objects.all().exclude(code__in=['VOR']),
                                 through_defaults={'is_responsible': False, 'can_view': True})
    # VOR is responsible
    new_category.departments.add(vor, through_defaults={'is_responsible': True, 'can_view': True})

    # Tijdelijke Verkeersmaatregelen
    new_category = Category.objects.create(
        parent=parent_category,
        name='Tijdelijke Verkeersmaatregelen',
        handling='A3DEC'
    )

    # SLO 3 working days
    ServiceLevelObjective.objects.create(category=new_category, n_days=3, use_calendar_days=False)

    # All departments can view
    new_category.departments.add(*Department.objects.all().exclude(code__in=['STW']),
                                 through_defaults={'is_responsible': False, 'can_view': True})
    # STW is responsible
    new_category.departments.add(stw, through_defaults={'is_responsible': True, 'can_view': True})


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0093_merge_20200122_1646'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='handling',
            field=models.CharField(
                choices=[('A3DMC', 'A3DMC'), ('A3DEC', 'A3DEC'), ('A3WMC', 'A3WMC'), ('A3WEC', 'A3WEC'),
                         ('I5DMC', 'I5DMC'), ('STOPEC', 'STOPEC'), ('KLOKLICHTZC', 'KLOKLICHTZC'), ('GLADZC', 'GLADZC'),
                         ('A3DEVOMC', 'A3DEVOMC'), ('WS1EC', 'WS1EC'), ('WS2EC', 'WS2EC'), ('WS3EC', 'WS3EC'),
                         ('REST', 'REST'), ('ONDERMIJNING', 'ONDERMIJNING'), ('EMPTY', 'EMPTY'),
                         ('LIGHTING', 'LIGHTING'), ('GLAD_OLIE', 'GLAD_OLIE'),
                         ('TECHNISCHE_STORING', 'TECHNISCHE_STORING'), ('STOPEC3', 'STOPEC3')], default='REST',
                max_length=20),
        ),  # New Handling codes
        migrations.RunPython(SIG_2170, None),  # No rollback available when adding new categories
    ]
