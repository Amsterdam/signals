from django.db import migrations, models
from django.utils.text import slugify

add = {
    # Main
    'Afval': [
        # Sub, departments, handling
        ('Container voor papier is stuk', ['ASC', 'Afval en grondstoffen', ], 'A3DMC', ),
        ('Container voor papier is vol', ['ASC', 'Afval en grondstoffen', ], 'A3DMC', ),
        ('Handhaving op afval', ['ASC', 'THOR', ], 'A3DMC', ),
    ],
    # Main
    'Wegen, verkeer, straatmeubilair': [
        # Sub, departments
        ('Autom. Verzinkbare palen', ['V&OR - VIS', ], 'A3WMC', ),
        ('Bewegwijzering', ['V&OR - VIS', ], 'A3WEC', ),
        ('Camerasystemen', ['V&OR - VIS', ], 'A3WEC', ),
        ('Lichthinder', ['V&OR OVL', ], 'STOPEC', ),
        ('Parkeer verwijssysteem', ['V&OR - VIS', ], 'A3WEC', ),
        ('Stadsplattegronden', ['V&OR - VIS', ], 'A3WEC', ),
        ('Verdeelkasten / bekabeling', ['V&OR - VIS', ], 'A3WEC', ),
        ('Verlichting netstoring', ['V&OR OVL', ], 'STOPEC', ),
    ],
    # Main
    'Ondermijning': [
        # Sub, departments, handling
        ('Vermoeden', ['Openbare Orde & Veiligheid', ], 'ONDERMIJNING', ),
    ],
    # Main
    'Overig': [
        # Sub, departments, handling
        ('Overige dienstverlening', ['CCA', 'ASC', ], 'REST', ),
    ]
}


def forward_categories(apps, schema_editor):
    category_model = apps.get_model('signals', 'Category')
    departments_model = apps.get_model('signals', 'Department')

    # Create the new departments
    departments_model.objects.create(name='V&OR - VIS', code='VIS')
    department_oov = departments_model.objects.create(name='Openbare Orde & Veiligheid', code='OOV')

    # Create the new "main" categories
    category_ondermijning = category_model.objects.create(name='Ondermijning',
                                                          slug=slugify('Ondermijning'),
                                                          handling='ONDERMIJNING')
    category_ondermijning.departments.add(department_oov)
    category_ondermijning.save()

    # Create the new "sub" categories
    for parent, children in add.items():
        parent_category = category_model.objects.get(name=parent, parent__isnull=True)

        for child in children:
            child_category = category_model.objects.create(name=child[0],
                                                           slug=slugify(child[0]),
                                                           parent=parent_category,
                                                           handling=child[2])

            departments = departments_model.objects.filter(name__in=child[1])
            if departments.exists():
                for department in departments:
                    child_category.departments.add(department)
                child_category.save()

    # We only soft delete the following categories
    category_model.objects.filter(
        name__in=[
            'Vuurwerkoverlast',
            'Personen op het water',
        ],
        parent__name='Overlast van en door personen of groepen'
    ).update(is_active=False)

    category_model.objects.filter(
        name='Deelfiets',
        parent__name='Overlast in de openbare ruimte'
    ).update(is_active=False)

    # Fix the departments for "auto-scooter-bromfietswrak"
    category = category_model.objects.get(slug='auto-scooter-bromfietswrak')
    category.departments.clear()
    category.save()

    departments = departments_model.objects.filter(name__in=['ASC', 'THOR'])
    for department in departments:
        category.departments.add(department)

    category.save()


class Migration(migrations.Migration):
    """
    SIG-1014 Aanpassen categorien

    This migration will add the new categories:
    -

    And remove the categories:
    -
    """
    dependencies = [
        ('signals', '0039_auto_20190314_1359'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='handling',
            field=models.CharField(
                choices=[('A3DMC', 'A3DMC'), ('A3DEC', 'A3DEC'), ('A3WMC', 'A3WMC'),
                         ('A3WEC', 'A3WEC'), ('I5DMC', 'I5DMC'), ('STOPEC', 'STOPEC'),
                         ('KLOKLICHTZC', 'KLOKLICHTZC'), ('GLADZC', 'GLADZC'),
                         ('A3DEVOMC', 'A3DEVOMC'), ('WS1EC', 'WS1EC'), ('WS2EC', 'WS2EC'),
                         ('REST', 'REST'), ('ONDERMIJNING', 'ONDERMIJNING')], default='REST',
                max_length=20),
        ),
        migrations.RunPython(forward_categories),
    ]
