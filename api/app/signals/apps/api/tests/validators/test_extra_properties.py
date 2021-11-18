# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import os

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from signals.apps.api.validators.extra_properties import ExtraPropertiesValidator
from signals.apps.signals.factories import CategoryFactory


class TestExtraPropertiesValidator(TestCase):
    schema_file_path = os.path.join(os.path.dirname(__file__), '../..', 'json_schema', 'extra_properties.json')

    def setUp(self):
        self.category = CategoryFactory()

    def test_extra_properties_validation(self):
        validator = ExtraPropertiesValidator(filename=self.schema_file_path)

        extra_properties = [{
            'id': 'test_id-1',
            'label': 'test_label',
            'answer': {
                'id': 'test_answer',
                'value': 'test_value'
            },
            'category_url': self.category
        }, {
            'id': 'test_id-2',
            'label': 'test_label',
            'answer': 'test_answer',
            'category_url': self.category
        }, {
            'id': 'test_id-3',
            'label': 'test_label',
            'answer': ['a', 'b', 'c'],
            'category_url': self.category
        }]
        validator(extra_properties)

    def test_extra_properties_validation_invalid_extra_properties(self):
        validator = ExtraPropertiesValidator(filename=self.schema_file_path)

        extra_properties = [1, 2, 3, 4]
        with self.assertRaises(ValidationError):
            validator(extra_properties)

    def test_extra_properties_validation_no_file_with_schema_filename_given(self):
        with self.assertRaises(TypeError):
            ExtraPropertiesValidator()
