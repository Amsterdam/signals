# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import inspect
import sys

import jsonschema
from django.core.exceptions import ValidationError as django_validation_error
from jsonschema.exceptions import SchemaError as js_schema_error
from jsonschema.exceptions import ValidationError as js_validation_error


class FieldType:
    """All field types should subclass this, so that they become visible as a choice"""

    def validate_submission_payload(self, payload):
        """
        Check Answer or Choice payload matches the FieldType subclass JSONSchema
        """
        # We raise Django ValidationErrors here because this function is called
        # from model.clean functions and services that underlie REST API calls.
        try:
            jsonschema.validate(payload, self.submission_schema)
        except js_schema_error:
            msg = f'JSONSchema for {self.__name__} is not valid.'
            raise django_validation_error(msg)
        except js_validation_error:
            msg = 'Submitted answer does not validate.'
            raise django_validation_error(msg)
        return payload


class PlainText(FieldType):
    choice = ('plain_text', 'PlainText')  # TODO: derive from class name
    submission_schema = {'type': 'string'}


class Integer(FieldType):
    choice = ('integer', 'Integer')
    submission_schema = {'type': 'integer'}


class Boolean(FieldType):
    choice = ('boolean', 'Boolean')
    submission_schema = {'type': 'boolean'}


def init():
    """Initialize field type mapping caches."""
    current_module = sys.modules[__name__]
    field_type_choices = {}
    field_type_classes = {}

    for _, item in inspect.getmembers(current_module):
        if inspect.isclass(item) and issubclass(item, FieldType) and item != FieldType:
            if item.choice[0] in field_type_choices:
                raise Exception(f'Class{item.__name__} is bad, repeated choice[0] of {item.choice[0]} !')

            k, v = item.choice
            field_type_choices[k] = v
            field_type_classes[k] = item

    return field_type_choices, field_type_classes


def field_type_choices():
    """All field types defined."""
    field_type_choices, _ = init()
    return [(k, v) for k, v in field_type_choices.items()]


def get_field_type_class(question):
    """Grab FieldType subclass that defines this question's behavior."""
    _, field_type_classes = init()
    return field_type_classes.get(question.field_type, None)
