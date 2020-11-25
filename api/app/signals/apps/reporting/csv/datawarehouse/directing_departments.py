import os

from django.contrib.postgres.aggregates import StringAgg

from signals.apps.reporting.csv.utils import queryset_to_csv_file, reorder_csv
from signals.apps.signals.models import SignalDepartments


def create_directing_departments_csv(location: str) -> str:
    """
    Create CSV file with all `DirectingDepartments` objects.

    :param location: Directory for saving the CSV file
    :returns: Path to CSV file
    """
    queryset = SignalDepartments.objects.values(
        'id',
        'created_at',
        'updated_at',
        '_signal_id',
        _departments=StringAgg('departments__name', delimiter=', '),
    ).filter(relation_type=SignalDepartments.REL_DIRECTING).order_by(
        '_signal_id',
        '-created_at',
    )

    csv_file = queryset_to_csv_file(queryset, os.path.join(location, 'directing_departments.csv'))

    ordered_field_names = ['id', 'created_at', 'updated_at', '_signal_id', 'departments', ]
    reorder_csv(csv_file.name, ordered_field_names)

    return csv_file.name
