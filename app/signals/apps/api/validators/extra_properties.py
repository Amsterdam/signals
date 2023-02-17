# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
import json

from jsonschema import ValidationError as JSONSchemaValidationError
from jsonschema import validate
from rest_framework.exceptions import ValidationError as DRFValidationError


class ExtraPropertiesValidator:
    def __init__(self, filename):
        with open(filename) as f:
            self.schema = json.load(f)

    def __call__(self, value):
        try:
            validate(instance=value, schema=self.schema)
        except JSONSchemaValidationError:
            # Transform jsonschema ValidationError to DRF ValidationError
            raise DRFValidationError()
        else:
            return value
