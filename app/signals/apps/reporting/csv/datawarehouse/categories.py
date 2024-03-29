# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
import os

from django.contrib.postgres.aggregates import StringAgg
from django.db.models import CharField, F, Q, Value
from django.db.models.functions import Cast, Coalesce

from signals.apps.reporting.csv.utils import queryset_to_csv_file, reorder_csv
from signals.apps.signals.models import CategoryAssignment, ServiceLevelObjective


def create_category_assignments_csv(location: str) -> str:
    """
    Create CSV file with all `CategoryAssignment` objects.

    :param location: Directory for saving the CSV file
    :returns: Path to CSV file
    """
    queryset = CategoryAssignment.objects.values(
        'id',
        'created_at',
        'updated_at',
        'deadline',
        'deadline_factor_3',
        '_signal_id',
        main=F('category__parent__name'),
        sub=F('category__name'),
        _departments=StringAgg('category__departments__name', delimiter=', ',
                               filter=Q(category__categorydepartment__is_responsible=True)),
        _extra_properties=Coalesce(Cast('extra_properties', output_field=CharField()),
                                   Value('null', output_field=CharField()))
    ).order_by(
        'id'
    )

    csv_file = queryset_to_csv_file(queryset, os.path.join(location, 'categories.csv'))

    ordered_field_names = ['id', 'main', 'sub', 'departments', 'created_at', 'updated_at', 'extra_properties',
                           '_signal_id', 'deadline', 'deadline_factor_3', ]
    reorder_csv(csv_file.name, ordered_field_names)

    return csv_file.name


def create_category_sla_csv(location: str) -> str:
    """
    Create CSV file with all `ServiceLevelObjective` objects.

    :param location: Directory for saving the CSV file
    :returns: Path to CSV file
    """
    queryset = ServiceLevelObjective.objects.values(
        'id',
        'n_days',
        'use_calendar_days',
        'created_at',
        main=F('category__parent__name'),
        sub=F('category__name'),
    ).order_by(
        'category_id',
        '-created_at'
    )

    csv_file = queryset_to_csv_file(queryset, os.path.join(location, 'sla.csv'))

    ordered_field_names = ['id', 'main', 'sub', 'n_days', 'use_calendar_days', 'created_at', ]
    reorder_csv(csv_file.name, ordered_field_names)

    return csv_file.name
