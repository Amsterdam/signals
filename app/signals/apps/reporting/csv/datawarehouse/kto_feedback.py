# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Gemeente Amsterdam
import os

from django.db.models import CharField, F, Func, TextField, Value
from django.db.models.functions import Cast, Coalesce, NullIf

from signals.apps.feedback.models import Feedback
from signals.apps.reporting.csv.utils import map_choices, queryset_to_csv_file, reorder_csv


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

    queryset = Feedback.objects.values(
        '_signal_id',
        'text_extra',
        'created_at',
        'submitted_at',

        _text=Coalesce(Cast(NullIf('text', Value('', output_field=CharField())), output_field=CharField()),
                       Cast('text_list__0', output_field=CharField()),
                       Value('', output_field=CharField())),
        _is_satisfied=map_choices('is_satisfied', [(True, 'True'), (False, 'False')]),
        _allows_contact=map_choices('allows_contact', [(True, 'True'), (False, 'False')]),
        _text_list=Func(F('text_list'), function='to_jsonb', output_field=TextField(),
                        function_kwargs={'indent': 4, 'ensure_ascii': False}),
    ).filter(submitted_at__isnull=False)

    csv_file = queryset_to_csv_file(queryset, os.path.join(location, file_name))

    ordered_field_names = ['_signal_id', 'is_satisfied', 'allows_contact', 'text',
                           'text_extra', 'created_at', 'submitted_at', 'text_list']
    reorder_csv(csv_file.name, ordered_field_names)

    return csv_file.name
