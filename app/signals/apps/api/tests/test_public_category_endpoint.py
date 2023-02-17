# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
import os

from signals.apps.questionnaires.factories import QuestionnaireFactory
from signals.apps.signals.factories import CategoryFactory, ParentCategoryFactory
from signals.apps.signals.models import Category
from signals.test.utils import SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)


class TestCategoryTermsEndpoints(SignalsBaseApiTestCase):
    def setUp(self):
        self.list_categories_schema = self.load_json_schema(
            os.path.join(
                THIS_DIR,
                'json_schema',
                'get_signals_v1_public_terms_categories.json'
            )
        )
        self.retrieve_category_schema = self.load_json_schema(
            os.path.join(
                THIS_DIR,
                'json_schema',
                'get_signals_v1_public_terms_categories_{slug}.json'
            )
        )
        self.retrieve_sub_category_schema = self.load_json_schema(
            os.path.join(
                THIS_DIR,
                'json_schema',
                'get_signals_v1_public_terms_categories_{slug}_sub_categories_{sub_slug}.json'
            )
        )

        self.parent_category = ParentCategoryFactory.create()
        CategoryFactory.create_batch(5, parent=self.parent_category)
        self.parent_category.refresh_from_db()

        super().setUp()

    def test_category_list(self):
        url = '/signals/v1/public/terms/categories/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.list_categories_schema, data)

        self.assertEqual(len(data['results']), Category.objects.filter(parent__isnull=True).count())

    def test_category_detail(self):
        url = '/signals/v1/public/terms/categories/{slug}'.format(slug=self.parent_category.slug)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.retrieve_category_schema, data)

        self.assertEqual(data['name'], self.parent_category.name)
        self.assertEqual(len(data['sub_categories']), self.parent_category.children.count())

    def test_sub_category_detail(self):
        sub_category = self.parent_category.children.first()

        url = '/signals/v1/public/terms/categories/{slug}/sub_categories/{sub_slug}'.format(
            slug=sub_category.parent.slug,
            sub_slug=sub_category.slug)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.retrieve_sub_category_schema, data)

        self.assertEqual(data['name'], sub_category.name)
        self.assertIn('is_active', data)

    def test_category_detail_questionnaire(self):
        questionnaire = QuestionnaireFactory.create()
        parent_category = ParentCategoryFactory.create(questionnaire=questionnaire)

        url = f'/signals/v1/public/terms/categories/{parent_category.slug}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.retrieve_category_schema, data)
        self.assertIsNotNone(data['_links']['sia:questionnaire'])

    def test_sub_category_detail_questionnaire(self):
        questionnaire = QuestionnaireFactory.create()
        parent_category = ParentCategoryFactory.create()
        sub_category = CategoryFactory.create(parent=parent_category, questionnaire=questionnaire)

        url = f'/signals/v1/public/terms/categories/{sub_category.parent.slug}/sub_categories/{sub_category.slug}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.retrieve_sub_category_schema, data)
        self.assertIsNotNone(data['_links']['sia:questionnaire'])
        self.assertEqual(data['questionnaire'], str(sub_category.questionnaire.uuid))

    def test_parent_category_public_name_and_is_public_accessible_true(self):
        """
        Parent category has a public name and is_public_accessible set to True
        Child category has a public name and is_public_accessible set to False

        The is_public_accessible of the parent category should be True in the response and the is_public_accessible
        of the child category should be False.
        """
        parent_category = ParentCategoryFactory.create(public_name='Publieke naam hoofdcategorie',
                                                       is_public_accessible=True)
        sub_category = CategoryFactory.create(parent=parent_category,
                                              public_name='Publieke naam kindcategorie',
                                              is_public_accessible=False)

        url = f'/signals/v1/public/terms/categories/{parent_category.slug}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.retrieve_category_schema, data)
        self.assertEqual(data['public_name'], parent_category.public_name)
        self.assertTrue(data['is_public_accessible'])

        self.assertEqual(data['sub_categories'][0]['public_name'], sub_category.public_name)
        self.assertFalse(data['sub_categories'][0]['is_public_accessible'])

        url = f'/signals/v1/public/terms/categories/{parent_category.slug}/sub_categories/{sub_category.slug}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.retrieve_sub_category_schema, data)
        self.assertEqual(data['public_name'], sub_category.public_name)
        self.assertFalse(data['is_public_accessible'])

    def test_child_category_public_name_and_is_public_accessible_true(self):
        """
        Parent category has a public name and is_public_accessible set to False
        Child category has a public name and is_public_accessible set to True

        The is_public_accessible of the parent category should be True because there is at least one child category that
        has the is_public_accessible set to True. The is_public_accessible of the child category should be True in the
        response.
        """
        parent_category = ParentCategoryFactory.create(public_name='Publieke naam hoofdcategorie',
                                                       is_public_accessible=False)
        sub_category = CategoryFactory.create(parent=parent_category,
                                              public_name='Publieke naam kindcategorie',
                                              is_public_accessible=True)

        url = f'/signals/v1/public/terms/categories/{parent_category.slug}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.retrieve_category_schema, data)
        self.assertEqual(data['public_name'], parent_category.public_name)
        self.assertTrue(data['is_public_accessible'])

        self.assertEqual(data['sub_categories'][0]['public_name'], sub_category.public_name)
        self.assertTrue(data['sub_categories'][0]['is_public_accessible'])

        url = f'/signals/v1/public/terms/categories/{parent_category.slug}/sub_categories/{sub_category.slug}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.retrieve_sub_category_schema, data)
        self.assertEqual(data['public_name'], sub_category.public_name)
        self.assertTrue(data['is_public_accessible'])
