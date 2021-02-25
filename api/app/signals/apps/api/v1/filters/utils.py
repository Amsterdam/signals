from signals.apps.signals.models import (
    STADSDELEN,
    Area,
    AreaType,
    Buurt,
    Category,
    Department,
    Expression,
    ExpressionType,
    Signal
)
from signals.apps.signals.workflow import STATUS_CHOICES

# Helper functions to to determine available choices used for filtering


def area_code_choices():
    return [(area.code, area.code) for area in Area.objects.only('code').all().distinct()]


def area_type_code_choices():
    return [(area_type.code, area_type.code) for area_type in AreaType.objects.only('code').all().distinct()]


def area_type_choices():
    return [(c, f'{n} ({c})') for c, n in AreaType.objects.values_list('code', 'name')]


def area_choices():
    return [(c, f'{n} ({t})') for c, t, n in Area.objects.values_list('code', '_type__name', 'name')]


boolean_true_choices = [(True, 'True'), ('true', 'true'), ('True', 'True'), (1, '1')]
boolean_false_choices = [(False, 'False'), ('false', 'false'), ('False', 'False'), (0, '0')]
boolean_choices = boolean_true_choices + boolean_false_choices


def buurt_choices():
    return [(c, f'{n} ({c})') for c, n in Buurt.objects.values_list('vollcode', 'naam')]


def contact_details_choices():
    return (('none', 'none'), ('email', 'email'), ('phone', 'phone'), )


def department_choices():
    return [
        ('null', 'null'),
    ] + [(department.code, f'{department.code}') for department in Department.objects.only('code').all()]


def expression_choices():
    """
    Helper function to determine available expressions
    """
    return [(expr.name, expr.name) for expr in Expression.objects.only('name').all().distinct()]


def expression_type_choices():
    """
    Helper function to determine available expression types
    """
    return [(expr_type.name, expr_type.name) for expr_type in ExpressionType.objects.only('name').all().distinct()]


def feedback_choices():
    return (('satisfied', 'satisfied'), ('not_satisfied', 'not_satisfied'), ('not_received', 'not_received'), )


def kind_choices():
    return (('parent_signal', 'parent_signal'), ('exclude_parent_signal', 'exclude_parent_signal'),
            ('child_signal', 'child_signal'), ('signal', 'signal'), )


def status_choices():
    return [(c, f'{n} ({c})') for c, n in STATUS_CHOICES]


def source_choices():
    return [(choice, f'{choice}') for choice in Signal.objects.order_by('source').values_list('name', flat=True).distinct()]  # noqa


def stadsdelen_choices():
    return (('null', 'Niet bepaald'), ) + STADSDELEN


# Helper functions to get the correct Category queryset


def _get_child_category_queryset():
    return Category.objects.filter(parent__isnull=False)


def _get_parent_category_queryset():
    return Category.objects.filter(parent__isnull=True)


def category_choices():
    return [(category.id, f'{category.name}') for category in Category.objects.all()]
