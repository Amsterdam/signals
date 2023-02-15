# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import jsonschema
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class JSONSchemaValidator:
    def __init__(self, schema):
        self.schema = schema

    def __call__(self, value):
        try:
            jsonschema.validate(instance=value, schema=self.schema)
        except jsonschema.ValidationError as e:
            raise ValidationError(str(e).replace('\n\n', ': ').replace('\n', ''))
        else:
            return value
