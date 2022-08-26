# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.core.exceptions import ValidationError as django_validation_error
from django.test import TestCase

from signals.apps.questionnaires.factories import ChoiceFactory, QuestionFactory
from signals.apps.questionnaires.services.answer import AnswerService


class TestAnswerService(TestCase):
    def test_validated_answer_payload_not_required(self):
        q = QuestionFactory.create(required=False)
        self.assertEqual(AnswerService.validate_answer_payload(None, q), None)
        self.assertEqual(AnswerService.validate_answer_payload('BLAH', q), 'BLAH')
        with self.assertRaises(django_validation_error):
            AnswerService.validate_answer_payload(['NOT', 'A', 'STRING'], q)

    def test_validated_answer_payload_required(self):
        q = QuestionFactory.create(required=True)
        self.assertEqual(AnswerService.validate_answer_payload('BLAH', q), 'BLAH')
        with self.assertRaises(django_validation_error):
            AnswerService.validate_answer_payload(None, q)
        with self.assertRaises(django_validation_error):
            AnswerService.validate_answer_payload(['NOT', 'A', 'STRING'], q)

    def test_validate_answer_payload_do_not_enforce_choices(self):
        q = QuestionFactory.create(required=False, enforce_choices=False)
        ChoiceFactory.create(question=q, payload='VALID')
        self.assertEqual(AnswerService.validate_answer_payload('VALID', q), 'VALID')
        self.assertEqual(AnswerService.validate_answer_payload('BLAH', q), 'BLAH')

    def test_validate_answer_payload_do_enforce_choices(self):
        q = QuestionFactory.create(required=False, enforce_choices=True)
        ChoiceFactory.create(question=q, payload='VALID')
        self.assertEqual(AnswerService.validate_answer_payload('VALID', q), 'VALID')
        with self.assertRaises(django_validation_error):
            AnswerService.validate_answer_payload('BLAH', q)

    def test_validate_fieldtypes(self):
        integer_question = QuestionFactory(field_type='integer', label='integer', short_label='integer')
        plaintext_question = QuestionFactory(
            field_type='plain_text', label='plain_text', short_label='plain_text')
        validate_answer = AnswerService.validate_answer_payload

        # Check integer fieldtype
        self.assertEqual(validate_answer(123456, integer_question), 123456)
        with self.assertRaises(django_validation_error):
            validate_answer('THESE ARE CHARACTERS', integer_question)
        with self.assertRaises(django_validation_error):
            validate_answer({'some': 'thing', 'complicated': {}}, integer_question)

        # check plain_text fieldtype
        self.assertEqual(validate_answer('THIS IS TEXT', plaintext_question), 'THIS IS TEXT')
        with self.assertRaises(django_validation_error):
            validate_answer(123456, plaintext_question)
        with self.assertRaises(django_validation_error):
            validate_answer({'some': 'thing', 'complicated': {}}, plaintext_question)

    def test_validate_field_type_select_object(self):
        selected_object_question = QuestionFactory(field_type='selected_object', label='selected_object',
                                                   short_label='selected_object')
        validate_answer = AnswerService.validate_answer_payload

        # Basic payloads that should raise a validation error
        with self.assertRaises(django_validation_error):
            validate_answer('Invalid payload', selected_object_question)
        with self.assertRaises(django_validation_error):
            validate_answer(123456789, selected_object_question)
        with self.assertRaises(django_validation_error):
            validate_answer(True, selected_object_question)
        with self.assertRaises(django_validation_error):
            validate_answer(False, selected_object_question)

        # These payloads should be valid
        payload_not_on_map_simple = {'type': 'not-on-map'}
        validate_answer(payload_not_on_map_simple, selected_object_question)

        payload_not_on_map_complex = {'id': 123456, 'type': 'not-on-map', 'label': 'Niet op de kaart - 123456'}
        validate_answer(payload_not_on_map_complex, selected_object_question)

        payload_object_selected = {'id': '123456', 'type': 'type-of-object', 'description': 'description',
                                   'isReported': False, 'label': 'Label - 123456'}
        validate_answer(payload_object_selected, selected_object_question)

        payload_object_selected = {'id': 123456, 'type': 'type-of-object', 'description': 'description',
                                   'isReported': False, 'label': 'Label - 123456',
                                   'location': {'coordinates': {'lat': 52.36768424, 'lon': 4.90022563}}}
        validate_answer(payload_object_selected, selected_object_question)

        payload_object_selected = {'id': 123456, 'type': 'type-of-object', 'description': 'description',
                                   'isReported': False, 'label': 'Label - 123456',
                                   'location': {'coordinates': {'lat': 52.36768424, 'lon': 4.90022563},
                                                'address': {'openbare_ruimte': 'De Ruijterkade', 'huisnummer': '36',
                                                            'huisletter': 'A', 'huisnummer_toevoeging': '',
                                                            'postcode': '1012AA', 'woonplaats': 'Amsterdam'}}}
        validate_answer(payload_object_selected, selected_object_question)
