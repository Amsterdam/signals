# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import json

from jsonschema import validate


class ValidateJsonSchemaMixin:
    @staticmethod
    def assertJsonSchema(schema, json_dict):
        validate(instance=json_dict, schema=schema)

    @staticmethod
    def load_json_schema(filename):
        with open(filename) as f:
            return json.load(f)
