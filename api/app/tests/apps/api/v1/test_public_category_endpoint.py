import os

from signals.apps.signals.models import Category
from tests.apps.signals.factories import CategoryFactory, ParentCategoryFactory
from tests.test import SignalsBaseApiTestCase

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

        super(TestCategoryTermsEndpoints, self).setUp()

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
