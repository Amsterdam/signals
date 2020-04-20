import json

from jsonschema import ValidationError as JSONSchemaValidationError
from jsonschema import validate
from rest_framework.exceptions import ValidationError


class ExtraPropertiesValidator(object):
    requires_context = True

    def __init__(self, *args, **kwargs):
        self.serializer_field = None
        self.schema = None

        filename = kwargs.pop('filename', None)
        if filename:
            with open(filename) as f:
                self.schema = json.load(f)

    def __call__(self, value, serializer_field):
        self.serializer_field = serializer_field

        try:
            validate(instance=value, schema=self.schema)
        except JSONSchemaValidationError:
            # Transform jsonschema ValidationError to DRF ValidationError
            raise ValidationError()
        else:
            return value
