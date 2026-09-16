# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import os

from signals.apps.api.filters import QuestionFilterSet
from signals.apps.api.views import PublicQuestionViewSet
from signals.apps.signals.factories import CategoryFactory, ParentCategoryFactory, QuestionFactory
from signals.apps.signals.factories.category_question import CategoryQuestionFactory
from signals.apps.signals.models import Question
from signals.test.utils import SignalsBaseApiTestCase

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

    def _create_questions_shared_over_categories(self):
        """
        One question re-used in every sub category, holding a different position in
        each of them, next to a question that belongs to a single category.
        """
        shared = QuestionFactory.create(key='shared')

        order = 0
        for i in range(3):
            parent = ParentCategoryFactory.create(name=f'Parent {i}')
            for j in range(3):
                sub = CategoryFactory.create(parent=parent, name=f'Parent {i} sub {j}')
                own = QuestionFactory.create(key=f'own_{i}_{j}')

                order += 1
                CategoryQuestionFactory.create(category=sub, question=own, order=order)
                order += 1
                CategoryQuestionFactory.create(category=sub, question=shared, order=order)

        return shared

    def test_unfiltered_list_does_not_repeat_shared_questions(self):
        """
        A question linked to several categories used to be returned once per
        category, because the columns it was ordered on ended up in the SELECT and
        made the rows distinct from one another.
        """
        shared = self._create_questions_shared_over_categories()

        response = self.client.get('/signals/v1/public/questions/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertJsonSchema(self.retrieve_sub_category_question_schema, data)

        returned_keys = [result['key'] for result in data['results']]
        self.assertEqual(returned_keys.count(shared.key), 1)
        self.assertEqual(len(returned_keys), len(set(returned_keys)))

    def test_unfiltered_queryset_yields_no_duplicate_rows(self):
        """
        Asserted on the rows themselves rather than on the response, because the
        page is truncated to the count: a duplicate that sorts past the cut-off
        disappears from the response and would hide the defect from a test that
        only looks at what the endpoint returned.
        """
        self._create_questions_shared_over_categories()

        queryset = PublicQuestionViewSet.queryset
        filterset = QuestionFilterSet(data={}, queryset=queryset)
        keys = [question.key for question in filterset.qs]

        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(len(keys), Question.objects.count())

    def test_unfiltered_list_does_not_drop_questions(self):
        """
        The count is established without the ordering and is therefore correctly
        de-duplicated, while the page itself was not. The page then got truncated
        to that lower count, silently dropping questions off the end of the list.
        """
        self._create_questions_shared_over_categories()

        response = self.client.get('/signals/v1/public/questions/')
        self.assertEqual(response.status_code, 200)
        data = response.json()

        returned_keys = {result['key'] for result in data['results']}
        self.assertEqual(returned_keys, set(Question.objects.values_list('key', flat=True)))

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

    def test_category_question_non_duplicates_in_list(self):
        question = QuestionFactory.create_batch(1)
        question2 = QuestionFactory.create_batch(1)
        self.parent_category = ParentCategoryFactory.create(questions=question2)
        CategoryFactory.create_batch(2, parent=self.parent_category, questions=question)
        self.parent_category.refresh_from_db()

        endpoint_url = '/signals/v1/public/questions/'

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
