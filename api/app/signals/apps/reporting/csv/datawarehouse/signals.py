"""
Dump CSV of SIA tables matching the old, agreed-upon, format.
"""
import logging
import os

from django.db.models import CharField, F, Max, Value

from signals.apps.reporting.csv.datawarehouse.utils import queryset_to_csv_file, reorder_csv
from signals.apps.signals.models import Signal

logger = logging.getLogger(__name__)


def create_signals_csv(location: str) -> str:
    """
    Create the CSV file with all `Signal` objects.

    :param location: Directory for saving the CSV file
    :returns: Path to CSV file
    """
    queryset = Signal.objects.annotate(
        type_assignment_id=Max('types__id'),
        image=Value(None, output_field=CharField())
    ).filter(
        types__id=F('type_assignment_id'),
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
        'extra_properties',
        'category_assignment_id',
        'location_id',
        'reporter_id',
        'status_id',

        signal_uuid=F('signal_id'),
        _priority=F('priority__priority'),
        priority_created_at=F('priority__created_at'),
        _parent=F('parent_id'),
        type=F('types__name'),
        type_created_at=F('types__created_at')
    )

    csv_file = queryset_to_csv_file(queryset, os.path.join(location, 'signals.csv'))

    ordered_field_names = ['id', 'signal_uuid', 'source', 'text', 'text_extra', 'incident_date_start',
                           'incident_date_end', 'created_at', 'updated_at', 'operational_date', 'expire_date', 'image',
                           'upload', 'extra_properties', 'category_assignment_id', 'location_id', 'reporter_id',
                           'status_id', 'priority', 'priority_created_at', 'parent', 'type', 'type_created_at', ]
    reorder_csv(csv_file.name, ordered_field_names)

    return csv_file.name
