# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import inspect
import re
import sys

from signals.apps.questionnaires.fieldtypes.attachment import Image
from signals.apps.questionnaires.fieldtypes.base import FieldType
from signals.apps.questionnaires.fieldtypes.boolean import Boolean
from signals.apps.questionnaires.fieldtypes.datetime import Date, DateTime, Time
from signals.apps.questionnaires.fieldtypes.float import Float
from signals.apps.questionnaires.fieldtypes.integer import Integer, PositiveInteger
from signals.apps.questionnaires.fieldtypes.text import DutchTelephoneNumber, Email, PlainText

__all__ = [
    'PlainText',
    'Email',
    'DutchTelephoneNumber',
    'Integer',
    'PositiveInteger',
    'Boolean',
    'Image',
    'Float',
    'Date',
    'DateTime',
    'Time',
]

_PATTERN_CAMEL_CASE = re.compile(r'(?<!^)(?=[A-Z])')


def _init():
    """Initialize field type mapping caches."""
    field_type_choices = {}
    field_type_classes = {}

    for _, item in inspect.getmembers(sys.modules[__name__]):
        if inspect.isclass(item) and issubclass(item, FieldType) and item != FieldType:
            key = _PATTERN_CAMEL_CASE.sub('_', item.__name__).lower()
            if key in field_type_choices:
                raise Exception(f'Class "{item.__name__}" is bad! Already registered!')

            field_type_choices[key] = item.verbose_name or item.__name__
            field_type_classes[key] = item

    return field_type_choices, field_type_classes


def field_type_choices():
    """All field types defined."""
    field_type_choices, _ = _init()
    return [(k, v) for k, v in field_type_choices.items()]


def get_field_type_class(question):
    """Grab FieldType subclass that defines this question's behavior."""
    _, field_type_classes = _init()
    return field_type_classes.get(question.field_type, None)
