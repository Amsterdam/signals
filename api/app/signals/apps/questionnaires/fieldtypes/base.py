# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import jsonschema
from django.core.exceptions import ValidationError as django_validation_error
from jsonschema.exceptions import SchemaError as js_schema_error
from jsonschema.exceptions import ValidationError as js_validation_error


class FieldType:
    """All field types should subclass this, so that they become visible as a choice"""

    # Overwrite this class variable in subclasses, will default to the class name
    verbose_name = None

    # _multiple_answers_schema contains the JSONSchema that will be used to validate if the given answer meets the min
    # and max items required.
    #
    # The default minItems is set to 1.
    # The default for maxItems is set to 10.
    # To overwrite the minItems and the maxItems the Question.additional_validation can be overwritten.
    #
    # For example:
    # {
    #   "answers":
    #   {
    #       "minItems": 3,
    #       "maxItems": 5
    #   }
    # }
    _multiple_answers_schema = {
        'type': 'array',
        'items': {},  # Default value, will be overridden with the correct schema for the given field_type
        'minItems': 1,  # Default value
        'maxItems': 10  # Default value
    }

    def __init__(self, multiple_answers_allowed=False, min_items=None, max_items=None):
        self.multiple_answers_allowed = multiple_answers_allowed
        self._min_items = min_items or None
        self._max_items = max_items or None

    def validate_submission_payload(self, payload: dict) -> dict:
        """
        Check Answer or Choice payload matches the FieldType subclass JSONSchema
        """
        # We raise Django ValidationErrors here because this function is called
        # from model.clean functions and services that underlie REST API calls.
        if self.multiple_answers_allowed:
            schema = self._multiple_answers_schema
            schema['items'].update(self.submission_schema)
            schema['minItems'] = self._min_items
            schema['maxItems'] = self._max_items
        else:
            schema = self.submission_schema

        try:
            jsonschema.validate(payload, schema)
        except js_schema_error:
            msg = f'JSONSchema for {self.verbose_name or self.__class__.__name__} is not valid.'
            raise django_validation_error(msg)
        except js_validation_error as jsve:
            msg = f'Submitted answer does not validate. {jsve.message}'
            raise django_validation_error(msg)
        return payload
