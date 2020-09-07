from signals.apps.signals.models import (
    STADSDELEN,
    Area,
    AreaType,
    Buurt,
    Category,
    Department,
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


def buurt_choices():
    return [(c, f'{n} ({c})') for c, n in Buurt.objects.values_list('vollcode', 'naam')]


def contact_details_choices():
    return (('none', 'none'), ('email', 'email'), ('phone', 'phone'), )


def department_choices():
    return [(department.code, f'{department.code}') for department in Department.objects.only('code').all()]


def feedback_choices():
    return (('satisfied', 'satisfied'), ('not_satisfied', 'not_satisfied'), ('not_received', 'not_received'), )


def status_choices():
    return [(c, f'{n} ({c})') for c, n in STATUS_CHOICES]


def source_choices():
    return [(choice, f'{choice}') for choice in Signal.objects.order_by('source').values_list('source', flat=True).distinct()]  # noqa


def stadsdelen_choices():
    return (('null', 'Niet bepaald'), ) + STADSDELEN


# Helper functions to get the correct Category queryset


def _get_child_category_queryset():
    return Category.objects.filter(parent__isnull=False)


def _get_parent_category_queryset():
    return Category.objects.filter(parent__isnull=True)
