# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
import os

from django.db.models import CharField, ExpressionWrapper, FloatField, Func, Value
from django.db.models.functions import Cast, Coalesce

from signals.apps.reporting.csv.utils import map_choices, queryset_to_csv_file, reorder_csv
from signals.apps.signals.models import STADSDELEN, Location


def create_locations_csv(location: str) -> str:
    """
    Create CSV file with all `Location` objects.

    :param location: Directory for saving the CSV file
    :returns: Path to CSV file
    """
    queryset = Location.objects.values(
        'id',
        'buurt_code',
        'address_text',
        'created_at',
        'updated_at',
        '_signal_id',
        lat=ExpressionWrapper(Func('geometrie', function='st_x'), output_field=FloatField()),
        lng=ExpressionWrapper(Func('geometrie', function='st_y'), output_field=FloatField()),
        _stadsdeel=Coalesce(map_choices('stadsdeel', STADSDELEN), Cast('area_code', output_field=CharField())),
        _address=Coalesce(Cast('address', output_field=CharField()), Value('null', output_field=CharField())),
        _extra_properties=Coalesce(Cast('extra_properties', output_field=CharField()),
                                   Value('null', output_field=CharField()))
    ).order_by(
        'id'
    )

    csv_file = queryset_to_csv_file(queryset, os.path.join(location, 'locations.csv'))

    ordered_field_names = ['id', 'lat', 'lng', 'stadsdeel', 'buurt_code', 'address', 'address_text', 'created_at',
                           'updated_at', 'extra_properties', '_signal_id', ]
    reorder_csv(csv_file.name, ordered_field_names)

    return csv_file.name
