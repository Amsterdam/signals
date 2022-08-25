# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import copy

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

        base_payload = {
            'id': None,
            'type': None,
            'onMap': None,
            'coordinates': {
                'lat': None,
                'lng': None
            }
        }

        # Basic payloads that should raise a validation error
        with self.assertRaises(django_validation_error):
            validate_answer('Invalid payload', selected_object_question)
        with self.assertRaises(django_validation_error):
            validate_answer(123456789, selected_object_question)
        with self.assertRaises(django_validation_error):
            validate_answer(True, selected_object_question)
        with self.assertRaises(django_validation_error):
            validate_answer(False, selected_object_question)

        # Layout of the payload is correct, the contents is empty. Should raise an error.
        # Only the id is allowed to be None
        with self.assertRaises(django_validation_error):
            validate_answer(base_payload, selected_object_question)

        # These payloads should be valid
        payload_not_on_map = copy.deepcopy(base_payload)

        payload_not_on_map['type'] = 'container'
        payload_not_on_map['onMap'] = True
        payload_not_on_map['type'] = 'not-on-map'
        payload_not_on_map['coordinates']['lat'] = 4.90022563
        payload_not_on_map['coordinates']['lng'] = 52.36768424

        for _id in [None, 123456, '123456-TEST']:
            payload_not_on_map['id'] = _id
            validate_answer(payload_not_on_map, selected_object_question)

        payload_not_on_map['onMap'] = False
        validate_answer(payload_not_on_map, selected_object_question)

        # Invalid types for onMap
        for invalid_on_map in ['True', 'False', 1, 0, '', None]:
            payload_not_on_map['onMap'] = invalid_on_map
            with self.assertRaises(django_validation_error):
                validate_answer(False, selected_object_question)

        selected_object_question.multiple_answers = True
        selected_object_question.save()

        validate_answer([payload_object_selected for x in range(3)], selected_object_question)

    def test_validate_multiple_answers(self):
        q = QuestionFactory.create(field_type='plain_text', multiple_answers=True, required=True,
                                   extra_properties={'answers': {'minItems': 2, 'maxItems': 5}})

        AnswerService.validate_answer_payload(['answer 1', 'answer 2'], q)
        AnswerService.validate_answer_payload([f'answer {x}' for x in range(5)], q)
        with self.assertRaises(django_validation_error):
            # Not a list
            AnswerService.validate_answer_payload('answer is not a list', q)

            # Only one answer is given, the minimum is 2
            AnswerService.validate_answer_payload(['answer 1', ], q)

            # An empty list
            AnswerService.validate_answer_payload([], q)

            # Not strings
            AnswerService.validate_answer_payload([1, 2, 3], q)

            # Too much answers
            AnswerService.validate_answer_payload([f'answer {x}' for x in range(6)], q)
