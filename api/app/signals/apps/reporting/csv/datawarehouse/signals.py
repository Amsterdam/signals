"""
Dump CSV of SIA tables matching the old, agreed-upon, format.
"""
import logging
import os

from django.db.models import CharField, F, Value
from django.db.models.functions import Cast, Coalesce

from signals.apps.reporting.csv.utils import queryset_to_csv_file, reorder_csv
from signals.apps.signals.models import Signal

logger = logging.getLogger(__name__)


def create_signals_csv(location: str) -> str:
    """
    Create the CSV file with all `Signal` objects.

    :param location: Directory for saving the CSV file
    :returns: Path to CSV file
    """
    queryset = Signal.objects.annotate(
        image=Value(None, output_field=CharField()),
    ).values(
        'id',
        'source',
        'text',
        'text_extra',
        'incident_date_start',
        'incident_date_end',
        'created_at',
        'updated_at',
        'operational_date',
        'expire_date',
        'image',
        'upload',
        'directing_departments_assignment_id',
        'category_assignment_id',
        'location_id',
        'reporter_id',
        'status_id',

        signal_uuid=F('signal_id'),
        _priority=F('priority__priority'),
        priority_created_at=F('priority__created_at'),
        _parent=F('parent_id'),
        type=F('type_assignment__name'),
        type_created_at=F('type_assignment__created_at'),
        _extra_properties=Coalesce(Cast('extra_properties', output_field=CharField()),
                                   Value('null', output_field=CharField()))
    ).order_by('created_at')

    csv_file = queryset_to_csv_file(queryset, os.path.join(location, 'signals.csv'))

    ordered_field_names = ['id', 'signal_uuid', 'source', 'text', 'text_extra', 'incident_date_start',
                           'incident_date_end', 'created_at', 'updated_at', 'operational_date', 'expire_date', 'image',
                           'upload', 'extra_properties', 'category_assignment_id', 'location_id', 'reporter_id',
                           'status_id', 'priority', 'priority_created_at', 'parent', 'type', 'type_created_at',
                           'directing_departments_assignment_id', ]
    reorder_csv(csv_file.name, ordered_field_names)

    return csv_file.name


def create_signals_assigned_user_csv(location: str) -> str:
    """
    Create the CSV file with all `Signal - assgined user relation` objects.

    :param location: Directory for saving the CSV file
    :returns: Path to CSV file
    """
    queryset = Signal.objects.annotate(
        image=Value(None, output_field=CharField()),
    ).values(
        'id',
        assigned_to=F('user_assignment__user__email'),
    ).exclude(user_assignment__user__isnull=True).exclude(user_assignment__user__email__exact='').order_by('created_at')

    csv_file = queryset_to_csv_file(queryset, os.path.join(location, 'signals_assigned_user.csv'))

    ordered_field_names = ['id', 'assigned_to', ]
    reorder_csv(csv_file.name, ordered_field_names)

    return csv_file.name
