# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from typing import TYPE_CHECKING

import jsonschema
from django.core.exceptions import ValidationError as django_validation_error
from jsonschema.exceptions import SchemaError as js_schema_error
from jsonschema.exceptions import ValidationError as js_validation_error

if TYPE_CHECKING:
    from signals.apps.questionnaires.models import Question


class FieldType:
    """All field types should subclass this, so that they become visible as a choice"""

    # Overwrite this class variable in subclasses, will default to the class name
    verbose_name = None

    def validate_submission_payload(self, payload: dict, question: 'Question' = None) -> dict:
        """
        Check Answer or Choice payload matches the FieldType subclass JSONSchema
        """
        # We raise Django ValidationErrors here because this function is called
        # from model.clean functions and services that underlie REST API calls.
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
