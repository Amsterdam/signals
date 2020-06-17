import os

from tests.apps.signals.factories import CategoryFactory, ParentCategoryFactory, QuestionFactory
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

        question = QuestionFactory.create_batch(1)
        question2 = QuestionFactory.create_batch(1)
        self.parent_category = ParentCategoryFactory.create(questions=question2)
        CategoryFactory.create_batch(1, parent=self.parent_category, questions=question)
        self.parent_category.refresh_from_db()
        super(TestCategoryQuestionEndpoints, self).setUp()

    def test_category_question_list(self):
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
