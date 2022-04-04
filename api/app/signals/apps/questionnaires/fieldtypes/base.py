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
