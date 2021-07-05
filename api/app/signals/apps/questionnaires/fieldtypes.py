# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import inspect
import sys

import jsonschema


class FieldType:
    """All field types should subclass this, so that they become visible as a choice"""
    def clean(self, payload):
        next_rules_schema = self.get_next_rules_schema()
        jsonschema.validate(payload, next_rules_schema)
        return payload

    def get_next_rules_schema(self):
        return {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'ref': {'type': 'string'},
                    'payload': self.submission_schema  # leave out "payload" if next is unconditional
                },
                'required': ['ref'],
                'additionalProperties': False
            }
        }


class PlainText(FieldType):
    choice = ('plain_text', 'PlainText')  # TODO: derive from class name
    submission_schema = {'type': 'string'}


class Integer(FieldType):
    choice = ('integer', 'Integer')
    submission_schema = {'type': 'integer'}


class Submmit(FieldType):
    choice = ('submit', 'Submit')
    submission_schema = {"type": "null"}


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
