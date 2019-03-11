import json

from jsonschema import validate
from jsonschema.exceptions import ValidationError
from rest_framework.test import APITestCase


class ValidationException(Exception):
    pass


class JsonAPITestCase(APITestCase):
    def assertJsonSchema(self, schema: dict, json_dict: dict):
        """ Validates json_dict against schema. Schema format as defined on json-schema.org . If
        additionalProperties is not set in schema, it will be set to False. This assertion
        treats all properties as 'required', except for when required properties are explicitly
        set according to the json-schema.org standard """

        if "additionalProperties" not in schema:
            schema["additionalProperties"] = False

        schema = self._make_all_properties_required(schema)

        self._validate(schema, json_dict)

    def _make_all_properties_required(self, schema: dict):
        """ Adds the 'required' key to all types 'object', except for when the 'required' key
        already exists """

        if "type" in schema and schema[
            "type"] == "object" and "properties" in schema and isinstance(schema["properties"],
                                                                          dict):

            keys = schema["properties"].keys()
            for key in keys:
                schema["properties"][key] = self._make_all_properties_required(
                    schema["properties"][key])

            if "required" not in schema.keys() and len(keys) > 0:
                schema["required"] = list(keys)

        return schema

    def _validate(self, schema: dict, json_dict: dict):
        try:
            validate(instance=json_dict, schema=schema)
        except ValidationError as e:
            raise ValidationException(e)

    def _load_schema(self, filename: str):
        with open(filename) as f:
            return json.load(f)
