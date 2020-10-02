import os

from django.db.models import CharField, Value
from django.db.models.functions import Cast, Coalesce

from signals.apps.reporting.csv.utils import map_choices, queryset_to_csv_file, reorder_csv
from signals.apps.signals.models import Status
from signals.apps.signals.workflow import STATUS_CHOICES


def create_statuses_csv(location: str) -> str:
    """
    Create CSV file with all `Status` objects.

    :param location: Directory for saving the CSV file
    :returns: Path to CSV file
    """
    queryset = Status.objects.values(
        'id',
        'text',
        'user',
        'target_api',
        'created_at',
        'updated_at',
        '_signal_id',
        'state',
        _extern=map_choices('extern', [(True, 'True'), (False, 'False')]),
        state_display=map_choices('state', STATUS_CHOICES),
        _extra_properties=Coalesce(Cast('extra_properties', output_field=CharField()),
                                   Value('null', output_field=CharField()))
    )

    csv_file = queryset_to_csv_file(queryset, os.path.join(location, 'statuses.csv'))

    ordered_field_names = ['id', 'text', 'user', 'target_api', 'state_display', 'extern', 'created_at', 'updated_at',
                           'extra_properties', '_signal_id', 'state', ]
    reorder_csv(csv_file.name, ordered_field_names)

    return csv_file.name
