import os

from django.db.models import BooleanField, Case, CharField, Q, Value, When

from signals.apps.reporting.csv.datawarehouse.utils import (
    map_choices,
    queryset_to_csv_file,
    reorder_csv
)
from signals.apps.signals.models import Reporter


def create_reporters_csv(location: str) -> str:
    """
    Create CSV file with all `Reporter` objects.

    :param location: Directory for saving the CSV file
    :returns: Path to CSV file
    """
    queryset = Reporter.objects.annotate(
        is_anonymized=Case(
            When(
                Q(
                    Q(email__isnull=True) | Q(email__exact='')
                ) & Q(
                    Q(phone__isnull=True) | Q(phone__exact='')
                ) & Q(
                    Q(email_anonymized=True) | Q(phone_anonymized=True)
                ),
                then=True,
            ),
            default=False,
            output_field=BooleanField()
        ),
        extra_properties=Value(None, output_field=CharField())
    ).values(
        'id',
        'email',
        'phone',
        'created_at',
        'updated_at',
        'extra_properties',
        '_signal_id',
        _is_anonymized=map_choices('is_anonymized', [(True, 'True'), (False, 'False')]),
    )

    csv_file = queryset_to_csv_file(queryset, os.path.join(location, 'reporters.csv'))

    ordered_field_names = ['id', 'email', 'phone', 'is_anonymized', 'created_at', 'updated_at', 'extra_properties',
                           '_signal_id', ]
    reorder_csv(csv_file.name, ordered_field_names)

    return csv_file.name
