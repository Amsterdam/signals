import os

from signals.apps.feedback.models import Feedback
from signals.apps.reporting.csv.datawarehouse.utils import (
    map_choices,
    queryset_to_csv_file,
    reorder_csv
)


def create_kto_feedback_csv(location: str) -> str:
    """
    Create CSV file with all `Feedback` objects.

    :param location: Directory for saving the CSV file
    :returns: Path to CSV file
    """
    environment = os.getenv('ENVIRONMENT')

    if environment is None:
        raise EnvironmentError('ENVIRONMENT env variable not set')
    elif environment.upper() not in ['PRODUCTION', 'ACCEPTANCE']:
        raise EnvironmentError('ENVIRONMENT env variable is wrong {}'.format(environment))

    file_name = f'kto-feedback-{environment}.csv'

    # TODO Fix order of fields
    queryset = Feedback.objects.values(
        '_signal_id',
        'text',
        'text_extra',
        'created_at',
        'submitted_at',
        _is_satisfied=map_choices('is_satisfied', [(True, 'True'), (False, 'False')]),
        _allows_contact=map_choices('allows_contact', [(True, 'True'), (False, 'False')]),
    ).filter(submitted_at__isnull=False)

    csv_file = queryset_to_csv_file(queryset, os.path.join(location, file_name))

    ordered_field_names = ['_signal_id', 'is_satisfied', 'allows_contact', 'text', 'text_extra', 'created_at',
                           'submitted_at', ]
    reorder_csv(csv_file.name, ordered_field_names)

    return csv_file.name
