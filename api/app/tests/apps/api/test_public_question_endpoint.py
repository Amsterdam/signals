# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import os

from signals.apps.signals.factories import CategoryFactory, ParentCategoryFactory, QuestionFactory
from signals.apps.signals.models import Question
from tests.test import SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)


class TestCategoryQuestionEndpoints(SignalsBaseApiTestCase):
    def setUp(self):
        self.retrieve_sub_category_question_schema = self.load_json_schema(
            os.path.join(
                THIS_DIR,
                'json_schema',
                'get_signals_v1_public_questions_categories_{slug}_sub_categories_{sub_slug}.json'
            )
        )

        super().setUp()

    def test_category_question_list(self):
        question = QuestionFactory.create_batch(1)
        question2 = QuestionFactory.create_batch(1)
        self.parent_category = ParentCategoryFactory.create(questions=question2)
        CategoryFactory.create_batch(1, parent=self.parent_category, questions=question)
        self.parent_category.refresh_from_db()

        endpoint_url = '/signals/v1/public/questions/'
        response = self.client.get(endpoint_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # JSONSchema validation
        self.assertJsonSchema(self.retrieve_sub_category_question_schema, data)
        self.assertEqual(data['count'], 2)

        # filter on main
        sub_category = self.parent_category.children.first()
        url = '{endp}?main_slug={slug}'.format(
            endp=endpoint_url,
            slug=sub_category.parent.slug)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, msg=url)
        data = response.json()
        # JSONSchema validation
        self.assertJsonSchema(self.retrieve_sub_category_question_schema, data)
        self.assertEqual(data['count'], 1)

        # filter on main and sub
        sub_category = self.parent_category.children.first()
        url = '{endp}?main_slug={slug}&sub_slug={sub_slug}'.format(
            endp=endpoint_url,
            slug=sub_category.parent.slug,
            sub_slug=sub_category.slug)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, msg=url)
        data = response.json()
        # JSONSchema validation
        self.assertJsonSchema(self.retrieve_sub_category_question_schema, data)
        self.assertEqual(data['count'], 2)

    def test_category_question_field_types(self):
        """
        Create a question for every field type and check if they are returned correctly
        """
        category = ParentCategoryFactory.create(name='Category for field_type testing',
                                                slug='question-field-type')
        for field_type in list(dict(Question.FIELD_TYPE_CHOICES).keys()):
            category.questions.clear()

            question = QuestionFactory.create(field_type=field_type)
            category.questions.add(question)
            category.refresh_from_db()

            response = self.client.get(f'/signals/v1/public/questions/?slug={category.slug}')
            self.assertEqual(response.status_code, 200)

            response_data = response.json()
            self.assertJsonSchema(self.retrieve_sub_category_question_schema, response_data)
            self.assertEqual(response_data['count'], 1)

            result = response_data['results'][0]
            self.assertEqual(result['key'], question.key)
            self.assertEqual(result['field_type'], question.field_type)
            self.assertEqual(result['meta'], question.meta)
            self.assertEqual(result['required'], question.required)
