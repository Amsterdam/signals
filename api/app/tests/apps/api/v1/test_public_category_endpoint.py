import os

from signals.apps.signals.models import Category
from tests.apps.signals.factories import CategoryFactory, ParentCategoryFactory
from tests.test import SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)
SIGNALS_TEST_DIR = os.path.join(os.path.split(THIS_DIR)[0], '..', 'signals')


class TestCategoryTermsEndpoints(SignalsBaseApiTestCase):
    fixtures = ['categories.json', ]

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

        super(TestCategoryTermsEndpoints, self).setUp()

    def test_category_list(self):
        # Asserting that we've 9 parent categories loaded from the json fixture.
        self.assertEqual(Category.objects.filter(parent__isnull=True).count(), 10)

        url = '/signals/v1/public/terms/categories/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.list_categories_schema, data)

        self.assertEqual(len(data['results']), 10)

    def test_category_detail(self):
        # Asserting that we've 13 sub categories for our parent category "Afval".
        main_category = ParentCategoryFactory.create(name='Afval')
        self.assertEqual(main_category.children.count(), 16)

        url = '/signals/v1/public/terms/categories/{slug}'.format(slug=main_category.slug)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.retrieve_category_schema, data)

        self.assertEqual(data['name'], 'Afval')
        self.assertEqual(len(data['sub_categories']), 16)

    def test_sub_category_detail(self):
        sub_category = CategoryFactory.create(name='Grofvuil', parent__name='Afval')

        url = '/signals/v1/public/terms/categories/{slug}/sub_categories/{sub_slug}'.format(
            slug=sub_category.parent.slug,
            sub_slug=sub_category.slug)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # JSONSchema validation
        self.assertJsonSchema(self.retrieve_sub_category_schema, data)

        self.assertEqual(data['name'], 'Grofvuil')
        self.assertIn('is_active', data)
