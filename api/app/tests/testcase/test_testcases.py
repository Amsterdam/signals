from unittest.mock import MagicMock

from rest_framework.test import APITestCase

from .testcases import JsonAPITestCase, ValidationException


class TestJsonAPITestCase(APITestCase):

    def test_additional_properties_defaults_false(self):
        json_api_testcase = JsonAPITestCase()
        json_api_testcase._validate = MagicMock()

        schema = {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                },
            },
        }
        data = {
            "key": "value"
        }
        json_api_testcase.assertJsonSchema(schema, data)

        schema["additionalProperties"] = False
        json_api_testcase._validate.assert_called_with(schema, data)

    def test_additional_properties_not_overridden_when_true(self):
        json_api_testcase = JsonAPITestCase()
        json_api_testcase._validate = MagicMock()

        schema = {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                },
            },
            "additionalProperties": True
        }
        data = {
            "key": "value"
        }

        json_api_testcase.assertJsonSchema(schema, data)
        json_api_testcase._validate.assert_called_with(schema, data)

    def _get_schema(self):
        return {
            "type": "object",
            "properties": {
                "numberproperty": {
                    "type": "number",
                },
                "strproperty": {
                    "type": "string",
                },
                "objproperty": {
                    "type": "object",
                    "properties": {
                        "prop1": {
                            "type": "number",
                        },
                        "prop2": {
                            "type": "string",
                        },
                    },
                },
                "arrayproperty": {
                    "type": "array",
                },
                "booleanproperty": {
                    "type": "boolean",
                },
                "nullproperty": {
                    "type": "null",
                },
                "enumproperty": {
                    # Can be used with or without type.
                    "enum": ["a", "b", "c", 1, 4],
                },
                "constproperty": {
                    "const": "This should always be this text",
                },
            },
        }

    def _get_data(self):
        return {
            "numberproperty": 4,
            "strproperty": "string value",
            "objproperty": {
                "prop1": .4,
                "prop2": "string val",
            },
            "arrayproperty": [1, 2, 3, 4, 5],
            "booleanproperty": True,
            "nullproperty": None,
            "enumproperty": "b",
            "constproperty": "This should always be this text",
        }

    def _test_schema_data(self, schema: dict, data: dict):
        json_api_testcase = JsonAPITestCase()
        json_api_testcase.assertJsonSchema(schema, data)

    def test_basic_valid_schema(self):
        """ Uses a schema definition with some different properties as example. See json-schema.org
        for more advanced schema's. """

        self._test_schema_data(self._get_schema(), self._get_data())

    def test_missing_property(self):
        """ Missing property should throw exception """

        data = self._get_data()
        del data["booleanproperty"]

        self.assertRaises(ValidationException, self._test_schema_data, self._get_schema(), data)

    def test_allow_missing_property(self):
        """ Allows missing properties when 'required' list is explicitly set """

        schema = self._get_schema()
        schema["properties"]["objproperty"]["required"] = ["prop2"]
        data = self._get_data()
        del data["objproperty"]["prop1"]

        self._test_schema_data(schema, data)

    def test_missing_nested_property(self):
        """ Missing property should throw exception """

        data = self._get_data()
        del data["objproperty"]["prop1"]

        self.assertRaises(ValidationException, self._test_schema_data, self._get_schema(), data)

    def test_wrong_property_type(self):
        """ Wrong property type should throw exception """
        data = self._get_data()
        data["booleanproperty"] = "Wrong type"

        self.assertRaises(ValidationException, self._test_schema_data, self._get_schema(), data)
